"""
backend/app/models/__init__.py
모델 패키지 — 모든 Pydantic 및 SQLAlchemy 모델 export
"""
from .enums import JobStatus, QuestionCategory
from .types import (
    SupportedLanguage, ExperienceLevel, Difficulty,
    RequirementCategory, PatternType, Severity, MatchType,
)
from .auth import User, OAuthAccount, APIKey
from .input import (
    LanguageConfig, InputData, LinkedInProfile, EnrichedInput,
    JobIdentifier, CreateJobRequest, CreateJobResponse,
)
from .analysis import (
    CandidateProfile, CodeAnalysis, JDAnalysis,
    RepositoryAnalysis, NotableImplementation,
)
from .question import (
    InterviewQuestion, InterviewScript, TerminologyEntry,
    EvaluationScenario, FollowUpQuestion, CodeReference,
    ExpectedAnswer, InterviewerNote, CandidateSummary,
)
from .checkpoint import (
    PipelineStep, PIPELINE_STEPS,
    CheckpointMeta, CheckpointStatus, RetryRequest, RetryResponse,
)
from .workflow import WorkflowState, AnalysisPhaseResult
from .database import Base, UserDB, OAuthAccountDB, APIKeyDB, JobDB, CheckpointDB, EmbeddingDB

__all__ = [
    # Enums
    "JobStatus", "QuestionCategory",
    # Types
    "SupportedLanguage", "ExperienceLevel", "Difficulty",
    # Auth
    "User", "OAuthAccount", "APIKey",
    # Input
    "InputData", "EnrichedInput", "JobIdentifier",
    "CreateJobRequest", "CreateJobResponse",
    # Analysis
    "CandidateProfile", "CodeAnalysis", "JDAnalysis",
    # Question
    "InterviewQuestion", "InterviewScript",
    # Checkpoint
    "PipelineStep", "PIPELINE_STEPS",
    # Workflow
    "WorkflowState",
    # Database ORM
    "Base", "UserDB", "OAuthAccountDB", "APIKeyDB", "JobDB", "CheckpointDB", "EmbeddingDB",
]
