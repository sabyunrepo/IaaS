"""
Analysis 도메인 모델 테스트

TDD: 테스트 먼저 작성 후 모델 구현
"""
import pytest
from pydantic import ValidationError

from domain.analysis.models import (
    AuthenticityScore,
    ComplexityMetrics,
    SkillAssessment,
)


# ---------------------------------------------------------------------------
# ComplexityMetrics
# ---------------------------------------------------------------------------


def _make_complexity(**overrides) -> ComplexityMetrics:
    defaults = dict(
        cyclomatic_complexity=5.0,
        halstead_difficulty=12.3,
        halstead_volume=234.5,
        maintainability_index=72.0,
        cognitive_complexity=8.0,
    )
    defaults.update(overrides)
    return ComplexityMetrics(**defaults)


class TestComplexityMetrics:
    def test_creation(self):
        m = _make_complexity()
        assert m.cyclomatic_complexity == 5.0
        assert m.halstead_difficulty == 12.3
        assert m.halstead_volume == 234.5
        assert m.maintainability_index == 72.0
        assert m.cognitive_complexity == 8.0

    def test_zero_values_accepted(self):
        m = _make_complexity(
            cyclomatic_complexity=0.0,
            halstead_difficulty=0.0,
            halstead_volume=0.0,
            maintainability_index=0.0,
            cognitive_complexity=0.0,
        )
        assert m.cyclomatic_complexity == 0.0
        assert m.maintainability_index == 0.0

    def test_maintainability_index_upper_bound(self):
        m = _make_complexity(maintainability_index=100.0)
        assert m.maintainability_index == 100.0

    def test_maintainability_index_exceeds_upper_bound(self):
        with pytest.raises(ValidationError):
            _make_complexity(maintainability_index=100.1)

    def test_negative_cyclomatic_rejected(self):
        with pytest.raises(ValidationError):
            _make_complexity(cyclomatic_complexity=-0.1)

    def test_negative_halstead_difficulty_rejected(self):
        with pytest.raises(ValidationError):
            _make_complexity(halstead_difficulty=-1.0)

    def test_negative_halstead_volume_rejected(self):
        with pytest.raises(ValidationError):
            _make_complexity(halstead_volume=-1.0)

    def test_negative_maintainability_rejected(self):
        with pytest.raises(ValidationError):
            _make_complexity(maintainability_index=-0.1)

    def test_negative_cognitive_rejected(self):
        with pytest.raises(ValidationError):
            _make_complexity(cognitive_complexity=-1.0)

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            ComplexityMetrics(cyclomatic_complexity=5.0)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# AuthenticityScore
# ---------------------------------------------------------------------------


def _make_authenticity(**overrides) -> AuthenticityScore:
    defaults = dict(
        human_typing_ratio=0.85,
        originality_ratio=0.90,
        ai_code_suspicion=0.10,
        plagiarism_ratio=0.05,
        style_consistency=0.80,
    )
    defaults.update(overrides)
    return AuthenticityScore(**defaults)


class TestAuthenticityScore:
    def test_creation(self):
        a = _make_authenticity()
        assert a.human_typing_ratio == 0.85
        assert a.originality_ratio == 0.90
        assert a.ai_code_suspicion == 0.10
        assert a.plagiarism_ratio == 0.05
        assert a.style_consistency == 0.80

    def test_zero_values_accepted(self):
        a = _make_authenticity(
            human_typing_ratio=0.0,
            originality_ratio=0.0,
            ai_code_suspicion=0.0,
            plagiarism_ratio=0.0,
            style_consistency=0.0,
        )
        assert a.human_typing_ratio == 0.0

    def test_one_values_accepted(self):
        a = _make_authenticity(
            human_typing_ratio=1.0,
            originality_ratio=1.0,
            ai_code_suspicion=1.0,
            plagiarism_ratio=1.0,
            style_consistency=1.0,
        )
        assert a.human_typing_ratio == 1.0

    def test_human_typing_ratio_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _make_authenticity(human_typing_ratio=-0.01)

    def test_human_typing_ratio_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _make_authenticity(human_typing_ratio=1.01)

    def test_originality_ratio_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _make_authenticity(originality_ratio=-0.01)

    def test_originality_ratio_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _make_authenticity(originality_ratio=1.01)

    def test_ai_code_suspicion_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _make_authenticity(ai_code_suspicion=-0.01)

    def test_ai_code_suspicion_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _make_authenticity(ai_code_suspicion=1.01)

    def test_plagiarism_ratio_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _make_authenticity(plagiarism_ratio=-0.01)

    def test_plagiarism_ratio_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _make_authenticity(plagiarism_ratio=1.01)

    def test_style_consistency_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _make_authenticity(style_consistency=-0.01)

    def test_style_consistency_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _make_authenticity(style_consistency=1.01)

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            AuthenticityScore(human_typing_ratio=0.5)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# SkillAssessment
# ---------------------------------------------------------------------------


def _make_skill(**overrides) -> SkillAssessment:
    defaults = dict(
        skill_name="Python",
        proficiency="advanced",
        evidence_count=15,
        evidence_sources=["src/service.py", "src/utils.py"],
        confidence="high",
    )
    defaults.update(overrides)
    return SkillAssessment(**defaults)


class TestSkillAssessment:
    def test_creation(self):
        s = _make_skill()
        assert s.skill_name == "Python"
        assert s.proficiency == "advanced"
        assert s.evidence_count == 15
        assert s.evidence_sources == ["src/service.py", "src/utils.py"]
        assert s.confidence == "high"

    def test_proficiency_beginner(self):
        s = _make_skill(proficiency="beginner")
        assert s.proficiency == "beginner"

    def test_proficiency_intermediate(self):
        s = _make_skill(proficiency="intermediate")
        assert s.proficiency == "intermediate"

    def test_proficiency_advanced(self):
        s = _make_skill(proficiency="advanced")
        assert s.proficiency == "advanced"

    def test_proficiency_expert(self):
        s = _make_skill(proficiency="expert")
        assert s.proficiency == "expert"

    def test_confidence_high(self):
        s = _make_skill(confidence="high")
        assert s.confidence == "high"

    def test_confidence_medium(self):
        s = _make_skill(confidence="medium")
        assert s.confidence == "medium"

    def test_confidence_low(self):
        s = _make_skill(confidence="low")
        assert s.confidence == "low"

    def test_evidence_count_zero(self):
        s = _make_skill(evidence_count=0)
        assert s.evidence_count == 0

    def test_evidence_count_negative_rejected(self):
        with pytest.raises(ValidationError):
            _make_skill(evidence_count=-1)

    def test_evidence_sources_empty(self):
        s = _make_skill(evidence_sources=[])
        assert s.evidence_sources == []

    def test_evidence_sources_multiple(self):
        sources = ["src/a.py", "src/b.py", "src/c.py"]
        s = _make_skill(evidence_sources=sources)
        assert s.evidence_sources == sources

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            SkillAssessment(skill_name="Python")  # type: ignore[call-arg]
