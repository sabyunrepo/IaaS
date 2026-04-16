"""Application API 스키마 — 요청/응답 Pydantic 모델."""

from pydantic import BaseModel, Field


class ApplicationCreateRequest(BaseModel):
    """지원 생성 요청 (관리자)."""

    candidate_name: str | None = None
    candidate_email: str | None = None
    github_username: str | None = None
    github_urls: list[str] = Field(default_factory=list)
    linkedin_url: str | None = None
    resume_path: str | None = None
    cover_letter_path: str | None = None
    portfolio_path: str | None = None
    memo: str | None = None


class ApplicationUpdateRequest(BaseModel):
    """지원 수정 요청."""

    candidate_name: str | None = None
    candidate_email: str | None = None
    github_username: str | None = None
    github_urls: list[str] | None = None
    linkedin_url: str | None = None
    resume_path: str | None = None
    cover_letter_path: str | None = None
    portfolio_path: str | None = None
    memo: str | None = None
    status: str | None = None


class ApplicationResponse(BaseModel):
    """지원 응답."""

    id: str
    posting_id: str
    candidate_name: str | None = None
    candidate_email: str | None = None
    github_username: str | None = None
    github_urls: list[str] = Field(default_factory=list)
    linkedin_url: str | None = None
    resume_path: str | None = None
    cover_letter_path: str | None = None
    portfolio_path: str | None = None
    memo: str | None = None
    source: str = "admin_manual"
    status: str = "pending"
    job_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class PublicApplyRequest(BaseModel):
    """지원자 직접 지원 요청 (public)."""

    candidate_name: str = Field(..., min_length=1, max_length=200)
    candidate_email: str = Field(..., min_length=1, max_length=200)
    github_username: str | None = None
    github_urls: list[str] = Field(default_factory=list)
    linkedin_url: str | None = None
    resume_path: str | None = None
    cover_letter_path: str | None = None
    portfolio_path: str | None = None


class PublicApplyResponse(BaseModel):
    """지원 완료 응답."""

    application_id: str
    message: str = "지원이 완료되었습니다."
