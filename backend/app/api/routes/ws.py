"""
backend/app/api/routes/ws.py
WebSocket 실시간 Job 진행률 및 분석 로그 스트리밍
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/api/v1/jobs/{job_id}/ws")
async def job_progress_ws(
    websocket: WebSocket,
    job_id: str,
    token: str = Query(default=""),
):
    """Job 진행률을 WebSocket으로 실시간 스트리밍.

    인증: ws://host/api/v1/jobs/{job_id}/ws?token=<api_key>
    Temporal workflow query를 2초 간격으로 폴링하여 전송.
    """
    # Authenticate
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        from app.api.deps import validate_api_key
        from app.core.database import async_session

        async with async_session() as db:
            user = await validate_api_key(token, db)
            if not user:
                await websocket.close(code=4003, reason="Invalid token")
                return
    except Exception:
        await websocket.close(code=4003, reason="Authentication failed")
        return

    await websocket.accept()

    try:
        # Look up job and get workflow handle
        from app.core.database import async_session
        from app.models.database import JobDB
        from sqlalchemy import select
        import uuid

        async with async_session() as db:
            result = await db.execute(
                select(JobDB).where(JobDB.id == uuid.UUID(job_id))
            )
            job = result.scalar_one_or_none()

        if not job or not job.temporal_workflow_id:
            await websocket.send_json({"error": "Job not found or no workflow"})
            await websocket.close(code=4004)
            return

        if job.user_id != user.id:
            await websocket.send_json({"error": "Not authorized"})
            await websocket.close(code=4003)
            return

        # Poll Temporal for progress
        from app.core.temporal import get_temporal_client
        client = await get_temporal_client()
        handle = client.get_workflow_handle(job.temporal_workflow_id)

        last_progress = None
        while True:
            try:
                progress = await handle.query("get_progress")
                # Only send if changed
                if progress != last_progress:
                    await websocket.send_json(progress)
                    last_progress = progress

                # Stop if terminal state
                if progress.get("status") in ("completed", "failed"):
                    await websocket.send_json({"event": "done", **progress})
                    break

            except Exception as e:
                logger.debug(f"Workflow query failed: {e}")
                await websocket.send_json({"event": "query_error", "message": "Workflow query failed"})
                break

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


@router.websocket("/api/v1/jobs/{job_id}/logs/ws")
async def job_logs_ws(
    websocket: WebSocket,
    job_id: str,
    token: str = Query(default=""),
):
    """Job 분석 로그를 WebSocket으로 실시간 스트리밍.

    인증: ws://host/api/v1/jobs/{job_id}/logs/ws?token=<api_key>
    DB 폴링으로 새 로그 전송 (2초 간격).
    """
    # Authenticate
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        from app.api.deps import validate_api_key
        from app.core.database import async_session

        async with async_session() as db:
            user = await validate_api_key(token, db)
            if not user:
                await websocket.close(code=4003, reason="Invalid token")
                return
    except Exception:
        await websocket.close(code=4003, reason="Authentication failed")
        return

    await websocket.accept()

    try:
        from app.core.database import async_session
        from app.models.database import JobDB
        from app.services.analysis_log_service import AnalysisLogService
        from sqlalchemy import select
        import uuid

        # Verify job exists and user owns it
        async with async_session() as db:
            result = await db.execute(
                select(JobDB).where(JobDB.id == uuid.UUID(job_id))
            )
            job = result.scalar_one_or_none()

        if not job:
            await websocket.send_json({"error": "Job not found"})
            await websocket.close(code=4004)
            return

        if job.user_id != user.id:
            await websocket.send_json({"error": "Not authorized"})
            await websocket.close(code=4003)
            return

        # Track last seen log time
        last_log_time = datetime.now(timezone.utc)

        # Send initial summary
        async with async_session() as db:
            service = AnalysisLogService(db)
            summary = await service.get_analysis_summary(job_id)
            await websocket.send_json({"event": "summary", "data": summary})

        while True:
            try:
                # Check for new logs
                async with async_session() as db:
                    service = AnalysisLogService(db)
                    new_logs = await service.get_logs_since(job_id, last_log_time)

                    if new_logs:
                        for log in new_logs:
                            log_data = {
                                "event": "log",
                                "data": {
                                    "id": str(log.id),
                                    "activity_name": log.activity_name,
                                    "phase": log.phase,
                                    "log_type": log.log_type,
                                    "message": log.message,
                                    "data": log.data or {},
                                    "duration_ms": log.duration_ms,
                                    "created_at": log.created_at.isoformat() if log.created_at else "",
                                },
                            }
                            await websocket.send_json(log_data)
                            if log.created_at:
                                last_log_time = log.created_at

                    # Check job status
                    result = await db.execute(
                        select(JobDB).where(JobDB.id == uuid.UUID(job_id))
                    )
                    job = result.scalar_one_or_none()

                    if job and job.status in ("completed", "failed"):
                        # Send final summary
                        summary = await service.get_analysis_summary(job_id)
                        await websocket.send_json({
                            "event": "done",
                            "status": job.status,
                            "summary": summary,
                        })
                        break

            except Exception as e:
                logger.debug(f"Log polling error: {e}")
                await websocket.send_json({"event": "error", "message": "Log polling failed"})
                break

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        logger.debug(f"Logs WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"Logs WebSocket error: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
