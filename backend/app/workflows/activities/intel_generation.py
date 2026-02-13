"""
backend/app/workflows/activities/intel_generation.py
Intel Brief 생성 Activity
"""
import logging

from temporalio import activity

from app.core.observability import observe_activity
from app.models.intel import (
    IntelBrief, JDSummary, GitHubSummary,
    LinkedInPosition, RequirementMatch,
)

logger = logging.getLogger(__name__)


def _extract_jd_summary(jd_analysis: dict, lang: str = "ko") -> JDSummary:
    """JD 분석에서 요약 정보 추출"""
    from app.services.i18n_labels import _t
    requirements = jd_analysis.get("requirements") or []
    # 필수 스킬 우선 정렬 (Issue #245)
    sorted_requirements = sorted(
        requirements,
        key=lambda r: 0 if r.get("category") in ("필수", "required", "must") else 1,
    )
    req_matches = []
    for req in sorted_requirements[:10]:
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


def _extract_github_summary(code_analysis: dict | None, lang: str = "ko") -> GitHubSummary | None:
    """코드 분석에서 GitHub 요약 추출"""
    from app.services.i18n_labels import _t

    if not code_analysis:
        return None

    repos = code_analysis.get("repositories", [])
    total_commits = sum(r.get("candidate_commits", r.get("commit_count", 0)) for r in repos)
    tech_stack = code_analysis.get("tech_stack", [])
    # JIT-61: GitHub API language 기반 프로그래밍 언어 (LLM tech_stack과 분리)
    primary_languages = code_analysis.get("primary_languages", [])

    # 월별 기여도 데이터 (12개월)
    chart_data = code_analysis.get("monthly_contributions", [0] * 12)
    if len(chart_data) < 12:
        chart_data = chart_data + [0] * (12 - len(chart_data))

    # JIT-44: HYBRID 분석 깊이 정보
    ast_chunks = code_analysis.get("ast_chunk_count")
    analyzed_fns = code_analysis.get("analyzed_functions_count")
    pipeline_type = code_analysis.get("pipeline_type", "legacy")
    analysis_method = "hybrid" if pipeline_type == "clone_based" else None

    # tech_match_note: HYBRID일 때 분석 깊이 표시
    if analysis_method == "hybrid" and ast_chunks:
        tech_match_note = _t("tech_stack_confirmed_hybrid", lang,
                             n=len(tech_stack), fn_count=analyzed_fns or 0)
    elif tech_stack:
        tech_match_note = _t("tech_stack_confirmed", lang, n=len(tech_stack))
    else:
        tech_match_note = _t("no_code_data", lang)

    return GitHubSummary(
        contributions=total_commits,
        repos=len(repos),
        main_languages=", ".join(primary_languages[:3]) if primary_languages else "N/A",
        tech_match=_t("high", lang) if tech_stack else _t("unconfirmed", lang),
        tech_match_note=tech_match_note,
        tenure_pattern=code_analysis.get("tenure_pattern", _t("unconfirmed", lang)),
        tenure_note=code_analysis.get("tenure_note", ""),
        activity_gap=code_analysis.get("activity_gap"),
        chart_data=chart_data[:12],
        ast_analysis_depth=ast_chunks,
        functions_analyzed=analyzed_fns,
        analysis_method=analysis_method,
    )


def _extract_linkedin_positions(linkedin_profile: dict | None) -> list[LinkedInPosition]:
    """LinkedIn 프로필에서 경력 추출 (duration 자동 계산 포함)"""
    if not linkedin_profile:
        return []

    experiences = linkedin_profile.get("experiences") or linkedin_profile.get("experience") or []
    positions = []

    for exp in experiences[:5]:  # 최근 5개
        company = exp.get("company") or exp.get("company_name") or "Unknown"
        title = exp.get("title") or exp.get("position") or ""
        duration = exp.get("duration") or exp.get("tenure") or ""

        # duration이 없으면 starts_at/ends_at에서 계산
        if not duration:
            starts = exp.get("starts_at") or exp.get("start_date") or ""
            ends = exp.get("ends_at") or exp.get("end_date") or ""
            if starts:
                duration = f"{starts} — {ends or 'Present'}"

        positions.append(LinkedInPosition(
            initial=company[0].upper() if company else "?",
            title=str(title) if title else "",
            company=str(company),
            detail=str(duration) if duration else "",
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
    candidate_profile: dict | None = None,
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

    # 2. 역량 매칭 — JIT-17: competency_matching 함수 제거, 빈 리스트
    competencies: list = []
    activity.heartbeat()

    # 3. GitHub 기여도 데이터 포맷
    github_summary = _extract_github_summary(code_analysis, lang=output_language)
    activity.heartbeat()

    # 4. LinkedIn 타임라인 구성
    linkedin_positions = _extract_linkedin_positions(linkedin_profile)

    # 4b. candidate_profile에서 LinkedIn 확장 데이터 보강
    linkedin_activity_summary = None
    linkedin_projects = []
    linkedin_honors = []
    if candidate_profile:
        linkedin_activity_summary = candidate_profile.get("linkedin_activity_summary")
        linkedin_projects = candidate_profile.get("linkedin_projects", [])
        linkedin_honors = candidate_profile.get("linkedin_honors", [])

    # LinkedIn 경고 메시지
    linkedin_warning = None
    if linkedin_profile:
        warnings = []
        experiences = linkedin_profile.get("experiences") or linkedin_profile.get("experience") or []
        if not any("CTO" in (e.get("title") or "") or "VP" in (e.get("title") or "") for e in experiences):
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

    # Attach profile extended data to intel brief output
    result = intel_brief.model_dump()
    if candidate_profile:
        if linkedin_activity_summary:
            result["linkedin_activity_summary"] = linkedin_activity_summary
        if linkedin_projects:
            result["linkedin_projects"] = linkedin_projects[:5]
        if linkedin_honors:
            result["linkedin_honors"] = linkedin_honors[:5]
        # 추천서/봉사활동 서머리 (JIT-50)
        recommendations_summary = candidate_profile.get("recommendations_summary")
        if recommendations_summary:
            result["recommendations_summary"] = recommendations_summary
        volunteer_summary = candidate_profile.get("volunteer_summary")
        if volunteer_summary:
            result["volunteer_summary"] = volunteer_summary
        # 추천서/봉사활동 원본 데이터 (프론트 표시용)
        recs = candidate_profile.get("linkedin_recommendations", [])
        if recs:
            result["linkedin_recommendations"] = recs[:10]
        vol = candidate_profile.get("linkedin_volunteer_experience", [])
        if vol:
            result["linkedin_volunteer_experience"] = vol[:10]
        # Cover letter insights for Decision tab cross-reference
        cover_letter = candidate_profile.get("cover_letter_insights")
        if cover_letter:
            result["cover_letter_insights"] = cover_letter
        # areas_to_probe from profile
        areas = candidate_profile.get("areas_to_probe", [])
        if areas:
            result["areas_to_probe"] = areas[:5]

    logger.info(f"Intel Brief generated with {len(competencies)} competencies")
    return result
