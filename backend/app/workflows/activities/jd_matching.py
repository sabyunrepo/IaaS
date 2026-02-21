"""
backend/app/workflows/activities/jd_matching.py
JD 매칭 Activity — 후보자 프로필 vs JD 매칭

후보자의 UnifiedCandidateProfile과 JD 분석 결과를 비교하여
매칭 점수, 스킬 매칭 상세, 갭 분석, 채용 추천을 생성.
"""
from temporalio import activity

from app.core.logging import get_logger

logger = get_logger(__name__)


@activity.defn
async def match_candidate_to_jd(
    candidate_profile: dict,
    jd_analysis: dict,
    experience_level: str = "Mid",
    output_language: str = "ko",
) -> dict:
    """후보자 프로필 vs JD → 매칭 점수 + 근거

    Args:
        candidate_profile: UnifiedCandidateProfile.model_dump()
        jd_analysis: analyze_jd() 결과
        experience_level: 경험 레벨
        output_language: 출력 언어

    Returns:
        CandidateJDMatch dict
    """
    from app.services.profile_scoring import (
        profile_weighted_skill_overlap,
        extract_profile_skills,
    )
    from app.services.scoring_formulas import calculate_radar_scores

    activity.heartbeat("Starting candidate-JD matching...")

    # 1. 스킬 매칭 (SkillNormalizer 기반)
    jd_requirements = jd_analysis.get("requirements", [])
    overlap_score, match_details = profile_weighted_skill_overlap(
        jd_requirements, candidate_profile,
    )
    skill_match_score = round(overlap_score * 100, 1)

    # Matched / Gap 분류
    matched_skills = [d for d in match_details if d.get("matched")]
    gap_skills = [d for d in match_details if not d.get("matched")]

    activity.heartbeat("Skill matching complete, calculating radar...")

    # 2. 레이더 차트 계산 (프로필 기반)
    # 기존 scoring_formulas를 재사용 — candidate_profile 전달
    code_profile = candidate_profile.get("code_profile") or {}
    doc_analysis_proxy = _build_doc_analysis_proxy(candidate_profile)

    radar = calculate_radar_scores(
        jd_analysis=jd_analysis,
        code_analysis=code_profile if code_profile.get("total_repos_analyzed", 0) > 0 else None,
        document_analysis=doc_analysis_proxy,
        experience_level=experience_level,
        linkedin_profile=None,  # 프로필에 이미 병합됨
        output_language=output_language,
        candidate_profile=candidate_profile,
    )

    activity.heartbeat("Radar calculation complete...")

    # 3. 전체 매치율 계산
    # Role Fit(30%) + Skill Match(40%) + Technical Depth(30%)
    radar_scores = radar.candidate if isinstance(radar.candidate, list) else [50, 50, 50, 50, 50]
    role_fit = radar_scores[0] if len(radar_scores) > 0 else 50
    technical = radar_scores[1] if len(radar_scores) > 1 else 50

    overall = round(
        role_fit * 0.30 + skill_match_score * 0.40 + technical * 0.30,
        1,
    )

    # 4. 채용 추천
    recommendation = _compute_recommendation(overall, skill_match_score, experience_level)

    # 5. 갭 분석 구조화
    gaps = []
    for g in gap_skills:
        gaps.append({
            "skill": g.get("skill", ""),
            "importance": "required" if g.get("category", "우대") in ("필수", "required", "must") else "preferred",
            "impact": "high" if g.get("category", "우대") in ("필수", "required", "must") else "medium",
        })

    # 6. 근거 설명 생성
    profile_skills = extract_profile_skills(candidate_profile)
    explanation = _build_match_explanation(
        overall, skill_match_score, len(matched_skills), len(gap_skills),
        recommendation, experience_level, output_language,
    )

    # 7. 신뢰도
    data_completeness = candidate_profile.get("data_completeness", 0.0)
    if data_completeness >= 0.8:
        confidence = "high"
    elif data_completeness >= 0.5:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "overall_match_score": overall,
        "skill_match_score": skill_match_score,
        "skill_matches": {
            "matched": matched_skills,
            "gaps": gaps,
            "overlap_score": overlap_score,
            "total_jd_skills": len(jd_requirements),
            "matched_count": len(matched_skills),
            "gap_count": len(gap_skills),
        },
        "radar_scores": {
            "candidate": radar.candidate,
            "required": radar.required,
            "sources": radar.sources,
            "human_sources": radar.human_sources,
        },
        "gaps": gaps,
        "match_explanation": explanation,
        "hiring_recommendation": recommendation,
        "recommendation_confidence": confidence,
        "confidence_level": confidence,
    }


def _build_doc_analysis_proxy(candidate_profile: dict) -> dict:
    """프로필에서 document_analysis-like dict 구성 (scoring_formulas 호환)"""
    skills = []
    for s in candidate_profile.get("skills", []):
        canonical = s.get("canonical_name", "")
        if canonical:
            skills.append(canonical)
        skills.extend(s.get("aliases", []))

    work_history = candidate_profile.get("work_history", [])
    exp_years = candidate_profile.get("experience_years", 0)

    return {
        "skills": list(set(skills)),
        "work_experience": work_history,
        "experience_years": exp_years,
        "education": candidate_profile.get("education", []),
    }


def _compute_recommendation(
    overall: float, skill_match: float, experience_level: str,
) -> str:
    """매치율 기반 채용 추천"""
    if overall >= 80 and skill_match >= 75:
        return "강력추천"
    elif overall >= 65 and skill_match >= 55:
        return "추천"
    elif overall >= 45:
        return "보류"
    else:
        return "비추천"


def _build_match_explanation(
    overall: float,
    skill_match: float,
    matched_count: int,
    gap_count: int,
    recommendation: str,
    experience_level: str,
    output_language: str,
) -> str:
    """매칭 근거 설명 생성 (비개발자 친화)"""
    if output_language == "ko":
        return (
            f"전체 매치율 {overall:.0f}%: "
            f"JD 요구 스킬 중 {matched_count}개 일치, {gap_count}개 부족. "
            f"스킬 매칭 {skill_match:.0f}%. "
            f"경험 레벨: {experience_level}. "
            f"채용 추천: {recommendation}."
        )
    return (
        f"Overall match {overall:.0f}%: "
        f"{matched_count} skills matched, {gap_count} gaps out of JD requirements. "
        f"Skill match {skill_match:.0f}%. "
        f"Experience level: {experience_level}. "
        f"Recommendation: {recommendation}."
    )
