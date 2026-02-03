"""
backend/app/workflows/activities/observability_activities.py
Langfuse Trace/Span 관리용 Activities
"""
import logging

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def start_job_trace(
    job_id: str,
    user_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    """Job 시작 시 Langfuse Trace 생성

    Returns:
        {"trace_id": str | None, "enabled": bool}
    """
    from app.core.observability import create_trace_for_job, is_langfuse_enabled

    if not is_langfuse_enabled():
        return {"trace_id": None, "enabled": False}

    trace_id = create_trace_for_job(
        job_id=job_id,
        user_id=user_id,
        metadata=metadata,
    )

    activity.heartbeat(f"Started Langfuse trace: {trace_id}")
    return {"trace_id": trace_id, "enabled": True}


@activity.defn
async def end_job_trace(
    job_id: str,
    trace_id: str | None,
    status: str = "success",
    quality_score: float | None = None,
) -> dict:
    """Job 종료 시 Langfuse Trace 종료 및 점수 추가

    Returns:
        {"scored": bool, "flushed": bool}
    """
    from app.core.observability import (
        is_langfuse_enabled,
        score_trace,
        flush_langfuse,
    )

    if not is_langfuse_enabled():
        return {"scored": False, "flushed": False}

    # 품질 점수 추가 (있는 경우)
    scored = False
    if trace_id and quality_score is not None:
        score_trace(
            trace_id=trace_id,
            name="completion_quality",
            value=quality_score,
            comment=f"Job {job_id} completed with status: {status}",
        )
        scored = True

    # 상태 점수 추가
    if trace_id:
        score_trace(
            trace_id=trace_id,
            name="job_status",
            value=1.0 if status == "success" else 0.0,
            comment=status,
        )

    # 버퍼 플러시
    flush_langfuse()

    activity.heartbeat(f"Ended Langfuse trace: {trace_id}")
    return {"scored": scored, "flushed": True}


@activity.defn
async def log_phase_event(
    job_id: str,
    phase: str,
    event: str,
    metadata: dict | None = None,
) -> dict:
    """Phase 이벤트 로깅

    Returns:
        {"logged": bool}
    """
    from app.core.observability import log_event, is_langfuse_enabled

    if not is_langfuse_enabled():
        return {"logged": False}

    log_event(
        name=f"{phase}:{event}",
        metadata={
            "job_id": job_id,
            "phase": phase,
            "event": event,
            **(metadata or {}),
        },
    )

    return {"logged": True}
