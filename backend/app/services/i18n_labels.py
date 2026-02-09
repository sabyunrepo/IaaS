"""
backend/app/services/i18n_labels.py
i18n label helper for rule-based outputs.

Provides translations for hardcoded labels used in rule-based fallback
logic across intel_generation, analysis_generation, and decision_generation.
"""

_LABELS: dict[str, dict[str, str]] = {
    # intel_generation.py -- competency match
    "candidate_no_evidence": {"ko": "후보자: 증거 없음", "en": "Candidate: No evidence"},
    "candidate_strong_match": {"ko": "후보자: 강한 매칭", "en": "Candidate: Strong match"},
    "candidate_partial_match": {"ko": "후보자: 부분 매칭", "en": "Candidate: Partial match"},
    # intel_generation.py -- github summary
    "high": {"ko": "높음", "en": "High"},
    "unconfirmed": {"ko": "미확인", "en": "Unconfirmed"},
    "no_code_data": {"ko": "코드 분석 데이터 없음", "en": "No code analysis data"},
    "tech_stack_confirmed": {"ko": "{n}개 기술 스택 확인", "en": "{n} tech stacks confirmed"},
    # analysis_generation.py -- engineering DNA
    "code_analysis": {"ko": "코드 분석", "en": "Code Analysis"},
    "test_coverage": {"ko": "테스트 커버리지", "en": "Test Coverage"},
    "doc_quality": {"ko": "문서화 품질", "en": "Documentation Quality"},
    "iac": {"ko": "IaC", "en": "IaC"},
    "code_complexity": {"ko": "코드 복잡도", "en": "Code Complexity"},
    "excellent": {"ko": "우수", "en": "Excellent"},
    "moderate": {"ko": "보통", "en": "Moderate"},
    "poor": {"ko": "미흡", "en": "Poor"},
    "confirmed": {"ko": "확인됨", "en": "Confirmed"},
    "low": {"ko": "낮음", "en": "Low"},
    "medium": {"ko": "중간", "en": "Medium"},
    "no_github_data": {"ko": "GitHub 데이터가 제공되지 않았습니다", "en": "No GitHub data provided"},
    "iac_not_found": {
        "ko": "Terraform, Ansible 같은 자동화 도구 사용 흔적이 GitHub에서 발견되지 않았습니다",
        "en": "No IaC tool usage (Terraform, Ansible) found in GitHub",
    },
    "iac_tooltip": {
        "ko": "서버 환경을 코드 파일로 관리하는 방식",
        "en": "Managing server environments as code files",
    },
    # analysis_generation.py -- risk flags
    "risk": {"ko": "리스크", "en": "Risk"},
    "caution": {"ko": "주의", "en": "Caution"},
    "needs_verification": {"ko": "확인 필요", "en": "Needs verification"},
    # analysis_generation.py -- skill table
    "no_evidence": {"ko": "증거 없음", "en": "No evidence"},
    "resume": {"ko": "이력서", "en": "Resume"},
    # decision_generation.py
    "jd_high": {"ko": "높음", "en": "High"},
    "jd_medium": {"ko": "중간", "en": "Medium"},
    "jd_low": {"ko": "낮음", "en": "Low"},
    "other": {"ko": "기타", "en": "Other"},
    "multi_source": {"ko": "다중 출처", "en": "Multi-source"},
    # intel_generation.py -- linkedin warning
    "no_cto_vp_experience": {"ko": "CTO/VP 타이틀 경험 없음", "en": "No CTO/VP title experience"},
    # intel_generation.py -- jd summary fallback
    "software_engineer": {"ko": "소프트웨어 엔지니어", "en": "Software Engineer"},
    # analysis_generation.py -- code analysis fallback
    "no_code_analysis_data": {"ko": "코드 분석 데이터 없음", "en": "No code analysis data"},
    "no_test_coverage_in_quality_metrics": {
        "ko": "quality_metrics에 테스트 커버리지 정보가 없음",
        "en": "No test coverage information in quality_metrics",
    },
    # decision_generation.py -- experience/time labels
    "years_n": {"ko": "{n}년", "en": "{n} years"},
    "years_at_company": {"ko": "{years}년 ({role} @ {company})", "en": "{years} yrs ({role} @ {company})"},
    "minutes_n": {"ko": "{n}분", "en": "{n} min"},
    "verify_resume_achievements": {
        "ko": "해당 경력 관련 구체적 성과와 역할 확인",
        "en": "Verify specific achievements and role for this career history",
    },
    "request_specific_examples": {
        "ko": "관련 경험 구체적 사례 요청",
        "en": "Request specific examples of related experience",
    },
    "ask_for_supporting_evidence": {
        "ko": "해당 주장을 뒷받침하는 구체적 사례를 요청하세요",
        "en": "Ask for specific examples to support these claims",
    },
    "positive_quantified_achievements": {
        "ko": "구체적 수치 기반 성과 설명",
        "en": "Quantified achievement descriptions",
    },
    "positive_failure_learning": {
        "ko": "실패 경험과 학습 내용 공유",
        "en": "Sharing failure experiences and lessons learned",
    },
    "positive_team_collaboration": {
        "ko": "팀 협업 사례 구체적 언급",
        "en": "Specific team collaboration examples",
    },
    "competency_n": {"ko": "역량{n}", "en": "Competency {n}"},
    # scoring_formulas.py -- human_source (비개발자 친화 점수 근거)
    "score_role_fit": {
        "ko": "직무 적합도 {total}점: JD 요구사항 매칭 {jd_pct}% (비중 70%) + 핵심 스킬 일치율 {skill_pct}% (비중 30%)",
        "en": "Role Fit {total}pts: JD requirement match {jd_pct}% (weight 70%) + key skill overlap {skill_pct}% (weight 30%)",
    },
    "score_technical": {
        "ko": "기술 역량 {total}점: 코드 품질 {cq}점 (40%) + 기술 스택 폭 {tb}점 (30%) + 꾸준한 활동 {cc}점 (30%)",
        "en": "Technical {total}pts: code quality {cq} (40%) + tech breadth {tb} (30%) + consistency {cc} (30%)",
    },
    "score_execution": {
        "ko": "실행력 {total}점: 경력 수준 {exp}점 (40%) + 개발 꾸준함 {cc}점 (30%) + 코드 작성량 {vol}점 (30%)",
        "en": "Execution {total}pts: experience {exp} (40%) + consistency {cc} (30%) + code volume {vol} (30%)",
    },
    "score_communication": {
        "ko": "소통/문서화 {total}점: 코드 문서화 수준 {doc}점 (50%) + 코드 가독성 {read}점 (50%)",
        "en": "Communication {total}pts: documentation {doc} (50%) + readability {read} (50%)",
    },
    "score_code_quality": {
        "ko": "코드 품질 {total}점: 테스트·문서화·복잡도·안정성 종합",
        "en": "Code Quality {total}pts: composite of tests, docs, complexity, stability",
    },
    "score_overall_match": {
        "ko": "종합 매칭 {total}점: 스킬({skill}점)×35% + 코드({code}점)×25% + 경력({exp}점)×25% + JD({jd}점)×15%",
        "en": "Overall Match {total}pts: skill({skill})×35% + code({code})×25% + exp({exp})×25% + JD({jd})×15%",
    },
}


def _t(key: str, lang: str = "ko", **kwargs) -> str:
    """Translate a label key to the specified language.

    Args:
        key: Label key from _LABELS dict
        lang: Target language code (ko, en)
        **kwargs: Format parameters for template strings

    Returns:
        Translated string, falls back to English, then key itself
    """
    entry = _LABELS.get(key, {})
    text = entry.get(lang, entry.get("en", key))
    if kwargs:
        text = text.format(**kwargs)
    return text
