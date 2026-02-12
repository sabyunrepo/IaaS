"""
backend/app/prompts/__init__.py
YAML 프롬프트 템플릿 로더 + Langfuse 프롬프트 관리 통합

Langfuse Prompt Management Features:
- 프롬프트 텍스트: Langfuse UI에서 버전 관리
- 모델 설정: prompt.config에서 model, temperature 등 관리
- Fallback: Langfuse 실패 시 로컬 YAML + llm_config.py 사용

Template Syntax (Mustache-style):
- {{variable}} = 변수 플레이스홀더
- { } = 리터럴 중괄호 (JSON 등)
"""
import logging
import os
import re
from functools import lru_cache
from typing import Any
from dataclasses import dataclass

import yaml

logger = logging.getLogger(__name__)
PROMPTS_DIR = os.path.dirname(__file__)


def mustache_format(template: str, **kwargs) -> str:
    """Mustache 스타일 변수 치환 ({{variable}} → value).

    Langfuse와 동일한 문법을 사용하여 YAML fallback에서도 일관성 유지.
    """
    result = template
    for key, value in kwargs.items():
        # {{key}} 패턴을 value로 치환
        pattern = r'\{\{' + re.escape(key) + r'\}\}'
        result = re.sub(pattern, str(value), result)
    return result

# Cache for Langfuse prompts (name -> prompt object)
_langfuse_prompt_cache: dict[str, Any] = {}


@dataclass
class PromptWithConfig:
    """프롬프트 텍스트와 모델 설정을 함께 담는 데이터 클래스"""
    prompt: str
    source: str  # "langfuse" or "yaml"
    name: str
    version: str | None = None
    model: str | None = None
    temperature: float | None = None
    config: dict | None = None  # Full config from Langfuse

    @property
    def max_output_tokens(self) -> int | None:
        """Langfuse config에서 max_output_tokens 추출"""
        if self.config:
            return self.config.get("max_output_tokens")
        return None


@lru_cache(maxsize=32)
def _load_yaml(filename: str) -> dict:
    """Load YAML file from local prompts directory."""
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _get_langfuse_prompt_name(filename: str, key: str) -> str:
    """Generate Langfuse prompt name from filename and key.

    Convention: filename without .yaml + underscore + key
    Example: jd_analysis.yaml + analyze → jd_analysis_analyze
    """
    base = filename.replace(".yaml", "")
    return f"{base}_{key}"


def _fetch_langfuse_prompt(prompt_name: str, **kwargs) -> str | None:
    """Try to fetch and compile a prompt from Langfuse.

    Args:
        prompt_name: Langfuse prompt name (e.g., "jd_analysis_analyze")
        **kwargs: Variables to compile into the prompt

    Returns:
        Compiled prompt string if successful, None otherwise
    """
    from app.core.observability import is_langfuse_enabled, get_langfuse_client

    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        # Check cache first
        if prompt_name not in _langfuse_prompt_cache:
            # Fetch prompt from Langfuse
            prompt = client.get_prompt(prompt_name)
            _langfuse_prompt_cache[prompt_name] = prompt
            logger.debug(f"Fetched Langfuse prompt: {prompt_name} v{prompt.version}")

        prompt = _langfuse_prompt_cache[prompt_name]

        # Compile prompt with variables
        compiled = prompt.compile(**kwargs)

        # Log prompt usage for observability
        _log_prompt_usage(prompt_name, prompt.version, "langfuse", kwargs.keys())

        return compiled

    except Exception as e:
        logger.debug(f"Langfuse prompt fetch failed for {prompt_name}: {e}")
        return None


def _log_prompt_usage(
    prompt_name: str,
    version: str | int | None,
    source: str,
    variable_names: list[str] | None = None,
):
    """Log prompt usage to Langfuse for tracking."""
    from app.core.observability import is_langfuse_enabled, log_event

    if not is_langfuse_enabled():
        return

    log_event(
        name="prompt_usage",
        metadata={
            "prompt_name": prompt_name,
            "prompt_version": str(version) if version else "local",
            "source": source,  # "langfuse" or "yaml"
            "variables": list(variable_names) if variable_names else [],
        },
    )


