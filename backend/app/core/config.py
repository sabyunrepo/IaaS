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

    # LLM
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    LLM_MODEL: str = "openai/gpt-4o"
    LLM_FALLBACK_MODEL: str = "anthropic/claude-sonnet-4-20250514"

    # Langfuse
    LANGFUSE_HOST: str = "http://localhost:3100"
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None

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

    # Embedding
    EMBEDDING_DIMENSION: int = 1536

    # 기타
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    @property
    def is_local(self) -> bool:
        return self.ENV == "local"

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
