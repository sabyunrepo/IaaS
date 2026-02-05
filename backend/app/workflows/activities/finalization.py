"""
backend/app/workflows/activities/finalization.py
최종화 Activity — 면접 스크립트 조립 및 저장
"""
import json
import logging
from datetime import datetime, timezone

from temporalio import activity

from app.core.observability import observe_activity

logger = logging.getLogger(__name__)


def _format_linkedin_summary(profile: dict) -> str:
    """LinkedIn 프로필을 프롬프트용 요약 텍스트로 변환"""
    if not profile:
        return "LinkedIn 프로필 정보 없음"

    parts = []

    # 기본 정보
    name = profile.get("full_name")
    headline = profile.get("headline")
    company = profile.get("current_company")

    if name:
        parts.append(f"이름: {name}")
    if headline:
        parts.append(f"직함: {headline}")
    if company:
        parts.append(f"현재 회사: {company}")

    # 프로젝트 (면접 질문 생성에 유용)
    projects = profile.get("projects", [])
    if projects:
        proj_lines = ["프로젝트:"]
        for p in projects[:5]:
            title = p.get("title", "")
            desc = p.get("description", "")[:200] if p.get("description") else ""
            proj_lines.append(f"  - {title}: {desc}")
        parts.append("\n".join(proj_lines))

    # 수상/인증 (면접 질문 생성에 유용)
    honors = profile.get("honors_and_awards", [])
    if honors:
        honor_lines = ["수상 경력:"]
        for h in honors[:5]:
            title = h.get("title", "")
            issuer = h.get("issuer", "")
            desc = h.get("description", "")[:200] if h.get("description") else ""
            honor_lines.append(f"  - {title} ({issuer}): {desc}")
        parts.append("\n".join(honor_lines))

    # 활동 (관심 분야 파악)
    activity = profile.get("activity", [])
    if activity:
        act_lines = ["최근 활동:"]
        for a in activity[:3]:
            interaction = a.get("interaction", "")
            title = a.get("title", "")[:100] if a.get("title") else ""
            act_lines.append(f"  - {interaction}: {title}")
        parts.append("\n".join(act_lines))

    # 경력 (있는 경우)
    experiences = profile.get("experiences", [])
    if experiences:
        exp_lines = ["경력:"]
        for e in experiences[:5]:
            title = e.get("title", "")
            company = e.get("company", "")
            exp_lines.append(f"  - {title} @ {company}")
        parts.append("\n".join(exp_lines))

    # 스킬 (있는 경우)
    skills = profile.get("skills", [])
    if skills:
        parts.append(f"스킬: {', '.join(skills[:15])}")

    return "\n\n".join(parts) if parts else "LinkedIn 프로필 정보 제한적"


@activity.defn
@observe_activity(name="finalize_output", phase="finalization")
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

    # 2. 후보자 요약 (LinkedIn 프로필 포함)
    linkedin_profile = enriched_input.get("linkedin_profile") or {}
    linkedin_summary = _format_linkedin_summary(linkedin_profile)

    from app.prompts import get_prompt
    summary_prompt = get_prompt(
        "finalization.yaml", "candidate_summary",
        document_analysis=json.dumps(analysis.get("document_analysis", {}), default=str)[:2000],
        code_analysis=json.dumps(analysis.get("code_analysis", {}), default=str)[:2000],
        linkedin_profile=linkedin_summary,
    )
    candidate_summary = await llm.run(summary_prompt, activity_name="finalize_candidate_summary")

    # 3. 면접관 가이드
    activity.heartbeat("Generating interviewer guide...")
    guide_prompt = get_prompt(
        "finalization.yaml", "interviewer_guide",
        experience_level=raw_input.get("experience_level", "미들"),
        total_questions=len(questions),
        categories=list(set(q.get("category", "") for q in questions)),
    )
    interviewer_guide = await llm.run(guide_prompt, activity_name="finalize_interviewer_guide")

    # 4. 최종 스크립트 조립
    final_script = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_language": output_language,
        "candidate_summary": candidate_summary if isinstance(candidate_summary, (dict, str)) else {},
        "questions": questions,
        "interviewer_guide": interviewer_guide if isinstance(interviewer_guide, (dict, str)) else {},
        "full_glossary": all_terms,
        "linkedin_profile": {
            "name": linkedin_profile.get("full_name"),
            "headline": linkedin_profile.get("headline"),
            "current_company": linkedin_profile.get("current_company"),
            "projects": linkedin_profile.get("projects", []),
            "honors_and_awards": linkedin_profile.get("honors_and_awards", []),
            "activity": linkedin_profile.get("activity", []),
            "profile_url": linkedin_profile.get("profile_url"),
        } if linkedin_profile else None,
        "metadata": {
            "total_questions": len(questions),
            "language": output_language,
            "terminology_count": len(all_terms),
            "experience_level": raw_input.get("experience_level", "미들"),
            "has_linkedin_data": bool(linkedin_profile),
        },
    }

    activity.heartbeat("Saving output...")

    # 5. 저장 (local 또는 S3)
    from app.services.storage_service import get_storage
    storage = get_storage()
    # job_id는 raw_input 안에 있음 (enrich_input이 raw_input을 포함하여 반환)
    job_id = enriched_input.get("raw_input", {}).get("job_id", "unknown")
    storage_key = f"outputs/{job_id}/interview_script.json"
    output_path = storage.upload_json(storage_key, final_script)

    logger.info(f"Interview script saved to {output_path}")
    final_script["output_path"] = output_path

    return final_script
