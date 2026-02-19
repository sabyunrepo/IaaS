"""
RunAnalysis Use Case — 분석 실행 오케스트레이션.

MetaAgent Graph를 컴파일하고 PostgreSQL Checkpointer와 함께 실행한다.
이벤트 콜백을 통해 실시간 진행률을 외부로 전달한다.
"""
from __future__ import annotations

import os
from typing import Any, Callable, Awaitable

from application.graphs.meta_graph import build_meta_graph
from application.states.meta_state import MetaState
from infrastructure.persistence.repository import JobRepository

# Interface 계층에서 주입하는 이벤트 콜백 타입
EventCallback = Callable[[str, dict[str, Any]], Awaitable[None]]


async def _noop_callback(job_id: str, event: dict[str, Any]) -> None:
    """콜백이 제공되지 않을 때 사용하는 no-op."""


async def run_analysis(
    job_id: str,
    on_event: EventCallback | None = None,
) -> dict[str, Any]:
    """분석 파이프라인을 실행한다.

    Args:
        job_id: 분석 작업 ID.
        on_event: 진행/에러 이벤트를 외부로 전달하는 콜백.
                  Interface 계층에서 WebSocket broadcast 등을 주입한다.
    """
    notify = on_event or _noop_callback
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

            final_state = None
            async for event in graph.astream(initial_state, config, stream_mode="updates"):
                await notify(job_id, {"type": "progress", "event": event})
                final_state = event

            return final_state or {"status": "completed"}

    except Exception as e:
        await job_repo.save_error(job_id, str(e))
        await notify(job_id, {"type": "error", "message": str(e)})
        raise
