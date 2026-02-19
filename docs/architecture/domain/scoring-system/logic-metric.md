---
title: "논리력 지표 (Logic Metric)"
type: component
layer: domain
parent: "[[domain/scoring-system/MOC]]"
depends-on:
  - "[[infrastructure/complexity-analysis/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# 논리력 지표 (Logic Metric)

> 전체 최종 점수에서 **30%** 기여.
> 복잡한 로직을 얼마나 명확하고 간결하게 구현하는지를 측정한다.
> 복잡도가 낮을수록 고득점 — 역방향 정규화 적용.

## 세부 항목 및 가중치

| 세부 지표 | 내부 가중치 | 측정 도구 | Worker | 설명 |
|----------|------------|---------|--------|------|
| 순환 복잡도 (Cyclomatic Complexity) | 40% | Radon / Lizard | W7 | 코드 내 독립 경로 수 (McCabe CC) |
| Halstead 난이도 (D) | 30% | Radon | W7 | 연산자/피연산자 비율로 산출한 인지 부하 |
| 인지적 복잡도 (Cognitive Complexity) | 30% | SonarQube | W8 | 중첩 구조/제어 흐름의 이해 난이도 |

## 측정 도구 상세

### Radon (CC + Halstead)

```
Radon 등급 기준:
  A (CC 1-5)   — 단순, 저위험
  B (CC 6-10)  — 적당히 복잡
  C (CC 11-15) — 복잡, 주의
  D (CC 16-20) — 고위험
  E (CC 21-25) — 매우 고위험
  F (CC 26+)   — 리팩토링 필수
```

Halstead 난이도(D) = (unique_operators / 2) × (total_operands / unique_operands)

### Lizard

다중 언어 지원(Python, JS/TS, Java, Go 등). Radon이 Python 전용인 반면
Lizard는 혼합 스택 레포에서 CC를 일관되게 추출할 때 사용.

### SonarQube (인지적 복잡도)

중첩 if/for/while, 재귀, 논리 연산자 등에 가중치를 부여하는
SonarSource의 고유 메트릭. McCabe CC보다 실제 가독성 난이도를 더 잘 반영.

## 산출 수학적 모델

```python
# domain/scoring/metrics/logic.py

def calculate_logic_score(
    cc_avg: float,         # 평균 순환 복잡도
    halstead_d: float,     # Halstead 난이도 평균
    cognitive_cc: float,   # SonarQube 인지적 복잡도 평균
    a: float = 0.1,        # CC 감쇠 계수
    b: float = 0.05,       # Halstead 감쇠 계수
) -> float:
    """
    복잡도가 낮을수록 고득점 — 역방향 정규화.
    각 세부 지표를 정규화 후 내부 가중치로 합산.
    """
    # 순환 복잡도: 역시그모이드 변환 (높은 CC → 낮은 점수)
    score_cc = 1 / (1 + a * cc_avg) * 100

    # Halstead 난이도: 역변환
    score_halstead = 1 / (1 + b * halstead_d) * 100

    # 인지적 복잡도: 역변환 (SonarQube 기준 20 이상 = 고위험)
    score_cognitive = max(0.0, 100.0 - cognitive_cc * 3)

    # 내부 가중치 합산
    return (
        score_cc * 0.40
        + score_halstead * 0.30
        + score_cognitive * 0.30
    )
```

## 전체 논리력 점수 기여

```python
# domain/scoring/calculator.py (발췌)
Score_logic = calculate_logic_score(
    cc_avg=metrics.cyclomatic_complexity,
    halstead_d=metrics.halstead_difficulty,
    cognitive_cc=metrics.cognitive_complexity,
)
# 최종 점수 기여: Score_logic * 0.30
```

## 인프라 의존성

[[infrastructure/complexity-analysis/MOC]] 에서 다음 측정값을 받아 사용한다:

- `cyclomatic_complexity` (float) — Radon/Lizard 평균 CC
- `halstead_difficulty` (float) — Radon Halstead D
- `halstead_volume` (float) — Radon Halstead V
- `cognitive_complexity` (float) — SonarQube 인지적 복잡도

Domain 계층은 이 값들을 직접 계산하지 않고 인프라에서 전달받는다 (DDD 규칙).
