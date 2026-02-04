"""
backend/app/models/intel.py
Intel Brief 탭 데이터 모델
"""
from typing import Literal

from pydantic import BaseModel, Field


class RequirementMatch(BaseModel):
    """JD 요구사항 매칭"""
    text: str
    desc: str
    matched: bool


class JDSummary(BaseModel):
    """JD 요약"""
    title: str
    subtitle: str
    requirements: list[RequirementMatch] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)


class CompetencyMatch(BaseModel):
    """JD 역량 vs 후보자 매칭"""
    name: str
    match: Literal["strong", "match", "partial", "unknown", "none"]
    match_label: str
    desc: str  # 비개발자용 설명
    why: str  # 왜 필요한가
    color: Literal["emerald", "amber", "red", "blue", "slate"]
    icon: str  # ✅/⚠️/❌


class LinkedInPosition(BaseModel):
    """LinkedIn 경력 항목"""
    initial: str
    title: str
    company: str
    detail: str


class GitHubSummary(BaseModel):
    """GitHub 기여 활동 요약"""
    contributions: int
    repos: int
    main_languages: str
    tech_match: str
    tech_match_note: str
    tenure_pattern: str
    tenure_note: str
    activity_gap: str | None = None
    chart_data: list[int] = Field(default_factory=list)  # 12개월 기여도 데이터


class IntelBrief(BaseModel):
    """Intel Brief 탭 데이터"""
    jd_summary: JDSummary
    jd_full: str | None = None  # JD 원문 HTML
    competencies: list[CompetencyMatch] = Field(default_factory=list)
    github: GitHubSummary | None = None
    linkedin: list[LinkedInPosition] = Field(default_factory=list)
    linkedin_warning: str | None = None
