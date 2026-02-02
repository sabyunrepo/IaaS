"""
backend/app/api/routes/ws.py
WebSocket 실시간 Job 진행률 스트리밍
"""
import asyncio
import json
import logging

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
                await websocket.send_json({"event": "query_error", "message": str(e)})
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
