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
# - 전체 Activity: Kimi K2.5 (256K context, $0.23/$3.00 per 1M USD)
# - 코드 분석: Kimi K2.5 (enhanced agentic coding + 멀티모달)
# - JD 분석: GPT-4.1 mini (저컨텍스트 구조화 추출, $0.40/$1.60 per 1M USD)
# - Fallback: GLM-4.5-flash 무료 모델 (settings.LLM_FALLBACK_MODEL)
# =============================================================================

# Z.AI GLM 모델 (Zhipu AI)
# glm-4.5-flash: 무료! 단순 작업에 최적
# glm-4.5-air: $0.20/1M input, $1.10/1M output
# glm-4.7: $0.60/1M input, $2.20/1M output (최신 플래그십)
GLM_CHAT_MODEL = "zai/glm-4.5-flash"  # 무료 모델
GLM_CODER_MODEL = "zai/glm-4.7"  # 코드 분석용 플래그십

# Moonshot AI (Kimi) 모델
# K2 (kimi-k2-0905-preview): 256K context, MoE 1T(32B active), $0.60/$2.50 per 1M USD
#   - enhanced agentic coding, improved frontend code quality, better context understanding
# K2.5 (kimi-k2.5): 256K context, 멀티모달(vision+text), $0.23/$3.00 per 1M USD
#   - thinking/non-thinking 모드, 이미지 분석 가능, Agent Swarm 기술
# 중국어+영어 최적화, 코드 분석/문서 이해에 강점
KIMI_K2_MODEL = "moonshot/kimi-k2-0905-preview"  # K2: 256K, MoE 1T(32B active)
KIMI_K2_5_MODEL = "moonshot/kimi-k2.5"  # K2.5: 256K, 멀티모달, Agent Swarm
KIMI_CHAT_MODEL = KIMI_K2_5_MODEL  # 전체 Activity 기본 — K2.5 업그레이드
KIMI_CODER_MODEL = KIMI_K2_5_MODEL  # 코드 분석 — K2.5 멀티모달 + agentic coding

# OpenAI 모델
# GPT-4.1 mini: 1M context, $0.40/$1.60 per 1M USD — 저컨텍스트 구조화 작업에 최적
# NOTE: pydantic-ai v1.x는 네이티브 OpenAI 모델에 'openai:' (콜론) 식별자를 요구함.
#       'openai/' (슬래시)를 주면 pydantic-ai가 UserError: Unknown model 로 거부하고
#       analyze_jd 가 즉시 실패 → 폴백으로 넘어가게 되어 프로덕션에서 근본 장애 원인이 됨.
GPT_41_MINI_MODEL = "openai:gpt-4.1-mini"

# Legacy alias (backward compatibility)
CODE_ANALYSIS_GLM_MODEL = GLM_CODER_MODEL

