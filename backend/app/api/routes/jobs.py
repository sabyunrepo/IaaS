"""
backend/app/api/routes/jobs.py
Job CRUD API 엔드포인트
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user_or_api_key
from app.models.database import UserDB
from app.models.input import CreateJobRequest, CreateJobResponse
from app.services import job_service

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
async def create_job(
    request: CreateJobRequest,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """면접 스크립트 생성 요청"""
    job = await job_service.create_job(
        user_id=user.id,
        input_data=request.input_data.model_dump(mode="json"),
        callback_url=request.callback_url,
        db=db,
    )

    # TODO: Step 7에서 Temporal workflow 시작 연동
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
    """Job 상세 조회"""
    job = await job_service.get_job(job_id, user.id, db)
    result = _job_to_dict(job)
    if job.final_output:
        result["output"] = job.final_output
    return result


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    user: UserDB = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Job 삭제"""
    await job_service.delete_job(job_id, user.id, db)
