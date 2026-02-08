"""
backend/app/workflows/workflow_constants.py
워크플로우 공유 상수 — Retry 정책, 버전, 카테고리 가중치

Extracted from interview_workflow.py for SRP compliance.
"""
from datetime import timedelta

from temporalio.common import RetryPolicy

# Workflow version — increment when making breaking changes to the workflow logic.
WORKFLOW_VERSION = "1.0.0"

# ── Retry policies ──

DEFAULT_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
)

LLM_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=3,
    non_retryable_error_types=["ValueError"],
)

EXTERNAL_API_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=3),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=120),
    maximum_attempts=4,
)

# ── 경험 레벨별 카테고리 가중치 ──

CATEGORY_WEIGHTS_BY_LEVEL = {
    "신입":   {"role_fit": 0.30, "technical_depth": 0.25, "execution_ownership": 0.15, "communication": 0.20, "risk_flags": 0.10},
    "주니어": {"role_fit": 0.30, "technical_depth": 0.25, "execution_ownership": 0.15, "communication": 0.20, "risk_flags": 0.10},
    "미들":   {"role_fit": 0.25, "technical_depth": 0.20, "execution_ownership": 0.20, "communication": 0.20, "risk_flags": 0.15},
    "시니어": {"role_fit": 0.15, "technical_depth": 0.20, "execution_ownership": 0.25, "communication": 0.20, "risk_flags": 0.20},
    "CTO/VP": {"role_fit": 0.15, "technical_depth": 0.15, "execution_ownership": 0.25, "communication": 0.20, "risk_flags": 0.25},
}