def get_prompt(filename: str, key: str, **kwargs) -> str:
    """프롬프트 템플릿을 로드하고 변수를 치환합니다.

    Langfuse에서 먼저 프롬프트를 가져오고, 실패하면 로컬 YAML에서 로드합니다.

    Args:
        filename: YAML 파일명 (예: "jd_analysis.yaml")
        key: 프롬프트 키 (예: "analyze")
        **kwargs: 템플릿 변수

    Returns:
        Compiled prompt string
    """
    # Try Langfuse first
    langfuse_name = _get_langfuse_prompt_name(filename, key)
    prompt = _fetch_langfuse_prompt(langfuse_name, **kwargs)

    if prompt is not None:
        return prompt

    # Fallback to local YAML
    data = _load_yaml(filename)
    template = data["prompts"][key]["template"]
    result = mustache_format(template, **kwargs)

    # Log YAML fallback usage
    _log_prompt_usage(langfuse_name, None, "yaml", kwargs.keys())

    return result


def get_prompt_with_metadata(filename: str, key: str, **kwargs) -> dict:
    """프롬프트와 메타데이터를 함께 반환합니다.

    Args:
        filename: YAML 파일명
        key: 프롬프트 키
        **kwargs: 템플릿 변수

    Returns:
        {
            "prompt": str,
            "source": "langfuse" | "yaml",
            "version": str | None,
            "name": str
        }
    """
    from app.core.observability import is_langfuse_enabled, get_langfuse_client

    langfuse_name = _get_langfuse_prompt_name(filename, key)

    # Try Langfuse
    if is_langfuse_enabled():
        try:
            client = get_langfuse_client()
            if client:
                if langfuse_name not in _langfuse_prompt_cache:
                    prompt_obj = client.get_prompt(langfuse_name)
                    _langfuse_prompt_cache[langfuse_name] = prompt_obj

                prompt_obj = _langfuse_prompt_cache[langfuse_name]
                compiled = prompt_obj.compile(**kwargs)

                _log_prompt_usage(langfuse_name, prompt_obj.version, "langfuse", kwargs.keys())

                return {
                    "prompt": compiled,
                    "source": "langfuse",
                    "version": str(prompt_obj.version),
                    "name": langfuse_name,
                }
        except Exception as e:
            logger.debug(f"Langfuse prompt not available: {e}")

    # Fallback to YAML
    data = _load_yaml(filename)
    template = data["prompts"][key]["template"]
    result = mustache_format(template, **kwargs)

    _log_prompt_usage(langfuse_name, None, "yaml", kwargs.keys())

    return {
        "prompt": result,
        "source": "yaml",
        "version": None,
        "name": langfuse_name,
    }


def get_prompt_with_config(filename: str, key: str, **kwargs) -> PromptWithConfig:
    """프롬프트와 모델 설정을 함께 반환합니다.

    Langfuse에서 프롬프트를 가져오면 config에서 model, temperature 등을 추출합니다.
    Langfuse 사용 불가 시 로컬 YAML과 llm_config.py 설정을 사용합니다.

    Args:
        filename: YAML 파일명 (예: "jd_analysis.yaml")
        key: 프롬프트 키 (예: "analyze")
        **kwargs: 템플릿 변수

    Returns:
        PromptWithConfig: 프롬프트 텍스트와 모델 설정
    """
    from app.core.observability import is_langfuse_enabled, get_langfuse_client

    langfuse_name = _get_langfuse_prompt_name(filename, key)

    # Try Langfuse first
    if is_langfuse_enabled():
        try:
            client = get_langfuse_client()
            if client:
                if langfuse_name not in _langfuse_prompt_cache:
                    prompt_obj = client.get_prompt(langfuse_name)
                    _langfuse_prompt_cache[langfuse_name] = prompt_obj
                    logger.info(f"Fetched Langfuse prompt: {langfuse_name} v{prompt_obj.version}")

                prompt_obj = _langfuse_prompt_cache[langfuse_name]
                compiled = prompt_obj.compile(**kwargs)

                # Extract model config from Langfuse prompt
                config = prompt_obj.config or {}
                model = config.get("model")
                temperature = config.get("temperature")

                _log_prompt_usage(langfuse_name, prompt_obj.version, "langfuse", kwargs.keys())

                return PromptWithConfig(
                    prompt=compiled,
                    source="langfuse",
                    name=langfuse_name,
                    version=str(prompt_obj.version),
                    model=model,
                    temperature=temperature,
                    config=config,
                )
        except Exception as e:
            logger.debug(f"Langfuse prompt not available: {e}")

    # Fallback to YAML + llm_config.py
    data = _load_yaml(filename)
    template = data["prompts"][key]["template"]
    result = mustache_format(template, **kwargs)

    # Get model from llm_config.py based on activity name
    from app.services.llm_config import get_model_for_activity
    activity_name = _prompt_key_to_activity_name(filename, key)
    fallback_model = get_model_for_activity(activity_name)

    _log_prompt_usage(langfuse_name, None, "yaml", kwargs.keys())

    return PromptWithConfig(
        prompt=result,
        source="yaml",
        name=langfuse_name,
        version=None,
        model=fallback_model,
        temperature=None,
        config=None,
    )


