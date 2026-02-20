"""
Scoring Calculator 도메인 테스트

TDD: 테스트 먼저 작성 후 모델/계산기/신뢰도 구현.
4대 지표(Logic/Mastery/Stability/Authenticity) 가중 합산 + 신뢰도 판별.
"""
import pytest
from pydantic import ValidationError

from domain.scoring.models import (
    CandidateScore,
    MetricScore,
    MetricType,
    ScoreConfidence,
)
from domain.scoring.calculator import calculate_weighted_score
from domain.scoring.confidence import determine_confidence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_metric_score(
    *,
    metric_type: MetricType = MetricType.LOGIC,
    raw_score: float = 75.0,
    normalized_score: float = 75.0,
    sub_scores: dict[str, float] | None = None,
    evidence_count: int = 5,
) -> MetricScore:
    return MetricScore(
        metric_type=metric_type,
        raw_score=raw_score,
        normalized_score=normalized_score,
        sub_scores=sub_scores if sub_scores is not None else {"complexity": 70.0, "structure": 80.0},
        evidence_count=evidence_count,
    )


def make_all_metrics(score: float = 80.0) -> dict[MetricType, MetricScore]:
    return {
        MetricType.LOGIC: make_metric_score(
            metric_type=MetricType.LOGIC,
            raw_score=score,
            normalized_score=score,
        ),
        MetricType.MASTERY: make_metric_score(
            metric_type=MetricType.MASTERY,
            raw_score=score,
            normalized_score=score,
        ),
        MetricType.STABILITY: make_metric_score(
            metric_type=MetricType.STABILITY,
            raw_score=score,
            normalized_score=score,
        ),
        MetricType.AUTHENTICITY: make_metric_score(
            metric_type=MetricType.AUTHENTICITY,
            raw_score=score,
            normalized_score=score,
        ),
    }


# ---------------------------------------------------------------------------
# MetricScore model tests
# ---------------------------------------------------------------------------


class TestMetricScore:
    def test_valid_creation(self):
        score = make_metric_score(
            metric_type=MetricType.LOGIC,
            raw_score=80.0,
            normalized_score=75.0,
            sub_scores={"complexity": 70.0, "structure": 80.0},
            evidence_count=3,
        )
        assert score.metric_type == MetricType.LOGIC
        assert score.raw_score == pytest.approx(80.0)
        assert score.normalized_score == pytest.approx(75.0)
        assert score.sub_scores == {"complexity": 70.0, "structure": 80.0}
        assert score.evidence_count == 3

    def test_raw_score_above_100_rejected(self):
        with pytest.raises(ValidationError):
            MetricScore(
                metric_type=MetricType.LOGIC,
                raw_score=101.0,
                normalized_score=75.0,
                sub_scores={},
                evidence_count=1,
            )

    def test_normalized_score_above_100_rejected(self):
        with pytest.raises(ValidationError):
            MetricScore(
                metric_type=MetricType.MASTERY,
                raw_score=80.0,
                normalized_score=100.1,
                sub_scores={},
                evidence_count=1,
            )

    def test_score_below_0_rejected(self):
        with pytest.raises(ValidationError):
            MetricScore(
                metric_type=MetricType.STABILITY,
                raw_score=-1.0,
                normalized_score=50.0,
                sub_scores={},
                evidence_count=0,
            )

    def test_normalized_score_below_0_rejected(self):
        with pytest.raises(ValidationError):
            MetricScore(
                metric_type=MetricType.AUTHENTICITY,
                raw_score=50.0,
                normalized_score=-0.1,
                sub_scores={},
                evidence_count=0,
            )

    def test_evidence_count_below_0_rejected(self):
        with pytest.raises(ValidationError):
            MetricScore(
                metric_type=MetricType.LOGIC,
                raw_score=50.0,
                normalized_score=50.0,
                sub_scores={},
                evidence_count=-1,
            )

    def test_boundary_values_accepted(self):
        """0.0 and 100.0 are valid edge values."""
        score_zero = MetricScore(
            metric_type=MetricType.LOGIC,
            raw_score=0.0,
            normalized_score=0.0,
            sub_scores={},
            evidence_count=0,
        )
        assert score_zero.raw_score == pytest.approx(0.0)

        score_max = MetricScore(
            metric_type=MetricType.MASTERY,
            raw_score=100.0,
            normalized_score=100.0,
            sub_scores={},
            evidence_count=10,
        )
        assert score_max.raw_score == pytest.approx(100.0)

    def test_all_metric_types(self):
        for mt in MetricType:
            score = make_metric_score(metric_type=mt)
            assert score.metric_type == mt

    def test_empty_sub_scores_allowed(self):
        score = MetricScore(
            metric_type=MetricType.LOGIC,
            raw_score=50.0,
            normalized_score=50.0,
            sub_scores={},
            evidence_count=0,
        )
        assert score.sub_scores == {}


