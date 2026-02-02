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
    plain_language_explanation: str
    context: str


# --- 키워드 & 채점 ---

class AnswerKeyword(BaseModel):
    keyword: str
    importance: Literal["must", "good_to_have"]
    explanation: str


class FollowUpScoring(BaseModel):
    good: str
    good_score: int
    poor: str
    poor_score: int


class FollowUpQuestion(BaseModel):
    """꼬리질문"""
    id: str
    trigger_level: Literal["expert", "mid", "low", "any"]
    question_text: str
    why_matters: str
    listen_for: str
    scoring: FollowUpScoring
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
    core_answer: str
    example_script: str
    answer_keywords: list[AnswerKeyword] = Field(default_factory=list)
    depth_expectations: dict[str, str] = Field(default_factory=dict)
    code_evidence: list[CodeEvidence] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)


# --- 평가 시나리오 ---

class EvaluationScenarioLevel(BaseModel):
    description: str
    indicators: list[str] = Field(default_factory=list)
    score: int


class EvaluationScenario(BaseModel):
    expert: EvaluationScenarioLevel
    mid: EvaluationScenarioLevel
    low: EvaluationScenarioLevel


# --- 면접관 노트 ---

class InterviewerNote(BaseModel):
    business_interpretation: str
    daily_analogy: str
    level_expectations: dict[str, str] | None = None


# --- JD 역량 매핑 ---

class JDCompetencyMapping(BaseModel):
    competency: str
    jd_original_text: str
    why_important: str
    related_questions: list[str] = Field(default_factory=list)
    assessment_weight: float


# --- 면접 질문 ---

class InterviewQuestion(BaseModel):
    """면접 질문 (최종 모델)"""
    id: str
    sequence: int
    category: QuestionCategory
    topic: str
    difficulty: Difficulty

    question_text: str
    context_bridge: str
    alternative_phrasings: list[str] = Field(default_factory=list)

    why_matters: str
    listen_for: str

    code_reference: CodeReference | None = None
    evaluation_scenarios: EvaluationScenario
    follow_ups: list[FollowUpQuestion] = Field(default_factory=list)
    expected_answer: ExpectedAnswer
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
    experience_level: str
    experience_years: int
    key_skills: list[str] = Field(default_factory=list)
    jd_match_score: float
    strengths: list[str] = Field(default_factory=list)
    areas_to_probe: list[str] = Field(default_factory=list)


class InterviewerGuide(BaseModel):
    total_duration_minutes: int
    question_order_rationale: str
    tips: list[str] = Field(default_factory=list)
    warning_signs: list[str] = Field(default_factory=list)


class InterviewScript(BaseModel):
    """최종 면접 스크립트"""
    job_id: str
    generated_at: datetime
    output_language: str
    candidate_summary: CandidateSummary
    questions: list[InterviewQuestion] = Field(default_factory=list)
    interviewer_guide: InterviewerGuide
    decision_guide: dict[str, Any] = Field(default_factory=dict)
    full_glossary: list[TerminologyEntry] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
