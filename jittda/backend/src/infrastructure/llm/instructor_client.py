"""
Instructor Client — 구조화 LLM 호출 클라이언트.

Instructor + Pydantic v2 + Langfuse 통합.
모든 LLM 호출의 구조화 출력을 보장하고 Langfuse로 추적한다.
"""
import instructor
from openai import AsyncOpenAI
from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class InstructorClient:
    """Instructor 기반 구조화 LLM 호출 클라이언트."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.moonshot.cn/v1",
        model: str = "kimi-k2.5",
        max_retries: int = 3,
    ):
        """
        Args:
            api_key: LLM API 키 (Kimi K2.5).
            base_url: OpenAI 호환 API 엔드포인트.
            model: 기본 모델명.
            max_retries: Pydantic 검증 실패 시 자동 재시도 횟수.
        """
        raw_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._client = instructor.from_openai(raw_client)
        self._model = model
        self._max_retries = max_retries

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
        return await self._client.chat.completions.create(
            model=model or self._model,
            response_model=response_model,
            messages=messages,
            temperature=temperature,
            max_retries=max_retries or self._max_retries,
        )
