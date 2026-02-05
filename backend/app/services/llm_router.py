"""
backend/app/services/llm_router.py
LiteLLM Router - Multi-provider Load Balancing & Fallback

Features:
- Primary/Fallback 모델 자동 전환
- Rate Limit 시 자동 cooldown
- 실패한 deployment 일시 제외
- 비용 효율적 라우팅 (무료 Z.AI 모델 활용)
"""
import logging
from typing import Any

from litellm import Router

from app.core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# 모델 배포 목록 (우선순위 및 비용 고려)
# =============================================================================

def _build_model_list() -> list[dict]:
    """환경변수 기반 모델 목록 동적 생성"""
    model_list = []

    # 1. OpenAI GPT-4o (Primary)
    if settings.OPENAI_API_KEY:
        model_list.append({
            "model_name": "gpt-4o",
            "litellm_params": {
                "model": "openai/gpt-4o",
                "api_key": settings.OPENAI_API_KEY,
            },
            "model_info": {
                "id": "openai-gpt4o-primary",
                "description": "Primary model for critical tasks",
            }
        })
        # GPT-4o-mini (저렴한 대안)
        model_list.append({
            "model_name": "gpt-4o-mini",
            "litellm_params": {
                "model": "openai/gpt-4o-mini",
                "api_key": settings.OPENAI_API_KEY,
            },
            "model_info": {
                "id": "openai-gpt4o-mini",
                "description": "Cost-effective OpenAI model",
            }
        })

    # 2. Anthropic Claude (Fallback)
    if settings.ANTHROPIC_API_KEY:
        model_list.append({
            "model_name": "claude-sonnet",
            "litellm_params": {
                "model": "anthropic/claude-3-5-sonnet-20241022",
                "api_key": settings.ANTHROPIC_API_KEY,
            },
            "model_info": {
                "id": "anthropic-claude-sonnet",
                "description": "Fallback for complex reasoning",
            }
        })
        model_list.append({
            "model_name": "claude-haiku",
            "litellm_params": {
                "model": "anthropic/claude-3-5-haiku-20241022",
                "api_key": settings.ANTHROPIC_API_KEY,
            },
            "model_info": {
                "id": "anthropic-claude-haiku",
                "description": "Fast and cheap Anthropic model",
            }
        })

    # 3. Z.AI GLM (비용 효율 - 무료/저렴)
    if settings.ZAI_API_KEY:
        # GLM-4.7 (플래그십, 코드 분석용)
        model_list.append({
            "model_name": "glm-coder",
            "litellm_params": {
                "model": "zai/glm-4.7",
                "api_key": settings.ZAI_API_KEY,
            },
            "model_info": {
                "id": "zai-glm47-coder",
                "description": "Z.AI flagship for code analysis",
            }
        })
        # GLM-4.5-flash (무료!)
        model_list.append({
            "model_name": "glm-free",
            "litellm_params": {
                "model": "zai/glm-4.5-flash",
                "api_key": settings.ZAI_API_KEY,
            },
            "model_info": {
                "id": "zai-glm45-free",
                "description": "Free Z.AI model for simple tasks",
            }
        })

    # 4. DeepSeek (Optional - 저렴)
    if settings.DEEPSEEK_API_KEY:
        model_list.append({
            "model_name": "deepseek",
            "litellm_params": {
                "model": "deepseek/deepseek-chat",
                "api_key": settings.DEEPSEEK_API_KEY,
            },
            "model_info": {
                "id": "deepseek-chat",
                "description": "Cost-effective DeepSeek model",
            }
        })

    return model_list


def _build_fallback_config() -> list[dict]:
    """Fallback 체인 설정"""
    fallbacks = []

    # gpt-4o 실패 시 fallback 체인
    gpt4o_fallbacks = []
    if settings.ZAI_API_KEY:
        gpt4o_fallbacks.append("glm-coder")  # Z.AI 플래그십
    if settings.ANTHROPIC_API_KEY:
        gpt4o_fallbacks.append("claude-sonnet")
    if settings.ZAI_API_KEY:
        gpt4o_fallbacks.append("glm-free")  # 최종 무료 fallback

    if gpt4o_fallbacks:
        fallbacks.append({"gpt-4o": gpt4o_fallbacks})

    # claude-sonnet 실패 시 fallback
    claude_fallbacks = []
    if settings.ZAI_API_KEY:
        claude_fallbacks.append("glm-coder")
        claude_fallbacks.append("glm-free")
    if claude_fallbacks:
        fallbacks.append({"claude-sonnet": claude_fallbacks})

    # glm-coder 실패 시 무료 모델로
    if settings.ZAI_API_KEY:
        fallbacks.append({"glm-coder": ["glm-free"]})

    return fallbacks


# =============================================================================
# Router 인스턴스 (Lazy Initialization)
# =============================================================================

_router: Router | None = None


def get_router() -> Router:
    """LiteLLM Router 싱글톤 인스턴스"""
    global _router

    if _router is None:
        model_list = _build_model_list()

        if not model_list:
            raise RuntimeError(
                "No LLM API keys configured. "
                "Set at least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, ZAI_API_KEY"
            )

        fallbacks = _build_fallback_config()

        logger.info(
            f"Initializing LiteLLM Router with {len(model_list)} models, "
            f"{len(fallbacks)} fallback rules"
        )

        _router = Router(
            model_list=model_list,
            fallbacks=fallbacks,

            # 재시도 설정
            num_retries=3,              # 각 모델에서 3회 재시도
            retry_after=60,             # Rate limit 시 60초 대기

            # Cooldown 설정
            allowed_fails=2,            # 2회 실패 시 cooldown
            cooldown_time=120,          # 120초 동안 해당 deployment 제외

            # 라우팅 전략
            routing_strategy="simple-shuffle",

            # 타임아웃
            timeout=120,

            # 디버깅
            set_verbose=settings.LOG_LEVEL == "DEBUG",
        )

        logger.info("LiteLLM Router initialized successfully")

    return _router


async def router_completion(
    model: str,
    messages: list[dict],
    **kwargs: Any,
) -> Any:
    """Router를 통한 LLM completion 호출

    Args:
        model: 모델 이름 (router에 등록된 model_name)
        messages: 대화 메시지 리스트
        **kwargs: 추가 LiteLLM 파라미터

    Returns:
        LiteLLM completion response
    """
    router = get_router()

    try:
        response = await router.acompletion(
            model=model,
            messages=messages,
            **kwargs,
        )
        return response
    except Exception as e:
        logger.error(f"Router completion failed: {type(e).__name__}: {e}")
        raise


def get_available_models() -> list[str]:
    """사용 가능한 모델 이름 목록"""
    router = get_router()
    return list(set(m["model_name"] for m in router.model_list))


def get_model_info() -> dict:
    """모델 정보 조회 (디버깅용)"""
    router = get_router()
    return {
        "models": [
            {
                "name": m["model_name"],
                "id": m.get("model_info", {}).get("id"),
                "description": m.get("model_info", {}).get("description"),
            }
            for m in router.model_list
        ],
        "fallbacks": router.fallbacks,
        "routing_strategy": router.routing_strategy,
    }
