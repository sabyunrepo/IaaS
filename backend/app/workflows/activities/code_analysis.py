"""
backend/app/workflows/activities/code_analysis.py
코드 분석 Activity (PyGithub + PyDriller + AST + LLM)
"""
import logging

from temporalio import activity

from app.core.observability import observe_activity

logger = logging.getLogger(__name__)


@activity.defn
@observe_activity(name="analyze_code", phase="analysis")
async def analyze_code(
    github_urls: list[str],
    input_data: dict,
    execution_plan: dict | None = None,
) -> dict:
    """
    GitHub 코드 분석 — 4-Phase 파이프라인

    Phase 1 (PyGithub): JD 매칭 레포 선별
    Phase 2 (PyDriller): 후보자 코드 추출 + 정적 메트릭
    Phase 3 (AST): 구조적 코드 분석
    Phase 4 (LLM): 의미 분석 + 질문 후보 추출
    """
    from app.services.github_service import GitHubService
    from app.services.code_analyzer import CodeAnalyzer

    github = GitHubService()
    analyzer = CodeAnalyzer()

    jd_tech_stack = (execution_plan or {}).get("jd_tech_stack") or input_data.get("jd_tech_stack", [])
    candidate_username = input_data.get("candidate_github_username")

    # Phase 1: JD 매칭 레포 선별
    activity.heartbeat("Phase 1: Filtering repos by JD tech stack...")
    target_repos = await github.filter_repos_by_language(
        github_urls=github_urls,
        target_languages=jd_tech_stack,
        min_language_ratio=0.3,
    )

    if not target_repos:
        return {"repositories": [], "top_question_candidates": []}

    # Phase 2-4: 레포별 분석
    repositories = []
    for i, repo_info in enumerate(target_repos):
        repo_url = repo_info.get("url", "")
        repo_name = repo_info.get("name", "unknown")

        # Phase 2: PyDriller
        activity.heartbeat(f"Phase 2: Analyzing {repo_name} ({i+1}/{len(target_repos)})")
        file_types = _jd_to_file_types(jd_tech_stack)
        driller_result = await analyzer.analyze_with_pydriller(
            repo_url=repo_url,
            job_id="",
            author=candidate_username,
            since_years=3,
            file_types=file_types,
        )

        # Phase 3: AST
        activity.heartbeat(f"Phase 3: AST analysis for {repo_name}...")
        top_files = analyzer.select_top_files(
            files=driller_result["files"],
            jd_tech_stack=jd_tech_stack,
            max_files=20,
        )
        primary_lang = max(repo_info.get("languages", {}), key=repo_info.get("languages", {}).get, default=None)
        ast_result = await analyzer.analyze_ast(files=top_files, primary_language=primary_lang)

        # Phase 4: LLM
        activity.heartbeat(f"Phase 4: LLM analysis for {repo_name}...")
        ranked_files = analyzer.rank_files_for_llm(
            files=driller_result["files"],
            jd_tech_stack=jd_tech_stack,
            token_budget=30_000,
        )
        analysis = await analyzer.llm_analyze_code(ranked_files, ast_context=ast_result)

        repositories.append({
            "repo_url": repo_url,
            "repo_name": repo_name,
            "language": primary_lang,
            "candidate_commits": driller_result["stats"]["total_commits"],
            "candidate_additions": driller_result["stats"]["total_additions"],
            "avg_complexity": driller_result["stats"]["avg_complexity"],
            "ast_analysis": ast_result,
            "analysis": analysis,
            "notable_implementations": analysis.get("notable_implementations", []),
        })

    # Aggregate
    all_notables = []
    for repo in repositories:
        all_notables.extend(repo.get("notable_implementations", []))

    return {
        "repositories": repositories,
        "top_question_candidates": all_notables[:20],
    }


def _jd_to_file_types(jd_tech_stack: list[str]) -> list[str]:
    """JD 기술스택 → 분석 대상 파일 확장자"""
    mapping = {
        "Python": [".py"], "JavaScript": [".js", ".jsx"],
        "TypeScript": [".ts", ".tsx"], "Java": [".java"],
        "Go": [".go"], "Rust": [".rs"], "C++": [".cpp", ".hpp"],
    }
    types = []
    for tech in jd_tech_stack:
        types.extend(mapping.get(tech, []))
    return types or [".py"]
