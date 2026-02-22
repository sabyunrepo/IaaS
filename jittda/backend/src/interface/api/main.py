"""FastAPI Application Factory — Temporal + Redis PubSub + DB Pool 통합."""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from infrastructure.logging import configure_logging
from infrastructure.persistence.pool import close_pool, get_pool, init_pool


@asynccontextmanager
async def lifespan(application: FastAPI):
    """앱 시작/종료 시 DB pool + Temporal client + Redis bridge 관리."""
    logger = structlog.get_logger()

    # DB Connection Pool 초기화
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url:
        try:
            pool = await init_pool(db_url, min_size=2, max_size=10)
            logger.info("db_pool_initialized", min_size=2, max_size=10)
        except Exception as e:
            logger.error("db_pool_init_failed", error=str(e))

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
    await close_pool()
    logger.info("app_shutdown_complete")


def create_app() -> FastAPI:
    configure_logging()
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

    # Session middleware (required for OAuth state) — auth.py와 동일 시크릿 사용
    from interface.api.middleware.auth import _get_secret

    application.add_middleware(SessionMiddleware, secret_key=_get_secret())

    # Rate limit middleware
    from infrastructure.security.rate_limiter import RateLimitMiddleware

    application.add_middleware(RateLimitMiddleware)

    # Proxy headers — 가장 마지막에 추가 (= 가장 먼저 실행)
    # nginx/Cloudflare가 전달하는 X-Forwarded-* 헤더를 신뢰
    # OAuth redirect_uri 등에서 올바른 외부 URL 생성에 필수
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

    trusted_hosts = os.environ.get("TRUSTED_PROXY_HOSTS", "127.0.0.1,backend").split(",")
    application.add_middleware(ProxyHeadersMiddleware, trusted_hosts=trusted_hosts)

    # Request logging + Prometheus metrics middleware
    @application.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_s = time.time() - start
        path = request.url.path
        logger.info(
            "http_request",
            method=request.method,
            path=path,
            status=response.status_code,
            duration_ms=round(duration_s * 1000, 1),
        )
        try:
            from infrastructure.observability.metrics import (
                http_request_duration_seconds,
                http_requests_total,
            )

            http_requests_total.labels(
                method=request.method, path=path, status=str(response.status_code)
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method, path=path
            ).observe(duration_s)
        except ImportError:
            pass
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
        from fastapi.responses import JSONResponse

        checks: dict = {"status": "ok", "version": "5.0.0"}

        # PostgreSQL check — pool 재사용
        try:
            pool = get_pool()
            async with pool.connection() as conn:
                await conn.execute("SELECT 1")
            stats = pool.get_stats()
            checks["postgres"] = "ok"
            checks["pool"] = {
                "size": stats.get("pool_size", 0) if isinstance(stats, dict) else getattr(stats, "pool_size", 0),
                "available": stats.get("pool_available", 0) if isinstance(stats, dict) else getattr(stats, "pool_available", 0),
                "waiting": stats.get("requests_waiting", 0) if isinstance(stats, dict) else getattr(stats, "requests_waiting", 0),
            }
        except RuntimeError:
            checks["postgres"] = "pool not initialized"
            checks["status"] = "degraded"
        except Exception as e:
            logger.error("health_postgres_error", error=str(e))
            checks["postgres"] = "unavailable"
            checks["status"] = "degraded"

        # Redis check — bridge 연결 재사용
        redis_bridge = getattr(application.state, "redis_bridge", None)
        if redis_bridge and redis_bridge.redis_client:
            try:
                await redis_bridge.redis_client.ping()
                checks["redis"] = "ok"
            except Exception as e:
                logger.error("health_redis_error", error=str(e))
                checks["redis"] = "unavailable"
                checks["status"] = "degraded"
        else:
            redis_url = os.environ.get("REDIS_URL", "")
            if redis_url:
                checks["redis"] = "not connected"
                checks["status"] = "degraded"

        # Temporal check
        if hasattr(application.state, "temporal_client") and application.state.temporal_client:
            checks["temporal"] = "ok"
        else:
            temporal_host = os.environ.get("TEMPORAL_HOST", "")
            if temporal_host:
                checks["temporal"] = "not connected"
                checks["status"] = "degraded"

        # Langfuse check — offline은 정상 (YAML fallback 사용), degraded 아님
        try:
            from infrastructure.llm.prompt_loader import get_prompt_loader

            loader = get_prompt_loader()
            checks["langfuse"] = "ok" if loader.has_langfuse else "offline (YAML fallback)"
        except Exception as e:
            logger.error("health_langfuse_error", error=str(e))
            checks["langfuse"] = "unavailable"

        # Circuit breaker 상태 (Redis 연결 시에만)
        if redis_bridge and redis_bridge.redis_client:
            try:
                from infrastructure.resilience.circuit_breaker import CircuitBreaker

                cb_services = ["github", "sonarqube", "brightdata", "llm"]
                cb_states = {}
                for svc in cb_services:
                    cb = CircuitBreaker(svc, redis_bridge.redis_client)
                    cb_states[svc] = await cb.get_state()
                checks["circuit_breakers"] = cb_states
            except Exception:
                pass

        status_code = 200 if checks["status"] == "ok" else 503
        return JSONResponse(content=checks, status_code=status_code)

    # Prometheus metrics endpoint
    @application.get("/metrics")
    async def metrics():
        from fastapi.responses import Response
        from infrastructure.observability.metrics import get_metrics_response

        body, content_type = get_metrics_response()
        return Response(content=body, media_type=content_type)

    return application


app = create_app()
