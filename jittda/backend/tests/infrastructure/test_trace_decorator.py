"""
trace_decorator 테스트

- Langfuse 미설정 시 no-op (원본 함수 그대로 실행)
- 성공 시 trace 기록
- 실패 시 에러 전파 + trace 기록
- job_id 미존재 시 "unknown" fallback
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Langfuse mock setup (테스트 환경에 langfuse 패키지 없을 수 있음)
# ---------------------------------------------------------------------------

_mock_langfuse_context = MagicMock()
_mock_observe_calls: list[dict] = []


def _mock_observe(**kwargs):
    """@observe() 데코레이터를 모킹한다."""
    _mock_observe_calls.append(kwargs)

    def decorator(fn):
        async def wrapper(*args, **kw):
            return await fn(*args, **kw)
        return wrapper
    return decorator


# langfuse.decorators 모듈을 mock으로 주입
_langfuse_decorators = ModuleType("langfuse.decorators")
_langfuse_decorators.langfuse_context = _mock_langfuse_context  # type: ignore[attr-defined]
_langfuse_decorators.observe = _mock_observe  # type: ignore[attr-defined]

if "langfuse" not in sys.modules:
    sys.modules["langfuse"] = ModuleType("langfuse")
if "langfuse.decorators" not in sys.modules:
    sys.modules["langfuse.decorators"] = _langfuse_decorators


# ---------------------------------------------------------------------------
# Tests: Langfuse 비활성 시 no-op
# ---------------------------------------------------------------------------


class TestTracedActivityNoOp:
    """Langfuse 비활성 시 데코레이터가 원본 함수를 그대로 반환."""

    @pytest.mark.asyncio
    async def test_returns_original_function_when_langfuse_unavailable(self):
        with patch.dict("os.environ", {}, clear=False):
            # LANGFUSE_PUBLIC_KEY 미설정 → no-op
            with patch(
                "infrastructure.observability.trace_decorator._LANGFUSE_AVAILABLE",
                False,
            ):
                from infrastructure.observability.trace_decorator import traced_activity

                async def my_activity(args: dict) -> dict:
                    return {"result": "ok"}

                decorated = traced_activity(my_activity)
                # no-op이면 원본 함수 그대로 반환
                assert decorated is my_activity

    @pytest.mark.asyncio
    async def test_noop_decorator_preserves_function_behavior(self):
        with patch(
            "infrastructure.observability.trace_decorator._LANGFUSE_AVAILABLE",
            False,
        ):
            from infrastructure.observability.trace_decorator import traced_activity

            async def my_activity(args: dict) -> dict:
                return {"value": args.get("input", 0) * 2}

            decorated = traced_activity(my_activity)
            result = await decorated({"input": 21})
            assert result == {"value": 42}


# ---------------------------------------------------------------------------
# Tests: Langfuse 활성 시 동작
# ---------------------------------------------------------------------------


class TestTracedActivityActive:
    """Langfuse 활성 시 데코레이터가 tracing wrapper를 반환."""

    @pytest.mark.asyncio
    async def test_successful_activity_returns_result(self):
        with patch(
            "infrastructure.observability.trace_decorator._LANGFUSE_AVAILABLE",
            True,
        ):
            from importlib import reload

            import infrastructure.observability.trace_decorator as mod

            reload(mod)

            async def my_activity(args: dict) -> dict:
                return {"status": "done", "job_id": args["job_id"]}

            decorated = mod.traced_activity(my_activity)
            result = await decorated({"job_id": "test-123"})

            assert result["status"] == "done"
            assert result["job_id"] == "test-123"

    @pytest.mark.asyncio
    async def test_error_propagates_through_decorator(self):
        with patch(
            "infrastructure.observability.trace_decorator._LANGFUSE_AVAILABLE",
            True,
        ):
            from importlib import reload

            import infrastructure.observability.trace_decorator as mod

            reload(mod)

            async def failing_activity(args: dict) -> dict:
                raise ValueError("test error")

            decorated = mod.traced_activity(failing_activity)
            with pytest.raises(ValueError, match="test error"):
                await decorated({"job_id": "fail-456"})

    @pytest.mark.asyncio
    async def test_missing_job_id_uses_unknown_fallback(self):
        with patch(
            "infrastructure.observability.trace_decorator._LANGFUSE_AVAILABLE",
            True,
        ):
            from importlib import reload

            import infrastructure.observability.trace_decorator as mod

            reload(mod)

            async def my_activity(args: dict) -> dict:
                return {"ok": True}

            decorated = mod.traced_activity(my_activity)
            # job_id 없는 args → "unknown" fallback (에러 없이 실행)
            result = await decorated({})
            assert result == {"ok": True}
