"""
Scoring 도메인 모델

4대 지표(Logic/Mastery/Stability/Authenticity) 기반 후보자 점수 모델.
순수 Pydantic v2 모델 — 외부 의존성 없음 (pydantic만 허용).
모든 데이터는 strict=True로 타입 안전성을 보장.
"""
from enum import StrEnum

from pydantic import BaseModel, Field


class MetricType(StrEnum):
    """4대 평가 지표 유형."""

    LOGIC = "logic"              # 로직 복잡도 — 30%
    MASTERY = "mastery"          # 기술 숙련도 — 30%
    STABILITY = "stability"      # 코드 안정성 — 20%
    AUTHENTICITY = "authenticity"  # 기여 진정성 — 20%


class ScoreConfidence(StrEnum):
    """점수 신뢰도 수준."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MetricScore(BaseModel, strict=True):
    """
    단일 지표 점수.

    raw_score: 원본 계산값 (0~100).
    normalized_score: 정규화 후 최종값 (0~100).
    sub_scores: 세부 항목별 점수 딕셔너리.
    evidence_count: 점수 산정에 사용된 증거 수.
    """

    metric_type: MetricType
    raw_score: float = Field(ge=0, le=100)
    normalized_score: float = Field(ge=0, le=100)
    sub_scores: dict[str, float]
    evidence_count: int = Field(ge=0)


class CandidateScore(BaseModel, strict=True):
    """
    후보자 종합 점수.

    4대 지표 MetricScore + 가중 합산 점수 + 신뢰도.
    """

    logic: MetricScore
    mastery: MetricScore
    stability: MetricScore
    authenticity: MetricScore
    weighted_total: float = Field(ge=0, le=100)
    confidence: ScoreConfidence
