"""
Forensic Aggregator — ForensicSupervisor 결과 통합.

모든 Worker 결과를 종합하여 forensic_summary + authenticity_score를 산출한다.
"""
from __future__ import annotations

from typing import Any

from application.states.forensic_state import ForensicState


async def forensic_aggregator(state: ForensicState) -> dict[str, Any]:
    """포렌식 분석 결과를 통합한다."""
    identity = state.get("identity_cluster")
    pure_contributions = state.get("pure_contributions", [])
    vibector_scores = state.get("vibector_scores", [])
    clave_fingerprint = state.get("clave_fingerprint")
    plagiarism_report = state.get("plagiarism_report")

    # Authenticity Score 산출 (0.0 ~ 1.0)
    scores: list[float] = []

    # 1. AI 코드 비율 (낮을수록 좋음)
    if vibector_scores:
        avg_ai = sum(v.get("ai_suspicion_score", 0) for v in vibector_scores) / len(
            vibector_scores
        )
        scores.append(1.0 - avg_ai)  # 역전: 인간 작성 비율

    # 2. 스타일 일관성 (높을수록 좋음)
    if clave_fingerprint:
        scores.append(clave_fingerprint.get("consistency_score", 0.5))

    # 3. 표절 비율 (낮을수록 좋음)
    if plagiarism_report:
        scores.append(1.0 - plagiarism_report.get("plagiarism_ratio", 0))

    authenticity = sum(scores) / len(scores) if scores else 0.5

    # 순수 로직 기여 통계
    total_pure_lines = sum(c.get("pure_logic_lines", 0) for c in pure_contributions)
    total_files = len(pure_contributions)

    summary = {
        "identity": identity,
        "total_files_analyzed": total_files,
        "total_pure_logic_lines": total_pure_lines,
        "ai_detection": {
            "snippets_analyzed": len(vibector_scores),
            "avg_suspicion": (
                sum(v.get("ai_suspicion_score", 0) for v in vibector_scores) / len(vibector_scores)
                if vibector_scores
                else 0
            ),
        },
        "style_consistency": clave_fingerprint.get("consistency_score") if clave_fingerprint else None,
        "plagiarism": plagiarism_report,
        "authenticity_score": authenticity,
    }

    return {
        "forensic_summary": summary,
        "authenticity_score": authenticity,
    }
