"""
backend/app/workflows/workflow_code_analysis.py
코드 분석 병렬 오케스트레이션 — HYBRID 병렬 분석 + 결과 집계

Extracted from interview_workflow.py for SRP compliance.
"""
import asyncio
import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from app.workflows.workflow_constants import DEFAULT_RETRY, EXTERNAL_API_RETRY
from app.workflows.activities.code_analysis import (
    analyze_code,
    analyze_single_repo,
    validate_code_analysis,
)

logger = logging.getLogger(__name__)


async def run_parallel_code_analysis(
    enriched: dict,
    raw_input: dict,
    execution_plan: dict,
    job_id: str | None,
) -> dict:
    """HYBRID 병렬 코드 분석 실행

    Step 1: Manager가 레포 필터링
    Step 2: 각 레포 병렬 분석 (Sub-Agents)
    Step 3: 품질 검증 (Quality Gate)
    Step 4: 실패한 레포 재분석 (최대 1회)
    Step 5: 결과 집계
    """
    # 버그 수정: enriched에서 candidate_github_username 읽기 (기존: raw_input에서 읽어 누락)
    candidate_username = enriched.get("candidate_github_username")
    candidate_name = enriched.get("candidate_name")

    # enriched_input_data 구성: raw_input + enriched에서 추론된 username 병합
    enriched_input_data = {**raw_input, "candidate_github_username": candidate_username}

    # org repos 병합: personal repos + candidate 식별된 org repos
    personal_github_urls = enriched.get("github_urls", [])
    org_repo_entries = enriched.get("org_github_urls", [])
    org_repo_urls = [r["url"] for r in org_repo_entries if r.get("url")]
    all_github_urls = personal_github_urls + org_repo_urls

    # per-repo candidate_username 매핑 (org repos는 개별 username 사용)
    repo_candidate_map = {}
    for entry in org_repo_entries:
        if entry.get("url") and entry.get("candidate_username"):
            repo_candidate_map[entry["url"]] = entry["candidate_username"]

    if not all_github_urls:
        return {"repositories": [], "top_question_candidates": []}

    # Step 1: Manager가 레포 필터링 + 분석
    manager_result = await workflow.execute_activity(
        analyze_code,
        args=[all_github_urls, enriched_input_data, execution_plan],
        start_to_close_timeout=timedelta(minutes=15),
        heartbeat_timeout=timedelta(seconds=120),
        retry_policy=EXTERNAL_API_RETRY,
    )

    target_repos = manager_result.get("target_repos", [])
    repositories = manager_result.get("repositories", [])

    # Case 1: 분석 결과가 이미 있으면 바로 반환
    if repositories:
        logger.info(f"Code analysis already completed with {len(repositories)} repos")
        return manager_result

    # Case 2: target_repos가 없으면 빈 결과 반환
    if not target_repos:
        logger.info("No target repos found for parallel analysis")
        return manager_result

    jd_tech_stack = manager_result.get("jd_tech_stack", [])
    # manager_result의 candidate_username보다 enriched에서 추론된 것이 우선
    if not candidate_username:
        candidate_username = manager_result.get("candidate_username")

    # Step 2: 각 레포 병렬 분석 (Sub-Agents)
    repo_tasks = []
    for repo in target_repos:
        # per-repo candidate_username 적용 (org repos는 개별 username 사용)
        repo_url = repo.get("url", "")
        per_repo_username = repo_candidate_map.get(repo_url, candidate_username)

        # _candidate_name 주입 → git log fallback용
        repo_with_meta = {**repo, "_candidate_name": candidate_name}

        task = workflow.execute_activity(
            analyze_single_repo,
            args=[repo_with_meta, jd_tech_stack, per_repo_username, job_id],
            start_to_close_timeout=timedelta(minutes=10),
            heartbeat_timeout=timedelta(seconds=120),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(seconds=60),
                maximum_attempts=2,
            ),
        )
        repo_tasks.append(task)

    repo_results = await asyncio.gather(*repo_tasks, return_exceptions=True)

    # 성공한 결과만 필터링
    successful_results = []
    failed_indices = []
    for i, result in enumerate(repo_results):
        if isinstance(result, Exception):
            logger.warning(f"Repo analysis failed: {target_repos[i].get('name')}: {result}")
            failed_indices.append(i)
        else:
            successful_results.append(result)

    # Step 3: 품질 검증 (Quality Gate)
    validation_tasks = []
    for result in successful_results:
        task = workflow.execute_activity(
            validate_code_analysis,
            args=[result],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=DEFAULT_RETRY,
        )
        validation_tasks.append(task)

    validations = await asyncio.gather(*validation_tasks, return_exceptions=True)

    # Step 4: 실패한 레포 재분석 (최대 1회)
    final_results = []
    for i, (result, validation) in enumerate(zip(successful_results, validations)):
        if isinstance(validation, Exception):
            logger.warning(f"Validation failed for {result.get('repo_name')}: {validation}")
            final_results.append(result)
            continue

        if validation.get("valid", True):
            final_results.append(result)
        else:
            # 재분석 시도
            repo_name = result.get("repo_name", "unknown")
            logger.warning(f"Re-analyzing {repo_name}: {validation.get('issues')}")

            original_repo = next(
                (r for r in target_repos if r.get("name") == repo_name),
                target_repos[i] if i < len(target_repos) else None
            )

            if original_repo:
                try:
                    retry_result = await workflow.execute_activity(
                        analyze_single_repo,
                        args=[original_repo, jd_tech_stack, candidate_username, job_id],
                        start_to_close_timeout=timedelta(minutes=15),
                        heartbeat_timeout=timedelta(seconds=120),
                        retry_policy=RetryPolicy(
                            initial_interval=timedelta(seconds=3),
                            backoff_coefficient=2.0,
                            maximum_interval=timedelta(seconds=90),
                            maximum_attempts=1,
                        ),
                    )
                    final_results.append(retry_result)
                except Exception as e:
                    logger.warning(f"Retry failed for {repo_name}: {e}")
                    final_results.append(result)
            else:
                final_results.append(result)

    # Step 5: 결과 집계
    return aggregate_code_analysis(final_results)


