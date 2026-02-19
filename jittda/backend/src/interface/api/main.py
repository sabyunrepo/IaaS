"""FastAPI Application Factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    application = FastAPI(
        title="Jittda Sniper v5.0",
        version="5.0.0",
        description="AI Interview Script Generator",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API 라우터 등록
    from interface.api.routes.jobs import router as jobs_router
    from interface.api.routes.jobs import ws_router

    application.include_router(jobs_router)
    application.include_router(ws_router)

    @application.get("/health")
    async def health_check():
        return {"status": "ok", "version": "5.0.0"}

    return application


app = create_app()
