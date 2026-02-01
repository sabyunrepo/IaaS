# Common Tools Skill

> 모든 에이전트(Activity)가 공유하는 공통 서비스, 유틸리티, 설정 라이브러리

---

## 역할

각 Activity(Planner, Document Manager, Code Manager 등)가 **중복 구현 없이** 공통 기능을 사용할 수 있도록 인프라 레벨 서비스를 제공한다.

## 해결하는 문제

| 문제 | 해결 |
|------|------|
| 각 Activity마다 Redis/DB/S3 연결 코드 중복 | 공통 의존성 주입 (`deps.py`) |
| LLM 호출 방식 파편화 | 단일 진입점 `CachedLLMService` |
| 환경 설정 직접 접근 | `pydantic-settings` 기반 `Settings` |
| 에러 분류 기준 불명확 | 공통 에러 계층 (`RetryableError`, `NonRetryableError`) |
| 로깅/모니터링 비일관 | 구조화된 로깅 유틸리티 |

---

## 아키텍처 위치

```
backend/app/
├── core/                  ← Common Tools 영역
│   ├── config.py          # 환경 설정
│   ├── deps.py            # 의존성 주입 (Redis, DB, S3, Temporal)
│   ├── database.py        # PostgreSQL + pgvector 연결
│   ├── temporal.py        # Temporal 클라이언트 팩토리
│   ├── errors.py          # 공통 에러 계층
│   └── logging.py         # 구조화된 로깅
├── services/              ← 공통 서비스 영역
│   ├── llm_service.py     # CachedLLMService
│   ├── llm_cache.py       # LLM 결과 캐시
│   ├── checkpoint_store.py# 체크포인트 저장소
│   ├── storage.py         # S3 추상화
│   └── vector_store.py    # pgvector 검색
```

---

## 구현 상세

### 1. 환경 설정 (`core/config.py`)

```python
"""
backend/app/core/config.py
pydantic-settings 기반 환경 설정

모든 설정은 이 파일을 통해서만 접근한다.
os.environ 직접 접근 금지.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 환경
    ENV: str = "local"  # local | staging | production

    # 데이터베이스
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/vantict"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Temporal
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "interview-generation"
    TEMPORAL_API_KEY: str | None = None
    TEMPORAL_CLOUD_NAMESPACE: str | None = None
    TEMPORAL_TLS_CERT: str | None = None
    TEMPORAL_TLS_KEY: str | None = None

    # S3
    S3_ENDPOINT: str | None = None  # LocalStack용
    S3_BUCKET_UPLOADS: str = "vantict-uploads"
    S3_BUCKET_RESULTS: str = "vantict-results"
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "ap-northeast-2"

    # LLM
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    LLM_PROVIDER: str = "openai"  # openai | anthropic
    LLM_MODEL: str = "gpt-4o"

    # 기타
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @property
    def is_local(self) -> bool:
        return self.ENV == "local"

    @property
    def s3_config(self) -> dict:
        config = {"region_name": self.AWS_REGION}
        if self.S3_ENDPOINT:
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

### 2. 의존성 주입 (`core/deps.py`)

```python
"""
backend/app/core/deps.py
모든 Activity와 API 라우터가 사용하는 의존성 주입

사용법 (FastAPI):
    @router.get("/health")
    async def health(db: AsyncSession = Depends(get_db)):
        ...

사용법 (Activity):
    from app.core.deps import get_redis, get_storage, get_llm_service
    redis = get_redis()
"""
from contextlib import asynccontextmanager
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from temporalio.client import Client

from app.core.config import get_settings

# ─── Redis ──────────────────────────────────────────
_redis_client: Redis | None = None

def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


# ─── Database (PostgreSQL + pgvector) ───────────────
_engine = None
_session_factory = None

def _get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=10,
            max_overflow=20,
        )
    return _engine

def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory

async def get_db() -> AsyncSession:
    """FastAPI Depends용 DB 세션"""
    factory = _get_session_factory()
    async with factory() as session:
        yield session

def get_db_session() -> AsyncSession:
    """Activity용 DB 세션 (동기 호출)"""
    factory = _get_session_factory()
    return factory()


# ─── S3 Storage ─────────────────────────────────────
_storage_client = None

def get_storage():
    global _storage_client
    if _storage_client is None:
        from app.services.storage import StorageClient
        settings = get_settings()
        _storage_client = StorageClient(settings.s3_config)
    return _storage_client


# ─── Temporal Client ────────────────────────────────
async def get_temporal_client() -> Client:
    """환경에 따라 로컬/클라우드 Temporal 연결"""
    settings = get_settings()

    if settings.TEMPORAL_API_KEY:
        # Temporal Cloud
        from temporalio.service import TLSConfig
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
        return await Client.connect(
            settings.TEMPORAL_HOST,
            namespace=settings.TEMPORAL_NAMESPACE,
        )