ACTIVITY_MODEL_CONFIG: dict[str, str] = {
    # Phase 0: Input Enrichment
    "enrich_input": KIMI_CHAT_MODEL,

    # Phase 1: Planning
    "select_topics": KIMI_CHAT_MODEL,

    # Phase 2: Analysis - Kimi K2.5 (256K context, 멀티모달, 문서/코드 분석 강점)
    "analyze_documents": KIMI_CHAT_MODEL,
    "analyze_code": KIMI_CODER_MODEL,
    "analyze_jd": GPT_41_MINI_MODEL,  # JD 분석: 저컨텍스트 구조화 추출, GPT-4.1 mini 최적

    # Phase 2: HYBRID 3-Stage 코드 분석 (Kimi Coder 모델)
    "code_overview_analysis": KIMI_CODER_MODEL,      # Stage 1: Overview Agent
    "code_deep_analysis": KIMI_CODER_MODEL,          # Stage 2: Deep Analysis (prefix match)
    "code_synthesis_analysis": KIMI_CODER_MODEL,     # Stage 3: Synthesis Agent

    # Phase 3: Question Generation - 전체 Kimi K2.5
    "craft_question": KIMI_CHAT_MODEL,               # 핵심 질문 생성
    "enhance_terminology": KIMI_CHAT_MODEL,           # 용어 설명
    "craft_evaluation_scenarios": KIMI_CHAT_MODEL,    # 평가 시나리오
    "design_follow_ups": KIMI_CHAT_MODEL,             # 후속 질문 설계
    "generate_interviewer_notes": KIMI_CHAT_MODEL,    # 면접관 노트
    "generate_decision_guide": KIMI_CHAT_MODEL,       # 채용 의사결정 가이드
    "revise_questions": KIMI_CHAT_MODEL,              # 질문 수정

    # Legacy activity names (backward compatibility)
    "enhance_question": KIMI_CHAT_MODEL,
    "generate_expected_answer": KIMI_CHAT_MODEL,
    "generate_follow_ups": KIMI_CHAT_MODEL,
    "generate_evaluation_rubric": KIMI_CHAT_MODEL,
    "generate_interviewer_note": KIMI_CHAT_MODEL,
    "generate_terminology": KIMI_CHAT_MODEL,
    "generate_depth_markers": KIMI_CHAT_MODEL,

    # Phase 4: Review & Finalization - 전체 Kimi K2.5
    "quality_review": KIMI_CHAT_MODEL,
    "check_duplicates": KIMI_CHAT_MODEL,              # 중복 체크
    "finalize_candidate_summary": KIMI_CHAT_MODEL,
    "finalize_interviewer_guide": KIMI_CHAT_MODEL,
    "finalize_output": KIMI_CHAT_MODEL,
    "generate_intel_brief": KIMI_CHAT_MODEL,           # v2 Intel Brief 생성
    "generate_deep_analysis": KIMI_CHAT_MODEL,         # v2 Deep Analysis 생성
    "generate_decision_support": KIMI_CHAT_MODEL,      # v2 Decision Support 생성

    # Phase 4: v2 Generation (Intel/Analysis/Decision) - Kimi K2.5
    "radar_analysis": KIMI_CHAT_MODEL,
    "skill_matching": KIMI_CHAT_MODEL,
    "decision_summary": KIMI_CHAT_MODEL,
    "interviewer_tips": KIMI_CHAT_MODEL,
}


# =============================================================================
# 모델별 최대 출력 토큰 수
# =============================================================================
# Kimi K2:   256K context, MoE 1T(32B active) → 16384
# Kimi K2.5: 256K context, 멀티모달, Agent Swarm → 16384
# GPT-4.1 mini: 1M context → 16384
# GLM-4.7:   플래그십 → 8192
# GLM-4.5-flash: 무료, 제한적 → 4096
# GPT-4o:    문서상 max_output_tokens=16384
# Claude:    안정적 출력 → 8192
MODEL_MAX_OUTPUT_TOKENS: dict[str, int] = {
    # Kimi (Moonshot AI)
    "moonshot/": 16384,
    # Z.AI (Zhipu) GLM
    "zai/glm-4.5-flash": 4096,
    "zai/": 8192,
    # OpenAI
    "openai:": 16384,
    "openai/": 16384,
    # Anthropic
    "claude-3-haiku": 4096,       # Haiku 실제 제한
    "anthropic:": 8192,
    "anthropic/": 8192,
    # Gemini
    "gemini:": 8192,
    "gemini/": 8192,
}


def get_max_output_tokens(model: str) -> int:
    """모델별 최적 max_output_tokens 반환 (exact → prefix → global fallback)"""
    # Exact match
    if model in MODEL_MAX_OUTPUT_TOKENS:
        return MODEL_MAX_OUTPUT_TOKENS[model]
    # Prefix match
    for prefix, tokens in MODEL_MAX_OUTPUT_TOKENS.items():
        if model.startswith(prefix):
            return tokens
    return settings.LLM_MAX_OUTPUT_TOKENS


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
    output_type: Any = None,
    system_prompt: str = "",
    model: str | None = None,
):
    """Pydantic AI Agent 생성

    Args:
        output_type: Pydantic 모델 (구조화 출력용, pydantic-ai v1.x)
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
    if output_type:
        kwargs["output_type"] = output_type
    if system_prompt:
        kwargs["system_prompt"] = system_prompt

    return Agent(**kwargs)


def get_llm_model() -> str:
    """현재 설정된 LLM 모델명 반환"""
    return settings.LLM_MODEL
