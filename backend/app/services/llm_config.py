"""
backend/app/services/llm_config.py
Pydantic AI Agent + LiteLLM 초기화 with Activity-specific Model Configuration
"""
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# Activity별 최적 LLM 모델 설정 (Langfuse upload_prompts_to_langfuse.py와 동기화)
# =============================================================================
# 모델 선택 기준:
# - 복잡한 추론/정확성 필요: GPT-4o, Claude Sonnet
# - 단순 작업/비용 최적화: Z.AI GLM (glm-4.5-flash: 무료!)
# - 코드 분석 최적화: Z.AI GLM-4.7 (플래그십)
# - 창의적 작업: Claude Sonnet
# =============================================================================

# Z.AI GLM 모델 (Zhipu AI)
# glm-4.5-flash: 무료! 단순 작업에 최적
# glm-4.5-air: $0.20/1M input, $1.10/1M output
# glm-4.7: $0.60/1M input, $2.20/1M output (최신 플래그십)
GLM_CHAT_MODEL = "zai/glm-4.5-flash"  # 무료 모델
GLM_CODER_MODEL = "zai/glm-4.7"  # 코드 분석용 플래그십

# Legacy alias (backward compatibility)
CODE_ANALYSIS_GLM_MODEL = GLM_CODER_MODEL

ACTIVITY_MODEL_CONFIG: dict[str, str] = {
    # Phase 0: Input Enrichment - 빠른 처리, GLM으로 비용 절감
    "enrich_input": GLM_CHAT_MODEL,

    # Phase 1: Planning
    "select_topics": "openai:gpt-4o",  # 중요한 의사결정 (토픽 선정)

    # Phase 2: Analysis
    "analyze_documents": "openai:gpt-4o",  # 문서 분석 (품질 중요)
    "analyze_code": GLM_CODER_MODEL,  # 코드 분석 Manager (GLM Coder)
    "analyze_jd": GLM_CHAT_MODEL,  # JD 분석 (GLM Chat)

    # Phase 2: HYBRID 3-Stage 코드 분석 (GLM Coder 모델)
    "code_overview_analysis": GLM_CODER_MODEL,      # Stage 1: Overview Agent
    "code_deep_analysis": GLM_CODER_MODEL,          # Stage 2: Deep Analysis (prefix match)
    "code_synthesis_analysis": GLM_CODER_MODEL,     # Stage 3: Synthesis Agent

    # Phase 3: Question Generation - 핵심은 GPT-4o, 보조는 GLM
    "craft_question": "openai:gpt-4o",  # 핵심 질문 생성 (중요)
    "enhance_terminology": GLM_CHAT_MODEL,  # 용어 설명 추가 (GLM)
    "craft_evaluation_scenarios": "openai:gpt-4o",  # 평가 시나리오 생성
    "design_follow_ups": GLM_CHAT_MODEL,  # 후속 질문 설계 (GLM)
    "generate_interviewer_notes": GLM_CHAT_MODEL,  # 면접관 노트 생성 (GLM)
    "generate_decision_guide": "openai:gpt-4o",  # 채용 의사결정 가이드
    "revise_questions": GLM_CHAT_MODEL,  # 질문 수정 (GLM)

    # Legacy activity names (backward compatibility)
    "enhance_question": GLM_CHAT_MODEL,  # 질문 개선 (GLM)
    "generate_expected_answer": "openai:gpt-4o",  # 예상 답변 생성
    "generate_follow_ups": GLM_CHAT_MODEL,  # 후속 질문 (GLM)
    "generate_evaluation_rubric": GLM_CHAT_MODEL,  # 평가 기준 (GLM)
    "generate_interviewer_note": GLM_CHAT_MODEL,  # 인터뷰어 노트 (GLM)
    "generate_terminology": GLM_CHAT_MODEL,  # 용어 설명 (GLM)
    "generate_depth_markers": GLM_CHAT_MODEL,  # 깊이 마커 (GLM)

    # Phase 4: Review & Finalization
    "quality_review": "openai:gpt-4o",  # 품질 검토 (중요)
    "finalize_candidate_summary": "openai:gpt-4o",  # 후보자 요약 생성
    "finalize_interviewer_guide": GLM_CHAT_MODEL,  # 면접관 가이드 (GLM)
    "finalize_output": GLM_CHAT_MODEL,  # 최종 요약 (GLM)
}


def get_model_for_activity(activity_name: str) -> str:
    """Activity 이름에 따른 최적 LLM 모델 반환

    Args:
        activity_name: Activity 함수명 (예: "analyze_documents", "craft_question")

    Returns:
        LLM 모델명 (예: "openai:gpt-4o")

    Note:
        HYBRID 코드 분석 Activity는 prefix 매칭 지원
        (예: "code_deep_analysis_src/main.py" → "code_deep_analysis" 매칭)
    """
    # 정확한 매칭 먼저 시도
    model = ACTIVITY_MODEL_CONFIG.get(activity_name)
    if model:
        logger.debug(f"Using optimized model for {activity_name}: {model}")
        return model

    # Prefix 매칭 시도 (HYBRID 코드 분석용)
    # code_deep_analysis_file/path.py → code_deep_analysis
    for config_key, config_model in ACTIVITY_MODEL_CONFIG.items():
        if activity_name.startswith(config_key):
            logger.debug(f"Using prefix-matched model for {activity_name}: {config_model}")
            return config_model

    # 기본값: settings에서 가져옴
    default_model = settings.LLM_MODEL
    logger.debug(f"Using default model for {activity_name}: {default_model}")
    return default_model


def _is_native_pydantic_ai_model(model_name: str) -> bool:
    """Check if model is natively supported by pydantic-ai.

    Native models: openai, anthropic, gemini, groq, mistral, ollama, vertexai, bedrock
    Non-native (requires LiteLLM bridge): zai (Z.AI/Zhipu), cohere, ai21, etc.
    """
    native_prefixes = (
        "openai:", "openai/",
        "anthropic:", "anthropic/",
        "gemini:", "gemini/",
        "groq:", "groq/",
        "mistral:", "mistral/",
        "ollama:", "ollama/",
        "vertexai:", "vertexai/",
        "bedrock:", "bedrock/",
    )
    return model_name.startswith(native_prefixes)


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

    Note:
        - Native models (openai, anthropic, etc.): 직접 pydantic-ai Agent에 전달
        - Non-native models (zai, cohere, etc.): LiteLLMModel wrapper 사용
    """
    from pydantic_ai import Agent

    model_name = model or settings.LLM_MODEL  # e.g. "openai/gpt-4o" or "zai/glm-4.5-flash"

    # Determine model wrapper based on provider
    if _is_native_pydantic_ai_model(model_name):
        # Native pydantic-ai model - use directly
        model_instance = model_name
        logger.debug(f"Using native pydantic-ai model: {model_name}")
    else:
        # Non-native model (Z.AI, Cohere, etc.) - use LiteLLM bridge
        try:
            from pydantic_ai_litellm import LiteLLMModel
            model_instance = LiteLLMModel(model_name=model_name)
            logger.debug(f"Using LiteLLM bridge for non-native model: {model_name}")
        except ImportError:
            logger.warning(
                f"pydantic-ai-litellm not installed. Falling back to native model handling for: {model_name}"
            )
            model_instance = model_name

    kwargs = {"model": model_instance}
    if result_type:
        kwargs["result_type"] = result_type
    if system_prompt:
        kwargs["system_prompt"] = system_prompt

    return Agent(**kwargs)


def get_llm_model() -> str:
    """현재 설정된 LLM 모델명 반환"""
    return settings.LLM_MODEL
