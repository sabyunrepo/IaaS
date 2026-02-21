"""FastAPI Application Factory — Temporal + Redis PubSub 통합."""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware


def _configure_logging() -> None:
    """Configure structlog for JSON structured logging."""
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


@asynccontextmanager
async def lifespan(application: FastAPI):
    """앱 시작/종료 시 Temporal client + Redis bridge 관리."""
    logger = structlog.get_logger()

    # Temporal Client 연결
    temporal_client = None
    temporal_host = os.environ.get("TEMPORAL_HOST", "")
    if temporal_host:
        try:
            from temporalio.client import Client

            temporal_client = await Client.connect(temporal_host)
            logger.info("temporal_client_connected", host=temporal_host)
        except Exception as e:
            logger.error("temporal_client_connection_failed", error=str(e))

    application.state.temporal_client = temporal_client

    # Redis PubSub Bridge 시작
    redis_bridge = None
    redis_url = os.environ.get("REDIS_URL", "")
    if redis_url:
        try:
            from interface.websocket.redis_bridge import RedisPubSubBridge

            redis_bridge = RedisPubSubBridge(redis_url)
            await redis_bridge.start()
            logger.info("redis_bridge_started")
        except Exception as e:
            logger.error("redis_bridge_start_failed", error=str(e))

    application.state.redis_bridge = redis_bridge

    yield

    # Cleanup
    if redis_bridge:
        await redis_bridge.stop()
    logger.info("app_shutdown_complete")


def create_app() -> FastAPI:
    _configure_logging()
    logger = structlog.get_logger()

    application = FastAPI(
        title="Jittda Sniper v5.0",
        version="5.0.0",
        description="AI Interview Script Generator",
        lifespan=lifespan,
    )

    # CORS — configurable via environment
    allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3001").split(",")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Session middleware (required for OAuth state)
    jwt_secret = os.environ.get("JWT_SECRET", "dev-secret-change-me")
    application.add_middleware(SessionMiddleware, secret_key=jwt_secret)

    # Request logging middleware
    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 1),
        )
        return response

    # API routers
    from interface.api.routes.auth import router as auth_router
    from interface.api.routes.jobs import router as jobs_router
    from interface.api.routes.jobs import ws_router

    application.include_router(auth_router)
    application.include_router(jobs_router)
    application.include_router(ws_router)

    # Health check with dependency verification
    @application.get("/health")
    async def health_check():
        checks = {"status": "ok", "version": "5.0.0"}

        # PostgreSQL check
        try:
            import psycopg

            db_url = os.environ.get("DATABASE_URL", "")
            if db_url:
                async with await psycopg.AsyncConnection.connect(db_url) as conn:
                    await conn.execute("SELECT 1")
                checks["postgres"] = "ok"
        except Exception as e:
            checks["postgres"] = f"error: {e}"
            checks["status"] = "degraded"

        # Redis check
        try:
            import redis.asyncio as aioredis

            redis_url = os.environ.get("REDIS_URL", "")
            if redis_url:
                r = aioredis.from_url(redis_url)
                await r.ping()
                await r.aclose()
                checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"
            checks["status"] = "degraded"

        # Temporal check
        if hasattr(application.state, "temporal_client") and application.state.temporal_client:
            checks["temporal"] = "ok"
        else:
            temporal_host = os.environ.get("TEMPORAL_HOST", "")
            if temporal_host:
                checks["temporal"] = "not connected"
                checks["status"] = "degraded"

        return checks

    return application


app = create_app()
