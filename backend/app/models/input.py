"""
backend/app/models/input.py
입력 데이터 모델
"""
from datetime import datetime
from typing import Literal
import uuid

from pydantic import BaseModel, Field, HttpUrl

from .types import ExperienceLevel


class LanguageConfig(BaseModel):
    """언어 설정"""
    output_language: str = Field("ko", description="출력 언어 코드")
    terminology_languages: list[str] = Field(
        default=["ko", "en"],
        description="용어집에 포함할 언어들",
    )


class InputData(BaseModel):
    """면접 스크립트 생성 요청 입력"""
    # 문서 입력
    resume_path: str | None = Field(None, description="이력서 파일 경로 (S3 key)")
    portfolio_path: str | None = Field(None, description="포트폴리오 파일 경로")
    cover_letter_path: str | None = Field(None, description="자기소개서/커버레터 파일 경로")

    # LinkedIn
    linkedin_url: str | None = Field(None, description="LinkedIn 프로필 URL")

    # GitHub
    github_urls: list[HttpUrl] = Field(default_factory=list, description="GitHub 레포 URL 목록")
    candidate_github_username: str | None = Field(None, description="후보자 GitHub 사용자명")

    # JD
    jd_text: str = Field(..., min_length=50, description="채용공고 텍스트")

    # 옵션
    experience_level: ExperienceLevel = Field(..., description="후보자 경험 레벨")
    language_config: LanguageConfig = Field(default_factory=LanguageConfig)
    max_questions: int = Field(25, ge=5, le=25, description="생성할 질문 수")
    include_expected_answers: bool = Field(True, description="예상 답변 포함 여부")
    focus_areas: list[str] | None = Field(None, description="집중할 기술 영역")


# --- LinkedIn 관련 ---

class LinkedInExperience(BaseModel):
    company: str
    title: str
    period: str
    location: str | None = None
    description: str | None = None


class LinkedInEducation(BaseModel):
    school: str
    degree: str | None = None
    field_of_study: str | None = None
    period: str | None = None


class LinkedInCertification(BaseModel):
    name: str
    issuing_organization: str | None = None
    issue_date: str | None = None


class LinkedInProfile(BaseModel):
    """Bright Data Web Scraper API 응답에서 추출한 LinkedIn 프로필"""
    full_name: str
    headline: str | None = None
    summary: str | None = None
    experiences: list[LinkedInExperience] = Field(default_factory=list)
    education: list[LinkedInEducation] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[LinkedInCertification] = Field(default_factory=list)
    github_url: str | None = None
    websites: list[str] = Field(default_factory=list)


# --- Enriched Input ---

class EnrichedInput(BaseModel):
    """Phase 0 Smart Input Extraction 결과"""
    raw_input: InputData
    github_urls: list[HttpUrl] = Field(default_factory=list)
    candidate_github_username: str | None = None
    linkedin_profile: LinkedInProfile | None = None
    extraction_sources: dict[str, list[str]] = Field(default_factory=dict)
    available_analyses: list[str] = Field(default_factory=list)


# --- Job Request/Response ---

class JobIdentifier(BaseModel):
    """작업 식별자"""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @staticmethod
    def create(user_id: str) -> "JobIdentifier":
        return JobIdentifier(user_id=user_id)


class CreateJobRequest(BaseModel):
    """Job 생성 API 요청"""
    input_data: InputData
    callback_url: str | None = Field(None, description="완료 시 호출할 웹훅 URL")
    priority: Literal["low", "normal", "high"] = "normal"


class CreateJobResponse(BaseModel):
    """Job 생성 API 응답"""
    job_id: str
    status: str
    estimated_time_seconds: int
    created_at: datetime
