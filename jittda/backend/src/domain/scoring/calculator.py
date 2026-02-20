"""
Scoring Calculator

4대 지표 가중 합산으로 CandidateScore를 생성한다.

가중치:
  LOGIC        30%
  MASTERY      30%
  STABILITY    20%
  AUTHENTICITY 20%

외부 의존성 없음 — 순수 도메인 로직.
"""
from domain.scoring.models import (
    CandidateScore,
    MetricScore,
    MetricType,
    ScoreConfidence,
)

# 지표별 가중치 (합계 = 1.0)
WEIGHTS: dict[MetricType, float] = {
    MetricType.LOGIC: 0.30,
    MetricType.MASTERY: 0.30,
    MetricType.STABILITY: 0.20,
    MetricType.AUTHENTICITY: 0.20,
}


def calculate_weighted_score(
    scores: dict[MetricType, MetricScore],
) -> CandidateScore:
    """
    4대 지표 MetricScore를 받아 가중 합산된 CandidateScore를 반환한다.

    Args:
        scores: MetricType → MetricScore 매핑. 4개 지표 모두 필수.

    Returns:
        CandidateScore: 가중 합산 점수 + 기본 신뢰도(LOW) 포함 종합 점수.
            신뢰도는 별도 determine_confidence() 호출로 갱신해야 한다.

    Raises:
        ValueError: 4개 지표 중 하나라도 누락된 경우.
    """
    # 누락 지표 검증
    for metric_type in MetricType:
        if metric_type not in scores:
            raise ValueError(
                f"Missing required metric: '{metric_type}'. "
                f"All 4 metrics (logic, mastery, stability, authenticity) must be provided."
            )

    # 가중 합산: normalized_score 기준
    weighted_total = sum(
        scores[metric_type].normalized_score * weight
        for metric_type, weight in WEIGHTS.items()
    )

    return CandidateScore(
        logic=scores[MetricType.LOGIC],
        mastery=scores[MetricType.MASTERY],
        stability=scores[MetricType.STABILITY],
        authenticity=scores[MetricType.AUTHENTICITY],
        weighted_total=round(weighted_total, 10),  # 부동소수점 누적 오차 최소화
        confidence=ScoreConfidence.LOW,  # 신뢰도는 determine_confidence()로 별도 설정
    )
