"""
Collector Worker (W1) — GitHub 리포지토리 수집 + 퍼널 필터링.

GitHub GraphQL으로 후보자 리포 목록 → Funnel Stage 1-3 필터링 → shallow clone.
"""
from __future__ import annotations

from typing import Any

from application.states.forensic_state import ForensicState
from domain.matching.funnel_rules import stage1_hard_filter, stage2_relevance_score
from domain.matching.models import FunnelConfig, RepoMetadata
from infrastructure.git.clone_manager import CloneManager
from infrastructure.github.github_client import GitHubClient


async def collector_worker(state: ForensicState) -> dict[str, Any]:
    """GitHub에서 후보자 리포를 수집하고 퍼널 필터링한다."""
    github_client = GitHubClient()
    clone_manager = CloneManager()
    config = FunnelConfig()

    username = state.get("candidate_username")
    github_urls = state.get("github_urls", [])
    jd_languages = state.get("jd_languages", [])
    jd_tech_stack = state.get("jd_tech_stack", [])

    # 1. GitHub API로 리포지토리 목록 수집
    raw_repos: list[dict] = []
    if username:
        raw_repos = await github_client.get_user_repos(username)

    # URL에서 직접 지정된 리포도 포함
    for url in github_urls:
        parts = url.rstrip("/").split("/")
        if len(parts) >= 2:
            owner, name = parts[-2], parts[-1]
            raw_repos.append({
                "name": name,
                "owner": owner,
                "url": url,
                "is_fork": False,
                "languages": [],
                "total_loc": 0,
                "days_since_push": 0,
            })

    # 2. RepoMetadata로 변환
    repo_metas = [
        RepoMetadata(
            name=r.get("name", ""),
            owner=r.get("owner", username or ""),
            url=r.get("url", r.get("html_url", "")),
            is_fork=r.get("is_fork", r.get("fork", False)),
            languages=r.get("languages", []),
            total_loc=r.get("total_loc", r.get("size", 0)),
            days_since_push=r.get("days_since_push", 0),
            detected_tech_stack=r.get("detected_tech_stack", []),
            description=r.get("description", "") or "",
        )
        for r in raw_repos
        if r.get("name")
    ]

    # 3. Funnel Stage 1: Hard Filter
    filtered = stage1_hard_filter(repo_metas, jd_languages, config)

    # 4. Funnel Stage 2: Relevance Score + Top-K
    scored = stage2_relevance_score(filtered, jd_tech_stack, jd_tech_stack)
    top_repos = [repo for repo, _score in scored[: config.top_k]]

    # 5. Shallow Clone
    collected = []
    local_paths = []
    for repo in top_repos:
        try:
            path = await clone_manager.shallow_clone(repo.url)
            local_paths.append(str(path))
            collected.append(repo.model_dump())
        except Exception:
            continue

    return {
        "collected_repos": collected,
        "repo_local_paths": local_paths,
    }
