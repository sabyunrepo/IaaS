---
title: "Interface Layer"
type: moc
layer: interface
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[MOC]]"
---

# Interface Layer

> 사용자 접점 계층. REST API, WebSocket, Electron 데스크톱 앱, D3 시각화.
> Application Layer의 결과를 외부에 노출한다.

## 인터페이스 목록

| 인터페이스 | 역할 | 기술 |
|-----------|------|------|
| [[rest-api/MOC\|REST API]] | Job 관리, 분석 결과 조회 | FastAPI |
| [[websocket/MOC\|WebSocket]] | 실시간 분석 진행률 스트리밍 | FastAPI WebSocket |
| [[electron-app/MOC\|Electron App]] | Jittda Live 데스크톱 클라이언트 | Electron / Tauri |
| [[d3-charts/MOC\|D3 Charts]] | 4축 Radar, Treemap, Heatmap 시각화 | D3.js v7 |
| [[interface/web-frontend/MOC\|Web Frontend]] | React 19, Vite, pnpm | Public App (지원자) + Admin App (관리자) |

## 문서 목록

```dataview
TABLE status, updated, tags
FROM "docs/architecture/interface"
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
