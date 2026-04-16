"""Kimi K2.5 thinking mode 정책 + extra_body 배관 테스트."""
from unittest.mock import patch

from app.services.cached_llm import CachedLLMService
from app.services.llm_config import (
    THINKING_ENABLED_PROMPTS,
    is_kimi_model,
    resolve_kimi_thinking,
)


class TestThinkingPolicy:
    def test_enabled_set_has_8_prompts(self):
        assert len(THINKING_ENABLED_PROMPTS) == 8

    def test_synthesis_prompts_enabled(self):
        for name in (
            "v2_generation_radar_analysis",
            "v2_generation_skill_matching",
            "v2_generation_decision_summary",
            "v2_generation_interviewer_tips",
        ):
            assert resolve_kimi_thinking(
                prompt_name=name, activity_name=None, langfuse_config=None
            ) is True, name

    def test_final_review_prompts_enabled(self):
        for name in (
            "quality_review_review",
            "question_enhancement_revise_questions",
        ):
            assert resolve_kimi_thinking(
                prompt_name=name, activity_name=None, langfuse_config=None
            ) is True, name

    def test_finalization_prompts_enabled(self):
        for name in (
            "finalization_candidate_summary",
            "finalization_interviewer_guide",
        ):
            assert resolve_kimi_thinking(
                prompt_name=name, activity_name=None, langfuse_config=None
            ) is True, name

    def test_parallel_analysis_prompts_disabled(self):
        for name in (
            "jd_analysis_analyze",
            "jd_analysis_translate",
            "document_analysis_extract_profile",
            "linkedin_summary_recommendations_summary",
            "question_topic_selection_select_topics",
            "question_craft_technical_depth_craft_question_technical_depth",
            "question_enhancement_enhance_terminology",
            "question_enhancement_generate_scenarios",
            "question_enhancement_generate_followups",
            "question_enhancement_generate_interviewer_notes",
            "question_enhancement_generate_decision_guide",
        ):
            assert resolve_kimi_thinking(
                prompt_name=name, activity_name=None, langfuse_config=None
            ) is False, name

    def test_code_deep_analysis_prefix_disabled(self):
        assert resolve_kimi_thinking(
            prompt_name=None,
            activity_name="code_deep_analysis_src/main.py",
            langfuse_config=None,
        ) is False

    def test_langfuse_config_enabled_override(self):
        assert resolve_kimi_thinking(
            prompt_name="jd_analysis_analyze",
            activity_name=None,
            langfuse_config={"thinking": {"type": "enabled"}},
        ) is True

    def test_langfuse_config_disabled_override(self):
        assert resolve_kimi_thinking(
            prompt_name="v2_generation_radar_analysis",
            activity_name=None,
            langfuse_config={"thinking": {"type": "disabled"}},
        ) is False

    def test_env_on_forces_enabled(self):
        with patch("app.services.llm_config.settings.LLM_KIMI_THINKING", "on"):
            assert resolve_kimi_thinking(
                prompt_name="jd_analysis_analyze",
                activity_name=None,
                langfuse_config=None,
            ) is True

    def test_env_off_forces_disabled(self):
        with patch("app.services.llm_config.settings.LLM_KIMI_THINKING", "off"):
            assert resolve_kimi_thinking(
                prompt_name="v2_generation_radar_analysis",
                activity_name=None,
                langfuse_config=None,
            ) is False

    def test_default_off_for_unknown(self):
        assert resolve_kimi_thinking(
            prompt_name="some_unknown_prompt",
            activity_name=None,
            langfuse_config=None,
        ) is False


class TestIsKimiModel:
    def test_moonshot_prefix_is_kimi(self):
        assert is_kimi_model("moonshot/kimi-k2.5") is True
        assert is_kimi_model("moonshot/kimi-k2-0905-preview") is True

    def test_other_providers_not_kimi(self):
        assert is_kimi_model("openai:gpt-4.1-mini") is False
        assert is_kimi_model("zai/glm-4.5-flash") is False
        assert is_kimi_model("anthropic:claude-3-5-sonnet") is False
        assert is_kimi_model(None) is False
        assert is_kimi_model("") is False


class TestBuildKimiThinkingArgs:
    def test_kimi_thinking_enabled_forces_temp_1(self):
        extra, temp = CachedLLMService._build_kimi_thinking_args(
            model="moonshot/kimi-k2.5",
            prompt_name="finalization_candidate_summary",
        )
        assert extra == {"thinking": {"type": "enabled"}}
        assert temp == 1.0

    def test_kimi_thinking_disabled_forces_temp_0_6(self):
        extra, temp = CachedLLMService._build_kimi_thinking_args(
            model="moonshot/kimi-k2.5",
            prompt_name="jd_analysis_analyze",
        )
        assert extra == {"thinking": {"type": "disabled"}}
        assert temp == 0.6

    def test_non_kimi_passthrough_preserves_base_temp(self):
        extra, temp = CachedLLMService._build_kimi_thinking_args(
            model="openai:gpt-4.1-mini",
            prompt_name="finalization_candidate_summary",
            base_temperature=0.2,
        )
        assert extra is None
        assert temp == 0.2

    def test_non_kimi_passthrough_with_no_base_temp(self):
        extra, temp = CachedLLMService._build_kimi_thinking_args(
            model="zai/glm-4.5-flash",
            activity_name="analyze_code",
        )
        assert extra is None
        assert temp == 0.0

    def test_langfuse_config_wins_over_default_set(self):
        extra, temp = CachedLLMService._build_kimi_thinking_args(
            model="moonshot/kimi-k2.5",
            prompt_name="jd_analysis_analyze",
            langfuse_config={"thinking": {"type": "enabled"}},
        )
        assert extra == {"thinking": {"type": "enabled"}}
        assert temp == 1.0
