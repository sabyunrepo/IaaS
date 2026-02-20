# Jittda Sniper v5.0 — Clean Slate 재건축 최종 설계서

> 작성일: 2026-02-15 | 버전: v5.1 (Dependency & Architecture Optimized)
> 상태: 최종 설계 완료 (구현 단계 진입)
> 기반: souce1-6.md (비전), review1.md (설계 리뷰), review2.md (구현 계획 리뷰), extra.md (아키텍처 최적화)
> 원칙: **"마이그레이션이 아닌 재건축(Reconstruction)"** — `jittda/` 신규 디렉토리, Fresh init.sql, Modern Tech Stack, Reference Passing

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [설계 철학 및 핵심 원칙](#2-설계-철학-및-핵심-원칙)
3. [Clean Slate 접근 전략](#3-clean-slate-접근-전략)
4. [DDD 아키텍처 및 디렉토리 구조](#4-ddd-아키텍처-및-디렉토리-구조)
5. [기술 스택 선정](#5-기술-스택-선정)
6. [3계층 HMAS 아키텍처](#6-3계층-hmas-아키텍처)
7. [Identity Resolution Pipeline](#7-identity-resolution-pipeline)
8. [JD 기반 Funnel Selection](#8-jd-기반-funnel-selection)
9. [Worker Agent 상세 설계](#9-worker-agent-상세-설계)
10. [LangGraph 그래프 설계](#10-langgraph-그래프-설계)
11. [4대 핵심 지표 체계](#11-4대-핵심-지표-체계)
12. [Pydantic 모델 + Instructor 통합](#12-pydantic-모델--instructor-통합)
13. [벡터 검색 (RAG) 전략](#13-벡터-검색-rag-전략)
14. [프롬프트 엔지니어링](#14-프롬프트-엔지니어링)
15. [인프라 구성 (Docker + Cloudflare Tunnel)](#15-인프라-구성-docker--cloudflare-tunnel)
16. [프론트엔드 설계](#16-프론트엔드-설계)
17. [테스트 전략](#17-테스트-전략)
18. [Phase별 구현 로드맵 및 Linear 티켓](#18-phase별-구현-로드맵-및-linear-티켓)

---

## 1. Executive Summary

현재 Vantict Sniper v4.0(Temporal.io 기반 고정 4-Phase 파이프라인)을 **완전히 새로운 프로젝트 `jittda/`**로 재건축한다. 기존 코드베이스 위에서 작업하는 "마이그레이션"이 아니라, 옆 부지에 새 건물을 짓고 필요한 가구(로직)만 골라 옮기는 **Clean Slate Reconstruction**이다.

### 핵심 변경점 (v5.1 반영)

| 영역 | AS-IS (Vantict v4.0) | TO-BE (Jittda v5.0) |
|------|----------------------|---------------------|
| **프로젝트 구조** | `backend/` (레거시 혼재) | `jittda/` Monorepo (`backend/src/`, `frontend/`, `infra/` 분리) |
| **오케스트레이션** | Temporal.io (고정 파이프라인) | **LangGraph 1.0+** StateGraph (동적 HMAS) |
| **상태 관리** | 메모리 내 전체 데이터 전달 | **Reference Passing** (DB ID만 전달, Raw Data 분리) |
| **AST 파싱** | 없음 | **Tree-sitter 0.24+** (Python 패키지 네이티브 바인딩) |
| **데이터 전달** | plain dict (암묵적 키) | Pydantic v2 TypedDict State (타입 안전) |
| **LLM 출력** | JSON 직접 파싱 | Instructor 1.7+ + Pydantic v2 (자동 검증/재시도) |
| **코드 분석** | PyGithub + 단순 clone | Identity Resolution + Forensic Blame + AST Pruning |
| **레포 선별** | 전체 레포 분석 | JD 기반 Funnel Selection (상위 3-5개만) |
| **정적 분석** | PyDriller 기본 | + Tree-sitter + Radon/Lizard + SonarQube + Datasketch |
| **인프라** | SonarQube 상시 구동 | **Docker Profile** 기반 On-Demand 실행 |
| **터널** | 포트 포워딩/ngrok | Cloudflare Tunnel (**`infra-tunnel/` 독립 프로젝트**) |
| **DB 초기화** | Alembic migration chain | Fresh `init.sql` + LangGraph Checkpoint 테이블 |
| **프론트엔드** | SVG 5축 레이더 | React 19 + Tailwind + D3.js (드릴다운 트리맵, 히트맵) |
| **DDD** | 미적용 (로직 혼재) | 엄격한 4계층 (`backend/src/` 하위) |

### review1.md 지적사항 반영 현황

| 지적 | 섹션 | 반영 상태 |
|------|------|----------|
| Identity Resolution Pipeline 도입 | §7 | ✅ GitHub Node ID + 동적 .mailmap + 3단계 포렌식 |
| JD 기반 Funnel Selection | §8 | ✅ 3단계 퍼널 (Hard Filter → Relevance Score → Vector) |
| DDD 적용 | §4 | ✅ 4계층 엄격 분리 |
| Cloudflare Tunnel | §15 | ✅ docker-compose 고정 서비스 |
| AI Code Heatmap | §16 | ✅ Human vs AI 비율 히트맵 |
| D3.js + 실시간 스트리밍 | §16 | ✅ WebSocket 기반 실시간 UI |

### review2.md 지적사항 반영 현황

| 지적 | 섹션 | 반영 상태 |
|------|------|----------|
| Clean Slate (jittda/ 신규 디렉토리) | §3 | ✅ 완전 신규 프로젝트 |
| Phase 4 "Temporal 제거" 삭제 | §18 | ✅ 존재하지 않으므로 제거 불필요 |
| Fresh init.sql (Alembic 히스토리 금지) | §15 | ✅ 단일 init.sql |
| Legacy = Read-only 참조 | §3 | ✅ Port Logic, Rewrite Code |
| DDD 의존성 규칙 엄격화 | §4 | ✅ domain → infrastructure import 금지 |
| Interface Layer 분리 | §4 | ✅ interface/api 계층 명시 |
| Makefile 표준화 | §15 | ✅ 표준 타겟 정의 |

### extra.md 지적사항 반영 현황

| 지적 | 섹션 | 반영 상태 |
|------|------|----------|
| 의존성 최신화 (LangGraph 1.0.8+, Tree-sitter 0.24.7+) | §5 | ✅ 2026-02 기준 최신 버전 |
| State Bloat 방지 — Reference Passing | §10 | ✅ DB ID만 전달, Load→Process→Save→Ref 패턴 |
| SonarQube On-Demand (Docker Profile) | §15 | ✅ `profiles: ["analysis"]` |
| Monorepo 구조 (backend/src/, frontend/, infra/) | §4 | ✅ 관심사 물리적 분리 |
| Cloudflare Tunnel 독립 프로젝트 (infra-tunnel/) | §15 | ✅ 생명주기 분리, 외부 네트워크 참조 |
| Tree-sitter 0.24 Breaking Change 대응 | §9 | ✅ Python 패키지 네이티브 바인딩 |
| Backend/Frontend 별도 Dockerfile (Multi-stage) | §15 | ✅ Hot Reload + Production 빌드 |
| Pydantic v2 ConfigDict 준수 | §12 | ✅ model_config = ConfigDict(strict=True) |
| LangGraph Checkpoint 테이블 명시 (3.0.x 호환) | §15 | ✅ init.sql에 checkpoints 테이블 |

---

## 2. 설계 철학 및 핵심 원칙

### 2.1 시스템 설계 철학

**"확률적 AI(LLM)와 결정론적 알고리즘(Static Analysis)의 하이브리드 결합"**

단순히 LLM에게 "이 코드 어때?"라고 묻는 것이 아니라, 수학적으로 계산된 지표(Fact)를 LLM에게 제공하여 해석(Insight)하게 함으로써 할루시네이션을 원천 차단하고 신뢰도를 보장한다.

### 2.2 핵심 원칙

| # | 원칙 | 설명 |
|---|------|------|
| 1 | **Noise-Free** | Fork, 라이브러리, AI 생성/Boilerplate 코드를 완벽히 제거한 순수 기여분만 분석 |
| 2 | **Semantic Analysis** | 텍스트 기반이 아닌 AST(추상 구문 트리) 기반의 논리적 분석 수행 |
| 3 | **Identity-First** | "이 코드를 정말 지원자가 짰는가?" 검증이 분석보다 선행 |
| 4 | **JD-Relevance** | "이 프로젝트가 회사 업무와 관련 있는가?" JD 적합성 선별 후 분석 |
| 5 | **Reference Passing** | LangGraph State에는 '데이터'가 아닌 '참조(DB ID)'만 담는다. Raw Data는 DB에 저장 |
| 6 | **Fact-Grounded** | 모든 LLM 판단에 정량적 분석 데이터 근거 필수 |
| 7 | **Parallel Execution** | Fan-out/Fan-in 패턴으로 분석 속도 극대화 |
| 8 | **Clean Separation** | DDD 4계층 엄격 준수, 계층 간 의존성 규칙 위반 금지 |

---

## 3. Clean Slate 접근 전략

### 3.1 원칙: "마이그레이션이 아닌 재건축"

```
❌ 기존 접근 (Migration)
backend/ 위에서 Temporal 제거 → LangGraph 교체 → 코드 정리

✅ 올바른 접근 (Reconstruction)
jittda/ 신규 생성 → 처음부터 DDD 구조 → 필요한 로직만 발췌 재작성
```

- `jittda/`는 **완전히 새로운 디렉토리**에서 시작
- Temporal 코드가 **애초에 존재하지 않음** (제거할 것이 없음)
- DB는 **Fresh `init.sql`** 하나로 초기화 (Alembic revision 히스토리 금지)
- 기존 Vantict 코드는 **참조용 라이브러리(Read-only)**로만 취급

### 3.2 레거시 자산 선별 가이드

**"파일 복사-붙여넣기 금지, 로직 이식 허용"**이 원칙이다.

#### [Asset] 핵심 로직 — Port Logic, Rewrite Code

비즈니스 로직은 가져오되, DDD/Pydantic 스타일에 맞춰 새로 작성한다.

| 원본 | 조치 | 대상 위치 |
|------|------|----------|
| `scoring_formulas.py` (899줄) | 로직 100% 유지, 클래스 구조로 재작성 | `domain/scoring/calculator.py` |
| `prompts/*.yaml` | LangChain/Instructor 포맷 호환성 검증 후 이전 | `infrastructure/llm/prompts/` |
| JD 분석/매칭 로직 | 키워드 매칭 → 벡터 검색 결합 재작성 | `domain/matching/funnel.py` |
| Redis 캐싱 아이디어 | 아이디어만 참조, 데코레이터 패턴으로 재작성 | `infrastructure/llm/client.py` |

#### [Reference] 참조 대상 — Read Only

아이디어만 가져오고 코드는 완전히 새로 작성한다.

| 원본 | 참조 이유 | 재구현 |
|------|----------|--------|
| `services/git.py` | 단순 clone 로직 폐기 | Identity Resolution 파이프라인으로 재구현 |
| `utils/llm_cache.py` | Redis 캐싱 패턴 참조 | `infrastructure/llm/cached_client.py`에 데코레이터 패턴 |
| `github_service.py` | API 호출 패턴 참조 | GraphQL 중심 재설계 |

#### [Liability] 폐기 대상 — Do Not Copy

새 프로젝트에 **절대 포함시키지 않는다**.

| 대상 | 이유 |
|------|------|
| `workflows/`, `activities/`, `worker.py` | Temporal 관련 — 존재 자체가 불필요 |
| `alembic/versions/*.py` | 레거시 DB 히스토리 — Fresh init.sql 사용 |
| SVG 차트 컴포넌트 | D3.js로 전면 교체 |
| 정규식 기반 파서 | Instructor(Structured Output)로 대체 |
| `core/temporal.py`, `core/temporal_interceptors.py` | Temporal 인프라 |
| `activity_logger.py` | Temporal 전용 로깅 |

---

## 4. DDD 아키텍처 및 디렉토리 구조

### 4.1 4계층 아키텍처

review2.md 지적에 따라 **Interface Layer**를 Application과 분리하고, **의존성 규칙**을 엄격히 적용한다.

```
의존성 방향 (단방향만 허용):

  Interface → Application → Domain ← Infrastructure
                              ↑
                              │ (Domain은 외부를 모른다)
                              │
                     Infrastructure가 Domain 모델을 리턴
```

**의존성 규칙:**
- `domain/`은 **어떤 외부 패키지도 import하지 않는다** (순수 Python + Pydantic만)
- `infrastructure/`는 `domain/` 모델을 리턴하도록 구현한다
- `application/`은 `domain/`과 `infrastructure/`를 조합한다
- `interface/`는 `application/` 유스케이스만 호출한다

### 4.2 Monorepo 디렉토리 구조

> **extra.md 반영:** Backend/Frontend/Infra를 물리적으로 격리하여 Docker 빌드 컨텍스트 최적화 및 관심사 분리를 달성한다. DDD 4계층은 `backend/src/` 하위에 위치한다.

```
/ (Root)
├── infra-tunnel/                  # [인프라] Cloudflare Tunnel 전용 (독립 생명주기)
│   ├── docker-compose.yml         # cloudflared + jittda-public 네트워크 생성
│   └── .env                       # TUNNEL_TOKEN
│
└── jittda/                        # [애플리케이션] Jittda 서비스 Monorepo
    ├── docker-compose.yml         # 전체 서비스 오케스트레이션
    ├── Makefile                   # 표준화된 개발 명령어
    ├── .env.example               # 공통 환경변수 템플릿
    ├── .gitignore
    │
    ├── backend/                   # [Backend Service] Python + FastAPI + LangGraph
    │   ├── Dockerfile             # Backend 전용 빌드 (python:3.11-slim + git)
    │   ├── pyproject.toml         # Python 의존성 (2026-02 최신 버전)
    │   ├── .dockerignore          # 빌드 컨텍스트 최적화
    │   │
    │   ├── src/                   # 소스 코드 루트 (PYTHONPATH=/app/src)
    │   │   ├── main.py            # 앱 진입점
    │   │   │
    │   │   ├── interface/         # [Layer 1] 외부 어댑터 (Web/HTTP)
    │   │   │   ├── api/
    │   │   │   │   ├── routes/
    │   │   │   │   │   ├── jobs.py        # Job CRUD + WebSocket 스트리밍
    │   │   │   │   │   ├── auth.py        # OAuth 인증
    │   │   │   │   │   └── health.py      # 헬스체크
    │   │   │   │   ├── middleware/
    │   │   │   │   ├── schemas/           # API 요청/응답 스키마
    │   │   │   │   └── main.py            # FastAPI 앱
    │   │   │   └── websocket/
    │   │   │       └── stream_manager.py
    │   │   │
    │   │   ├── application/       # [Layer 2] 오케스트레이션 + 유스케이스
    │   │   │   ├── graphs/        # LangGraph StateGraph 정의
    │   │   │   │   ├── meta_graph.py
    │   │   │   │   ├── forensic_graph.py
    │   │   │   │   ├── logic_graph.py
    │   │   │   │   ├── stack_graph.py
    │   │   │   │   └── question_graph.py
    │   │   │   ├── nodes/         # LangGraph 노드 (thin wrapper, Load→Process→Save→Ref)
    │   │   │   ├── states/        # TypedDict State (Reference Passing 적용)
    │   │   │   └── use_cases/
    │   │   │
    │   │   ├── domain/            # [Layer 3] 순수 비즈니스 로직 (외부 의존성 0)
    │   │   │   ├── identity/      # Identity Resolution
    │   │   │   │   ├── models.py
    │   │   │   │   ├── mailmap_builder.py
    │   │   │   │   ├── blame_filter.py
    │   │   │   │   └── semantic_pruner.py
    │   │   │   ├── scoring/       # 점수 산출
    │   │   │   │   ├── models.py
    │   │   │   │   ├── calculator.py
    │   │   │   │   └── normalizer.py
    │   │   │   ├── matching/      # JD-후보자 매칭
    │   │   │   ├── question/      # 질문 생성 규칙
    │   │   │   └── analysis/      # 분석 도메인 모델
    │   │   │
    │   │   └── infrastructure/    # [Layer 4] 외부 서비스 어댑터
    │   │       ├── git/           # blame_runner, clone_manager, mailmap_writer
    │   │       ├── github/        # graphql_client, rest_client
    │   │       ├── analysis/      # tree_sitter_adapter (v0.24), radon, lizard, sonarqube, datasketch
    │   │       ├── llm/           # instructor_client, cached_client, langfuse
    │   │       ├── linkedin/      # brightdata_client
    │   │       ├── embedding/     # pgvector_store
    │   │       └── persistence/   # job_repository, analysis_repository
    │   │
    │   └── tests/                 # Backend 테스트
    │       ├── domain/            # 순수 단위 테스트
    │       ├── infrastructure/    # Mock 기반 어댑터 테스트
    │       ├── application/       # LangGraph 통합 테스트
    │       └── e2e/               # E2E 파이프라인
    │
    ├── frontend/                  # [Frontend Service] React 19 + Vite + D3.js
    │   ├── Dockerfile             # Multi-stage (development → builder → production/Nginx)
    │   ├── package.json
    │   ├── vite.config.ts
    │   ├── tsconfig.json
    │   ├── tailwind.config.js
    │   ├── .dockerignore
    │   ├── public/
    │   └── src/
    │       ├── components/
    │       │   └── charts/
    │       │       ├── FourAxisRadar.tsx
    │       │       ├── ComplexityTreemap.tsx
    │       │       ├── AuthenticityGauge.tsx
    │       │       ├── AICodeHeatmap.tsx
    │       │       ├── SkillHeatmap.tsx
    │       │       ├── CommitTimeline.tsx
    │       │       └── AgentProgressFlow.tsx
    │       ├── hooks/
    │       │   └── useLangGraphStream.ts
    │       ├── pages/
    │       │   └── ResultPage/
    │       └── services/          # API 호출 클라이언트
    │
    └── infra/                     # [Infrastructure] 설정 및 초기화 스크립트
        ├── postgres/
        │   └── init.sql           # Fresh DB Schema + LangGraph Checkpoint 테이블
        ├── sonarqube/
        │   └── sonar-project.properties
        └── nginx/                 # Production 리버스 프록시
            └── default.conf
```

---

## 5. 기술 스택 선정

### 5.1 백엔드

> **extra.md 반영:** 2026년 2월 기준 안정성이 검증된 최신 버전으로 확정. 특히 Tree-sitter 0.24의 Breaking Change(바인딩 방식 변경)를 반영.

| 영역 | 기술 | 버전 | 선정 근거 |
|------|------|------|----------|
| **Runtime** | Python 3.11 + FastAPI | 0.119+ | 기존 검증, Pydantic v2 최적화 |
| **Orchestration** | LangGraph | **1.0.8+** (GA) | StateGraph HMAS, Checkpointer durability |
| **Checkpointer** | langgraph-checkpoint-postgres | **3.0.4+** | PostgreSQL 재활용, 3.x 스키마 호환 |
| **Structured Output** | Instructor | **1.7.0+** | Pydantic v2 네이티브, 자동 재시도(max 3) |
| **AST Parsing** | Tree-sitter | **0.24.7+** | Python 패키지 네이티브 바인딩 (.so 빌드 폐기) |
| **Python Complexity** | Radon | 6.0.1+ | 정확한 CC/Halstead/MI |
| **Multi-lang Complexity** | Lizard | 1.17.10+ | CC + NLOC + Parameter Count |
| **Quality Gate** | SonarQube Community | latest | On-Demand 실행 (Docker Profile) |
| **Plagiarism** | Datasketch | 1.6.5+ | MinHash/LSH, Python 네이티브 |
| **Git History** | PyDriller | **2.9+** | 커밋 순회, Code Churn |
| **DB** | PostgreSQL 16 + pgvector | 0.3.6+ | 벡터 검색 통합 |
| **Cache** | Redis 7 | 5.2.0+ | LLM 캐시, Rate Limit |
| **LLM** | Kimi K2.5 (Langfuse-first) | — | 비용 효율, 한국어 지원 |
| **Tracing** | Langfuse | **2.57.0+** | 프롬프트 관리 + 추적 |

### 5.2 프론트엔드

| 영역 | 기술 | 선정 근거 |
|------|------|----------|
| **Framework** | React 19 + Vite | 기존 검증, 빠른 HMR |
| **Styling** | Tailwind CSS 4 | 기존 검증, 유틸리티 기반 |
| **Visualization** | D3.js v7 | Treemap, Heatmap 등 복잡한 계층 데이터 시각화에 최대 유연성 |
| **State** | TanStack Query | 실시간 데이터 페칭 + 캐싱 |
| **Streaming** | WebSocket | LangGraph 실행 상태 실시간 전송 |

### 5.3 인프라

| 영역 | 기술 | 선정 근거 |
|------|------|----------|
| **Container** | Docker Compose | 개발 환경 통일 |
| **Tunnel** | Cloudflare Tunnel (cloudflared) | Zero Trust, 포트 포워딩 불필요, 보안 |
| **CI/CD** | GitHub Actions | 기존 검증 |

### 5.4 Python 의존성 (pyproject.toml) — 2026-02 최신화

```toml
[project]
dependencies = [
    # Orchestration: 1.0 GA 안정화 + 3.x 체크포인터
    "langgraph>=1.0.8",
    "langgraph-checkpoint-postgres>=3.0.4",

    # LLM: 최신 모델 지원
    "instructor>=1.7.0",
    "langfuse>=2.57.0",

    # Web Framework: Pydantic v2 최적화
    "fastapi>=0.119.0",
    "uvicorn>=0.30.0",
    "websockets>=14.0",

    # AST & Static Analysis: 0.24.x 통일 (Breaking Change 대응)
    "tree-sitter>=0.24.7",
    "tree-sitter-python>=0.24.1",
    "tree-sitter-javascript>=0.24.1",
    "tree-sitter-typescript>=0.24.1",
    "tree-sitter-java>=0.24.1",
    "tree-sitter-go>=0.24.1",
    "radon>=6.0.1",
    "lizard>=1.17.10",
    "bandit>=1.8.0",

    # Git & GitHub
    "PyGithub>=2.5.0",
    "gql[aiohttp]>=3.5.0",
    "PyDriller>=2.9",

    # Data & Vector
    "psycopg[binary]>=3.2.0",
    "pgvector>=0.3.6",
    "redis>=5.2.0",
    "datasketch>=1.6.5",

    # Utilities
    "pydantic>=2.12.5",
    "python-Levenshtein>=0.26.0",
    "httpx>=0.28.0",
]
```

> **주의:** `temporalio`는 의존성에 포함되지 **않는다**. 처음부터 설치하지 않는 것이 Clean Slate 원칙이다.

---

## 6. 3계층 HMAS 아키텍처

### 6.1 시스템 아키텍처 개요

```
                    ┌──────────────────────────────────┐
                    │     Frontend (React 19 + D3.js)   │
                    │  Tailwind + WebSocket Streaming    │
                    └──────────────┬───────────────────┘
                                   │ REST + WebSocket
                    ┌──────────────▼───────────────────┐
                    │  Interface Layer (FastAPI Routes)  │
                    │  Job CRUD + Auth + WS Streaming    │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │   Application Layer (LangGraph)    │
                    │  MetaAgent + Supervisor Subgraphs  │
                    │  PostgreSQL Checkpointer           │
                    │  + Langfuse Tracing                │
                    └──────────────┬───────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
   ┌──────────▼──────┐  ┌────────▼────────┐  ┌────────▼────────┐
   │ ForensicSuper   │  │ LogicSuper      │  │ StackSuper      │
   │ (수집/정제/진정성)│  │ (복잡도/품질)    │  │ (전문성/스택)    │
   └──────┬──────────┘  └──────┬──────────┘  └──────┬──────────┘
          │                    │                     │
    ┌─────┼─────┐        ┌────┼────┐          ┌────┼────┐
    │     │     │        │    │    │          │    │    │
   W1    W2   W3-5      W6   W7   W8        W9   W10  W11
```

### 6.2 3계층 HMAS 구조

```
Level 1: MetaAgent (총괄 오케스트레이터)
│
├── Phase 0: InputRouter
│   └── 입력 파싱 + 소스 라우팅
│
├── Phase 1: PlanGenerator
│   └── LLM 기반 실행 계획 동적 생성
│
├── Phase 2: AnalysisDispatcher (Fan-out)
│   ├── Level 2: ForensicSupervisor
│   │   ├── Level 3: CollectorWorker (W1) — GitHub GraphQL + Identity Resolution
│   │   ├── Level 3: CleanerWorker (W2) — Funnel Selection + 노이즈 제거
│   │   ├── Level 3: VibectorWorker (W3) — AI 코드 탐지 (WPM)
│   │   ├── Level 3: CLAVEWorker (W4) — 스타일로메트리
│   │   └── Level 3: DatasketchWorker (W5) — 표절 탐지 (MinHash/LSH)
│   │
│   ├── Level 2: LogicSupervisor
│   │   ├── Level 3: ASTAnalyzerWorker (W6) — Tree-sitter
│   │   ├── Level 3: ComplexityMeterWorker (W7) — Radon/Lizard
│   │   └── Level 3: QualityScannerWorker (W8) — SonarQube
│   │
│   └── Level 2: StackSupervisor (LogicSupervisor 완료 후 실행)
│       ├── Level 3: SkillExtractorWorker (W9)
│       ├── Level 3: APIDepthAnalyzerWorker (W10)
│       └── Level 3: ArchitectureEvaluatorWorker (W11)
│
├── Phase 2.5: ProfileSynthesizer (Fan-in)
│   └── 모든 분석 결과 → UnifiedCandidateProfile + 4대 지표 산출
│
├── Phase 3: QuestionOrchestrator
│   ├── TopicSelector (벡터 검색 기반)
│   ├── QuestionCrafter x N (3전략 병렬)
│   └── EnhancementAgents x 5 (병렬)
│
├── Phase 4: QualityGate
│   ├── Reviewer (품질 검증)
│   └── Reviser (조건부 재생성, 최대 2회)
│
└── Phase 5: OutputAssembler
    ├── IntelBriefGenerator
    ├── DeepAnalysisGenerator
    ├── DecisionSupportGenerator
    └── FinalScriptAssembler
```

### 6.3 Supervisor 내부 Worker 의존성

```
ForensicSupervisor:
  Collector → IdentityResolver → SemanticPruner → [Vibector, CLAVE, Datasketch] (병렬) → Aggregator

LogicSupervisor:
  [ASTAnalyzer, ComplexityMeter, QualityScanner] (완전 병렬) → Aggregator

StackSupervisor (LogicSupervisor의 AST 결과에 의존):
  [SkillExtractor, APIDepthAnalyzer, ArchitectureEvaluator] (완전 병렬) → Aggregator
```

**의존성 제약:**
- ForensicSupervisor와 LogicSupervisor는 **병렬 실행**
- StackSupervisor는 LogicSupervisor **완료 후 실행** (AST 결과 필요)

---

## 7. Identity Resolution Pipeline

review1.md §2.1에서 지적된 **사용자 식별 및 기여분 추출** 결함을 해결하는 핵심 모듈이다.

### 7.1 문제점 (AS-IS)

- 단순 `git clone` → `git blame`으로 전체 분석
- 지원자의 여러 이메일(개인/회사/학교), 닉네임 변경, 다른 컴퓨터 커밋 미고려
- 공백 수정, 파일 이동, 리팩토링까지 '기여'로 잡힘 → 거품 섞인 분석

### 7.2 해결: 3단계 Identity Resolution

#### Step 1: GitHub Node ID 기반 추적

이메일이 바뀌어도 변하지 않는 GitHub 고유 ID(`databaseId`)를 GraphQL로 조회하여 유저를 특정한다.

```python
# infrastructure/github/graphql_client.py
async def get_user_node_id(username: str) -> str:
    """GitHub 고유 ID 조회 — 이메일 변경에도 불변"""
    query = """
    query($login: String!) {
        user(login: $login) {
            databaseId
            email
            name
            contributionsCollection {
                commitContributionsByRepository {
                    repository { nameWithOwner }
                    contributions { totalCount }
                }
            }
        }
    }
    """
    result = await gql_client.execute(query, {"login": username})
    return str(result["user"]["databaseId"])
```

#### Step 2: 동적 `.mailmap` 생성

레포지토리 내 커밋 히스토리에서 이름/이메일 유사도를 분석하여, 동일인으로 추정되는 커밋을 하나로 묶는 클러스터링을 수행한다.

```python
# domain/identity/mailmap_builder.py
def build_dynamic_mailmap(
    git_authors: list[GitAuthor],
    github_profile: GitHubProfile,
    github_node_id: str,
    threshold: float = 0.75,
) -> list[MailmapEntry]:
    """동적 .mailmap 생성 — 동일인 이메일 클러스터링"""
    entries = []

    # 1. noreply email 패턴 매칭 (확정적)
    # 예: 12345+username@users.noreply.github.com
    for author in git_authors:
        if "noreply.github.com" in author.email:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="high",
            ))

    # 2. GitHub profile name/email 교차 매칭 (확정적)
    for author in git_authors:
        if author.email == github_profile.email:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="high",
            ))

    # 3. 이름 Levenshtein distance < threshold → 클러스터링 (휴리스틱)
    for author in git_authors:
        similarity = 1 - (levenshtein(author.name, github_profile.name)
                         / max(len(author.name), len(github_profile.name)))
        if similarity >= threshold:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="medium",
            ))

    # 4. 동일 커스텀 도메인 이메일 → 후보 추가 (약한 신호)
    profile_domain = github_profile.email.split("@")[-1]
    for author in git_authors:
        if author.email.split("@")[-1] == profile_domain:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="low",
            ))

    return deduplicate(entries)
```

#### Step 3: 3단계 포렌식 쿼리

```
Level 1 (Git Internal):
  git blame -w -M -C -C --line-porcelain
  → 공백(-w), 파일 이동(-M), 코드 복사(-C) 제외한 순수 로직 작성분만 추출

Level 2 (Semantic Pruning):
  Tree-sitter AST 파싱 →
  import 구문, 주석, Config 설정, 자동 생성 코드(Generated Code) 제거 →
  함수/클래스 본문만 보존

Level 3 (Authenticity Check):
  Vibector(WPM) + CLAVE(스타일로메트리) + Datasketch(표절) 교차 검증
```

### 7.3 Domain 모델

```python
# domain/identity/models.py
from pydantic import BaseModel

class MailmapEntry(BaseModel):
    canonical: str             # 정규 이름
    canonical_email: str       # 정규 이메일
    alias_name: str            # 별칭 이름
    alias_email: str           # 별칭 이메일
    confidence: str            # "high" | "medium" | "low"

class IdentityCluster(BaseModel):
    github_node_id: str
    canonical_name: str
    canonical_email: str
    aliases: list[MailmapEntry]
    total_commits: int
    verified_commits: int

class BlameLineAttribution(BaseModel):
    file_path: str
    line_number: int
    content: str
    author_name: str
    author_email: str
    commit_sha: str
    is_move: bool              # -M 감지
    is_copy: bool              # -C 감지
    is_whitespace_only: bool   # -w 감지

class PureContribution(BaseModel):
    file_path: str
    language: str
    total_lines: int           # 전체 blame 라인
    pure_logic_lines: int      # 노이즈 제거 후 순수 로직
    removed_imports: int
    removed_comments: int
    removed_config: int
    removed_generated: int
    function_bodies: list[str] # 보존된 함수/클래스 본문
```

---

## 8. JD 기반 Funnel Selection

review1.md §2.2에서 지적된 **모든 레포 분석 = 토큰 낭비** 문제를 해결한다.

### 8.1 문제점 (AS-IS)

- 백엔드 지원자의 3년 전 React 토이 프로젝트, 알고리즘 문제 풀이 레포까지 심층 분석
- LLM 토큰 + 분석 시간 낭비
- "질문은 JD 기반"이라는 원칙과 모순

### 8.2 해결: 3단계 Funnel Architecture

```
전체 레포 목록 (GraphQL 수집)
        │
        ▼ Stage 1: Hard Filter
[Fork, 크기, 최근 push 날짜, 유저 기여도 필터]
        │
        ▼ Stage 2: Relevance Scoring
[JD tech_stack + requirements 기반 LLM 스코어링]
        │
        ▼ Stage 3: Vector Similarity
[JD 텍스트 ↔ README/Description 벡터 유사도]
        │
        ▼ 상위 3-5개 프로젝트만 심층 분석
```

### 8.3 Domain 규칙

```python
# domain/matching/funnel_rules.py

class FunnelConfig(BaseModel):
    min_push_days: int = 365     # 최근 1년 내 push
    min_stars: int = 0
    max_repos: int = 20          # GraphQL 수집 상한
    top_k: int = 5               # 최종 선별 개수
    org_contribution_threshold: float = 0.10  # Org 레포 기여도 최소 10%
    vector_similarity_min: float = 0.60       # 벡터 유사도 최소

def stage1_hard_filter(
    repos: list[RepoMetadata],
    jd_languages: list[str],
    config: FunnelConfig,
) -> list[RepoMetadata]:
    """Stage 1: 메타데이터 기반 하드 필터"""
    filtered = []
    for repo in repos:
        # Fork 제외
        if repo.is_fork:
            continue
        # 최근 push 날짜 확인
        if repo.days_since_push > config.min_push_days:
            continue
        # Org 레포: 기여도 임계치 확인
        if repo.is_org_repo and repo.user_contribution_ratio < config.org_contribution_threshold:
            continue
        # 언어 교집합 확인 (JD에서 요구하는 언어가 레포에 있는지)
        if jd_languages and not set(repo.languages).intersection(set(jd_languages)):
            continue
        filtered.append(repo)
    return filtered

def stage2_relevance_score(
    repos: list[RepoMetadata],
    jd_requirements: list[str],
    jd_tech_stack: list[str],
) -> list[tuple[RepoMetadata, float]]:
    """Stage 2: JD 기반 적합성 스코어링"""
    scored = []
    for repo in repos:
        score = 0.0
        # tech_stack 매칭 (LLM 분석 결과 활용)
        matched_techs = set(repo.detected_tech_stack).intersection(set(jd_tech_stack))
        score += len(matched_techs) * 0.3
        # 최근 활동 가산
        if repo.days_since_push < 90:
            score += 0.2
        # 코드 규모 가산 (너무 작은 레포 감점)
        if repo.total_loc > 500:
            score += 0.1
        scored.append((repo, score))
    return sorted(scored, key=lambda x: x[1], reverse=True)

def stage3_should_include(
    similarity: float,
    config: FunnelConfig,
) -> bool:
    """Stage 3: 벡터 유사도 임계값 판정"""
    return similarity >= config.vector_similarity_min
```

---

## 9. Worker Agent 상세 설계 (Tree-sitter 0.24 반영)

### 9.0 Tree-sitter 0.24 Breaking Change 대응

> **extra.md 반영:** Tree-sitter 0.24부터 `.so` 파일 빌드 방식(`Language.build_library`)이 **폐기**되었다. Python 패키지 바인딩을 직접 사용하는 방식으로 구현해야 한다.

```python
# infrastructure/analysis/tree_sitter_adapter.py
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava

class TreeSitterAdapter:
    def __init__(self):
        # 0.24.x: 언어별 패키지에서 직접 language 객체 로딩
        self.languages = {
            "python": Language(tspython.language()),
            "javascript": Language(tsjs.language()),
            "typescript": Language(tsjs.language()),
            "go": Language(tsgo.language()),
            "java": Language(tsjava.language()),
        }

    def get_parser(self, lang_name: str) -> Parser:
        """Parser는 Thread-safe하지 않으므로 매 요청마다 생성"""
        if lang_name not in self.languages:
            raise ValueError(f"Unsupported language: {lang_name}")
        return Parser(self.languages[lang_name])

    def parse_code(self, code: str, lang_name: str):
        parser = self.get_parser(lang_name)
        return parser.parse(bytes(code, "utf8"))

    def extract_functions(self, root_node, lang_name: str) -> list[dict]:
        """Query API로 함수/클래스 추출"""
        query_scm = """
        (function_definition
          name: (identifier) @func.name)
        """
        query = self.languages[lang_name].query(query_scm)
        captures = query.captures(root_node)
        return [{"name": c[0].text.decode(), "node": c[0]} for c in captures]
```

### 9.1 Worker 총괄표

| # | Worker | Supervisor | 도구 | 입력 | 출력 | LLM |
|---|--------|------------|------|------|------|-----|
| W1 | CollectorWorker | Forensic | GraphQL, PyDriller, BrightData | github_urls, linkedin_url | collected_repos, identity_cluster | X |
| W2 | CleanerWorker | Forensic | git blame -w -M -C, Tree-sitter | raw_diffs, identity_cluster | cleaned_diffs, pure_contributions | X |
| W3 | VibectorWorker | Forensic | Git log, WPM calculator | cleaned_diffs, commit_timestamps | vibector_scores (AI 의심 구간) | X |
| W4 | CLAVEWorker | Forensic | Stylometry analyzer | cleaned_diffs | clave_fingerprint (저자 지문) | O |
| W5 | DatasketchWorker | Forensic | Datasketch (MinHash/LSH) | cleaned_diffs | plagiarism_report (유사도 맵) | X |
| W6 | ASTAnalyzerWorker | Logic | Tree-sitter (5개 언어) | cleaned_diffs, repo_files | ast_trees, semantic_diffs, code_chunks | X |
| W7 | ComplexityMeterWorker | Logic | Radon, Lizard, cloc | repo_files | complexity_metrics (CC, Halstead, MI) | X |
| W8 | QualityScannerWorker | Logic | SonarQube API, Bandit | repo_url | quality_report (부채, 스멜, 취약점) | X |
| W9 | SkillExtractorWorker | Stack | Tree-sitter, import parser | ast_analysis, jd_tech_stack | skill_extraction (기술 매핑) | O |
| W10 | APIDepthAnalyzerWorker | Stack | AST call graph | ast_analysis | api_depth_scores (API 활용 깊이) | O |
| W11 | ArchitectureEvaluatorWorker | Stack | AST pattern detector | ast_analysis | architecture_eval (패턴/SOLID) | O |

### 9.2 Worker 구현 패턴

#### BaseWorker (Template Method Pattern)

```python
# application/nodes/base_worker.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Generic, TypeVar

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)

class BaseWorker(ABC, Generic[TInput, TOutput]):
    """모든 Worker의 기본 클래스"""

    @abstractmethod
    def validate_input(self, input_data: TInput) -> bool:
        """입력 데이터 검증"""
        ...

    @abstractmethod
    async def execute(self, input_data: TInput) -> TOutput:
        """핵심 분석 로직"""
        ...

    @abstractmethod
    def handle_error(self, error: Exception, input_data: TInput) -> TOutput:
        """에러 시 Graceful Degradation"""
        ...

    async def run(self, state: dict) -> dict:
        """LangGraph 노드로 실행 (Template Method)"""
        input_data = self.parse_input(state)

        if not self.validate_input(input_data):
            return self.empty_result()

        try:
            result = await self.execute(input_data)
            return self.format_output(result)
        except Exception as e:
            return self.format_output(self.handle_error(e, input_data))
```

#### Strategy + Factory Pattern (언어별 분석)

```python
# infrastructure/analysis/strategy.py
class AnalysisStrategy(ABC):
    @abstractmethod
    def analyze_complexity(self, file_path: str) -> dict: ...

    @abstractmethod
    def parse_ast(self, code: str) -> dict: ...

class PythonAnalysis(AnalysisStrategy):
    def analyze_complexity(self, file_path):
        # Radon CC + Halstead
        ...
    def parse_ast(self, code):
        # Tree-sitter python grammar
        ...

class JavaScriptAnalysis(AnalysisStrategy):
    """TypeScript도 동일 Strategy 사용"""
    ...

class AnalysisStrategyFactory:
    _strategies = {
        "python": PythonAnalysis,
        "javascript": JavaScriptAnalysis,
        "typescript": JavaScriptAnalysis,
        "java": JavaAnalysis,
        "go": GoAnalysis,
    }

    @classmethod
    def create(cls, language: str) -> AnalysisStrategy:
        strategy_cls = cls._strategies.get(language)
        if not strategy_cls:
            return GenericAnalysis()
        return strategy_cls()
```

### 9.3 노드 함수 원칙: Thin Wrapper

노드 함수는 **domain 호출 + infrastructure 호출의 조합**이다. 비즈니스 로직을 직접 작성하지 않는다.

```python
# application/nodes/identity_resolver.py
async def identity_resolver_node(state: ForensicState) -> dict:
    """DDD 원칙: 노드 = domain + infrastructure 조합"""
    # 1. infrastructure: git authors 추출
    authors = await git_adapter.extract_authors(state["clone_dir"])

    # 2. infrastructure: GitHub Node ID 조회
    node_id = await github_client.get_user_node_id(state["candidate_username"])

    # 3. domain: mailmap 생성 (순수 비즈니스 로직)
    mailmap = mailmap_builder.build_dynamic_mailmap(
        authors, state["github_profile"], node_id
    )

    # 4. infrastructure: .mailmap 파일 쓰기
    await mailmap_writer.write(state["clone_dir"], mailmap)

    # 5. infrastructure: git blame -w -M -C 실행
    blame_lines = await blame_runner.run_git_blame(
        state["clone_dir"], state["target_files"], mailmap
    )

    # 6. domain: blame 필터링 (순수 비즈니스 로직)
    identity_cluster = IdentityCluster.from_mailmap(mailmap, node_id)
    filtered = blame_filter.filter_blame_lines(blame_lines, identity_cluster)

    return {"blame_attributions": filtered, "identity_cluster": identity_cluster}
```

---

## 10. LangGraph 그래프 설계 (Reference Passing)

> **extra.md 반영:** State 객체에 Raw Data(AST, Diff 전문)를 직접 넣으면 DB Checkpoint 크기가 폭발하고 성능이 저하된다. **DB Primary Key(UUID)만 전달**하는 Reference Passing 패턴을 적용한다.

### 10.1 MetaState 정의 (Reference Passing 적용)

```python
# application/states/meta_state.py
from typing import TypedDict, Optional

class MetaState(TypedDict):
    # Core Context
    job_id: str

    # References (Not Raw Data — DB ID만 전달)
    input_data_ref: str                          # jobs 테이블 ID
    identity_cluster_ref: Optional[str]          # identity_resolutions 테이블 ID

    # Analysis Result References (analysis_results 테이블 ID)
    forensic_result_ref: Optional[str]
    logic_result_ref: Optional[str]
    stack_result_ref: Optional[str]

    # Metrics (가벼우므로 State에 포함 가능)
    candidate_scores: Optional[dict]             # 4대 지표 점수

    # Flow Control
    status: str
    revision_count: int                          # 최대 2회 루프
    errors: list[str]
```

### 10.1.1 노드 구현 패턴: Load → Process → Save → Return Ref

모든 노드는 아래 4단계를 따른다. State에는 **결과 자체**가 아닌 **결과가 저장된 DB의 ID(참조)**만 리턴한다.

```python
# application/nodes/logic_supervisor.py
async def logic_supervisor_node(state: MetaState) -> dict:
    job_id = state["job_id"]

    # 1. Load: DB에서 필요한 데이터 조회 (ref 기반)
    repo_files = await repo_repository.get_files(job_id)

    # 2. Process: 분석 수행
    ast_result = await ast_analyzer.analyze(repo_files)

    # 3. Save: 대용량 결과를 DB에 저장
    result_id = await analysis_repository.save_result(
        job_id, "logic_supervisor", ast_result
    )

    # 4. Return Ref: ID만 리턴 (State Checkpoint에는 ID만 기록)
    return {"logic_result_ref": result_id}
```

### 10.2 MetaAgent Graph (Level 1)

```python
# application/graphs/meta_graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

def build_meta_graph() -> StateGraph:
    builder = StateGraph(MetaState)

    # 노드 등록
    builder.add_node("input_router", input_router_node)
    builder.add_node("plan_generator", plan_generator_node)
    builder.add_node("forensic_supervisor", forensic_subgraph)
    builder.add_node("logic_supervisor", logic_subgraph)
    builder.add_node("stack_supervisor", stack_subgraph)
    builder.add_node("profile_synthesizer", profile_synthesizer_node)
    builder.add_node("question_orchestrator", question_subgraph)
    builder.add_node("quality_gate", quality_gate_node)
    builder.add_node("output_assembler", output_assembler_node)

    # Phase 0-1: 순차
    builder.add_edge(START, "input_router")
    builder.add_edge("input_router", "plan_generator")

    # Phase 2: Fan-out (ForensicSuper ∥ LogicSuper → StackSuper)
    builder.add_edge("plan_generator", "forensic_supervisor")
    builder.add_edge("plan_generator", "logic_supervisor")
    builder.add_edge("logic_supervisor", "stack_supervisor")  # AST 의존

    # Phase 2.5: Fan-in
    builder.add_edge("forensic_supervisor", "profile_synthesizer")
    builder.add_edge("stack_supervisor", "profile_synthesizer")

    # Phase 3-4: 순차 + 조건부 루프
    builder.add_edge("profile_synthesizer", "question_orchestrator")
    builder.add_edge("question_orchestrator", "quality_gate")

    builder.add_conditional_edges(
        "quality_gate",
        should_revise,  # revision_count < 2 && has_flagged
        {"revise": "question_orchestrator", "approve": "output_assembler"},
    )

    # Phase 5: 최종 출력
    builder.add_edge("output_assembler", END)

    return builder
```

### 10.3 ForensicSupervisor Subgraph (Level 2)

```python
# application/graphs/forensic_graph.py
class ForensicState(TypedDict):
    github_urls: list[str]
    candidate_username: str | None
    linkedin_url: str | None
    jd_languages: list[str]
    jd_tech_stack: list[str]

    # Worker 결과
    collected_repos: list[dict]
    identity_cluster: dict
    blame_attributions: list[dict]
    pure_contributions: list[dict]
    cleaned_diffs: list[dict]
    vibector_scores: list[dict]
    clave_fingerprint: dict
    plagiarism_report: dict

    # 통합
    forensic_summary: dict
    authenticity_score: float

def build_forensic_graph() -> StateGraph:
    builder = StateGraph(ForensicState)

    builder.add_node("collector", collector_worker)          # GraphQL + Funnel Stage 1-3
    builder.add_node("identity_resolver", identity_resolver) # Mailmap + Blame
    builder.add_node("semantic_pruner", semantic_pruner)      # Tree-sitter AST pruning
    builder.add_node("vibector", vibector_worker)             # WPM 분석
    builder.add_node("clave", clave_worker)                   # 스타일로메트리
    builder.add_node("datasketch", datasketch_worker)         # 표절 탐지
    builder.add_node("forensic_aggregator", forensic_aggregator)

    # 순차: collector → identity_resolver → semantic_pruner
    builder.add_edge(START, "collector")
    builder.add_edge("collector", "identity_resolver")
    builder.add_edge("identity_resolver", "semantic_pruner")

    # 병렬: pruner 후 진정성 검증 3개 동시
    builder.add_edge("semantic_pruner", "vibector")
    builder.add_edge("semantic_pruner", "clave")
    builder.add_edge("semantic_pruner", "datasketch")

    # Fan-in
    builder.add_edge("vibector", "forensic_aggregator")
    builder.add_edge("clave", "forensic_aggregator")
    builder.add_edge("datasketch", "forensic_aggregator")

    return builder
```

### 10.4 LogicSupervisor / StackSupervisor Subgraphs

```python
# application/graphs/logic_graph.py
class LogicState(TypedDict):
    cleaned_diffs: list[dict]
    repo_paths: list[str]
    ast_analysis: list[dict]
    complexity_metrics: list[dict]
    quality_report: dict
    logic_summary: dict
    logic_score: float

def build_logic_graph() -> StateGraph:
    builder = StateGraph(LogicState)
    builder.add_node("ast_analyzer", ast_analyzer_worker)
    builder.add_node("complexity_meter", complexity_meter_worker)
    builder.add_node("quality_scanner", quality_scanner_worker)
    builder.add_node("logic_aggregator", logic_aggregator)

    # 3개 Worker 완전 병렬
    builder.add_edge(START, "ast_analyzer")
    builder.add_edge(START, "complexity_meter")
    builder.add_edge(START, "quality_scanner")
    builder.add_edge("ast_analyzer", "logic_aggregator")
    builder.add_edge("complexity_meter", "logic_aggregator")
    builder.add_edge("quality_scanner", "logic_aggregator")
    return builder

# application/graphs/stack_graph.py
class StackState(TypedDict):
    ast_analysis: list[dict]    # LogicSupervisor에서 전달
    cleaned_diffs: list[dict]
    jd_tech_stack: list[str]
    skill_extraction: dict
    api_depth_scores: list[dict]
    architecture_eval: dict
    stack_summary: dict
    mastery_score: float

def build_stack_graph() -> StateGraph:
    builder = StateGraph(StackState)
    builder.add_node("skill_extractor", skill_extractor_worker)
    builder.add_node("api_depth_analyzer", api_depth_analyzer_worker)
    builder.add_node("architecture_evaluator", architecture_evaluator_worker)
    builder.add_node("stack_aggregator", stack_aggregator)

    # 3개 Worker 완전 병렬
    builder.add_edge(START, "skill_extractor")
    builder.add_edge(START, "api_depth_analyzer")
    builder.add_edge(START, "architecture_evaluator")
    builder.add_edge("skill_extractor", "stack_aggregator")
    builder.add_edge("api_depth_analyzer", "stack_aggregator")
    builder.add_edge("architecture_evaluator", "stack_aggregator")
    return builder
```

### 10.5 FastAPI 통합

```python
# interface/api/routes/jobs.py
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def run_analysis(job_id: str, input_data: dict):
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        graph = build_meta_graph().compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": job_id}}

        async for event in graph.astream(input_data, config, stream_mode="updates"):
            # WebSocket으로 실시간 전송
            await ws_manager.broadcast(job_id, event)
```

---

## 11. 4대 핵심 지표 체계

### 11.1 점수 산출 공식

```
최종 점수 = 0.30 × 논리력 + 0.30 × 전문성 + 0.20 × 안정성 + 0.20 × 진정성
```

### 11.2 각 지표 세부 구성

| 주지표 | 세부 지표 | 산출 도구 | 내부 가중치 | Worker |
|--------|----------|----------|------------|--------|
| **논리력 (30%)** | | | | |
| | 순환 복잡도 (CC) | Radon/Lizard | 40% | W7 |
| | 할스테드 난이도 (D) | Radon | 30% | W7 |
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

### 11.3 점수 산출 수학적 모델

```python
# domain/scoring/calculator.py

# 논리력: 복잡도가 낮을수록 고득점
Score_logic = 1 / (1 + α × M_avg + β × D_avg) × 100

# 전문성: API 활용 깊이 가중치 합산
Score_mastery = Σ(Count_API × Weight_Level)

# 안정성: 부채와 Churn이 낮을수록 고득점
Score_stability = max(0, 100 - (tech_debt_ratio × 40 + churn_ratio × 30 + smell_density × 30))

# 진정성: 순수 기여 비율
Index_authenticity = (LoC_total - LoC_AI - LoC_copy) / LoC_total × 100
```

### 11.4 신뢰도 표시 체계

| 신뢰도 | 조건 | 표시 |
|--------|------|------|
| 🟢 높음 | 데이터 소스 3개 이상 + 공개 레포 5개 이상 | 초록색 |
| 🟡 중간 | 데이터 소스 2개 + 공개 레포 2-4개 | 노란색 |
| 🔴 낮음 | 데이터 소스 1개 또는 공개 레포 1개 이하 | 빨간색 |

---

## 12. Pydantic 모델 + Instructor 통합

### 12.1 구조화 출력 모델

> **extra.md 반영:** Pydantic v2에서는 `class Config` 대신 `model_config = ConfigDict(strict=True)`를 사용한다.

```python
# domain/analysis/models.py
from pydantic import BaseModel, Field, ConfigDict

class ComplexityMetrics(BaseModel):
    model_config = ConfigDict(strict=True)  # Pydantic v2

    cyclomatic_complexity: float = Field(ge=0, description="McCabe 순환 복잡도 평균")
    halstead_difficulty: float = Field(ge=0, description="Halstead 난이도")
    halstead_volume: float = Field(ge=0, description="Halstead 볼륨")
    maintainability_index: float = Field(ge=0, le=100, description="유지보수 지수")
    cognitive_complexity: float = Field(ge=0, description="인지적 복잡도")

class AuthenticityScore(BaseModel):
    model_config = ConfigDict(strict=True)

    human_typing_ratio: float = Field(ge=0, le=1)
    originality_ratio: float = Field(ge=0, le=1)
    ai_code_suspicion: float = Field(ge=0, le=1)
    plagiarism_ratio: float = Field(ge=0, le=1)
    style_consistency: float = Field(ge=0, le=1)

class SkillAssessment(BaseModel):
    model_config = ConfigDict(strict=True)

    skill_name: str
    proficiency: str  # beginner | intermediate | advanced | expert
    evidence_count: int = Field(ge=0)
    evidence_sources: list[str]  # ["github:repo1", "linkedin", "resume"]
    confidence: str  # "high" | "medium" | "low"
```

### 12.2 면접 질문 모델

```python
# domain/question/models.py
class InterviewQuestion(BaseModel):
    """Instructor로 LLM이 직접 생성하는 구조화된 면접 질문"""
    model_config = ConfigDict(strict=True)  # Pydantic v2

    question_id: str
    category: str      # technical_depth | execution_ownership | communication | role_fit | risk_flags
    strategy: str      # negative_selection | intentional_complexity | evolution
    difficulty: str    # easy | medium | hard
    question_text: str = Field(min_length=20, max_length=500)
    intent: str = Field(description="이 질문의 의도 (비개발자용)")
    code_reference: str | None = Field(description="관련 코드 파일:라인")
    expected_answer_guide: str = Field(description="비개발자도 이해 가능한 예상 답변 가이드")
    red_flags: list[str] = Field(description="주의해야 할 답변 패턴")
    follow_up_triggers: list[str] = Field(description="파생 질문 트리거 조건")
    terminology: list[dict] = Field(description="질문에 포함된 전문 용어 설명")
```

### 12.3 Instructor + Langfuse 통합

```python
# infrastructure/llm/instructor_client.py
import instructor
from langfuse.decorators import observe

@observe(name="generate_interview_question")
async def generate_question(topic: dict, context: dict) -> InterviewQuestion:
    """Langfuse 추적 + Instructor 구조화 출력"""
    # 1. Langfuse에서 프롬프트 가져오기
    prompt = langfuse.get_prompt("question_craft_v5", label="production")

    # 2. Instructor로 구조화 출력 생성
    result = await client.chat.completions.create(
        model=prompt.config.get("model", "kimi-k2.5"),
        response_model=InterviewQuestion,
        messages=prompt.compile(topic=topic, context=context),
        temperature=prompt.config.get("temperature", 0.7),
        max_retries=3,  # Pydantic 검증 실패 시 자동 재시도
    )
    return result
```

---

## 13. 벡터 검색 (RAG) 전략

### 13.1 임베딩 파이프라인

```
코드 파일 → Tree-sitter AST → 함수/클래스 단위 청크 분할
                                       │
                                       ▼
                              임베딩 모델 (text-embedding-3-small)
                                       │
                                       ▼
                              pgvector 저장 (Vector(1536))
                                       │
                              ┌────────┼────────┐
                              │        │        │
                          kind: code  kind: jd  kind: resume
```

### 13.2 청크 전략

| 소스 | 청크 단위 | 메타데이터 |
|------|----------|-----------|
| 코드 | 함수/클래스 (AST 기반) | file_path, language, complexity, author |
| JD | 섹션별 (자격요건, 우대사항) | section_type, keywords |
| 이력서 | 경력/프로젝트별 | company, role, duration |
| LinkedIn | 프로필 섹션별 | section_type |

### 13.3 JD-Repo 유사도 비교 (Funnel Stage 3 용)

```python
# infrastructure/embedding/pgvector_store.py
async def compute_jd_repo_similarity(
    jd_text: str,
    repo_readme: str,
    repo_description: str,
) -> float:
    """JD 텍스트와 레포 README/Description 간 벡터 유사도 계산"""
    jd_embedding = await embed(jd_text)
    repo_text = f"{repo_description}\n{repo_readme}"
    repo_embedding = await embed(repo_text)
    return cosine_similarity(jd_embedding, repo_embedding)
```

### 13.4 컨텍스트 예산 관리

```python
# application/use_cases/context_budget.py
class ContextBudget:
    MAX_TOKENS = 8000

    ALLOCATION = {
        "system_prompt": 1500,
        "jd_context": 1500,
        "code_chunks": 3000,      # 벡터 검색된 코드 청크
        "candidate_profile": 1000,
        "topic_context": 1000,
    }

    def allocate(self, section: str, content: str) -> str:
        max_tokens = self.ALLOCATION[section]
        return truncate_to_tokens(content, max_tokens)
```

---

## 14. 프롬프트 엔지니어링

### 14.1 프롬프트 전략

| 전략 | 적용 대상 | 설명 |
|------|----------|------|
| Few-shot | 질문 생성, 디자인 패턴 탐지 | 2-3개 예시로 출력 형식/품질 가이드 |
| Chain-of-Thought | 복잡도 해석, 결정 생성 | 단계별 추론 유도 |
| Fact-Grounded | 모든 판단 프롬프트 | "결정론적 수치를 참조하여" 전제 |
| Negative Prompting | 질문 생성 | "일반적/교과서적 질문은 제외" |

### 14.2 질문 생성 3전략

#### 전략 A: Negative Selection (안 한 이유 묻기)

```
분석 로직: AST 분석 결과, 사용될 법하지만 사용되지 않은 패턴/기술 감지
질문 예시: "async/await를 적용하지 않고 동기식으로 처리하셨습니다.
           동시성 이슈를 우려하여 일부러 그렇게 설계하신 건가요?"
검증 포인트:
  ✅ 합격: 트레이드오프 이해 ("데이터 순서가 중요해서")
  ❌ 불합격: "그냥 짜다 보니 그렇게 됐습니다"
```

#### 전략 B: Intentional Complexity (높은 난이도 의도 묻기)

```
분석 로직: Halstead 난이도(D)와 순환 복잡도(M)가 국소적으로 매우 높은 구간 식별
질문 예시: "validateToken 메서드는 순환 복잡도가 매우 높습니다(분기문 15개).
           이 부분을 분리하지 않고 유지한 아키텍처적 이유가 있나요?"
검증 포인트:
  ✅ 합격: 응집도 / 보안 감사 용이성 등 구체적 이유
  ❌ 불합격: "복잡한 줄 몰랐습니다"
```

#### 전략 C: Code Evolution (변화 과정 묻기)

```
분석 로직: Git 히스토리에서 Code Churn이 높았던 구간, 대규모 리팩토링 지점 추적
질문 예시: "PaymentGateway 모듈이 초기 버전에서 3번 구조가 크게 바뀌었습니다.
           초기 설계에서 예상하지 못했던 문제는 구체적으로 무엇이었나요?"
검증 포인트:
  ✅ 합격: 구체적인 문제와 해결 과정 설명 (해당 코드를 직접 고민해본 사람만 답변 가능)
  ❌ 불합격: 최종 결과물만 설명 (AI는 수정 역사를 모름)
```

### 14.3 프롬프트 관리 흐름

```
Langfuse UI에서 프롬프트 편집/버전 관리
         │
         ▼
    get_prompt("question_craft_v5", label="production")
         │
         ▼ (Langfuse 장애 시)
    YAML fallback (infrastructure/llm/prompts/)
         │
         ▼
    Instructor + Pydantic 검증
         │
         ▼ (검증 실패 시)
    자동 재시도 (최대 3회, 에러 메시지 포함)
```

---

## 15. 인프라 구성 (Docker + Cloudflare Tunnel)

> **extra.md 반영:** Cloudflare Tunnel은 **독립 프로젝트(`infra-tunnel/`)**로 분리. SonarQube는 **Docker Profile로 On-Demand** 실행. Backend/Frontend **별도 Dockerfile + 빌드 컨텍스트**. init.sql에 **LangGraph Checkpoint 테이블** 포함.

### 15.0 인프라 분리 원칙

```
/ (Root)
├── infra-tunnel/             # [인프라] Cloudflare Tunnel 전용 (독립 생명주기)
│   ├── docker-compose.yml    # cloudflared + jittda-public 네트워크 생성
│   └── .env                  # TUNNEL_TOKEN
│
└── jittda/                   # [애플리케이션] Jittda 서비스
    ├── docker-compose.yml    # frontend가 외부 네트워크(jittda-public) 참조
    ├── backend/Dockerfile
    ├── frontend/Dockerfile
    └── infra/postgres/init.sql
```

**분리 이유:**
- 앱을 배포/재시작해도 **터널 연결은 유지**
- 여러 프로젝트가 하나의 터널 네트워크를 **공유 가능**
- 인프라와 애플리케이션의 **생명주기 독립**

### 15.1 Step 1: Cloudflare Tunnel 독립 프로젝트

```yaml
# infra-tunnel/docker-compose.yml
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: jittda_tunnel_gateway
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${TUNNEL_TOKEN}
    networks:
      - public_net

# 핵심: 명시적 네트워크 이름 지정 (다른 컴포즈에서 참조할 이름)
networks:
  public_net:
    name: jittda-public
    driver: bridge
```

**실행:**
```bash
cd infra-tunnel/
echo "TUNNEL_TOKEN=eyJh..." > .env
docker compose up -d
# → jittda-public 네트워크 생성 + 터널 대기
```

### 15.2 Step 2: Jittda 애플리케이션 Docker Compose

```yaml
# jittda/docker-compose.yml
# Clean Slate: Temporal/cloudflared가 존재하지 않음

services:
  # --- Data Layer (내부망 전용) ---
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: jittda
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 5
    networks:
      - internal_net

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - internal_net

  sonarqube:
    image: sonarqube:community
    profiles: ["analysis"]    # 기본 up 시 실행되지 않음 — On-Demand
    environment:
      - SONAR_JDBC_URL=jdbc:postgresql://postgres:5432/sonarqube
      - SONAR_JDBC_USERNAME=postgres
      - SONAR_JDBC_PASSWORD=postgres
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "9000:9000"
    networks:
      - internal_net

  # --- Application Layer ---
  backend:
    build:
      context: ./backend            # 중요: backend 디렉토리를 컨텍스트로 사용
      dockerfile: Dockerfile
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/jittda
      - REDIS_URL=redis://redis:6379
      - LANGGRAPH_CHECKPOINTER_URI=postgresql://postgres:postgres@postgres:5432/jittda
      - SONAR_ON_DEMAND=true
      - LANGFUSE_HOST=${LANGFUSE_HOST}
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - KIMI_API_KEY=${KIMI_API_KEY}
    volumes:
      - ./backend/src:/app/src      # 개발 시 Hot Reload
    ports:
      - "8000:8000"
    networks:
      - internal_net

  frontend:
    build:
      context: ./frontend           # 중요: frontend 디렉토리를 컨텍스트로 사용
      dockerfile: Dockerfile
      target: development           # 개발용 스테이지
    container_name: jittda_frontend  # 터널에서 바라볼 호스트네임 고정
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./frontend/src:/app/src     # 개발 시 Hot Reload
    ports:
      - "3000:3000"
    networks:
      - internal_net                # 백엔드와 통신용
      - external_tunnel_net         # 터널과 통신용 (외부 노출)

  sonar-scanner:
    image: sonarsource/sonar-scanner-cli:latest
    profiles: ["analysis"]           # 분석 시에만: docker compose --profile analysis up sonar-scanner
    depends_on:
      sonarqube:
        condition: service_healthy
    networks:
      - internal_net

volumes:
  postgres_data:
  redis_data:
  sonarqube_data:
  sonarqube_extensions:

networks:
  internal_net:
    driver: bridge

  # infra-tunnel에서 생성한 외부 네트워크 참조
  external_tunnel_net:
    name: jittda-public
    external: true
```

### 15.3 Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# System Dependencies (Git: PyDriller/Cloning 필수)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python Dependencies (캐싱 레이어: requirements 먼저 복사)
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy Application Code
COPY . .

# Environment
ENV PYTHONPATH=/app/src

# Run
CMD ["uvicorn", "src.interface.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 15.4 Frontend Dockerfile (Multi-stage)

```dockerfile
# frontend/Dockerfile

# Stage 1: Base & Install Dependencies
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Development (Hot Reload)
FROM base AS development
COPY . .
CMD ["npm", "run", "dev", "--", "--host"]

# Stage 3: Builder (Production)
FROM base AS builder
COPY . .
RUN npm run build

# Stage 4: Production Serve (Nginx)
FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 15.5 Fresh init.sql (LangGraph Checkpoint 포함)

```sql
-- infra/postgres/init.sql
-- Clean Slate: Alembic 히스토리 없이 최적화된 단일 스키마

-- 확장 모듈
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- SonarQube 전용 DB
CREATE DATABASE sonarqube;

-- ============================================================
-- LangGraph Checkpoint (3.0.x 호환)
-- ============================================================
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint BYTEA,
    metadata BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- ============================================================
-- 비즈니스 테이블
-- ============================================================

-- 사용자
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    oauth_provider VARCHAR(20),
    oauth_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 분석 Job
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    langgraph_thread_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',  -- pending | running | completed | failed
    progress FLOAT DEFAULT 0.0,
    input_data JSONB NOT NULL,
    result_data JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_jobs_user ON jobs(user_id);
CREATE INDEX idx_jobs_thread ON jobs(langgraph_thread_id);
CREATE INDEX idx_jobs_status ON jobs(status);

-- 분석 결과 (Worker별 — Reference Passing의 저장소)
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    worker_name VARCHAR(50) NOT NULL,
    supervisor_name VARCHAR(30) NOT NULL,
    result_data JSONB NOT NULL,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_analysis_job ON analysis_results(job_id);
CREATE INDEX idx_analysis_worker ON analysis_results(worker_name);

-- 4대 지표 점수
CREATE TABLE candidate_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    logic_score FLOAT NOT NULL,
    mastery_score FLOAT NOT NULL,
    stability_score FLOAT NOT NULL,
    authenticity_score FLOAT NOT NULL,
    weighted_total FLOAT NOT NULL,
    confidence VARCHAR(10) NOT NULL,  -- high | medium | low
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id)
);

-- Identity Resolution 결과
CREATE TABLE identity_resolutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    github_node_id VARCHAR(50),
    canonical_name VARCHAR(100),
    canonical_email VARCHAR(200),
    mailmap_entries JSONB,
    total_commits INT DEFAULT 0,
    verified_commits INT DEFAULT 0,
    pure_logic_lines INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id)
);

-- SonarQube 프로젝트 매핑
CREATE TABLE sonarqube_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    project_key VARCHAR(200) NOT NULL,
    repo_url TEXT,
    scan_status VARCHAR(20) DEFAULT 'pending',
    result_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 벡터 임베딩 (pgvector)
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL,  -- code | jd | resume | linkedin
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_embeddings_job ON embeddings(job_id);
CREATE INDEX idx_embeddings_kind ON embeddings(kind);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

### 15.6 Makefile 표준화

```makefile
# jittda/Makefile
.PHONY: up down logs shell test lint clean infra-clean tunnel-up tunnel-down sonar-scan

# --- Cloudflare Tunnel (독립 생명주기) ---
tunnel-up:
	cd ../infra-tunnel && docker compose up -d

tunnel-down:
	cd ../infra-tunnel && docker compose down

# --- 개발 환경 관리 ---
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f backend

shell:
	docker compose exec backend bash

# --- 테스트 ---
test:
	docker compose exec backend pytest tests/ -v

test-domain:
	docker compose exec backend pytest tests/domain/ -v

test-e2e:
	docker compose exec backend pytest tests/e2e/ -v

# --- 코드 품질 ---
lint:
	docker compose exec backend ruff check .

format:
	docker compose exec backend ruff format .

# --- SonarQube 분석 (On-Demand) ---
sonar-scan:
	docker compose --profile analysis up -d sonarqube
	@echo "Waiting for SonarQube to start..."
	@sleep 30
	docker compose --profile analysis up sonar-scanner

# --- 정리 ---
clean:
	docker compose down -v

infra-clean:
	docker compose down -v --remove-orphans
	docker volume prune -f
```

### 15.7 Cloudflare Zero Trust 대시보드 설정

터널과 프론트엔드가 `jittda-public` 네트워크를 공유하므로, **Public Hostname** 설정:

| 설정 | 값 |
|------|-----|
| Service | HTTP |
| URL | `jittda_frontend:80` |

**트래픽 흐름:**
```
User → Cloudflare Edge → cloudflared (jittda-public) → jittda_frontend:80 (Nginx/React)
                                                              ↓ (internal_net)
                                                         backend:8000 (FastAPI)
                                                              ↓
                                                         postgres / redis
```

---

## 16. 프론트엔드 설계

### 16.1 새로운 시각화 컴포넌트

| 컴포넌트 | 기술 | 데이터 소스 | 용도 |
|----------|------|-----------|------|
| `FourAxisRadar.tsx` | D3.js | 4대 지표 | 논리력/전문성/안정성/진정성 레이더 |
| `ComplexityTreemap.tsx` | D3.js | W7 결과 | 파일별 복잡도 드릴다운 |
| `AuthenticityGauge.tsx` | D3.js | W3+W5 결과 | 진정성 게이지 (WPM + 표절률) |
| `AICodeHeatmap.tsx` | D3.js | W3 결과 | 파일별 Human vs AI 생성 비율 히트맵 |
| `SkillHeatmap.tsx` | D3.js | W9 결과 | 기술스택 히트맵 (JD 매칭) |
| `CommitTimeline.tsx` | D3.js | W1 결과 | Git 커밋 타임라인 |
| `AgentProgressFlow.tsx` | React | WebSocket | HMAS 에이전트 실행 흐름 실시간 |

### 16.2 탭 구조

```
ResultPage 탭:
├── Tab 1: Overview (3초 요약)
│   ├── 신호등 카드 (Green/Yellow/Red) + 종합 등급 (예: B+)
│   ├── 한 줄 평: "기본기 탄탄(Green), 최신 스택 부족(Yellow), 보안 취약(Red)"
│   ├── 신뢰도 지표: "AI 생성 의심 구간 12%"
│   └── FourAxisRadar.tsx (4대 지표)
│
├── Tab 2: Intel Brief (기존 유지 + 강화)
│   └── + 진정성 검증 섹션 추가
│
├── Tab 3: Code Deep Dive (신규)
│   ├── ComplexityTreemap.tsx (파일 클릭 → 상세 팝업)
│   ├── AICodeHeatmap.tsx (Human vs AI 비율)
│   ├── SkillHeatmap.tsx (JD 매칭)
│   └── CommitTimeline.tsx
│
├── Tab 4: Interview (기존 유지 + 강화)
│   ├── 3전략별 질문 그룹핑 (Negative/Complexity/Evolution)
│   ├── 카드형 UI (Q + 의도 + 체크리스트 + 평가 버튼)
│   └── 파생 질문 (Follow-up) 자동 표시
│
└── Tab 5: Decision (기존 유지 + 강화)
    └── + 4대 지표 기반 종합 판단 근거
```

### 16.3 CEO용 3초 요약 카드

```
┌─────────────────────────────────────────┐
│  종합 등급: B+ (상위 15%)                │
│                                         │
│  [🟢 논리력 78]  [🟡 전문성 65]          │
│  [🟢 안정성 72]  [🔴 진정성 45]          │
│                                         │
│  핵심 요약:                              │
│  "기본기는 탄탄하나, 최신 기술 스택 활용    │
│   경험이 부족하고, AI 생성 코드 의심 12%"  │
│                                         │
│  ⚠️ AI 코드 의심: 12%                   │
└─────────────────────────────────────────┘
```

### 16.4 실시간 스트리밍 (WebSocket)

```typescript
// frontend/src/hooks/useLangGraphStream.ts
export function useLangGraphStream(jobId: string) {
  const [agentStates, setAgentStates] = useState<AgentState[]>([]);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/jobs/${jobId}/stream`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      switch (data.type) {
        case 'agent_started':
          setAgentStates(prev => [...prev, { name: data.agent, status: 'running' }]);
          break;
        case 'agent_completed':
          setAgentStates(prev => prev.map(a =>
            a.name === data.agent ? { ...a, status: 'completed', result: data.result } : a
          ));
          break;
        case 'progress':
          setProgress(data.progress);
          break;
        case 'metric_update':
          // 실시간 지표 업데이트 (레이더 차트 점진적 렌더링)
          break;
      }
    };

    return () => ws.close();
  }, [jobId]);

  return { agentStates, progress };
}
```

### 16.5 프론트엔드 의존성

```json
{
  "dependencies": {
    "react": "^19.0.0",
    "d3": "^7.9.0",
    "@types/d3": "^7.4.3",
    "@tanstack/react-query": "^5.0.0"
  }
}
```

---

## 17. 테스트 전략

### 17.1 테스트 계층

| 레벨 | 대상 | 도구 | 커버리지 목표 |
|------|------|------|-------------|
| **Unit** | Domain 로직 (순수 함수) | pytest | 90% |
| **Unit** | Worker 개별 로직 | pytest + pytest-asyncio | 80% |
| **Integration** | Subgraph 내 Worker 연동 | pytest + testcontainer (PostgreSQL) | 70% |
| **E2E** | MetaGraph 전체 파이프라인 | pytest + Mock LLM | 60% |
| **Visual** | 프론트엔드 차트/UI | Playwright | 주요 페이지 |
| **Performance** | Worker 병렬 실행 시간 | pytest-benchmark | 기준선 대비 |

### 17.2 Domain 테스트 원칙

Domain 레이어는 **외부 의존성이 0**이므로, 순수 단위 테스트로 작성한다.

```python
# tests/domain/test_mailmap_builder.py
def test_noreply_email_detected():
    authors = [GitAuthor(name="Kim", email="123+kim@users.noreply.github.com")]
    profile = GitHubProfile(name="Kim Doe", email="kim@example.com")
    result = build_dynamic_mailmap(authors, profile, "12345")
    assert len(result) == 1
    assert result[0].confidence == "high"

def test_levenshtein_clustering():
    authors = [GitAuthor(name="Kim Doe", email="kimdoe@company.com")]
    profile = GitHubProfile(name="Kim D.", email="kim@personal.com")
    result = build_dynamic_mailmap(authors, profile, "12345", threshold=0.75)
    assert len(result) >= 1

def test_funnel_stage1_excludes_forks():
    repos = [RepoMetadata(is_fork=True), RepoMetadata(is_fork=False)]
    result = stage1_hard_filter(repos, ["python"], FunnelConfig())
    assert len(result) == 1
    assert result[0].is_fork is False
```

### 17.3 테스트 시나리오

```
1. Happy Path: 모든 데이터 소스 사용 가능
   - GitHub 3 repos + LinkedIn + Resume + JD
   - 예상: 모든 Worker 실행 → 4대 지표 산출 → 20개 질문 생성

2. Partial Data: GitHub만 사용 가능
   - GitHub 1 repo + JD (LinkedIn/Resume 없음)
   - 예상: Forensic + Logic + Stack 실행, 신뢰도 "낮음"

3. Quality Gate Rejection: 질문 품질 미달
   - 강제 저품질 질문 주입
   - 예상: Reviewer → Reviser → Re-review (최대 2회 루프)

4. Worker Failure: SonarQube 서비스 다운
   - SonarQube 연결 불가
   - 예상: QualityScanner Graceful Degradation, 나머지 Worker 정상

5. Concurrent: 3개 Job 동시 실행
   - LangGraph thread_id로 격리, 교차 오염 없음
```

---

## 18. Phase별 구현 로드맵 및 Linear 티켓

> **Clean Slate 원칙:** "Temporal 제거" Phase가 존재하지 않는다. 처음부터 설치하지 않기 때문이다.

### Phase 0: Scaffolding (3일, 4 티켓)

| # | 티켓 | 작업 내용 | 의존성 |
|---|------|----------|--------|
| 1 | 프로젝트 초기화 | `jittda/` 디렉토리 생성, DDD 4계층 구조, pyproject.toml | — |
| 2 | Docker Compose + Cloudflare Tunnel | PostgreSQL, Redis, SonarQube, cloudflared 서비스 | #1 |
| 3 | Fresh init.sql 작성 | 전체 DB 스키마 (Alembic 없음) | #2 |
| 4 | Makefile 표준화 | up/down/logs/shell/test/lint/clean/infra-clean 타겟 | #2 |

### Phase 1: Domain Layer (5일, 6 티켓)

| # | 티켓 | 작업 내용 | 의존성 |
|---|------|----------|--------|
| 5 | Identity Resolution 모델 | MailmapEntry, IdentityCluster, BlameLineAttribution, PureContribution | #1 |
| 6 | Mailmap Builder | 동적 .mailmap 생성 (noreply + Levenshtein + domain) | #5 |
| 7 | Blame Filter | blame 라인 필터링 (identity_cluster 기반) | #5 |
| 8 | Semantic Pruner 규칙 | AST 노이즈 제거 규칙 (import, 주석, config, generated) | #5 |
| 9 | Funnel Selection 규칙 | 3단계 퍼널 (Hard Filter + Relevance Score + Vector) | #1 |
| 10 | Scoring Calculator | 4대 지표 가중 합산 (기존 scoring_formulas.py 재작성) | #1 |

### Phase 2: Infrastructure Layer (7일, 8 티켓)

| # | 티켓 | 작업 내용 | 의존성 |
|---|------|----------|--------|
| 11 | Git 어댑터 | blame_runner (-w -M -C), clone_manager, mailmap_writer | #3 |
| 12 | GitHub GraphQL 클라이언트 | get_user_node_id, get_user_repos_graphql | #3 |
| 13 | Tree-sitter 어댑터 | AST 파싱 (Python, JS, TS, Java, Go) | #1 |
| 14 | Radon/Lizard 어댑터 | CC, Halstead, MI 산출 | #1 |
| 15 | SonarQube 어댑터 | REST API 연동 (기술부채, 코드스멜, 보안) | #2 |
| 16 | Datasketch 어댑터 | MinHash/LSH 표절 탐지 | #1 |
| 17 | Instructor 클라이언트 | Instructor + Pydantic + Langfuse 통합 | #1 |
| 18 | pgvector 확장 | JD-Repo 벡터 유사도 + 코드 청크 임베딩 | #3 |

### Phase 3: Application Layer - Graphs (7일, 6 티켓)

| # | 티켓 | 작업 내용 | 의존성 |
|---|------|----------|--------|
| 19 | State 정의 | MetaState, ForensicState, LogicState, StackState | #1 |
| 20 | ForensicSupervisor Graph | Collector → IdentityResolver → Pruner → [Vibector∥CLAVE∥Datasketch] | #6,7,8,11,12 |
| 21 | LogicSupervisor Graph | [ASTAnalyzer∥ComplexityMeter∥QualityScanner] 병렬 | #13,14,15 |
| 22 | StackSupervisor Graph | [SkillExtractor∥APIDepth∥Architecture] 병렬 | #13,17 |
| 23 | MetaAgent Graph 조립 | 전체 연결 + Fan-out/Fan-in + QualityGate 루프 | #19,20,21,22 |
| 24 | FastAPI + WebSocket 통합 | Interface Layer 라우트 + 실시간 스트리밍 | #23 |

### Phase 4: 질문 생성 + Enhancement (5일, 5 티켓)

| # | 티켓 | 작업 내용 | 의존성 |
|---|------|----------|--------|
| 25 | TopicSelector | 벡터 검색 기반 토픽 선별 | #18,23 |
| 26 | 3전략 QuestionCrafter | Negative/Complexity/Evolution 프롬프트 | #17,25 |
| 27 | Enhancement Agents (5개) | 용어설명, 비개발자 답변가이드, 파생질문 등 | #26 |
| 28 | QualityGate 루프 | Reviewer + Reviser (최대 2회 루프) | #27 |
| 29 | Langfuse 프롬프트 업로드 | 모든 프롬프트 Langfuse production 등록 | #26,27 |

### Phase 5: 출력 + 프론트엔드 (10일, 9 티켓)

| # | 티켓 | 작업 내용 | 의존성 |
|---|------|----------|--------|
| 30 | OutputAssembler | IntelBrief + DeepAnalysis + DecisionSupport 생성 | #28 |
| 31 | 4대 지표 산출 + DB 저장 | candidate_scores 테이블 연동 | #10,23 |
| 32 | FourAxisRadar.tsx | 4대 지표 레이더 차트 (D3.js) | #31 |
| 33 | ComplexityTreemap.tsx | 파일별 복잡도 드릴다운 (D3.js) | #31 |
| 34 | AICodeHeatmap.tsx | Human vs AI 생성 비율 히트맵 (D3.js) | #31 |
| 35 | AgentProgressFlow.tsx | HMAS 에이전트 실행 흐름 실시간 (WebSocket) | #24 |
| 36 | Overview Tab | 3초 요약 카드 + 신호등 UI | #32 |
| 37 | Code Deep Dive Tab | Treemap + Heatmap + Timeline 통합 | #33,34 |
| 38 | Interview Tab 강화 | 3전략 그룹핑 + 카드형 UI + 평가 버튼 | #30 |

### Phase 6: 통합 테스트 + 정리 (5일, 4 티켓)

| # | 티켓 | 작업 내용 | 의존성 |
|---|------|----------|--------|
| 39 | Domain 단위 테스트 | Identity, Scoring, Funnel 테스트 (커버리지 90%) | #5-10 |
| 40 | E2E 통합 테스트 | Happy Path + Partial Data + Worker Failure + Concurrent | #23 |
| 41 | Playwright E2E | Overview + Code Deep Dive 탭 렌더링 검증 | #36,37 |
| 42 | 성능 벤치마크 + 문서화 | 기존 Temporal 대비 실행 시간 비교, 아키텍처 다이어그램 | #40 |

### 일정 요약

| Phase | 기간 | 티켓 수 | 핵심 산출물 |
|-------|------|---------|-----------|
| Phase 0: Scaffolding | 3일 | 4개 | 프로젝트 구조, Docker, DB |
| Phase 1: Domain | 5일 | 6개 | 순수 비즈니스 로직 |
| Phase 2: Infrastructure | 7일 | 8개 | 외부 서비스 어댑터 |
| Phase 3: Application | 7일 | 6개 | LangGraph 그래프 |
| Phase 4: Questions | 5일 | 5개 | 질문 생성 엔진 |
| Phase 5: Output + FE | 10일 | 9개 | 출력 + UI |
| Phase 6: Test + Polish | 5일 | 4개 | 테스트 + 벤치마크 |
| **총합** | **42일** | **42개** | |

---

## 부록 A: 리스크 및 완화 전략

| 리스크 | 영향 | 완화 |
|--------|------|------|
| SonarQube Docker 메모리 (2GB+) | 로컬 개발 환경 부담 | 최소 설정 + 분석 시에만 실행 (profile) |
| Tree-sitter 언어 미지원 | 일부 마이너 언어 | GenericAnalysis fallback |
| LangGraph Checkpointer 성능 | 동시 Job 처리 시 DB 병목 | 커넥션 풀 최적화 + Redis 보조 |
| Instructor 모델 호환성 | Kimi K2.5 structured output 미지원 시 | JSON mode fallback + 수동 파싱 |
| Datasketch FOSS Corpus 크기 | 초기 구축 시간 | 단계적 확장 (주요 프레임워크부터) |
| Cloudflare Tunnel 토큰 관리 | 보안 | `.env` 분리 + CI/CD secrets |

## 부록 B: 디자인 패턴 적용 총괄

| 패턴 | 적용 위치 | 목적 |
|------|----------|------|
| **Strategy** | Worker 내 언어별 분석 도구 선택 | 하드코딩 없이 언어별 분석 로직 분리 |
| **Factory** | AnalysisStrategyFactory | Worker/Strategy 객체 생성 추상화 |
| **Template Method** | BaseWorker.run() | Worker 공통 실행 흐름 통일 |
| **Observer** | EventBus (에이전트 간 진행률 알림) | 느슨한 결합 유지 |
| **Chain of Responsibility** | QualityGate (Review → Revise → Re-review) | 품질 검증 체인 |
| **Composite** | HMAS 3계층 (MetaGraph → SubGraph → Node) | 계층 구조 일관된 인터페이스 |
| **Adapter** | SonarQube, Langfuse, GitHub API 래퍼 | 외부 서비스 통합 추상화 |
| **Builder** | ContextBudget, PromptBuilder | 복잡한 객체 단계적 조립 |

## 부록 C: 기술 선택 근거

| 기술 | 선택 이유 | 대안 | 대안 미선택 이유 |
|------|----------|------|----------------|
| LangGraph | StateGraph HMAS 표현, Checkpointer durability | CrewAI, AutoGen | 추상화 과다, 커스터마이징 제한 |
| Instructor | Pydantic 네이티브, 자동 재시도, 다중 모델 지원 | LangChain structured_output | Pydantic v2 미완전 지원 |
| Tree-sitter | 50+ 언어, 증분 파싱, 메모리 효율 | Python `ast`, Babel | 단일 언어만, 느린 속도 |
| Radon/Lizard | 정확한 CC/Halstead, 경량 | SonarQube 내장 | 세부 지표 API 제한 |
| SonarQube Community | 무료, 종합적 품질 분석, REST API | CodeClimate, Codacy | 유료, 제한적 API |
| Datasketch | MinHash/LSH 표절 탐지, Python 네이티브 | Moss, JPlag | 학술용, API 의존 |
| D3.js | 최대 유연성, 커스텀 시각화 | Recharts, Chart.js | 커스터마이징 한계 |
| Cloudflare Tunnel | Zero Trust, 무료, 보안 | ngrok | 유료, 보안 제한 |
| Fresh init.sql | Clean Slate 원칙, 최적 스키마 | Alembic migration | 레거시 히스토리 오염 |
