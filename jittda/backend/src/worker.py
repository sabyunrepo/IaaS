"""
Temporal Worker — Analysis Pipeline 실행.

docker-compose worker 서비스의 엔트리포인트.
모든 Workflows + Activities를 등록하고 Task Queue를 폴링한다.
"""
from __future__ import annotations

import asyncio
import logging
import os

import structlog
from temporalio.client import Client
from temporalio.worker import Worker

from application.temporal import TASK_QUEUE
from application.temporal.activities import ALL_ACTIVITIES
from application.temporal.workflows import AnalysisPipeline


def _configure_logging() -> None:
    """Worker용 structlog 설정."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", level=logging.INFO)


async def main() -> None:
    _configure_logging()
    logger = structlog.get_logger()

    temporal_host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    logger.info("temporal_worker_starting", host=temporal_host, queue=TASK_QUEUE)

    client = await Client.connect(temporal_host)

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[AnalysisPipeline],
        activities=ALL_ACTIVITIES,
        max_concurrent_activities=3,
    )

    logger.info("temporal_worker_running", activities=len(ALL_ACTIVITIES))
    try:
        await worker.run()
    finally:
        from application.temporal.activities import close_redis_pool

        await close_redis_pool()
        logger.info("temporal_worker_stopped")


if __name__ == "__main__":
    asyncio.run(main())
