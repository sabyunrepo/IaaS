"""
backend/app/workflows/activities/intel_generation.py
Intel Brief 생성 Activity (LLM 강화 + 규칙 기반 fallback)
"""
import json
import logging
from typing import Any

from temporalio import activity

from app.core.observability import observe_activity
from app.models.intel import (
    IntelBrief, JDSummary, CompetencyMatch, GitHubSummary,
    LinkedInPosition, RequirementMatch,
)

logger = logging.getLogger(__name__)


async def _llm_match_competencies(
    jd_analysis: dict,
    document_analysis: dict,
    code_analysis: dict | None,
    output_language: str = "ko",
    job_id: str | None = None,
) -> list[CompetencyMatch] | None:
    """LLM 기반 시맨틱 역량 매칭 (실패 시 None 반환)"""
    try:
        from app.services.cached_llm import CachedLLMService
        from app.prompts import get_prompt_with_config
        from app.workflows.utils import run_llm_with_prompt_config_heartbeat

        jd_requirements = jd_analysis.get("requirements") or []
        if not jd_requirements:
            return None

        candidate_skills = (document_analysis.get("profile") or {}).get("skills") or []
        code_skills = (code_analysis.get("tech_stack") or []) if code_analysis else []

        # VectorStore 시맨틱 스킬 매칭
        vector_context = ""
        if job_id:
            try:
                from app.services.vector_store import get_vector_store
                vs = get_vector_store(job_id)
                for req in jd_requirements[:6]:
                    skill = req.get("skill", "") if isinstance(req, dict) else str(req)
                    if skill:
                        matches = await vs.search_profile(skill, limit=2)
                        for m in matches:
                            if m["similarity"] >= 0.6:
                                vector_context += f"- {skill}: {m['content_text'][:100]} (sim={m['similarity']:.2f})\n"
            except Exception as e:
                logger.debug(f"Vector skill enrichment failed: {e}")

        kg_context = ""
        if vector_context:
            kg_context = f"Semantic skill matches from vector search:\n{vector_context}"

        prompt_config = get_prompt_with_config(
            "v2_generation.yaml", "competency_matching",
            jd_requirements=json.dumps(jd_requirements[:6], ensure_ascii=False, default=str),
            candidate_skills=json.dumps(candidate_skills[:20], ensure_ascii=False, default=str),
            code_skills=json.dumps(code_skills[:20], ensure_ascii=False, default=str),
            output_language=output_language,
            kg_context=kg_context,
        )

        llm = CachedLLMService()
        result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)

        if not isinstance(result, list):
            return None

        from app.services.match_config import get_match_color_icon

        # VectorStore에서 매칭된 스킬 이름 목록 (evidence_source 보강용)
        vector_matched_skills = set()
        if vector_context:
            for line in vector_context.strip().split("\n"):
                if line.startswith("- ") and ":" in line:
                    skill_part = line[2:].split(":")[0].strip().lower()
                    if skill_part:
                        vector_matched_skills.add(skill_part)

        VALID_SOURCES = {"resume", "github", "resume+github", "vector_store", "none", "llm"}

        competencies = []
        for item in result[:6]:
            if not isinstance(item, dict):
                continue
            match_level = item.get("match", "none")
            color, icon = get_match_color_icon(match_level)
            # LLM이 evidence_source를 반환하면 유효값 검증 후 사용
            ev_source = item.get("evidence_source", "")
            if ev_source and ev_source not in VALID_SOURCES:
                ev_source = ""  # 유효하지 않은 값은 무시
            if not ev_source:
                label = item.get("match_label", "").lower()
                if "github" in label or "code" in label or "repo" in label:
                    ev_source = "github"
                elif "resume" in label or "이력서" in label or "경력" in label:
                    ev_source = "resume"
                elif match_level in ("strong", "match", "partial"):
                    ev_source = "llm"

            # VectorStore 시맨틱 매칭이 기여한 경우 소스 보강
            comp_name_lower = item.get("name", "").lower()
            if vector_matched_skills and comp_name_lower:
                for vs_skill in vector_matched_skills:
                    if vs_skill in comp_name_lower or comp_name_lower in vs_skill:
                        if ev_source and ev_source not in ("none", "llm", "vector_store"):
                            ev_source = f"{ev_source}+vector_store"
                        elif ev_source in ("none", "llm", ""):
                            ev_source = "vector_store"
                        break
            competencies.append(CompetencyMatch(
                name=item.get("name", ""),
                match=match_level,
                match_label=item.get("match_label", ""),
                desc=item.get("desc", ""),
                why=item.get("why", ""),
                color=color,
                icon=icon,
                evidence_source=ev_source,
            ))

        if competencies:
            # === Post-processing 품질 검증 ===
            VAGUE_PATTERNS = (
                "다양한 경험", "풍부한 경력", "excellent skills", "strong background",
                "good experience", "sufficient capability", "적절한 역량",
                "관련 경험 있음", "해당 기술 보유",
            )
            vague_count = 0
            no_why_count = 0
            for c in competencies:
                label_lower = (c.match_label or "").lower().strip()
                if any(vp in label_lower for vp in VAGUE_PATTERNS) or (
                    c.match in ("strong", "match") and len(label_lower) < 10
                ):
                    vague_count += 1
                if not c.why or len(c.why.strip()) < 5:
                    no_why_count += 1
            if vague_count > 0:
                logger.warning(
                    f"Competency matching: {vague_count}/{len(competencies)} items have vague match_label"
                )
            if no_why_count > 0:
                logger.warning(
                    f"Competency matching: {no_why_count}/{len(competencies)} items have empty/short 'why' field"
                )
            logger.info(f"LLM competency matching: {len(competencies)} items")
            return competencies
        return None

    except Exception as e:
        logger.warning(f"LLM competency matching failed, using fallback: {e}")
        return None


