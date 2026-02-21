"""
backend/app/workflows/activities/question_generation_utils.py
질문 생성 유틸리티 — 카테고리 배분 상수 + 프롬프트 컨텍스트 빌더

Extracted from question_generation.py for SRP compliance.
"""

# ── 경험 레벨별 퍼센트 기반 카테고리 배분 ──
# 각 레벨에서 중요한 질문 유형에 더 높은 비율 할당
TOTAL_QUESTIONS = 20

_ENTRY_DIST = {
    "role_fit":             {"count": 6, "difficulty": ["Easy", "Easy", "Easy", "Medium", "Medium", "Hard"]},
    "technical_depth":      {"count": 5, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"]},
    "execution_ownership":  {"count": 3, "difficulty": ["Easy", "Medium", "Hard"]},
    "communication":        {"count": 4, "difficulty": ["Easy", "Easy", "Medium", "Hard"]},
    "risk_flags":           {"count": 2, "difficulty": ["Easy", "Medium"]},
}
_JUNIOR_DIST = {
    "role_fit":             {"count": 6, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Medium", "Hard"]},
    "technical_depth":      {"count": 5, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"]},
    "execution_ownership":  {"count": 3, "difficulty": ["Easy", "Medium", "Hard"]},
    "communication":        {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
    "risk_flags":           {"count": 2, "difficulty": ["Easy", "Medium"]},
}
_MID_DIST = {
    "role_fit":             {"count": 5, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"]},
    "technical_depth":      {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
    "execution_ownership":  {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
    "communication":        {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
    "risk_flags":           {"count": 3, "difficulty": ["Easy", "Medium", "Hard"]},
}
_SENIOR_DIST = {
    "role_fit":             {"count": 3, "difficulty": ["Medium", "Medium", "Hard"]},
    "technical_depth":      {"count": 4, "difficulty": ["Medium", "Medium", "Hard", "Hard"]},
    "execution_ownership":  {"count": 5, "difficulty": ["Easy", "Medium", "Medium", "Hard", "Hard"]},
    "communication":        {"count": 4, "difficulty": ["Medium", "Medium", "Hard", "Hard"]},
    "risk_flags":           {"count": 4, "difficulty": ["Easy", "Medium", "Hard", "Hard"]},
}
_CTO_DIST = {
    "role_fit":             {"count": 3, "difficulty": ["Medium", "Hard", "Hard"]},
    "technical_depth":      {"count": 3, "difficulty": ["Medium", "Hard", "Hard"]},
    "execution_ownership":  {"count": 5, "difficulty": ["Medium", "Medium", "Hard", "Hard", "Hard"]},
    "communication":        {"count": 4, "difficulty": ["Medium", "Medium", "Hard", "Hard"]},
    "risk_flags":           {"count": 5, "difficulty": ["Medium", "Medium", "Hard", "Hard", "Hard"]},
}

CATEGORY_DISTRIBUTION: dict[str, dict[str, dict]] = {
    # English keys (primary)
    "Entry": _ENTRY_DIST, "Junior": _JUNIOR_DIST, "Mid": _MID_DIST,
    "Senior": _SENIOR_DIST, "CTO/VP": _CTO_DIST,
    # Korean keys (backward compat)
    "신입": _ENTRY_DIST, "주니어": _JUNIOR_DIST, "미들": _MID_DIST,
    "시니어": _SENIOR_DIST,
}

# ── 카테고리별 데이터 소스 접근 제어 ──
# 각 카테고리에서 사용 가능한 데이터 소스와 수준을 정의
# - "full": 전체 데이터 (경력, 스킬, 프로젝트 등)
# - "skills_only": 스킬/기술 목록만
# - "tech_stack_only": 언어/기술 스택만 (구현 세부사항 제외)
# - "project_scope": 프로젝트 규모/요약만 (코드 세부사항 제외)
# - "role_only": 직무명만
# - "none": 데이터 완전 제외
CATEGORY_DATA_ACCESS: dict[str, dict[str, str]] = {
    "role_fit": {
        "resume": "full",
        "linkedin": "full",
        "code_analysis": "tech_stack_only",
        "jd": "full",
    },
    "technical_depth": {
        "resume": "skills_only",
        "linkedin": "skills_only",
        "code_analysis": "full",
        "jd": "full",
    },
    "execution_ownership": {
        "resume": "full",
        "linkedin": "full",
        "code_analysis": "project_scope",
        "jd": "role_only",
    },
    "communication": {
        "resume": "full",
        "linkedin": "full",
        "code_analysis": "none",
        "jd": "role_only",
    },
    "risk_flags": {
        "resume": "full",
        "linkedin": "full",
        "code_analysis": "tech_stack_only",
        "jd": "full",
    },
}


def get_distribution(experience_level: str) -> dict[str, dict]:
    """경험 레벨에 맞는 카테고리 배분 반환 (fallback: 미들)"""
    return CATEGORY_DISTRIBUTION.get(experience_level, CATEGORY_DISTRIBUTION["Mid"])


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


# ── 카테고리별 컨텍스트 빌더 (섹션별 분리) ──

def _build_resume_section(analysis: dict, level: str) -> str:
    """이력서 섹션 빌드 — level에 따라 포함 범위 조절"""
    doc = analysis.get("document_analysis", {})
    profile = doc.get("profile", {})
    if not profile:
        return ""

    parts = []
    if profile.get("name"):
        parts.append(f"Name: {profile['name']}")

    if level == "full":
        if profile.get("summary"):
            parts.append(f"Summary: {profile['summary'][:200]}")

    # skills_only와 full 모두 스킬 포함
    skills = profile.get("skills", [])
    if skills:
        if isinstance(skills, dict):
            skills = list(skills.keys())
        elif not isinstance(skills, list):
            skills = [str(skills)]
        parts.append(f"Skills: {', '.join(str(s) for s in skills[:15])}")

    if level == "full":
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

    if not parts:
        return ""
    return "## Resume/Portfolio\n" + "\n".join(parts)


def _build_linkedin_section(enriched_input: dict, level: str) -> str:
    """LinkedIn 섹션 빌드 — level에 따라 포함 범위 조절"""
    raw_input = enriched_input.get("raw_input", {})
    linkedin = raw_input.get("linkedin_profile") or enriched_input.get("linkedin_profile", {})
    if not linkedin or not isinstance(linkedin, dict):
        return ""

    parts = []
    name = linkedin.get("full_name") or linkedin.get("name", "")
    headline = linkedin.get("headline", "")
    if name:
        parts.append(f"Name: {name}")
    if headline:
        parts.append(f"Headline: {headline}")

    if level == "full":
        experiences = linkedin.get("experiences") or linkedin.get("experience", [])
        if experiences and isinstance(experiences, list):
            for exp in experiences[:3]:
                if isinstance(exp, dict):
                    title = exp.get("title", "")
                    company = exp.get("company_name") or exp.get("company", "")
                    if title or company:
                        parts.append(f"  - {title} @ {company}")

    # skills_only와 full 모두 스킬 포함
    li_skills = linkedin.get("skills", [])
    if li_skills and isinstance(li_skills, list):
        skill_names = []
        for s in li_skills[:10]:
            skill_names.append(s.get("name", str(s)) if isinstance(s, dict) else str(s))
        parts.append(f"Skills: {', '.join(skill_names)}")

    if not parts:
        return ""
    return "## LinkedIn Profile\n" + "\n".join(parts)


def _build_code_section(analysis: dict, level: str) -> str:
    """코드 분석 섹션 빌드 — level에 따라 포함 범위 조절"""
    code = analysis.get("code_analysis", {})
    if not code:
        return ""

    parts = []

    # tech_stack_only, project_scope, full 모두 언어/기술 포함
    langs = code.get("languages") or code.get("tech_stack", [])
    if langs:
        if isinstance(langs, dict):
            parts.append(f"Languages: {', '.join(list(langs.keys())[:10])}")
        elif isinstance(langs, list):
            parts.append(f"Tech Stack: {', '.join(str(lang) for lang in langs[:10])}")

    if level in ("project_scope", "full"):
        repo_summary = code.get("summary") or code.get("repo_summary", "")
        if repo_summary and isinstance(repo_summary, str):
            parts.append(f"Summary: {repo_summary[:200]}")

    if level == "full":
        top_candidates = code.get("top_question_candidates", [])
        if top_candidates:
            cand_lines = [f"  - {c.get('title', '')}" for c in top_candidates[:5] if isinstance(c, dict)]
            if cand_lines:
                parts.append("Notable Implementations:\n" + "\n".join(cand_lines))

    if not parts:
        return ""
    # tech_stack_only 수준에서는 코드 분석이 아닌 기술 스택 제목 사용 (LLM이 코드 참조 질문 생성 방지)
    heading = "## Technical Skills\n" if level == "tech_stack_only" else "## Code Analysis (GitHub)\n"
    return heading + "\n".join(parts)


def _build_jd_section(analysis: dict, level: str, emphasize: bool = False) -> str:
    """JD 요구사항 섹션 빌드 — level에 따라 포함 범위 조절, emphasize=True시 앵커 텍스트 추가"""
    jd = analysis.get("jd_analysis", {})
    if not jd:
        return ""

    parts = []
    title = jd.get("job_title", "")
    if title:
        parts.append(f"Target Role: {title}")

    if level in ("full", "tech_only"):
        reqs = jd.get("requirements", [])
        if reqs:
            req_skills = []
            for r in reqs[:8]:
                if isinstance(r, dict):
                    req_skills.append(r.get("skill", str(r)))
                else:
                    req_skills.append(str(r))
            parts.append(f"Key Requirements: {', '.join(req_skills)}")

    if not parts:
        return ""
    # JIT-76: emphasize=True면 앵커 텍스트로 LLM에 JD 우선 필터링 지시
    heading = "## JD Requirements — USE THIS AS PRIMARY FILTER\n" if emphasize else "## JD Requirements\n"
    return heading + "\n".join(parts)


def build_candidate_context(
    analysis: dict,
    enriched_input: dict,
    category: str | None = None,
) -> str:
    """
    후보자 정보를 LLM 프롬프트용 요약 텍스트로 조합.
    category가 지정되면 해당 카테고리에 적합한 데이터만 필터링.
    category=None이면 전체 데이터 포함 (select_topics용).
    """
    access = CATEGORY_DATA_ACCESS.get(category) if category else None

    sections = []

    # JIT-76: JD를 최상단에 배치하여 LLM이 JD 기준으로 필터링하도록 유도
    # 1. JD 매칭 요약 (최상단 — PRIMARY FILTER)
    jd_level = access["jd"] if access else "full"
    if jd_level != "none":
        section = _build_jd_section(analysis, jd_level, emphasize=True)
        if section:
            sections.append(section)

    # 2. 이력서/포트폴리오 프로필
    resume_level = access["resume"] if access else "full"
    if resume_level != "none":
        section = _build_resume_section(analysis, resume_level)
        if section:
            sections.append(section)

    # 3. LinkedIn 프로필
    linkedin_level = access["linkedin"] if access else "full"
    if linkedin_level != "none":
        section = _build_linkedin_section(enriched_input, linkedin_level)
        if section:
            sections.append(section)

    # 4. 코드 분석
    code_level = access["code_analysis"] if access else "full"
    if code_level != "none":
        section = _build_code_section(analysis, code_level)
        if section:
            sections.append(section)

    if not sections:
        return ""

    return "\n\n".join(sections)


def format_candidates(candidates: list[dict]) -> str:
    lines = []
    for i, c in enumerate(candidates[:30]):
        lines.append(f"{i+1}. [{c['source']}] {c['topic']} (score: {c['score']})")
    return "\n".join(lines)