def _prompt_key_to_activity_name(filename: str, key: str) -> str:
    """YAML 파일명과 키를 activity 이름으로 변환.

    매핑 규칙:
    - question_generation.yaml + select_topics → select_topics
    - question_generation.yaml + craft_question → craft_question
    - document_analysis.yaml + extract_profile → analyze_documents
    - jd_analysis.yaml + analyze → analyze_jd
    - quality_review.yaml + review → quality_review
    - finalization.yaml + candidate_summary → finalize_candidate_summary
    """
    # 특수 매핑
    special_mappings = {
        ("document_analysis.yaml", "extract_profile"): "analyze_documents",
        ("jd_analysis.yaml", "analyze"): "analyze_jd",
        ("jd_analysis.yaml", "translate"): "analyze_jd",
        ("quality_review.yaml", "review"): "quality_review",
        ("quality_review.yaml", "check_duplicates"): "check_duplicates",
        ("finalization.yaml", "candidate_summary"): "finalize_candidate_summary",
        ("finalization.yaml", "interviewer_guide"): "finalize_interviewer_guide",
        ("finalization.yaml", "final_synthesis"): "finalize_output",
        ("finalization.yaml", "generate_intel_brief"): "generate_intel_brief",
        ("finalization.yaml", "generate_deep_analysis"): "generate_deep_analysis",
        ("finalization.yaml", "generate_decision_support"): "generate_decision_support",
        ("v2_generation.yaml", "radar_analysis"): "radar_analysis",
        ("v2_generation.yaml", "decision_summary"): "decision_summary",
        ("v2_generation.yaml", "interviewer_tips"): "interviewer_tips",
        ("linkedin_summary.yaml", "recommendations_summary"): "profile_builder",
        ("linkedin_summary.yaml", "volunteer_summary"): "profile_builder",
    }

    mapping_key = (filename, key)
    if mapping_key in special_mappings:
        return special_mappings[mapping_key]

    # 기본: 키 자체가 activity 이름
    return key


def clear_langfuse_prompt_cache():
    """Langfuse 프롬프트 캐시만 초기화 (스크립트/테스트용).

    프롬프트 재업로드 후 워커가 새 버전을 가져오도록 할 때 사용.
    YAML 캐시는 유지됩니다.
    """
    _langfuse_prompt_cache.clear()
    logger.info("Langfuse prompt cache cleared")


def clear_prompt_cache():
    """Clear the Langfuse prompt cache and YAML cache (useful for testing or hot-reload)."""
    _langfuse_prompt_cache.clear()
    _load_yaml.cache_clear()
    logger.info("Prompt cache cleared")


def list_local_prompts() -> dict[str, list[str]]:
    """List all available prompts from local YAML files.

    Returns:
        {filename: [prompt_keys]}
    """
    result = {}
    for filename in os.listdir(PROMPTS_DIR):
        if filename.endswith(".yaml"):
            try:
                data = _load_yaml(filename)
                result[filename] = list(data.get("prompts", {}).keys())
            except Exception:
                pass
    return result
