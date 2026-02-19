---
title: "안정성 지표 (Stability Metric)"
type: component
layer: domain
parent: "[[domain/scoring-system/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# 안정성 지표 (Stability Metric)

> 전체 최종 점수에서 **20%** 기여.
> 코드가 장기적으로 유지보수 가능하고 안전한지를 측정한다.
> 기술 부채, 코드 스멜, Churn, 보안 취약점 4축을 평가한다.
> 낮은 부채/스멜/Churn/취약점이 높은 점수로 역변환된다.

## 세부 항목 및 가중치

| 세부 지표 | 내부 가중치 | 측정 도구 | Worker | 설명 |
|----------|------------|---------|--------|------|
| 기술 부채 비율 | 35% | SonarQube | W8 | 전체 코드 대비 리팩토링 필요 코드 비율 |
| 코드 스멜 밀도 | 25% | SonarQube | W8 | 1000줄당 코드 스멜 발생 건수 |
| 리워크 비율 (Churn) | 20% | PyDriller | W7 | 최근 N개 커밋에서 반복 수정된 라인 비율 |
| 보안 취약점 밀도 | 20% | SonarQube + Bandit | W8 | 1000줄당 보안 취약점 발생 건수 |

## 측정 도구 상세

### SonarQube (기술 부채 + 코드 스멜 + 보안)

SonarQube는 정적 분석으로 다음 3가지 메트릭을 동시에 제공한다:

```
기술 부채 (Technical Debt):
  SonarQube가 추정하는 리팩토링 소요 시간 (분 단위)
  tech_debt_ratio = debt_minutes / development_minutes

코드 스멜 (Code Smell):
  냄새 밀도 = 코드 스멜 건수 / (LoC / 1000)
  종류: Long Method, Feature Envy, Data Clumps, God Class 등

보안 취약점 (Vulnerability):
  OWASP Top 10 기반 정적 분석
  취약점 밀도 = 취약점 건수 / (LoC / 1000)
```

### PyDriller (Churn)

```
리워크 비율 (Code Churn):
  분석 대상: 최근 90일 또는 최근 50커밋
  churn_ratio = 반복 수정 라인 수 / 전체 변경 라인 수
  높은 Churn = 불안정한 코드, 잦은 버그 수정 패턴
```

### Bandit (보안 — Python 전용)

```
Bandit 심각도 분류:
  HIGH:   SQL Injection, Command Injection, Hardcoded Password
  MEDIUM: Use of weak hash, Insecure deserialization
  LOW:    Use of assert, Broad exception catch
```

## 산출 수학적 모델

```python
# domain/scoring/metrics/stability.py

def calculate_stability_score(
    tech_debt_ratio: float,    # 0.0 ~ 1.0 (기술 부채 비율)
    churn_ratio: float,        # 0.0 ~ 1.0 (리워크 비율)
    smell_density: float,      # LoC 1000당 스멜 건수 (0 이상)
    vuln_density: float,       # LoC 1000당 취약점 건수 (0 이상)
) -> float:
    """
    안정성 점수: 부채/Churn/스멜/취약점이 낮을수록 고득점.
    각 요소를 감점 방식으로 산출 후 내부 가중치 합산.
    """
    # 기술 부채: 비율 100% → 0점, 0% → 100점
    score_debt = max(0.0, 100.0 - tech_debt_ratio * 100)

    # 코드 스멜: 1000줄당 30개 이상이면 0점
    score_smell = max(0.0, 100.0 - smell_density * 3.3)

    # Churn: 비율 100% → 0점, 0% → 100점
    score_churn = max(0.0, 100.0 - churn_ratio * 100)

    # 보안 취약점: 1000줄당 10개 이상이면 0점 (HIGH는 2배 감점)
    score_vuln = max(0.0, 100.0 - vuln_density * 10)

    # 내부 가중치 합산
    return (
        score_debt * 0.35
        + score_smell * 0.25
        + score_churn * 0.20
        + score_vuln * 0.20
    )
```

## 전체 안정성 점수 기여

```python
# domain/scoring/calculator.py (발췌)
Score_stability = max(0, 100 - (
    tech_debt_ratio * 40
    + churn_ratio * 30
    + smell_density * 30
))
# 최종 점수 기여: Score_stability * 0.20
```

## 안정성 등급 기준

| 점수 범위 | 등급 | 해석 |
|----------|------|------|
| 80-100 | A (안정) | 부채 최소, 장기 유지보수 우수 |
| 60-79 | B (양호) | 일부 부채 존재, 관리 가능 수준 |
| 40-59 | C (주의) | 상당한 기술 부채, 개선 필요 |
| 0-39 | D (위험) | 심각한 부채/취약점, 리팩토링 필수 |
