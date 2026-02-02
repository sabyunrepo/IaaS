"""
backend/app/api/routes/jobs.py
Job CRUD API 엔드포인트
"""
import logging

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.api.deps import get_current_user_or_api_key
from app.models.database import UserDB
from app.models.input import CreateJobRequest, CreateJobResponse
from app.services import job_service

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
async def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """사용자의 Job 목록 조회"""
    jobs = await job_service.list_jobs(user.id, db, limit=limit, offset=offset)
    return [_job_to_dict(j) for j in jobs]


@router.get("/{job_id}")
async def get_job(
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
            progress = await handle.query("get_progress")
            result["progress"] = progress

            # Temporal 상태가 DB와 다르면 DB 동기화
            if progress.get("status") and progress["status"] != job.status:
                job.status = progress["status"]
                result["status"] = progress["status"]
        except Exception as e:
            logger.debug(f"Could not query workflow progress: {e}")

    return result


@router.get("/{job_id}/result")
async def get_job_result(
    job_id: str,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """완성된 면접 스크립트 조회"""
    job = await job_service.get_job(job_id, user.id, db)
    if job.status != "completed" or not job.final_output:
        from app.exceptions import ValidationError
        raise ValidationError("Job is not completed yet")
    return job.final_output


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Job 삭제"""
    await job_service.delete_job(job_id, user.id, db)
