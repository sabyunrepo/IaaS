"""
backend/app/services/llm_resilient.py
Resilient LLM Call Wrapper

Features:
- Tenacity: Exponential Backoff with Jitter
- Response Validation: Truncation Detection (finish_reason)
- Custom Exceptions for retry control
"""
import logging
from typing import Any

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
    before_sleep_log,
)
from litellm.exceptions import (
    RateLimitError,
    APIConnectionError,
    Timeout,
    ServiceUnavailableError,
    APIError,
)

from app.services.llm_router import get_router

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================

class TruncatedResponseError(Exception):
    """LLM 응답이 토큰 한도로 중단됨 (finish_reason=length)"""
    pass


class EmptyResponseError(Exception):
    """LLM 응답이 비어있음"""
    pass


class InvalidResponseError(Exception):
    """LLM 응답이 유효하지 않음"""
    pass


# 재시도 대상 예외 목록
RETRYABLE_EXCEPTIONS = (
    RateLimitError,
    APIConnectionError,
    Timeout,
    ServiceUnavailableError,
    TruncatedResponseError,
    EmptyResponseError,
)


# =============================================================================
# Response Validation
# =============================================================================

def validate_response(response: Any, allow_truncated: bool = False) -> bool:
    """응답 완전성 검증

    Args:
        response: LiteLLM response object
        allow_truncated: True면 truncation 허용 (재시도 안함)

    Returns:
        True if valid

    Raises:
        EmptyResponseError: 응답이 비어있을 때
        TruncatedResponseError: 토큰 한도로 잘렸을 때
    """
    # 1. 응답 존재 확인
    if not response:
        raise EmptyResponseError("Response is None")

    if not hasattr(response, 'choices') or not response.choices:
        raise EmptyResponseError("Response has no choices")

    choice = response.choices[0]

    # 2. 메시지 내용 확인
    if not hasattr(choice, 'message') or not choice.message:
        raise EmptyResponseError("Response has no message")

    content = getattr(choice.message, 'content', None)
    if content is None or (isinstance(content, str) and not content.strip()):
        raise EmptyResponseError("Response content is empty")

    # 3. finish_reason 확인
    finish_reason = getattr(choice, 'finish_reason', None)

    if finish_reason == "length" and not allow_truncated:
        logger.warning(
            f"Response truncated (finish_reason=length). "
            f"Content length: {len(content) if content else 0}"
        )
        raise TruncatedResponseError(
            f"Response truncated due to token limit. "
            f"Got {len(content)} chars before truncation."
        )

    if finish_reason == "content_filter":
        logger.warning("Response filtered by content filter")
        raise InvalidResponseError("Response blocked by content filter")

    # 유효한 finish_reason
    valid_reasons = ("stop", "end_turn", "tool_calls", "function_call", None)
    if finish_reason not in valid_reasons and finish_reason != "length":
        logger.warning(f"Unexpected finish_reason: {finish_reason}")

    return True


def get_response_content(response: Any) -> str:
    """응답에서 content 추출"""
    if not response or not response.choices:
        return ""

    message = response.choices[0].message
    return getattr(message, 'content', "") or ""


# =============================================================================
# Resilient Completion
# =============================================================================

async def resilient_completion(
    model: str,
    messages: list[dict],
    max_retries: int = 5,
    min_wait: float = 4.0,
    max_wait: float = 60.0,
    allow_truncated: bool = False,
    **kwargs: Any,
) -> Any:
    """Rate Limit + Truncation 자동 처리 LLM 호출

    Args:
        model: 모델 이름 (router에 등록된 model_name)
        messages: 대화 메시지 리스트
        max_retries: 최대 재시도 횟수
        min_wait: 최소 대기 시간 (초)
        max_wait: 최대 대기 시간 (초)
        allow_truncated: True면 truncation 허용 (재시도 안함)
        **kwargs: 추가 LiteLLM 파라미터

    Returns:
        LiteLLM completion response (검증됨)

    Raises:
        RetryError: 모든 재시도 실패
        Exception: 재시도 불가능한 오류
    """
    router = get_router()
    last_exception = None

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential_jitter(
            initial=min_wait,
            max=max_wait,
            jitter=5,  # 랜덤 jitter 추가
        ),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    ):
        with attempt:
            attempt_number = attempt.retry_state.attempt_number
            logger.debug(
                f"Attempt {attempt_number}/{max_retries} for model={model}"
            )

            try:
                # Router를 통한 호출 (자체 fallback 로직 포함)
                response = await router.acompletion(
                    model=model,
                    messages=messages,
                    **kwargs,
                )

                # 응답 검증
                validate_response(response, allow_truncated=allow_truncated)

                logger.debug(
                    f"Success on attempt {attempt_number} for model={model}"
                )
                return response

            except RETRYABLE_EXCEPTIONS as e:
                last_exception = e
                logger.warning(
                    f"Retryable error on attempt {attempt_number}: "
                    f"{type(e).__name__}: {e}"
                )
                raise  # Tenacity가 재시도 처리

            except Exception as e:
                # 재시도 불가능한 오류
                logger.error(
                    f"Non-retryable error on attempt {attempt_number}: "
                    f"{type(e).__name__}: {e}"
                )
                raise

    # 모든 재시도 실패
    logger.error(f"All {max_retries} retries failed for model={model}")
    raise last_exception or RuntimeError("Unknown error after all retries")


async def resilient_completion_with_content(
    model: str,
    messages: list[dict],
    **kwargs: Any,
) -> str:
    """응답 content만 반환하는 간편 함수"""
    response = await resilient_completion(model, messages, **kwargs)
    return get_response_content(response)


# =============================================================================
# Retry Decorator (Activity용)
# =============================================================================

def create_retry_decorator(
    max_attempts: int = 5,
    min_wait: float = 4.0,
    max_wait: float = 60.0,
):
    """Tenacity 재시도 데코레이터 생성 (Activity에서 사용)

    Usage:
        @create_retry_decorator(max_attempts=3)
        async def my_llm_function():
            ...
    """
    from tenacity import retry

    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=min_wait, max=max_wait, jitter=5),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
