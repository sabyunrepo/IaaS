"""OAuth 2.0 Authentication routes (Google + GitHub)."""

from __future__ import annotations

import os

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


def _get_redirect_base() -> str:
    return (
        os.environ.get("FRONTEND_URL")
        or os.environ.get("ALLOWED_ORIGINS", "http://localhost:3001").split(",")[0]
    )


@router.get("/google")
async def google_login(request: Request):
    """Redirect to Google OAuth consent screen."""
    redirect_uri = str(request.url_for("google_callback"))
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
    redirect_url = f"{_get_redirect_base()}/auth/callback?token={jwt_token}"
    return RedirectResponse(url=redirect_url)


@router.get("/github")
async def github_login(request: Request):
    """Redirect to GitHub OAuth consent screen."""
    redirect_uri = str(request.url_for("github_callback"))
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
    redirect_url = f"{_get_redirect_base()}/auth/callback?token={jwt_token}"
    return RedirectResponse(url=redirect_url)


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return user
