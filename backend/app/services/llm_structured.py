"""
backend/app/services/llm_structured.py
Instructor Integration for Structured LLM Output

Features:
- Pydantic 모델 기반 구조화된 출력
- 검증 실패 시 자동 재시도 (LLM에게 오류 전달)
- Router와 통합된 Fallback 지원
- 비동기 지원
"""
import logging
from typing import TypeVar, Any

import instructor
from pydantic import BaseModel

from app.services.llm_router import get_router
from app.services.json_parser import safe_parse_json

logger = logging.getLogger(__name__)

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)


# =============================================================================
# Instructor Client (Lazy Initialization)
# =============================================================================

_instructor_client = None


def get_instructor_client():
    """Instructor client 싱글톤 (Router 연동)"""
    global _instructor_client

    if _instructor_client is None:
        router = get_router()
        # Router의 acompletion 메서드와 Instructor 연동
        _instructor_client = instructor.from_litellm(router.acompletion)
        logger.info("Instructor client initialized with LiteLLM Router")

    return _instructor_client


# =============================================================================
# Structured Output Functions
# =============================================================================

async def get_structured_output(
    model: str,
    response_model: type[T],
    messages: list[dict],
    max_retries: int = 3,
    **kwargs: Any,
) -> T:
    """Pydantic 모델로 구조화된 출력 생성

    Instructor의 자동 재시도 기능:
    - Pydantic 검증 실패 시 오류 메시지를 LLM에게 전달
    - LLM이 오류를 참고하여 수정된 출력 생성
    - max_retries 횟수만큼 반복

    Args:
        model: 모델 이름 (router에 등록된 model_name)
        response_model: Pydantic 모델 클래스
        messages: 대화 메시지 리스트
        max_retries: 검증 실패 시 최대 재시도 횟수
        **kwargs: 추가 LiteLLM 파라미터

    Returns:
        검증된 Pydantic 모델 인스턴스

    Raises:
        instructor.exceptions.InstructorRetryException: 모든 재시도 실패
        pydantic.ValidationError: 검증 실패 (재시도 후에도)
    """
    client = get_instructor_client()

    logger.debug(
        f"Requesting structured output: model={model}, "
        f"response_model={response_model.__name__}, max_retries={max_retries}"
    )

    try:
        result = await client.chat.completions.create(
            model=model,
            response_model=response_model,
            messages=messages,
            max_retries=max_retries,
            **kwargs,
        )

        logger.debug(
            f"Structured output success: {response_model.__name__}"
        )
        return result

    except Exception as e:
        logger.error(
            f"Structured output failed: {type(e).__name__}: {e}"
        )
        raise


async def get_structured_output_safe(
    model: str,
    response_model: type[T],
    messages: list[dict],
    max_retries: int = 3,
    fallback_model: str | None = None,
    **kwargs: Any,
) -> T | None:
    """안전한 구조화된 출력 (예외 시 None 반환)

    Primary 모델 실패 시 fallback_model로 재시도.

    Args:
        model: Primary 모델
        response_model: Pydantic 모델 클래스
        messages: 대화 메시지 리스트
        max_retries: 각 모델에서 최대 재시도 횟수
        fallback_model: Primary 실패 시 사용할 모델
        **kwargs: 추가 파라미터

    Returns:
        Pydantic 모델 인스턴스 또는 None
    """
    # Primary 시도
    try:
        return await get_structured_output(
            model=model,
            response_model=response_model,
            messages=messages,
            max_retries=max_retries,
            **kwargs,
        )
    except Exception as e:
        logger.warning(f"Primary model {model} failed: {e}")

    # Fallback 시도
    if fallback_model:
        try:
            logger.info(f"Trying fallback model: {fallback_model}")
            return await get_structured_output(
                model=fallback_model,
                response_model=response_model,
                messages=messages,
                max_retries=max_retries,
                **kwargs,
            )
        except Exception as e:
            logger.warning(f"Fallback model {fallback_model} failed: {e}")

    return None