# ---------------------------------------------------------------------------
# MetricType enum tests
# ---------------------------------------------------------------------------


class TestMetricType:
    def test_enum_values(self):
        assert MetricType.LOGIC == "logic"
        assert MetricType.MASTERY == "mastery"
        assert MetricType.STABILITY == "stability"
        assert MetricType.AUTHENTICITY == "authenticity"


# ---------------------------------------------------------------------------
# ScoreConfidence enum tests
# ---------------------------------------------------------------------------


class TestScoreConfidence:
    def test_enum_values(self):
        assert ScoreConfidence.HIGH == "high"
        assert ScoreConfidence.MEDIUM == "medium"
        assert ScoreConfidence.LOW == "low"


# ---------------------------------------------------------------------------
# calculate_weighted_score tests
# ---------------------------------------------------------------------------


class TestCalculateWeightedScore:
    def test_default_weights_equal_scores(self):
        """All 4 metrics at 80.0 → weighted_total == 80.0."""
        metrics = make_all_metrics(score=80.0)
        result = calculate_weighted_score(metrics)
        assert isinstance(result, CandidateScore)
        assert result.weighted_total == pytest.approx(80.0)

    def test_all_zeros(self):
        """All 4 metrics at 0.0 → weighted_total == 0.0."""
        metrics = make_all_metrics(score=0.0)
        result = calculate_weighted_score(metrics)
        assert result.weighted_total == pytest.approx(0.0)

    def test_all_perfect(self):
        """All 4 metrics at 100.0 → weighted_total == 100.0."""
        metrics = make_all_metrics(score=100.0)
        result = calculate_weighted_score(metrics)
        assert result.weighted_total == pytest.approx(100.0)

    def test_weight_distribution(self):
        """
        LOGIC=100, MASTERY=0, STABILITY=0, AUTHENTICITY=0
        Expected: 100 * 0.30 = 30.0
        """
        metrics = {
            MetricType.LOGIC: make_metric_score(
                metric_type=MetricType.LOGIC, raw_score=100.0, normalized_score=100.0
            ),
            MetricType.MASTERY: make_metric_score(
                metric_type=MetricType.MASTERY, raw_score=0.0, normalized_score=0.0
            ),
            MetricType.STABILITY: make_metric_score(
                metric_type=MetricType.STABILITY, raw_score=0.0, normalized_score=0.0
            ),
            MetricType.AUTHENTICITY: make_metric_score(
                metric_type=MetricType.AUTHENTICITY, raw_score=0.0, normalized_score=0.0
            ),
        }
        result = calculate_weighted_score(metrics)
        assert result.weighted_total == pytest.approx(30.0)

    def test_mastery_weight_only(self):
        """
        LOGIC=0, MASTERY=100, STABILITY=0, AUTHENTICITY=0
        Expected: 100 * 0.30 = 30.0
        """
        metrics = {
            MetricType.LOGIC: make_metric_score(
                metric_type=MetricType.LOGIC, raw_score=0.0, normalized_score=0.0
            ),
            MetricType.MASTERY: make_metric_score(
                metric_type=MetricType.MASTERY, raw_score=100.0, normalized_score=100.0
            ),
            MetricType.STABILITY: make_metric_score(
                metric_type=MetricType.STABILITY, raw_score=0.0, normalized_score=0.0
            ),
            MetricType.AUTHENTICITY: make_metric_score(
                metric_type=MetricType.AUTHENTICITY, raw_score=0.0, normalized_score=0.0
            ),
        }
        result = calculate_weighted_score(metrics)
        assert result.weighted_total == pytest.approx(30.0)

    def test_stability_weight_only(self):
        """
        LOGIC=0, MASTERY=0, STABILITY=100, AUTHENTICITY=0
        Expected: 100 * 0.20 = 20.0
        """
        metrics = {
            MetricType.LOGIC: make_metric_score(
                metric_type=MetricType.LOGIC, raw_score=0.0, normalized_score=0.0
            ),
            MetricType.MASTERY: make_metric_score(
                metric_type=MetricType.MASTERY, raw_score=0.0, normalized_score=0.0
            ),
            MetricType.STABILITY: make_metric_score(
                metric_type=MetricType.STABILITY, raw_score=100.0, normalized_score=100.0
            ),
            MetricType.AUTHENTICITY: make_metric_score(
                metric_type=MetricType.AUTHENTICITY, raw_score=0.0, normalized_score=0.0
            ),
        }
        result = calculate_weighted_score(metrics)
        assert result.weighted_total == pytest.approx(20.0)

    def test_authenticity_weight_only(self):
        """
        LOGIC=0, MASTERY=0, STABILITY=0, AUTHENTICITY=100
        Expected: 100 * 0.20 = 20.0
        """
        metrics = {
            MetricType.LOGIC: make_metric_score(
                metric_type=MetricType.LOGIC, raw_score=0.0, normalized_score=0.0
            ),
            MetricType.MASTERY: make_metric_score(
                metric_type=MetricType.MASTERY, raw_score=0.0, normalized_score=0.0
            ),
            MetricType.STABILITY: make_metric_score(
                metric_type=MetricType.STABILITY, raw_score=0.0, normalized_score=0.0
            ),
            MetricType.AUTHENTICITY: make_metric_score(
                metric_type=MetricType.AUTHENTICITY, raw_score=100.0, normalized_score=100.0
            ),
        }
        result = calculate_weighted_score(metrics)
        assert result.weighted_total == pytest.approx(20.0)

    def test_weights_sum_to_100(self):
        """Verify all weights contribute correctly: 0.30+0.30+0.20+0.20 = 1.0."""
        metrics = {
            MetricType.LOGIC: make_metric_score(
                metric_type=MetricType.LOGIC, raw_score=100.0, normalized_score=100.0
            ),
            MetricType.MASTERY: make_metric_score(
                metric_type=MetricType.MASTERY, raw_score=100.0, normalized_score=100.0
            ),
            MetricType.STABILITY: make_metric_score(
                metric_type=MetricType.STABILITY, raw_score=100.0, normalized_score=100.0
            ),
            MetricType.AUTHENTICITY: make_metric_score(
                metric_type=MetricType.AUTHENTICITY, raw_score=100.0, normalized_score=100.0
            ),
        }
        result = calculate_weighted_score(metrics)
        # 100*0.30 + 100*0.30 + 100*0.20 + 100*0.20 = 100.0
        assert result.weighted_total == pytest.approx(100.0)

    def test_mixed_scores(self):
        """
        LOGIC=60, MASTERY=80, STABILITY=40, AUTHENTICITY=100
        Expected: 60*0.30 + 80*0.30 + 40*0.20 + 100*0.20
               = 18 + 24 + 8 + 20 = 70.0
        """
        metrics = {
            MetricType.LOGIC: make_metric_score(
                metric_type=MetricType.LOGIC, raw_score=60.0, normalized_score=60.0
            ),
            MetricType.MASTERY: make_metric_score(
                metric_type=MetricType.MASTERY, raw_score=80.0, normalized_score=80.0
            ),
            MetricType.STABILITY: make_metric_score(
                metric_type=MetricType.STABILITY, raw_score=40.0, normalized_score=40.0
            ),
            MetricType.AUTHENTICITY: make_metric_score(
                metric_type=MetricType.AUTHENTICITY, raw_score=100.0, normalized_score=100.0
            ),
        }
        result = calculate_weighted_score(metrics)
        assert result.weighted_total == pytest.approx(70.0)

    def test_missing_metric_raises_value_error(self):
        """If any of the 4 metrics is missing, ValueError is raised."""
        metrics = {
            MetricType.LOGIC: make_metric_score(metric_type=MetricType.LOGIC),
            MetricType.MASTERY: make_metric_score(metric_type=MetricType.MASTERY),
            MetricType.STABILITY: make_metric_score(metric_type=MetricType.STABILITY),
            # AUTHENTICITY intentionally missing
        }
        with pytest.raises(ValueError, match="authenticity"):
            calculate_weighted_score(metrics)

    def test_missing_logic_raises_value_error(self):
        metrics = {
            MetricType.MASTERY: make_metric_score(metric_type=MetricType.MASTERY),
            MetricType.STABILITY: make_metric_score(metric_type=MetricType.STABILITY),
            MetricType.AUTHENTICITY: make_metric_score(metric_type=MetricType.AUTHENTICITY),
        }
        with pytest.raises(ValueError, match="logic"):
            calculate_weighted_score(metrics)

    def test_empty_metrics_raises_value_error(self):
        with pytest.raises(ValueError):
            calculate_weighted_score({})

    def test_result_metric_fields_preserved(self):
        """CandidateScore fields reference the original MetricScore objects."""
        metrics = make_all_metrics(score=70.0)
        result = calculate_weighted_score(metrics)
        assert result.logic.metric_type == MetricType.LOGIC
        assert result.mastery.metric_type == MetricType.MASTERY
        assert result.stability.metric_type == MetricType.STABILITY
        assert result.authenticity.metric_type == MetricType.AUTHENTICITY

    def test_weighted_total_within_0_100(self):
        """weighted_total is always in [0, 100]."""
        metrics = make_all_metrics(score=50.0)
        result = calculate_weighted_score(metrics)
        assert 0.0 <= result.weighted_total <= 100.0


