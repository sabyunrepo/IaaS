"""
backend/app/models/enums.py
Enum 정의
"""
from enum import Enum


class JobStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"
    ENRICHING = "enriching"
    PLANNING = "planning"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QuestionCategory(str, Enum):
    """질문 카테고리"""
    ROLE_FIT = "role_fit"
    TECHNICAL_DEPTH = "technical_depth"
    EXECUTION_OWNERSHIP = "execution_ownership"
    COMMUNICATION = "communication"
    RISK_FLAGS = "risk_flags"
