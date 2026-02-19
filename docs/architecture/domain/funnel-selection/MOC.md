---
title: "Funnel Selection"
type: moc
layer: domain
parent: "[[domain/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-90"]
---

# Funnel Selection

## 개요

Funnel Selection은 JD 분석 결과를 기반으로 **후보자의 전체 레포지토리 목록에서 심층 분석할 상위 3-5개 프로젝트를 추려내는** 3단계 필터링 아키텍처다.

### 문제 (AS-IS)

모든 레포지토리를 동등하게 심층 분석하면 다음 문제가 발생한다:

- 백엔드 지원자의 3년 전 React 토이 프로젝트, 알고리즘 문제풀이 레포까지 분석
- LLM 토큰 및 분석 시간 낭비
- "질문은 JD 기반"이라는 원칙과 모순

### 해결: 3단계 Funnel Architecture

```
전체 레포 목록 (GraphQL 수집, 최대 20개)
        |
        v Stage 1: Hard Filter
[Fork 제거, 최근 push 날짜, Org 기여도, 언어 교집합]
        |
        v Stage 2: Relevance Scoring
[JD tech_stack + requirements 기반 LLM 스코어링]
        |
        v Stage 3: Vector Similarity
[JD 텍스트 <-> README/Description 벡터 유사도 (최소 0.60)]
        |
        v 상위 3-5개 프로젝트만 심층 분석
```

### FunnelConfig 핵심 파라미터

| 파라미터 | 기본값 | 의미 |
|----------|--------|------|
| `min_push_days` | 365 | 최근 1년 내 push 필수 |
| `max_repos` | 20 | GraphQL 수집 상한 |
| `top_k` | 5 | 최종 선별 개수 |
| `org_contribution_threshold` | 0.10 | Org 레포 기여도 최소 10% |
| `vector_similarity_min` | 0.60 | 벡터 유사도 최소 임계값 |

---

## 구성 요소

- [[domain/funnel-selection/hard-filter]] — Stage 1: 메타데이터 기반 하드 필터
- [[domain/funnel-selection/relevance-scoring]] — Stage 2: JD 기반 적합성 스코어링
- [[domain/funnel-selection/vector-similarity]] — Stage 3: pgvector 기반 벡터 유사도 검색

---

## Dataview

```dataview
TABLE type, status
FROM "docs/architecture/domain/funnel-selection"
WHERE type = "component"
SORT file.name ASC
```
