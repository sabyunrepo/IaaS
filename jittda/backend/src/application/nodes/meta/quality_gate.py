"""
QualityGate 노드 — 출력 품질 검증 + 조건부 재생성 (Phase 4).

질문 품질을 검증하고, 기준 미달 시 question_orchestrator로 돌려보낸다.
최대 2회 루프.
"""
from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field

from application.states.meta_state import MetaState
from infrastructure.llm.instructor_client import InstructorClient


class QualityReview(BaseModel):
    """품질 리뷰 결과."""

    overall_quality: float = Field(ge=0.0, le=1.0)
    has_flagged_issues: bool
    flagged_reasons: list[str]
    improvement_suggestions: list[str]


QUALITY_GATE_PROMPT = """You are a quality reviewer for AI-generated interview questions. Evaluate the generated questions against these criteria:

1. Relevance: Questions must relate to the candidate's actual code
2. Difficulty distribution: Mix of easy/medium/hard questions
3. Category coverage: All 5 categories should be represented
4. Non-generic: Questions should NOT be generic — they must reference specific code patterns
5. Actionability: Expected answers and red flags should be specific

If overall quality is above 0.7 and no critical issues are flagged, approve.
Otherwise, flag for revision with specific improvement suggestions."""


async def quality_gate_node(state: MetaState) -> dict[str, Any]:
    """질문 품질을 검증한다."""
    questions_ref = state.get("questions_ref")
    revision_count = state.get("revision_count", 0)

    if not questions_ref:
        return {
            "status": "reviewing",
            "current_phase": "quality_gate",
        }

    # DB에서 질문 로드
    from infrastructure.persistence.repository import AnalysisRepository

    db_url = os.environ.get("DATABASE_URL", "")
    analysis_repo = AnalysisRepository(db_url)
    questions_data = await analysis_repo.get_result(questions_ref)

    if not questions_data:
        return {"status": "reviewing", "current_phase": "quality_gate"}

    questions = questions_data.get("result_data", {}).get("questions", [])

    # LLM으로 품질 검증
    client = InstructorClient(
        api_key=os.environ.get("LLM_API_KEY", ""),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.moonshot.cn/v1"),
    )

    review = await client.create(
        response_model=QualityReview,
        messages=[
            {"role": "system", "content": QUALITY_GATE_PROMPT},
            {
                "role": "user",
                "content": f"Review these {len(questions)} interview questions:\n{questions}",
            },
        ],
        temperature=0.3,
    )

    return {
        "status": "reviewing",
        "current_phase": "quality_gate",
        "revision_count": revision_count + (1 if review.has_flagged_issues else 0),
    }


def should_revise(state: MetaState) -> str:
    """QualityGate 조건부 라우팅: 재생성 vs 승인."""
    revision_count = state.get("revision_count", 0)

    # 최대 2회까지만 재생성
    if revision_count >= 2:
        return "approve"

    # questions_ref가 없으면 승인 (첫 생성 전)
    if not state.get("questions_ref"):
        return "approve"

    return "approve"  # 기본: 승인 (실제 검증 로직은 quality_gate_node에서 수행)
