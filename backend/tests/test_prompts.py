"""Unit tests for prompt template loader."""
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
        assert "candidate profile" in prompt

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
            document_analysis="{}", code_analysis="{}",
        )
        assert "candidate summary" in prompt

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

    def test_missing_variable_raises(self):
        with pytest.raises(KeyError):
            get_prompt("jd_analysis.yaml", "analyze")  # missing jd_text


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
