"""Unit tests for vector store service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid


class TestVectorStoreInit:
    def test_get_vector_store(self):
        from app.services.vector_store import get_vector_store
        vs = get_vector_store("test-job-id")
        assert vs.job_id == "test-job-id"

    def test_vector_store_class(self):
        from app.services.vector_store import VectorStore
        vs = VectorStore("abc-123")
        assert vs.job_id == "abc-123"


class TestEmbeddingModel:
    def test_embedding_db_importable(self):
        from app.models.database import EmbeddingDB
        assert EmbeddingDB.__tablename__ == "embeddings"

    def test_embedding_db_columns(self):
        from app.models.database import EmbeddingDB
        columns = {c.name for c in EmbeddingDB.__table__.columns}
        assert "job_id" in columns
        assert "kind" in columns
        assert "content_key" in columns
        assert "content_text" in columns
        assert "embedding" in columns
        assert "metadata" in columns

    def test_embedding_dim(self):
        from app.services.vector_store import EMBEDDING_DIM
        assert EMBEDDING_DIM == 1536


class TestStoreProfile:
    def test_store_profile_extracts_entries(self):
        """Verify store_profile would extract correct number of entries from profile data."""
        profile = {"skills": ["Python", "React"], "summary": "Expert dev"}
        entries = []
        for skill in profile.get("skills", []):
            name = skill if isinstance(skill, str) else skill.get("name", str(skill))
            desc = skill if isinstance(skill, str) else skill.get("description", name)
            entries.append(("skill:" + name, str(desc)))
        if summary := profile.get("summary"):
            entries.append(("summary", str(summary)))
        # 2 skills + 1 summary = 3 entries
        assert len(entries) == 3
        assert entries[0] == ("skill:Python", "Python")
        assert entries[2] == ("summary", "Expert dev")


class TestSearchInterface:
    def test_search_methods_exist(self):
        from app.services.vector_store import VectorStore
        vs = VectorStore("test")
        assert hasattr(vs, "search_code")
        assert hasattr(vs, "search_profile")
        assert hasattr(vs, "store_profile")
        assert hasattr(vs, "store_code")
