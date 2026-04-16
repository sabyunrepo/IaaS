"""Kimi K2.5 thinking mode 정책 + extra_body 배관 테스트."""
from unittest.mock import patch

import pytest

from app.services import llm_config
from app.services.cached_llm import CachedLLMService
from app.services.llm_config import (
    THINKING_ENABLED_PROMPTS,
    is_kimi_model,
    resolve_kimi_thinking,
)


@pytest.fixture(autouse=True)
def _reset_malformed_warn_cache():
    """각 테스트마다 malformed warn dedup 세트를 초기화."""
    llm_config._WARNED_MALFORMED_THINKING.clear()
    yield
    llm_config._WARNED_MALFORMED_THINKING.clear()


class TestThinkingPolicy:
    def test_enabled_set_has_9_prompts(self):
        # 8 + code_synthesis_analysis (3-Stage 코드 분석 Stage 3 종합)
        assert len(THINKING_ENABLED_PROMPTS) == 9

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


class TestCodeSynthesisThinking:
    """Fix #2: code_synthesis_analysis (Stage 3 종합)가 thinking=ON."""

    def test_synthesis_activity_enabled(self):
        # activity_name 경로 (code_analyzer.llm_synthesize_analysis에서 사용)
        assert resolve_kimi_thinking(
            prompt_name=None,
            activity_name="code_synthesis_analysis",
            langfuse_config=None,
        ) is True

    def test_overview_activity_disabled(self):
        # Stage 1 overview는 OFF 유지 (preliminary survey)
        assert resolve_kimi_thinking(
            prompt_name=None,
            activity_name="code_overview_analysis",
            langfuse_config=None,
        ) is False

    def test_deep_analysis_prefix_still_disabled(self):
        # Stage 2 per-file deep analysis도 OFF 유지
        assert resolve_kimi_thinking(
            prompt_name=None,
            activity_name="code_deep_analysis_src/foo.py",
            langfuse_config=None,
        ) is False

    def test_synthesis_in_enabled_set(self):
        assert "code_synthesis_analysis" in THINKING_ENABLED_PROMPTS


class TestMalformedLangfuseThinkingConfig:
    """Fix #4 Part B: 잘못된 Langfuse config.thinking은 정책으로 fallthrough + 1회 경고."""

    def test_bool_true_falls_back_to_policy(self):
        # enabled_set에 있는 프롬프트 → 정책으로 True
        assert resolve_kimi_thinking(
            prompt_name="finalization_candidate_summary",
            activity_name=None,
            langfuse_config={"thinking": True},
        ) is True

    def test_bool_true_unknown_prompt_falls_back_to_default_off(self):
        assert resolve_kimi_thinking(
            prompt_name="some_unknown_prompt",
            activity_name=None,
            langfuse_config={"thinking": True},
        ) is False

    def test_string_enabled_falls_back_to_policy(self):
        # "yes"는 dict가 아니므로 malformed → 정책 fallthrough
        assert resolve_kimi_thinking(
            prompt_name="v2_generation_radar_analysis",
            activity_name=None,
            langfuse_config={"thinking": "yes"},
        ) is True

    def test_wrong_dict_shape_falls_back_to_policy(self):
        # {"enabled": True} 형태도 malformed
        assert resolve_kimi_thinking(
            prompt_name="jd_analysis_analyze",
            activity_name=None,
            langfuse_config={"thinking": {"enabled": True}},
        ) is False

    def test_warning_logged_once_per_prompt(self, caplog):
        import logging
        caplog.set_level(logging.WARNING, logger="app.services.llm_config")
        # 같은 프롬프트로 두 번 호출 → warn은 한 번만
        for _ in range(3):
            resolve_kimi_thinking(
                prompt_name="some_prompt",
                activity_name=None,
                langfuse_config={"thinking": True},
            )
        warn_records = [
            r for r in caplog.records
            if r.levelno == logging.WARNING
            and "config.thinking malformed" in r.getMessage()
        ]
        assert len(warn_records) == 1, f"expected 1 warning, got {len(warn_records)}"

    def test_warning_separate_per_prompt(self, caplog):
        import logging
        caplog.set_level(logging.WARNING, logger="app.services.llm_config")
        resolve_kimi_thinking(
            prompt_name="prompt_a", activity_name=None,
            langfuse_config={"thinking": True},
        )
        resolve_kimi_thinking(
            prompt_name="prompt_b", activity_name=None,
            langfuse_config={"thinking": "yes"},
        )
        warn_records = [
            r for r in caplog.records
            if r.levelno == logging.WARNING
            and "config.thinking malformed" in r.getMessage()
        ]
        assert len(warn_records) == 2

    def test_valid_config_does_not_warn(self, caplog):
        import logging
        caplog.set_level(logging.WARNING, logger="app.services.llm_config")
        resolve_kimi_thinking(
            prompt_name="whatever", activity_name=None,
            langfuse_config={"thinking": {"type": "enabled"}},
        )
        warn_records = [
            r for r in caplog.records
            if "config.thinking malformed" in r.getMessage()
        ]
        assert len(warn_records) == 0

    def test_missing_thinking_key_does_not_warn(self, caplog):
        import logging
        caplog.set_level(logging.WARNING, logger="app.services.llm_config")
        resolve_kimi_thinking(
            prompt_name="whatever", activity_name=None,
            langfuse_config={"other_field": 42},
        )
        warn_records = [
            r for r in caplog.records
            if "config.thinking malformed" in r.getMessage()
        ]
        assert len(warn_records) == 0


