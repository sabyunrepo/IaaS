"""
backend/app/models/decision.py
Decision 탭 데이터 모델
"""
from pydantic import BaseModel, Field


class DecisionSummary(BaseModel):
    """후보자 요약"""
    experience: str
    jd_match: str
    level: str
    level_evidence: str = ""  # 레벨 분류 근거 (SFIA/Dreyfus 기준 + 데이터 출처)
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)


class ResumeTip(BaseModel):
    """이력서 기반 확인 포인트"""
    section: str
    insight: str
    question_link: str | None = None


class CoverLetterInsight(BaseModel):
    """커버레터 검증 포인트"""
    highlight: str
    interpretation: str
    follow_up_opportunity: str | None = None


class InterviewerGuideTips(BaseModel):
    """면접관 가이드 팁"""
    interview_flow: str
    time_allocation: dict[str, str] = Field(default_factory=dict)
    resume_based_tips: list[ResumeTip] = Field(default_factory=list)
    cover_letter_insights: list[CoverLetterInsight] = Field(default_factory=list)
    red_flags_to_watch: list[str] = Field(default_factory=list)
    positive_signals: list[str] = Field(default_factory=list)


class JDCompetencyWeight(BaseModel):
    """JD 역량 가중치"""
    competency: str
    weight: float
    related_questions: list[int] = Field(default_factory=list)


class DecisionSupport(BaseModel):
    """Decision 탭 데이터"""
    summary: DecisionSummary
    interviewer_guide: InterviewerGuideTips
    jd_competency_map: list[JDCompetencyWeight] = Field(default_factory=list)
