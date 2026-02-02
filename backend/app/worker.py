"""
backend/app/worker.py
Temporal Worker 엔트리포인트
"""
import asyncio
import logging

from temporalio.worker import Worker

from app.core.config import settings
from app.core.temporal import get_temporal_client
from app.workflows.interview_workflow import InterviewGenerationWorkflow

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Activity 함수 등록
from app.workflows.activities.input_enrichment import enrich_input

ACTIVITIES = [enrich_input]


async def main():
    logger.info(f"Connecting to Temporal at {settings.TEMPORAL_HOST}")
    client = await get_temporal_client()

    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[InterviewGenerationWorkflow],
        activities=ACTIVITIES,
    )

    logger.info(f"Worker started, listening on task queue: {settings.TEMPORAL_TASK_QUEUE}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
