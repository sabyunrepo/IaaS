"""
backend/app/models/question.py
질문 및 면접 스크립트 모델
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .enums import QuestionCategory
from .types import Difficulty


# --- 용어 ---

class TerminologyEntry(BaseModel):
    """기술 용어 설명 (비개발자 친화)"""
    term: str
    definition: str
    plain_language_explanation: str = ""
    context: str = ""
    # v2 추가 필드 (optional for backward compatibility)
    pronunciation: str | None = None
    explanation: str | None = None
    plain_language: str | None = None


# --- 키워드 & 채점 ---

class AnswerKeyword(BaseModel):
    keyword: str
    importance: Literal["must", "good_to_have"]
    explanation: str


# --- v2 꼬리질문 응답 ---

class FollowUpResponse(BaseModel):
    """꼬리질문 응답 (v2)"""
    text: str
    score: int


class FollowUpScoring(BaseModel):
    """꼬리질문 채점 (v1 호환)"""
    good: str
    good_score: int
    poor: str
    poor_score: int


class FollowUpQuestion(BaseModel):
    """꼬리질문"""
    id: str
    # v1: trigger_level, v2: trigger (둘 다 지원)
    trigger_level: Literal["expert", "mid", "low", "any"] | None = None
    trigger: Literal["Expert", "Mid", "Low", "any"] | None = None  # v2 format
    question_text: str
    why_matters: str
    listen_for: str
    # v1 format
    scoring: FollowUpScoring | None = None
    # v2 format (개별 good/poor 객체)
    good: FollowUpResponse | None = None
    poor: FollowUpResponse | None = None
    terminology: list[TerminologyEntry] = Field(default_factory=list)


# --- 코드 참조 ---

class CodeReference(BaseModel):
    repo_name: str
    file_path: str
    line_range: str
    permalink: str
    snippet: str
    explanation: str
    plain_language_summary: str


class CodeEvidence(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    explanation: str


# --- 예상 답변 ---

class ExpectedAnswer(BaseModel):
    # v1 fields
    core_answer: str = ""
    example_script: str = ""
    answer_keywords: list[AnswerKeyword] = Field(default_factory=list)
    depth_expectations: dict[str, str] = Field(default_factory=dict)
    code_evidence: list[CodeEvidence] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    # v2 fields
    core: str | None = None  # v2 alias for core_answer
    example: str | None = None  # v2 alias for example_script


# --- 평가 시나리오 ---

class EvaluationScenarioLevel(BaseModel):
    """v1 평가 시나리오 레벨"""
    description: str
    indicators: list[str] = Field(default_factory=list)
    score: int


class EvaluationScenario(BaseModel):
    """v1 평가 시나리오 (expert/mid/low 객체)"""
    expert: EvaluationScenarioLevel
    mid: EvaluationScenarioLevel
    low: EvaluationScenarioLevel


# --- v2 시나리오 배열 ---

class ScenarioLevel(BaseModel):
    """v2 시나리오 레벨 (배열 형태)"""
    level: Literal["Expert", "Mid", "Low"]
    score: int
    text: str
    depth_expectations: str = ""


# --- 면접관 노트 ---

class InterviewerNote(BaseModel):
    business_interpretation: str
    daily_analogy: str
    level_expectations: dict[str, str] | None = None
    level_expectation: str | None = None  # v2 단일 문자열


# --- JD 역량 매핑 ---

class JDCompetencyMapping(BaseModel):
    competency: str
    jd_original_text: str
    why_important: str
    related_questions: list[str] = Field(default_factory=list)
    assessment_weight: float


# --- 면접 질문 ---

class InterviewQuestion(BaseModel):
    """면접 질문 (최종 모델) - v1/v2 호환"""
    id: str | int  # v2는 int 사용
    sequence: int = 0
    category: QuestionCategory | str  # v2는 string category
    topic: str = ""
    difficulty: Difficulty | str  # v2는 string difficulty (Easy/Medium/Hard)

    # v2 추가 필드
    title: str = ""  # 짧은 제목 (예: "첫 90일 우선순위")
    is_risk: bool = False  # 위험 신호 검증 질문 여부

    question_text: str
    context_bridge: str = ""
    alternative_phrasings: list[str] = Field(default_factory=list)

    why_matters: str
    listen_for: str

    code_reference: CodeReference | None = None

    # v1: evaluation_scenarios (객체)
    evaluation_scenarios: EvaluationScenario | None = None
    # v2: scenarios (배열)
    scenarios: list[ScenarioLevel] = Field(default_factory=list)

    # v2: 질문 레벨 answer_keywords
    answer_keywords: list[AnswerKeyword] = Field(default_factory=list)

    follow_ups: list[FollowUpQuestion] = Field(default_factory=list)
    expected_answer: ExpectedAnswer | None = None
    terminology: list[TerminologyEntry] = Field(default_factory=list)

    language: str = "ko"
    estimated_time_minutes: int = 5
    skills_assessed: list[str] = Field(default_factory=list)
    interviewer_note: InterviewerNote | None = None
    generation_rationale: str = ""
    jd_competency_link: str = ""


# --- 최종 출력 ---

class CandidateSummary(BaseModel):
    name: str
    experience_level: str = ""
    experience_years: int = 0
    key_skills: list[str] = Field(default_factory=list)
    jd_match_score: float = 0.0
    strengths: list[str] = Field(default_factory=list)
    areas_to_probe: list[str] = Field(default_factory=list)
    # v2 추가 필드
    initials: str = ""
    role: str = ""
    company_context: str = ""
    experience: str = ""  # v2 문자열 형태 (예: "7년")
    jd_match: str = ""  # v2 문자열 형태 (예: "78%")
    level: str = ""
    current_title: str = ""


class InterviewerGuide(BaseModel):
    total_duration_minutes: int = 60
    question_order_rationale: str = ""
    tips: list[str] = Field(default_factory=list)
    warning_signs: list[str] = Field(default_factory=list)


# --- v2 Import ---
# IntelBrief, DeepAnalysis, DecisionSupport are imported from separate modules
# to avoid circular imports and keep this file clean


class InterviewScript(BaseModel):
    """최종 면접 스크립트 - v1/v2 호환"""
    job_id: str
    generated_at: datetime
    output_language: str
    candidate_summary: CandidateSummary
    questions: list[InterviewQuestion] = Field(default_factory=list)
    interviewer_guide: InterviewerGuide
    decision_guide: dict[str, Any] = Field(default_factory=dict)
    full_glossary: list[TerminologyEntry] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # v2 추가 필드 (Optional for backward compatibility)
    candidate: CandidateSummary | None = None  # v2 alias
    intel: Any | None = None  # IntelBrief
    analysis: Any | None = None  # DeepAnalysis
    decision: Any | None = None  # DecisionSupport
    category_weights: dict[str, float] | None = None
