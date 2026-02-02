"""
backend/app/services/job_service.py
Job 비즈니스 로직
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import JobNotFoundError, AuthorizationError
from app.models.database import JobDB
from app.models.enums import JobStatus


async def create_job(
    user_id: uuid.UUID,
    input_data: dict,
    callback_url: str | None = None,
    db: AsyncSession = None,
) -> JobDB:
    """Job 생성"""
    job = JobDB(
        id=uuid.uuid4(),
        user_id=user_id,
        status=JobStatus.PENDING.value,
        input_data=input_data,
        callback_url=callback_url,
    )
    db.add(job)
    await db.flush()
    return job


async def get_job(job_id: str, user_id: uuid.UUID, db: AsyncSession) -> JobDB:
    """Job 조회 (소유권 확인)"""
    result = await db.execute(
        select(JobDB).where(JobDB.id == uuid.UUID(job_id))
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise JobNotFoundError(job_id)
    if job.user_id != user_id:
        raise AuthorizationError("Not your job")
    return job


async def list_jobs(user_id: uuid.UUID, db: AsyncSession, limit: int = 20, offset: int = 0) -> list[JobDB]:
    """사용자의 Job 목록"""
    result = await db.execute(
        select(JobDB)
        .where(JobDB.user_id == user_id)
        .order_by(JobDB.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def delete_job(job_id: str, user_id: uuid.UUID, db: AsyncSession) -> None:
    """Job 삭제"""
    job = await get_job(job_id, user_id, db)
    await db.delete(job)


async def update_job_status(job_id: str, status: JobStatus, db: AsyncSession) -> JobDB:
    """Job 상태 업데이트 (내부용)"""
    result = await db.execute(select(JobDB).where(JobDB.id == uuid.UUID(job_id)))
    job = result.scalar_one_or_none()
    if job is None:
        raise JobNotFoundError(job_id)
    job.status = status.value
    job.updated_at = datetime.now(timezone.utc)
    if status == JobStatus.COMPLETED:
        job.completed_at = datetime.now(timezone.utc)
    return job
