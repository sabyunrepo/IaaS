"""
RepoCollector 노드 — GitHub 리포 수집 + 퍼널 + shallow clone + sparse checkout.

Phase 8: Collector에서 clone 로직을 MetaGraph 레벨로 분리하여
forensic/logic 병렬 실행의 전제 조건을 만든다.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from application.states.meta_state import MetaState
from domain.matching.funnel_rules import stage1_hard_filter, stage2_relevance_score
from domain.matching.language_extensions import get_sparse_checkout_patterns
from domain.matching.models import FunnelConfig, RepoMetadata
from infrastructure.git.clone_manager import CloneManager
from infrastructure.github.github_client import GitHubClient
from infrastructure.persistence.repository import AnalysisRepository, JobRepository

logger = logging.getLogger(__name__)


async def repo_collector_node(state: MetaState) -> dict[str, Any]:
    """GitHub 리포를 수집, 필터링, clone하여 repo_paths_ref를 반환한다."""
    job_id = state["job_id"]
    db_url = os.environ.get("DATABASE_URL", "")

    try:
        # 1. Load: DB에서 input_data 로드
        job_repo = JobRepository(db_url)
        job = await job_repo.get(job_id)
        input_data = job.get("input_data", {}) if job else {}

        github_client = GitHubClient()
        clone_manager = CloneManager()
        config = FunnelConfig()

        username = input_data.get("candidate_username")
        github_urls = input_data.get("github_urls", [])
        jd_languages = input_data.get("jd_languages", [])
        jd_tech_stack = input_data.get("jd_tech_stack", [])

        # 2. GitHub API로 리포 수집
        raw_repos: list[dict] = []
        if username:
            raw_repos = await github_client.get_user_repos(username)

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

        # 3. RepoMetadata 변환 + 퍼널 필터링
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

        filtered = stage1_hard_filter(repo_metas, jd_languages, config)
        scored = stage2_relevance_score(filtered, jd_tech_stack, jd_tech_stack)
        top_repos = [repo for repo, _score in scored[: config.top_k]]

        # 4. Shallow Clone + Sparse Checkout
        sparse_patterns = get_sparse_checkout_patterns(jd_languages)
        collected = []
        local_paths = []
        for repo in top_repos:
            try:
                path = await clone_manager.shallow_clone(repo.url)
                if sparse_patterns:
                    try:
                        await clone_manager.sparse_checkout(path, sparse_patterns)
                    except Exception:
                        logger.warning("Sparse checkout failed for %s", repo.name)
                local_paths.append(str(path))
                collected.append(repo.model_dump())
            except Exception:
                continue

        # 5. Save: DB에 저장
        analysis_repo = AnalysisRepository(db_url)
        result_id = await analysis_repo.save_result(
            job_id,
            "repo_collector",
            "meta",
            {
                "collected_repos": collected,
                "repo_local_paths": local_paths,
                "jd_languages": jd_languages,
                "jd_tech_stack": jd_tech_stack,
                "sparse_patterns": sparse_patterns,
            },
        )

        await job_repo.update_status(job_id, "analyzing", progress=0.15)

        return {"repo_paths_ref": result_id}

    except Exception as e:
        logger.error("repo_collector_node failed for job %s: %s", job_id, e)
        analysis_repo = AnalysisRepository(db_url)
        result_id = await analysis_repo.save_result(
            job_id, "repo_collector", "meta", {"error": str(e), "status": "failed"}
        )
        return {
            "repo_paths_ref": result_id,
            "errors": state.get("errors", []) + [f"repo_collector: {e}"],
        }
