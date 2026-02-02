"""
backend/app/core/observability.py
Langfuse LLM observability — LiteLLM callback 방식
"""
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_initialized = False


def setup_langfuse() -> bool:
    """Langfuse를 LiteLLM success/failure callback으로 등록.

    LANGFUSE_PUBLIC_KEY가 설정되지 않으면 skip.
    Returns True if enabled.
    """
    global _initialized
    if _initialized:
        return True

    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        logger.info("Langfuse disabled (LANGFUSE_PUBLIC_KEY not set)")
        return False

    try:
        import litellm

        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]

        # LiteLLM reads these env vars automatically, but set explicitly
        import os
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.LANGFUSE_PUBLIC_KEY)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.LANGFUSE_SECRET_KEY)
        os.environ.setdefault("LANGFUSE_HOST", settings.LANGFUSE_HOST)

        _initialized = True
        logger.info(f"Langfuse enabled → {settings.LANGFUSE_HOST}")
        return True
    except Exception as e:
        logger.warning(f"Langfuse setup failed: {e}")
        return False
