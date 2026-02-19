"""Embedding infrastructure 어댑터."""

__all__: list[str] = []

try:
    from infrastructure.embedding.embedding_service import EmbeddingService
    __all__ += ["EmbeddingService"]
except ImportError:
    pass

try:
    from infrastructure.embedding.pgvector_store import ChunkKind, EmbeddingRecord, PgvectorStore
    __all__ += ["PgvectorStore", "ChunkKind", "EmbeddingRecord"]
except ImportError:
    pass
