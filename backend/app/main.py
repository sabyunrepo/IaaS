"""
backend/app/main.py
FastAPI 애플리케이션
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.exceptions import VantictBaseError
from app.api.health import router as health_router

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Vantict Sniper",
    description="AI Technical Interview Script Generator",
    version="4.0.0",
    docs_url="/docs" if settings.is_local else None,
    redoc_url="/redoc" if settings.is_local else None,
)

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


@app.get("/")
async def root():
    return {"service": "vantict-sniper", "version": "4.0.0"}
