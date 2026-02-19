"""
OutputAssembler 노드 — 최종 면접 스크립트 조립 (Phase 5).

모든 분석 결과를 종합하여 구조화된 최종 출력을 생성하고 DB에 저장한다.
4개 섹션: IntelBrief(3초 요약) + DeepAnalysis(코드 분석) + InterviewScript(질문)
         + DecisionSupport(채용 판단 근거)
"""
from __future__ import annotations

import logging
import os
from typing import Any

from application.states.meta_state import MetaState
from infrastructure.persistence.repository import AnalysisRepository, JobRepository

logger = logging.getLogger(__name__)


def _build_intel_brief(
    candidate_scores: dict | None,
    profile_result: dict,
    forensic_result: dict,
) -> dict[str, Any]:
    """IntelBrief: CEO용 3초 요약 카드."""
    scores = candidate_scores or {}

    # 4대 지표 추출
    logic = scores.get("logic", {}).get("normalized_score", 0)
    mastery = scores.get("mastery", {}).get("normalized_score", 0)
    stability = scores.get("stability", {}).get("normalized_score", 0)
    authenticity = scores.get("authenticity", {}).get("normalized_score", 0)
    weighted_total = scores.get("weighted_total", 0)
    confidence = scores.get("confidence", "low")

    # 신호등 판정 (Green >= 70, Yellow >= 50, Red < 50)
    def _signal(score: float) -> str:
        if score >= 70:
            return "green"
        if score >= 50:
            return "yellow"
        return "red"

    # 등급 산출
    def _grade(total: float) -> str:
        if total >= 90:
            return "A+"
        if total >= 85:
            return "A"
        if total >= 80:
            return "A-"
        if total >= 75:
            return "B+"
        if total >= 70:
            return "B"
        if total >= 65:
            return "B-"
        if total >= 60:
            return "C+"
        if total >= 55:
            return "C"
        return "D"

    # AI 코드 의심률
    ai_detection = forensic_result.get("ai_detection", {})
    ai_suspicion_pct = round(ai_detection.get("avg_suspicion", 0) * 100, 1) if ai_detection else 0

    return {
        "grade": _grade(weighted_total),
        "weighted_total": round(weighted_total, 1),
        "confidence": confidence,
        "four_axes": {
            "logic": {"score": round(logic, 1), "signal": _signal(logic)},
            "mastery": {"score": round(mastery, 1), "signal": _signal(mastery)},
            "stability": {"score": round(stability, 1), "signal": _signal(stability)},
            "authenticity": {"score": round(authenticity, 1), "signal": _signal(authenticity)},
        },
        "ai_code_suspicion_pct": ai_suspicion_pct,
    }


def _build_deep_analysis(
    forensic_result: dict,
    logic_result: dict,
    stack_result: dict,
) -> dict[str, Any]:
    """DeepAnalysis: 코드 분석 상세 섹션."""
    return {
        "forensic": {
            "total_files_analyzed": forensic_result.get("total_files_analyzed", 0),
            "ai_detection": forensic_result.get("ai_detection"),
            "style_consistency": forensic_result.get("style_consistency"),
            "plagiarism": forensic_result.get("plagiarism"),
        },
        "logic": {
            "files_analyzed": logic_result.get("files_analyzed", 0),
            "avg_cyclomatic_complexity": logic_result.get("avg_cyclomatic_complexity", 0),
            "avg_maintainability_index": logic_result.get("avg_maintainability_index", 0),
            "logic_summary": logic_result.get("logic_summary"),
        },
        "stack": {
            "total_skills_detected": stack_result.get("total_skills_detected", 0),
            "avg_api_depth": stack_result.get("avg_api_depth", 0),
            "architecture_score": stack_result.get("architecture_score"),
            "stack_summary": stack_result.get("stack_summary"),
        },
    }


