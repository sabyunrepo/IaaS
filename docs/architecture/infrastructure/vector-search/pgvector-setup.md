---
title: "pgvector Setup"
type: component
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [pgvector, postgresql, hnsw, iterative-scan, init-sql]
parent: "[[vector-search/MOC]]"
depends-on:
  - "[[decisions/0007-pgvector-iterative-scan]]"
linear: [JIT-99]
---

# pgvector Setup

## 개요

> PostgreSQL 16 + pgvector 0.8.x 환경에서 HNSW 인덱스를 설정하고
> `iterative_scan`을 활성화하여 실시간 RAG 파이프라인의 20ms 검색 목표를 달성한다.
> 코드 청크, JD, 이력서, LinkedIn 프로필 4종 임베딩을 단일 테이블에 통합 관리한다.

## 상세 설계

### 핵심 개념

**HNSW (Hierarchical Navigable Small World)**:
- 그래프 기반 ANN(Approximate Nearest Neighbor) 알고리즘
- `m=16` (그래프 연결 수), `ef_construction=64` (인덱스 빌드 정확도)
- 삽입 속도와 검색 정확도의 균형이 pgvector 기본 설정에서 최적

**iterative_scan (pgvector 0.8.x)**:
- HNSW 인덱스에서 `relaxed_order` 모드로 처리량 9.4배 향상
- 결과 정렬 순서가 완벽히 보장되지 않으나, 상위 3~5개 검색 시나리오에서 무시 가능한 트레이드오프
- PostgreSQL 세션 단위 설정 — 연결 풀링 환경에서 각 연결에 적용

**`vector_cosine_ops`**:
- 텍스트 임베딩에 코사인 유사도 사용 (내적 vs 코사인 vs L2 중 텍스트에 최적)
- `embedding <=> :query_vec` 연산자로 코사인 거리 계산 (거리 = 1 - 유사도)

### Docker 설정

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    # pgvector 0.8.1 이상 포함된 공식 이미지 사용
    environment:
      POSTGRES_DB: jittda
      POSTGRES_USER: jittda
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - ./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
```

### 코드 예시

#### init.sql — 스키마 및 인덱스

```sql
-- infra/postgres/init.sql

-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- iterative_scan 활성화 (pgvector 0.8.x, 세션 레벨)
-- 연결 풀링 환경: pgbouncer 또는 asyncpg pool의 각 연결에 적용
SET hnsw.iterative_scan = 'relaxed_order';

-- 임베딩 통합 테이블
-- kind: 'code' | 'jd' | 'resume' | 'linkedin'
CREATE TABLE IF NOT EXISTS embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id      UUID NOT NULL,
    kind        VARCHAR(20) NOT NULL CHECK (kind IN ('code', 'jd', 'resume', 'linkedin')),
    content     TEXT NOT NULL,            -- 원본 텍스트 (청크)
    embedding   vector(1536) NOT NULL,    -- text-embedding-3-small
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW 인덱스 (코사인 거리)
CREATE INDEX IF NOT EXISTS embeddings_embedding_hnsw_idx
ON embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- job_id + kind 복합 인덱스 (필터링 성능)
CREATE INDEX IF NOT EXISTS embeddings_job_kind_idx
ON embeddings (job_id, kind);

-- 코드 청크 특화 테이블 (추가 메타데이터)
CREATE TABLE IF NOT EXISTS code_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id      UUID NOT NULL,
    file_path   TEXT NOT NULL,
    language    VARCHAR(20) NOT NULL,
    chunk_type  VARCHAR(20) NOT NULL,  -- 'function' | 'class' | 'module'
    chunk_name  TEXT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1536) NOT NULL,
    complexity  FLOAT,
    author      TEXT,
    commit_hash TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS code_chunks_embedding_hnsw_idx
ON code_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS code_chunks_job_lang_idx
ON code_chunks (job_id, language);
```

#### pgvector_store.py — 저장/조회 구현

```python
# infrastructure/embedding/pgvector_store.py
from uuid import UUID
import asyncpg

class PgVectorStore:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def save_embedding(
        self,
        job_id: UUID,
        kind: str,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> UUID:
        """임베딩 저장 후 ID 반환"""
        async with self.pool.acquire() as conn:
            # iterative_scan은 연결마다 설정 필요
            await conn.execute("SET hnsw.iterative_scan = 'relaxed_order'")
            row = await conn.fetchrow(
                """
                INSERT INTO embeddings (job_id, kind, content, embedding, metadata)
                VALUES ($1, $2, $3, $4::vector, $5)
                RETURNING id
                """,
                job_id, kind, content, str(embedding), metadata or {},
            )
            return row["id"]

    async def search_similar(
        self,
        query_embedding: list[float],
        job_id: UUID,
        kind: str,
        top_k: int = 5,
    ) -> list[dict]:
        """HNSW iterative_scan 기반 코사인 유사도 검색"""
        async with self.pool.acquire() as conn:
            await conn.execute("SET hnsw.iterative_scan = 'relaxed_order'")
            rows = await conn.fetch(
                """
                SELECT id, content, metadata,
                       1 - (embedding <=> $1::vector) AS similarity
                FROM embeddings
                WHERE kind = $2 AND job_id = $3
                ORDER BY embedding <=> $1::vector
                LIMIT $4
                """,
                str(query_embedding), kind, job_id, top_k,
            )
            return [dict(row) for row in rows]

    async def compute_jd_repo_similarity(
        self,
        jd_text: str,
        repo_readme: str,
        repo_description: str,
        embedder,
    ) -> float:
        """JD ↔ 레포 README/Description 코사인 유사도 (Funnel Stage 3)"""
        jd_embedding = await embedder.embed(jd_text)
        repo_text = f"{repo_description}\n{repo_readme}"
        repo_embedding = await embedder.embed(repo_text)

        # PostgreSQL에서 벡터 내적으로 코사인 유사도 계산
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 - ($1::vector <=> $2::vector) AS similarity",
                str(jd_embedding), str(repo_embedding),
            )
            return float(row["similarity"])
```

### 인덱스 파라미터 튜닝 가이드

| 파라미터 | 기본값 | 권장값 | 설명 |
|---------|-------|-------|------|
| `m` | 16 | 16 | 그래프 연결 수. 높을수록 recall↑, 인덱스 크기↑ |
| `ef_construction` | 64 | 64 | 빌드 정확도. 높을수록 품질↑, 빌드 시간↑ |
| `hnsw.ef_search` | 40 | 40~100 | 검색 정확도. 높을수록 recall↑, 지연↑ |

```sql
-- 검색 품질 조정 (세션 레벨)
SET hnsw.ef_search = 80;  -- 더 높은 recall 필요 시
```

### 성능 목표

| 시나리오 | 목표 레이턴시 | 비고 |
|---------|------------|------|
| 코드 청크 검색 (Jittda Live) | <20ms | iterative_scan 활성화 필수 |
| JD-Repo 유사도 (Funnel Stage 3) | <100ms | 단발성 계산 |
| 배치 임베딩 저장 | N/A | 분석 완료 후 일괄 처리 |

## 관련 문서

- 상위: [[vector-search/MOC]]
- 의존: [[decisions/0007-pgvector-iterative-scan]]
- 연관: [[vector-search/embedding-strategy]]