def aggregate_code_analysis(repo_results: list[dict]) -> dict:
    """레포별 결과를 종합

    Args:
        repo_results: 각 레포의 분석 결과 리스트

    Returns:
        종합된 코드 분석 결과
    """
    if not repo_results:
        return {
            "repositories": [],
            "combined_tech_stack": [],
            "total_patterns": 0,
            "total_notable_implementations": 0,
            "top_question_candidates": [],
        }

    all_notables = []
    all_tech_stack = set()
    total_patterns = 0

    for repo in repo_results:
        notables = repo.get("notable_implementations", [])
        if isinstance(notables, list):
            all_notables.extend(notables)

        analysis = repo.get("analysis", {})
        tech_stack = analysis.get("tech_stack", [])
        if isinstance(tech_stack, list):
            all_tech_stack.update(tech_stack)

        patterns = analysis.get("patterns", [])
        if isinstance(patterns, list):
            total_patterns += len(patterns)

    sorted_notables = sorted(
        all_notables,
        key=lambda x: x.get("question_potential", 0) if isinstance(x, dict) else 0,
        reverse=True,
    )

    hybrid_summary = {
        "total_repos_analyzed": len(repo_results),
        "repos_with_hybrid": sum(
            1 for r in repo_results if r.get("hybrid_metadata")
        ),
        "total_key_files": sum(
            r.get("hybrid_metadata", {}).get("key_files_count", 0)
            for r in repo_results
        ),
        "total_deep_analyses": sum(
            r.get("hybrid_metadata", {}).get("deep_analyses_count", 0)
            for r in repo_results
        ),
    }

    return {
        "repositories": repo_results,
        "combined_tech_stack": list(all_tech_stack),
        "total_patterns": total_patterns,
        "total_notable_implementations": len(all_notables),
        "top_question_candidates": sorted_notables[:20],
        "hybrid_summary": hybrid_summary,
    }
