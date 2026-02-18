---
title: "Application Layer"
type: moc
layer: application
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[MOC]]"
---

# Application Layer

> LangGraph HMAS 오케스트레이션 계층. Domain 로직을 조합하여 전체 분석 파이프라인을 구성한다.
> 3-Phase Lifecycle: Pre-Interview → Live Interview → Post-Interview.

## 핵심 컴포넌트

| 컴포넌트 | 역할 | Phase |
|----------|------|-------|
| [[hmas-graph/MOC\|HMAS Graph]] | MetaAgent → Supervisor → Worker 계층 실행 | Pre-Interview |
| [[live-session/MOC\|Live Session]] | 실시간 AI 면접 엔진 (3-Layer Questions) | Live Interview |
| [[state-management/MOC\|State Management]] | Reference Passing + MetaState 관리 | 전체 |
| [[quality-gate/MOC\|Quality Gate]] | 출력 품질 검증 + 리뷰 루프 | Pre + Post |

## 문서 목록

```dataview
TABLE status, updated, tags
FROM "docs/architecture/application"
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
