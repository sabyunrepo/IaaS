"""
Job API 스키마 — 요청/응답 Pydantic 모델.
"""
from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    """분석 Job 생성 요청."""

    candidate_username: str | None = None
    github_urls: list[str] = Field(default_factory=list)
    linkedin_url: str | None = None
    jd_languages: list[str] = Field(default_factory=list)
    jd_tech_stack: list[str] = Field(default_factory=list)
    jd_description: str | None = None


class JobResponse(BaseModel):
    """Job 응답."""

    id: str
    status: str
    progress: float


class JobDetailResponse(BaseModel):
    """Job 상세 응답."""

    id: str
    status: str
    progress: float
    input_data: dict | None = None
    result_data: dict | None = None
    error_message: str | None = None
