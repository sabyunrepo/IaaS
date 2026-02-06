"""
backend/app/workflows/activities/quality_review.py
품질 검토 Activity
"""
import logging

from temporalio import activity

from app.core.observability import observe_activity

logger = logging.getLogger(__name__)


@activity.defn
@observe_activity(name="review_questions", phase="quality_review")
async def review_questions(questions: list[dict], output_language: str = "ko") -> dict:
    """
    질문 품질 검토

    검토 항목:
    1. 중복 검사
    2. 난이도 균형
    3. 카테고리 분포
    """
    from app.services.cached_llm import CachedLLMService
    from app.workflows.utils import run_llm_with_prompt_config_heartbeat

    llm = CachedLLMService()
    issues = []
    questions_to_revise = []

    activity.heartbeat("Reviewing question quality...")

    # 1. 카테고리 분포 확인
    category_counts = {}
    for q in questions:
        cat = q.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    expected_categories = {"role_fit", "technical_depth", "execution_ownership", "communication", "risk_flags"}
    for cat in expected_categories:
        count = category_counts.get(cat, 0)
        if count < 3:
            issues.append({
                "type": "category_underrepresented",
                "category": cat,
                "count": count,
            })

    # 2. 난이도 분포 확인
    difficulty_counts = {}
    for q in questions:
        diff = q.get("difficulty", "Medium")
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1

    total = len(questions)
    if total > 0:
        easy_ratio = difficulty_counts.get("Easy", 0) / total
        hard_ratio = difficulty_counts.get("Hard", 0) / total
        if easy_ratio > 0.6:
            issues.append({"type": "too_many_easy", "ratio": easy_ratio})
        if hard_ratio > 0.6:
            issues.append({"type": "too_many_hard", "ratio": hard_ratio})

    # 3. LLM 기반 중복/품질 검토
    if len(questions) > 0:
        question_texts = [q.get("question_text", "") for q in questions[:25]]
        from app.prompts import get_prompt_with_config
        formatted_questions = "\n".join(f"{i+1}. {t}" for i, t in enumerate(question_texts))
        prompt_config = get_prompt_with_config("quality_review.yaml", "review", questions=formatted_questions, output_language=output_language)
        # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
        review_result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)
        if isinstance(review_result, dict):
            if review_result.get("duplicates"):
                issues.append({"type": "duplicates", "details": review_result["duplicates"]})

    verdict = "APPROVED" if len(questions_to_revise) == 0 and len(issues) < 3 else "NEEDS_REVISION"

    return {
        "verdict": verdict,
        "issues": issues,
        "questions_to_revise": questions_to_revise,
        "category_distribution": category_counts,
        "difficulty_distribution": difficulty_counts,
    }
