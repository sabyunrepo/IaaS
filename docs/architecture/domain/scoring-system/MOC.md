---
title: "Scoring System"
type: moc
layer: domain
parent: "[[domain/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# Scoring System

> 후보자 GitHub 코드와 경력 데이터를 기반으로 4대 핵심 지표를 산출하는 도메인.
> 모든 점수에 코드/경력 데이터 근거와 신뢰도(🟢🟡🔴)를 함께 표시한다.
> Infrastructure import 금지 — 순수 비즈니스 로직만 포함.

## 4대 지표 개요

| 지표 | 가중치 | 측정 대상 | 주요 도구 |
|------|--------|----------|---------|
| [[logic-metric\|논리력 (Logic)]] | 30% | 순환 복잡도, Halstead 난이도, 인지적 복잡도 | Radon, Lizard, SonarQube |
| [[mastery-metric\|전문성 (Mastery)]] | 30% | API 활용 깊이, 디자인 패턴, SOLID 준수율 | AST 분석, 아키텍처 분석 |
| [[stability-metric\|안정성 (Stability)]] | 20% | 기술 부채, 코드 스멜, Churn, 보안 취약점 | SonarQube, PyDriller, Bandit |
| [[authenticity-metric\|진정성 (Authenticity)]] | 20% | 인간 타이핑 패턴, 순수 기여도, 표절 비율 | Vibector, Datasketch LSH, CLAVE |

## 가중 합산 공식

```
최종 점수 = 0.30 × 논리력 + 0.30 × 전문성 + 0.20 × 안정성 + 0.20 × 진정성
```

각 지표는 0-100점 범위로 정규화된 후 가중 합산된다.

## 신뢰도 체계

점수 산출에 사용된 데이터 소스 수와 공개 레포 수에 따라 신뢰도를 자동 판정한다.
상세 기준: [[confidence-levels]]

## 하위 문서

```dataview
TABLE type, status, updated
FROM "docs/architecture/domain/scoring-system"
WHERE file.name != "MOC"
SORT file.name ASC
```

## 관련 도메인

- [[identity-resolution/MOC]] — 순수 기여도 산출 (진정성 지표 입력)
- [[funnel-selection/MOC]] — 분석 대상 레포 선별

## 관련 Infrastructure

- [[infrastructure/complexity-analysis/MOC]] — Radon/Lizard CC, Halstead 수치 제공
- [[infrastructure/tree-sitter-ast/MOC]] — AST 기반 패턴 분석
- [[infrastructure/plagiarism-detection/MOC]] — Datasketch MinHash 표절 탐지

## 구현 위치

```
jittda/domain/scoring/
├── calculator.py          # 가중 합산 + 정규화
├── metrics/
│   ├── logic.py           # 논리력 산출
│   ├── mastery.py         # 전문성 산출
│   ├── stability.py       # 안정성 산출
│   └── authenticity.py    # 진정성 산출
└── confidence.py          # 신뢰도 판정
```
