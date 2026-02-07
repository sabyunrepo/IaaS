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
