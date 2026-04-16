"""
PlanGenerator 노드 — LLM 기반 실행 계획 동적 생성 (Phase 1).

입력 데이터를 기반으로 분석 전략(어떤 분석을 수행할지)을 결정한다.
"""
from __future__ import annotations

import logging
from typing import Any

from application.states.meta_state import MetaState
from infrastructure.persistence.repository import JobRepository

logger = logging.getLogger(__name__)


async def plan_generator_node(state: MetaState) -> dict[str, Any]:
    """분석 실행 계획을 생성한다."""
    job_id = state["job_id"]

    try:
        repo = JobRepository()
        job = await repo.get(job_id)

        if not job:
            return {"status": "failed", "errors": state.get("errors", []) + ["Job not found"]}

        input_data = job.get("input_data", {})

        # GitHub URL 유효성 확인
        github_urls = input_data.get("github_urls", [])
        if not github_urls and not input_data.get("candidate_username"):
            return {
                "status": "failed",
                "errors": state.get("errors", []) + ["No GitHub URLs or username provided"],
            }

        await repo.update_status(job_id, "analyzing", progress=0.1)

        return {
            "status": "analyzing",
            "current_phase": "analysis",
        }
    except Exception as e:
        logger.error("plan_generator_node failed for job %s: %s", job_id, e)
        return {
            "status": "failed",
            "errors": state.get("errors", []) + [f"plan_generator: {e}"],
        }
