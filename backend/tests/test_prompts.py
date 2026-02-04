"""Unit tests for prompt template loader and Langfuse integration."""
import pytest
from app.prompts import get_prompt, _load_yaml


class TestPromptLoader:
    def test_load_jd_analysis(self):
        prompt = get_prompt("jd_analysis.yaml", "analyze", jd_text="Test JD text")
        assert "job_title" in prompt
        assert "Test JD text" in prompt

    def test_load_document_analysis(self):
        prompt = get_prompt("document_analysis.yaml", "extract_profile", documents="Resume content here")
        assert "Resume content here" in prompt
        assert "structured candidate profile" in prompt.lower() or "candidate profile" in prompt.lower()

    def test_load_select_topics(self):
        prompt = get_prompt(
            "question_generation.yaml", "select_topics",
            max_questions=25, experience_level="시니어", candidates="1. React",
        )
        assert "25" in prompt
        assert "시니어" in prompt

    def test_load_craft_question(self):
        prompt = get_prompt(
            "question_generation.yaml", "craft_question",
            output_language="ko", experience_level="주니어",
            topic="React hooks", category="technical_depth", difficulty="Medium",
        )
        assert "React hooks" in prompt
        assert "ko" in prompt

    def test_load_quality_review(self):
        prompt = get_prompt("quality_review.yaml", "review", questions="1. What is X?")
        assert "quality" in prompt
        assert "What is X?" in prompt

    def test_load_candidate_summary(self):
        prompt = get_prompt(
            "finalization.yaml", "candidate_summary",
            document_analysis="{}", code_analysis="{}", linkedin_profile="{}",
        )
        assert "candidate" in prompt.lower() and "summary" in prompt.lower()

    def test_load_interviewer_guide(self):
        prompt = get_prompt(
            "finalization.yaml", "interviewer_guide",
            experience_level="시니어", total_questions=25,
            categories=["role_fit", "technical_depth"],
        )
        assert "시니어" in prompt
        assert "25" in prompt

    def test_missing_key_raises(self):
        with pytest.raises(KeyError):
            get_prompt("jd_analysis.yaml", "nonexistent_key", jd_text="test")

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            get_prompt("nonexistent.yaml", "key")

    def test_missing_variable_keeps_placeholder(self):
        """Mustache 스타일: 누락된 변수는 플레이스홀더 유지 (에러 아님)."""
        result = get_prompt("jd_analysis.yaml", "analyze")  # missing jd_text
        # 누락된 변수 {{jd_text}}가 그대로 남아있어야 함
        assert "{{jd_text}}" in result


class TestYamlStructure:
    """Verify all YAML files have correct structure."""

    YAML_FILES = [
        "jd_analysis.yaml",
        "document_analysis.yaml",
        "question_generation.yaml",
        "quality_review.yaml",
        "finalization.yaml",
    ]

    def test_all_yamls_loadable(self):
        for f in self.YAML_FILES:
            data = _load_yaml(f)
            assert "prompts" in data, f"{f} missing 'prompts' key"

    def test_all_prompts_have_template(self):
        for f in self.YAML_FILES:
            data = _load_yaml(f)
            for key, value in data["prompts"].items():
                assert "template" in value, f"{f}:{key} missing 'template'"
                assert len(value["template"]) > 10, f"{f}:{key} template too short"


# =============================================================================
# Phase 3: Langfuse Prompt Management Integration Tests
# =============================================================================

class TestPhase3LangfusePromptFunctions:
    """Test new Phase 3 prompt management functions."""

    def test_get_prompt_with_metadata_importable(self):
        """get_prompt_with_metadata function is importable."""
        from app.prompts import get_prompt_with_metadata
        assert callable(get_prompt_with_metadata)

    def test_clear_prompt_cache_importable(self):
        """clear_prompt_cache function is importable."""
        from app.prompts import clear_prompt_cache
        assert callable(clear_prompt_cache)

    def test_list_local_prompts_importable(self):
        """list_local_prompts function is importable."""
        from app.prompts import list_local_prompts
        assert callable(list_local_prompts)

    def test_get_langfuse_prompt_name_importable(self):
        """_get_langfuse_prompt_name function is importable."""
        from app.prompts import _get_langfuse_prompt_name
        assert callable(_get_langfuse_prompt_name)

    def test_fetch_langfuse_prompt_importable(self):
        """_fetch_langfuse_prompt function is importable."""
        from app.prompts import _fetch_langfuse_prompt
        assert callable(_fetch_langfuse_prompt)


