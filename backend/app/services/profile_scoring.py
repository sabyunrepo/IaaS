"""
backend/app/services/profile_scoring.py
Profile → Scoring Adapter — UnifiedCandidateProfile ↔ scoring_formulas 연결

candidate_profile이 있으면 정규화된 스킬/implied 관계를 활용하여
scoring_formulas의 기존 함수들을 호출. 없으면 기존 경로 그대로 유지.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_profile_skills(candidate_profile: dict) -> set[str]:
    """프로필에서 정규화된 스킬 집합 추출 (canonical + implied)

    Returns:
        lowercase canonical_name set + implied_skills
    """
    skills_set: set[str] = set()
    for skill in candidate_profile.get("skills", []):
        canonical = skill.get("canonical_name", "")
        if canonical:
            skills_set.add(canonical.lower())
        # implied skills도 포함 (React → JavaScript 인정)
        for implied in skill.get("implied_skills", []):
            if implied:
                skills_set.add(implied.lower())
    return skills_set


def extract_profile_skill_sources(candidate_profile: dict) -> dict[str, list[str]]:
    """프로필에서 스킬별 소스 매핑 추출

    Returns:
        {"react": ["resume", "github", "linkedin"], ...}
    """
    sources_map: dict[str, list[str]] = {}
    for skill in candidate_profile.get("skills", []):
        canonical = skill.get("canonical_name", "").lower()
        if canonical:
            sources_map[canonical] = skill.get("sources", [])
    return sources_map


def profile_weighted_skill_overlap(
    jd_requirements: list[dict],
    candidate_profile: dict,
) -> tuple[float, list[dict]]:
    """프로필 기반 JD 스킬 매칭 (정규화된 canonical 비교)

    SkillNormalizer 결과(canonical_name)를 활용하므로
    "React" vs "react.js" vs "ReactJS" 모두 동일하게 처리.
    implied_skills로 "React" 보유 → "JavaScript" 자동 인정.

    Args:
        jd_requirements: JD 분석의 requirements 리스트
        candidate_profile: UnifiedCandidateProfile dict

    Returns:
        (weighted_overlap_score, match_details)
        - weighted_overlap_score: 0.0-1.0
        - match_details: [{"skill": ..., "matched": True/False, "source": ..., "confidence": ...}]
    """
    from app.services.scoring_formulas import _TRIVIAL_SKILLS

    if not jd_requirements:
        return 0.0, []

    # 프로필에서 정규화 스킬 + implied 추출
    candidate_skills = extract_profile_skills(candidate_profile)
    sources_map = extract_profile_skill_sources(candidate_profile)

    total_weight = 0.0
    matched_weight = 0.0
    match_details = []

    for req in jd_requirements:
        skill = req.get("skill", "").strip()
        if not skill:
            continue
        skill_lower = skill.lower()
        category = req.get("category", "우대")

        # Weight by category (trivial overrides)
        if skill_lower in _TRIVIAL_SKILLS:
            weight = 0.1
        elif category in ("필수", "required", "must"):
            weight = 1.0
        else:
            weight = 0.5

        total_weight += weight

        # Canonical exact match (이미 정규화된 스킬끼리 비교)
        if skill_lower in candidate_skills:
            matched_weight += weight * 1.0
            skill_sources = sources_map.get(skill_lower, ["profile"])
            match_details.append({
                "skill": skill,
                "matched": True,
                "match_score": 1.0,
                "source": "+".join(skill_sources) if skill_sources else "profile",
                "confidence": 1.0,
                "method": "canonical_exact",
            })
        else:
            # Partial token match as fallback
            skill_tokens = set(skill_lower.replace("-", " ").replace(".", " ").split())
            best_match = 0.0
            best_source = ""
            for cs in candidate_skills:
                cs_tokens = set(cs.replace("-", " ").replace(".", " ").split())
                if skill_tokens and cs_tokens:
                    overlap = len(skill_tokens & cs_tokens)
                    token_score = overlap / max(len(skill_tokens), 1)
                    if token_score > best_match:
                        best_match = token_score
                        best_source = "+".join(sources_map.get(cs, ["profile"]))

            if best_match >= 0.5:
                matched_weight += weight * 0.6
                match_details.append({
                    "skill": skill,
                    "matched": True,
                    "match_score": 0.6,
                    "source": best_source or "profile",
                    "confidence": best_match,
                    "method": "token_overlap",
                })
            else:
                match_details.append({
                    "skill": skill,
                    "matched": False,
                    "match_score": 0.0,
                    "source": "",
                    "confidence": 0.0,
                    "method": "none",
                })

    overlap_score = matched_weight / max(total_weight, 0.001)
    return overlap_score, match_details


def profile_skill_match_evidence(
    jd_requirements: list[dict],
    candidate_profile: dict,
) -> str:
    """프로필 기반 스킬 매칭의 evidence_source 문자열 생성

    Returns:
        "profile(canonical_match)" 또는 소스 상세 정보
    """
    skills = candidate_profile.get("skills", [])
    source_counts: dict[str, int] = {}
    for skill in skills:
        for src in skill.get("sources", []):
            source_counts[src] = source_counts.get(src, 0) + 1

    parts = []
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        parts.append(f"{src}({count})")
    return "profile: " + ", ".join(parts) if parts else "profile"
