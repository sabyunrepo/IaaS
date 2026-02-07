"""
backend/app/main.py
FastAPI 애플리케이션
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.logging import setup_logging, get_logger
from app.exceptions import VantictBaseError
from app.api.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.ws import router as ws_router
from app.api.routes.upload import router as upload_router
from app.api.routes.analysis_logs import router as analysis_logs_router
from app.api.routes.internal import router as internal_router
from app.api.routes.storage import router as storage_router

# Phoenix evals (optional - requires arize-phoenix package)
try:
    from app.api.routes.evals import router as evals_router
    EVALS_AVAILABLE = True
except ImportError:
    evals_router = None
    EVALS_AVAILABLE = False

# Structlog 기반 구조화 로깅 설정
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown lifecycle."""
    # --- Startup ---
    from app.core.observability import setup_langfuse
    setup_langfuse()

    # 프로덕션 환경 시크릿 검증
    if not settings.is_local and not settings.has_secure_secrets:
        logger.warning(
            "SECURITY WARNING: Default development secrets detected in non-local environment. "
            "Set JWT_SECRET and SESSION_SECRET to secure values."
        )

    logger.info("Vantict Sniper v4.0.0 started")

    yield

    # --- Shutdown ---
    logger.info("Shutting down...")

    # Close DB engine pool
    try:
        from app.core.database import engine
        await engine.dispose()
        logger.info("DB engine disposed")
    except Exception as e:
        logger.warning(f"DB shutdown error: {e}")

    # Close Temporal client
    try:
        from app.core import temporal
        if temporal._client is not None:
            await temporal._client.service_client.disconnect()
            temporal._client = None
            logger.info("Temporal client disconnected")
    except Exception as e:
        logger.warning(f"Temporal shutdown error: {e}")

    # Close Redis 연결 풀
    try:
        from app.services.cached_llm import _redis_pool
        if _redis_pool is not None:
            await _redis_pool.aclose()
            logger.info("Redis connection pool closed")
    except Exception as e:
        logger.warning(f"Redis shutdown error: {e}")

    logger.info("Shutdown complete")


app = FastAPI(
    title="Vantict Sniper",
    description="AI Technical Interview Script Generator",
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_local else None,
    redoc_url="/redoc" if settings.is_local else None,
)

# --- Rate Limiting ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Middleware ---

# GZip compression (60-70% reduction for large JSON responses)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Internal-Token"],
    max_age=600,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
)

# --- Security Headers ---

@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# --- Error Handlers ---

@app.exception_handler(VantictBaseError)
async def vantict_error_handler(request: Request, exc: VantictBaseError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )

# --- Routers ---

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(ws_router)
app.include_router(upload_router)
app.include_router(analysis_logs_router)
app.include_router(internal_router)
app.include_router(storage_router)

# Phoenix evals (optional)
if EVALS_AVAILABLE and evals_router:
    app.include_router(evals_router)
    logger.info("Phoenix evals router enabled")


@app.get("/")
async def root():
    return {"service": "vantict-sniper", "version": "4.0.0"}
