"""
backend/app/core/config.py
애플리케이션 설정 (pydantic-settings)
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 환경
    ENV: str = "local"

    # 데이터베이스
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vantict"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Temporal
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "interview-generation"
    TEMPORAL_CLOUD_NAMESPACE: str | None = None
    TEMPORAL_TLS_CERT: str | None = None
    TEMPORAL_TLS_KEY: str | None = None
    TEMPORAL_API_KEY: str | None = None

    # Object Storage (local | r2)
    STORAGE_BACKEND: str = "local"
    LOCAL_STORAGE_PATH: str = "./data"

    # Cloudflare R2 (S3-compatible)
    R2_ACCOUNT_ID: str | None = None
    R2_ACCESS_KEY_ID: str | None = None
    R2_SECRET_ACCESS_KEY: str | None = None
    R2_BUCKET: str = "vantict-data"
    R2_PUBLIC_URL: str | None = None  # e.g. https://pub-xxx.r2.dev

    # GitHub
    GITHUB_TOKEN: str | None = None
    GITHUB_ANALYSIS_YEARS: int = 1  # 분석 기간 (기본 1년, 최대 3년 권장)

    # LLM
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None  # Google AI Studio API Key
    DEEPSEEK_API_KEY: str | None = None  # DeepSeek API Key
    ZAI_API_KEY: str | None = None  # Z.AI (Zhipu AI) API Key for GLM models
    MOONSHOT_API_KEY: str | None = None  # Moonshot AI (Kimi) API Key
    LLM_MODEL: str = "openai:gpt-4o"
    LLM_FALLBACK_MODEL: str = "anthropic:claude-3-5-sonnet-20241022"
    # GLM 모델 (Z.AI - Zhipu AI)
    # glm-4.5-flash: 무료!, glm-4.5-air: 저렴, glm-4.7: 최신 플래그십
    GLM_MODEL: str = "zai/glm-4.5-flash"  # 무료 모델
    GLM_CODER_MODEL: str = "zai/glm-4.7"  # 코드 분석용 플래그십

    # Document Parsing
    PDF_PARSER_MIN_CHARS: int = 200  # pymupdf4llm 결과가 이보다 짧으면 Gemini OCR 사용

    # Langfuse
    LANGFUSE_HOST: str = "http://localhost:3100"
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None

    # Phoenix (AI Observability - Evaluation & Experiments)
    PHOENIX_COLLECTOR_ENDPOINT: str | None = None

    # LinkedIn (Bright Data Web Scraper API)
    BRIGHTDATA_API_TOKEN: str | None = None

    # OAuth + JWT
    JWT_SECRET: str = "dev-secret-change-in-production"
    OAUTH_TOKEN_ENCRYPTION_KEY: str = "dev-key-generate-with-python-Fernet.generate_key"
    SESSION_SECRET: str = "dev-session-secret-change-in-production"
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    # Worker → Backend 내부 통신용 URL (Docker: http://backend:8000)
    INTERNAL_API_URL: str = "http://backend:8000"
    INTERNAL_API_TOKEN: str = "dev-internal-token"  # Worker↔Backend 내부 인증 토큰

    # LLM Output
    LLM_MAX_OUTPUT_TOKENS: int = 8192  # LLM 최대 출력 토큰 수

    # LLM Cache
    LLM_CACHE_ENABLED: bool = True  # False면 LLM 응답 캐싱 비활성화

    # Embedding
    EMBEDDING_DIMENSION: int = 1536

    # DB Pool
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # 기타
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost", "http://localhost:80"]

    @property
    def is_local(self) -> bool:
        return self.ENV == "local"

    @property
    def has_secure_secrets(self) -> bool:
        """프로덕션 환경에서 기본 시크릿 사용 여부 검증"""
        dev_defaults = [
            "dev-secret-change-in-production",
            "dev-session-secret-change-in-production",
        ]
        return (
            self.JWT_SECRET not in dev_defaults
            and self.SESSION_SECRET not in dev_defaults
        )

    @property
    def r2_endpoint(self) -> str | None:
        if self.R2_ACCOUNT_ID:
            return f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        return None

    @property
    def storage_config(self) -> dict:
        if self.STORAGE_BACKEND == "r2":
            return {
                "backend": "r2",
                "endpoint_url": self.r2_endpoint,
                "bucket": self.R2_BUCKET,
            }
        return {"backend": "local", "path": self.LOCAL_STORAGE_PATH}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