def _build_interview_script(
    questions_result: dict,
) -> dict[str, Any]:
    """InterviewScript: 질문 세트 구조화."""
    questions = questions_result.get("questions", [])

    # 전략별 그룹핑
    by_strategy: dict[str, list] = {}
    for q in questions:
        strategy = q.get("strategy", "unknown")
        by_strategy.setdefault(strategy, []).append(q)

    # 카테고리별 그룹핑
    by_category: dict[str, list] = {}
    for q in questions:
        category = q.get("category", "unknown")
        by_category.setdefault(category, []).append(q)

    return {
        "total_questions": len(questions),
        "questions": questions,
        "by_strategy": by_strategy,
        "by_category": by_category,
        "strategy_distribution": questions_result.get("strategy_distribution", {}),
        "category_distribution": questions_result.get("category_distribution", {}),
        "enhancement_applied": questions_result.get("enhancement_applied", False),
    }


# 4대 지표 이름 (한→영 매핑용)
_AXIS_LABELS: dict[str, str] = {
    "logic": "논리적 사고력",
    "mastery": "기술 숙련도",
    "stability": "코드 안정성",
    "authenticity": "코드 진정성",
}


def _build_decision_support(
    candidate_scores: dict | None,
    forensic_result: dict,
    profile_result: dict,
) -> dict[str, Any]:
    """DecisionSupport: 4대 지표 기반 채용 판단 근거."""
    scores = candidate_scores or {}

    # 4대 지표 추출
    logic = scores.get("logic", {}).get("normalized_score", 0)
    mastery = scores.get("mastery", {}).get("normalized_score", 0)
    stability = scores.get("stability", {}).get("normalized_score", 0)
    authenticity = scores.get("authenticity", {}).get("normalized_score", 0)
    weighted_total = scores.get("weighted_total", 0)
    confidence = scores.get("confidence", "low")

    axes = {
        "logic": logic,
        "mastery": mastery,
        "stability": stability,
        "authenticity": authenticity,
    }

    # 신호등 판정 (동일 기준: Green >= 70, Yellow >= 50, Red < 50)
    def _signal(score: float) -> str:
        if score >= 70:
            return "green"
        if score >= 50:
            return "yellow"
        return "red"

    # 축별 verdict 텍스트
    def _verdict_text(score: float) -> str:
        if score >= 70:
            return "Strong"
        if score >= 50:
            return "Moderate"
        return "Weak"

    # red 축 개수 산출
    red_count = sum(1 for s in axes.values() if s < 50)
    all_above_50 = all(s >= 50 for s in axes.values())

    # 추천 로직
    if weighted_total >= 70 and all_above_50:
        recommendation = "hire"
    elif weighted_total >= 60 and red_count <= 1:
        recommendation = "conditional_hire"
    else:
        recommendation = "no_hire"

    # strengths: green(>= 70) 축 근거
    strengths: list[str] = []
    for axis_key, score in axes.items():
        if score >= 70:
            label = _AXIS_LABELS[axis_key]
            strengths.append(f"{label}({axis_key}) {round(score, 1)}점 — 우수")

    # concerns: yellow/red(< 70) 축 근거
    concerns: list[str] = []
    for axis_key, score in axes.items():
        if score < 70:
            label = _AXIS_LABELS[axis_key]
            signal = _signal(score)
            level = "주의" if signal == "yellow" else "경고"
            concerns.append(f"{label}({axis_key}) {round(score, 1)}점 — {level}")

    # risk_factors
    risk_factors: list[str] = []

    # AI 코드 의심률
    ai_detection = forensic_result.get("ai_detection", {})
    ai_suspicion = ai_detection.get("avg_suspicion", 0) if ai_detection else 0
    if ai_suspicion > 0.3:
        pct = round(ai_suspicion * 100, 1)
        risk_factors.append(f"AI 코드 의심률 {pct}% — 코드 진정성 검증 필요")

    # 안정성 낮음
    if stability < 50:
        risk_factors.append(
            f"코드 안정성 {round(stability, 1)}점 — 유지보수 리스크"
        )

    # 진정성 낮음
    if authenticity < 50:
        risk_factors.append(
            f"코드 진정성 {round(authenticity, 1)}점 — 본인 작성 여부 검증 필요"
        )

    # recommendation_reason 생성
    if recommendation == "hire":
        recommendation_reason = (
            f"종합 {round(weighted_total, 1)}점, "
            f"4대 지표 모두 50점 이상으로 채용 권장"
        )
    elif recommendation == "conditional_hire":
        weak_axes = [k for k, v in axes.items() if v < 50]
        weak_str = ", ".join(_AXIS_LABELS[k] for k in weak_axes) if weak_axes else "없음"
        recommendation_reason = (
            f"종합 {round(weighted_total, 1)}점, "
            f"약점 지표({weak_str}) 보완 확인 후 조건부 채용 검토"
        )
    else:
        recommendation_reason = (
            f"종합 {round(weighted_total, 1)}점, "
            f"red 지표 {red_count}개 — 채용 비권장"
        )

    # four_axes_summary
    four_axes_summary = {}
    for axis_key, score in axes.items():
        four_axes_summary[axis_key] = {
            "score": round(score, 1),
            "verdict": _verdict_text(score),
        }

    return {
        "recommendation": recommendation,
        "recommendation_reason": recommendation_reason,
        "strengths": strengths,
        "concerns": concerns,
        "risk_factors": risk_factors,
        "confidence": confidence,
        "four_axes_summary": four_axes_summary,
    }


