"""
backend/app/models/candidate_profile.py
통합 후보자 프로필 모델 — JD-agnostic, 모든 소스 통합

Sources: 이력서, GitHub, LinkedIn, 커버레터
스킬: SkillNormalizer로 정규화 완료
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class UnifiedSkill(BaseModel):
    """정규화된 통합 스킬"""
    canonical_name: str               # taxonomy의 canonical
    aliases: list[str] = Field(default_factory=list)       # 원본 스킬명들 (중복 제거)
    sources: list[str] = Field(default_factory=list)       # ["resume", "github", "linkedin", "cover_letter"]
    category: str | None = None       # language/framework/tool/platform/concept
    domain: str | None = None         # frontend/backend/devops/ml/data
    confidence: float = 1.0           # 정규화 신뢰도
    proficiency_signals: dict = Field(default_factory=dict)   # {"github_repos": 5, "years_mentioned": 3}
    implied_skills: list[str] = Field(default_factory=list)   # taxonomy implies 관계


class UnifiedWorkExperience(BaseModel):
    """통합 경력 (이력서 + LinkedIn 병합)"""
    company: str
    position: str
    period: str
    location: str | None = None
    description: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    source: str = "resume"             # "resume" | "linkedin" | "merged"
    is_current: bool = False


class Education(BaseModel):
    """학력"""
    institution: str
    degree: str | None = None
    major: str | None = None
    graduation_year: int | None = None
    source: str = "resume"


class CodeProfile(BaseModel):
    """코드 프로필 (JD-agnostic — 전체 레포 분석 결과)"""
    total_repos_analyzed: int = 0
    total_commits: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    primary_languages: list[str] = Field(default_factory=list)
    frameworks_detected: list[str] = Field(default_factory=list)
    design_patterns: list[str] = Field(default_factory=list)
    avg_complexity: float = 0.0
    quality_metrics: dict = Field(default_factory=dict)
    notable_implementations: list[dict] = Field(default_factory=list)
    monthly_contributions: list[int] = Field(default_factory=list)
    repo_summaries: list[dict] = Field(default_factory=list)


class CoverLetterProfile(BaseModel):
    """커버레터 인사이트"""
    motivation: str | None = None          # 지원 동기
    key_strengths: list[str] = Field(default_factory=list)
    mentioned_skills: list[str] = Field(default_factory=list)
    cultural_fit_signals: list[str] = Field(default_factory=list)
    career_goals: str | None = None


class UnifiedCandidateProfile(BaseModel):
    """통합 후보자 프로필 — JD-agnostic, 모든 소스 병합"""

    # 기본 정보
    name: str
    email: str | None = None
    avatar_url: str | None = None
    linkedin_url: str | None = None
    github_username: str | None = None

    # 통합 스킬 (정규화 완료)
    skills: list[UnifiedSkill] = Field(default_factory=list)

    # 경력 (이력서 + LinkedIn 병합)
    work_history: list[UnifiedWorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)

    # 경력 연수 (계산값)
    experience_years: int = 0
    experience_level: str | None = None  # CTO/VP, 시니어, 미들, 주니어, 신입

    # 코드 프로필 (JD-agnostic)
    code_profile: CodeProfile | None = None

    # 커버레터 인사이트
    cover_letter_insights: CoverLetterProfile | None = None

    # LinkedIn 확장 데이터 (현재 미사용 → 활용)
    linkedin_activity_summary: str | None = None
    linkedin_projects: list[dict] = Field(default_factory=list)
    linkedin_honors: list[dict] = Field(default_factory=list)
    recommendations_count: int = 0

    # 탐색 포인트
    areas_to_probe: list[str] = Field(default_factory=list)

    # 메타
    data_sources: list[str] = Field(default_factory=list)   # ["resume", "github", "linkedin", "cover_letter"]
    data_completeness: float = 0.0      # 0.0-1.0
    confidence_level: str = "low"       # "high"/"medium"/"low"

    # 요약
    profile_summary: str | None = None  # LLM 생성 1-2문장 요약
