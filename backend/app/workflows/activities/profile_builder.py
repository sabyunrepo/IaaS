"""
backend/app/workflows/activities/profile_builder.py
Profile Builder Activity — Phase 2.5

모든 소스(이력서, GitHub, LinkedIn, 커버레터)의 분석 결과를
UnifiedCandidateProfile로 통합.

SkillNormalizer로 스킬 정규화 + 중복 제거 + implies 관계 추적.
추천서/봉사활동 LLM 서머리 생성 (JIT-48).
"""
import logging
from datetime import datetime

from temporalio import activity

logger = logging.getLogger(__name__)


async def _summarize_recommendations(
    recommendations: list[dict],
    output_language: str = "ko",
) -> str | None:
    """추천서 전문을 LLM으로 서머리: 추천인 관계, 핵심 평가, 공통 테마"""
    if not recommendations:
        return None

    rec_text = "\n".join([
        f"- {r.get('from_user', '익명')} ({r.get('relationship', '')}): {r.get('text', '')}"
        for r in recommendations[:10]
    ])

    try:
        from app.prompts import get_prompt_with_config
        from app.services.cached_llm import CachedLLMService

        prompt_config = get_prompt_with_config(
            "linkedin_summary.yaml", "recommendations_summary",
            recommendations=rec_text,
            output_language=output_language,
        )
        llm = CachedLLMService()
        result = await llm.run_with_prompt_config(prompt_config)
        return result.strip() if result else None
    except Exception as e:
        logger.warning(f"Recommendations summary failed: {e}")
        return None


async def _summarize_volunteer(
    volunteer: list[dict],
    output_language: str = "ko",
) -> str | None:
    """봉사활동 내역을 LLM으로 서머리: 활동 분야, 역할, 지속성"""
    if not volunteer:
        return None

    vol_text = "\n".join([
        f"- {v.get('organization', '')} | {v.get('role', '')} | {v.get('cause', '')} | {v.get('description', '')}"
        for v in volunteer[:10]
    ])

    try:
        from app.prompts import get_prompt_with_config
        from app.services.cached_llm import CachedLLMService

        prompt_config = get_prompt_with_config(
            "linkedin_summary.yaml", "volunteer_summary",
            volunteer_activities=vol_text,
            output_language=output_language,
        )
        llm = CachedLLMService()
        result = await llm.run_with_prompt_config(prompt_config)
        return result.strip() if result else None
    except Exception as e:
        logger.warning(f"Volunteer summary failed: {e}")
        return None


