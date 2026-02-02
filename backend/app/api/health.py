"""
backend/app/api/health.py
헬스체크 엔드포인트
"""
import logging

from fastapi import APIRouter

from app.core.config import settings
from app.workflows.interview_workflow import WORKFLOW_VERSION

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """서비스 상태 확인"""
    checks = {
        "service": "ok",
        "version": "4.0.0",
        "workflow_version": WORKFLOW_VERSION,
        "env": settings.ENV,
    }

    # DB 체크
    try:
        from app.core.database import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {type(e).__name__}"
        logger.warning(f"DB health check failed: {e}")

    # Redis 체크
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {type(e).__name__}"
        logger.warning(f"Redis health check failed: {e}")

    # Temporal 체크
    try:
        from app.core.temporal import get_temporal_client
        client = await get_temporal_client()
        checks["temporal"] = "ok"
    except Exception as e:
        checks["temporal"] = f"error: {type(e).__name__}"
        logger.warning(f"Temporal health check failed: {e}")

    is_healthy = checks.get("database") == "ok"
    status = "healthy" if is_healthy else "degraded"

    return {"status": status, "checks": checks}
