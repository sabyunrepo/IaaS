---
title: "Architecture Decisions"
type: moc
layer: decisions
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[MOC]]"
---

# Architecture Decisions

> MADR v4 형식의 아키텍처 결정 기록. 모든 주요 설계 결정의 컨텍스트, 옵션, 근거를 문서화한다.

## ADR 대시보드

```dataview
TABLE status, date, decision-makers, tags
FROM "docs/architecture/decisions"
WHERE type = "adr"
SORT file.name ASC
```

## 상태별 분류

```dataview
TABLE length(rows) as "개수"
FROM "docs/architecture/decisions"
WHERE type = "adr"
GROUP BY status
```
