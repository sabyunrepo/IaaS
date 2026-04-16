"""Posting API 스키마 — 요청/응답 Pydantic 모델."""

from pydantic import BaseModel, Field


class PostingCreateRequest(BaseModel):
    """공고 생성 요청."""

    title: str = Field(..., min_length=1, max_length=200)
    department: str | None = None
    jd_description: str | None = None
    jd_languages: list[str] = Field(default_factory=list)
    jd_tech_stack: list[str] = Field(default_factory=list)
    jd_experience_years: int | None = None
    auto_analyze: bool = False
    status: str = "draft"


class PostingUpdateRequest(BaseModel):
    """공고 수정 요청."""

    title: str | None = Field(None, min_length=1, max_length=200)
    department: str | None = None
    jd_description: str | None = None
    jd_languages: list[str] | None = None
    jd_tech_stack: list[str] | None = None
    jd_experience_years: int | None = None
    auto_analyze: bool | None = None
    status: str | None = None


class PostingResponse(BaseModel):
    """공고 응답."""

    id: str
    user_id: str
    title: str
    department: str | None = None
    jd_description: str | None = None
    jd_languages: list[str] = Field(default_factory=list)
    jd_tech_stack: list[str] = Field(default_factory=list)
    jd_experience_years: int | None = None
    auto_analyze: bool = False
    status: str = "draft"
    application_count: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class CompanyUpdateRequest(BaseModel):
    """회사 정보 수정 요청."""

    company_name: str | None = Field(None, max_length=100)
    company_slug: str | None = Field(None, max_length=50, pattern=r"^[a-z0-9-]+$")
    company_logo: str | None = None
    company_description: str | None = None


class CompanyResponse(BaseModel):
    """회사 정보 응답."""

    company_name: str | None = None
    company_slug: str | None = None
    company_logo: str | None = None
    company_description: str | None = None
