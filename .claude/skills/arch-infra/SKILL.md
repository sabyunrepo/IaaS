---
name: arch-infra
description: 인프라 및 Docker 설정. Docker Compose, 환경 변수, Settings, 배포, LocalStack, Temporal 서버 관련 구현 시 사용.
argument-hint: [target] (예: docker, settings, env, deploy)
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Infrastructure Architecture Skill

Docker Compose 기반 Local-First 인프라 구현 가이드.

## 반드시 먼저 읽을 문서
1. `docs/architecture/04-infrastructure.md` — 인프라 전체 설계
2. `docs/architecture/ARCHITECTURE.md` — 프로젝트 구조

## 서비스 구성

| 서비스 | 이미지 | 포트 | 용도 |
|--------|--------|------|------|
| frontend | Vite dev server | 5173 | React SPA |
| backend | FastAPI | 8000 | REST API |
| worker | Python | — | Temporal Worker |
| temporal | temporalio/auto-setup | 7233 | Workflow 엔진 |
| temporal-ui | temporalio/ui | 8080 | Temporal 관리 UI |
| postgres | postgres:16 | 5432 | DB + pgvector |
| redis | redis:7 | 6379 | 캐시 + Rate Limit |
| localstack | localstack/localstack | 4566 | S3 에뮬레이션 |

## Settings 클래스 (pydantic-settings)
```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    # Redis
    REDIS_URL: str
    # Temporal
    TEMPORAL_ADDRESS: str = "temporal:7233"
    TEMPORAL_NAMESPACE: str = "default"
    # Auth
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    OAUTH_TOKEN_ENCRYPTION_KEY: str
    SESSION_SECRET: str
    FRONTEND_URL: str = "http://localhost:5173"
    # LLM
    OPENAI_API_KEY: str
    # Storage
    S3_ENDPOINT: str | None = None  # LocalStack용
    S3_BUCKET: str = "vantict-files"

    model_config = SettingsConfigDict(env_file=".env.local")
```

## 파일 배치
```
docker-compose.yml          — 로컬 개발 환경
docker-compose.prod.yml     — 프로덕션 오버라이드
.env.local                  — 로컬 환경 변수
.env.production             — 프로덕션 환경 변수
backend/Dockerfile          — Backend + Worker 이미지
frontend/Dockerfile         — Frontend 이미지
backend/app/core/config.py  — Settings 클래스
backend/app/core/database.py — DB 세션 관리
backend/app/core/temporal.py — Temporal 클라이언트
scripts/setup.sh            — 초기 설정
```

## Local → Cloud 전환
| 로컬 | 클라우드 | 방법 |
|-----|---------|------|
| PostgreSQL | RDS Aurora | DATABASE_URL 변경 |
| Redis | ElastiCache | REDIS_URL 변경 |
| LocalStack | AWS S3 | S3_ENDPOINT 제거 |
| Temporal local | Temporal Cloud | TEMPORAL_ADDRESS 변경 |
| Docker Compose | ECS Fargate | `copilot deploy` |

## 규칙
- 환경 변수로만 설정 전환 (코드 수정 금지)
- Secret은 `.env` 파일 또는 AWS Secrets Manager
- pgvector 확장: `CREATE EXTENSION IF NOT EXISTS vector;`
- 헬스체크: 모든 서비스에 healthcheck 설정
