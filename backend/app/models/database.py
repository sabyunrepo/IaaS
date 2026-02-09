"""
backend/app/models/database.py
SQLAlchemy ORM 모델 (PostgreSQL 테이블)
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text, BigInteger,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
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
    candidates = relationship("CandidateDB", back_populates="user")
    job_descriptions = relationship("JobDescriptionDB", back_populates="user")


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
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"))
    jd_id = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    user = relationship("UserDB", back_populates="jobs")
    checkpoints = relationship("CheckpointDB", back_populates="job", cascade="all, delete-orphan")
    analysis_logs = relationship("AnalysisLogDB", back_populates="job", cascade="all, delete-orphan")


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


class AnalysisLogDB(Base):
    """Activity 실행 로그 - 분석 중간 결과 및 진행 상황 추적."""
    __tablename__ = "analysis_logs"
    __table_args__ = (
        Index("idx_analysis_logs_job", "job_id"),
        Index("idx_analysis_logs_activity", "activity_name"),
        Index("idx_analysis_logs_phase", "phase"),
        Index("idx_analysis_logs_created", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    activity_name = Column(String(100), nullable=False)  # 'document_analysis', 'code_analysis', etc.
    phase = Column(String(50), nullable=False)  # 'enriching', 'analyzing', 'generating'
    log_type = Column(String(20), nullable=False)  # 'start', 'progress', 'result', 'error'
    message = Column(Text)
    data = Column(JSONB, server_default="{}")  # Structured analysis data
    duration_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobDB", back_populates="analysis_logs")


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


# ============================================
# Knowledge Graph Tables
# ============================================

class KGNodeDB(Base):
    """Knowledge Graph nodes for entity storage."""
    __tablename__ = "kg_nodes"
    __table_args__ = (
        Index("idx_kg_nodes_job", "job_id"),
        Index("idx_kg_nodes_type", "entity_type"),
        Index("idx_kg_nodes_job_type", "job_id", "entity_type"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    entity_type = Column(String(100), nullable=False)  # 'Skill', 'CodePattern', 'Requirement', etc.
    name = Column(String(500), nullable=False)  # Entity name for quick lookup
    properties = Column(JSONB, nullable=False, server_default="{}")  # Entity attributes
    embedding = Column(Vector(1536))  # Optional: for hybrid graph+vector search
    provenance = Column(JSONB)  # W3C PROV-O tracking: source, extraction_method, confidence
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobDB")
    outgoing_edges = relationship("KGEdgeDB", foreign_keys="KGEdgeDB.source_id", back_populates="source_node")
    incoming_edges = relationship("KGEdgeDB", foreign_keys="KGEdgeDB.target_id", back_populates="target_node")


class KGEdgeDB(Base):
    """Knowledge Graph edges for relationship storage."""
    __tablename__ = "kg_edges"
    __table_args__ = (
        Index("idx_kg_edges_job", "job_id"),
        Index("idx_kg_edges_source", "source_id"),
        Index("idx_kg_edges_target", "target_id"),
        Index("idx_kg_edges_relation", "relation_type"),
        Index("idx_kg_edges_job_relation", "job_id", "relation_type"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("kg_nodes.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("kg_nodes.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(100), nullable=False)  # 'has_skill', 'demonstrated_by', 'matches', etc.
    properties = Column(JSONB, server_default="{}")  # Relation attributes
    confidence = Column("confidence", BigInteger, nullable=False, default=100)  # 0-100 scale
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobDB")
    source_node = relationship("KGNodeDB", foreign_keys=[source_id], back_populates="outgoing_edges")
    target_node = relationship("KGNodeDB", foreign_keys=[target_id], back_populates="incoming_edges")


class ClaimEvidenceDB(Base):
    """Claim-Evidence verification records for interview probing."""
    __tablename__ = "claim_evidence"
    __table_args__ = (
        Index("idx_claim_evidence_job", "job_id"),
        Index("idx_claim_evidence_type", "evidence_type"),
        Index("idx_claim_evidence_strength", "evidence_strength"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    claim_node_id = Column(UUID(as_uuid=True), ForeignKey("kg_nodes.id", ondelete="SET NULL"))
    evidence_node_id = Column(UUID(as_uuid=True), ForeignKey("kg_nodes.id", ondelete="SET NULL"))
    evidence_type = Column(String(50), nullable=False)  # 'supporting', 'contradicting', 'neutral', 'missing'
    evidence_strength = Column("evidence_strength", BigInteger, nullable=False)  # 0-100 scale
    analysis = Column(Text)  # LLM analysis of claim vs evidence
    recommended_probe = Column(Text)  # Suggested interview question to verify claim
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("JobDB")
    claim_node = relationship("KGNodeDB", foreign_keys=[claim_node_id])
    evidence_node = relationship("KGNodeDB", foreign_keys=[evidence_node_id])


# ============================================
# Candidate & JD Tables (Multi-Tenant)
# ============================================

class CandidateDB(Base):
    """후보자 1급 엔터티 (JD-agnostic 프로필)"""
    __tablename__ = "candidates"
    __table_args__ = (
        Index("idx_candidates_user", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    experience_years = Column(Integer)
    experience_level = Column(String(50))
    skills = Column(ARRAY(Text), nullable=False, server_default="{}")
    github_username = Column(String(255))
    linkedin_url = Column(String(2048))
    profile_data = Column(JSONB, nullable=False, server_default="{}")
    data_completeness = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("UserDB", back_populates="candidates")
    matches = relationship("CandidateJDMatchDB", back_populates="candidate", cascade="all, delete-orphan")
    candidate_embeddings = relationship("CandidateEmbeddingDB", back_populates="candidate", cascade="all, delete-orphan")


class JobDescriptionDB(Base):
    """JD 1급 엔터티"""
    __tablename__ = "job_descriptions"
    __table_args__ = (
        Index("idx_jd_user", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    required_skills = Column(ARRAY(Text), server_default="{}")
    preferred_skills = Column(ARRAY(Text), server_default="{}")
    jd_text = Column(Text)
    jd_analysis = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("UserDB", back_populates="job_descriptions")
    matches = relationship("CandidateJDMatchDB", back_populates="jd", cascade="all, delete-orphan")


class CandidateJDMatchDB(Base):
    """후보자-JD 매칭 결과 (사전계산)"""
    __tablename__ = "candidate_jd_matches"
    __table_args__ = (
        UniqueConstraint("candidate_id", "jd_id", name="uq_candidate_jd_match"),
        Index("idx_match_by_jd", "jd_id", "overall_match_score"),
        Index("idx_match_by_candidate", "candidate_id", "overall_match_score"),
        Index("idx_match_user", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    jd_id = Column(UUID(as_uuid=True), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    overall_match_score = Column(Float, default=0.0)
    skill_match_score = Column(Float, default=0.0)
    skill_matches = Column(JSONB, server_default="{}")
    gaps = Column(JSONB, server_default="[]")
    match_explanation = Column(Text)
    confidence_level = Column(String(10), default="medium")
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("CandidateDB", back_populates="matches")
    jd = relationship("JobDescriptionDB", back_populates="matches")


class CandidateEmbeddingDB(Base):
    """후보자 임베딩 (프로필 시맨틱 검색)"""
    __tablename__ = "candidate_embeddings"
    __table_args__ = (
        UniqueConstraint("candidate_id", "embedding_type", name="uq_candidate_embedding"),
        Index("idx_candidate_emb_user", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    embedding_type = Column(String(50))  # 'profile_summary', 'skills'
    embedding = Column(Vector(384))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    candidate = relationship("CandidateDB", back_populates="candidate_embeddings")
