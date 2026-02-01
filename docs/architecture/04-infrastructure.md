# 04. 인프라 및 배포

> Local-First, Cloud-Ready 인프라 설계

---

## 개요

로컬 개발 환경에서 시작하여 AWS 클라우드로 쉽게 전환할 수 있는 인프라 구조입니다.

### 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **동일 코드** | 로컬/클라우드에서 같은 애플리케이션 코드 실행 |
| **환경 추상화** | 환경변수로 로컬/클라우드 전환 |
| **컨테이너 우선** | 모든 서비스는 Docker 컨테이너로 실행 |
| **Infrastructure as Code** | 모든 인프라 설정은 코드로 관리 |

---

## 로컬 개발 환경

### Docker Compose 구조

```yaml
# docker-compose.yml

services:
  # ============================================
  # 핵심 서비스
  # ============================================

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - ENV=local
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/vantict
      - REDIS_URL=redis://redis:6379
      - TEMPORAL_HOST=temporal:7233
      - S3_ENDPOINT=http://localstack:4566
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - PROXYCURL_API_KEY=${PROXYCURL_API_KEY}
      - LANGFUSE_HOST=http://langfuse:3000
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
    volumes:
      - ./backend:/app
      - /app/.venv  # venv는 마운트 제외
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      temporal:
        condition: service_started
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - ENV=local
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/vantict
      - REDIS_URL=redis://redis:6379
      - TEMPORAL_HOST=temporal:7233
      - S3_ENDPOINT=http://localstack:4566
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - PROXYCURL_API_KEY=${PROXYCURL_API_KEY}
      - LANGFUSE_HOST=http://langfuse:3000
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      - backend
      - temporal
      - langfuse
    command: python -m app.workers.main

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev

  # ============================================
  # 데이터베이스
  # ============================================

  postgres:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: vantict
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru

  # ============================================
  # Temporal (워크플로우 엔진)
  # ============================================

  temporal:
    image: temporalio/auto-setup:1.22
    ports:
      - "7233:7233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=postgres
      - POSTGRES_PWD=postgres
      - POSTGRES_SEEDS=postgres
      - DYNAMIC_CONFIG_FILE_PATH=/etc/temporal/config/dynamicconfig/development.yaml
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./config/temporal:/etc/temporal/config/dynamicconfig

  temporal-ui:
    image: temporalio/ui:2.21.3
    ports:
      - "8080:8080"
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
      - TEMPORAL_CORS_ORIGINS=http://localhost:3000
    depends_on:
      - temporal

  # ============================================
  # LLM 관측 (Langfuse)
  # ============================================

  langfuse:
    image: langfuse/langfuse:2
    ports:
      - "3100:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/langfuse
      - NEXTAUTH_URL=http://localhost:3100
      - NEXTAUTH_SECRET=langfuse-dev-secret
      - SALT=langfuse-dev-salt
    depends_on:
      postgres:
        condition: service_healthy

  # ============================================
  # AWS 로컬 에뮬레이션
  # ============================================

  localstack:
    image: localstack/localstack:3.0
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3
      - DEBUG=1
      - DATA_DIR=/var/lib/localstack/data
    volumes:
      - localstack_data:/var/lib/localstack
      - ./scripts/localstack-init.sh:/etc/localstack/init/ready.d/init.sh

volumes:
  postgres_data:
  redis_data:
  localstack_data:
```

### 초기화 스크립트