# ─── LLM Service ───────────────────────────────────
_llm_service = None

def get_llm_service():
    """CachedLLMService 싱글턴"""
    global _llm_service
    if _llm_service is None:
        from app.services.llm_service import CachedLLMService
        settings = get_settings()
        redis = get_redis()

        if settings.LLM_PROVIDER == "openai":
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        _llm_service = CachedLLMService(client, redis)
    return _llm_service


# ─── Vector Store ───────────────────────────────────
def get_vector_store(job_id: str):
    """Job별 벡터 스토어"""
    from app.services.vector_store import VectorStore
    engine = _get_engine()
    return VectorStore(engine, job_id)
```

### 3. 공통 에러 계층 (`core/errors.py`)

```python
"""
backend/app/core/errors.py
에러 분류 체계

Temporal RetryPolicy가 이 분류를 기반으로 재시도 여부를 결정한다.
"""


class RetryableError(Exception):
    """재시도 가능한 에러 — Temporal이 자동 재시도"""
    pass

class NonRetryableError(Exception):
    """재시도 불가능한 에러 — 즉시 실패 처리"""
    pass


# ─── 구체적 에러 클래스 ────────────────────────────

# 재시도 가능
class LLMRateLimitError(RetryableError):
    """LLM API 호출 한도 초과"""
    pass

class LLMTimeoutError(RetryableError):
    """LLM API 응답 시간 초과"""
    pass

class GitHubRateLimitError(RetryableError):
    """GitHub API 호출 한도 초과"""
    pass

class TemporaryServiceError(RetryableError):
    """외부 서비스 일시적 장애"""
    pass


# 재시도 불가능
class InputValidationError(NonRetryableError):
    """입력 데이터 검증 실패"""
    pass

class AuthenticationError(NonRetryableError):
    """인증 실패 (API 키 무효)"""
    pass

class UnsupportedFileError(NonRetryableError):
    """지원하지 않는 파일 형식"""
    pass

class GitHubAccessDeniedError(NonRetryableError):
    """비공개 레포지토리 접근 불가"""
    pass


# ─── 에러 분류 유틸리티 ────────────────────────────

ERROR_CLASSIFICATION: dict[str, type] = {
    "RateLimitError": RetryableError,
    "Timeout": RetryableError,
    "ConnectionError": RetryableError,
    "ServiceUnavailable": RetryableError,
    "ValidationError": NonRetryableError,
    "AuthenticationError": NonRetryableError,
    "PermissionError": NonRetryableError,
}

def classify_error(error: Exception) -> type:
    """외부 라이브러리 에러를 내부 분류로 변환"""
    error_name = type(error).__name__
    for pattern, error_class in ERROR_CLASSIFICATION.items():
        if pattern in error_name:
            return error_class
    return RetryableError  # 기본: 재시도 시도


# ─── Temporal RetryPolicy 에서 사용 ────────────────
NON_RETRYABLE_TYPES = [
    "InputValidationError",
    "AuthenticationError",
    "UnsupportedFileError",
    "GitHubAccessDeniedError",
    "ValueError",
    "ValidationError",
]
```

### 4. S3 스토리지 추상화 (`services/storage.py`)

```python
"""
backend/app/services/storage.py
S3 스토리지 클라이언트 (LocalStack/AWS 투명 전환)

로컬: LocalStack S3 (endpoint_url 설정)
프로덕션: AWS S3 (endpoint_url 없음 → 실제 AWS)
"""
import aioboto3
from typing import BinaryIO


class StorageClient:
    """
    S3 추상화 클라이언트.
    config의 endpoint_url 유무로 LocalStack/AWS 자동 전환.
    """

    def __init__(self, s3_config: dict):
        self.config = s3_config
        self.session = aioboto3.Session()

    async def upload(
        self,
        bucket: str,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
    ) -> str:
        """파일 업로드. S3 key 반환."""
        async with self.session.client("s3", **self.config) as s3:
            if isinstance(data, bytes):
                await s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=data,
                    ContentType=content_type,
                )
            else:
                await s3.upload_fileobj(data, bucket, key)
        return key

    async def download(self, bucket: str, key: str) -> bytes | None:
        """파일 다운로드. 없으면 None."""
        async with self.session.client("s3", **self.config) as s3:
            try:
                response = await s3.get_object(Bucket=bucket, Key=key)
                return await response["Body"].read()
            except s3.exceptions.NoSuchKey:
                return None
            except Exception:
                return None

    async def delete(self, bucket: str, key: str) -> None:
        """파일 삭제."""
        async with self.session.client("s3", **self.config) as s3:
            await s3.delete_object(Bucket=bucket, Key=key)

    async def list_keys(self, bucket: str, prefix: str) -> list[str]:
        """특정 prefix 하위 키 목록."""
        keys = []
        async with self.session.client("s3", **self.config) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            async for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    keys.append(obj["Key"])
        return keys
