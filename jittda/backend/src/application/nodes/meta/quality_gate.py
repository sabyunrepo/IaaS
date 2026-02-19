"""
QualityGate 노드 — 출력 품질 검증 + 조건부 재생성 (Phase 4).

질문 품질을 검증하고, 기준 미달 시 루프하여 재검증한다.
최대 2회 리비전. should_revise가 conditional edge router로 사용된다.

Flow:
  question_orchestrator → quality_gate → [should_revise] → approve → output_assembler
                                              ↑          → revise ─┘ (self-loop, max 2)
"""
from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel, Field

from application.states.meta_state import MetaState
from infrastructure.llm.instructor_client import InstructorClient
from infrastructure.persistence.repository import AnalysisRepository

logger = logging.getLogger(__name__)

# ─── 최대 리비전 횟수 ────────────────────────────────────────────────
MAX_REVISIONS = 2

# ─── Quality Review 모델 ─────────────────────────────────────────────


class QualityReview(BaseModel):
    """LLM이 반환하는 품질 리뷰 결과."""

    overall_quality: float = Field(
        ge=0.0, le=1.0, description="Overall quality score. 0.7+ means approve."
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Specific quality issues found.",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Concrete improvement suggestions.",
    )
    verdict: str = Field(
        description="Either 'approve' or 'revise'.",
    )


# ─── 프롬프트 ────────────────────────────────────────────────────────

QUALITY_GATE_PROMPT = """\
You are a quality reviewer for AI-generated interview questions.
Evaluate the generated questions against these criteria:

1. **Code Specificity** — Questions MUST reference specific code patterns, files, \
or functions from the candidate's repository. Generic questions (e.g. "What is \
polymorphism?") are unacceptable.

2. **Difficulty Distribution** — There should be a mix of easy, medium, and hard \
questions. All questions at the same difficulty level is a failure.

3. **Category Coverage** — At least 3 of the 5 categories (technical_depth, \
execution_ownership, communication, role_fit, risk_flags) should be represented.

4. **Actionability** — Each question should have clear expected_answer_guide and \
red_flags that a non-developer interviewer can use.

5. **Strategy Diversity** — Questions should come from multiple strategies \
(negative_selection, intentional_complexity, code_evolution).

Scoring:
- overall_quality >= 0.7 AND no critical issues → verdict: "approve"
- overall_quality < 0.7 OR critical issues found → verdict: "revise"

Be strict but fair. If questions are reasonably specific and diverse, approve them."""


# ─── 메인 노드 ────────────────────────────────────────────────────────


