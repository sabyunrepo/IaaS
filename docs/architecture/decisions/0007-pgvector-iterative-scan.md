---
title: "ADR-0007: pgvector iterative_scan 활성화"
type: adr
status: proposed
date: 2026-02-19
decision-makers: ["@sabyun"]
related-adrs: []
impacts: ["[[infrastructure/vector-search/MOC]]"]
tags: [pgvector, vector-search, performance]
---

# ADR-0007: pgvector iterative_scan 활성화

## 상태

proposed

---

## 컨텍스트

`plan/v5-design/phase2-infrastructure.md` §13 및
`docs/plans/2026-02-19-architecture-documentation-design.md` §6.1 기준:

Jittda v5.0의 벡터 검색 전략은 다음 세 가지 소스의 임베딩을 pgvector에 저장한다:

| 소스 | 청크 단위 | 벡터 용도 |
|------|----------|----------|
| 코드 | 함수/클래스 (AST 기반) | 코드 의미 유사도 검색 |
| JD | 섹션별 (자격요건, 우대사항) | JD-Repo 유사도 비교 (Funnel Stage 3) |
| 이력서 | 경력/프로젝트별 | 후보 프로필 매핑 |
| LinkedIn | 프로필 섹션별 | 경력 검증 |

임베딩 모델은 `text-embedding-3-small` (Vector 1536차원)을 사용하며,
인덱스는 HNSW(Hierarchical Navigable Small World)를 채택한다.

### pgvector 0.8.x의 iterative_scan 기능

v5 초기 설계서는 pgvector 버전을 명시하지 않았으나,
`docs/plans/2026-02-19-architecture-documentation-design.md` §6.1에서
**pgvector 0.8.1 + `iterative_scan` 9.4배 성능 향상**이 확인되었다.

pgvector 0.8.x에서 HNSW 인덱스에 대해 `iterative_scan`을 활성화하면:
- 검색 정밀도와 recall을 희생하지 않고 처리량을 크게 향상
- `relaxed_order` 모드: 결과 순서가 완벽히 정렬되지 않을 수 있으나,
  면접 질문 생성 시나리오에서는 허용 가능한 트레이드오프

Jittda Live의 실시간 RAG 파이프라인은 STT 텍스트가 들어온 뒤
20ms 이내에 관련 코드 청크를 검색해야 한다.
기본 설정으로는 이 레이턴시 요건을 만족하기 어렵다.

---

## 검토한 옵션

### 옵션 A: 기존 기본 설정 유지 (iterative_scan 비활성화)

**설명**: pgvector의 기본 HNSW 검색 설정 그대로 사용.

**장점**:
- 별도 설정 없이 동작
- 결과 정렬 순서 보장

**단점**:
- 대용량 코드 청크 인덱스에서 검색 지연 증가
- 실시간 면접 파이프라인(20ms 목표)에서 병목 가능성
- 9.4x 성능 이득을 포기

---

### 옵션 B: iterative_scan 활성화 (선택)

**설명**: `init.sql`에 `SET hnsw.iterative_scan = 'relaxed_order'`를 추가하고
HNSW 인덱스 파라미터를 최적화한다.

**장점**:
- 공식 벤치마크 기준 9.4x 처리량 향상
- Jittda Live의 20ms 로컬 RAG 쿼리 목표 달성 가능성
- 코드 청크 + JD + 이력서 병합 인덱스에서의 대규모 쿼리 효율 향상

**단점**:
- `relaxed_order` 모드 — 결과 정렬이 완전히 보장되지 않음
  (면접 질문 생성 시나리오에서 코사인 유사도 최상위 3-5개 검색이므로 허용 가능)
- PostgreSQL 세션 또는 트랜잭션 단위 설정이므로 연결 풀링 환경에서 주의 필요

---

## 결정

**옵션 B 채택: iterative_scan 활성화**

Jittda의 벡터 검색은 정렬 순서의 완벽성보다 **처리량과 레이턴시**가 핵심이다.
면접 질문 생성 및 JD-Repo 유사도 계산 시나리오에서는
상위 3~5개 결과를 빠르게 반환하는 것이 중요하며,
`relaxed_order`에 의한 미세한 순서 차이는 실질적인 품질 저하를 유발하지 않는다.

9.4x 성능 향상은 실시간 RAG 파이프라인 목표(20ms) 달성에 직접 기여한다.

---

## 결과

### init.sql 변경 사항

```sql
-- infra/postgres/init.sql에 추가
-- pgvector iterative_scan 활성화 (0.8.x)
SET hnsw.iterative_scan = 'relaxed_order';

-- HNSW 인덱스 (1536차원, text-embedding-3-small)
CREATE INDEX IF NOT EXISTS code_chunks_embedding_idx
ON code_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- JD/이력서/LinkedIn 임베딩 인덱스
CREATE INDEX IF NOT EXISTS embeddings_embedding_idx
ON embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### pgvector_store 쿼리 패턴

```python
# infrastructure/embedding/pgvector_store.py
async def search_similar_chunks(
    query_embedding: list[float],
    kind: str,
    job_id: str,
    top_k: int = 5,
) -> list[dict]:
    """HNSW iterative_scan 기반 벡터 유사도 검색"""
    result = await db.fetch_all(
        """
        SELECT id, content, metadata, embedding <=> :query_vec AS distance
        FROM embeddings
        WHERE kind = :kind AND job_id = :job_id
        ORDER BY embedding <=> :query_vec
        LIMIT :top_k
        """,
        {
            "query_vec": str(query_embedding),
            "kind": kind,
            "job_id": job_id,
            "top_k": top_k,
        },
    )
    return [dict(row) for row in result]
```

### 버전 고정

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    # pgvector 0.8.1 이상 포함된 공식 이미지 사용
```

### 적용 대상 Linear 티켓

- JIT-99: pgvector 확장 구현 시 iterative_scan 설정 포함
- JIT-111~112: OutputAssembler 4대 지표 산출 시 벡터 검색 사용

### 참조

- `plan/v5-design/phase2-infrastructure.md` §13.3 JD-Repo 유사도 비교
- `docs/plans/2026-02-19-architecture-documentation-design.md` §6.1, §6.2
- `[[infrastructure/vector-search/pgvector-setup]]`
- `[[infrastructure/vector-search/embedding-strategy]]`
