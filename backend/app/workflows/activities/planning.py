"""
backend/app/workflows/activities/planning.py
Phase 1: 실행 계획 수립 Activity
"""
import logging

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def create_execution_plan(enriched_input: dict) -> dict:
    """
    실행 계획 수립 (enriched_input 기반)

    1. enriched_input 검증
    2. GitHub API로 워크로드 추정
    3. 실행 계획 생성
    """
    from app.services.github_service import GitHubService

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
    }

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
