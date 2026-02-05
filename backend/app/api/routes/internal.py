"""
backend/app/api/routes/internal.py
Internal API - Activity에서 사용하는 내부 엔드포인트
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.services.analysis_log_service import AnalysisLogService

router = APIRouter(prefix="/api/internal", tags=["internal"])


async def verify_internal_token(
    x_internal_token: str | None = Header(None, alias="X-Internal-Token"),
) -> None:
    """Worker → Backend 내부 API 인증"""
    if not settings.is_local:
        if not x_internal_token or x_internal_token != settings.INTERNAL_API_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid internal API token",
            )
logger = logging.getLogger(__name__)


class CreateAnalysisLogRequest(BaseModel):
    """분석 로그 생성 요청 모델."""
    job_id: str
    activity_name: str
    phase: str
    log_type: str  # 'start', 'progress', 'result', 'error'
    message: Optional[str] = None
    data: Optional[dict] = None
    duration_ms: Optional[int] = None


class CreateAnalysisLogResponse(BaseModel):
    """분석 로그 생성 응답 모델."""
    id: str
    created_at: str


@router.post(
    "/analysis-logs",
    response_model=CreateAnalysisLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_analysis_log(
    request: CreateAnalysisLogRequest,
    db: AsyncSession = Depends(get_db),
    _auth: None = Depends(verify_internal_token),
):
    """Activity에서 분석 로그를 기록하는 내부 엔드포인트.

    Note: 이 엔드포인트는 내부 네트워크에서만 접근 가능해야 합니다.
    프로덕션 환경에서는 적절한 네트워크 보안 설정이 필요합니다.
    """
    # Validate log_type
    valid_log_types = {"start", "progress", "result", "error"}
    if request.log_type not in valid_log_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid log_type. Must be one of: {valid_log_types}",
        )

    try:
        service = AnalysisLogService(db)
        log_entry = await service.create_log(
            job_id=request.job_id,
            activity_name=request.activity_name,
            phase=request.phase,
            log_type=request.log_type,
            message=request.message,
            data=request.data,
            duration_ms=request.duration_ms,
        )

        return CreateAnalysisLogResponse(
            id=str(log_entry.id),
            created_at=log_entry.created_at.isoformat() if log_entry.created_at else "",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create analysis log: {e}")
        raise HTTPException(status_code=500, detail="Failed to create analysis log")