def _extract_jd_summary(jd_analysis: dict, lang: str = "ko") -> JDSummary:
    """JD 분석에서 요약 정보 추출"""
    from app.services.i18n_labels import _t
    requirements = jd_analysis.get("requirements") or []
    req_matches = []
    for req in requirements[:5]:  # 상위 5개 요구사항
        req_matches.append(RequirementMatch(
            text=req.get("skill", req.get("text", "")),
            desc=req.get("description", req.get("desc", "")),
            matched=req.get("matched", False),
        ))

    # job_title: 프롬프트에서 추론하도록 수정됨, 방어적 폴백 추가
    # company_name: null 허용 (subtitle은 빈 문자열로 처리)
    return JDSummary(
        title=jd_analysis.get("job_title") or jd_analysis.get("title") or _t("software_engineer", lang),
        subtitle=jd_analysis.get("company_context") or jd_analysis.get("company_name") or "",
        requirements=req_matches,
        success_metrics=jd_analysis.get("success_metrics", []),
    )


def _match_competencies(
    jd_analysis: dict,
    document_analysis: dict,
    code_analysis: dict | None,
    lang: str = "ko",
) -> list[CompetencyMatch]:
    """JD 역량과 후보자 매칭 분석"""
    competencies = []
    jd_requirements = jd_analysis.get("requirements") or []
    candidate_skills = (document_analysis.get("profile") or {}).get("skills") or []
    code_skills = []
    if code_analysis:
        code_skills = code_analysis.get("tech_stack") or []

    # 색상 및 아이콘 매핑
    match_config = {
        "strong": ("emerald", "✅"),
        "match": ("emerald", "✅"),
        "partial": ("amber", "⚠️"),
        "unknown": ("amber", "⚠️"),
        "none": ("red", "❌"),
    }

    for req in jd_requirements[:6]:  # 상위 6개 역량
        skill = req.get("skill", req.get("text", ""))
        desc = req.get("description", req.get("desc", ""))
        why = req.get("importance", req.get("why", ""))

        # 매칭 레벨 결정
        skill_lower = skill.lower()
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        code_skills_lower = [s.lower() for s in code_skills]

        from app.services.i18n_labels import _t

        match_level = "none"
        match_label = _t("candidate_no_evidence", lang)
        evidence_source = ""

        # 정확 매칭 확인 — 이력서 스킬 우선, 그다음 코드 스킬
        resume_match = any(skill_lower in cs for cs in candidate_skills_lower)
        code_match = any(skill_lower in cs for cs in code_skills_lower)
        if resume_match or code_match:
            match_level = "strong"
            match_label = _t("candidate_strong_match", lang)
            evidence_source = "resume" if resume_match else "github"
        # 부분 매칭 확인
        elif any(
            any(word in cs for word in skill_lower.split())
            for cs in candidate_skills_lower
        ):
            match_level = "partial"
            match_label = _t("candidate_partial_match", lang)
            evidence_source = "resume"
        elif any(
            any(word in cs for word in skill_lower.split())
            for cs in code_skills_lower
        ):
            match_level = "partial"
            match_label = _t("candidate_partial_match", lang)
            evidence_source = "github"

        color, icon = match_config.get(match_level, ("slate", "❓"))

        competencies.append(CompetencyMatch(
            name=skill,
            match=match_level,
            match_label=match_label,
            desc=desc,
            why=why,
            color=color,
            icon=icon,
            evidence_source=evidence_source,
        ))

    return competencies


