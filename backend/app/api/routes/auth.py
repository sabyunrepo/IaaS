"""
backend/app/api/routes/auth.py
OAuth 로그인/콜백 + API Key 관리
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.github import GitHubOAuth2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.exceptions import AuthenticationError, ValidationError
from app.models.database import UserDB, OAuthAccountDB, APIKeyDB
from app.services.auth_service import create_jwt, create_api_key, encrypt_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# --- OAuth Clients ---

google_oauth = GoogleOAuth2(
    client_id=settings.GOOGLE_CLIENT_ID or "",
    client_secret=settings.GOOGLE_CLIENT_SECRET or "",
)

github_oauth = GitHubOAuth2(
    client_id=settings.GITHUB_CLIENT_ID or "",
    client_secret=settings.GITHUB_CLIENT_SECRET or "",
)

OAUTH_CLIENTS = {
    "google": google_oauth,
    "github": github_oauth,
}

OAUTH_SCOPES = {
    "google": ["openid", "email", "profile"],
    "github": ["user:email"],
}


def _get_public_base_url(request: Request) -> str:
    """nginx 리버스 프록시 뒤에서 공개 URL 감지.

    X-Forwarded-Proto/Host 헤더가 있으면 사용하고,
    없으면 settings 값으로 fallback.
    """
    forwarded_proto = request.headers.get("x-forwarded-proto")
    host = request.headers.get("host")
    if forwarded_proto and host:
        return f"{forwarded_proto}://{host}"
    return settings.BACKEND_URL


# --- Login ---

@router.get("/{provider}/login")
async def oauth_login(provider: str, request: Request):
    """OAuth 로그인 시작 → provider 동의 화면으로 리다이렉트"""
    if provider not in OAUTH_CLIENTS:
        raise ValidationError(f"Unsupported provider: {provider}")

    client = OAUTH_CLIENTS[provider]
    callback_url = f"{_get_public_base_url(request)}/auth/{provider}/callback"
    scopes = OAUTH_SCOPES.get(provider, [])

    authorization_url = await client.get_authorization_url(
        callback_url,
        scope=scopes,
    )

    return RedirectResponse(url=authorization_url)


# --- Callback ---

@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """OAuth 콜백 → JWT 발급 → 프론트엔드로 리다이렉트"""
    if provider not in OAUTH_CLIENTS:
        raise ValidationError(f"Unsupported provider: {provider}")

    client = OAUTH_CLIENTS[provider]
    callback_url = f"{_get_public_base_url(request)}/auth/{provider}/callback"

    # 1. code → access_token
    try:
        token_response = await client.get_access_token(code, callback_url)
    except Exception:
        raise AuthenticationError("Failed to exchange OAuth code")

    access_token = token_response["access_token"]

    # 2. access_token → 사용자 정보
    async with client.get_httpx_client() as httpx_client:
        if provider == "google":
            resp = await httpx_client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_info = resp.json()
            email = user_info["email"]
            name = user_info.get("name")
            image = user_info.get("picture")
            provider_account_id = user_info["sub"]
        elif provider == "github":
            resp = await httpx_client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_info = resp.json()
            # GitHub email can be private, fetch separately
            email_resp = await httpx_client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            emails = email_resp.json()
            primary = next((e for e in emails if e.get("primary")), emails[0] if emails else None)
            email = primary["email"] if primary else user_info.get("email", "")
            name = user_info.get("name") or user_info.get("login")
            image = user_info.get("avatar_url")
            provider_account_id = str(user_info["id"])
        else:
            raise ValidationError(f"Unsupported provider: {provider}")

    if not email:
        raise AuthenticationError("Could not retrieve email from OAuth provider")

    # 3. User upsert
    result = await db.execute(select(UserDB).where(UserDB.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        user = UserDB(
            id=uuid.uuid4(),
            email=email,
            name=name,
            image=image,
        )
        db.add(user)
        await db.flush()

    # 4. OAuthAccount upsert
    result = await db.execute(
        select(OAuthAccountDB).where(
            OAuthAccountDB.provider == provider,
            OAuthAccountDB.provider_account_id == provider_account_id,
        )
    )
    oauth_account = result.scalar_one_or_none()

    encrypted_token = encrypt_token(access_token)

    if oauth_account is None:
        oauth_account = OAuthAccountDB(
            id=uuid.uuid4(),
            user_id=user.id,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=encrypted_token,
            token_type=token_response.get("token_type"),
            scope=token_response.get("scope"),
        )
        db.add(oauth_account)
    else:
        oauth_account.access_token = encrypted_token

    await db.flush()

    # 5. JWT 발급
    jwt_token = create_jwt({
        "sub": str(user.id),
        "email": user.email,
        "plan": user.plan,
    })

    # 6. 프론트엔드로 리다이렉트 (같은 도메인 뒤 nginx 프록시)
    base_url = _get_public_base_url(request)
    return RedirectResponse(url=f"{base_url}/auth/callback?token={jwt_token}")


# --- API Key Management ---

@router.post("/api-keys")
async def create_api_key_endpoint(
    name: str | None = None,
    user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """새 API Key 생성 (raw key는 이 응답에서만 확인 가능)"""
    raw_key, key_hash = create_api_key()

    api_key = APIKeyDB(
        id=uuid.uuid4(),
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=raw_key[:8],
        name=name,
    )
    db.add(api_key)
    await db.flush()

    return {
        "id": str(api_key.id),
        "key": raw_key,
        "prefix": raw_key[:8],
        "name": name,
        "created_at": api_key.created_at,
    }


@router.get("/me")
async def get_me(user: UserDB = Depends(get_current_user)):
    """현재 사용자 정보"""
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "image": user.image,
        "plan": user.plan,
    }


# --- Dev Login (로컬 환경 전용) ---

@router.post("/dev-login")
async def dev_login(db: AsyncSession = Depends(get_db)):
    """개발/테스트용 로그인 — 로컬 환경에서만 활성화"""
    if not settings.is_local:
        raise AuthenticationError("Dev login is only available in local environment")

    test_email = "dev@vantict.local"
    result = await db.execute(select(UserDB).where(UserDB.email == test_email))
    user = result.scalar_one_or_none()

    if user is None:
        user = UserDB(
            id=uuid.uuid4(),
            email=test_email,
            name="Dev User",
            image=None,
        )
        db.add(user)
        await db.flush()

    jwt_token = create_jwt({
        "sub": str(user.id),
        "email": user.email,
        "plan": user.plan,
    })

    return {"token": jwt_token}
