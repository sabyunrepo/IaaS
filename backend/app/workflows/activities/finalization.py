"""
backend/app/workflows/activities/finalization.py
최종화 Activity — 면접 스크립트 조립 및 저장
"""
import json
import logging
from datetime import datetime, timezone

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def finalize_output(
    questions: list[dict],
    analysis: dict,
    enriched_input: dict,
) -> dict:
    """
    최종 면접 스크립트 생성

    1. 용어집 통합
    2. 후보자 요약 생성
    3. 면접관 가이드 생성
    4. 스크립트 조립
    5. 저장
    """
    from app.services.cached_llm import CachedLLMService
    from app.core.config import settings

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    activity.heartbeat("Generating candidate summary...")

    # 1. 용어집 통합
    all_terms = []
    seen_terms = set()
    for q in questions:
        for term in q.get("terminology", []):
            term_name = term.get("term", "") if isinstance(term, dict) else str(term)
            if term_name and term_name not in seen_terms:
                all_terms.append(term if isinstance(term, dict) else {"term": term_name})
                seen_terms.add(term_name)

    # 2. 후보자 요약
    summary_prompt = (
        "Generate a brief candidate summary based on:\n"
        f"Document analysis: {json.dumps(analysis.get('document_analysis', {}), default=str)[:2000]}\n"
        f"Code analysis: {json.dumps(analysis.get('code_analysis', {}), default=str)[:2000]}\n"
    )
    candidate_summary = await llm.run(summary_prompt)

    # 3. 면접관 가이드
    activity.heartbeat("Generating interviewer guide...")
    guide_prompt = (
        f"Generate interviewer guide for {raw_input.get('experience_level', '미들')} level candidate.\n"
        f"Total questions: {len(questions)}\n"
        f"Categories: {list(set(q.get('category', '') for q in questions))}\n"
    )
    interviewer_guide = await llm.run(guide_prompt)

    # 4. 최종 스크립트 조립
    final_script = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_language": output_language,
        "candidate_summary": candidate_summary if isinstance(candidate_summary, (dict, str)) else {},
        "questions": questions,
        "interviewer_guide": interviewer_guide if isinstance(interviewer_guide, (dict, str)) else {},
        "full_glossary": all_terms,
        "metadata": {
            "total_questions": len(questions),
            "language": output_language,
            "terminology_count": len(all_terms),
            "experience_level": raw_input.get("experience_level", "미들"),
        },
    }

    activity.heartbeat("Saving output...")

    # 5. 로컬 저장 (S3는 인프라 연결 후)
    import os
    output_dir = os.path.join(settings.LOCAL_STORAGE_PATH, "outputs")
    os.makedirs(output_dir, exist_ok=True)

    # JSON 저장
    output_path = os.path.join(output_dir, "interview_script.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_script, f, ensure_ascii=False, indent=2, default=str)

    logger.info(f"Interview script saved to {output_path}")
    final_script["output_path"] = output_path

    return final_script
