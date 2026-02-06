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
) -> list[CompetencyMatch] | None:
    """LLM 기반 시맨틱 역량 매칭 (실패 시 None 반환)"""
    try:
        from app.services.cached_llm import CachedLLMService
        from app.workflows.utils import run_llm_with_heartbeat
        from app.core.config import settings

        jd_requirements = jd_analysis.get("requirements") or []
        if not jd_requirements:
            return None

        candidate_skills = (document_analysis.get("profile") or {}).get("skills") or []
        code_skills = (code_analysis.get("tech_stack") or []) if code_analysis else []

        # 프롬프트 로딩
        import yaml
        from pathlib import Path
        prompts_path = Path(__file__).parent.parent.parent / "prompts" / "v2_generation.yaml"
        with open(prompts_path) as f:
            prompts = yaml.safe_load(f)
        template = prompts["prompts"]["competency_matching"]["template"]

        prompt = template.format(
            jd_requirements=json.dumps(jd_requirements[:6], ensure_ascii=False, default=str),
            candidate_skills=json.dumps(candidate_skills[:20], ensure_ascii=False, default=str),
            code_skills=json.dumps(code_skills[:20], ensure_ascii=False, default=str),
            output_language=output_language,
        )

        llm = CachedLLMService(activity_name="intel_competency_matching")
        result = await run_llm_with_heartbeat(llm, prompt, "intel_competency_matching", interval=30.0)

        if not isinstance(result, list):
            return None

        # 색상 및 아이콘 매핑
        match_config = {
            "strong": ("emerald", "✅"),
            "match": ("emerald", "✅"),
            "partial": ("amber", "⚠️"),
            "unknown": ("amber", "⚠️"),
            "none": ("red", "❌"),
        }

        competencies = []
        for item in result[:6]:
            if not isinstance(item, dict):
                continue
            match_level = item.get("match", "none")
            color, icon = match_config.get(match_level, ("slate", "❓"))
            competencies.append(CompetencyMatch(
                name=item.get("name", ""),
                match=match_level,
                match_label=item.get("match_label", ""),
                desc=item.get("desc", ""),
                why=item.get("why", ""),
                color=color,
                icon=icon,
            ))

        if competencies:
            logger.info(f"LLM competency matching: {len(competencies)} items")
            return competencies
        return None

    except Exception as e:
        logger.warning(f"LLM competency matching failed, using fallback: {e}")
        return None


def _extract_jd_summary(jd_analysis: dict) -> JDSummary:
    """JD 분석에서 요약 정보 추출"""
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
        title=jd_analysis.get("job_title") or jd_analysis.get("title") or "소프트웨어 엔지니어",
        subtitle=jd_analysis.get("company_context") or jd_analysis.get("company_name") or "",
        requirements=req_matches,
        success_metrics=jd_analysis.get("success_metrics", []),
    )


def _match_competencies(
    jd_analysis: dict,
    document_analysis: dict,
    code_analysis: dict | None,
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

        match_level = "none"
        match_label = "후보자: 증거 없음"

        # 정확 매칭 확인
        if any(skill_lower in cs for cs in candidate_skills_lower + code_skills_lower):
            match_level = "strong"
            match_label = "후보자: 강한 매칭"
        # 부분 매칭 확인
        elif any(
            any(word in cs for word in skill_lower.split())
            for cs in candidate_skills_lower + code_skills_lower
        ):
            match_level = "partial"
            match_label = "후보자: 부분 매칭"

        color, icon = match_config.get(match_level, ("slate", "❓"))

        competencies.append(CompetencyMatch(
            name=skill,
            match=match_level,
            match_label=match_label,
            desc=desc,
            why=why,
            color=color,
            icon=icon,
        ))

    return competencies


def _extract_github_summary(code_analysis: dict | None) -> GitHubSummary | None:
    """코드 분석에서 GitHub 요약 추출"""
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
        tech_match="높음" if tech_stack else "미확인",
        tech_match_note=f"{len(tech_stack)}개 기술 스택 확인" if tech_stack else "코드 분석 데이터 없음",
        tenure_pattern=code_analysis.get("tenure_pattern", "미확인"),
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
    jd_summary = _extract_jd_summary(jd_analysis)
    activity.heartbeat()

    # 2. 역량 매칭 분석 (LLM 우선, 규칙 기반 fallback)
    competencies = await _llm_match_competencies(jd_analysis, document_analysis, code_analysis, output_language)
    if competencies is None:
        competencies = _match_competencies(jd_analysis, document_analysis, code_analysis)
    activity.heartbeat()

    # 3. GitHub 기여도 데이터 포맷
    github_summary = _extract_github_summary(code_analysis)
    activity.heartbeat()

    # 4. LinkedIn 타임라인 구성
    linkedin_positions = _extract_linkedin_positions(linkedin_profile)

    # LinkedIn 경고 메시지
    linkedin_warning = None
    if linkedin_profile:
        warnings = []
        experiences = linkedin_profile.get("experiences") or linkedin_profile.get("experience") or []
        if not any("CTO" in e.get("title", "") or "VP" in e.get("title", "") for e in experiences):
            warnings.append("CTO/VP 타이틀 경험 없음")
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