@activity.defn
async def build_candidate_profile(
    enriched: dict,
    doc_analysis: dict,
    code_analysis: dict | None,
) -> dict:
    """Phase 2 분석 결과 → UnifiedCandidateProfile 통합

    Args:
        enriched: EnrichedInput (Phase 0)
        doc_analysis: analyze_documents() 결과
        code_analysis: analyze_code() 결과 (optional)

    Returns:
        UnifiedCandidateProfile.model_dump()
    """
    from app.services.skill_normalizer import SkillNormalizer
    from app.models.candidate_profile import (
        UnifiedCandidateProfile, UnifiedSkill, UnifiedWorkExperience,
        Education, CodeProfile, CoverLetterProfile,
    )
    from app.core.database import async_session

    async with async_session() as session:
        normalizer = SkillNormalizer(session)

        # 1. 모든 소스에서 스킬 수집
        profile = doc_analysis.get("profile", {})
        raw_resume_skills = profile.get("skills", [])
        # Handle skills as list or dict
        resume_skills = []
        if isinstance(raw_resume_skills, dict):
            resume_skills = list(raw_resume_skills.keys())
        elif isinstance(raw_resume_skills, list):
            resume_skills = [s for s in raw_resume_skills if isinstance(s, str)]

        github_skills = []
        if code_analysis:
            github_skills = code_analysis.get("tech_stack", [])
            if not github_skills:
                github_skills = code_analysis.get("combined_tech_stack", [])

        linkedin_profile = enriched.get("linkedin_profile") or {}
        linkedin_skills_raw = linkedin_profile.get("skills", [])
        linkedin_skills = []
        for ls in linkedin_skills_raw:
            if isinstance(ls, str):
                linkedin_skills.append(ls)
            elif isinstance(ls, dict):
                linkedin_skills.append(ls.get("name", ""))

        cover_letter_skills = doc_analysis.get("cover_letter_insights", {}).get("mentioned_skills", [])
        if not isinstance(cover_letter_skills, list):
            cover_letter_skills = []

        # 2. SkillNormalizer로 정규화 + 소스 추적 + 중복 제거
        unified_resolved = await normalizer.unify_from_sources({
            "resume": resume_skills,
            "github": github_skills,
            "linkedin": linkedin_skills,
            "cover_letter": cover_letter_skills,
        }, session)

        # Convert to UnifiedSkill Pydantic models
        unified_skills = [
            UnifiedSkill(
                canonical_name=r.canonical,
                aliases=r.aliases,
                sources=r.sources,
                category=r.category,
                domain=r.domain,
                confidence=r.confidence,
                implied_skills=r.implied_skills,
                proficiency_signals=r.proficiency_signals,
            )
            for r in unified_resolved
        ]

        # 3. 경력 병합 (이력서 + LinkedIn)
        work_history = _merge_work_history(
            resume_history=profile.get("work_history", []),
            linkedin_history=linkedin_profile.get("experiences", []),
        )

        # 4. 학력 병합
        education = _merge_education(
            resume_education=profile.get("education", []),
            linkedin_education=linkedin_profile.get("education", []),
        )

        # 5. 코드 프로필 구축 (JD-agnostic)
        code_profile = _build_code_profile(code_analysis) if code_analysis else None

        # 6. 커버레터 인사이트 구조화
        cover_letter = _extract_cover_letter_insights(doc_analysis)

        # 7. LinkedIn 확장 데이터
        linkedin_projects = linkedin_profile.get("projects", [])
        if not isinstance(linkedin_projects, list):
            linkedin_projects = []
        linkedin_honors = linkedin_profile.get("honors_and_awards", [])
        if not isinstance(linkedin_honors, list):
            linkedin_honors = []
        linkedin_activity = linkedin_profile.get("activity", [])
        activity_summary = _summarize_activities(linkedin_activity)

        # 추천서/봉사활동 (JIT-47)
        linkedin_recommendations = linkedin_profile.get("recommendations", [])
        if not isinstance(linkedin_recommendations, list):
            linkedin_recommendations = []
        linkedin_volunteer = linkedin_profile.get("volunteer_experience", [])
        if not isinstance(linkedin_volunteer, list):
            linkedin_volunteer = []
        # 버그 수정: connections가 아닌 실제 recommendations 배열 길이 사용
        recommendations_count = len(linkedin_recommendations)

        # 7.5. 추천서/봉사활동 LLM 서머리 생성 (JIT-48)
        output_language = enriched.get("raw_input", {}).get("language_config", {}).get("output_language", "ko")
        if not isinstance(output_language, str):
            output_language = "ko"
        recommendations_summary = await _summarize_recommendations(
            linkedin_recommendations, output_language,
        )
        volunteer_summary = await _summarize_volunteer(
            linkedin_volunteer, output_language,
        )

        # 8. 경력 연수 계산
        experience_years = profile.get("experience_years", 0) or 0
        if not experience_years and linkedin_profile:
            experience_years = linkedin_profile.get("experience_years", 0) or 0

        # 9. 데이터 소스 + 완전성
        data_sources = []
        completeness = 0.0
        if resume_skills or profile.get("work_history"):
            data_sources.append("resume")
            completeness += 0.25
        if github_skills or code_analysis:
            data_sources.append("github")
            completeness += 0.25
        if linkedin_profile.get("full_name") or linkedin_skills:
            data_sources.append("linkedin")
            completeness += 0.25
        if cover_letter_skills or cover_letter:
            data_sources.append("cover_letter")
            completeness += 0.25

        confidence_level = "low"
        if len(data_sources) >= 3:
            confidence_level = "high"
        elif len(data_sources) >= 2:
            confidence_level = "medium"

        # 10. 탐색 포인트
        areas_to_probe = doc_analysis.get("areas_to_probe", [])
        if not isinstance(areas_to_probe, list):
            areas_to_probe = []

        # Build profile
        candidate_profile = UnifiedCandidateProfile(
            name=profile.get("name", linkedin_profile.get("full_name", "Unknown")),
            email=profile.get("email"),
            avatar_url=linkedin_profile.get("avatar_url"),
            linkedin_url=linkedin_profile.get("profile_url"),
            github_username=enriched.get("candidate_github_username"),
            skills=unified_skills,
            work_history=work_history,
            education=education,
            experience_years=experience_years,
            experience_level=enriched.get("raw_input", {}).get("experience_level"),
            code_profile=code_profile,
            cover_letter_insights=cover_letter,
            linkedin_activity_summary=activity_summary,
            linkedin_projects=[p if isinstance(p, dict) else {"title": str(p)} for p in linkedin_projects],
            linkedin_honors=[h if isinstance(h, dict) else {"title": str(h)} for h in linkedin_honors],
            linkedin_recommendations=[r if isinstance(r, dict) else {"from_user": str(r)} for r in linkedin_recommendations],
            linkedin_volunteer_experience=[v if isinstance(v, dict) else {"organization": str(v)} for v in linkedin_volunteer],
            recommendations_count=recommendations_count,
            recommendations_summary=recommendations_summary,
            volunteer_summary=volunteer_summary,
            areas_to_probe=areas_to_probe,
            data_sources=data_sources,
            data_completeness=completeness,
            confidence_level=confidence_level,
        )

        logger.info(
            f"Profile built: {candidate_profile.name}, "
            f"{len(unified_skills)} skills, "
            f"{len(work_history)} positions, "
            f"sources={data_sources}, "
            f"completeness={completeness:.0%}"
        )

        return candidate_profile.model_dump()


