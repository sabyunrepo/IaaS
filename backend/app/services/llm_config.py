"""
backend/app/services/llm_config.py
Pydantic AI Agent + LiteLLM 초기화
"""
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_llm_agent(result_type: Any = None, system_prompt: str = ""):
    """Pydantic AI Agent 생성

    Args:
        result_type: Pydantic 모델 (구조화 출력용)
        system_prompt: 시스템 프롬프트

    Returns:
        pydantic_ai.Agent 인스턴스
    """
    from pydantic_ai import Agent

    model = settings.LLM_MODEL  # e.g. "openai/gpt-4o"

    kwargs = {"model": model}
    if result_type:
        kwargs["result_type"] = result_type
    if system_prompt:
        kwargs["system_prompt"] = system_prompt

    return Agent(**kwargs)


def get_llm_model() -> str:
    """현재 설정된 LLM 모델명 반환"""
    return settings.LLM_MODEL
