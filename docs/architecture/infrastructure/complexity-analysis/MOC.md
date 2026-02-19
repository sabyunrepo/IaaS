---
title: "Complexity Analysis"
type: moc
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[infrastructure/MOC]]"
linear: [JIT-95, JIT-96]
---

# Complexity Analysis

> 소스코드의 복잡도 지표를 산출하는 어댑터 계층.
> Radon(CC/Halstead), Lizard(MI), SonarQube(기술부채/코드스멜/보안)를 사용하며,
> ComplexityMeterWorker(W7)과 QualityScannerWorker(W8)에서 소비된다.

## 설계 결정

- Radon: Python 전용 CC(순환복잡도) + Halstead 메트릭
- Lizard: 다중 언어 MI(Maintainability Index) 산출
- SonarQube: Docker On-Demand 프로파일로 실행, REST API로 결과 조회
- 세 도구의 출력을 `complexity_metrics` 단일 구조로 병합

## 문서 목록

| 문서 | 설명 |
|------|------|
| [[complexity-analysis/radon\|radon]] | Radon CC/Halstead 메트릭, 코드 예시 |
| [[complexity-analysis/lizard\|lizard]] | Lizard MI(Maintainability Index), 코드 예시 |
| [[complexity-analysis/sonarqube\|sonarqube]] | Docker Profile On-Demand 분석 |

```dataview
TABLE status, updated, tags
FROM "docs/architecture/infrastructure/complexity-analysis"
WHERE file.name != "MOC"
SORT file.name ASC
```

## 관련 ADR

```dataview
LIST
FROM "docs/architecture/decisions"
WHERE contains(impacts, this.file.link)
SORT date DESC
```

## 사용 Worker

| Worker | 사용 도구 | 출력 |
|--------|----------|------|
| W7 ComplexityMeterWorker | Radon, Lizard, cloc | `complexity_metrics` (CC, Halstead, MI) |
| W8 QualityScannerWorker | SonarQube API, Bandit | `quality_report` (기술부채, 코드스멜, 취약점) |
