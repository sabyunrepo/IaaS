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
