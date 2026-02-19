"""
OutputAssembler 노드의 _build_decision_support() 순수 함수 테스트.

외부 의존성 없이 dict 입출력만 검증한다.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# langfuse import 문제 우회 (Python 3.14 + pydantic v1 호환 문제)
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
        if _mod_name == "langfuse":
            _m.Langfuse = MagicMock  # type: ignore[attr-defined]
        sys.modules[_mod_name] = _m

from application.nodes.meta.output_assembler import (  # noqa: E402
    _build_decision_support,
)


# ===========================================================================
# 헬퍼: 테스트용 candidate_scores 생성
# ===========================================================================


def _make_scores(
    logic: float = 75,
    mastery: float = 75,
    stability: float = 75,
    authenticity: float = 75,
    weighted_total: float = 75,
    confidence: str = "high",
) -> dict:
    """4대 지표가 포함된 candidate_scores dict를 생성한다."""
    return {
        "logic": {"normalized_score": logic},
        "mastery": {"normalized_score": mastery},
        "stability": {"normalized_score": stability},
        "authenticity": {"normalized_score": authenticity},
        "weighted_total": weighted_total,
        "confidence": confidence,
    }


# ===========================================================================
# test_decision_support_hire: 모든 점수 높음 → hire
# ===========================================================================


class TestDecisionSupportHire:
    """weighted_total >= 70 + 모든 축 >= 50 → hire."""

    def test_all_high_scores(self):
        scores = _make_scores(
            logic=85, mastery=80, stability=75, authenticity=90,
            weighted_total=82, confidence="high",
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "hire"
        assert result["confidence"] == "high"
        assert "채용 권장" in result["recommendation_reason"]

    def test_all_axes_exactly_70(self):
        scores = _make_scores(
            logic=70, mastery=70, stability=70, authenticity=70,
            weighted_total=70, confidence="medium",
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "hire"

    def test_strengths_populated_for_green_axes(self):
        scores = _make_scores(
            logic=85, mastery=80, stability=75, authenticity=90,
            weighted_total=82,
        )
        result = _build_decision_support(scores, {}, {})

        # 모든 축이 >= 70이므로 4개 strengths
        assert len(result["strengths"]) == 4
        assert len(result["concerns"]) == 0

    def test_four_axes_summary_all_strong(self):
        scores = _make_scores(
            logic=85, mastery=80, stability=75, authenticity=90,
            weighted_total=82,
        )
        result = _build_decision_support(scores, {}, {})

        for axis in ("logic", "mastery", "stability", "authenticity"):
            assert result["four_axes_summary"][axis]["verdict"] == "Strong"

    def test_no_risk_factors_when_all_good(self):
        scores = _make_scores(
            logic=85, mastery=80, stability=75, authenticity=90,
            weighted_total=82,
        )
        # AI 의심률 낮음
        forensic = {"ai_detection": {"avg_suspicion": 0.1}}
        result = _build_decision_support(scores, forensic, {})

        assert result["risk_factors"] == []


# ===========================================================================
# test_decision_support_conditional: 중간 점수 → conditional_hire
# ===========================================================================


class TestDecisionSupportConditionalHire:
    """weighted_total >= 60 + red 축 <= 1개 → conditional_hire."""

    def test_total_65_one_red_axis(self):
        """총점 65, red 1개 → conditional_hire."""
        scores = _make_scores(
            logic=70, mastery=65, stability=45, authenticity=70,
            weighted_total=65, confidence="medium",
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "conditional_hire"
        assert result["confidence"] == "medium"
        assert "조건부 채용" in result["recommendation_reason"]

    def test_total_60_no_red_axis(self):
        """총점 60, 모든 축 50 이상이지만 총점 < 70 → conditional_hire."""
        scores = _make_scores(
            logic=55, mastery=60, stability=55, authenticity=65,
            weighted_total=60, confidence="medium",
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "conditional_hire"

    def test_total_69_all_above_50(self):
        """총점 69 (< 70), 모든 축 >= 50 → conditional_hire (hire 아님)."""
        scores = _make_scores(
            logic=65, mastery=68, stability=55, authenticity=72,
            weighted_total=69, confidence="medium",
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "conditional_hire"

    def test_concerns_for_yellow_axes(self):
        """yellow(50~69) 축은 concerns에 포함."""
        scores = _make_scores(
            logic=75, mastery=55, stability=60, authenticity=80,
            weighted_total=68,
        )
        result = _build_decision_support(scores, {}, {})

        # mastery(55), stability(60) → 2개 concerns
        assert len(result["concerns"]) == 2
        for c in result["concerns"]:
            assert "주의" in c  # yellow = 주의

    def test_weak_axes_in_reason(self):
        """red 축이 있으면 recommendation_reason에 약점 표시."""
        scores = _make_scores(
            logic=75, mastery=75, stability=40, authenticity=75,
            weighted_total=65,
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "conditional_hire"
        assert "코드 안정성" in result["recommendation_reason"]


# ===========================================================================
# test_decision_support_no_hire: 낮은 점수 → no_hire
# ===========================================================================


class TestDecisionSupportNoHire:
    """weighted_total < 60 or red 축 >= 2 → no_hire."""

    def test_very_low_total(self):
        scores = _make_scores(
            logic=30, mastery=35, stability=25, authenticity=20,
            weighted_total=28, confidence="low",
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "no_hire"
        assert result["confidence"] == "low"
        assert "채용 비권장" in result["recommendation_reason"]

    def test_total_59_one_red(self):
        """총점 59 + red 1개 → no_hire (총점 < 60)."""
        scores = _make_scores(
            logic=60, mastery=65, stability=45, authenticity=60,
            weighted_total=59,
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "no_hire"

    def test_total_65_two_red(self):
        """총점 65 + red 2개 → no_hire (red > 1)."""
        scores = _make_scores(
            logic=80, mastery=85, stability=40, authenticity=35,
            weighted_total=65,
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "no_hire"

    def test_concerns_for_red_axes(self):
        """red(< 50) 축은 concerns에 '경고'로 포함."""
        scores = _make_scores(
            logic=30, mastery=35, stability=25, authenticity=20,
            weighted_total=28,
        )
        result = _build_decision_support(scores, {}, {})

        assert len(result["concerns"]) == 4
        for c in result["concerns"]:
            assert "경고" in c  # red = 경고

    def test_four_axes_summary_all_weak(self):
        scores = _make_scores(
            logic=30, mastery=35, stability=25, authenticity=20,
            weighted_total=28,
        )
        result = _build_decision_support(scores, {}, {})

        for axis in ("logic", "mastery", "stability", "authenticity"):
            assert result["four_axes_summary"][axis]["verdict"] == "Weak"

    def test_red_count_in_reason(self):
        scores = _make_scores(
            logic=80, mastery=85, stability=40, authenticity=35,
            weighted_total=65,
        )
        result = _build_decision_support(scores, {}, {})

        assert "red 지표 2개" in result["recommendation_reason"]


# ===========================================================================
# test_decision_support_risk_factors: AI 의심 높을 때 리스크 포함
# ===========================================================================


class TestDecisionSupportRiskFactors:
    """리스크 요인이 올바르게 포함되는지 검증."""

    def test_high_ai_suspicion(self):
        """AI 의심률 > 30% → risk_factors에 포함."""
        scores = _make_scores(weighted_total=75)
        forensic = {"ai_detection": {"avg_suspicion": 0.55}}

        result = _build_decision_support(scores, forensic, {})

        assert len(result["risk_factors"]) >= 1
        assert any("AI 코드 의심률" in r for r in result["risk_factors"])
        assert any("55.0%" in r for r in result["risk_factors"])

    def test_low_ai_suspicion_no_risk(self):
        """AI 의심률 <= 30% → risk_factors에 미포함."""
        scores = _make_scores(weighted_total=75)
        forensic = {"ai_detection": {"avg_suspicion": 0.2}}

        result = _build_decision_support(scores, forensic, {})

        assert not any("AI 코드 의심률" in r for r in result["risk_factors"])

    def test_ai_suspicion_at_boundary(self):
        """AI 의심률 정확히 30% → 포함 안 됨 (> 0.3 조건)."""
        scores = _make_scores(weighted_total=75)
        forensic = {"ai_detection": {"avg_suspicion": 0.3}}

        result = _build_decision_support(scores, forensic, {})

        assert not any("AI 코드 의심률" in r for r in result["risk_factors"])

    def test_low_stability_risk(self):
        """stability < 50 → risk_factors에 유지보수 리스크."""
        scores = _make_scores(stability=40, weighted_total=55)

        result = _build_decision_support(scores, {}, {})

        assert any("유지보수 리스크" in r for r in result["risk_factors"])

    def test_low_authenticity_risk(self):
        """authenticity < 50 → risk_factors에 진정성 검증 필요."""
        scores = _make_scores(authenticity=35, weighted_total=55)

        result = _build_decision_support(scores, {}, {})

        assert any("본인 작성 여부 검증" in r for r in result["risk_factors"])

    def test_multiple_risk_factors(self):
        """여러 리스크가 동시에 발생할 수 있음."""
        scores = _make_scores(
            stability=30, authenticity=25, weighted_total=40,
        )
        forensic = {"ai_detection": {"avg_suspicion": 0.8}}

        result = _build_decision_support(scores, forensic, {})

        assert len(result["risk_factors"]) == 3  # AI + stability + authenticity

    def test_empty_ai_detection(self):
        """forensic에 ai_detection이 빈 dict → 리스크 없음."""
        scores = _make_scores(weighted_total=75)
        forensic = {"ai_detection": {}}

        result = _build_decision_support(scores, forensic, {})

        assert not any("AI 코드 의심률" in r for r in result["risk_factors"])

    def test_missing_ai_detection(self):
        """forensic에 ai_detection 키 자체가 없음 → 리스크 없음."""
        scores = _make_scores(weighted_total=75)

        result = _build_decision_support(scores, {}, {})

        assert not any("AI 코드 의심률" in r for r in result["risk_factors"])


# ===========================================================================
# test_decision_support_empty_scores: 빈 scores → no_hire + low confidence
# ===========================================================================


class TestDecisionSupportEmptyScores:
    """candidate_scores가 빈/None일 때 안전하게 처리."""

    def test_none_scores(self):
        result = _build_decision_support(None, {}, {})

        assert result["recommendation"] == "no_hire"
        assert result["confidence"] == "low"
        assert result["strengths"] == []
        assert len(result["concerns"]) == 4  # 모든 축 0점 → 4개 경고

    def test_empty_dict_scores(self):
        result = _build_decision_support({}, {}, {})

        assert result["recommendation"] == "no_hire"
        assert result["confidence"] == "low"

    def test_partial_scores(self):
        """일부 축만 있을 때도 안전 처리."""
        scores = {
            "logic": {"normalized_score": 80},
            "weighted_total": 50,
            "confidence": "low",
        }
        result = _build_decision_support(scores, {}, {})

        assert result["four_axes_summary"]["logic"]["score"] == 80.0
        assert result["four_axes_summary"]["mastery"]["score"] == 0.0
        assert result["recommendation"] == "no_hire"  # weighted_total=50 < 60

    def test_four_axes_summary_defaults_to_zero(self):
        result = _build_decision_support(None, {}, {})

        for axis in ("logic", "mastery", "stability", "authenticity"):
            assert result["four_axes_summary"][axis]["score"] == 0.0
            assert result["four_axes_summary"][axis]["verdict"] == "Weak"

    def test_recommendation_reason_for_empty(self):
        result = _build_decision_support(None, {}, {})

        assert "종합 0점" in result["recommendation_reason"]
        assert "채용 비권장" in result["recommendation_reason"]


# ===========================================================================
# 경계값 테스트
# ===========================================================================


class TestDecisionSupportBoundary:
    """추천 로직의 경계값 검증."""

    def test_total_70_all_50_is_hire(self):
        """정확히 70 + 모든 축 정확히 50 → hire."""
        scores = _make_scores(
            logic=50, mastery=50, stability=50, authenticity=50,
            weighted_total=70,
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "hire"

    def test_total_70_one_at_49_is_conditional(self):
        """총점 70이지만 한 축이 49 → conditional_hire (all_above_50 실패)."""
        scores = _make_scores(
            logic=80, mastery=70, stability=49, authenticity=70,
            weighted_total=70,
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "conditional_hire"

    def test_total_60_two_red_is_no_hire(self):
        """총점 60이지만 red 2개 → no_hire."""
        scores = _make_scores(
            logic=80, mastery=80, stability=40, authenticity=35,
            weighted_total=60,
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "no_hire"

    def test_total_60_one_red_is_conditional(self):
        """총점 60 + red 1개 → conditional_hire."""
        scores = _make_scores(
            logic=75, mastery=70, stability=45, authenticity=65,
            weighted_total=60,
        )
        result = _build_decision_support(scores, {}, {})

        assert result["recommendation"] == "conditional_hire"

    def test_verdict_moderate_for_score_50(self):
        """정확히 50점 → Moderate."""
        scores = _make_scores(logic=50, weighted_total=50)
        result = _build_decision_support(scores, {}, {})

        assert result["four_axes_summary"]["logic"]["verdict"] == "Moderate"

    def test_verdict_strong_for_score_70(self):
        """정확히 70점 → Strong."""
        scores = _make_scores(logic=70, weighted_total=70)
        result = _build_decision_support(scores, {}, {})

        assert result["four_axes_summary"]["logic"]["verdict"] == "Strong"

    def test_verdict_weak_for_score_49(self):
        """49점 → Weak."""
        scores = _make_scores(logic=49, weighted_total=49)
        result = _build_decision_support(scores, {}, {})

        assert result["four_axes_summary"]["logic"]["verdict"] == "Weak"
