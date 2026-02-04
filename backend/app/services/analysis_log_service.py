"""
backend/app/services/analysis_log_service.py
Analysis Log Service - DB 기반 분석 로그 관리
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import AnalysisLogDB

logger = logging.getLogger(__name__)


class AnalysisLogService:
    """Analysis log CRUD 및 조회 서비스."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        job_id: str,
        activity_name: str,
        phase: str,
        log_type: str,
        message: Optional[str] = None,
        data: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> AnalysisLogDB:
        """새 분석 로그 생성."""
        log_entry = AnalysisLogDB(
            id=uuid.uuid4(),
            job_id=uuid.UUID(job_id),
            activity_name=activity_name,
            phase=phase,
            log_type=log_type,
            message=message,
            data=data or {},
            duration_ms=duration_ms,
        )
        self.db.add(log_entry)
        await self.db.commit()
        await self.db.refresh(log_entry)
        return log_entry

    async def log_activity_start(
        self,
        job_id: str,
        activity_name: str,
        phase: str,
        message: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> AnalysisLogDB:
        """Activity 시작 로그."""
        return await self.create_log(
            job_id=job_id,
            activity_name=activity_name,
            phase=phase,
            log_type="start",
            message=message or f"Starting {activity_name}",
            data=data,
        )

    async def log_activity_progress(
        self,
        job_id: str,
        activity_name: str,
        phase: str,
        message: str,
        data: Optional[dict] = None,
    ) -> AnalysisLogDB:
        """Activity 진행 상황 로그."""
        return await self.create_log(
            job_id=job_id,
            activity_name=activity_name,
            phase=phase,
            log_type="progress",
            message=message,
            data=data,
        )

    async def log_activity_result(
        self,
        job_id: str,
        activity_name: str,
        phase: str,
        message: Optional[str] = None,
        data: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> AnalysisLogDB:
        """Activity 결과 로그."""
        return await self.create_log(
            job_id=job_id,
            activity_name=activity_name,
            phase=phase,
            log_type="result",
            message=message or f"Completed {activity_name}",
            data=data,
            duration_ms=duration_ms,
        )

    async def log_activity_error(
        self,
        job_id: str,
        activity_name: str,
        phase: str,
        message: str,
        data: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> AnalysisLogDB:
        """Activity 에러 로그."""
        return await self.create_log(
            job_id=job_id,
            activity_name=activity_name,
            phase=phase,
            log_type="error",
            message=message,
            data=data,
            duration_ms=duration_ms,
        )

    async def get_logs_for_job(
        self,
        job_id: str,
        phase: Optional[str] = None,
        activity_name: Optional[str] = None,
        log_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AnalysisLogDB]:
        """Job별 로그 조회 (필터링 지원)."""
        conditions = [AnalysisLogDB.job_id == uuid.UUID(job_id)]

        if phase:
            conditions.append(AnalysisLogDB.phase == phase)
        if activity_name:
            conditions.append(AnalysisLogDB.activity_name == activity_name)
        if log_type:
            conditions.append(AnalysisLogDB.log_type == log_type)

        query = (
            select(AnalysisLogDB)
            .where(and_(*conditions))
            .order_by(AnalysisLogDB.created_at.asc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_logs_since(
        self,
        job_id: str,
        since: datetime,
    ) -> list[AnalysisLogDB]:
        """특정 시간 이후의 로그 조회 (WebSocket 스트리밍용)."""
        query = (
            select(AnalysisLogDB)
            .where(
                and_(
                    AnalysisLogDB.job_id == uuid.UUID(job_id),
                    AnalysisLogDB.created_at > since,
                )
            )
            .order_by(AnalysisLogDB.created_at.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_analysis_summary(self, job_id: str) -> dict:
        """Job 분석 요약 정보."""
        job_uuid = uuid.UUID(job_id)

        # 총 로그 수
        total_query = select(func.count(AnalysisLogDB.id)).where(
            AnalysisLogDB.job_id == job_uuid
        )
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar() or 0

        # 완료된 Activity 수 (log_type='result')
        completed_query = select(func.count(AnalysisLogDB.id)).where(
            and_(
                AnalysisLogDB.job_id == job_uuid,
                AnalysisLogDB.log_type == "result",
            )
        )
        completed_result = await self.db.execute(completed_query)
        completed_count = completed_result.scalar() or 0

        # 에러 수
        error_query = select(func.count(AnalysisLogDB.id)).where(
            and_(
                AnalysisLogDB.job_id == job_uuid,
                AnalysisLogDB.log_type == "error",
            )
        )
        error_result = await self.db.execute(error_query)
        error_count = error_result.scalar() or 0

        # 총 소요 시간
        duration_query = select(func.sum(AnalysisLogDB.duration_ms)).where(
            and_(
                AnalysisLogDB.job_id == job_uuid,
                AnalysisLogDB.duration_ms.isnot(None),
            )
        )
        duration_result = await self.db.execute(duration_query)
        total_duration_ms = duration_result.scalar() or 0

        # Phase별 통계
        phase_query = (
            select(
                AnalysisLogDB.phase,
                func.count(AnalysisLogDB.id).label("count"),
            )
            .where(AnalysisLogDB.job_id == job_uuid)
            .group_by(AnalysisLogDB.phase)
        )
        phase_result = await self.db.execute(phase_query)
        phase_stats = {row.phase: row.count for row in phase_result.all()}

        # Activity별 통계
        activity_query = (
            select(
                AnalysisLogDB.activity_name,
                func.count(AnalysisLogDB.id).label("count"),
            )
            .where(AnalysisLogDB.job_id == job_uuid)
            .group_by(AnalysisLogDB.activity_name)
        )
        activity_result = await self.db.execute(activity_query)
        activity_stats = {row.activity_name: row.count for row in activity_result.all()}

        return {
            "job_id": job_id,
            "total_logs": total_count,
            "completed_activities": completed_count,
            "errors": error_count,
            "total_duration_ms": total_duration_ms,
            "total_duration_sec": round(total_duration_ms / 1000, 2) if total_duration_ms else 0,
            "phase_stats": phase_stats,
            "activity_stats": activity_stats,
        }
