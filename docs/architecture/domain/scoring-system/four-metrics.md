---
title: "4대 지표 체계"
type: component
layer: domain
parent: "[[domain/scoring-system/MOC]]"
children:
  - "[[domain/scoring-system/logic-metric]]"
  - "[[domain/scoring-system/mastery-metric]]"
  - "[[domain/scoring-system/stability-metric]]"
  - "[[domain/scoring-system/authenticity-metric]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# 4대 지표 체계

> Jittda Sniper v5.0 의 핵심 평가 프레임워크.
> 후보자의 실제 GitHub 코드에서 추출한 측정값을 정규화하여 0-100점으로 산출한다.

## 가중 합산 공식

```
최종 점수 = 0.30 × 논리력 + 0.30 × 전문성 + 0.20 × 안정성 + 0.20 × 진정성
```

논리력과 전문성이 각 30%로 가장 높은 가중치를 가진다.
안정성과 진정성은 각 20%로 코드 품질의 지속성과 저작권을 검증한다.

## 4축 지표 개요

| 주지표 | 가중치 | 핵심 질문 | 산출 방향 | 세부 문서 |
|--------|--------|----------|---------|---------|
| **논리력** | 30% | 복잡한 로직을 얼마나 명확하게 구현했는가? | 복잡도 낮을수록 고득점 | [[logic-metric]] |
| **전문성** | 30% | 해당 기술 스택을 얼마나 깊이 이해하는가? | API/패턴 활용 깊이 높을수록 고득점 | [[mastery-metric]] |
| **안정성** | 20% | 코드가 장기적으로 유지보수 가능한가? | 부채/스멜/Churn 낮을수록 고득점 | [[stability-metric]] |
| **진정성** | 20% | 실제로 본인이 작성한 코드인가? | 순수 기여 비율 높을수록 고득점 | [[authenticity-metric]] |

## 세부 지표 전체 구성

| 주지표 | 세부 지표 | 산출 도구 | 내부 가중치 | Worker |
|--------|----------|----------|------------|--------|
| **논리력 (30%)** | | | | |
| | 순환 복잡도 (CC) | Radon / Lizard | 40% | W7 |
| | Halstead 난이도 (D) | Radon | 30% | W7 |
| | 인지적 복잡도 | SonarQube | 30% | W8 |
| **전문성 (30%)** | | | | |
| | API 활용 깊이 | AST 분석 | 35% | W10 |
| | 디자인 패턴 사용 | AST 패턴 감지 | 25% | W11 |
| | SOLID 준수율 | 아키텍처 분석 | 20% | W11 |
| | 기술스택 다양성 | 스킬 추출 | 20% | W9 |
| **안정성 (20%)** | | | | |
| | 기술 부채 비율 | SonarQube | 35% | W8 |
| | 코드 스멜 밀도 | SonarQube | 25% | W8 |
| | 리워크 비율 (Churn) | PyDriller | 20% | W7 |
| | 보안 취약점 밀도 | SonarQube + Bandit | 20% | W8 |
| **진정성 (20%)** | | | | |
| | 인간 타이핑 속도 (WPM) | Vibector | 30% | W3 |
| | 순수 기여도 | Blame + AST Pruning | 30% | W2 |
| | 표절/복사 비율 | Datasketch (LSH) | 20% | W5 |
| | 스타일 일관성 | CLAVE | 20% | W4 |

## 점수 정규화 원칙

- 모든 원시 측정값은 0-100점 범위로 정규화 후 가중 합산
- 논리력/안정성은 낮은 복잡도/부채가 높은 점수로 역변환 적용
- 전문성/진정성은 높은 활용도/순수 기여가 높은 점수로 직접 매핑

## 신뢰도 연동

점수 산출 시 데이터 소스 수에 따라 신뢰도 플래그가 함께 반환된다.
신뢰도 기준 상세: [[confidence-levels]]
