"""
Jobs API — 분석 Job CRUD + WebSocket 스트리밍.

POST /api/jobs — 분석 Job 생성 + 비동기 실행
GET /api/jobs/{job_id} — Job 상태 조회
GET /api/jobs/{job_id}/result — Job 결과 조회
WS /ws/jobs/{job_id} — 실시간 진행률 스트리밍
"""
from __future__ import annotations

import asyncio
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect

from application.use_cases.run_analysis import run_analysis
from infrastructure.persistence.repository import JobRepository
from interface.api.schemas.job_schemas import (
    JobCreateRequest,
    JobDetailResponse,
    JobResponse,
)
from interface.websocket.ws_manager import ws_manager

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
ws_router = APIRouter()


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
):
    """분석 Job을 생성하고 백그라운드에서 실행한다."""
    db_url = os.environ.get("DATABASE_URL", "")
    repo = JobRepository(db_url)

    # 입력 검증
    if not request.github_urls and not request.candidate_username:
        raise HTTPException(400, "github_urls 또는 candidate_username이 필요합니다.")

    # Job 생성
    job_id = await repo.create(request.model_dump())

    # 백그라운드 실행
    background_tasks.add_task(_run_analysis_task, job_id)

    return JobResponse(id=job_id, status="pending", progress=0.0)


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: str):
    """Job 상태를 조회한다."""
    db_url = os.environ.get("DATABASE_URL", "")
    repo = JobRepository(db_url)

    job = await repo.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")

    return JobDetailResponse(**job)


@router.get("/{job_id}/result")
async def get_job_result(job_id: str):
    """Job 결과를 조회한다."""
    db_url = os.environ.get("DATABASE_URL", "")
    repo = JobRepository(db_url)

    job = await repo.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    if job["status"] != "completed":
        raise HTTPException(400, f"Job is not completed yet. Status: {job['status']}")

    return job.get("result_data", {})


@ws_router.websocket("/ws/jobs/{job_id}")
async def job_websocket(websocket: WebSocket, job_id: str):
    """Job 실시간 진행률 WebSocket."""
    await ws_manager.connect(job_id, websocket)
    try:
        while True:
            # 클라이언트 메시지 대기 (keepalive)
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(job_id, websocket)


async def _run_analysis_task(job_id: str) -> None:
    """백그라운드에서 분석을 실행한다."""
    try:
        await run_analysis(job_id, on_event=ws_manager.broadcast)
    except Exception:
        pass  # 에러는 run_analysis 내부에서 DB에 저장됨
