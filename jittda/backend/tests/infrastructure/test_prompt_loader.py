"""
PromptLoader 테스트 — Langfuse 런타임 프롬프트 로딩 + YAML fallback.

외부 서비스(Langfuse)는 모두 mock 처리. 실제 API 호출 없음.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# langfuse import 문제 우회 (Python 3.14 + pydantic v1 호환 문제)
# infrastructure.llm.__init__.py가 langfuse_client를 import할 때
# langfuse가 pydantic v1에서 폭발하므로, langfuse 모듈 트리를 사전 등록한다.
# ---------------------------------------------------------------------------
_langfuse_modules = [
    "langfuse",
    "langfuse.api",
    "langfuse.api.core",
    "langfuse.api.core.pydantic_utilities",
    "langfuse.api.resources",
    "langfuse.api.resources.annotation_queues",
    "langfuse.api.resources.annotation_queues.types",
    "langfuse.api.resources.commons",
    "langfuse.api.resources.commons.types",
    "langfuse.batch_evaluation",
    "langfuse.decorators",
]
for _mod_name in _langfuse_modules:
    if _mod_name not in sys.modules:
        _m = ModuleType(_mod_name)
        # langfuse 최상위에 Langfuse 클래스 더미 등록
        if _mod_name == "langfuse":
            _m.Langfuse = MagicMock  # type: ignore[attr-defined]
        sys.modules[_mod_name] = _m

from infrastructure.llm.prompt_loader import (  # noqa: E402
    PromptLoader,
    get_prompt_loader,
    _mustache_to_python_format,
    _PROMPTS_DIR,
)


# ---------------------------------------------------------------------------
# _mustache_to_python_format
# ---------------------------------------------------------------------------


class TestMustacheToPythonFormat:
    def test_single_variable(self):
        assert _mustache_to_python_format("Hello {{name}}!") == "Hello {name}!"

    def test_multiple_variables(self):
        result = _mustache_to_python_format("{{a}} and {{b}}")
        assert result == "{a} and {b}"

    def test_no_variables(self):
        text = "No variables here."
        assert _mustache_to_python_format(text) == text

    def test_preserves_non_mustache_braces(self):
        # JSON-like content with single braces should not be affected
        text = "data = {key: value}"
        assert _mustache_to_python_format(text) == text

    def test_underscored_variable_names(self):
        result = _mustache_to_python_format("{{profile_context}}")
        assert result == "{profile_context}"


# ---------------------------------------------------------------------------
# PromptLoader.__init__ / _init_langfuse
# ---------------------------------------------------------------------------


class TestPromptLoaderInit:
    @patch.dict("os.environ", {
        "LANGFUSE_PUBLIC_KEY": "pk-test",
        "LANGFUSE_SECRET_KEY": "sk-test",
    })
    def test_init_with_langfuse_keys(self):
        """환경변수 설정 시 Langfuse 클라이언트가 초기화된다."""
        with patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", Path("/nonexistent")):
            loader = PromptLoader()

        # sys.modules에 등록된 mock Langfuse가 MagicMock이므로
        # _init_langfuse()에서 Langfuse() 호출이 성공하여 _langfuse가 설정됨
        assert loader.has_langfuse is True

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_langfuse_keys(self):
        """환경변수 미설정 시 Langfuse 없이 graceful 시작."""
        with patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", Path("/nonexistent")):
            loader = PromptLoader()

        assert loader.has_langfuse is False

    @patch.dict("os.environ", {
        "LANGFUSE_PUBLIC_KEY": "pk-test",
        "LANGFUSE_SECRET_KEY": "sk-test",
    })
    def test_init_langfuse_constructor_error(self):
        """Langfuse 생성자 실패 시 graceful fallback."""
        mock_langfuse_cls = MagicMock(side_effect=RuntimeError("connection refused"))

        with (
            patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", Path("/nonexistent")),
            patch.dict(sys.modules, {"langfuse": _make_langfuse_module(mock_langfuse_cls)}),
        ):
            loader = PromptLoader()

        assert loader.has_langfuse is False

    @patch.dict("os.environ", {
        "LANGFUSE_PUBLIC_KEY": "pk-test",
        "LANGFUSE_SECRET_KEY": "sk-test",
        "LANGFUSE_HOST": "https://my-langfuse.example.com",
    })
    def test_init_uses_custom_host(self):
        """LANGFUSE_HOST 환경변수가 커스텀 호스트를 설정한다."""
        mock_langfuse_cls = MagicMock()

        with (
            patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", Path("/nonexistent")),
            patch.dict(sys.modules, {"langfuse": _make_langfuse_module(mock_langfuse_cls)}),
        ):
            loader = PromptLoader()

        mock_langfuse_cls.assert_called_once_with(
            public_key="pk-test",
            secret_key="sk-test",
            host="https://my-langfuse.example.com",
        )
        assert loader.has_langfuse is True


# ---------------------------------------------------------------------------
# PromptLoader._load_yaml_fallbacks
# ---------------------------------------------------------------------------


class TestPromptLoaderYAMLLoading:
    def test_loads_yaml_files_from_prompts_dir(self, tmp_path):
        """prompts/ 디렉토리의 YAML 파일이 fallback으로 로드된다."""
        yaml_file = tmp_path / "test_prompt.yaml"
        yaml_file.write_text(
            "name: my_test_prompt\nversion: 1\nprompt: |\n  Hello {{name}}!\n"
        )

        with (
            patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", tmp_path),
            patch.dict("os.environ", {}, clear=True),
        ):
            loader = PromptLoader()

        assert "my_test_prompt" in loader.fallback_names

    def test_skips_yaml_without_name(self, tmp_path):
        """name 필드 없는 YAML 파일은 건너뛴다."""
        good = tmp_path / "good.yaml"
        good.write_text("name: good_prompt\nprompt: Hello!\n")

        bad = tmp_path / "bad.yaml"
        bad.write_text("not_a_name: oops\nprompt: Bye!\n")

        with (
            patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", tmp_path),
            patch.dict("os.environ", {}, clear=True),
        ):
            loader = PromptLoader()

        assert "good_prompt" in loader.fallback_names
        assert len([n for n in loader.fallback_names if "bad" in n or "oops" in n]) == 0

    def test_skips_yaml_without_prompt(self, tmp_path):
        """prompt 필드 없는 YAML 파일은 건너뛴다."""
        bad = tmp_path / "no_prompt.yaml"
        bad.write_text("name: no_prompt_field\nversion: 1\n")

        with (
            patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", tmp_path),
            patch.dict("os.environ", {}, clear=True),
        ):
            loader = PromptLoader()

        assert "no_prompt_field" not in loader.fallback_names

    def test_handles_missing_prompts_dir(self):
        """prompts/ 디렉토리가 없어도 에러 없이 동작."""
        with (
            patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", Path("/nonexistent")),
            patch.dict("os.environ", {}, clear=True),
        ):
            loader = PromptLoader()

        assert loader.fallback_names == []

    def test_loads_real_prompts_directory(self):
        """실제 prompts/ 디렉토리에서 YAML 파일 로드 확인."""
        if not _PROMPTS_DIR.exists():
            pytest.skip("prompts/ directory not available")

        with patch.dict("os.environ", {}, clear=True):
            loader = PromptLoader()

        # 최소 1개 이상의 프롬프트가 로드되어야 함
        assert len(loader.fallback_names) > 0
        # 알려진 프롬프트 이름 확인
        assert "question_code_evolution_v5" in loader.fallback_names
        assert "question_quality_gate_v5" in loader.fallback_names
        assert "question_negative_selection_v5" in loader.fallback_names

    def test_loads_multiple_yaml_files(self, tmp_path):
        """여러 YAML 파일이 모두 로드된다."""
        for i in range(5):
            f = tmp_path / f"prompt_{i}.yaml"
            f.write_text(f"name: prompt_{i}\nprompt: Content {i}\n")

        with (
            patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", tmp_path),
            patch.dict("os.environ", {}, clear=True),
        ):
            loader = PromptLoader()

        assert len(loader.fallback_names) == 5
        for i in range(5):
            assert f"prompt_{i}" in loader.fallback_names


# ---------------------------------------------------------------------------
# PromptLoader.get_prompt
# ---------------------------------------------------------------------------


def _make_loader_no_langfuse(fallbacks: dict[str, str] | None = None) -> PromptLoader:
    """Langfuse 없는 PromptLoader 생성 (fallback만 사용)."""
    with (
        patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", Path("/nonexistent")),
        patch.dict("os.environ", {}, clear=True),
    ):
        loader = PromptLoader()

    if fallbacks:
        for name, template in fallbacks.items():
            loader.register_fallback(name, template)

    return loader


class TestPromptLoaderGetPrompt:
    def test_get_prompt_langfuse_success(self):
        """Langfuse에서 프롬프트를 성공적으로 가져온다."""
        mock_langfuse = MagicMock()
        mock_prompt = MagicMock()
        mock_prompt.compile.return_value = "Compiled prompt for Alice"
        mock_langfuse.get_prompt.return_value = mock_prompt

        loader = _make_loader_no_langfuse()
        loader._langfuse = mock_langfuse

        result = loader.get_prompt("greeting", name="Alice")

        mock_langfuse.get_prompt.assert_called_once_with("greeting")
        mock_prompt.compile.assert_called_once_with(name="Alice")
        assert result == "Compiled prompt for Alice"

    def test_get_prompt_langfuse_fails_uses_fallback(self):
        """Langfuse 실패 시 fallback 프롬프트를 사용한다."""
        mock_langfuse = MagicMock()
        mock_langfuse.get_prompt.side_effect = ConnectionError("server down")

        loader = _make_loader_no_langfuse(
            fallbacks={"greeting": "Hello {{name}}!"}
        )
        loader._langfuse = mock_langfuse

        result = loader.get_prompt("greeting", name="Bob")

        assert result == "Hello Bob!"

    def test_get_prompt_langfuse_compile_fails_uses_fallback(self):
        """Langfuse compile 실패 시 fallback 사용."""
        mock_langfuse = MagicMock()
        mock_prompt = MagicMock()
        mock_prompt.compile.side_effect = ValueError("missing variable")
        mock_langfuse.get_prompt.return_value = mock_prompt

        loader = _make_loader_no_langfuse(
            fallbacks={"greeting": "Fallback: {{name}}"}
        )
        loader._langfuse = mock_langfuse

        result = loader.get_prompt("greeting", name="Charlie")

        assert result == "Fallback: Charlie"

    def test_get_prompt_fallback_with_variables(self):
        """Fallback 프롬프트의 Mustache 변수가 올바르게 치환된다."""
        loader = _make_loader_no_langfuse(
            fallbacks={"analysis": "Profile: {{profile_context}}\nCode: {{code_context}}"}
        )

        result = loader.get_prompt(
            "analysis",
            profile_context="Senior Dev",
            code_context="clean architecture",
        )

        assert result == "Profile: Senior Dev\nCode: clean architecture"

    def test_get_prompt_fallback_without_variables(self):
        """변수 없이 fallback 프롬프트를 가져온다."""
        loader = _make_loader_no_langfuse(
            fallbacks={"simple": "Just a static prompt."}
        )

        result = loader.get_prompt("simple")

        assert result == "Just a static prompt."

    def test_get_prompt_no_fallback_returns_empty(self):
        """Langfuse도 fallback도 없으면 빈 문자열 반환."""
        loader = _make_loader_no_langfuse()

        result = loader.get_prompt("nonexistent_prompt")

        assert result == ""

    def test_get_prompt_fallback_missing_variable(self):
        """Fallback 프롬프트에 변수가 부족하면 원본 템플릿 반환."""
        loader = _make_loader_no_langfuse(
            fallbacks={"partial": "Hello {{name}} from {{city}}!"}
        )

        # name만 제공, city 누락
        result = loader.get_prompt("partial", name="Alice")

        # KeyError 시 원본 템플릿 반환
        assert result == "Hello {{name}} from {{city}}!"

    def test_get_prompt_langfuse_none_skips_to_fallback(self):
        """Langfuse가 None이면 바로 fallback으로 간다."""
        loader = _make_loader_no_langfuse(
            fallbacks={"my_prompt": "Fallback content"}
        )
        assert loader._langfuse is None

        result = loader.get_prompt("my_prompt")

        assert result == "Fallback content"


# ---------------------------------------------------------------------------
# PromptLoader.register_fallback
# ---------------------------------------------------------------------------


class TestPromptLoaderRegisterFallback:
    def test_register_and_retrieve(self):
        """register_fallback으로 등록한 프롬프트를 get_prompt로 가져온다."""
        loader = _make_loader_no_langfuse()

        loader.register_fallback("custom", "Custom prompt: {{topic}}")
        result = loader.get_prompt("custom", topic="testing")

        assert result == "Custom prompt: testing"

    def test_register_overrides_existing(self):
        """동일 이름으로 재등록하면 기존 값을 덮어쓴다."""
        loader = _make_loader_no_langfuse()

        loader.register_fallback("prompt_a", "Version 1")
        loader.register_fallback("prompt_a", "Version 2")

        result = loader.get_prompt("prompt_a")

        assert result == "Version 2"

    def test_register_overrides_yaml_loaded(self, tmp_path):
        """수동 등록이 YAML에서 로드된 프롬프트를 덮어쓴다."""
        yaml_file = tmp_path / "override_test.yaml"
        yaml_file.write_text("name: overridable\nprompt: Original from YAML\n")

        with (
            patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", tmp_path),
            patch.dict("os.environ", {}, clear=True),
        ):
            loader = PromptLoader()

        assert loader.get_prompt("overridable") == "Original from YAML"

        loader.register_fallback("overridable", "Overridden by code")
        assert loader.get_prompt("overridable") == "Overridden by code"


# ---------------------------------------------------------------------------
# get_prompt_loader (싱글톤)
# ---------------------------------------------------------------------------


class TestGetPromptLoaderSingleton:
    def test_returns_same_instance(self):
        """get_prompt_loader()는 항상 동일 인스턴스를 반환한다."""
        get_prompt_loader.cache_clear()

        with (
            patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", Path("/nonexistent")),
            patch.dict("os.environ", {}, clear=True),
        ):
            loader1 = get_prompt_loader()
            loader2 = get_prompt_loader()

        assert loader1 is loader2

        # 테스트 후 캐시 정리 (다른 테스트에 영향 방지)
        get_prompt_loader.cache_clear()

    def test_returns_prompt_loader_instance(self):
        """get_prompt_loader()가 PromptLoader 인스턴스를 반환한다."""
        get_prompt_loader.cache_clear()

        with (
            patch("infrastructure.llm.prompt_loader._PROMPTS_DIR", Path("/nonexistent")),
            patch.dict("os.environ", {}, clear=True),
        ):
            loader = get_prompt_loader()

        assert isinstance(loader, PromptLoader)

        get_prompt_loader.cache_clear()


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------


class TestPromptLoaderProperties:
    def test_fallback_names_sorted(self):
        """fallback_names는 정렬된 리스트를 반환한다."""
        loader = _make_loader_no_langfuse()

        loader.register_fallback("z_prompt", "Z")
        loader.register_fallback("a_prompt", "A")
        loader.register_fallback("m_prompt", "M")

        assert loader.fallback_names == ["a_prompt", "m_prompt", "z_prompt"]

    def test_has_langfuse_false_without_keys(self):
        """환경변수 미설정 시 has_langfuse는 False."""
        loader = _make_loader_no_langfuse()
        assert loader.has_langfuse is False

    def test_has_langfuse_true_with_mock(self):
        """Langfuse 인스턴스가 있으면 has_langfuse는 True."""
        loader = _make_loader_no_langfuse()
        loader._langfuse = MagicMock()
        assert loader.has_langfuse is True


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _make_langfuse_module(langfuse_cls: MagicMock) -> ModuleType:
    """커스텀 Langfuse 클래스를 가진 mock 모듈 생성."""
    mod = ModuleType("langfuse")
    mod.Langfuse = langfuse_cls  # type: ignore[attr-defined]
    return mod
