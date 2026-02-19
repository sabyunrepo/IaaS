"""
MetaState — MetaAgent Graph (Level 1) 상태 정의.

Reference Passing 패턴: Raw Data 대신 DB ID(UUID)만 보유.
LangGraph Checkpoint에 기록되므로 최소한의 크기를 유지한다.
"""
from typing import TypedDict


class MetaState(TypedDict):
    """MetaAgent 전체 파이프라인 상태."""

    # Core Context
    job_id: str

    # Input References (jobs 테이블)
    input_data_ref: str  # jobs 테이블 ID

    # Identity Resolution (identity_resolutions 테이블 ID)
    identity_cluster_ref: str | None

    # Analysis Result References (analysis_results 테이블 ID)
    forensic_result_ref: str | None
    logic_result_ref: str | None
    stack_result_ref: str | None

    # Synthesized Profile (analysis_results 테이블 ID)
    profile_ref: str | None

    # Scores (가벼우므로 State에 직접 포함)
    candidate_scores: dict | None  # {logic, mastery, stability, authenticity, weighted_total}

    # Question Generation (analysis_results 테이블 ID)
    questions_ref: str | None

    # Flow Control
    status: str  # pending | collecting | analyzing | synthesizing | questioning | reviewing | assembling | completed | failed
    current_phase: str  # input_router | plan_generator | analysis | synthesis | questions | quality_gate | output
    revision_count: int  # QualityGate 루프 카운터 (최대 2)
    errors: list[str]
