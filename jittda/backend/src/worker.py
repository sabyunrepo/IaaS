"""
Temporal Worker — Analysis Pipeline 실행.

docker-compose worker 서비스의 엔트리포인트.
모든 Workflows + Activities를 등록하고 Task Queue를 폴링한다.
SIGTERM/SIGINT 수신 시 graceful shutdown: 진행 중 Activity 완료 대기 후 종료.
"""
from __future__ import annotations

import asyncio
import os
import signal

import structlog
from temporalio.client import Client
from temporalio.worker import Worker

from application.temporal import TASK_QUEUE
from application.temporal.activities import ALL_ACTIVITIES, close_redis_pool, init_redis_pool
from application.temporal.workflows import AnalysisPipeline
from infrastructure.logging import configure_logging
from infrastructure.persistence.pool import close_pool, init_pool


def _validate_env() -> list[str]:
    """필수 환경변수 검증. 누락 목록 반환."""
    required = {
        "DATABASE_URL": "PostgreSQL 연결",
        "REDIS_URL": "Redis PubSub 이벤트",
        "TEMPORAL_HOST": "Temporal 서버",
    }
    recommended = {
        "LLM_API_KEY": "LLM 분석",
        "GITHUB_TOKEN": "GitHub 리포 수집",
    }
    missing = []
    for var, desc in required.items():
        if not os.environ.get(var):
            missing.append(f"[REQUIRED] {var} — {desc}")
    for var, desc in recommended.items():
        if not os.environ.get(var):
            missing.append(f"[RECOMMENDED] {var} — {desc}")
    return missing


async def main() -> None:
    configure_logging()
    logger = structlog.get_logger()

    # 환경변수 검증
    missing = _validate_env()
    required_missing = [m for m in missing if m.startswith("[REQUIRED]")]
    if required_missing:
        for m in required_missing:
            logger.error("env_missing", detail=m)
        raise SystemExit(f"Missing required env vars: {len(required_missing)}")
    for m in missing:
        logger.warning("env_missing", detail=m)

    # DB Pool 초기화 (Worker: min=1, max=5)
    db_url = os.environ.get("DATABASE_URL", "")
    await init_pool(db_url, min_size=1, max_size=5)
    logger.info("db_pool_initialized", min_size=1, max_size=5)

    # Redis Pool 초기화
    await init_redis_pool()
    logger.info("redis_pool_initialized")

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

    # Graceful shutdown: SIGTERM/SIGINT → worker.shutdown()
    shutdown_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("shutdown_signal_received")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _signal_handler)

    logger.info("temporal_worker_running", activities=len(ALL_ACTIVITIES))

    # Worker를 별도 태스크로 실행하고, 시그널 대기
    worker_task = asyncio.create_task(worker.run())

    # shutdown signal 또는 worker 자체 종료 대기
    done, _ = await asyncio.wait(
        [worker_task, asyncio.create_task(shutdown_event.wait())],
        return_when=asyncio.FIRST_COMPLETED,
    )

    if shutdown_event.is_set() and not worker_task.done():
        logger.info("graceful_shutdown_starting")
        await worker.shutdown()
        logger.info("worker_shutdown_complete")

    # Cleanup
    await close_redis_pool()
    await close_pool()
    logger.info("temporal_worker_stopped")


if __name__ == "__main__":
    asyncio.run(main())