```sql
-- scripts/init-db.sql
-- PostgreSQL 초기화

-- pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- Langfuse DB (self-host)
CREATE DATABASE langfuse;

-- 작업 테이블 (02-data-models.md Section 8 참조)
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_data JSONB NOT NULL,
    analysis_result JSONB,
    final_output JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_session ON jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_jobs_tenant ON jobs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);

-- 코드 분석 벡터 테이블
CREATE TABLE IF NOT EXISTS code_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    code_snippet TEXT NOT NULL,
    snippet_type VARCHAR(50),
    embedding vector(1536),  -- settings.EMBEDDING_DIMENSION
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_code_job ON code_embeddings(job_id);

-- 벡터 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_code_embedding_vector
ON code_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 학습 데이터 수집용 (Phase 2: Langfuse Datasets로 마이그레이션 예정)
CREATE TABLE IF NOT EXISTS training_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id),
    agent_type VARCHAR(100) NOT NULL,
    system_prompt TEXT NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    quality VARCHAR(50) DEFAULT 'unlabeled',
    quality_score FLOAT,
    human_feedback TEXT,
    model_used VARCHAR(100),
    prompt_tokens INT,
    completion_tokens INT,
    latency_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

```bash
#!/bin/bash
# scripts/localstack-init.sh
# LocalStack 초기화 (S3 버킷 생성)

awslocal s3 mb s3://vantict-data
# 단일 버킷, 디렉터리로 구분:
#   uploads/{job_id}/       — 업로드 파일
#   analysis/{job_id}/      — 분석 결과
#   outputs/{job_id}/       — 최종 스크립트
#   training/               — 학습 데이터

echo "LocalStack initialized: S3 bucket created"
```

---

## 환경 설정

### 환경변수 구조

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 환경
    ENV: str = "local"  # local, staging, production

    # 데이터베이스
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Temporal
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "interview-generation"
    # Temporal Cloud (프로덕션)
    TEMPORAL_CLOUD_NAMESPACE: str | None = None
    TEMPORAL_TLS_CERT: str | None = None   # mTLS 인증서 내용
    TEMPORAL_TLS_KEY: str | None = None    # mTLS 키 내용
    TEMPORAL_API_KEY: str | None = None    # API Key 인증 (대안)

    # Object Storage (S3-compatible)
    # 로컬(기본) → Cloudflare R2(프로덕션 우선) → AWS S3 순으로 전환
    STORAGE_BACKEND: str = "local"          # local | r2 | s3
    S3_ENDPOINT: str | None = None         # R2/MinIO/LocalStack용 커스텀 엔드포인트
    S3_BUCKET: str = "vantict-data"        # 단일 버킷, 디렉터리로 구분
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "ap-northeast-2"
    LOCAL_STORAGE_PATH: str = "./data"     # STORAGE_BACKEND=local 시 사용

    # GitHub (PyGithub)
    GITHUB_TOKEN: str | None = None        # GitHub API 인증 토큰

    # LLM (Pydantic AI + LiteLLM)
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    LLM_MODEL: str = "openai/gpt-4o"  # LiteLLM 모델 ID (provider/model)
    LLM_FALLBACK_MODEL: str = "anthropic/claude-sonnet-4-20250514"

    # LLM 관측 (Langfuse self-host)
    LANGFUSE_HOST: str = "http://localhost:3100"
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None

    # LinkedIn (Proxycurl)
    PROXYCURL_API_KEY: str | None = None   # LinkedIn 프로필 수집용

    # Embedding
    EMBEDDING_DIMENSION: int = 1536        # 벡터 차원 (ada-002/text-embedding-3-small: 1536)

    # 기타
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @property
    def is_local(self) -> bool:
        return self.ENV == "local"

    @property
    def storage_config(self) -> dict:
        """Object Storage 클라이언트 설정
        local(기본) → Cloudflare R2(프로덕션 권장) → AWS S3
        R2/S3/MinIO/LocalStack 모두 S3-compatible API 사용
        """
        if self.STORAGE_BACKEND == "local":
            return {"backend": "local", "path": self.LOCAL_STORAGE_PATH}

        # r2 | s3 | minio 등 — 모두 S3-compatible
        config = {
            "backend": self.STORAGE_BACKEND,
            "region_name": self.AWS_REGION,
            "bucket": self.S3_BUCKET,
        }
        if self.S3_ENDPOINT:  # R2, MinIO, LocalStack
            config["endpoint_url"] = self.S3_ENDPOINT
            config["aws_access_key_id"] = self.AWS_ACCESS_KEY_ID or "test"
            config["aws_secret_access_key"] = self.AWS_SECRET_ACCESS_KEY or "test"
        return config

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### 환경별 설정 파일

```env
# .env.local
ENV=local
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vantict
REDIS_URL=redis://localhost:6379
TEMPORAL_HOST=localhost:7233
STORAGE_BACKEND=local
# LocalStack 사용 시: STORAGE_BACKEND=s3, S3_ENDPOINT=http://localhost:4566
OPENAI_API_KEY=sk-xxx
LLM_MODEL=openai/gpt-4o
LANGFUSE_HOST=http://localhost:3100
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
```

```env
# .env.production (Cloudflare R2 — 권장)
ENV=production
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/vantict
REDIS_URL=redis://elasticache-endpoint:6379
TEMPORAL_HOST=temporal.internal:7233
STORAGE_BACKEND=r2
S3_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
AWS_ACCESS_KEY_ID=<r2-access-key>
AWS_SECRET_ACCESS_KEY=<r2-secret-key>
AWS_REGION=auto
OPENAI_API_KEY=sk-xxx
LLM_MODEL=openai/gpt-4o
LLM_FALLBACK_MODEL=anthropic/claude-sonnet-4-20250514
LANGFUSE_HOST=https://langfuse.internal:3000
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
```

---

## 클라우드 전환 (AWS)

### 아키텍처 매핑

| 로컬 (Docker Compose) | AWS |
|----------------------|-----|
| PostgreSQL (pgvector) | RDS PostgreSQL + pgvector |
| Redis | ElastiCache Redis |
| Temporal | Temporal Cloud 또는 ECS 자체 호스팅 |
| LocalStack S3 | Amazon S3 |
| Docker containers | ECS Fargate |
| docker-compose.yml | AWS Copilot / CDK |

### AWS Copilot 설정

```yaml
# copilot/backend/manifest.yml
name: backend
type: Load Balanced Web Service

