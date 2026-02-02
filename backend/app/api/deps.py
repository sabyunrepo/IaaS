"""
backend/app/api/deps.py
FastAPI 의존성 (인증)
"""
from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions import AuthenticationError
from app.models.database import UserDB, APIKeyDB
from app.services.auth_service import verify_jwt, hash_api_key


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> UserDB:
    """JWT Bearer 토큰으로 사용자 인증"""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")

    token = authorization[7:]
    payload = verify_jwt(token)
    if payload is None or "sub" not in payload:
        raise AuthenticationError("Invalid or expired token")

    result = await db.execute(select(UserDB).where(UserDB.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")

    return user


async def get_current_user_or_api_key(
    authorization: str | None = Header(None, alias="Authorization"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> UserDB:
    """JWT 또는 API Key로 사용자 인증"""
    # API Key 우선
    if x_api_key and x_api_key.startswith("vnt_"):
        key_hash = hash_api_key(x_api_key)
        result = await db.execute(
            select(APIKeyDB).where(APIKeyDB.key_hash == key_hash, APIKeyDB.is_active == True)
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            raise AuthenticationError("Invalid API key")

        # Update last_used_at
        from datetime import datetime, timezone
        api_key.last_used_at = datetime.now(timezone.utc)

        # Get user
        user_result = await db.execute(select(UserDB).where(UserDB.id == api_key.user_id))
        user = user_result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        return user

    # JWT fallback
    return await get_current_user(authorization=authorization, db=db)


async def validate_api_key(token: str, db: AsyncSession) -> UserDB | None:
    """WebSocket용 토큰 검증 (API Key 또는 JWT)"""
    # Try API Key
    if token.startswith("vnt_"):
        key_hash = hash_api_key(token)
        result = await db.execute(
            select(APIKeyDB).where(APIKeyDB.key_hash == key_hash, APIKeyDB.is_active == True)
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            return None
        user_result = await db.execute(select(UserDB).where(UserDB.id == api_key.user_id))
        return user_result.scalar_one_or_none()

    # Try JWT
    payload = verify_jwt(token)
    if payload and "sub" in payload:
        result = await db.execute(select(UserDB).where(UserDB.id == payload["sub"]))
        user = result.scalar_one_or_none()
        if user and user.is_active:
            return user
    return None
