"""
Logic Aggregator — LogicSupervisor 결과 통합.

AST 분석 + 복잡도 + 품질 리포트를 종합하여 logic_summary + logic_score 산출.
"""
from __future__ import annotations

from typing import Any

from application.states.logic_state import LogicState


async def logic_aggregator(state: LogicState) -> dict[str, Any]:
    """로직 분석 결과를 통합한다."""
    ast_analysis = state.get("ast_analysis", [])
    complexity_metrics = state.get("complexity_metrics", [])
    quality_report = state.get("quality_report")

    # AST 통계
    total_functions = sum(a.get("total_functions", 0) for a in ast_analysis)
    total_classes = sum(a.get("total_classes", 0) for a in ast_analysis)
    languages_used = list({a.get("language", "") for a in ast_analysis if a.get("language")})

    # 복잡도 평균
    avg_cc = 0.0
    avg_mi = 0.0
    if complexity_metrics:
        avg_cc = sum(m.get("cyclomatic_complexity", 0) for m in complexity_metrics) / len(
            complexity_metrics
        )
        avg_mi = sum(m.get("maintainability_index", 0) for m in complexity_metrics) / len(
            complexity_metrics
        )

    # Logic Score 산출 (0~100)
    # MI 기반 (0~100), CC 패널티 (높을수록 감점)
    mi_score = min(avg_mi, 100.0)
    cc_penalty = min(avg_cc * 2, 30.0)  # CC 15 이상이면 최대 30점 감점
    logic_score = max(0.0, min(100.0, mi_score - cc_penalty))

    # 품질 리포트 보너스/패널티
    if quality_report and quality_report.get("status") not in ("skipped", "unavailable"):
        bugs = quality_report.get("bugs", 0)
        vulnerabilities = quality_report.get("vulnerabilities", 0)
        quality_penalty = min((bugs + vulnerabilities) * 2, 20.0)
        logic_score = max(0.0, logic_score - quality_penalty)

    summary = {
        "total_functions": total_functions,
        "total_classes": total_classes,
        "languages": languages_used,
        "files_analyzed": len(ast_analysis),
        "avg_cyclomatic_complexity": round(avg_cc, 2),
        "avg_maintainability_index": round(avg_mi, 2),
        "quality_report_status": quality_report.get("status") if quality_report else "none",
    }

    return {
        "logic_summary": summary,
        "logic_score": round(logic_score, 2),
    }