image:
  build: backend/Dockerfile
  port: 8000

http:
  path: "/"
  healthcheck:
    path: "/health"
    interval: 10s
    timeout: 5s

cpu: 512
memory: 1024
count:
  range: 1-4
  cpu_percentage: 70

variables:
  ENV: production
  TEMPORAL_NAMESPACE: production

secrets:
  DATABASE_URL: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/DATABASE_URL
  REDIS_URL: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/REDIS_URL
  OPENAI_API_KEY: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/OPENAI_API_KEY
  GITHUB_TOKEN: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/GITHUB_TOKEN
  PROXYCURL_API_KEY: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/PROXYCURL_API_KEY
  LANGFUSE_PUBLIC_KEY: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/LANGFUSE_PUBLIC_KEY
  LANGFUSE_SECRET_KEY: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/LANGFUSE_SECRET_KEY
```

```yaml
# copilot/worker/manifest.yml
name: worker
type: Backend Service

image:
  build: backend/Dockerfile
  command: ["python", "-m", "app.workers.main"]

cpu: 1024
memory: 4096  # ⚠️ Docling(PyTorch CPU) + PyDriller + AST + LLM 동시 실행 — 프로파일링 후 조정
count:
  range: 1-8
  cpu_percentage: 70

variables:
  ENV: production
  TEMPORAL_TASK_QUEUE: interview-generation

secrets:
  DATABASE_URL: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/DATABASE_URL
  REDIS_URL: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/REDIS_URL
  OPENAI_API_KEY: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/OPENAI_API_KEY
  GITHUB_TOKEN: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/GITHUB_TOKEN
  PROXYCURL_API_KEY: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/PROXYCURL_API_KEY
  LANGFUSE_PUBLIC_KEY: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/LANGFUSE_PUBLIC_KEY
  LANGFUSE_SECRET_KEY: /copilot/${COPILOT_APPLICATION_NAME}/${COPILOT_ENVIRONMENT_NAME}/secrets/LANGFUSE_SECRET_KEY
