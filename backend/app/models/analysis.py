"""
backend/app/models/analysis.py
분석 결과 모델 (Phase 2)
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .types import Severity, MatchType, PatternType


# --- Candidate Profile (문서 분석) ---

class Education(BaseModel):
    institution: str
    degree: str
    major: str | None = None
    graduation_year: int | None = None


class WorkExperience(BaseModel):
    company: str
    position: str
    period: str
    description: str
    tech_stack: list[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str
    description: str
    role: str
    tech_stack: list[str] = Field(default_factory=list)
    period: str | None = None
    url: str | None = None


class CandidateProfile(BaseModel):
    """후보자 프로필 (문서 분석 결과)"""
    name: str
    email: str | None = None
    phone: str | None = None
    experience_years: int
    skills: list[str] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    work_history: list[WorkExperience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    summary: str
    source_files: list[str] = Field(default_factory=list)
    confidence_score: float


# --- Code Analysis ---

class CodePattern(BaseModel):
    pattern_type: PatternType
    name: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    explanation: str


class ComplexityMetrics(BaseModel):
    total_lines: int
    code_lines: int
    comment_lines: int
    avg_function_length: float
    max_function_length: int
    cyclomatic_complexity_avg: float


class QualityIssue(BaseModel):
    severity: Severity
    category: str
    message: str
    file_path: str
    line: int | None = None


class NotableImplementation(BaseModel):
    title: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    why_notable: str
    question_potential: float


class CandidateContribution(BaseModel):
    """후보자 기여도 (PyDriller)"""
    total_commits: int
    total_additions: int
    total_deletions: int
    avg_complexity: float
    files_modified: int
    analysis_period_years: int
    primary_file_types: list[str] = Field(default_factory=list)


class ASTFunction(BaseModel):
    name: str
    params: list[str] = Field(default_factory=list)
    return_type: str | None = None
    decorators: list[str] = Field(default_factory=list)
    complexity: int | None = None


class ASTClass(BaseModel):
    name: str
    bases: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    attributes: list[str] = Field(default_factory=list)


class ASTPattern(BaseModel):
    pattern_type: str
    name: str
    evidence: str


class ASTAnalysis(BaseModel):
    """AST 구조 분석 결과"""
    functions: list[ASTFunction] = Field(default_factory=list)
    classes: list[ASTClass] = Field(default_factory=list)
    patterns: list[ASTPattern] = Field(default_factory=list)
    imports: list[dict] = Field(default_factory=list)
    parser_used: str


class RepositoryAnalysis(BaseModel):
    """단일 레포지토리 분석 결과"""
    repo_url: str
    repo_name: str
    language: str
    language_ratio: float
    total_files: int
    analyzed_files: int
    candidate_contribution: CandidateContribution
    ast_analysis: ASTAnalysis | None = None
    tech_stack: list[str] = Field(default_factory=list)
    patterns: list[CodePattern] = Field(default_factory=list)
    complexity: ComplexityMetrics
    quality_issues: list[QualityIssue] = Field(default_factory=list)
    notable_implementations: list[NotableImplementation] = Field(default_factory=list)
    last_commit_date: datetime | None = None
    contributors_count: int = 0
    jd_match_score: float = 0.0


class CodeAnalysis(BaseModel):
    """전체 코드 분석 결과"""
    repositories: list[RepositoryAnalysis] = Field(default_factory=list)
    combined_tech_stack: list[str] = Field(default_factory=list)
    total_patterns: int = 0
    total_notable_implementations: int = 0
    top_question_candidates: list[NotableImplementation] = Field(default_factory=list)


# --- JD Analysis ---

class Requirement(BaseModel):
    category: Literal["필수", "우대"]
    skill: str
    detail: str | None = None
    experience_years: int | None = None


class SkillMatch(BaseModel):
    required_skill: str
    candidate_skill: str | None = None
    match_type: MatchType
    evidence: str | None = None
    confidence: float


class JDAnalysis(BaseModel):
    """채용공고 분석 결과"""
    job_title: str
    company_name: str | None = None
    requirements: list[Requirement] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    company_culture: list[str] = Field(default_factory=list)
    skill_matches: list[SkillMatch] = Field(default_factory=list)
    overall_match_score: float = 0.0
    gaps: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)


# =============================================================================
# HYBRID 3-Stage Multi-Agent 분석 스키마
# =============================================================================


class KeyFile(BaseModel):
    """Stage 1에서 선별된 핵심 파일"""
    path: str
    relevance_score: float = Field(ge=0.0, le=1.0, description="JD 기술 스택 매칭 점수")
    reason: str = Field(description="선별 이유")
    language: str | None = None
    complexity: int | None = None
    diff_preview: str | None = Field(default=None, max_length=500)


class OverviewAnalysisResult(BaseModel):
    """Stage 1: Overview Agent 분석 결과

    전체 diff를 분석하여 핵심 파일을 선별하고 기술 개요를 생성합니다.
    """
    key_files: list[KeyFile] = Field(
        default_factory=list,
        max_length=10,
        description="JD 매칭 핵심 파일 (최대 10개)"
    )
    tech_overview: str = Field(description="레포지토리 기술 스택 개요")
    candidate_strengths: list[str] = Field(
        default_factory=list,
        description="후보자 기술 강점 (초벌 분석)"
    )
    primary_languages: list[str] = Field(
        default_factory=list,
        description="주요 프로그래밍 언어"
    )
    frameworks_detected: list[str] = Field(
        default_factory=list,
        description="감지된 프레임워크/라이브러리"
    )


class DeepAnalysisResult(BaseModel):
    """Stage 2: Deep Analysis Agent 분석 결과 (단일 파일)

    핵심 파일의 심층 분석 결과입니다.
    """
    file_path: str
    patterns_found: list[str] = Field(
        default_factory=list,
        description="발견된 디자인 패턴"
    )
    algorithms_used: list[str] = Field(
        default_factory=list,
        description="사용된 알고리즘"
    )
    code_quality_score: float = Field(
        ge=0.0, le=1.0,
        description="코드 품질 점수 (0.0~1.0)"
    )
    quality_notes: str = Field(
        default="",
        description="코드 품질 관련 노트"
    )
    question_candidates: list[str] = Field(
        default_factory=list,
        description="면접 질문 후보"
    )
    notable_aspects: list[str] = Field(
        default_factory=list,
        description="주목할 만한 구현 측면"
    )
    complexity_assessment: str = Field(
        default="",
        description="복잡도 평가"
    )


class SynthesizedNotable(BaseModel):
    """종합된 주목할 만한 구현"""
    title: str
    description: str
    file_path: str
    code_snippet: str | None = None
    why_notable: str
    question_potential: float = Field(ge=0.0, le=1.0)
    related_patterns: list[str] = Field(default_factory=list)
    interview_angles: list[str] = Field(default_factory=list)


class SynthesisAnalysisResult(BaseModel):
    """Stage 3: Synthesis Agent 분석 결과

    Overview와 모든 Deep Analysis 결과를 종합합니다.
    """
    notable_implementations: list[SynthesizedNotable] = Field(
        default_factory=list,
        description="종합된 주목할 만한 구현 (우선순위 정렬)"
    )
    tech_stack: list[str] = Field(
        default_factory=list,
        description="종합된 기술 스택"
    )
    patterns: list[str] = Field(
        default_factory=list,
        description="발견된 디자인 패턴 (중복 제거)"
    )
    algorithms: list[str] = Field(
        default_factory=list,
        description="사용된 알고리즘 (중복 제거)"
    )
    quality_score: float = Field(
        ge=0.0, le=1.0,
        description="전체 코드 품질 점수"
    )
    quality_summary: str = Field(
        default="",
        description="코드 품질 종합 평가"
    )
    candidate_assessment: str = Field(
        default="",
        description="후보자 기술 역량 평가"
    )
    top_interview_questions: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="추천 면접 질문 (최대 10개)"
    )


class HybridAnalysisMetadata(BaseModel):
    """HYBRID 3-Stage 분석 메타데이터"""
    model_used: str = Field(description="사용된 LLM 모델")
    key_files_count: int = Field(ge=0, description="분석된 핵심 파일 수")
    deep_analyses_count: int = Field(ge=0, description="성공한 심층 분석 수")
    total_tokens_used: int | None = Field(default=None, description="총 토큰 사용량")
    analysis_duration_ms: int | None = Field(default=None, description="분석 소요 시간 (밀리초)")


class CodeAnalysisValidation(BaseModel):
    """코드 분석 결과 품질 검증"""
    valid: bool = Field(description="검증 통과 여부")
    issues: list[str] = Field(default_factory=list, description="발견된 문제점")
    suggestions: list[str] = Field(default_factory=list, description="재분석 시 제안사항")
    repo_name: str | None = Field(default=None, description="검증 대상 레포지토리")
