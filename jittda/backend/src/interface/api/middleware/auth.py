"""JWT Authentication middleware."""

from __future__ import annotations

import os
import secrets as _secrets_mod
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(hours=24)

security = HTTPBearer(auto_error=False)

_cached_secret: str | None = None


def _get_secret() -> str:
    """JWT 서명 시크릿을 반환한다. 미설정 시 캐시된 랜덤 시크릿 사용."""
    global _cached_secret
    if _cached_secret is not None:
        return _cached_secret
    secret = os.environ.get("JWT_SECRET", "")
    if not secret:
        structlog.get_logger().warning(
            "jwt_secret_missing",
            detail="JWT_SECRET not set, using random secret (tokens won't persist across restarts)",
        )
        secret = _secrets_mod.token_urlsafe(32)
    _cached_secret = secret
    return secret


def create_token(user_id: str, email: str) -> str:
    """Create a JWT access token."""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + JWT_EXPIRATION,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _get_secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        return jwt.decode(token, _get_secret(), algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """FastAPI dependency: extract and verify JWT from Authorization header."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_token(credentials.credentials)
    return {"user_id": payload["sub"], "email": payload["email"]}


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict | None:
    """FastAPI dependency: optional authentication (returns None if no token)."""
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return {"user_id": payload["sub"], "email": payload["email"]}
    except HTTPException:
        return None
