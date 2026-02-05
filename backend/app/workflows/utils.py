"""
backend/app/workflows/utils.py
Temporal Activity 유틸리티 함수

LLM 호출 등 장기 실행 작업 중 heartbeat 유지를 위한 헬퍼 함수 제공
"""
import asyncio
import logging
from typing import Any, Awaitable, Callable, TypeVar

from temporalio import activity

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def run_with_heartbeat(
    coro: Awaitable[T],
    interval: float = 30.0,
    message: str | Callable[[], str] = "Waiting for async operation...",
) -> T:
    """장기 실행 코루틴에 주기적 heartbeat 전송

    LLM 호출 등 긴 작업 중에도 Temporal Activity가 타임아웃되지 않도록
    주기적으로 heartbeat를 전송합니다.

    Args:
        coro: 실행할 코루틴 (예: llm.run(prompt))
        interval: heartbeat 전송 간격 (초, 기본값: 30초)
        message: heartbeat 메시지 (문자열 또는 callable)

    Returns:
        코루틴의 결과값

    Example:
        # 기본 사용
        result = await run_with_heartbeat(llm.run(prompt))

        # 커스텀 간격 및 메시지
        result = await run_with_heartbeat(
            llm.run(prompt),
            interval=20.0,
            message="Waiting for LLM response..."
        )

        # 동적 메시지 (진행 상황 표시)
        elapsed = [0]
        def msg():
            elapsed[0] += 30
            return f"LLM processing... ({elapsed[0]}s elapsed)"
        result = await run_with_heartbeat(llm.run(prompt), message=msg)
    """
    task = asyncio.create_task(coro)
    heartbeat_count = 0

    while not task.done():
        try:
            # interval 동안 대기하되, task가 완료되면 즉시 반환
            return await asyncio.wait_for(asyncio.shield(task), timeout=interval)
        except asyncio.TimeoutError:
            # 타임아웃은 heartbeat 주기일 뿐, 계속 대기
            heartbeat_count += 1
            msg = message() if callable(message) else message
            activity.heartbeat(f"{msg} (heartbeat #{heartbeat_count})")
            logger.debug(f"Sent heartbeat #{heartbeat_count}: {msg}")
            continue
        except asyncio.CancelledError:
            # Activity 취소 시 task도 취소
            task.cancel()
            raise

    # task가 완료된 경우
    return await task


async def run_llm_with_heartbeat(
    llm_service: Any,
    prompt: str,
    activity_name: str,
    interval: float = 30.0,
    **kwargs: Any,
) -> Any:
    """CachedLLMService.run()을 heartbeat와 함께 실행

    편의 함수로, run_with_heartbeat와 CachedLLMService.run()을 결합합니다.

    Args:
        llm_service: CachedLLMService 인스턴스
        prompt: LLM 프롬프트
        activity_name: Activity 이름 (로깅용)
        interval: heartbeat 간격 (초)
        **kwargs: llm_service.run()에 전달할 추가 인자

    Returns:
        LLM 응답

    Example:
        from app.services.cached_llm import CachedLLMService
        from app.workflows.utils import run_llm_with_heartbeat

        llm = CachedLLMService()
        result = await run_llm_with_heartbeat(
            llm, prompt, "analyze_jd"
        )
    """
    elapsed = [0]

    def heartbeat_message() -> str:
        elapsed[0] += int(interval)
        return f"LLM call in progress ({activity_name}, {elapsed[0]}s elapsed)"

    return await run_with_heartbeat(
        llm_service.run(prompt, activity_name=activity_name, **kwargs),
        interval=interval,
        message=heartbeat_message,
    )
