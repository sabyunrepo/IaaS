"""
backend/app/models/database.py
SQLAlchemy ORM 모델 (PostgreSQL 테이블)
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index, String, Text, BigInteger,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserDB(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    image = Column(String(2048))
    plan = Column(String(50), nullable=False, default="free")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    oauth_accounts = relationship("OAuthAccountDB", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKeyDB", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("JobDB", back_populates="user")


class OAuthAccountDB(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        Index("idx_oauth_provider", "provider", "provider_account_id"),
        Index("idx_oauth_user", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)
    provider_account_id = Column(String(255), nullable=False)
    access_token = Column(Text)
    refresh_token = Column(Text)
    expires_at = Column(BigInteger)
    token_type = Column(String(50))
    scope = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("UserDB", back_populates="oauth_accounts")


class APIKeyDB(Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("idx_api_keys_user", "user_id"),
        Index("idx_api_keys_hash", "key_hash"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(10), nullable=False)
    name = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("UserDB", back_populates="api_keys")


class JobDB(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("idx_jobs_user", "user_id"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_temporal", "temporal_workflow_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    temporal_workflow_id = Column(String(255), unique=True)
    status = Column(String(50), nullable=False, default="pending")
    input_data = Column(JSONB, nullable=False)
    final_output = Column(JSONB)
    callback_url = Column(String(2048))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    user = relationship("UserDB", back_populates="jobs")
    checkpoints = relationship("CheckpointDB", back_populates="job", cascade="all, delete-orphan")


class CheckpointDB(Base):
    __tablename__ = "checkpoints"
    __table_args__ = (
        Index("idx_checkpoints_job", "job_id"),
        UniqueConstraint("job_id", "phase", name="uq_checkpoints_job_phase"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    phase = Column(String(50), nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobDB", back_populates="checkpoints")


class EmbeddingDB(Base):
    """pgvector embeddings for profile/code similarity search."""
    __tablename__ = "embeddings"
    __table_args__ = (
        Index("idx_embeddings_job", "job_id"),
        Index("idx_embeddings_kind", "kind"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String(20), nullable=False)  # 'profile' or 'code'
    content_key = Column(String(255), nullable=False)  # e.g. skill name, file path
    content_text = Column(Text, nullable=False)
    extra_data = Column("metadata", JSONB, server_default="{}")
    embedding = Column(Vector(1536), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobDB")
