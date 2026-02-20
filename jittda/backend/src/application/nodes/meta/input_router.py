"""
InputRouter 노드 — 입력 파싱 + 소스 라우팅 (Phase 0).

Job의 input_data를 파싱하여 분석에 필요한 정보를 추출하고
적절한 분석 경로를 결정한다.
"""
from __future__ import annotations

import logging
from typing import Any

from application.states.meta_state import MetaState
from infrastructure.persistence.repository import JobRepository

logger = logging.getLogger(__name__)


async def input_router_node(state: MetaState) -> dict[str, Any]:
    """입력 데이터를 파싱하고 분석 경로를 결정한다."""
    import os

    job_id = state["job_id"]

    try:
        # DB에서 input_data 로드
        repo = JobRepository(os.environ.get("DATABASE_URL", ""))
        job = await repo.get(job_id)

        if not job:
            return {
                "status": "failed",
                "errors": state.get("errors", []) + [f"Job {job_id} not found"],
            }

        input_data = job.get("input_data", {})

        # 상태 업데이트
        await repo.update_status(job_id, "collecting", progress=0.05)

        return {
            "input_data_ref": job_id,
            "status": "collecting",
            "current_phase": "plan_generator",
        }
    except Exception as e:
        logger.error("input_router_node failed for job %s: %s", job_id, e)
        return {
            "status": "failed",
            "errors": state.get("errors", []) + [f"input_router: {e}"],
        }
