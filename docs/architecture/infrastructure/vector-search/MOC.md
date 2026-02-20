---
title: "Vector Search"
type: moc
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[infrastructure/MOC]]"
tags: [pgvector, embedding, hnsw, rag, vector-search]
---

# Vector Search

> pgvector 0.8.x 기반 벡터 유사도 검색 계층.
> 코드 청크, JD, 이력서, LinkedIn 프로필의 임베딩을 저장하고
> 면접 질문 생성 및 JD-Repo Funnel Selection에 사용한다.

## 역할

- `text-embedding-3-small` 모델로 텍스트 임베딩 생성 (1536차원)
- HNSW 인덱스 + `iterative_scan` 활성화로 실시간 RAG 20ms 목표 달성
- JD-Repo 코사인 유사도 비교 (Funnel Stage 3)
- 코드 청크, JD, 이력서, LinkedIn 4종 소스 통합 관리

## 문서 목록

| 문서 | 내용 |
|------|------|
| [[vector-search/pgvector-setup\|pgvector Setup]] | init.sql, HNSW 인덱스, iterative_scan 설정 |
| [[vector-search/embedding-strategy\|Embedding Strategy]] | 청크 전략, 임베딩 모델, 배치 처리 |

## 아키텍처 위치

```
infrastructure/embedding/
├── pgvector_store.py        # 저장/조회 포트 구현
├── embedder.py              # text-embedding-3-small 래핑
└── chunker.py               # AST 기반 코드 청킹

infra/postgres/
└── init.sql                 # pgvector CREATE EXTENSION + HNSW 인덱스
```

## 임베딩 소스 요약

| 소스 | 청크 단위 | 벡터 용도 |
|------|----------|----------|
| 코드 | 함수/클래스 (AST 기반) | 코드 의미 유사도 |
| JD | 섹션별 (자격요건, 우대사항) | JD-Repo 유사도 (Funnel Stage 3) |
| 이력서 | 경력/프로젝트별 | 후보 프로필 매핑 |
| LinkedIn | 프로필 섹션별 | 경력 검증 |

## 관련 ADR

- [[decisions/0007-pgvector-iterative-scan|ADR-0007: pgvector iterative_scan 활성화]]

## 관련 문서

```dataview
TABLE status, updated, tags
FROM "docs/architecture/infrastructure/vector-search"
WHERE file.name != "MOC"
SORT file.name ASC
```
