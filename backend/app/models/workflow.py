"""
backend/app/models/workflow.py
Temporal 워크플로우 상태 모델
"""
from datetime import datetime

from pydantic import BaseModel, Field

from .analysis import CandidateProfile, CodeAnalysis, JDAnalysis
from .checkpoint import PipelineStep
from .input import EnrichedInput, InputData, JobIdentifier
from .question import InterviewQuestion, InterviewScript


class AnalysisPhaseResult(BaseModel):
    """분석 단계 결과"""
    document_analysis: CandidateProfile | None = None
    code_analysis: CodeAnalysis | None = None
    jd_analysis: JDAnalysis | None = None


class QuestionGenerationState(BaseModel):
    """질문 생성 상태"""
    selected_topics: list[dict] = Field(default_factory=list)
    generated_questions: list[InterviewQuestion] = Field(default_factory=list)
    review_feedback: dict | None = None
    revision_count: int = 0


class WorkflowState(BaseModel):
    """전체 워크플로우 상태"""
    job: JobIdentifier
    temporal_workflow_id: str
    input_data: InputData

    # Phase 0
    enriched_input: EnrichedInput | None = None

    # Phase 1
    execution_plan: dict | None = None
    estimated_workload: dict | None = None

    # Phase 2
    analysis_result: AnalysisPhaseResult = Field(default_factory=AnalysisPhaseResult)

    # Phase 3
    question_state: QuestionGenerationState = Field(default_factory=QuestionGenerationState)

    # Phase 4
    final_output: InterviewScript | None = None

    # Meta
    current_phase: str = "pending"
    errors: list[dict] = Field(default_factory=list)
    checkpoints: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
