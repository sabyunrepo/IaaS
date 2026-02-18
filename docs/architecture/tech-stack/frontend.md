---
title: "Frontend Tech Stack"
type: component
layer: crosscutting
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[tech-stack/MOC]]"
depends-on: []
affects: []
linear: ""
tags: [frontend, react, d3, tailwind, tech-stack]
---

# Frontend Tech Stack

> React 19 + Vite + Tailwind 4 + D3.js v7 기반 웹 프론트엔드.
> WebSocket 실시간 스트리밍 + TanStack Query 데이터 페칭.

## 핵심 의존성

| 영역 | 기술 | 버전 | 선정 근거 |
|------|------|------|----------|
| **Framework** | React | 19 | Concurrent Mode, 기존 검증 |
| **Build** | Vite | latest | 빠른 HMR |
| **Styling** | Tailwind CSS | 4 | 유틸리티 기반 |
| **Visualization** | D3.js | 7.9+ | 복잡한 계층 데이터 시각화 |
| **State/Fetching** | TanStack Query | 5.0+ | 실시간 데이터 페칭 + 캐싱 |
| **Streaming** | WebSocket (Native) | - | LangGraph 실시간 스트리밍 |
| **Types** | TypeScript | 5.x | 타입 안전성 |

## D3 시각화 컴포넌트

| 컴포넌트 | 기술 | 데이터 소스 | 용도 |
|----------|------|-----------|------|
| `FourAxisRadar.tsx` | D3.js | 4대 지표 | 논리력/전문성/안정성/진정성 레이더 |
| `ComplexityTreemap.tsx` | D3.js | W7 결과 | 파일별 복잡도 드릴다운 |
| `AICodeHeatmap.tsx` | D3.js | W3 결과 | 파일별 Human vs AI 히트맵 |
| `SkillHeatmap.tsx` | D3.js | W9 결과 | 기술스택 히트맵 (JD 매칭) |
| `AuthenticityGauge.tsx` | D3.js | W3+W5 | 진정성 게이지 |
| `CommitTimeline.tsx` | D3.js | W1 결과 | Git 커밋 타임라인 |
| `AgentProgressFlow.tsx` | React | WebSocket | HMAS 에이전트 실행 흐름 |

## Electron 데스크톱 (Jittda Live)

| 영역 | 기술 | 버전 | 선정 근거 |
|------|------|------|----------|
| **Desktop** | Electron | 33+ | 오디오 캡처 생태계 |
| **Audio** | electron-audio-loopback | 1.0.6 | OS 네이티브 캡처 |
| **VAD** | Silero VAD + @ricky0123/vad | WASM | Renderer에서 1ms 이하 |
| **Local DB** | LanceDB | 0.26 | In-process 벡터 검색 |
| **Graph** | graphology | latest | In-memory 그래프 탐색 |
| **State** | Zustand | latest | Pub/Sub 이벤트 버스 |
| **Build** | Electron Forge | latest | 크로스 플랫폼 패키징 |

## 폐기된 기술

| 기술 | 이유 |
|------|------|
| SVG 차트 컴포넌트 | D3.js로 전면 교체 |
| Chart.js | D3.js로 통일 (유연성) |

## 관련 문서

- [[interface/d3-charts/MOC]] -- D3 차트 상세
- [[interface/electron-app/MOC]] -- Electron 앱 상세
- [[decisions/0009-electron-vs-tauri]] -- 데스크톱 프레임워크 선택
- [[tech-stack/version-matrix]] -- 전체 버전 매트릭스
