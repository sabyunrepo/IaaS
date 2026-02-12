"""
backend/app/workflows/activities/finalization.py
최종화 Activity — 면접 스크립트 조립 및 저장
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import PurePosixPath

from temporalio import activity

from app.core.observability import observe_activity

logger = logging.getLogger(__name__)


_AVATAR_ALLOWED_DOMAINS = frozenset({
    "media.licdn.com",
    "media-exp1.licdn.com",
    "media-exp2.licdn.com",
    "static.licdn.com",
    "platform-lookaside.fbsbx.com",
    "gravatar.com",
    "www.gravatar.com",
    "avatars.githubusercontent.com",
})


def _is_avatar_url_allowed(url: str) -> bool:
    """SSRF 방어: avatar URL 도메인을 allowlist로 검증."""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        return hostname in _AVATAR_ALLOWED_DOMAINS
    except (ValueError, AttributeError):
        return False


def _extract_quality_metadata(questions: list[dict]) -> dict:
    """질문 목록에서 품질 메타데이터 집계 (quality_review에서 병합된 데이터 활용)"""
    evidence_scores = []
    quality_counts = {"high": 0, "medium": 0, "low": 0}
    for q in questions:
        if not isinstance(q, dict):
            continue
        es = q.get("evidence_score")
        if es is not None and isinstance(es, (int, float)):
            evidence_scores.append(es)
        eq = q.get("evidence_quality", "")
        if eq in quality_counts:
            quality_counts[eq] += 1

    avg_evidence = round(sum(evidence_scores) / len(evidence_scores), 1) if evidence_scores else None
    return {
        "avg_evidence_score": avg_evidence,
        "evidence_score_count": len(evidence_scores),
        "evidence_quality_distribution": quality_counts,
    }


def _validate_finalization_integrity(
    questions: list[dict],
    analysis: dict,
    linkedin_profile: dict | None,
) -> list[str]:
    """최종 출력 데이터 무결성 + 교차 일관성 검증. 발견된 문제를 문자열 리스트로 반환."""
    issues = []

    # 1. 질문 데이터 완전성
    if not questions:
        issues.append("CRITICAL: questions list is empty")
    else:
        no_text = sum(1 for q in questions if not isinstance(q, dict) or not q.get("question_text"))
        no_category = sum(1 for q in questions if isinstance(q, dict) and not q.get("category"))
        if no_text > 0:
            issues.append(f"questions: {no_text}/{len(questions)} missing question_text")
        if no_category > 0:
            issues.append(f"questions: {no_category}/{len(questions)} missing category")

        # 카테고리 배분 확인
        categories = {}
        for q in questions:
            if isinstance(q, dict):
                cat = q.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1
        sparse_cats = [c for c, n in categories.items() if n < 2 and c != "unknown"]
        if sparse_cats:
            issues.append(f"questions: sparse categories (< 2 questions): {sparse_cats}")

    # 2. 분석 데이터 존재 확인
    doc_analysis = analysis.get("document_analysis") or {}
    code_analysis = analysis.get("code_analysis")
    jd_analysis = analysis.get("jd_analysis") or {}

    profile = doc_analysis.get("profile") or {}
    if not profile.get("full_name") and not profile.get("name"):
        issues.append("document_analysis: candidate name missing from profile")
    if not profile.get("skills"):
        issues.append("document_analysis: skills list empty")

    if not jd_analysis.get("requirements"):
        issues.append("jd_analysis: requirements list empty")

    # 3. LinkedIn ↔ document_analysis 이름 교차 확인
    if linkedin_profile:
        li_name = (linkedin_profile.get("full_name") or linkedin_profile.get("name") or "").strip().lower()
        doc_name = (profile.get("full_name") or profile.get("name") or "").strip().lower()
        if li_name and doc_name and li_name != doc_name:
            # 부분 매칭 허용 (성/이름 일부 겹침)
            li_parts = set(li_name.split())
            doc_parts = set(doc_name.split())
            if not li_parts & doc_parts:
                issues.append(f"name mismatch: LinkedIn='{li_name}' vs Document='{doc_name}'")

    # 4. JD 요구 스킬 ↔ 질문 카테고리 커버리지
    jd_skills = set()
    for req in (jd_analysis.get("requirements") or [])[:6]:
        if isinstance(req, dict):
            jd_skills.add((req.get("skill") or "").lower())
    if jd_skills and questions:
        q_topics = set()
        for q in questions:
            if isinstance(q, dict):
                q_topics.add((q.get("topic") or "").lower())
                q_topics.add((q.get("question_text") or "")[:50].lower())
        # 기본 커버리지 — JD 스킬 키워드가 질문에 최소 1번 등장하는지
        uncovered = []
        for skill in jd_skills:
            if skill and not any(skill in t for t in q_topics):
                uncovered.append(skill)
        if len(uncovered) > len(jd_skills) // 2:
            issues.append(f"JD coverage gap: {len(uncovered)}/{len(jd_skills)} JD skills not covered in questions: {uncovered[:3]}")

    return issues


async def _download_and_store_avatar(avatar_url: str, job_id: str) -> str | None:
    """LinkedIn avatar를 다운로드하여 S3에 저장, 영구 URL 반환.

    CORS/만료 문제 해결: LinkedIn CDN URL → S3 영구 URL로 교체.
    SSRF 방어: 허용된 도메인만 다운로드 허용.
    실패 시 None 반환 (원본 URL 유지하도록 caller가 처리).
    """
    if not avatar_url or not job_id:
        return None

    if not _is_avatar_url_allowed(avatar_url):
        logger.warning(f"Avatar download blocked: domain not in allowlist ({avatar_url[:80]})")
        return None

    try:
        import httpx

        async with httpx.AsyncClient(timeout=3.0, follow_redirects=False) as client:
            resp = await client.get(avatar_url)

            # 리다이렉트 시 대상 도메인 재검증
            if resp.is_redirect:
                redirect_url = str(resp.headers.get("location", ""))
                if not _is_avatar_url_allowed(redirect_url):
                    logger.warning(f"Avatar redirect blocked: {redirect_url[:80]}")
                    return None
                resp = await client.get(redirect_url)
            resp.raise_for_status()

            # Validate content type
            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                logger.warning(f"Avatar download: unexpected content-type {content_type}")
                return None

            # Size guard (1MB max)
            if len(resp.content) > 1_048_576:
                logger.warning(f"Avatar too large: {len(resp.content)} bytes")
                return None

            # Determine extension from content-type
            ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
            ext = ext_map.get(content_type.split(";")[0].strip(), "jpg")

            # Upload to storage
            from app.services.storage_service import get_storage
            storage = get_storage()
            storage_key = f"avatars/{job_id}/avatar.{ext}"
            storage.upload_file(storage_key, resp.content, content_type)

            # Return public URL if available (R2), otherwise local path
            public_url = storage.get_public_url(storage_key)
            if public_url:
                logger.info(f"Avatar stored to CDN: {public_url}")
                return public_url

            # Local mode: return a relative path that frontend can serve
            logger.info(f"Avatar stored locally: {storage_key}")
            return f"/storage/{storage_key}"

    except Exception as e:
        logger.warning(f"Avatar download/store failed (non-fatal): {e}")
        return None


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

    # 추천서 (JIT-50)
    recommendations = profile.get("recommendations", [])
    if recommendations:
        rec_lines = ["추천서:"]
        for r in recommendations[:5]:
            if isinstance(r, dict):
                from_user = r.get("from_user", "익명")
                text = (r.get("text") or "")[:200]
                rec_lines.append(f"  - {from_user}: {text}")
        parts.append("\n".join(rec_lines))

    # 봉사활동 (JIT-50)
    volunteer = profile.get("volunteer_experience", [])
    if volunteer:
        vol_lines = ["봉사활동:"]
        for v in volunteer[:5]:
            if isinstance(v, dict):
                org = v.get("organization", "")
                role = v.get("role", "")
                vol_lines.append(f"  - {org}: {role}")
        parts.append("\n".join(vol_lines))

    return "\n\n".join(parts) if parts else "LinkedIn 프로필 정보 제한적"


def _build_candidate(
    linkedin_profile: dict | None,
    analysis: dict,
    raw_input: dict,
) -> dict:
    """LinkedIn 프로필 + 분석 데이터에서 Candidate 객체 생성"""
    candidate = {}

    # LinkedIn 프로필에서 기본 정보 추출
    if linkedin_profile:
        candidate["name"] = linkedin_profile.get("full_name", "")
        candidate["avatar_url"] = linkedin_profile.get("avatar_url")
        candidate["current_title"] = linkedin_profile.get("headline", "")
        candidate["company_context"] = linkedin_profile.get("current_company", "")

        # 이니셜 생성
        name = candidate.get("name", "")
        if name:
            parts = name.split()
            candidate["initials"] = "".join(p[0].upper() for p in parts if p)[:2]

        # 경력에서 경험 연수 추론
        experiences = linkedin_profile.get("experiences", [])
        if experiences:
            candidate["experience"] = f"{len(experiences)}+ 포지션"

    # JD 분석에서 역할 정보 추출
    jd_analysis = analysis.get("jd_analysis", {})
    if jd_analysis:
        candidate["role"] = jd_analysis.get("job_title", "")

    # 경험 레벨
    candidate["level"] = raw_input.get("experience_level", "")

    # document_analysis에서 추가 정보
    doc_analysis = analysis.get("document_analysis", {})
    if doc_analysis:
        profile = doc_analysis.get("profile", {})
        if not candidate.get("name") and profile.get("name"):
            candidate["name"] = profile["name"]
        if not candidate.get("experience") and profile.get("experience_years"):
            candidate["experience"] = f"{profile['experience_years']}년"

    return candidate if candidate.get("name") else None


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
    from app.workflows.utils import run_llm_with_prompt_config_heartbeat

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    activity.heartbeat("Generating candidate summary...")

    # 1. 후보자 요약 (LinkedIn 프로필 포함)
    linkedin_profile = enriched_input.get("linkedin_profile") or {}
    linkedin_summary = _format_linkedin_summary(linkedin_profile)

    from app.prompts import get_prompt_with_config
    # 분석 데이터 직렬화 + 절단 (LLM 컨텍스트 제한)
    MAX_ANALYSIS_CHARS = 2000
    doc_json = json.dumps(analysis.get("document_analysis", {}), default=str)
    code_json = json.dumps(analysis.get("code_analysis", {}), default=str)
    doc_truncated = len(doc_json) > MAX_ANALYSIS_CHARS
    code_truncated = len(code_json) > MAX_ANALYSIS_CHARS
    if doc_truncated:
        logger.warning(f"document_analysis truncated for summary: {len(doc_json)} → {MAX_ANALYSIS_CHARS} chars")
    if code_truncated:
        logger.warning(f"code_analysis truncated for summary: {len(code_json)} → {MAX_ANALYSIS_CHARS} chars")

    summary_config = get_prompt_with_config(
        "finalization.yaml", "candidate_summary",
        document_analysis=doc_json[:MAX_ANALYSIS_CHARS],
        code_analysis=code_json[:MAX_ANALYSIS_CHARS],
        linkedin_profile=linkedin_summary,
        output_language=output_language,
    )
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    candidate_summary = await run_llm_with_prompt_config_heartbeat(llm, summary_config, interval=30.0)

    # 3. 면접관 가이드
    activity.heartbeat("Generating interviewer guide...")
    guide_config = get_prompt_with_config(
        "finalization.yaml", "interviewer_guide",
        experience_level=raw_input.get("experience_level", "미들"),
        total_questions=len(questions),
        categories=list(set(q.get("category", "") for q in questions)),
        output_language=output_language,
    )
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    interviewer_guide = await run_llm_with_prompt_config_heartbeat(llm, guide_config, interval=30.0)

    # 4. Avatar 다운로드 → S3 저장 (CORS/만료 해결)
    job_id = enriched_input.get("raw_input", {}).get("job_id", "unknown")
    original_avatar_url = linkedin_profile.get("avatar_url") or linkedin_profile.get("avatar")
    stored_avatar_url = None
    if original_avatar_url and job_id != "unknown":
        activity.heartbeat("Downloading avatar...")
        stored_avatar_url = await _download_and_store_avatar(original_avatar_url, job_id)

    # 5. 최종 스크립트 조립
    # LLM 응답이 string인 경우 dict로 래핑 (Temporal 직렬화 호환성)
    if isinstance(candidate_summary, str):
        candidate_summary = {"summary_text": candidate_summary}
    elif not isinstance(candidate_summary, dict):
        candidate_summary = {}

    if isinstance(interviewer_guide, str):
        interviewer_guide = {"guide_text": interviewer_guide}
    elif not isinstance(interviewer_guide, dict):
        interviewer_guide = {}

    final_script = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "output_language": output_language,
        "candidate_summary": candidate_summary,
        "questions": questions,
        "interviewer_guide": interviewer_guide,
        "linkedin_profile": {
            "name": linkedin_profile.get("full_name") or linkedin_profile.get("name"),
            "headline": linkedin_profile.get("headline"),
            "current_company": linkedin_profile.get("current_company"),
            "avatar_url": stored_avatar_url or linkedin_profile.get("avatar_url") or linkedin_profile.get("avatar"),
            "skills": linkedin_profile.get("skills", []),
            "experiences": linkedin_profile.get("experiences") or linkedin_profile.get("experience", []),
            "education": linkedin_profile.get("education", []),
            "languages": linkedin_profile.get("languages", []),
            "certifications": linkedin_profile.get("certifications", []),
            "projects": linkedin_profile.get("projects", []),
            "honors_and_awards": linkedin_profile.get("honors_and_awards", []),
            "activity": linkedin_profile.get("activity", []),
            "profile_url": linkedin_profile.get("profile_url") or linkedin_profile.get("linkedin_url"),
        } if linkedin_profile else None,
        "candidate": (lambda c: ({**c, "avatar_url": stored_avatar_url} if stored_avatar_url and c else c))(_build_candidate(linkedin_profile, analysis, raw_input)) if linkedin_profile or analysis else None,
        "metadata": {
            "total_questions": len(questions),
            "language": output_language,
            "terminology_count": 0,
            "experience_level": raw_input.get("experience_level", "미들"),
            "has_linkedin_data": bool(linkedin_profile),
            "has_code_analysis": bool(analysis.get("code_analysis")),
            "has_document_analysis": bool(analysis.get("document_analysis")),
            "code_analysis_tech_stack": (analysis.get("code_analysis") or {}).get("tech_stack", [])[:10],
            "chart_data": (analysis.get("code_analysis") or {}).get("monthly_contributions", []),
            "document_analysis_skills": (
                list((analysis.get("document_analysis") or {}).get("profile", {}).get("skills", {}).keys())[:10]
                if isinstance((analysis.get("document_analysis") or {}).get("profile", {}).get("skills"), dict)
                else list((analysis.get("document_analysis") or {}).get("profile", {}).get("skills", []))[:10]
                if isinstance((analysis.get("document_analysis") or {}).get("profile", {}).get("skills"), list)
                else []
            ),
            "data_truncation": {
                "document_analysis": doc_truncated,
                "code_analysis": code_truncated,
            },
            "quality": _extract_quality_metadata(questions),
        },
    }

    # === 데이터 무결성 + 교차 일관성 검증 ===
    integrity_issues = _validate_finalization_integrity(questions, analysis, linkedin_profile)
    if integrity_issues:
        for issue in integrity_issues:
            logger.warning(f"Finalization integrity: {issue}")
        final_script["metadata"]["integrity_validation"] = {
            "has_issues": True,
            "issue_count": len(integrity_issues),
            "issues": integrity_issues,
        }
    else:
        final_script["metadata"]["integrity_validation"] = {"has_issues": False}

    activity.heartbeat("Saving output...")

    # 6. 저장 (local 또는 S3)
    from app.services.storage_service import get_storage
    storage = get_storage()
    storage_key = f"outputs/{job_id}/interview_script.json"
    output_path = storage.upload_json(storage_key, final_script)

    logger.info(f"Interview script saved to {output_path}")
    final_script["output_path"] = output_path

    return final_script