async def output_assembler_node(state: MetaState) -> dict[str, Any]:
    """최종 면접 스크립트를 구조화하여 조립한다."""
    job_id = state["job_id"]
    db_url = os.environ.get("DATABASE_URL", "")

    analysis_repo = AnalysisRepository(db_url)
    job_repo = JobRepository(db_url)

    # 모든 결과 로드
    profile_ref = state.get("profile_ref")
    questions_ref = state.get("questions_ref")
    forensic_ref = state.get("forensic_result_ref")
    logic_ref = state.get("logic_result_ref")
    stack_ref = state.get("stack_result_ref")
    candidate_scores = state.get("candidate_scores")

    profile_data = await analysis_repo.get_result(profile_ref) if profile_ref else None
    questions_data = await analysis_repo.get_result(questions_ref) if questions_ref else None
    forensic_data = await analysis_repo.get_result(forensic_ref) if forensic_ref else None
    logic_data = await analysis_repo.get_result(logic_ref) if logic_ref else None
    stack_data = await analysis_repo.get_result(stack_ref) if stack_ref else None

    profile_result = profile_data.get("result_data", {}) if profile_data else {}
    questions_result = questions_data.get("result_data", {}) if questions_data else {}
    forensic_result = forensic_data.get("result_data", {}) if forensic_data else {}
    logic_result = logic_data.get("result_data", {}) if logic_data else {}
    stack_result = stack_data.get("result_data", {}) if stack_data else {}

    # 4개 섹션 조립
    intel_brief = _build_intel_brief(candidate_scores, profile_result, forensic_result)
    deep_analysis = _build_deep_analysis(forensic_result, logic_result, stack_result)
    interview_script = _build_interview_script(questions_result)
    decision_support = _build_decision_support(
        candidate_scores, forensic_result, profile_result
    )

    # 최종 구조화 결과
    result = {
        "job_id": job_id,
        "version": "5.0",
        "intel_brief": intel_brief,
        "deep_analysis": deep_analysis,
        "interview_script": interview_script,
        "decision_support": decision_support,
        "candidate_scores": candidate_scores,
        "errors": state.get("errors", []),
        "status": "completed",
    }

    # DB에 최종 결과 저장
    try:
        await job_repo.save_result_data(job_id, result)
    except Exception as e:
        logger.error("output_assembler: failed to save result: %s", e)
        return {
            "status": "failed",
            "current_phase": "output",
            "errors": state.get("errors", []) + [f"output_assembler: {e}"],
        }

    logger.info(
        "output_assembler completed: job=%s grade=%s questions=%d recommendation=%s",
        job_id,
        intel_brief.get("grade", "N/A"),
        interview_script.get("total_questions", 0),
        decision_support.get("recommendation", "N/A"),
    )

    return {
        "status": "completed",
        "current_phase": "output",
    }
