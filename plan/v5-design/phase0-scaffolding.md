# Phase 0: Scaffolding

> 원본 설계서: `plan/2026-02-15-v5-final-design.md`
> Linear 티켓: JIT-82 ~ JIT-85

## Linear 티켓 매핑

| 티켓 | 제목 | 참조 섹션 |
|------|------|----------|
| JIT-82 | 프로젝트 초기화 (`jittda/` 디렉토리 생성, DDD 4계층 구조, pyproject.toml) | §3, §4, §5.4 |
| JIT-83 | Docker Compose + Cloudflare Tunnel | §15.0, §15.1, §15.2 |
| JIT-84 | Fresh init.sql 작성 | §15.5 |
| JIT-85 | Makefile 표준화 | §15.6 |

---

## §3. Clean Slate 접근 전략

### 3.1 원칙: "마이그레이션이 아닌 재건축"

```
XXXX 기존 접근 (Migration)
backend/ 위에서 Temporal 제거 -> LangGraph 교체 -> 코드 정리

OK 올바른 접근 (Reconstruction)
jittda/ 신규 생성 -> 처음부터 DDD 구조 -> 필요한 로직만 발췌 재작성
```

- `jittda/`는 **완전히 새로운 디렉토리**에서 시작
- Temporal 코드가 **애초에 존재하지 않음** (제거할 것이 없음)
- DB는 **Fresh `init.sql`** 하나로 초기화 (Alembic revision 히스토리 금지)
- 기존 Vantict 코드는 **참조용 라이브러리(Read-only)**로만 취급

### 3.2 레거시 자산 선별 가이드

**"파일 복사-붙여넣기 금지, 로직 이식 허용"**이 원칙이다.

#### [Asset] 핵심 로직 -- Port Logic, Rewrite Code

비즈니스 로직은 가져오되, DDD/Pydantic 스타일에 맞춰 새로 작성한다.

| 원본 | 조치 | 대상 위치 |
|------|------|----------|
| `scoring_formulas.py` (899줄) | 로직 100% 유지, 클래스 구조로 재작성 | `domain/scoring/calculator.py` |
| `prompts/*.yaml` | LangChain/Instructor 포맷 호환성 검증 후 이전 | `infrastructure/llm/prompts/` |
| JD 분석/매칭 로직 | 키워드 매칭 -> 벡터 검색 결합 재작성 | `domain/matching/funnel.py` |
| Redis 캐싱 아이디어 | 아이디어만 참조, 데코레이터 패턴으로 재작성 | `infrastructure/llm/client.py` |

#### [Reference] 참조 대상 -- Read Only

아이디어만 가져오고 코드는 완전히 새로 작성한다.

| 원본 | 참조 이유 | 재구현 |
|------|----------|--------|
| `services/git.py` | 단순 clone 로직 폐기 | Identity Resolution 파이프라인으로 재구현 |
| `utils/llm_cache.py` | Redis 캐싱 패턴 참조 | `infrastructure/llm/cached_client.py`에 데코레이터 패턴 |
| `github_service.py` | API 호출 패턴 참조 | GraphQL 중심 재설계 |

#### [Liability] 폐기 대상 -- Do Not Copy

새 프로젝트에 **절대 포함시키지 않는다**.

| 대상 | 이유 |
|------|------|
| `workflows/`, `activities/`, `worker.py` | Temporal 관련 -- 존재 자체가 불필요 |
| `alembic/versions/*.py` | 레거시 DB 히스토리 -- Fresh init.sql 사용 |
| SVG 차트 컴포넌트 | D3.js로 전면 교체 |
| 정규식 기반 파서 | Instructor(Structured Output)로 대체 |
| `core/temporal.py`, `core/temporal_interceptors.py` | Temporal 인프라 |
| `activity_logger.py` | Temporal 전용 로깅 |

---

## §4. DDD 아키텍처 및 디렉토리 구조

### 4.1 4계층 아키텍처

review2.md 지적에 따라 **Interface Layer**를 Application과 분리하고, **의존성 규칙**을 엄격히 적용한다.

```
의존성 방향 (단방향만 허용):

  Interface -> Application -> Domain <- Infrastructure
                              ^
                              | (Domain은 외부를 모른다)
                              |
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
    │   │   │   ├── nodes/         # LangGraph 노드 (thin wrapper, Load->Process->Save->Ref)
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
    │   ├── Dockerfile             # Multi-stage (development -> builder -> production/Nginx)
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

## §5. 기술 스택 선정 (pyproject.toml)

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
| **LLM** | Kimi K2.5 (Langfuse-first) | -- | 비용 효율, 한국어 지원 |
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

### 5.4 Python 의존성 (pyproject.toml) -- 2026-02 최신화

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

## §15. 인프라 구성 (Docker + Cloudflare Tunnel)

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
# -> jittda-public 네트워크 생성 + 터널 대기
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
    profiles: ["analysis"]    # 기본 up 시 실행되지 않음 -- On-Demand
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

-- 분석 결과 (Worker별 -- Reference Passing의 저장소)
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
User -> Cloudflare Edge -> cloudflared (jittda-public) -> jittda_frontend:80 (Nginx/React)
                                                              | (internal_net)
                                                         backend:8000 (FastAPI)
                                                              |
                                                         postgres / redis
```
