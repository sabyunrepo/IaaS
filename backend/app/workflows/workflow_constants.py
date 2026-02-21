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

_W_ENTRY   = {"role_fit": 0.30, "technical_depth": 0.25, "execution_ownership": 0.15, "communication": 0.20, "risk_flags": 0.10}
_W_JUNIOR  = {"role_fit": 0.30, "technical_depth": 0.25, "execution_ownership": 0.15, "communication": 0.20, "risk_flags": 0.10}
_W_MID     = {"role_fit": 0.25, "technical_depth": 0.20, "execution_ownership": 0.20, "communication": 0.20, "risk_flags": 0.15}
_W_SENIOR  = {"role_fit": 0.15, "technical_depth": 0.20, "execution_ownership": 0.25, "communication": 0.20, "risk_flags": 0.20}
_W_CTO     = {"role_fit": 0.15, "technical_depth": 0.15, "execution_ownership": 0.25, "communication": 0.20, "risk_flags": 0.25}

CATEGORY_WEIGHTS_BY_LEVEL = {
    # English keys (primary)
    "Entry": _W_ENTRY, "Junior": _W_JUNIOR, "Mid": _W_MID, "Senior": _W_SENIOR, "CTO/VP": _W_CTO,
    # Korean keys (backward compat)
    "신입": _W_ENTRY, "주니어": _W_JUNIOR, "미들": _W_MID, "시니어": _W_SENIOR,
}
