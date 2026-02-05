"""
backend/app/workflows/activities/planning.py
Phase 1: 실행 계획 수립 Activity
"""
import logging

from temporalio import activity

from app.core.observability import observe_activity
from app.services.activity_logger import ActivityLogger

logger = logging.getLogger(__name__)


@activity.defn
@observe_activity(name="create_execution_plan", phase="planning")
async def create_execution_plan(enriched_input: dict) -> dict:
    """
    실행 계획 수립 (enriched_input 기반)

    1. enriched_input 검증
    2. GitHub API로 워크로드 추정
    3. 실행 계획 생성
    """
    from app.services.github_service import GitHubService

    # Initialize activity logger
    job_id = enriched_input.get("raw_input", {}).get("job_id")
    alog = ActivityLogger(job_id, "planning", "planning") if job_id else None

    github_urls = enriched_input.get("github_urls", [])
    available = enriched_input.get("available_analyses", [])

    # Debug logging for troubleshooting
    logger.info(f"[Planning] Received github_urls: {github_urls}")
    logger.info(f"[Planning] Received available_analyses: {available}")
    logger.info(f"[Planning] code_analysis enabled: {'code_analysis' in available}")

    if alog:
        await alog.start("Creating execution plan", {
            "github_urls_count": len(github_urls),
            "available_analyses": available,
        })

    github = GitHubService()
    raw_input = enriched_input.get("raw_input", {})

    # GitHub 워크로드 추정
    workload = {}
    github_urls = enriched_input.get("github_urls", [])

    for url in github_urls:
        activity.heartbeat(f"Estimating workload for {url}...")
        repo_info = await github.get_repo_info(url)
        languages = await github.get_repo_languages(url)
        workload[url] = {
            "total_files": repo_info.get("size", 0),
            "languages": languages,
            "estimated_time_seconds": _calculate_time(repo_info),
        }

    # 사용 가능한 분석 목록
    available = enriched_input.get("available_analyses", [])

    # JD text에서 기술 스택 추출 (code_analysis에서 사용)
    jd_text = raw_input.get("jd_text", "")
    jd_tech_stack = _extract_tech_stack_from_jd(jd_text)

    # workload에서 수집된 언어들도 포함
    repo_languages = set()
    for w in workload.values():
        repo_languages.update(w.get("languages", {}).keys())

    # JD tech_stack과 repo languages 병합 (JD 우선)
    if not jd_tech_stack and repo_languages:
        jd_tech_stack = list(repo_languages)

    logger.info(f"[Planning] Extracted jd_tech_stack: {jd_tech_stack}")

    plan = {
        "candidate_github_username": enriched_input.get("candidate_github_username"),
        "phases": [
            {"name": "document_analysis", "enabled": "document_analysis" in available},
            {"name": "code_analysis", "enabled": "code_analysis" in available},
            {"name": "jd_analysis", "enabled": True},
        ],
        "workload": workload,
        "estimated_total_time_seconds": sum(
            w["estimated_time_seconds"] for w in workload.values()
        ) + 120,
        "raw_input": raw_input,
        "jd_tech_stack": jd_tech_stack,  # ✅ code_analysis에서 사용
    }

    # Log final result
    if alog:
        await alog.result("Execution plan created", {
            "enabled_phases": [p["name"] for p in plan["phases"] if p["enabled"]],
            "estimated_total_time_seconds": plan["estimated_total_time_seconds"],
            "repos_analyzed": len(workload),
        })

    return plan


def _calculate_time(repo_info: dict) -> int:
    """레포 크기 기반 분석 소요 시간 추정 (초)"""
    size = repo_info.get("size", 0)  # KB
    if size < 1000:
        return 30
    elif size < 10000:
        return 60
    elif size < 100000:
        return 120
    return 300


def _extract_tech_stack_from_jd(jd_text: str) -> list[str]:
    """JD 텍스트에서 기술 스택 키워드 추출 (regex 기반)

    code_analysis에서 레포 필터링에 사용됨.
    """
    import re

    # 주요 프로그래밍 언어 및 기술 패턴
    tech_patterns = {
        # Languages (대소문자 무시)
        r'\bPython\b': 'Python',
        r'\bJavaScript\b': 'JavaScript',
        r'\bTypeScript\b': 'TypeScript',
        r'\bJava\b(?!\s*Script)': 'Java',  # JavaScript와 구분
        r'\bGo\b(?:lang)?\b': 'Go',
        r'\bRust\b': 'Rust',
        r'\bC\+\+\b': 'C++',
        r'\bC#\b': 'C#',
        r'\bRuby\b': 'Ruby',
        r'\bPHP\b': 'PHP',
        r'\bSwift\b': 'Swift',
        r'\bKotlin\b': 'Kotlin',
        r'\bScala\b': 'Scala',
        r'\bR\b(?:\s+language)?': 'R',
        # Frameworks/Technologies (언어 추론)
        r'\bReact\b': 'JavaScript',
        r'\bVue\b': 'JavaScript',
        r'\bAngular\b': 'TypeScript',
        r'\bNode\.?js\b': 'JavaScript',
        r'\bDjango\b': 'Python',
        r'\bFlask\b': 'Python',
        r'\bFastAPI\b': 'Python',
        r'\bSpring\b': 'Java',
        r'\bRails\b': 'Ruby',
        r'\bLaravel\b': 'PHP',
        r'\bNext\.?js\b': 'TypeScript',
        r'\bNuxt\b': 'JavaScript',
    }

    found = set()
    text_lower = jd_text

    for pattern, language in tech_patterns.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            found.add(language)

    return list(found)