def _merge_work_history(
    resume_history: list[dict],
    linkedin_history: list[dict],
) -> list:
    """이력서 + LinkedIn 경력 병합 (중복 제거)"""
    from app.models.candidate_profile import UnifiedWorkExperience

    merged = []
    seen_keys = set()

    # Resume history first (primary)
    for exp in (resume_history or []):
        if not isinstance(exp, dict):
            continue
        company = (exp.get("company") or "").strip()
        position = (exp.get("position") or exp.get("title") or "").strip()
        key = f"{company.lower()}|{position.lower()}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged.append(UnifiedWorkExperience(
            company=company,
            position=position,
            period=exp.get("period") or "",
            description=exp.get("description"),
            tech_stack=exp.get("tech_stack", []),
            source="resume",
        ))

    # LinkedIn supplementary (add only new entries)
    for exp in (linkedin_history or []):
        if not isinstance(exp, dict):
            continue
        company = (exp.get("company") or "").strip()
        position = (exp.get("title") or exp.get("position") or "").strip()
        key = f"{company.lower()}|{position.lower()}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        merged.append(UnifiedWorkExperience(
            company=company,
            position=position,
            period=exp.get("period") or "",
            location=exp.get("location"),
            description=exp.get("description"),
            source="linkedin",
        ))

    return merged


