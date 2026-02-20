---
title: "전문성 지표 (Mastery Metric)"
type: component
layer: domain
parent: "[[domain/scoring-system/MOC]]"
depends-on:
  - "[[infrastructure/tree-sitter-ast/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# 전문성 지표 (Mastery Metric)

> 전체 최종 점수에서 **30%** 기여.
> 해당 기술 스택을 얼마나 깊이 이해하고 숙련되게 활용하는지를 측정한다.
> API 활용 깊이, 디자인 패턴 사용, SOLID 준수율, 기술 다양성 4축을 평가한다.

## 세부 항목 및 가중치

| 세부 지표 | 내부 가중치 | 측정 도구 | Worker | 설명 |
|----------|------------|---------|--------|------|
| API 활용 깊이 | 35% | AST 분석 | W10 | 라이브러리/프레임워크 고급 API 사용 빈도 및 수준 |
| 디자인 패턴 사용 | 25% | AST 패턴 감지 | W11 | GoF 패턴, 아키텍처 패턴(MVC, CQRS 등) 활용 여부 |
| SOLID 준수율 | 20% | 아키텍처 분석 | W11 | 단일 책임, 개방-폐쇄, 의존성 역전 등 준수도 |
| 기술스택 다양성 | 20% | 스킬 추출 | W9 | 사용 언어/프레임워크/DB/클라우드 등의 폭과 깊이 |

## 기술 스택 Depth 레벨

API 활용 깊이를 판정할 때 아래 4단계 수준으로 분류한다:

| 레벨 | 설명 | 예시 | 점수 가중치 |
|------|------|------|------------|
| `beginner` | 기본 CRUD, 단순 API 호출 | `requests.get()`, `list.append()` | 1× |
| `intermediate` | 미들웨어, 훅, 컨텍스트 매니저 | Django middleware, `__enter__/__exit__` | 2× |
| `advanced` | 비동기, 메타클래스, 제너레이터 활용 | `asyncio`, `__init_subclass__`, `yield from` | 3× |
| `expert` | 프레임워크 내부 확장, 커스텀 프로토콜 | Pydantic `__get_validators__`, LangGraph 커스텀 노드 | 4× |

## AST 기반 패턴 감지

[[infrastructure/tree-sitter-ast/MOC]] 에서 파싱된 AST를 받아 다음 패턴을 감지한다:

```
감지 대상 패턴:
  GoF 생성 패턴: Factory, Builder, Singleton, Prototype
  GoF 구조 패턴: Adapter, Decorator, Facade, Proxy
  GoF 행동 패턴: Observer, Strategy, Command, Iterator, State
  아키텍처 패턴: Repository, CQRS, Event Sourcing, DDD Aggregate
  비동기 패턴: async/await, Promise chaining, Actor Model
```

## 산출 수학적 모델

```python
# domain/scoring/metrics/mastery.py

from dataclasses import dataclass
from typing import Literal

ProficiencyLevel = Literal["beginner", "intermediate", "advanced", "expert"]
LEVEL_WEIGHT: dict[ProficiencyLevel, float] = {
    "beginner": 1.0,
    "intermediate": 2.0,
    "advanced": 3.0,
    "expert": 4.0,
}


def calculate_api_depth_score(
    api_usages: list[tuple[str, ProficiencyLevel, int]],
    # (api_name, level, count)
) -> float:
    """API 활용 깊이 점수: 레벨 가중치 × 사용 횟수 합산 후 정규화."""
    raw = sum(LEVEL_WEIGHT[level] * count for _, level, count in api_usages)
    # 최대 기준값(예: 400점) 대비 정규화
    return min(100.0, raw / 4.0)


def calculate_mastery_score(
    api_depth_score: float,       # 0-100
    pattern_score: float,         # 0-100 (감지된 패턴 수 기반)
    solid_score: float,           # 0-100 (SOLID 위반 역산)
    stack_diversity_score: float, # 0-100 (스킬 추출 기반)
) -> float:
    """전문성 지표 최종 점수 산출."""
    return (
        api_depth_score * 0.35
        + pattern_score * 0.25
        + solid_score * 0.20
        + stack_diversity_score * 0.20
    )
```

## SkillAssessment 모델 연동

```python
# domain/analysis/models.py (발췌)
class SkillAssessment(BaseModel):
    model_config = ConfigDict(strict=True)

    skill_name: str
    proficiency: str  # beginner | intermediate | advanced | expert
    evidence_count: int = Field(ge=0)
    evidence_sources: list[str]  # ["github:repo1", "linkedin", "resume"]
    confidence: str  # "high" | "medium" | "low"
```

각 스킬의 `proficiency`와 `evidence_count`가 전문성 점수 산출의 직접 입력값이 된다.

## 전체 전문성 점수 기여

```python
# domain/scoring/calculator.py (발췌)
Score_mastery = calculate_mastery_score(
    api_depth_score=api_depth,
    pattern_score=pattern_count / MAX_PATTERNS * 100,
    solid_score=solid_compliance_rate * 100,
    stack_diversity_score=stack_diversity,
)
# 최종 점수 기여: Score_mastery * 0.30
```

## 인프라 의존성

[[infrastructure/tree-sitter-ast/MOC]] 에서 다음 정보를 받아 사용한다:

- AST 노드 목록 (import, call, class, function)
- 라이브러리별 API 호출 목록 + 호출 깊이
- 클래스/함수 구조 (SOLID 분석 기반)

Domain 계층은 AST 파싱을 직접 수행하지 않는다 (DDD 규칙).
