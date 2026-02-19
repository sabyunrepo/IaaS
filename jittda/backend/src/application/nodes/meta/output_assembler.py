"""
OutputAssembler 노드 — 최종 면접 스크립트 조립 (Phase 5).

모든 분석 결과를 종합하여 최종 InterviewScript를 생성하고 DB에 저장한다.
"""
from __future__ import annotations

import os
from typing import Any

from application.states.meta_state import MetaState
from infrastructure.persistence.repository import AnalysisRepository, JobRepository


async def output_assembler_node(state: MetaState) -> dict[str, Any]:
    """최종 면접 스크립트를 조립한다."""
    job_id = state["job_id"]
    db_url = os.environ.get("DATABASE_URL", "")

    analysis_repo = AnalysisRepository(db_url)
    job_repo = JobRepository(db_url)

    # 모든 결과 로드
    profile_ref = state.get("profile_ref")
    questions_ref = state.get("questions_ref")
    candidate_scores = state.get("candidate_scores")

    profile_data = await analysis_repo.get_result(profile_ref) if profile_ref else None
    questions_data = await analysis_repo.get_result(questions_ref) if questions_ref else None

    # 최종 결과 조립
    result = {
        "job_id": job_id,
        "candidate_scores": candidate_scores,
        "profile": profile_data.get("result_data") if profile_data else None,
        "questions": questions_data.get("result_data") if questions_data else None,
        "status": "completed",
    }

    # DB에 최종 결과 저장
    await job_repo.save_result_data(job_id, result)

    return {
        "status": "completed",
        "current_phase": "output",
    }
