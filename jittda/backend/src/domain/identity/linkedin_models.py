"""
LinkedIn 프로필 도메인 모델

순수 Pydantic v2 모델 — 외부 의존성 없음 (pydantic만 허용).
strict=True로 타입 안전성을 보장하며, BrightData raw JSON 정규화 후 사용.
"""
from pydantic import BaseModel, Field


class LinkedInExperience(BaseModel, strict=True):
    """LinkedIn 경력 항목."""

    company: str
    title: str
    duration_months: int = Field(ge=0)
    start_date: str | None = None   # "YYYY-MM"
    end_date: str | None = None     # "YYYY-MM", None = 현재 재직 중
    description: str = ""
    location: str | None = None
    is_current: bool = False


class LinkedInEducation(BaseModel, strict=True):
    """LinkedIn 학력 항목."""

    school: str
    degree: str | None = None
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class LinkedInSkill(BaseModel, strict=True):
    """LinkedIn 스킬 항목."""

    name: str
    endorsement_count: int = Field(ge=0, default=0)


class LinkedInCertification(BaseModel, strict=True):
    """LinkedIn 자격증 항목."""

    name: str
    issuer: str
    issue_date: str | None = None       # "YYYY-MM"
    credential_url: str | None = None


class LinkedInProfile(BaseModel, strict=True):
    """
    LinkedIn 프로필 전체.

    BrightData raw JSON을 normalize_linkedin_profile()로 정규화한 후
    이 모델로 표현한다.
    """

    name: str
    headline: str | None = None
    location: str | None = None
    summary: str = ""
    profile_url: str
    experiences: list[LinkedInExperience] = []
    educations: list[LinkedInEducation] = []
    skills: list[LinkedInSkill] = []
    certifications: list[LinkedInCertification] = []

    @property
    def total_experience_months(self) -> int:
        """모든 경력 duration_months 합계."""
        return sum(exp.duration_months for exp in self.experiences)

    @property
    def current_company(self) -> str | None:
        """현재 재직 중인 첫 번째 경력의 회사명. 없으면 None."""
        for exp in self.experiences:
            if exp.is_current:
                return exp.company
        return None
