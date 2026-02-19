---
title: "Web Frontend"
type: moc
layer: interface
status: active
created: 2026-02-19
tags: [moc, interface, frontend, react]
---

# Web Frontend

> 사용자 웹 인터페이스. 지원자 셀프서비스 + 관리자 대시보드.

## 개요

pnpm 모노레포 기반 3패키지 구조:
- **@jittda/ui** — 공유 디자인 시스템 (Button, Input, Card, FileUpload, Modal)
- **@jittda/public** — 지원자용 앱 (비인증, 4페이지)
- **@jittda/admin** — 관리자용 앱 (OAuth 인증, 11페이지)

## Tech Stack

| 기술 | 버전 | 용도 |
|------|------|------|
| React | 19 | UI 프레임워크 |
| Vite | - | ESM 번들러 |
| Tailwind CSS | 4 | 스타일링 |
| pnpm | 9+ | 패키지 관리 |
| react-router-dom | 7+ | SPA 라우팅 |
| react-i18next | - | 다국어 |
| D3.js | 7.9+ | 데이터 시각화 (admin-app) |

## 구성 문서

| 문서 | 설명 |
|------|------|
| [[interface/web-frontend/public-app\|Public App]] | 지원자용 앱 (커리어 페이지, 지원 폼) |
| [[interface/web-frontend/admin-app\|Admin App]] | 관리자용 앱 (대시보드, 분석 결과) |
| [[interface/web-frontend/shared-ui\|Shared UI]] | 공유 디자인 시스템 |

## 디렉토리 구조

```
jittda/frontend/
├── pnpm-workspace.yaml
├── packages/
│   ├── ui/              # @jittda/ui
│   ├── public-app/      # @jittda/public
│   └── admin-app/       # @jittda/admin
├── package.json
└── tsconfig.base.json
```

## 연동점

- **REST API** → [[interface/rest-api/MOC|REST API]] 엔드포인트 호출
- **WebSocket** → [[interface/websocket/MOC|WebSocket]] 분석 진행률 스트리밍
- **D3 Charts** → [[interface/d3-charts/MOC|D3 Charts]] admin-app에 통합
- **HMAS Graph** → POST /api/v1/applications/:id/analyze로 분석 시작
