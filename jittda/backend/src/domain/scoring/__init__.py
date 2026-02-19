"""
Scoring 도메인 패키지

4대 지표 가중 합산 점수 계산 + 신뢰도 판별.
"""
from domain.scoring.calculator import WEIGHTS, calculate_weighted_score
from domain.scoring.confidence import determine_confidence
from domain.scoring.models import (
    CandidateScore,
    MetricScore,
    MetricType,
    ScoreConfidence,
)

__all__ = [
    # 모델
    "MetricType",
    "ScoreConfidence",
    "MetricScore",
    "CandidateScore",
    # 계산기
    "WEIGHTS",
    "calculate_weighted_score",
    # 신뢰도
    "determine_confidence",
]
