"""
Stack Aggregator — StackSupervisor 결과 통합.

스킬 추출 + API 깊이 + 아키텍처 평가를 종합하여 mastery_score 산출.
"""
from __future__ import annotations

from typing import Any

from application.states.stack_state import StackState


async def stack_aggregator(state: StackState) -> dict[str, Any]:
    """스택 분석 결과를 통합한다."""
    skill_extraction = state.get("skill_extraction")
    api_depth_scores = state.get("api_depth_scores", [])
    architecture_eval = state.get("architecture_eval")

    scores: list[float] = []

    # 1. 스킬 기반 점수 (숙련도 분포)
    if skill_extraction and skill_extraction.get("skills"):
        proficiency_map = {"beginner": 25, "intermediate": 50, "advanced": 75, "expert": 100}
        skill_scores = [
            proficiency_map.get(s.get("proficiency", "beginner"), 25)
            for s in skill_extraction["skills"]
        ]
        scores.append(sum(skill_scores) / len(skill_scores))

    # 2. API 깊이 점수
    if api_depth_scores:
        avg_depth = sum(s.get("depth_score", 0) for s in api_depth_scores) / len(api_depth_scores)
        scores.append(avg_depth * 100)

    # 3. 아키텍처 점수
    if architecture_eval:
        scores.append(architecture_eval.get("overall_score", 0.5) * 100)

    mastery_score = sum(scores) / len(scores) if scores else 50.0

    summary = {
        "primary_language": (
            skill_extraction.get("primary_language") if skill_extraction else None
        ),
        "total_skills_detected": (
            len(skill_extraction.get("skills", [])) if skill_extraction else 0
        ),
        "frameworks": skill_extraction.get("frameworks", []) if skill_extraction else [],
        "avg_api_depth": (
            sum(s.get("depth_score", 0) for s in api_depth_scores) / len(api_depth_scores)
            if api_depth_scores
            else 0
        ),
        "architecture_patterns": (
            architecture_eval.get("patterns_detected", []) if architecture_eval else []
        ),
        "architecture_score": (
            architecture_eval.get("overall_score") if architecture_eval else None
        ),
    }

    return {
        "stack_summary": summary,
        "mastery_score": round(mastery_score, 2),
    }
