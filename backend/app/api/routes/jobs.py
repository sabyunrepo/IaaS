"""
backend/app/api/routes/jobs.py
Job CRUD API 엔드포인트
"""
import asyncio
import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.api.deps import get_current_user_or_api_key
from app.models.database import UserDB
from pydantic import BaseModel
from sqlalchemy import select

from app.models.input import CreateJobRequest, CreateJobResponse
from app.models.database import CheckpointDB
from app.services import job_service
from app.api.transformers import ensure_compatible_format

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def _job_to_dict(job) -> dict:
    return {
        "job_id": str(job.id),
        "status": job.status,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


@router.post("", status_code=201)
@limiter.limit("10/minute")
async def create_job(
    request: Request,
    body: CreateJobRequest,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """면접 스크립트 생성 요청"""
    job = await job_service.create_job(
        user_id=user.id,
        input_data=body.input_data.model_dump(mode="json"),
        callback_url=body.callback_url,
        db=db,
    )

    return CreateJobResponse(
        job_id=str(job.id),
        status=job.status,
        estimated_time_seconds=300,
        created_at=job.created_at,
    )


@router.get("")
@limiter.limit("60/minute")
async def list_jobs(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """사용자의 Job 목록 조회"""
    jobs = await job_service.list_jobs(user.id, db, limit=limit, offset=offset)
    return [_job_to_dict(j) for j in jobs]


@router.get("/{job_id}")
@limiter.limit("120/minute")
async def get_job(
    request: Request,
    job_id: str,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Job 상세 조회 (Temporal에서 실시간 진행률 포함)"""
    job = await job_service.get_job(job_id, user.id, db)
    result = _job_to_dict(job)
    if job.final_output:
        result["output"] = job.final_output

    # Temporal에서 실시간 진행률 조회
    if job.temporal_workflow_id and job.status not in ("completed", "failed"):
        try:
            from app.core.temporal import get_temporal_client
            client = await get_temporal_client()
            handle = client.get_workflow_handle(job.temporal_workflow_id)
            progress = await asyncio.wait_for(
                handle.query("get_progress"), timeout=5.0
            )
            result["progress"] = progress

            # Temporal 상태가 DB와 다르면 DB 동기화
            if progress.get("status") and progress["status"] != job.status:
                job.status = progress["status"]
                result["status"] = progress["status"]
        except Exception as e:
            logger.debug(f"Could not query workflow progress: {e}")

    return result


@router.get("/{job_id}/result")
@limiter.limit("50/minute")
async def get_job_result(
    request: Request,
    job_id: str,
    version: str = Query("v2", regex="^v[12]$", description="API response format version"),
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """완성된 면접 스크립트 조회

    Args:
        job_id: Job ID
        version: Response format version (v1 or v2, default v2)
            - v1: Legacy format with evaluation_scenarios object
            - v2: New format with scenarios array, intel, analysis, decision

    Returns:
        Interview script in requested format
    """
    job = await job_service.get_job(job_id, user.id, db)
    if job.status != "completed" or not job.final_output:
        from app.exceptions import ValidationError
        raise ValidationError("Job is not completed yet")

    # Transform to requested format
    script = ensure_compatible_format(job.final_output, version)

    # Filter internal metadata from response
    metadata = script.get("metadata")
    if isinstance(metadata, dict):
        for internal_key in ("model_used", "llm_provider", "trace_id", "langfuse_url"):
            metadata.pop(internal_key, None)

    # Cache-Control: completed jobs are immutable
    response = JSONResponse(content=script)
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response


WORKFLOW_STEPS = [
    "enrich_input", "plan", "document_analysis", "code_analysis",
    "jd_analysis", "aggregate_analysis", "select_topics",
    "craft_questions", "enhance_questions", "review_quality", "finalize",
]


class RetryRequest(BaseModel):
    from_step: str | None = None
    force_rerun: bool = False


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: str,
    body: RetryRequest = RetryRequest(),
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """실패한 Job을 체크포인트부터 재시작"""
    import uuid as _uuid
    job = await job_service.get_job(job_id, user.id, db)

    if job.status not in ("failed", "completed"):
        from app.exceptions import ValidationError
        raise ValidationError("Only failed or completed jobs can be retried")

    # Determine resume point
    result = await db.execute(
        select(CheckpointDB)
        .where(CheckpointDB.job_id == _uuid.UUID(job_id))
        .order_by(CheckpointDB.created_at.desc())
    )
    checkpoints = list(result.scalars().all())
    completed_phases = {cp.phase for cp in checkpoints}

    if body.from_step:
        resume_from = body.from_step
    else:
        # Auto-detect: first step without checkpoint
        resume_from = WORKFLOW_STEPS[-1]
        for step in WORKFLOW_STEPS:
            if step not in completed_phases:
                resume_from = step
                break

    # Determine skipped/cached steps
    resume_idx = WORKFLOW_STEPS.index(resume_from) if resume_from in WORKFLOW_STEPS else 0
    skipped = WORKFLOW_STEPS[:resume_idx]
    cached = [s for s in skipped if s in completed_phases]

    # Start new Temporal workflow
    try:
        from app.core.temporal import get_temporal_client
        from app.workflows.interview_workflow import InterviewGenerationWorkflow
        from app.core.config import settings

        client = await get_temporal_client()
        workflow_id = f"interview-{job.id}-retry"
        workflow_input = {
            **(job.input_data or {}),
            "job_id": str(job.id),
            "resume_from": resume_from,
            "force_rerun": body.force_rerun,
        }
        await client.start_workflow(
            InterviewGenerationWorkflow.run,
            workflow_input,
            id=workflow_id,
            task_queue=settings.TEMPORAL_TASK_QUEUE,
        )
        job.temporal_workflow_id = workflow_id
        job.status = "retrying"
    except Exception as e:
        logger.error(f"Failed to start retry workflow: {e}")
        from app.exceptions import ValidationError
        raise ValidationError(f"Could not start retry: {e}")

    return {
        "job_id": str(job.id),
        "status": "retrying",
        "resume_from": resume_from,
        "skipped_steps": skipped,
        "cached_steps": cached,
    }


@router.get("/{job_id}/checkpoints")
@limiter.limit("60/minute")
async def get_checkpoints(
    request: Request,
    job_id: str,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Job의 체크포인트 상태 조회"""
    import uuid as _uuid
    # Verify ownership
    await job_service.get_job(job_id, user.id, db)

    result = await db.execute(
        select(CheckpointDB)
        .where(CheckpointDB.job_id == _uuid.UUID(job_id))
        .order_by(CheckpointDB.created_at)
    )
    checkpoints = list(result.scalars().all())
    completed_phases = {cp.phase for cp in checkpoints}

    steps = []
    resume_point = None
    for step in WORKFLOW_STEPS:
        status = "completed" if step in completed_phases else "pending"
        steps.append({"name": step, "status": status})
        if status == "pending" and resume_point is None:
            resume_point = step

    return {
        "job_id": job_id,
        "steps": steps,
        "resume_point": resume_point,
        "total_steps": len(WORKFLOW_STEPS),
        "completed_count": len(completed_phases & set(WORKFLOW_STEPS)),
    }


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Job 삭제"""
    await job_service.delete_job(job_id, user.id, db)
