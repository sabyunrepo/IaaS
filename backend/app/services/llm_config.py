"""
backend/app/services/llm_config.py
LLM Configuration with Resilient Routing

Features:
- Activity별 최적 모델 설정
- LiteLLM Router 통합 (Fallback, Retry, Cooldown)
- Pydantic AI Agent 지원 (pydantic-ai-litellm 브릿지)
- Instructor 통합 (구조화된 출력)
- Tenacity 기반 재시도 (Exponential Backoff)
"""
import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

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

# Moonshot AI (Kimi) 모델
# K2: 128K context, MoE 1T params (32B active), $0.06/1M input, $0.18/1M output
# K2.5: 256K context, vision 지원, $0.06/1M input, $0.18/1M output (권장)
# 중국어+영어 최적화, 코드 분석/문서 이해에 강점
KIMI_K2_MODEL = "moonshot/moonshot-v1-128k"  # K2: 128K context
KIMI_K2_5_MODEL = "moonshot/moonshot-v1-auto"  # K2.5: auto mode (최신, 권장)
KIMI_CHAT_MODEL = KIMI_K2_5_MODEL  # 기본 채팅용
KIMI_CODER_MODEL = KIMI_K2_5_MODEL  # 코드 분석용

# Legacy alias (backward compatibility)
CODE_ANALYSIS_GLM_MODEL = GLM_CODER_MODEL

ACTIVITY_MODEL_CONFIG: dict[str, str] = {
    # Phase 0: Input Enrichment - 빠른 처리, GLM으로 비용 절감
    "enrich_input": GLM_CHAT_MODEL,

    # Phase 1: Planning
    "select_topics": KIMI_CHAT_MODEL,  # Kimi로 교체 (토픽 선정)

    # Phase 2: Analysis - Kimi K2.5 (128K/256K context, 문서/코드 분석 강점)
    "analyze_documents": KIMI_CHAT_MODEL,  # 문서 분석 → Kimi
    "analyze_code": KIMI_CODER_MODEL,  # 코드 분석 Manager → Kimi
    "analyze_jd": KIMI_CHAT_MODEL,  # JD 분석 → Kimi

    # Phase 2: HYBRID 3-Stage 코드 분석 (Kimi Coder 모델)
    "code_overview_analysis": KIMI_CODER_MODEL,      # Stage 1: Overview Agent
    "code_deep_analysis": KIMI_CODER_MODEL,          # Stage 2: Deep Analysis (prefix match)
    "code_synthesis_analysis": KIMI_CODER_MODEL,     # Stage 3: Synthesis Agent

    # Phase 3: Question Generation - Kimi로 교체 (테스트 후 품질 확인)
    "craft_question": KIMI_CHAT_MODEL,  # 핵심 질문 생성 → Kimi
    "enhance_terminology": GLM_CHAT_MODEL,  # 용어 설명 추가 (GLM 유지)
    "craft_evaluation_scenarios": KIMI_CHAT_MODEL,  # 평가 시나리오 → Kimi
    "design_follow_ups": GLM_CHAT_MODEL,  # 후속 질문 설계 (GLM 유지)
    "generate_interviewer_notes": GLM_CHAT_MODEL,  # 면접관 노트 (GLM 유지)
    "generate_decision_guide": KIMI_CHAT_MODEL,  # 채용 의사결정 가이드 → Kimi
    "revise_questions": GLM_CHAT_MODEL,  # 질문 수정 (GLM 유지)

    # Legacy activity names (backward compatibility)
    "enhance_question": GLM_CHAT_MODEL,  # 질문 개선 (GLM 유지)
    "generate_expected_answer": KIMI_CHAT_MODEL,  # 예상 답변 → Kimi
    "generate_follow_ups": GLM_CHAT_MODEL,  # 후속 질문 (GLM 유지)
    "generate_evaluation_rubric": GLM_CHAT_MODEL,  # 평가 기준 (GLM 유지)
    "generate_interviewer_note": GLM_CHAT_MODEL,  # 인터뷰어 노트 (GLM 유지)
    "generate_terminology": GLM_CHAT_MODEL,  # 용어 설명 (GLM 유지)
    "generate_depth_markers": GLM_CHAT_MODEL,  # 깊이 마커 (GLM 유지)

    # Phase 4: Review & Finalization - Kimi로 교체
    "quality_review": KIMI_CHAT_MODEL,  # 품질 검토 → Kimi
    "finalize_candidate_summary": KIMI_CHAT_MODEL,  # 후보자 요약 → Kimi
    "finalize_interviewer_guide": GLM_CHAT_MODEL,  # 면접관 가이드 (GLM 유지)
    "finalize_output": GLM_CHAT_MODEL,  # 최종 요약 (GLM 유지)
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
    Non-native (requires LiteLLM bridge): zai (Z.AI/Zhipu), moonshot (Kimi), cohere, ai21, etc.
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
