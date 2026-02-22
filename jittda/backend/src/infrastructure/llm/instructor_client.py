"""
Instructor Client — 구조화 LLM 호출 클라이언트.

Instructor + Pydantic v2 + Langfuse 통합.
모든 LLM 호출의 구조화 출력을 보장하고 Langfuse로 추적한다.
"""
import logging
import os
import time

import instructor
from openai import AsyncOpenAI
from typing import TypeVar, Type
from pydantic import BaseModel

from infrastructure.resilience.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Langfuse @observe 가용성 확인 (패키지 + 환경변수)
try:
    from langfuse.decorators import langfuse_context, observe

    _LANGFUSE_AVAILABLE = bool(os.environ.get("LANGFUSE_PUBLIC_KEY"))
except ImportError:
    _LANGFUSE_AVAILABLE = False


class InstructorClient:
    """Instructor 기반 구조화 LLM 호출 클라이언트."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.moonshot.cn/v1",
        model: str = "kimi-k2.5",
        max_retries: int = 3,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        """
        Args:
            api_key: LLM API 키 (Kimi K2.5).
            base_url: OpenAI 호환 API 엔드포인트.
            model: 기본 모델명.
            max_retries: Pydantic 검증 실패 시 자동 재시도 횟수.
            circuit_breaker: Circuit breaker 인스턴스 (없으면 직접 호출).
        """
        raw_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._client = instructor.from_openai(raw_client)
        self._model = model
        self._max_retries = max_retries
        self._cb = circuit_breaker

    async def create(
        self,
        *,
        response_model: Type[T],
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_retries: int | None = None,
    ) -> T:
        """구조화 출력을 생성한다.

        Args:
            response_model: Pydantic 모델 클래스.
            messages: OpenAI 형식 메시지 리스트.
            model: 모델명 (None이면 기본 모델).
            temperature: 생성 온도.
            max_retries: 재시도 횟수 (None이면 기본값).

        Returns:
            response_model 인스턴스.
        """
        used_model = model or self._model

        async def _do_create() -> T:
            start = time.monotonic()
            try:
                if _LANGFUSE_AVAILABLE:
                    result = await self._create_with_trace(
                        response_model=response_model,
                        messages=messages,
                        model=used_model,
                        temperature=temperature,
                        max_retries=max_retries,
                    )
                else:
                    result = await self._client.chat.completions.create(
                        model=used_model,
                        response_model=response_model,
                        messages=messages,
                        temperature=temperature,
                        max_retries=max_retries or self._max_retries,
                    )
            finally:
                elapsed = time.monotonic() - start
                _record_llm_metrics(used_model, response_model.__name__, elapsed)
            return result

        if self._cb:
            return await self._cb.call(_do_create)
        return await _do_create()

    async def _create_with_trace(
        self,
        *,
        response_model: Type[T],
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_retries: int | None,
    ) -> T:
        """Langfuse generation child span 내에서 LLM 호출."""

        @observe(as_type="generation", name=f"llm-{response_model.__name__}")
        async def _traced_llm_call() -> T:
            try:
                langfuse_context.update_current_observation(
                    metadata={"model": model, "response_model": response_model.__name__},
                )
            except Exception:
                pass

            start = time.monotonic()
            result = await self._client.chat.completions.create(
                model=model,
                response_model=response_model,
                messages=messages,
                temperature=temperature,
                max_retries=max_retries or self._max_retries,
            )
            elapsed = time.monotonic() - start

            try:
                langfuse_context.update_current_observation(
                    metadata={
                        "model": model,
                        "response_model": response_model.__name__,
                        "temperature": temperature,
                        "duration_s": round(elapsed, 2),
                    },
                )
            except Exception:
                pass

            return result

        return await _traced_llm_call()


def _record_llm_metrics(model: str, response_model: str, elapsed: float) -> None:
    """Prometheus LLM 메트릭 기록 (prometheus-client 미설치 시 no-op)."""
    try:
        from infrastructure.observability.metrics import (
            llm_call_duration_seconds,
            llm_calls_total,
        )

        llm_calls_total.labels(model=model, response_model=response_model).inc()
        llm_call_duration_seconds.labels(model=model).observe(elapsed)
    except ImportError:
        pass
