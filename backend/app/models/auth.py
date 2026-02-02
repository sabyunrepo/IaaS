"""
backend/app/models/auth.py
인증 관련 Pydantic 모델
"""
from datetime import datetime
from typing import Literal
import uuid

from pydantic import BaseModel, Field


class User(BaseModel):
    """사용자 (OAuth 로그인 시 자동 생성)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str | None = None
    image: str | None = None
    plan: Literal["free", "pro", "enterprise"] = "free"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OAuthAccount(BaseModel):
    """OAuth 연결 계정"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    provider: str
    provider_account_id: str
    access_token: str | None = None
    refresh_token: str | None = None
    expires_at: int | None = None
    token_type: str | None = None
    scope: str | None = None


class APIKey(BaseModel):
    """API Key (프로그래밍 접근용)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    key_prefix: str
    name: str | None = None
    is_active: bool = True
    last_used_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
