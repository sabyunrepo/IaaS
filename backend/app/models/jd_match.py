"""
backend/app/models/jd_match.py
JD 매칭 결과 모델 — 후보자 프로필 vs JD 매칭

JD Matching Layer의 출력 모델.
같은 프로필에 다른 JD를 적용하면 다른 매칭 결과가 나옴.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class SkillMatchDetail(BaseModel):
    """개별 스킬 매칭 상세"""
    jd_skill: str                  # JD 요구 스킬 (원본)
    jd_canonical: str              # 정규화된 canonical
    candidate_skill: str | None = None  # 매칭된 후보자 스킬
    match_type: str = "none"       # "exact" | "semantic" | "implied" | "none"
    category: str = "우대"         # "필수" | "우대"
    confidence: float = 0.0


class SkillMatchResult(BaseModel):
    """스킬 매칭 결과 요약"""
    matched: list[SkillMatchDetail] = Field(default_factory=list)
    gaps: list[dict] = Field(default_factory=list)
    overlap_score: float = 0.0     # 가중 매칭 비율 (0.0-1.0)
    total_jd_skills: int = 0
    matched_count: int = 0
    gap_count: int = 0


class CandidateJDMatch(BaseModel):
    """후보자-JD 매칭 결과 (사전계산)"""

    # 매칭 점수
    overall_match_score: float = 0.0     # 0-100
    skill_match_score: float = 0.0       # 0-100

    # 스킬 매칭 상세
    skill_matches: SkillMatchResult = Field(default_factory=SkillMatchResult)

    # 레이더 차트 점수
    radar_scores: dict = Field(default_factory=dict)

    # 갭 분석
    gaps: list[dict] = Field(default_factory=list)

    # 근거 설명
    match_explanation: str = ""

    # 채용 추천
    hiring_recommendation: str = "보류"  # 강력추천/추천/보류/비추천
    recommendation_confidence: str = "medium"

    # 메타
    confidence_level: str = "medium"     # "high" | "medium" | "low"

    # Quick match 결과 (경량 Intel/Analysis/Decision)
    intel_summary: dict | None = None
    analysis_summary: dict | None = None
    decision_summary: dict | None = None
