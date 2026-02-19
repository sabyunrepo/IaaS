"""
PgvectorStore / EmbeddingService 테스트

DB 연결이 필요한 테스트는 skip하고, 순수 로직만 테스트한다.
"""
import pytest

psycopg = pytest.importorskip("psycopg")

from infrastructure.embedding.embedding_service import EmbeddingService  # noqa: E402
from infrastructure.embedding.pgvector_store import (  # noqa: E402
    ChunkKind,
    EmbeddingRecord,
    PgvectorStore,
)


# ---------------------------------------------------------------------------
# EmbeddingService
# ---------------------------------------------------------------------------


class TestEmbeddingServiceDimensions:
    def test_default_dimensions(self):
        svc = EmbeddingService(api_key="test-key")
        assert svc.dimensions == 1536

    def test_custom_dimensions(self):
        svc = EmbeddingService(api_key="test-key", dimensions=768)
        assert svc.dimensions == 768


class TestEmbeddingServiceEmbed:
    @pytest.mark.asyncio
    async def test_empty_string_returns_zero_vector(self):
        svc = EmbeddingService(api_key="test-key", dimensions=1536)
        result = await svc.embed("")
        assert result == [0.0] * 1536

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_zero_vector(self):
        svc = EmbeddingService(api_key="test-key", dimensions=1536)
        result = await svc.embed("   \t\n  ")
        assert result == [0.0] * 1536

    @pytest.mark.asyncio
    async def test_empty_string_length_matches_dimensions(self):
        svc = EmbeddingService(api_key="test-key", dimensions=256)
        result = await svc.embed("")
        assert len(result) == 256

    @pytest.mark.asyncio
    async def test_embed_batch_empty_list_returns_empty(self):
        svc = EmbeddingService(api_key="test-key")
        result = await svc.embed_batch([])
        assert result == []


# ---------------------------------------------------------------------------
# ChunkKind
# ---------------------------------------------------------------------------


class TestChunkKind:
    def test_code_value(self):
        assert ChunkKind.CODE == "code"
        assert ChunkKind.CODE.value == "code"

    def test_jd_value(self):
        assert ChunkKind.JD == "jd"
        assert ChunkKind.JD.value == "jd"

    def test_resume_value(self):
        assert ChunkKind.RESUME == "resume"
        assert ChunkKind.RESUME.value == "resume"

    def test_linkedin_value(self):
        assert ChunkKind.LINKEDIN == "linkedin"
        assert ChunkKind.LINKEDIN.value == "linkedin"

    def test_from_string(self):
        assert ChunkKind("code") is ChunkKind.CODE
        assert ChunkKind("jd") is ChunkKind.JD

    def test_all_members(self):
        members = {m.value for m in ChunkKind}
        assert members == {"code", "jd", "resume", "linkedin"}


# ---------------------------------------------------------------------------
# EmbeddingRecord
# ---------------------------------------------------------------------------


class TestEmbeddingRecord:
    def test_create_record(self):
        record = EmbeddingRecord(
            id="rec-1",
            job_id="job-abc",
            kind=ChunkKind.CODE,
            content="def foo(): pass",
            metadata={"file": "main.py", "line": 1},
            embedding=[0.1, 0.2, 0.3],
        )
        assert record.id == "rec-1"
        assert record.job_id == "job-abc"
        assert record.kind == ChunkKind.CODE
        assert record.content == "def foo(): pass"
        assert record.metadata == {"file": "main.py", "line": 1}
        assert record.embedding == [0.1, 0.2, 0.3]
        assert record.similarity == 0.0  # 기본값

    def test_create_record_with_similarity(self):
        record = EmbeddingRecord(
            id="rec-2",
            job_id="job-xyz",
            kind=ChunkKind.JD,
            content="Senior Engineer",
            metadata={},
            embedding=[],
            similarity=0.95,
        )
        assert record.similarity == 0.95

    def test_record_is_frozen(self):
        """EmbeddingRecord는 불변(frozen=True)이어야 한다."""
        record = EmbeddingRecord(
            id="rec-3",
            job_id="job-1",
            kind=ChunkKind.RESUME,
            content="test",
            metadata={},
            embedding=[],
        )
        with pytest.raises((AttributeError, TypeError)):
            record.id = "new-id"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# PgvectorStore.compute_similarity
# ---------------------------------------------------------------------------


class TestComputeSimilarity:
    """DB 없이 순수 Python 연산만 테스트."""

    @pytest.fixture
    def store(self) -> PgvectorStore:
        return PgvectorStore(dsn="postgresql://dummy/dummy")

    @pytest.mark.asyncio
    async def test_identical_vectors_return_one(self, store: PgvectorStore):
        vec = [1.0, 0.0, 0.0]
        result = await store.compute_similarity(vec, vec)
        assert abs(result - 1.0) < 1e-9

    @pytest.mark.asyncio
    async def test_orthogonal_vectors_return_zero(self, store: PgvectorStore):
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [0.0, 1.0, 0.0]
        result = await store.compute_similarity(vec_a, vec_b)
        assert abs(result - 0.0) < 1e-9

    @pytest.mark.asyncio
    async def test_opposite_vectors_return_minus_one(self, store: PgvectorStore):
        vec_a = [1.0, 0.0]
        vec_b = [-1.0, 0.0]
        result = await store.compute_similarity(vec_a, vec_b)
        assert abs(result - (-1.0)) < 1e-9

    @pytest.mark.asyncio
    async def test_zero_vector_a_returns_zero(self, store: PgvectorStore):
        zero = [0.0, 0.0, 0.0]
        other = [1.0, 2.0, 3.0]
        result = await store.compute_similarity(zero, other)
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_zero_vector_b_returns_zero(self, store: PgvectorStore):
        other = [1.0, 2.0, 3.0]
        zero = [0.0, 0.0, 0.0]
        result = await store.compute_similarity(other, zero)
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_both_zero_vectors_return_zero(self, store: PgvectorStore):
        zero = [0.0, 0.0]
        result = await store.compute_similarity(zero, zero)
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_partial_similarity(self, store: PgvectorStore):
        """45도 각도 → cos(45°) ≈ 0.7071"""
        vec_a = [1.0, 0.0]
        vec_b = [1.0, 1.0]
        result = await store.compute_similarity(vec_a, vec_b)
        expected = 1.0 / (2.0**0.5)
        assert abs(result - expected) < 1e-9

    @pytest.mark.asyncio
    async def test_high_dimensional_vectors(self, store: PgvectorStore):
        """1536차원 동일 벡터 → 유사도 1.0"""
        vec = [0.1] * 1536
        result = await store.compute_similarity(vec, vec)
        assert abs(result - 1.0) < 1e-6