# =============================================================================
# Raw Output with Manual Parsing (Fallback Strategy)
# =============================================================================

async def get_output_with_json_fallback(
    model: str,
    response_model: type[T],
    messages: list[dict],
    max_retries: int = 3,
    **kwargs: Any,
) -> T:
    """Instructor 실패 시 수동 JSON 파싱으로 fallback

    순서:
    1. Instructor로 구조화된 출력 시도
    2. 실패 시 일반 completion + safe_parse_json으로 시도
    3. Pydantic 모델로 수동 변환

    Args:
        model: 모델 이름
        response_model: Pydantic 모델 클래스
        messages: 대화 메시지 리스트
        max_retries: 최대 재시도 횟수
        **kwargs: 추가 파라미터

    Returns:
        Pydantic 모델 인스턴스

    Raises:
        ValueError: 모든 방법 실패
    """
    # 1. Instructor 시도
    try:
        return await get_structured_output(
            model=model,
            response_model=response_model,
            messages=messages,
            max_retries=max_retries,
            **kwargs,
        )
    except Exception as e:
        logger.warning(f"Instructor failed, trying JSON fallback: {e}")

    # 2. 일반 completion + 수동 파싱
    from app.services.llm_resilient import resilient_completion

    # JSON 출력 유도 메시지 추가
    json_prompt_messages = messages.copy()
    json_prompt_messages.append({
        "role": "system",
        "content": (
            f"Respond ONLY with valid JSON matching this schema: "
            f"{response_model.model_json_schema()}"
        ),
    })

    try:
        response = await resilient_completion(
            model=model,
            messages=json_prompt_messages,
            max_retries=max_retries,
            **kwargs,
        )

        content = response.choices[0].message.content
        parsed = safe_parse_json(content, raise_on_failure=True)

        # Pydantic 모델로 변환
        result = response_model.model_validate(parsed)
        logger.info("JSON fallback parsing succeeded")
        return result

    except Exception as e:
        logger.error(f"JSON fallback also failed: {e}")
        raise ValueError(
            f"Failed to get structured output for {response_model.__name__}: {e}"
        )


# =============================================================================
# Batch Processing
# =============================================================================

async def get_structured_outputs_batch(
    model: str,
    response_model: type[T],
    message_batches: list[list[dict]],
    max_retries: int = 2,
    continue_on_error: bool = True,
    **kwargs: Any,
) -> list[T | None]:
    """여러 요청의 구조화된 출력 배치 처리

    Args:
        model: 모델 이름
        response_model: Pydantic 모델 클래스
        message_batches: 메시지 리스트의 리스트
        max_retries: 각 요청의 최대 재시도 횟수
        continue_on_error: True면 오류 시에도 계속 진행
        **kwargs: 추가 파라미터

    Returns:
        결과 리스트 (오류 시 None)
    """
    import asyncio

    async def process_single(messages: list[dict]) -> T | None:
        try:
            return await get_structured_output(
                model=model,
                response_model=response_model,
                messages=messages,
                max_retries=max_retries,
                **kwargs,
            )
        except Exception as e:
            if continue_on_error:
                logger.warning(f"Batch item failed: {e}")
                return None
            raise

    tasks = [process_single(msgs) for msgs in message_batches]
    return await asyncio.gather(*tasks)


# =============================================================================
# Utility Functions
# =============================================================================

def create_system_message(content: str) -> dict:
    """시스템 메시지 생성"""
    return {"role": "system", "content": content}


def create_user_message(content: str) -> dict:
    """사용자 메시지 생성"""
    return {"role": "user", "content": content}


def create_messages(system: str, user: str) -> list[dict]:
    """시스템 + 사용자 메시지 리스트 생성"""
    return [
        create_system_message(system),
        create_user_message(user),
    ]