async def quality_gate_node(state: MetaState) -> dict[str, Any]:
    """질문 품질을 검증하고, verdict를 state에 기록한다."""
    questions_ref = state.get("questions_ref")
    revision_count = state.get("revision_count", 0)
    job_id = state.get("job_id", "")

    # --- Guard: revision cap reached → force approve without LLM call ---
    if revision_count >= MAX_REVISIONS:
        logger.info(
            "quality_gate: max revisions (%d) reached for job %s — force approve",
            MAX_REVISIONS,
            job_id,
        )
        return {
            "status": "reviewing",
            "current_phase": "quality_gate",
            "_quality_verdict": "approve",
        }

    # --- Guard: no questions ref → approve (nothing to review) ---
    if not questions_ref:
        logger.warning("quality_gate: no questions_ref in state — approve by default")
        return {
            "status": "reviewing",
            "current_phase": "quality_gate",
            "_quality_verdict": "approve",
        }

    # --- DB에서 질문 데이터 로드 ---
    db_url = os.environ.get("DATABASE_URL", "")
    analysis_repo = AnalysisRepository(db_url)

    try:
        questions_data = await analysis_repo.get_result(questions_ref)
    except Exception as exc:
        logger.error("quality_gate: DB read failed for ref %s: %s", questions_ref, exc)
        return {
            "status": "reviewing",
            "current_phase": "quality_gate",
            "_quality_verdict": "approve",
        }

    if not questions_data:
        logger.warning("quality_gate: no data found for ref %s — approve", questions_ref)
        return {
            "status": "reviewing",
            "current_phase": "quality_gate",
            "_quality_verdict": "approve",
        }

    result_data = questions_data.get("result_data", {})
    questions = result_data.get("questions", [])

    if not questions:
        logger.warning("quality_gate: empty questions list — approve")
        return {
            "status": "reviewing",
            "current_phase": "quality_gate",
            "_quality_verdict": "approve",
        }

    # --- 질문 요약 구성 (LLM 토큰 절약) ---
    questions_summary = _summarize_questions(questions)

    # --- LLM 품질 검증 ---
    try:
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
                    "content": (
                        f"Review these {len(questions)} interview questions "
                        f"(revision #{revision_count}):\n\n{questions_summary}"
                    ),
                },
            ],
            temperature=0.3,
        )
    except Exception as exc:
        logger.error("quality_gate: LLM call failed: %s", exc)
        # LLM 장애 시 안전하게 승인 (파이프라인 중단 방지)
        return {
            "status": "reviewing",
            "current_phase": "quality_gate",
            "_quality_verdict": "approve",
        }

    verdict = review.verdict if review.verdict in ("approve", "revise") else "approve"

    logger.info(
        "quality_gate: job=%s revision=%d quality=%.2f verdict=%s issues=%d",
        job_id,
        revision_count,
        review.overall_quality,
        verdict,
        len(review.issues),
    )

    # --- 리뷰 결과 DB 저장 (Reference Passing) ---
    try:
        review_ref = await analysis_repo.save_result(
            job_id=job_id,
            worker_name="quality_gate",
            supervisor_name="meta",
            result_data={
                "overall_quality": review.overall_quality,
                "issues": review.issues,
                "suggestions": review.suggestions,
                "verdict": verdict,
                "revision_number": revision_count,
                "questions_reviewed": len(questions),
            },
            metrics={
                "overall_quality": review.overall_quality,
                "issue_count": len(review.issues),
                "suggestion_count": len(review.suggestions),
            },
        )
        logger.debug("quality_gate: review saved as %s", review_ref)
    except Exception as exc:
        logger.error("quality_gate: failed to save review to DB: %s", exc)
        # DB 저장 실패해도 파이프라인은 계속 진행

    # --- State 업데이트 ---
    new_revision_count = revision_count + (1 if verdict == "revise" else 0)

    return {
        "status": "reviewing",
        "current_phase": "quality_gate",
        "revision_count": new_revision_count,
        "_quality_verdict": verdict,
    }


# ─── 조건부 라우터 ────────────────────────────────────────────────────


def should_revise(state: MetaState) -> str:
    """QualityGate 조건부 라우팅: 'revise' vs 'approve'.

    LangGraph conditional edge router로 사용된다.
    quality_gate_node가 설정한 _quality_verdict 값을 읽어 라우팅한다.
    """
    # 최대 리비전 횟수 도달 → 강제 승인
    if state.get("revision_count", 0) >= MAX_REVISIONS:
        return "approve"

    # questions_ref 없으면 승인 (검증할 대상 없음)
    if not state.get("questions_ref"):
        return "approve"

    # quality_gate_node가 설정한 verdict 사용
    verdict = state.get("_quality_verdict", "approve")
    if verdict not in ("approve", "revise"):
        return "approve"

    return verdict


# ─── 헬퍼 ─────────────────────────────────────────────────────────────


def _summarize_questions(questions: list[dict[str, Any] | Any]) -> str:
    """LLM에 전달할 질문 요약을 구성한다. 토큰 절약을 위해 핵심 필드만 추출."""
    lines: list[str] = []
    for i, q in enumerate(questions, 1):
        if isinstance(q, dict):
            qid = q.get("question_id", f"Q-{i}")
            cat = q.get("category", "unknown")
            strategy = q.get("strategy", "unknown")
            difficulty = q.get("difficulty", "unknown")
            text = q.get("question_text", "")[:300]
            code_ref = q.get("code_reference", "none")
            answer_guide = q.get("expected_answer_guide", "")[:200]
            red_flags = q.get("red_flags", [])
        else:
            # Pydantic model인 경우
            qid = getattr(q, "question_id", f"Q-{i}")
            cat = getattr(q, "category", "unknown")
            strategy = getattr(q, "strategy", "unknown")
            difficulty = getattr(q, "difficulty", "unknown")
            text = str(getattr(q, "question_text", ""))[:300]
            code_ref = getattr(q, "code_reference", "none")
            answer_guide = str(getattr(q, "expected_answer_guide", ""))[:200]
            red_flags = getattr(q, "red_flags", [])

        lines.append(
            f"[{i}] id={qid} category={cat} strategy={strategy} "
            f"difficulty={difficulty}\n"
            f"    Q: {text}\n"
            f"    Code ref: {code_ref}\n"
            f"    Answer guide: {answer_guide}\n"
            f"    Red flags: {red_flags}"
        )

    return "\n\n".join(lines)