class TestCacheKeyThinkingAware:
    """Fix #1: cache-key가 temperature/extra_body 변화를 반영."""

    def test_different_thinking_mode_different_cache_key(self):
        # 같은 prompt+model, thinking ON vs OFF → 다른 키
        key_on = CachedLLMService._make_cache_key(
            prompt="hello", model="moonshot/kimi-k2.5",
            activity_name="synthesis",
            temperature=1.0,
            extra_body={"thinking": {"type": "enabled"}},
        )
        key_off = CachedLLMService._make_cache_key(
            prompt="hello", model="moonshot/kimi-k2.5",
            activity_name="synthesis",
            temperature=0.6,
            extra_body={"thinking": {"type": "disabled"}},
        )
        assert key_on != key_off

    def test_same_thinking_mode_same_cache_key(self):
        key_a = CachedLLMService._make_cache_key(
            prompt="hello", model="moonshot/kimi-k2.5",
            activity_name="synthesis",
            temperature=1.0,
            extra_body={"thinking": {"type": "enabled"}},
        )
        key_b = CachedLLMService._make_cache_key(
            prompt="hello", model="moonshot/kimi-k2.5",
            activity_name="synthesis",
            temperature=1.0,
            extra_body={"thinking": {"type": "enabled"}},
        )
        assert key_a == key_b

    def test_non_kimi_stable_key_regardless_of_temperature_fluctuation(self):
        # Non-Kimi: extra_body=None, temperature는 operator가 설정한 base
        # → temperature가 같으면 같은 키 (안정적)
        key_a = CachedLLMService._make_cache_key(
            prompt="hello", model="openai:gpt-4.1-mini",
            activity_name="analyze_jd",
            temperature=0.0, extra_body=None,
        )
        key_b = CachedLLMService._make_cache_key(
            prompt="hello", model="openai:gpt-4.1-mini",
            activity_name="analyze_jd",
            temperature=0.0, extra_body=None,
        )
        assert key_a == key_b

    def test_non_kimi_extra_body_none_does_not_affect_hash(self):
        # extra_body=None 일 때 해시는 model+prompt (+temperature) 기반이어야 한다
        key_with = CachedLLMService._make_cache_key(
            prompt="hi", model="openai:gpt-4.1-mini",
            temperature=0.0, extra_body=None,
        )
        # 같은 인자를 명시적으로 전달해도 동일
        key_also = CachedLLMService._make_cache_key(
            prompt="hi", model="openai:gpt-4.1-mini",
            temperature=0.0, extra_body=None,
        )
        assert key_with == key_also

    def test_prefix_separator_changed_from_colon_to_pipe(self):
        # Orphan 키 방지: 새 포맷은 `|` separator를 사용하여 이전 `model:prompt` 해시와 다름
        import hashlib
        model, prompt = "moonshot/kimi-k2.5", "hello"
        old_format_hash = hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()
        new_key = CachedLLMService._make_cache_key(
            prompt=prompt, model=model, temperature=None, extra_body=None,
        )
        # 새 키는 old_format 해시를 포함하지 않아야 한다
        assert old_format_hash not in new_key

    def test_cache_key_signature_accepts_new_kwargs(self):
        # 시그니처 regression 방지
        key = CachedLLMService._make_cache_key(
            prompt="p", model="m",
            activity_name="a", job_id="j",
            temperature=0.6, extra_body={"thinking": {"type": "disabled"}},
        )
        assert key.startswith("llm_cache:job:j:a:")
