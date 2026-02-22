"""Posting Domain Models — Pydantic v2 immutable."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PostingStatus(str, Enum):
    draft = "draft"
    active = "active"
    closed = "closed"


class ApplicationStatus(str, Enum):
    pending = "pending"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"


class ApplicationSource(str, Enum):
    self_apply = "self_apply"
    admin_manual = "admin_manual"


class UploaderType(str, Enum):
    admin = "admin"
    candidate = "candidate"


class FileType(str, Enum):
    resume = "resume"
    cover_letter = "cover_letter"
    portfolio = "portfolio"


class Posting(BaseModel):
    """채용 공고."""

    model_config = ConfigDict(frozen=True)

    id: str
    user_id: str
    title: str
    department: str | None = None
    jd_description: str | None = None
    jd_languages: list[str] = Field(default_factory=list)
    jd_tech_stack: list[str] = Field(default_factory=list)
    jd_experience_years: int | None = None
    auto_analyze: bool = False
    status: PostingStatus = PostingStatus.draft
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Application(BaseModel):
    """지원."""

    model_config = ConfigDict(frozen=True)

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
    source: ApplicationSource = ApplicationSource.admin_manual
    status: ApplicationStatus = ApplicationStatus.pending
    job_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FileUpload(BaseModel):
    """파일 업로드 메타데이터."""

    model_config = ConfigDict(frozen=True)

    id: str
    uploader_type: UploaderType
    uploader_ref: str | None = None
    file_type: FileType
    file_name: str
    file_path: str
    content_type: str | None = None
    size_bytes: int | None = None
    created_at: datetime | None = None
