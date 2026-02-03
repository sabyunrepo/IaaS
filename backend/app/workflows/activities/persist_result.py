"""
backend/app/workflows/activities/persist_result.py
워크플로우 결과를 DB에 저장하는 Activity
"""
import logging
from datetime import datetime, timezone

from temporalio import activity

from app.core.observability import observe_activity

logger = logging.getLogger(__name__)


@activity.defn
@observe_activity(name="persist_result", phase="finalization")
async def persist_result(job_id: str, final_script: dict) -> dict:
    """워크플로우 완료 결과를 DB에 저장"""
    from app.core.database import async_session
    from app.models.database import JobDB
    from sqlalchemy import select
    import uuid

    async with async_session() as session:
        result = await session.execute(
            select(JobDB).where(JobDB.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if job is None:
            logger.error(f"Job {job_id} not found for result persistence")
            return {"persisted": False}

        is_error = "error" in final_script and len(final_script) == 1
        job.status = "failed" if is_error else "completed"
        job.final_output = final_script
        job.updated_at = datetime.now(timezone.utc)
        if not is_error:
            job.completed_at = datetime.now(timezone.utc)
        await session.commit()

    logger.info(f"Job {job_id} result persisted to DB")
    return {"persisted": True}
