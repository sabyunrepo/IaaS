---
title: "Vector Similarity"
type: component
layer: domain
parent: "[[domain/funnel-selection/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-90", "JIT-99"]
depends-on: ["[[infrastructure/vector-search/MOC]]"]
---

# Vector Similarity (Stage 3)

## 목적

Relevance Scoring을 통과한 레포의 README/Description을 **JD 전문 텍스트와 벡터 유사도로 비교**하여 최종 포함 여부를 결정한다. 기술스택 키워드 매칭만으로는 잡을 수 없는 의미론적 유사성을 포착한다.

## 동작 원리

1. JD 전문 텍스트를 임베딩하여 벡터화
2. 레포의 README + Description을 임베딩하여 벡터화
3. pgvector의 코사인 유사도 계산
4. 유사도 >= `vector_similarity_min (0.60)`이면 포함

## 임계값 판정 함수

```python
# domain/matching/funnel_rules.py

def stage3_should_include(
    similarity: float,
    config: FunnelConfig,
) -> bool:
    """Stage 3: 벡터 유사도 임계값 판정

    Args:
        similarity: pgvector 코사인 유사도 (0.0 ~ 1.0)
        config: FunnelConfig (vector_similarity_min 기본값 0.60)

    Returns:
        True이면 심층 분석 대상에 포함
    """
    return similarity >= config.vector_similarity_min
```

## 임베딩 전략

| 대상 | 임베딩 내용 | 이유 |
|------|-------------|------|
| JD 벡터 | `job_title + requirements + tech_stack` | JD의 핵심 요구사항 압축 |
| 레포 벡터 | `repo_name + description + README[:2000]` | 레포가 다루는 도메인/문제 요약 |

임베딩 모델 및 저장소는 Infrastructure 레이어([[infrastructure/vector-search/MOC]])에서 담당한다.

## pgvector 쿼리 예시

```sql
-- pgvector 코사인 유사도 기반 검색
SELECT repo_id, 1 - (embedding <=> $1::vector) AS similarity
FROM repo_embeddings
WHERE 1 - (embedding <=> $1::vector) >= 0.60
ORDER BY similarity DESC
LIMIT 5;
```

## 최종 선별 결과

Stage 3까지 통과한 레포는 `FunnelConfig.top_k` (기본값 5)개로 제한된다. 이 레포들만 AST 분석, 코드 복잡도 산출, 질문 생성의 심층 분석 대상이 된다.

## 입력 / 출력

| | 타입 | 설명 |
|--|------|------|
| 입력 | `float` | pgvector가 계산한 코사인 유사도 |
| 입력 | `FunnelConfig` | `vector_similarity_min` 임계값 포함 |
| 출력 | `bool` | True = 심층 분석 포함, False = 제외 |

## 의존성

- pgvector 벡터 저장 및 쿼리: [[infrastructure/vector-search/MOC]] (JIT-99)
- 레포 임베딩 생성: Infrastructure 레이어 GitHub 어댑터 (JIT-92)