# ---------------------------------------------------------------------------
# determine_confidence tests
# ---------------------------------------------------------------------------


class TestDetermineConfidence:
    # --- HIGH ---
    def test_high_confidence(self):
        """sources >= 3 AND repos >= 5 → HIGH."""
        assert determine_confidence(data_source_count=3, public_repo_count=5) == ScoreConfidence.HIGH

    def test_high_confidence_above_minimums(self):
        assert determine_confidence(data_source_count=5, public_repo_count=10) == ScoreConfidence.HIGH

    def test_high_confidence_exact_boundary(self):
        """Exactly 3 sources and 5 repos → HIGH."""
        assert determine_confidence(data_source_count=3, public_repo_count=5) == ScoreConfidence.HIGH

    # --- MEDIUM ---
    def test_medium_confidence(self):
        """sources >= 2 AND repos >= 2 → MEDIUM (when not HIGH)."""
        assert determine_confidence(data_source_count=2, public_repo_count=2) == ScoreConfidence.MEDIUM

    def test_medium_confidence_sources_3_repos_4(self):
        """sources=3, repos=4 → MEDIUM (repos < 5, fails HIGH)."""
        assert determine_confidence(data_source_count=3, public_repo_count=4) == ScoreConfidence.MEDIUM

    def test_medium_confidence_sources_2_repos_many(self):
        """sources=2, repos=100 → MEDIUM (sources < 3, fails HIGH)."""
        assert determine_confidence(data_source_count=2, public_repo_count=100) == ScoreConfidence.MEDIUM

    def test_medium_exact_boundary(self):
        """sources=2 AND repos=2 → MEDIUM."""
        assert determine_confidence(data_source_count=2, public_repo_count=2) == ScoreConfidence.MEDIUM

    # --- LOW ---
    def test_low_confidence_zero_sources(self):
        assert determine_confidence(data_source_count=0, public_repo_count=0) == ScoreConfidence.LOW

    def test_low_confidence_one_source_many_repos(self):
        """sources=1, repos=100 → LOW (sources < 2)."""
        assert determine_confidence(data_source_count=1, public_repo_count=100) == ScoreConfidence.LOW

    def test_low_confidence_many_sources_zero_repos(self):
        """sources=10, repos=0 → LOW (repos < 2, fails MEDIUM)."""
        assert determine_confidence(data_source_count=10, public_repo_count=0) == ScoreConfidence.LOW

    def test_low_confidence_many_sources_one_repo(self):
        """sources=5, repos=1 → LOW (repos < 2, fails MEDIUM)."""
        assert determine_confidence(data_source_count=5, public_repo_count=1) == ScoreConfidence.LOW

    def test_low_confidence_sources_2_repos_1(self):
        """sources=2, repos=1 → LOW (repos < 2)."""
        assert determine_confidence(data_source_count=2, public_repo_count=1) == ScoreConfidence.LOW

    def test_low_confidence_one_source_one_repo(self):
        assert determine_confidence(data_source_count=1, public_repo_count=1) == ScoreConfidence.LOW

    def test_edge_case_high_sources_zero_repos(self):
        """Many sources but 0 repos → LOW (repos < 2)."""
        assert determine_confidence(data_source_count=100, public_repo_count=0) == ScoreConfidence.LOW