def _extract_github_summary(code_analysis: dict | None, lang: str = "ko") -> GitHubSummary | None:
    """코드 분석에서 GitHub 요약 추출"""
    from app.services.i18n_labels import _t

    if not code_analysis:
        return None

    repos = code_analysis.get("repositories", [])
    total_commits = sum(r.get("commit_count", 0) for r in repos)
    tech_stack = code_analysis.get("tech_stack", [])

    # 월별 기여도 데이터 (12개월)
    chart_data = code_analysis.get("monthly_contributions", [0] * 12)
    if len(chart_data) < 12:
        chart_data = chart_data + [0] * (12 - len(chart_data))

    return GitHubSummary(
        contributions=total_commits,
        repos=len(repos),
        main_languages=", ".join(tech_stack[:3]) if tech_stack else "N/A",
        tech_match=_t("high", lang) if tech_stack else _t("unconfirmed", lang),
        tech_match_note=_t("tech_stack_confirmed", lang, n=len(tech_stack)) if tech_stack else _t("no_code_data", lang),
        tenure_pattern=code_analysis.get("tenure_pattern", _t("unconfirmed", lang)),
        tenure_note=code_analysis.get("tenure_note", ""),
        activity_gap=code_analysis.get("activity_gap"),
        chart_data=chart_data[:12],
    )


def _extract_linkedin_positions(linkedin_profile: dict | None) -> list[LinkedInPosition]:
    """LinkedIn 프로필에서 경력 추출"""
    if not linkedin_profile:
        return []

    experiences = linkedin_profile.get("experiences") or linkedin_profile.get("experience") or []
    positions = []

    for exp in experiences[:5]:  # 최근 5개
        company = exp.get("company", exp.get("company_name", "Unknown"))
        title = exp.get("title", exp.get("position", ""))
        duration = exp.get("duration", exp.get("tenure", ""))

        positions.append(LinkedInPosition(
            initial=company[0].upper() if company else "?",
            title=title,
            company=company,
            detail=duration,
        ))

    return positions


@activity.defn
@observe_activity(name="generate_intel_brief", phase="finalization")
async def generate_intel_brief(
    jd_analysis: dict,
    document_analysis: dict,
    code_analysis: dict | None,
    linkedin_profile: dict | None,
    jd_text: str | None = None,
    job_id: str | None = None,
    output_language: str = "ko",
) -> dict:
    """Intel Brief 생성

    Args:
        jd_analysis: JD 분석 결과
        document_analysis: 문서 분석 결과
        code_analysis: 코드 분석 결과 (optional)
        linkedin_profile: LinkedIn 프로필 (optional)
        jd_text: JD 원문 (optional)
        job_id: Job ID (observability용)

    Returns:
        IntelBrief 데이터
    """
    logger.info(f"Generating Intel Brief for job_id={job_id}")
    activity.heartbeat()

    # 1. JD 요약 생성
    jd_summary = _extract_jd_summary(jd_analysis, lang=output_language)
    activity.heartbeat()

    # 2. 역량 매칭 분석 (LLM 우선, 규칙 기반 fallback)
    competencies = await _llm_match_competencies(jd_analysis, document_analysis, code_analysis, output_language, job_id=job_id)
    if competencies is None:
        competencies = _match_competencies(jd_analysis, document_analysis, code_analysis, lang=output_language)
    activity.heartbeat()

    # 3. GitHub 기여도 데이터 포맷
    github_summary = _extract_github_summary(code_analysis, lang=output_language)
    activity.heartbeat()

    # 4. LinkedIn 타임라인 구성
    linkedin_positions = _extract_linkedin_positions(linkedin_profile)

    # LinkedIn 경고 메시지
    linkedin_warning = None
    if linkedin_profile:
        warnings = []
        experiences = linkedin_profile.get("experiences") or linkedin_profile.get("experience") or []
        if not any("CTO" in e.get("title", "") or "VP" in e.get("title", "") for e in experiences):
            from app.services.i18n_labels import _t
            warnings.append(_t("no_cto_vp_experience", output_language))
        if warnings:
            linkedin_warning = " · ".join(warnings)

    intel_brief = IntelBrief(
        jd_summary=jd_summary,
        jd_full=jd_text,
        competencies=competencies,
        github=github_summary,
        linkedin=linkedin_positions,
        linkedin_warning=linkedin_warning,
    )

    logger.info(f"Intel Brief generated with {len(competencies)} competencies")
    return intel_brief.model_dump()
