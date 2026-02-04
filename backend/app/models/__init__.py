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
    LanguageConfig, InputData,
    LinkedInExperience, LinkedInEducation, LinkedInCertification,
    LinkedInProject, LinkedInHonor, LinkedInActivity, LinkedInProfile,
    EnrichedInput, JobIdentifier, CreateJobRequest, CreateJobResponse,
)
from .analysis import (
    CandidateProfile, CodeAnalysis, JDAnalysis,
    RepositoryAnalysis, NotableImplementation,
)
from .question import (
    InterviewQuestion, InterviewScript, TerminologyEntry,
    EvaluationScenario, FollowUpQuestion, CodeReference,
    ExpectedAnswer, InterviewerNote, CandidateSummary,
    ScenarioLevel, FollowUpResponse, AnswerKeyword,
)
from .checkpoint import (
    PipelineStep, PIPELINE_STEPS,
    CheckpointMeta, CheckpointStatus, RetryRequest, RetryResponse,
)
from .workflow import WorkflowState, AnalysisPhaseResult
from .database import Base, UserDB, OAuthAccountDB, APIKeyDB, JobDB, CheckpointDB, EmbeddingDB

# v2 모델
from .intel import (
    IntelBrief, JDSummary, CompetencyMatch, GitHubSummary,
    LinkedInPosition, RequirementMatch,
)
from .deep_analysis import (
    DeepAnalysis, EngineeringDNAItem, RiskFlag, SkillMatchRow,
)
from .decision import (
    DecisionSupport, DecisionSummary, InterviewerGuideTips,
    JDCompetencyWeight, ResumeTip, CoverLetterInsight,
)

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
    # Question (v1/v2)
    "InterviewQuestion", "InterviewScript",
    "ScenarioLevel", "FollowUpResponse", "AnswerKeyword",
    # Checkpoint
    "PipelineStep", "PIPELINE_STEPS",
    # Workflow
    "WorkflowState",
    # Database ORM
    "Base", "UserDB", "OAuthAccountDB", "APIKeyDB", "JobDB", "CheckpointDB", "EmbeddingDB",
    # v2 Intel
    "IntelBrief", "JDSummary", "CompetencyMatch", "GitHubSummary",
    "LinkedInPosition", "RequirementMatch",
    # v2 Deep Analysis
    "DeepAnalysis", "EngineeringDNAItem", "RiskFlag", "SkillMatchRow",
    # v2 Decision
    "DecisionSupport", "DecisionSummary", "InterviewerGuideTips",
    "JDCompetencyWeight", "ResumeTip", "CoverLetterInsight",
]
