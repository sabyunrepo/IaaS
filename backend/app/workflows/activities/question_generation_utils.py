"""
backend/app/workflows/activities/question_generation_utils.py
질문 생성 유틸리티 — 카테고리 배분 상수 + 프롬프트 컨텍스트 빌더

Extracted from question_generation.py for SRP compliance.
"""

# ── 경험 레벨별 퍼센트 기반 카테고리 배분 ──
# 각 레벨에서 중요한 질문 유형에 더 높은 비율 할당
TOTAL_QUESTIONS = 20

CATEGORY_DISTRIBUTION: dict[str, dict[str, dict]] = {
    # 신입: 기초 기술력 + 성장 가능성 + 커뮤니케이션 중심
    "신입": {
        "role_fit":             {"count": 6, "difficulty": ["Easy", "Easy", "Easy", "Medium", "Medium", "Hard"]},
        "technical_depth":      {"count": 5, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"]},
        "execution_ownership":  {"count": 3, "difficulty": ["Easy", "Medium", "Hard"]},
        "communication":        {"count": 4, "difficulty": ["Easy", "Easy", "Medium", "Hard"]},
        "risk_flags":           {"count": 2, "difficulty": ["Easy", "Medium"]},
    },
    # 주니어: 성장 가능성 + 기초 기술력 중심
    "주니어": {
        "role_fit":             {"count": 6, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Medium", "Hard"]},
        "technical_depth":      {"count": 5, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"]},
        "execution_ownership":  {"count": 3, "difficulty": ["Easy", "Medium", "Hard"]},
        "communication":        {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
        "risk_flags":           {"count": 2, "difficulty": ["Easy", "Medium"]},
    },
    # 미들: 균형 잡힌 배분
    "미들": {
        "role_fit":             {"count": 5, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"]},
        "technical_depth":      {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
        "execution_ownership":  {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
        "communication":        {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
        "risk_flags":           {"count": 3, "difficulty": ["Easy", "Medium", "Hard"]},
    },
    # 시니어: 실행력 + 리스크 + 기술 깊이 중심
    "시니어": {
        "role_fit":             {"count": 3, "difficulty": ["Medium", "Medium", "Hard"]},
        "technical_depth":      {"count": 4, "difficulty": ["Medium", "Medium", "Hard", "Hard"]},
        "execution_ownership":  {"count": 5, "difficulty": ["Easy", "Medium", "Medium", "Hard", "Hard"]},
        "communication":        {"count": 4, "difficulty": ["Medium", "Medium", "Hard", "Hard"]},
        "risk_flags":           {"count": 4, "difficulty": ["Easy", "Medium", "Hard", "Hard"]},
    },
    # CTO/VP: 리더십 + 전략적 실행력 + 리스크 관리 중심
    "CTO/VP": {
        "role_fit":             {"count": 3, "difficulty": ["Medium", "Hard", "Hard"]},
        "technical_depth":      {"count": 3, "difficulty": ["Medium", "Hard", "Hard"]},
        "execution_ownership":  {"count": 5, "difficulty": ["Medium", "Medium", "Hard", "Hard", "Hard"]},
        "communication":        {"count": 4, "difficulty": ["Medium", "Medium", "Hard", "Hard"]},
        "risk_flags":           {"count": 5, "difficulty": ["Medium", "Medium", "Hard", "Hard", "Hard"]},
    },
}


def get_distribution(experience_level: str) -> dict[str, dict]:
    """경험 레벨에 맞는 카테고리 배분 반환 (fallback: 미들)"""
    return CATEGORY_DISTRIBUTION.get(experience_level, CATEGORY_DISTRIBUTION["미들"])


def format_distribution_for_prompt(dist: dict[str, dict]) -> tuple[str, str]:
    """프롬프트용 카테고리 배분 + 난이도 배분 텍스트 생성"""
    from collections import Counter

    cat_lines = []
    diff_lines = []
    for cat, info in dist.items():
        count = info["count"]
        pct = round(count / TOTAL_QUESTIONS * 100)
        cat_desc = {
            "role_fit": "Culture fit, motivation, career goals, growth potential",
            "technical_depth": "Technical skills, problem-solving, architecture",
            "execution_ownership": "Project delivery, ownership, impact, leadership",
            "communication": "Collaboration, explanation ability, conflict resolution",
            "risk_flags": "Gaps, concerns, areas needing clarification",
        }
        cat_lines.append(f"- **{cat}** ({pct}%): {count} topics — {cat_desc.get(cat, '')}")

        # 난이도 카운트
        diff_count = Counter(info["difficulty"])
        diff_str = ", ".join(f"{d}:{c}" for d, c in sorted(diff_count.items(), key=lambda x: ["Easy", "Medium", "Hard"].index(x[0])))
        diff_lines.append(f"- **{cat}** ({count} topics): {diff_str}")

    return "\n      ".join(cat_lines), "\n      ".join(diff_lines)


def build_candidate_context(analysis: dict, enriched_input: dict) -> str:
    """
    후보자 정보를 LLM 프롬프트용 요약 텍스트로 조합.
    document_analysis, code_analysis, linkedin_profile, jd_analysis에서 핵심 정보 추출.
    각 섹션은 graceful degradation (데이터 없으면 스킵).
    """
    sections = []

    # 1. 이력서/포트폴리오 프로필
    doc = analysis.get("document_analysis", {})
    profile = doc.get("profile", {})
    if profile:
        parts = []
        if profile.get("name"):
            parts.append(f"Name: {profile['name']}")
        if profile.get("summary"):
            parts.append(f"Summary: {profile['summary'][:200]}")
        skills = profile.get("skills", [])
        if skills:
            if isinstance(skills, dict):
                skills = list(skills.keys())
            elif not isinstance(skills, list):
                skills = [str(skills)]
            parts.append(f"Skills: {', '.join(str(s) for s in skills[:15])}")
        experience = profile.get("work_experience") or profile.get("experience", [])
        if experience and isinstance(experience, list):
            exp_lines = []
            for exp in experience[:3]:
                if isinstance(exp, dict):
                    role = exp.get("title") or exp.get("role", "")
                    company = exp.get("company", "")
                    if role or company:
                        exp_lines.append(f"  - {role} @ {company}")
                elif isinstance(exp, str):
                    exp_lines.append(f"  - {exp[:100]}")
            if exp_lines:
                parts.append("Work Experience:\n" + "\n".join(exp_lines))
        projects = profile.get("projects", [])
        if projects and isinstance(projects, list):
            proj_lines = []
            for proj in projects[:3]:
                if isinstance(proj, dict):
                    proj_lines.append(f"  - {proj.get('name', proj.get('title', ''))}: {proj.get('description', '')[:80]}")
                elif isinstance(proj, str):
                    proj_lines.append(f"  - {proj[:100]}")
            if proj_lines:
                parts.append("Projects:\n" + "\n".join(proj_lines))
        if parts:
            sections.append("## Resume/Portfolio\n" + "\n".join(parts))

    # 2. LinkedIn 프로필
    raw_input = enriched_input.get("raw_input", {})
    linkedin = raw_input.get("linkedin_profile") or enriched_input.get("linkedin_profile", {})
    if linkedin and isinstance(linkedin, dict):
        parts = []
        name = linkedin.get("full_name") or linkedin.get("name", "")
        headline = linkedin.get("headline", "")
        if name:
            parts.append(f"Name: {name}")
        if headline:
            parts.append(f"Headline: {headline}")
        experiences = linkedin.get("experiences") or linkedin.get("experience", [])
        if experiences and isinstance(experiences, list):
            for exp in experiences[:3]:
                if isinstance(exp, dict):
                    title = exp.get("title", "")
                    company = exp.get("company_name") or exp.get("company", "")
                    if title or company:
                        parts.append(f"  - {title} @ {company}")
        li_skills = linkedin.get("skills", [])
        if li_skills and isinstance(li_skills, list):
            skill_names = []
            for s in li_skills[:10]:
                skill_names.append(s.get("name", str(s)) if isinstance(s, dict) else str(s))
            parts.append(f"Skills: {', '.join(skill_names)}")
        if parts:
            sections.append("## LinkedIn Profile\n" + "\n".join(parts))

    # 3. 코드 분석
    code = analysis.get("code_analysis", {})
    if code:
        parts = []
        langs = code.get("languages") or code.get("tech_stack", [])
        if langs:
            if isinstance(langs, dict):
                parts.append(f"Languages: {', '.join(list(langs.keys())[:10])}")
            elif isinstance(langs, list):
                parts.append(f"Tech Stack: {', '.join(str(l) for l in langs[:10])}")
        repo_summary = code.get("summary") or code.get("repo_summary", "")
        if repo_summary and isinstance(repo_summary, str):
            parts.append(f"Summary: {repo_summary[:200]}")
        top_candidates = code.get("top_question_candidates", [])
        if top_candidates:
            cand_lines = [f"  - {c.get('title', '')}" for c in top_candidates[:5] if isinstance(c, dict)]
            if cand_lines:
                parts.append("Notable Implementations:\n" + "\n".join(cand_lines))
        if parts:
            sections.append("## Code Analysis (GitHub)\n" + "\n".join(parts))

    # 4. JD 매칭 요약
    jd = analysis.get("jd_analysis", {})
    if jd:
        parts = []
        title = jd.get("job_title", "")
        if title:
            parts.append(f"Target Role: {title}")
        reqs = jd.get("requirements", [])
        if reqs:
            req_skills = []
            for r in reqs[:8]:
                if isinstance(r, dict):
                    req_skills.append(r.get("skill", str(r)))
                else:
                    req_skills.append(str(r))
            parts.append(f"Key Requirements: {', '.join(req_skills)}")
        if parts:
            sections.append("## JD Requirements\n" + "\n".join(parts))

    if not sections:
        return ""

    return "\n\n".join(sections)


def format_candidates(candidates: list[dict]) -> str:
    lines = []
    for i, c in enumerate(candidates[:30]):
        lines.append(f"{i+1}. [{c['source']}] {c['topic']} (score: {c['score']})")
    return "\n".join(lines)
