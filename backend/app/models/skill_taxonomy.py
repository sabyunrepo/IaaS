"""
backend/app/models/skill_taxonomy.py
Skill Taxonomy SQLAlchemy 모델 — Hybrid Skill Graph Foundation

3-Tier 스킬 정규화 시스템의 DB 기반:
1. Alias Lookup (O(1)) — skill_aliases 테이블
2. Embedding Similarity (O(log n)) — pgvector HNSW 인덱스
3. LLM Classification (fallback) — 새 스킬 자동 등록

Taxonomy Source: MIND Tech Ontology (3,333 스킬, 974 개념, 10,897 관계)
"""
import uuid

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Index, Integer, String,
    UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship

from .database import Base


class SkillTaxonomyDB(Base):
    """정규 스킬 택소노미 — canonical skill names + 메타데이터"""
    __tablename__ = "skill_taxonomy"
    __table_args__ = (
        Index("idx_taxonomy_canonical", "canonical_name", unique=True),
        Index("idx_taxonomy_category", "category"),
        Index("idx_taxonomy_domain", "domain"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_name = Column(String(255), unique=True, nullable=False)  # "React"
    category = Column(String(50))       # language/framework/tool/platform/concept
    domain = Column(String(50))         # frontend/backend/devops/ml/data
    embedding = Column(Vector(384))     # all-MiniLM-L6-v2 임베딩
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    aliases = relationship("SkillAliasDB", back_populates="taxonomy", cascade="all, delete-orphan")
    outgoing_relations = relationship(
        "SkillRelationshipDB",
        foreign_keys="SkillRelationshipDB.source_id",
        back_populates="source",
        cascade="all, delete-orphan",
    )
    incoming_relations = relationship(
        "SkillRelationshipDB",
        foreign_keys="SkillRelationshipDB.target_id",
        back_populates="target",
    )


class SkillAliasDB(Base):
    """스킬 동의어 — "react.js", "ReactJS", "react" → taxonomy_id(React)"""
    __tablename__ = "skill_aliases"
    __table_args__ = (
        UniqueConstraint("alias", name="uq_skill_alias"),
        Index("idx_alias_lookup", "alias"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    taxonomy_id = Column(Integer, ForeignKey("skill_taxonomy.id", ondelete="CASCADE"), nullable=False)
    alias = Column(String(255), nullable=False)  # lowercase normalized
    source = Column(String(20), nullable=False, default="ontology")  # "ontology" | "auto_learned" | "manual"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    taxonomy = relationship("SkillTaxonomyDB", back_populates="aliases")


class SkillRelationshipDB(Base):
    """스킬 관계 — React→JavaScript (implies), Docker→Linux (requires)"""
    __tablename__ = "skill_relationships"
    __table_args__ = (
        Index("idx_skill_rel_source", "source_id"),
        Index("idx_skill_rel_target", "target_id"),
        Index("idx_skill_rel_type", "relation_type"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("skill_taxonomy.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(Integer, ForeignKey("skill_taxonomy.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(30), nullable=False)  # "implies" | "requires" | "related_to" | "subset_of"
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("SkillTaxonomyDB", foreign_keys=[source_id], back_populates="outgoing_relations")
    target = relationship("SkillTaxonomyDB", foreign_keys=[target_id], back_populates="incoming_relations")