def _merge_education(
    resume_education: list[dict],
    linkedin_education: list[dict],
) -> list:
    """학력 병합"""
    from app.models.candidate_profile import Education

    merged = []
    seen = set()

    for edu in (resume_education or []):
        if not isinstance(edu, dict):
            continue
        institution = (edu.get("institution") or edu.get("school") or "").strip()
        key = institution.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(Education(
            institution=institution,
            degree=edu.get("degree"),
            major=edu.get("major", edu.get("field_of_study")),
            graduation_year=edu.get("graduation_year"),
            source="resume",
        ))

    for edu in (linkedin_education or []):
        if not isinstance(edu, dict):
            continue
        institution = (edu.get("school") or edu.get("institution") or "").strip()
        key = institution.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(Education(
            institution=institution,
            degree=edu.get("degree"),
            major=edu.get("field_of_study", edu.get("major")),
            source="linkedin",
        ))

    return merged


def _build_code_profile(code_analysis: dict) -> "CodeProfile":
    """code_analysis → CodeProfile (JD-agnostic)"""
    from app.models.candidate_profile import CodeProfile

    repos = code_analysis.get("repositories", [])
    total_commits = 0
    total_additions = 0
    total_deletions = 0
    languages = set()
    frameworks = set()
    patterns = set()
    notables = []
    repo_summaries = []

    for repo in repos:
        if not isinstance(repo, dict):
            continue
        total_commits += repo.get("candidate_commits", 0)
        total_additions += repo.get("candidate_additions", 0)
        total_deletions += repo.get("candidate_deletions", 0)
        lang = repo.get("language", "")
        if lang:
            languages.add(lang)
        for ts in repo.get("tech_stack", []):
            frameworks.add(ts)
        for p in repo.get("patterns", []):
            if isinstance(p, dict):
                patterns.add(p.get("name", ""))
            elif isinstance(p, str):
                patterns.add(p)
        for n in repo.get("notable_implementations", []):
            notables.append(n if isinstance(n, dict) else {"title": str(n)})
        repo_summaries.append({
            "name": repo.get("repo_name", ""),
            "language": lang,
            "commits": repo.get("candidate_commits", 0),
        })

    # Complexity from stats or repos
    complexities = [r.get("avg_complexity", 0) for r in repos if isinstance(r, dict) and r.get("avg_complexity", 0) > 0]
    avg_complexity = sum(complexities) / len(complexities) if complexities else 0

    quality = code_analysis.get("quality_metrics", {})
    monthly = code_analysis.get("monthly_contributions", [])

    return CodeProfile(
        total_repos_analyzed=len(repos),
        total_commits=total_commits,
        total_additions=total_additions,
        total_deletions=total_deletions,
        primary_languages=list(languages),
        frameworks_detected=list(frameworks),
        design_patterns=list(patterns - {""}),
        avg_complexity=avg_complexity,
        quality_metrics=quality,
        notable_implementations=notables[:10],  # Top 10
        monthly_contributions=monthly if isinstance(monthly, list) else [],
        repo_summaries=repo_summaries,
    )


def _extract_cover_letter_insights(doc_analysis: dict) -> "CoverLetterProfile | None":
    """문서 분석에서 커버레터 인사이트 추출"""
    from app.models.candidate_profile import CoverLetterProfile

    insights = doc_analysis.get("cover_letter_insights", {})
    if not insights or not isinstance(insights, dict):
        return None

    return CoverLetterProfile(
        motivation=insights.get("motivation"),
        key_strengths=insights.get("key_strengths", []),
        mentioned_skills=insights.get("mentioned_skills", []),
        cultural_fit_signals=insights.get("cultural_fit_signals", []),
        career_goals=insights.get("career_goals"),
    )


def _summarize_activities(activities: list) -> str | None:
    """LinkedIn 활동 요약"""
    if not activities or not isinstance(activities, list):
        return None

    valid = [a for a in activities if isinstance(a, dict)]
    if not valid:
        return None

    # Count interaction types
    types = {}
    for a in valid:
        interaction = a.get("interaction", "Unknown")
        types[interaction] = types.get(interaction, 0) + 1

    parts = [f"{count} {itype}" for itype, count in types.items()]
    return f"LinkedIn 활동: {', '.join(parts)} (최근 {len(valid)}건)"