class TestPhase3PromptNameGeneration:
    """Test Langfuse prompt name generation."""

    def test_prompt_name_from_jd_analysis(self):
        """Generates correct name for jd_analysis prompts."""
        from app.prompts import _get_langfuse_prompt_name
        name = _get_langfuse_prompt_name("jd_analysis.yaml", "analyze")
        assert name == "jd_analysis_analyze"

    def test_prompt_name_from_question_generation(self):
        """Generates correct name for question_generation prompts."""
        from app.prompts import _get_langfuse_prompt_name
        name = _get_langfuse_prompt_name("question_generation.yaml", "craft_question")
        assert name == "question_generation_craft_question"

    def test_prompt_name_from_finalization(self):
        """Generates correct name for finalization prompts."""
        from app.prompts import _get_langfuse_prompt_name
        name = _get_langfuse_prompt_name("finalization.yaml", "candidate_summary")
        assert name == "finalization_candidate_summary"


class TestPhase3PromptMetadata:
    """Test prompt metadata functionality."""

    def test_get_prompt_with_metadata_returns_dict(self, monkeypatch):
        """get_prompt_with_metadata returns proper structure."""
        # Disable Langfuse for predictable behavior
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.prompts import get_prompt_with_metadata
        result = get_prompt_with_metadata(
            "jd_analysis.yaml",
            "analyze",
            jd_text="Test JD"
        )

        assert isinstance(result, dict)
        assert "prompt" in result
        assert "source" in result
        assert "version" in result
        assert "name" in result

    def test_yaml_fallback_sets_correct_metadata(self, monkeypatch):
        """YAML fallback sets source to 'yaml' and version to None."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.prompts import get_prompt_with_metadata
        result = get_prompt_with_metadata(
            "jd_analysis.yaml",
            "analyze",
            jd_text="Test JD"
        )

        assert result["source"] == "yaml"
        assert result["version"] is None
        assert result["name"] == "jd_analysis_analyze"
        assert "Test JD" in result["prompt"]


class TestPhase3PromptCache:
    """Test prompt caching functionality."""

    def test_clear_cache_function(self):
        """clear_prompt_cache executes without error."""
        from app.prompts import clear_prompt_cache, _langfuse_prompt_cache

        # Add test item to cache
        _langfuse_prompt_cache["test_key"] = "test_value"
        assert "test_key" in _langfuse_prompt_cache

        # Clear cache
        clear_prompt_cache()

        # Verify cleared
        assert "test_key" not in _langfuse_prompt_cache

    def test_list_local_prompts_returns_all_files(self):
        """list_local_prompts returns all YAML files."""
        from app.prompts import list_local_prompts

        result = list_local_prompts()

        assert isinstance(result, dict)
        assert "jd_analysis.yaml" in result
        assert "question_generation.yaml" in result
        assert "document_analysis.yaml" in result
        assert "quality_review.yaml" in result
        assert "finalization.yaml" in result

    def test_list_local_prompts_includes_keys(self):
        """list_local_prompts includes prompt keys for each file."""
        from app.prompts import list_local_prompts

        result = list_local_prompts()

        # Check specific keys exist
        assert "analyze" in result["jd_analysis.yaml"]
        assert "select_topics" in result["question_generation.yaml"]
        assert "craft_question" in result["question_generation.yaml"]


class TestPhase3LangfuseFallback:
    """Test Langfuse to YAML fallback behavior."""

    def test_langfuse_disabled_uses_yaml(self, monkeypatch):
        """When Langfuse disabled, get_prompt uses YAML."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.prompts import get_prompt
        prompt = get_prompt("jd_analysis.yaml", "analyze", jd_text="Test")

        # Should work with YAML fallback
        assert "Test" in prompt

    def test_fetch_langfuse_prompt_returns_none_when_disabled(self, monkeypatch):
        """_fetch_langfuse_prompt returns None when Langfuse disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.prompts import _fetch_langfuse_prompt
        result = _fetch_langfuse_prompt("test_prompt", jd_text="test")

        assert result is None

    def test_get_prompt_backward_compatible(self, monkeypatch):
        """get_prompt remains backward compatible with existing code."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.prompts import get_prompt

        # Test all existing prompt types still work
        prompt1 = get_prompt("jd_analysis.yaml", "analyze", jd_text="JD")
        assert "JD" in prompt1

        prompt2 = get_prompt(
            "question_generation.yaml", "select_topics",
            max_questions=25, experience_level="Senior", candidates="data"
        )
        assert "25" in prompt2


class TestPhase3PromptLogging:
    """Test prompt usage logging."""

    def test_log_prompt_usage_importable(self):
        """_log_prompt_usage function is importable."""
        from app.prompts import _log_prompt_usage
        assert callable(_log_prompt_usage)

    def test_log_prompt_usage_no_error_when_disabled(self, monkeypatch):
        """_log_prompt_usage doesn't raise when Langfuse disabled."""
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None
        )
        monkeypatch.setattr(
            "app.core.observability.settings.LANGFUSE_SECRET_KEY", None
        )

        from app.prompts import _log_prompt_usage

        # Should not raise
        _log_prompt_usage("test_prompt", "v1", "yaml", ["var1"])
