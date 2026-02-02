"""
backend/app/workflows/activities/quality_review.py
품질 검토 Activity
"""
import logging

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def review_questions(questions: list[dict]) -> dict:
    """
    질문 품질 검토

    검토 항목:
    1. 중복 검사
    2. 난이도 균형
    3. 카테고리 분포
    """
    from app.services.cached_llm import CachedLLMService

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
        prompt = (
            "Review these interview questions for quality:\n"
            "1. Identify any duplicate or very similar questions (list indices)\n"
            "2. Rate overall quality 1-10\n"
            "3. Suggest any improvements\n\n"
            + "\n".join(f"{i+1}. {t}" for i, t in enumerate(question_texts))
        )
        review_result = await llm.run(prompt)
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
