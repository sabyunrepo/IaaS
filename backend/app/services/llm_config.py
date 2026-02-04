"""
backend/app/services/llm_config.py
Pydantic AI Agent + LiteLLM 초기화 with Activity-specific Model Configuration
"""
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# Activity별 최적 LLM 모델 설정
# =============================================================================
# 모델 선택 기준:
# - 복잡한 추론/정확성 필요: GPT-4o, Claude Sonnet
# - 단순 작업/비용 최적화: GPT-4o-mini, Claude Haiku
# - 창의적 작업: Claude Sonnet
# =============================================================================

ACTIVITY_MODEL_CONFIG: dict[str, str] = {
    # Phase 0: Input Enrichment - 빠른 처리
    "enrich_input": "openai:gpt-4o-mini",

    # Phase 1: Planning
    "select_topics": "openai:gpt-4o",  # 중요한 의사결정 (토픽 선정)

    # Phase 2: Analysis - 복잡한 추론
    "analyze_documents": "openai:gpt-4o",  # 이력서/포트폴리오 분석
    "analyze_code": "openai:gpt-4o",  # GitHub 코드 분석
    "analyze_jd": "openai:gpt-4o-mini",  # JD 분석 (상대적으로 단순)

    # Phase 3: Question Generation - 고품질 콘텐츠 생성
    "craft_question": "openai:gpt-4o",  # 핵심 질문 생성 (중요)
    "enhance_terminology": "openai:gpt-4o-mini",  # 용어 설명 추가
    "craft_evaluation_scenarios": "openai:gpt-4o",  # 평가 시나리오 생성
    "design_follow_ups": "openai:gpt-4o-mini",  # 후속 질문 설계
    "generate_interviewer_notes": "openai:gpt-4o-mini",  # 면접관 노트 생성
    "generate_decision_guide": "openai:gpt-4o",  # 채용 의사결정 가이드
    "revise_questions": "openai:gpt-4o-mini",  # 질문 수정 (피드백 반영)

    # Legacy activity names (backward compatibility)
    "enhance_question": "openai:gpt-4o-mini",  # 질문 개선 (보조 작업)
    "generate_expected_answer": "openai:gpt-4o",  # 예상 답변 생성
    "generate_follow_ups": "openai:gpt-4o-mini",  # 후속 질문
    "generate_evaluation_rubric": "openai:gpt-4o-mini",  # 평가 기준
    "generate_interviewer_note": "openai:gpt-4o-mini",  # 인터뷰어 노트
    "generate_terminology": "openai:gpt-4o-mini",  # 용어 설명
    "generate_depth_markers": "openai:gpt-4o-mini",  # 깊이 마커

    # Phase 4: Review & Finalization
    "quality_review": "openai:gpt-4o",  # 품질 검토 (중요)
    "finalize_candidate_summary": "openai:gpt-4o",  # 후보자 요약 생성
    "finalize_interviewer_guide": "openai:gpt-4o-mini",  # 면접관 가이드 생성
    "finalize_output": "openai:gpt-4o-mini",  # 최종 요약
}


def get_model_for_activity(activity_name: str) -> str:
    """Activity 이름에 따른 최적 LLM 모델 반환

    Args:
        activity_name: Activity 함수명 (예: "analyze_documents", "craft_question")

    Returns:
        LLM 모델명 (예: "openai:gpt-4o")
    """
    model = ACTIVITY_MODEL_CONFIG.get(activity_name)
    if model:
        logger.debug(f"Using optimized model for {activity_name}: {model}")
        return model

    # 기본값: settings에서 가져옴
    default_model = settings.LLM_MODEL
    logger.debug(f"Using default model for {activity_name}: {default_model}")
    return default_model


def get_llm_agent(
    result_type: Any = None,
    system_prompt: str = "",
    model: str | None = None,
):
    """Pydantic AI Agent 생성

    Args:
        result_type: Pydantic 모델 (구조화 출력용)
        system_prompt: 시스템 프롬프트
        model: LLM 모델명 (기본값: settings.LLM_MODEL)

    Returns:
        pydantic_ai.Agent 인스턴스
    """
    from pydantic_ai import Agent

    model = model or settings.LLM_MODEL  # e.g. "openai/gpt-4o"

    kwargs = {"model": model}
    if result_type:
        kwargs["result_type"] = result_type
    if system_prompt:
        kwargs["system_prompt"] = system_prompt

    return Agent(**kwargs)


def get_llm_model() -> str:
    """현재 설정된 LLM 모델명 반환"""
    return settings.LLM_MODEL
