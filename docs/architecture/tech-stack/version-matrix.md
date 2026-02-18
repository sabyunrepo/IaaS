---
title: "Version Matrix"
type: component
layer: crosscutting
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[tech-stack/MOC]]"
depends-on: []
affects: []
linear: ""
tags: [versions, compatibility, matrix, tech-stack]
---

# Version Matrix

> 전체 의존성 버전 매트릭스. 2026-02 기준 안정성 검증된 최신 버전.
> 호환성 제약과 Breaking Change를 한눈에 파악.

## Backend (Python)

| 패키지 | 최소 버전 | 비고 |
|--------|----------|------|
| `langgraph` | 1.0.8 | GA, StateGraph HMAS |
| `langgraph-checkpoint-postgres` | 3.0.4 | 3.x 스키마 호환 |
| `instructor` | 1.7.0 | Pydantic v2 네이티브 |
| `langfuse` | 2.57.0 | 프롬프트 관리 + 추적 |
| `fastapi` | 0.119.0 | Pydantic v2 최적화 |
| `uvicorn` | 0.30.0 | ASGI 서버 |
| `websockets` | 14.0 | WebSocket 지원 |
| `tree-sitter` | 0.24.7 | **Breaking: 네이티브 바인딩** |
| `tree-sitter-python` | 0.24.1 | 0.24.x 통일 |
| `tree-sitter-javascript` | 0.24.1 | 0.24.x 통일 |
| `tree-sitter-typescript` | 0.24.1 | 0.24.x 통일 |
| `tree-sitter-java` | 0.24.1 | 0.24.x 통일 |
| `tree-sitter-go` | 0.24.1 | 0.24.x 통일 |
| `radon` | 6.0.1 | CC/Halstead/MI |
| `lizard` | 1.17.10 | 멀티 언어 CC |
| `bandit` | 1.8.0 | 보안 스캔 |
| `PyGithub` | 2.5.0 | GitHub REST API |
| `gql[aiohttp]` | 3.5.0 | GitHub GraphQL |
| `PyDriller` | 2.9 | 커밋 순회 |
| `psycopg[binary]` | 3.2.0 | PostgreSQL async |
| `pgvector` | 0.3.6 | 벡터 검색 |
| `redis` | 5.2.0 | Redis 클라이언트 |
| `datasketch` | 1.6.5 | MinHash/LSH |
| `pydantic` | 2.12.5 | 데이터 모델 |
| `python-Levenshtein` | 0.26.0 | 문자열 유사도 |
| `httpx` | 0.28.0 | HTTP 클라이언트 |

## Frontend (Node.js)

| 패키지 | 최소 버전 | 비고 |
|--------|----------|------|
| `react` | 19.0.0 | Concurrent Mode |
| `d3` | 7.9.0 | 시각화 |
| `@types/d3` | 7.4.3 | TypeScript 타입 |
| `@tanstack/react-query` | 5.0.0 | 데이터 페칭 |
| `tailwindcss` | 4.x | 스타일링 |

## Desktop (Electron)

| 패키지 | 최소 버전 | 비고 |
|--------|----------|------|
| `electron` | 33.0.0 | 데스크톱 프레임워크 |
| `electron-audio-loopback` | 1.0.6 | OS 네이티브 오디오 |
| `@ricky0123/vad` | latest | Silero VAD (WASM) |
| `@lancedb/lancedb` | 0.26.0 | In-process 벡터 DB |
| `graphology` | latest | In-memory 그래프 |
| `zustand` | latest | 상태 관리 (EventBus) |

## Infrastructure

| 기술 | 버전 | 비고 |
|------|------|------|
| Docker Compose | v2 | 최신 CLI |
| PostgreSQL | 16 (alpine) | pgvector 0.3.6 |
| Redis | 7 (alpine) | - |
| SonarQube | Community (latest) | On-Demand |
| Cloudflare Tunnel | latest | Zero Trust |
| Node.js | 20 (alpine) | Frontend 빌드 |
| Nginx | alpine | 프로덕션 서빙 |

## 호환성 제약

| 제약 | 영향 범위 | 설명 |
|------|---------|------|
| Tree-sitter 0.24.x | 모든 tree-sitter-{lang} | **버전 통일 필수** (.so 빌드 폐기) |
| LangGraph Checkpoint 3.x | PostgreSQL | checkpoint 테이블 스키마 3.x 전용 |
| Pydantic v2 | FastAPI, Instructor | `ConfigDict(strict=True)` 사용 |
| macOS 13.0+ | Electron 오디오 | ScreenCaptureKit 최소 요구 |

## 폐기된 기술 (v5.0에서 제거)

| 기술 | 이유 | 대체 |
|------|------|------|
| `temporalio` | LangGraph로 대체 | `langgraph` |
| `alembic` | Clean Slate | Fresh `init.sql` |
| `langchain` | Instructor로 대체 | `instructor` |
| SVG 차트 | D3.js로 교체 | `d3` |
| 정규식 파서 | Structured Output | `instructor` |

## 관련 문서

- [[tech-stack/backend]] -- 백엔드 상세
- [[tech-stack/frontend]] -- 프론트엔드 상세
- [[tech-stack/infrastructure]] -- 인프라 상세
- [[decisions/0001-langgraph-over-temporal]] -- LangGraph 선택
- [[decisions/0005-instructor-pydantic]] -- Instructor 선택
- [[decisions/0006-tree-sitter-025]] -- Tree-sitter Breaking Change
