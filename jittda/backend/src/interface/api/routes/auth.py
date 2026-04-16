"""OAuth 2.0 Authentication routes (Google + GitHub)."""

from __future__ import annotations

import os
import secrets
import time

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from infrastructure.persistence.repository import UserRepository
from interface.api.middleware.auth import create_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth = OAuth()

# Google OAuth
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# GitHub OAuth
oauth.register(
    name="github",
    client_id=os.environ.get("GITHUB_CLIENT_ID", ""),
    client_secret=os.environ.get("GITHUB_CLIENT_SECRET", ""),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "read:user user:email"},
)


_auth_codes: dict[str, tuple[str, float]] = {}  # code -> (jwt, expiry)


async def _store_auth_code(jwt_token: str) -> str:
    """JWT를 임시 코드로 교환. 30초 TTL, 1회용."""
    now = time.time()
    # Lazy cleanup: 만료된 엔트리 제거 (메모리 누수 방지)
    expired = [k for k, (_, exp) in _auth_codes.items() if exp < now]
    for k in expired:
        del _auth_codes[k]
    code = secrets.token_urlsafe(32)
    _auth_codes[code] = (jwt_token, now + 30)
    return code


def _get_redirect_base() -> str:
    return (
        os.environ.get("FRONTEND_URL")
        or os.environ.get("ALLOWED_ORIGINS", "http://localhost:3001").split(",")[0]
    )


def _warn_if_localhost_redirect(redirect_uri: str, provider: str) -> None:
    """프로덕션에서 localhost redirect_uri 생성 시 경고."""
    if "localhost" in redirect_uri and os.environ.get("ENV") == "production":
        import structlog

        structlog.get_logger().warning(
            "oauth_redirect_uri_suspicious",
            provider=provider,
            redirect_uri=redirect_uri,
            hint="ProxyHeadersMiddleware가 X-Forwarded-* 헤더를 올바르게 처리하지 못했을 수 있음",
        )


@router.get("/google")
async def google_login(request: Request):
    """Redirect to Google OAuth consent screen."""
    redirect_uri = str(request.url_for("google_callback"))
    _warn_if_localhost_redirect(redirect_uri, "google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request):
    """Handle Google OAuth callback."""
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(400, "Failed to get user info from Google")

    user_repo = UserRepository()

    user = await user_repo.upsert_oauth_user(
        email=userinfo["email"],
        name=userinfo.get("name", ""),
        oauth_provider="google",
        oauth_id=userinfo["sub"],
    )

    jwt_token = create_token(user["id"], user["email"])
    code = await _store_auth_code(jwt_token)
    redirect_url = f"{_get_redirect_base()}/auth/callback?code={code}"
    return RedirectResponse(url=redirect_url)


@router.get("/github")
async def github_login(request: Request):
    """Redirect to GitHub OAuth consent screen."""
    redirect_uri = str(request.url_for("github_callback"))
    _warn_if_localhost_redirect(redirect_uri, "github")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request):
    """Handle GitHub OAuth callback."""
    token = await oauth.github.authorize_access_token(request)

    resp = await oauth.github.get("user", token=token)
    github_user = resp.json()

    # GitHub email might need separate API call
    email = github_user.get("email")
    if not email:
        emails_resp = await oauth.github.get("user/emails", token=token)
        emails = emails_resp.json()
        primary = next((e for e in emails if e.get("primary")), None)
        email = primary["email"] if primary else f"{github_user['login']}@github.noreply.com"

    user_repo = UserRepository()

    user = await user_repo.upsert_oauth_user(
        email=email,
        name=github_user.get("name") or github_user["login"],
        oauth_provider="github",
        oauth_id=str(github_user["id"]),
    )

    jwt_token = create_token(user["id"], user["email"])
    code = await _store_auth_code(jwt_token)
    redirect_url = f"{_get_redirect_base()}/auth/callback?code={code}"
    return RedirectResponse(url=redirect_url)


@router.post("/exchange")
async def exchange_code(code: str):
    """임시 코드를 JWT로 교환 (1회용, 30초 TTL)."""
    entry = _auth_codes.pop(code, None)
    if not entry or entry[1] < time.time():
        raise HTTPException(401, "Invalid or expired code")
    return {"token": entry[0]}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return user
