"""
RunAnalysis Use Case — 분석 실행 오케스트레이션.

MetaAgent Graph를 컴파일하고 Checkpointer와 함께 실행한다.
이벤트 콜백을 통해 실시간 진행률을 외부로 전달한다.

G7: 노드 실행 시 구조화된 WS 이벤트 발행.
G9: PostgreSQL Checkpointer 실패 시 MemorySaver로 자동 폴백.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Awaitable

from application.events import build_node_event
from application.graphs.meta_graph import build_meta_graph
from application.states.meta_state import MetaState
from infrastructure.persistence.repository import JobRepository

logger = logging.getLogger(__name__)

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
        "_quality_verdict": "",
        "errors": [],
    }

    try:
        # G9: Checkpointer — PostgreSQL 우선, 실패 시 MemorySaver 폴백
        checkpointer = await _create_checkpointer(db_url)

        graph = build_meta_graph().compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": job_id}}

        final_state = None
        # G7: astream의 updates를 구조화된 노드 이벤트로 변환하여 발행
        async for event in graph.astream(initial_state, config, stream_mode="updates"):
            # event 형태: {"node_name": {state_delta}}
            for node_name, state_delta in event.items():
                node_event = build_node_event(node_name, state_delta)
                await notify(job_id, node_event)
            final_state = event

        return final_state or {"status": "completed"}

    except Exception as e:
        await job_repo.save_error(job_id, str(e))
        await notify(job_id, {"type": "error", "message": str(e)})
        raise


async def _create_checkpointer(db_url: str) -> Any:
    """Checkpointer를 생성한다. PostgreSQL 우선, 실패 시 MemorySaver 폴백.

    Args:
        db_url: PostgreSQL 연결 문자열. 빈 문자열이면 MemorySaver 사용.

    Returns:
        LangGraph Checkpointer 인스턴스.
    """
    if db_url:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            checkpointer = AsyncPostgresSaver.from_conn_string(db_url)
            await checkpointer.__aenter__()
            logger.info("Using PostgreSQL checkpointer")
            return checkpointer
        except Exception as e:
            logger.warning(
                "PostgreSQL checkpointer unavailable, falling back to MemorySaver: %s", e
            )

    from langgraph.checkpoint.memory import MemorySaver

    logger.info("Using MemorySaver checkpointer (in-memory, non-persistent)")
    return MemorySaver()
