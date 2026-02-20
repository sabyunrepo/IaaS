"""
PgvectorStore — pgvector 기반 벡터 저장/검색 스토어.

PostgreSQL pgvector 확장으로 임베딩을 저장하고 유사도 검색을 수행한다.
"""
import json
from dataclasses import dataclass
from enum import StrEnum


class ChunkKind(StrEnum):
    """임베딩 청크 종류."""

    CODE = "code"
    JD = "jd"
    RESUME = "resume"
    LINKEDIN = "linkedin"


@dataclass(frozen=True)
class EmbeddingRecord:
    """저장된 임베딩 레코드."""

    id: str
    job_id: str
    kind: ChunkKind
    content: str
    metadata: dict
    embedding: list[float]
    similarity: float = 0.0  # 검색 시 채워짐


class PgvectorStore:
    """pgvector 기반 벡터 스토어."""

    def __init__(self, *, dsn: str, table_name: str = "embeddings", dimensions: int = 1536):
        self._dsn = dsn
        self._table_name = table_name
        self._dimensions = dimensions

    async def initialize(self) -> None:
        """테이블 및 pgvector 확장 초기화 (CREATE IF NOT EXISTS)."""
        import psycopg

        async with await psycopg.AsyncConnection.connect(self._dsn) as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{{}}',
                    embedding vector({self._dimensions})
                )
                """
            )
            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self._table_name}_job_kind
                ON {self._table_name} (job_id, kind)
                """
            )
            await conn.commit()

    async def save_embedding(
        self,
        *,
        record_id: str,
        job_id: str,
        kind: ChunkKind | str,
        content: str,
        metadata: dict,
        embedding: list[float],
    ) -> None:
        """임베딩을 저장한다 (UPSERT)."""
        import psycopg

        kind_str = kind.value if isinstance(kind, ChunkKind) else kind

        async with await psycopg.AsyncConnection.connect(self._dsn) as conn:
            await conn.execute(
                f"""
                INSERT INTO {self._table_name} (id, job_id, kind, content, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s::vector)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding
                """,
                (
                    record_id,
                    job_id,
                    kind_str,
                    content,
                    json.dumps(metadata),
                    str(embedding),
                ),
            )
            await conn.commit()

    async def search_similar(
        self,
        *,
        query_embedding: list[float],
        kind: ChunkKind | str | None = None,
        job_id: str | None = None,
        top_k: int = 10,
    ) -> list[EmbeddingRecord]:
        """코사인 유사도 기반 검색."""
        import psycopg

        conditions: list[str] = []
        filter_params: list = []

        if kind is not None:
            kind_str = kind.value if isinstance(kind, ChunkKind) else kind
            conditions.append("kind = %s")
            filter_params.append(kind_str)
        if job_id is not None:
            conditions.append("job_id = %s")
            filter_params.append(job_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # 파라미터 순서:
        #   1. similarity 계산의 embedding 인자 (%s::vector)
        #   2. WHERE 절 필터 파라미터들
        #   3. ORDER BY 절의 embedding 인자 (%s::vector)
        #   4. LIMIT 인자
        embedding_str = str(query_embedding)
        params: list = [embedding_str] + filter_params + [embedding_str, top_k]

        query = f"""
            SELECT id, job_id, kind, content, metadata,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM {self._table_name}
            {where_clause}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """

        async with await psycopg.AsyncConnection.connect(self._dsn) as conn:
            cursor = await conn.execute(query, params)
            rows = await cursor.fetchall()

        records: list[EmbeddingRecord] = []
        for row in rows:
            row_id, row_job_id, row_kind, row_content, row_metadata, row_similarity = row
            metadata_dict = row_metadata if isinstance(row_metadata, dict) else json.loads(row_metadata)
            records.append(
                EmbeddingRecord(
                    id=row_id,
                    job_id=row_job_id,
                    kind=ChunkKind(row_kind),
                    content=row_content,
                    metadata=metadata_dict,
                    embedding=[],  # 검색 결과에서는 임베딩 벡터를 반환하지 않음 (용량 절약)
                    similarity=float(row_similarity),
                )
            )
        return records

    async def compute_similarity(
        self, embedding_a: list[float], embedding_b: list[float]
    ) -> float:
        """두 임베딩 간 코사인 유사도 계산 (순수 Python)."""
        dot = sum(a * b for a, b in zip(embedding_a, embedding_b))
        norm_a = sum(a * a for a in embedding_a) ** 0.5
        norm_b = sum(b * b for b in embedding_b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
