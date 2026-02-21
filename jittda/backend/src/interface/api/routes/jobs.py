"""
Jobs API — 분석 Job CRUD + WebSocket 스트리밍.

GET /api/jobs — Job 목록 조회
POST /api/jobs — 분석 Job 생성 + Temporal Workflow 실행
GET /api/jobs/{job_id} — Job 상태 조회
GET /api/jobs/{job_id}/result — Job 결과 조회
WS /ws/jobs/{job_id} — 실시간 진행률 스트리밍 (Redis PubSub 브릿지)
"""
from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect

from infrastructure.persistence.repository import JobRepository
from interface.api.middleware.auth import get_optional_user
from interface.api.schemas.job_schemas import (
    JobCreateRequest,
    JobDetailResponse,
    JobResponse,
)
from interface.websocket.ws_manager import ws_manager

router = APIRouter(prefix="/api/jobs", tags=["jobs"])
ws_router = APIRouter()


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    limit: int = Query(default=100, ge=1, le=100),
    user: dict = Depends(get_optional_user),
):
    """Job 목록을 조회한다. 인증된 사용자는 자신의 Job만, 미인증은 빈 목록."""
    if not user:
        return []
    db_url = os.environ.get("DATABASE_URL", "")
    repo = JobRepository(db_url)
    jobs = await repo.list_recent(limit=limit, user_id=user["user_id"])
    return [JobResponse(**j) for j in jobs]


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    request_body: JobCreateRequest,
    request: Request,
    user: dict = Depends(get_optional_user),
):
    """분석 Job을 생성하고 Temporal Workflow를 시작한다."""
    db_url = os.environ.get("DATABASE_URL", "")
    repo = JobRepository(db_url)

    # 입력 검증
    if not request_body.github_urls and not request_body.candidate_username:
        raise HTTPException(400, "github_urls 또는 candidate_username이 필요합니다.")

    # Job 생성
    user_id = user["user_id"] if user else None
    job_id = await repo.create(request_body.model_dump(), user_id=user_id)

    # Temporal Workflow 시작
    temporal_client = getattr(request.app.state, "temporal_client", None)
    if not temporal_client:
        raise HTTPException(503, "Temporal service unavailable")

    from application.temporal import TASK_QUEUE
    from application.temporal.workflows import AnalysisPipeline

    await temporal_client.start_workflow(
        AnalysisPipeline.run,
        job_id,
        id=f"analysis-{job_id}",
        task_queue=TASK_QUEUE,
    )

    return JobResponse(id=job_id, status="pending", progress=0.0)


def _validate_uuid(job_id: str) -> None:
    """UUID 형식을 검증한다."""
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(400, "Invalid job ID format") from None


def _check_job_access(job: dict, user: dict | None) -> None:
    """Job 소유권을 검증한다. 소유자가 있는 Job은 인증된 소유자만 접근 가능."""
    job_owner = job.get("user_id")
    if job_owner:
        if not user or user["user_id"] != job_owner:
            raise HTTPException(403, "Access denied")


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: str, user: dict | None = Depends(get_optional_user)):
    """Job 상태를 조회한다."""
    _validate_uuid(job_id)
    db_url = os.environ.get("DATABASE_URL", "")
    repo = JobRepository(db_url)

    job = await repo.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    _check_job_access(job, user)
    return JobDetailResponse(**job)


@router.get("/{job_id}/result")
async def get_job_result(job_id: str, user: dict | None = Depends(get_optional_user)):
    """Job 결과를 조회한다."""
    _validate_uuid(job_id)
    db_url = os.environ.get("DATABASE_URL", "")
    repo = JobRepository(db_url)

    job = await repo.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    _check_job_access(job, user)
    if job["status"] != "completed":
        raise HTTPException(400, f"Job is not completed yet. Status: {job['status']}")

    return job.get("result_data", {})


@ws_router.websocket("/ws/jobs/{job_id}")
async def job_websocket(websocket: WebSocket, job_id: str):
    """Job 실시간 진행률 WebSocket — Redis PubSub 브릿지 연동."""
    await ws_manager.connect(job_id, websocket)

    # Redis PubSub 구독 시작
    redis_bridge = getattr(websocket.app.state, "redis_bridge", None)
    if redis_bridge:
        await redis_bridge.subscribe(job_id)

    try:
        while True:
            # 클라이언트 메시지 대기 (keepalive)
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(job_id, websocket)
        # WebSocket 연결이 없으면 Redis 구독도 해제
        if redis_bridge and not ws_manager.has_connections(job_id):
            await redis_bridge.unsubscribe(job_id)
