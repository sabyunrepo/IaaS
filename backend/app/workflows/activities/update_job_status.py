"""
backend/app/workflows/activities/update_job_status.py
워크플로우 Phase 변경 시 DB 상태를 즉시 동기화하는 Activity
"""
import logging
import uuid
from datetime import datetime, timezone

from temporalio import activity
from sqlalchemy import select

from app.core.database import async_session
from app.models.database import JobDB

logger = logging.getLogger(__name__)


@activity.defn
async def update_job_status_activity(job_id: str, status: str) -> None:
    """Job 상태를 DB에 즉시 반영.

    Args:
        job_id: Job UUID 문자열
        status: JobStatus enum 값 (e.g. "enriching", "planning")
    """
    async with async_session() as session:
        result = await session.execute(
            select(JobDB).where(JobDB.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if job is None:
            logger.warning(f"Job {job_id} not found for status update")
            return

        job.status = status
        job.updated_at = datetime.now(timezone.utc)
        await session.commit()

    logger.info(f"Job {job_id} status updated to {status}")
