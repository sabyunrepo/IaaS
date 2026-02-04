"""
backend/app/api/routes/analysis_logs.py
Analysis Logs API - 분석 로그 조회 엔드포인트
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.database import JobDB, UserDB
from app.services.analysis_log_service import AnalysisLogService

router = APIRouter(prefix="/api/v1/jobs", tags=["analysis-logs"])


class AnalysisLogResponse(BaseModel):
    """분석 로그 응답 모델."""
    id: str
    job_id: str
    activity_name: str
    phase: str
    log_type: str
    message: Optional[str]
    data: dict
    duration_ms: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


class AnalysisSummaryResponse(BaseModel):
    """분석 요약 응답 모델."""
    job_id: str
    total_logs: int
    completed_activities: int
    errors: int
    total_duration_ms: int
    total_duration_sec: float
    phase_stats: dict
    activity_stats: dict


@router.get("/{job_id}/analysis-logs", response_model=list[AnalysisLogResponse])
async def get_analysis_logs(
    job_id: str,
    phase: Optional[str] = Query(None, description="Filter by phase"),
    activity_name: Optional[str] = Query(None, description="Filter by activity name"),
    log_type: Optional[str] = Query(None, description="Filter by log type (start, progress, result, error)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    """Job의 분석 로그 조회.

    필터링 옵션:
    - phase: enriching, planning, analyzing, generating, reviewing
    - activity_name: document_analysis, code_analysis, jd_analysis 등
    - log_type: start, progress, result, error
    """
    # Verify job ownership
    job_uuid = uuid.UUID(job_id)
    result = await db.execute(select(JobDB).where(JobDB.id == job_uuid))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job's logs")

    service = AnalysisLogService(db)
    logs = await service.get_logs_for_job(
        job_id=job_id,
        phase=phase,
        activity_name=activity_name,
        log_type=log_type,
        limit=limit,
        offset=offset,
    )

    return [
        AnalysisLogResponse(
            id=str(log.id),
            job_id=str(log.job_id),
            activity_name=log.activity_name,
            phase=log.phase,
            log_type=log.log_type,
            message=log.message,
            data=log.data or {},
            duration_ms=log.duration_ms,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )
        for log in logs
    ]


@router.get("/{job_id}/analysis-summary", response_model=AnalysisSummaryResponse)
async def get_analysis_summary(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: UserDB = Depends(get_current_user),
):
    """Job의 분석 요약 정보 조회."""
    # Verify job ownership
    job_uuid = uuid.UUID(job_id)
    result = await db.execute(select(JobDB).where(JobDB.id == job_uuid))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this job's summary")

    service = AnalysisLogService(db)
    summary = await service.get_analysis_summary(job_id)

    return AnalysisSummaryResponse(**summary)
