"""
backend/app/models/decision.py
Decision 탭 데이터 모델
"""
from pydantic import BaseModel, Field


class DecisionSummary(BaseModel):
    """채용 판단 요약

    experience/jd_match/level은 IntelBrief candidate에서 원본 표시 (GitHub #270).
    백엔드 일관성 검증용으로 유지하되, 프론트엔드 Decision 탭에서는 미표시.
    """
    experience: str = ""
    jd_match: str = ""
    level: str = ""
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
    """면접관 가이드 팁 (JIT-14/16: interview_flow, time_allocation, positive_signals 제거)"""
    resume_based_tips: list[ResumeTip] = Field(default_factory=list)
    cover_letter_insights: list[CoverLetterInsight] = Field(default_factory=list)
    red_flags_to_watch: list[str] = Field(default_factory=list)


class JDCompetencyWeight(BaseModel):
    """JD 역량 가중치"""
    competency: str
    weight: float
    related_questions: list[int] = Field(default_factory=list)


class KGEvidence(BaseModel):
    """Knowledge Graph 기반 분석 근거"""
    conflicts: list[str] = Field(default_factory=list)   # KG에서 발견된 모순/주의점
    gaps: list[str] = Field(default_factory=list)          # KG에서 발견된 스킬 갭
    conflict_count: int = 0
    gap_count: int = 0


class DecisionSupport(BaseModel):
    """Decision 탭 데이터"""
    summary: DecisionSummary
    interviewer_guide: InterviewerGuideTips
    jd_competency_map: list[JDCompetencyWeight] = Field(default_factory=list)
    kg_evidence: KGEvidence | None = None  # Knowledge Graph 근거 (있는 경우)
