---
title: "Tech Stack"
type: moc
layer: crosscutting
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[MOC]]"
tags: [tech-stack, versions, dependencies]
---

# Tech Stack

> Jittda v5.0 + Jittda Live 통합 기술 스택 레지스트리.
> 모든 의존성의 버전, 선정 근거, 호환성 매트릭스를 관리한다.

## 스택 개요

| 계층 | 핵심 기술 |
|------|----------|
| [[tech-stack/backend\|Backend]] | Python 3.11 + FastAPI + LangGraph + Instructor |
| [[tech-stack/frontend\|Frontend]] | React 19 + Vite + Tailwind 4 + D3.js v7 |
| [[tech-stack/infrastructure\|Infrastructure]] | Docker Compose + PostgreSQL 16 + Redis 7 + Cloudflare Tunnel |

## 버전 매트릭스

| 기술 | 버전 | 비고 |
|------|------|------|
| Python | 3.11 | Pydantic v2 최적화 |
| LangGraph | 1.0.8+ | GA, HMAS StateGraph |
| FastAPI | 0.119+ | Pydantic v2 네이티브 |
| React | 19 | Concurrent Mode |
| D3.js | 7.9+ | Treemap, Heatmap |
| PostgreSQL | 16 | pgvector 0.3.6+ |
| Electron | 33+ | Jittda Live 데스크톱 |

> 전체 버전 매트릭스: [[tech-stack/version-matrix]]

## 문서 목록 (자동)

```dataview
TABLE status, updated, tags
FROM "docs/architecture/tech-stack"
WHERE file.name != "MOC"
SORT file.name ASC
```
