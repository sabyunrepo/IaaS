"""Langfuse 런타임 프롬프트 로더.

Langfuse 서버에서 프롬프트를 런타임에 로딩.
서버 미연결 시 로컬 YAML fallback 사용.

Architecture:
    1. Langfuse (환경변수 설정 시) -> 런타임 프롬프트 관리
    2. YAML fallback (src/infrastructure/llm/prompts/) -> 로컬 백업
    3. 수동 register_fallback() -> 코드에서 직접 등록

DDD: infrastructure 레이어 — 외부 서비스(Langfuse) 어댑터.
"""
from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 프롬프트 YAML 디렉토리 (이 파일 기준 상대 경로)
_PROMPTS_DIR = Path(__file__).parent / "prompts"


def _mustache_to_python_format(template: str) -> str:
    """Mustache 스타일 {{var}} 를 Python str.format 스타일 {var} 로 변환.

    Langfuse/YAML 프롬프트는 {{variable}} 구문을 사용하지만,
    Python fallback에서는 str.format()을 사용하므로 변환이 필요하다.
    """
    return re.sub(r"\{\{(\w+)\}\}", r"{\1}", template)


def _load_yaml_file(path: Path) -> dict[str, Any] | None:
    """단일 YAML 파일을 로드. yaml 미설치 시 None 반환."""
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not installed, cannot load fallback prompts from YAML")
        return None

    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning("Failed to load YAML prompt %s: %s", path, e)
        return None


class PromptLoader:
    """Langfuse-first, YAML-fallback 프롬프트 로더.

    사용법::

        loader = get_prompt_loader()

        # Langfuse에서 프롬프트 로딩 (실패 시 YAML fallback)
        prompt = loader.get_prompt(
            "question_code_evolution_v5",
            profile_context="...",
            code_context="...",
            evolution_context="...",
        )

        # 수동 fallback 등록
        loader.register_fallback("custom_prompt", "Hello {{name}}!")
    """

    def __init__(self) -> None:
        self._langfuse: Any = None
        self._fallback_prompts: dict[str, str] = {}
        self._init_langfuse()
        self._load_yaml_fallbacks()

    def _init_langfuse(self) -> None:
        """Langfuse 클라이언트 초기화. 실패 시 None 유지."""
        try:
            from langfuse import Langfuse

            public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
            secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
            host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

            if public_key and secret_key:
                self._langfuse = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host,
                )
                logger.info("Langfuse client initialized (host=%s)", host)
            else:
                logger.warning(
                    "Langfuse keys not set (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY), "
                    "using fallback prompts"
                )
        except ImportError:
            logger.warning("langfuse package not available, using fallback prompts")
        except Exception as e:
            logger.warning("Langfuse init failed: %s, using fallback prompts", e)

    def _load_yaml_fallbacks(self) -> None:
        """prompts/ 디렉토리에서 YAML 파일을 로드하여 fallback 등록."""
        if not _PROMPTS_DIR.exists():
            logger.info("Prompts directory not found: %s", _PROMPTS_DIR)
            return

        loaded = 0
        for yaml_path in sorted(_PROMPTS_DIR.glob("*.yaml")):
            data = _load_yaml_file(yaml_path)
            if data and "name" in data and "prompt" in data:
                self._fallback_prompts[data["name"]] = data["prompt"]
                loaded += 1

        if loaded:
            logger.info("Loaded %d YAML fallback prompts from %s", loaded, _PROMPTS_DIR)

    def get_prompt(self, prompt_name: str, **kwargs: Any) -> str:
        """프롬프트를 Langfuse에서 가져오고, 실패 시 YAML fallback 사용.

        Args:
            prompt_name: 프롬프트 이름 (Langfuse 프롬프트명 또는 YAML의 name 필드).
            **kwargs: 프롬프트 템플릿 변수 (예: profile_context="...", name="...").

        Returns:
            컴파일된 프롬프트 문자열. 둘 다 실패 시 빈 문자열.
        """
        # 1. Langfuse에서 시도
        if self._langfuse is not None:
            try:
                prompt = self._langfuse.get_prompt(prompt_name)
                compiled = prompt.compile(**kwargs)
                return compiled
            except Exception as e:
                logger.warning("Langfuse prompt '%s' fetch failed: %s", prompt_name, e)

        # 2. Fallback 사용
        template = self._fallback_prompts.get(prompt_name)
        if template is None:
            logger.error("No fallback prompt found for '%s'", prompt_name)
            return ""

        if not kwargs:
            return template

        try:
            python_template = _mustache_to_python_format(template)
            return python_template.format(**kwargs)
        except KeyError as e:
            logger.warning(
                "Fallback prompt '%s' missing variable %s, returning raw template",
                prompt_name,
                e,
            )
            return template

    def register_fallback(self, name: str, template: str) -> None:
        """로컬 fallback 프롬프트를 수동 등록 (또는 덮어쓰기).

        Args:
            name: 프롬프트 이름.
            template: 프롬프트 템플릿 (Mustache {{var}} 또는 Python {var} 구문).
        """
        self._fallback_prompts[name] = template

    @property
    def fallback_names(self) -> list[str]:
        """등록된 fallback 프롬프트 이름 목록."""
        return sorted(self._fallback_prompts.keys())

    @property
    def has_langfuse(self) -> bool:
        """Langfuse 클라이언트가 활성화되어 있는지 여부."""
        return self._langfuse is not None


@lru_cache(maxsize=1)
def get_prompt_loader() -> PromptLoader:
    """싱글톤 PromptLoader 인스턴스를 반환한다.

    Returns:
        PromptLoader 인스턴스 (프로세스당 하나).
    """
    return PromptLoader()