```

---

## Temporal 설정

### 로컬 Temporal 설정

```yaml
# config/temporal/development.yaml
system.forceSearchAttributesCacheRefreshOnRead:
  - value: true
    constraints: {}

limit.maxIDLength:
  - value: 255
    constraints: {}

frontend.enableClientVersionCheck:
  - value: true
    constraints: {}
```

### Temporal Cloud 전환

```python
# backend/app/core/temporal.py
from temporalio.client import Client
from temporalio.service import TLSConfig
import ssl

async def get_temporal_client(settings: Settings) -> Client:
    """환경에 맞는 Temporal 클라이언트 생성"""

    if settings.ENV == "production" and settings.TEMPORAL_CLOUD_NAMESPACE:
        # Temporal Cloud
        tls_config = TLSConfig(
            client_cert=settings.TEMPORAL_TLS_CERT.encode(),
            client_private_key=settings.TEMPORAL_TLS_KEY.encode(),
        )
        return await Client.connect(
            f"{settings.TEMPORAL_CLOUD_NAMESPACE}.tmprl.cloud:7233",
            namespace=settings.TEMPORAL_CLOUD_NAMESPACE,
            tls=tls_config,
        )
    else:
        # 로컬 또는 자체 호스팅
        return await Client.connect(
            settings.TEMPORAL_HOST,
            namespace=settings.TEMPORAL_NAMESPACE,
        )
```

---

## Dockerfile

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim as base

WORKDIR /app

# 시스템 의존성 (Docling: tesseract, poppler / PyDriller: git)
RUN apt-get update && apt-get install -y \
    git \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
# ⚠️ Docling은 PyTorch CPU를 포함하여 이미지 ~5-6GB
# 프로덕션에서는 multi-stage build로 최적화 권장
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드
COPY . .

# 개발용 타겟
FROM base as development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 프로덕션 타겟
FROM base as production
RUN pip install gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine as base
WORKDIR /app

# 의존성
COPY package*.json ./
RUN npm ci

# 소스 코드
COPY . .

# 개발용
FROM base as development
CMD ["npm", "run", "dev"]

# 빌드
FROM base as builder
RUN npm run build

# 프로덕션
FROM node:20-alpine as production
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
CMD ["node", "server.js"]
```

---

## 개발 명령어

### Makefile

```makefile
# Makefile

.PHONY: up down logs test migrate

# 로컬 환경 시작
up:
	docker-compose up -d
	@echo "Services starting..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Temporal UI: http://localhost:8080"
	@echo "Langfuse: http://localhost:3100"

# 로컬 환경 중지
down:
	docker-compose down

# 로그 확인
logs:
	docker-compose logs -f $(service)

# 테스트 실행
test:
	docker-compose exec backend pytest -v

# DB 마이그레이션
migrate:
	docker-compose exec backend alembic upgrade head

# 개발 쉘
shell:
	docker-compose exec backend bash

# 전체 재빌드
rebuild:
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d

# AWS 배포 (Copilot)
deploy-staging:
	copilot deploy --env staging

deploy-prod:
	copilot deploy --env production
```

---

## 모니터링

### 로컬 모니터링

```yaml
# docker-compose.monitoring.yml (선택적)

services:
  prometheus:
    image: prom/prometheus:v2.45.0
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:10.0.0
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

### 헬스체크 엔드포인트

```python
# backend/app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """헬스체크 엔드포인트"""
    checks = {
        "status": "healthy",
        "checks": {}
    }

    # DB 체크
    try:
        await db.execute("SELECT 1")
        checks["checks"]["database"] = "ok"
    except Exception:
        checks["checks"]["database"] = "unavailable"
        checks["status"] = "unhealthy"

    # Redis 체크
    try:
        redis = get_redis()
        await redis.ping()
        checks["checks"]["redis"] = "ok"
    except Exception:
        checks["checks"]["redis"] = "unavailable"
        checks["status"] = "unhealthy"

    return checks
```

---

## 다음 문서

- [05. API 명세](./05-api-spec.md)