```

### 5. 구조화된 로깅 (`core/logging.py`)

```python
"""
backend/app/core/logging.py
JSON 구조화 로깅

모든 Activity/서비스에서 일관된 로깅 형식 사용.
"""
import logging
import json
import sys
from datetime import datetime

from app.core.config import get_settings


class StructuredFormatter(logging.Formatter):
    """JSON 형식 로그 포매터"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 추가 컨텍스트
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        if hasattr(record, "phase"):
            log_data["phase"] = record.phase
        if hasattr(record, "activity"):
            log_data["activity"] = record.activity

        # 에러 정보
        if record.exc_info:
            log_data["error"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging() -> None:
    """애플리케이션 로깅 초기화. main.py에서 1회 호출."""
    settings = get_settings()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    root_logger.handlers = [handler]

    # 외부 라이브러리 로그 레벨 제한
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("temporalio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 생성"""
    return logging.getLogger(f"vantict.{name}")


class ActivityLogger:
    """
    Activity 전용 로거 (job_id 자동 포함)

    사용법:
        logger = ActivityLogger("code_analysis", job_id)
        logger.info("Analyzing repo", repo_url=url)
    """

    def __init__(self, activity_name: str, job_id: str):
        self.logger = get_logger(f"activity.{activity_name}")
        self.job_id = job_id
        self.activity_name = activity_name

    def _log(self, level: str, message: str, **kwargs):
        extra = {
            "job_id": self.job_id,
            "activity": self.activity_name,
            **kwargs,
        }
        record = self.logger.makeRecord(
            self.logger.name, getattr(logging, level),
            "", 0, message, (), None,
        )
        for k, v in extra.items():
            setattr(record, k, v)
        self.logger.handle(record)

    def info(self, message: str, **kwargs):
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log("ERROR", message, **kwargs)
```

### 6. Activity 공통 패턴

```python
"""
Activity 구현 시 반드시 따라야 하는 공통 패턴.

모든 Activity는 아래 패턴을 따른다:
"""
from temporalio import activity
from app.core.deps import get_redis, get_llm_service, get_vector_store
from app.core.errors import RetryableError, NonRetryableError
from app.core.logging import ActivityLogger


@activity.defn
async def example_activity(job_id: str, data: dict) -> dict:
    """
    Activity 표준 구현 패턴

    규칙:
    1. 의존성은 함수 내부에서 get_*()로 획득
    2. LLM은 반드시 get_llm_service() 사용 (캐시 통합)
    3. 긴 작업은 activity.heartbeat() 호출
    4. 에러는 RetryableError/NonRetryableError로 분류
    5. ActivityLogger로 구조화된 로깅
    """
    logger = ActivityLogger("example", job_id)

    try:
        # 의존성 획득
        llm = get_llm_service()
        redis = get_redis()
        vector_store = get_vector_store(job_id)

        logger.info("Starting example activity")

        # 작업 수행
        result = await llm.chat(
            messages=[{"role": "user", "content": "..."}],
            model="gpt-4o",
        )

        # heartbeat (긴 작업 시)
        activity.heartbeat("Step 1 complete")

        logger.info("Activity completed", result_size=len(str(result)))
        return result

    except Exception as e:
        logger.error("Activity failed", error=str(e))
        # 에러 분류 → Temporal이 재시도 여부 결정
        from app.core.errors import classify_error
        error_class = classify_error(e)
        raise error_class(str(e)) from e
```

---

## 공통 타입 정의 (`models/types.py`)

```python
"""
backend/app/models/types.py
전체 프로젝트에서 사용하는 공통 타입

모든 모델/Activity/서비스가 이 타입을 임포트한다.
"""
from typing import Literal, TypeAlias

# 지원 언어
SupportedLanguage: TypeAlias = Literal[
    "ko", "en", "ja", "zh-CN", "zh-TW",
    "es", "de", "fr", "pt", "vi", "th", "id"
]

# 경험 레벨
ExperienceLevel: TypeAlias = Literal["신입", "주니어", "미들", "시니어"]

# 질문 난이도
Difficulty: TypeAlias = Literal["basic", "intermediate", "advanced"]

# 질문 카테고리
QuestionCategory: TypeAlias = Literal[
    "technical_concept", "code_implementation", "architecture",
    "problem_solving", "experience_based", "behavioral"
]

# 요구사항 구분
RequirementCategory: TypeAlias = Literal["필수", "우대"]

# 코드 패턴 유형
PatternType: TypeAlias = Literal["design_pattern", "anti_pattern", "idiom"]

