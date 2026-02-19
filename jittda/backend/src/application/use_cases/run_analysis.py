"""
RunAnalysis Use Case — 분석 실행 오케스트레이션.

MetaAgent Graph를 컴파일하고 PostgreSQL Checkpointer와 함께 실행한다.
WebSocket을 통해 실시간 진행률을 스트리밍한다.
"""
from __future__ import annotations

import os
from typing import Any

from application.graphs.meta_graph import build_meta_graph
from application.states.meta_state import MetaState
from infrastructure.persistence.repository import JobRepository


async def run_analysis(job_id: str) -> dict[str, Any]:
    """분석 파이프라인을 실행한다."""
    db_url = os.environ.get("DATABASE_URL", "")

    # Job 상태 업데이트
    job_repo = JobRepository(db_url)
    await job_repo.update_status(job_id, "running", progress=0.0)

    # 초기 State 구성
    initial_state: MetaState = {
        "job_id": job_id,
        "input_data_ref": job_id,
        "identity_cluster_ref": None,
        "forensic_result_ref": None,
        "logic_result_ref": None,
        "stack_result_ref": None,
        "profile_ref": None,
        "candidate_scores": None,
        "questions_ref": None,
        "status": "pending",
        "current_phase": "input_router",
        "revision_count": 0,
        "errors": [],
    }

    try:
        # PostgreSQL Checkpointer로 컴파일
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:
            graph = build_meta_graph().compile(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": job_id}}

            # WebSocket 스트리밍
            from interface.websocket.ws_manager import ws_manager

            final_state = None
            async for event in graph.astream(initial_state, config, stream_mode="updates"):
                await ws_manager.broadcast(job_id, {
                    "type": "progress",
                    "event": event,
                })
                final_state = event

            return final_state or {"status": "completed"}

    except Exception as e:
        await job_repo.save_error(job_id, str(e))
        from interface.websocket.ws_manager import ws_manager

        await ws_manager.broadcast(job_id, {
            "type": "error",
            "message": str(e),
        })
        raise
