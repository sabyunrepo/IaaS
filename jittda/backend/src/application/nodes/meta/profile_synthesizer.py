"""
ProfileSynthesizer 노드 — Fan-in: 모든 분석 결과 통합 (Phase 2.5).

ForensicSupervisor + StackSupervisor 결과를 종합하여
UnifiedCandidateProfile + 4대 지표 점수를 산출한다.
"""
from __future__ import annotations

import logging
from typing import Any

from application.states.meta_state import MetaState
from domain.scoring.calculator import calculate_weighted_score
from domain.scoring.models import MetricScore, MetricType
from infrastructure.persistence.repository import (
    AnalysisRepository,
    JobRepository,
    ScoreRepository,
)

logger = logging.getLogger(__name__)


async def profile_synthesizer_node(state: MetaState) -> dict[str, Any]:
    """분석 결과를 종합하여 후보자 프로필 + 점수를 산출한다."""
    job_id = state["job_id"]

    try:
        analysis_repo = AnalysisRepository()
        score_repo = ScoreRepository()
        job_repo = JobRepository()

        # DB에서 각 Supervisor 결과 로드
        forensic_ref = state.get("forensic_result_ref")
        logic_ref = state.get("logic_result_ref")
        stack_ref = state.get("stack_result_ref")

        forensic_data = await analysis_repo.get_result(forensic_ref) if forensic_ref else None
        logic_data = await analysis_repo.get_result(logic_ref) if logic_ref else None
        stack_data = await analysis_repo.get_result(stack_ref) if stack_ref else None

        # 4대 지표 MetricScore 구성
        scores: dict[MetricType, MetricScore] = {}

        # Logic Score
        logic_result = logic_data.get("result_data", {}) if logic_data else {}
        logic_score = logic_result.get("logic_score", 50.0)
        scores[MetricType.LOGIC] = MetricScore(
            metric_type=MetricType.LOGIC,
            raw_score=logic_score,
            normalized_score=logic_score,
            sub_scores={
                "cyclomatic_complexity": logic_result.get("avg_cyclomatic_complexity", 0),
                "maintainability_index": logic_result.get("avg_maintainability_index", 0),
            },
            evidence_count=logic_result.get("files_analyzed", 0),
        )

        # Mastery Score
        stack_result = stack_data.get("result_data", {}) if stack_data else {}
        mastery_score = stack_result.get("mastery_score", 50.0)
        scores[MetricType.MASTERY] = MetricScore(
            metric_type=MetricType.MASTERY,
            raw_score=mastery_score,
            normalized_score=mastery_score,
            sub_scores={
                "api_depth": stack_result.get("avg_api_depth", 0),
                "architecture": stack_result.get("architecture_score", 0) if stack_result.get("architecture_score") else 0,
            },
            evidence_count=stack_result.get("total_skills_detected", 0),
        )

        # Stability Score (로직 복잡도 + 품질 기반)
        stability_score = min(100.0, logic_score * 0.8 + 20)  # 기본 로직 기반 추정
        scores[MetricType.STABILITY] = MetricScore(
            metric_type=MetricType.STABILITY,
            raw_score=stability_score,
            normalized_score=stability_score,
            sub_scores={"logic_based": logic_score},
            evidence_count=logic_result.get("files_analyzed", 0),
        )

        # Authenticity Score
        forensic_result = forensic_data.get("result_data", {}) if forensic_data else {}
        auth_raw = forensic_result.get("authenticity_score", 0.5)
        authenticity_score = auth_raw * 100
        scores[MetricType.AUTHENTICITY] = MetricScore(
            metric_type=MetricType.AUTHENTICITY,
            raw_score=authenticity_score,
            normalized_score=authenticity_score,
            sub_scores={
                "ai_suspicion": forensic_result.get("ai_detection", {}).get("avg_suspicion", 0),
                "style_consistency": forensic_result.get("style_consistency", 0) or 0,
            },
            evidence_count=forensic_result.get("total_files_analyzed", 0),
        )

        # 가중 합산
        candidate_score = calculate_weighted_score(scores)

        # DB 저장
        profile_id = await analysis_repo.save_result(
            job_id,
            "profile_synthesizer",
            "meta",
            {
                "forensic": forensic_result,
                "logic": logic_result,
                "stack": stack_result,
                "scores": candidate_score.model_dump(),
            },
        )

        await score_repo.save(
            job_id,
            candidate_score.logic.normalized_score,
            candidate_score.mastery.normalized_score,
            candidate_score.stability.normalized_score,
            candidate_score.authenticity.normalized_score,
            candidate_score.weighted_total,
            candidate_score.confidence,
        )

        await job_repo.update_status(job_id, "synthesizing", progress=0.6)

        return {
            "profile_ref": profile_id,
            "candidate_scores": candidate_score.model_dump(),
            "status": "synthesizing",
            "current_phase": "questions",
        }
    except Exception as e:
        logger.error("profile_synthesizer_node failed for job %s: %s", job_id, e)
        # 기본 점수로 파이프라인 계속 진행 (질문 생성은 가능)
        default_scores = {
            "logic": {"normalized_score": 50.0},
            "mastery": {"normalized_score": 50.0},
            "stability": {"normalized_score": 50.0},
            "authenticity": {"normalized_score": 50.0},
            "weighted_total": 50.0,
            "confidence": "low",
        }
        return {
            "profile_ref": None,
            "candidate_scores": default_scores,
            "status": "synthesizing",
            "current_phase": "questions",
            "errors": state.get("errors", []) + [f"profile_synthesizer: {e}"],
        }
