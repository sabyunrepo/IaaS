"""
backend/app/main.py
FastAPI 애플리케이션
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.rate_limit import limiter
from app.exceptions import VantictBaseError
from app.api.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.ws import router as ws_router
from app.api.routes.upload import router as upload_router

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / Shutdown lifecycle."""
    # --- Startup ---
    from app.core.observability import setup_langfuse
    setup_langfuse()
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

    # Close Redis (CachedLLMService)
    try:
        from app.services.cached_llm import CachedLLMService
        # CachedLLMService instances are per-use; just close any module-level redis
    except Exception:
        pass

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
)

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


@app.get("/")
async def root():
    return {"service": "vantict-sniper", "version": "4.0.0"}
