"""
Langfuse Trace Decorator — Activity + LLM Call 3단 추적.

Trace Hierarchy:
  Trace (session_id=job_id) → Span (activity) → Generation (LLM call)

@observe() 데코레이터 기반. Langfuse SDK >=2.57.0 필요.
Langfuse 미설정 시 no-op (graceful degradation).
"""
from __future__ import annotations

import functools
import logging
import os
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Langfuse 가용성 확인 (패키지 import + 환경변수 설정 여부)
try:
    from langfuse.decorators import langfuse_context, observe

    _LANGFUSE_AVAILABLE = bool(os.environ.get("LANGFUSE_PUBLIC_KEY"))
except ImportError:
    _LANGFUSE_AVAILABLE = False


def traced_activity(fn: Callable) -> Callable:
    """Temporal Activity에 Langfuse tracing을 추가하는 데코레이터.

    @activity.defn 아래(안쪽)에 적용:
        @activity.defn
        @traced_activity
        async def my_activity(args: dict) -> dict: ...

    동작:
        1. Langfuse trace 생성 (session_id=job_id로 Job 단위 그룹핑)
        2. Activity 이름, 소요 시간, 성공/실패 기록
        3. Langfuse 미설정 시 no-op (원본 함수 그대로 실행)
    """
    if not _LANGFUSE_AVAILABLE:
        return fn

    @observe()
    async def _observed(args: dict[str, Any]) -> dict[str, Any]:
        job_id = args.get("job_id", "unknown")
        try:
            langfuse_context.update_current_trace(
                name=f"job-{job_id}",
                session_id=job_id,
            )
            langfuse_context.update_current_observation(
                name=fn.__name__,
                metadata={"job_id": job_id, "activity": fn.__name__},
            )
        except Exception:
            logger.debug("Langfuse trace setup failed, continuing without tracing")

        start = time.monotonic()
        try:
            result = await fn(args)
            elapsed = time.monotonic() - start
            try:
                langfuse_context.update_current_observation(
                    status_message="success",
                    metadata={
                        "job_id": job_id,
                        "activity": fn.__name__,
                        "duration_s": round(elapsed, 2),
                    },
                )
            except Exception:
                pass
            return result
        except Exception as e:
            elapsed = time.monotonic() - start
            try:
                langfuse_context.update_current_observation(
                    status_message="error",
                    level="ERROR",
                    metadata={
                        "job_id": job_id,
                        "activity": fn.__name__,
                        "duration_s": round(elapsed, 2),
                        "error_type": type(e).__name__,
                        "error": str(e)[:500],
                    },
                )
            except Exception:
                pass
            raise

    @functools.wraps(fn)
    async def wrapper(args: dict[str, Any]) -> dict[str, Any]:
        try:
            return await _observed(args)
        finally:
            try:
                langfuse_context.flush()
            except Exception:
                pass

    return wrapper