# 이슈 심각도
Severity: TypeAlias = Literal["info", "warning", "error"]

# 스킬 매칭 유형
MatchType: TypeAlias = Literal["exact", "similar", "partial", "none"]

# 파이프라인 단계
PipelineStep: TypeAlias = Literal[
    "plan", "document_analysis", "code_analysis", "jd_analysis",
    "aggregate_analysis", "select_topics", "craft_questions",
    "review_quality", "finalize",
]

PIPELINE_STEPS: list[str] = [
    "plan", "document_analysis", "code_analysis", "jd_analysis",
    "aggregate_analysis", "select_topics", "craft_questions",
    "review_quality", "finalize",
]

# Job 상태
JobStatusType: TypeAlias = Literal[
    "pending", "planning", "analyzing", "generating",
    "reviewing", "finalizing", "completed", "failed", "cancelled"
]
```

---

## 의존성 패키지 (`pyproject.toml` 핵심)

```toml
[project]
name = "vantict-sniper"
version = "4.1.0"
requires-python = ">=3.11"

dependencies = [
    # Web Framework
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "python-multipart>=0.0.6",

    # Temporal
    "temporalio>=1.4.0",

    # Database
    "sqlalchemy[asyncio]>=2.0.23",
    "asyncpg>=0.29.0",
    "pgvector>=0.2.4",

    # Redis
    "redis[hiredis]>=5.0.0",

    # S3
    "aioboto3>=12.0.0",

    # LLM
    "openai>=1.6.0",
    "anthropic>=0.8.0",

    # Document Parsing
    "pypdf>=3.17.0",
    "pdfplumber>=0.10.0",
    "python-docx>=1.0.0",

    # GitHub
    "gitpython>=3.1.40",
    "httpx>=0.25.0",

    # Config
    "pydantic-settings>=2.1.0",

    # Utilities
    "python-jose[cryptography]>=3.3.0",  # JWT
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]
```

---

## Activity에서의 사용 예시

```python
# 모든 Activity가 따르는 임포트 패턴

# ✅ CORRECT — 공통 도구 사용
from app.core.deps import get_redis, get_llm_service, get_vector_store, get_storage
from app.core.errors import RetryableError, NonRetryableError, NON_RETRYABLE_TYPES
from app.core.config import get_settings
from app.core.logging import ActivityLogger
from app.models.types import ExperienceLevel, PipelineStep

# ❌ WRONG — 직접 생성/접근
import os
import redis
import openai
```

---

## 관련 파일

```
backend/app/
├── core/
│   ├── __init__.py
│   ├── config.py           # Settings + get_settings()
│   ├── deps.py             # get_redis, get_db, get_llm_service, ...
│   ├── database.py         # AsyncEngine, AsyncSession (deps.py에서 사용)
│   ├── temporal.py         # get_temporal_client (deps.py에서 사용)
│   ├── errors.py           # RetryableError, NonRetryableError, classify_error
│   └── logging.py          # StructuredFormatter, ActivityLogger
├── services/
│   ├── llm_service.py      # CachedLLMService (→ checkpoint-manager SKILL 참조)
│   ├── llm_cache.py        # LLMResultCache (→ checkpoint-manager SKILL 참조)
│   ├── checkpoint_store.py # CheckpointStore (→ checkpoint-manager SKILL 참조)
│   ├── storage.py          # StorageClient (S3 추상화)
│   └── vector_store.py     # VectorStore (pgvector)
├── models/
│   └── types.py            # 공통 타입 정의
└── pyproject.toml          # 의존성 패키지
```

---

## 구현 체크리스트

에이전트가 Common Tools를 구현할 때:

- [ ] `core/config.py` — Settings 클래스 (pydantic-settings)
- [ ] `core/deps.py` — 의존성 팩토리 (Redis, DB, S3, Temporal, LLM, VectorStore)
- [ ] `core/errors.py` — 에러 계층 + 분류 유틸리티
- [ ] `core/logging.py` — 구조화된 JSON 로깅 + ActivityLogger
- [ ] `services/storage.py` — S3 클라이언트 (LocalStack/AWS 투명 전환)
- [ ] `models/types.py` — 공통 타입 정의
- [ ] `pyproject.toml` — 의존성 패키지 목록

---

## 의존성 관계

```
core/config.py        ← 모든 파일이 의존
core/deps.py          ← 모든 Activity, API 라우터가 의존
core/errors.py        ← 모든 Activity, 서비스가 의존
core/logging.py       ← 모든 Activity가 의존
services/storage.py   ← checkpoint_store, finalization이 의존
models/types.py       ← 모든 모델, Activity가 의존
```

**의존 방향**: `core/` → `services/` → `workflows/activities/` → `api/`
**역방향 의존 금지**: Activity가 API를 임포트하면 안 됨
