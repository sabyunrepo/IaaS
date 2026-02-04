"""
backend/app/workflows/activities/code_analysis.py
코드 분석 Activity (PyGithub + PyDriller + AST + LLM)
"""
import logging

from temporalio import activity

from app.core.observability import observe_activity
from app.services.activity_logger import ActivityLogger

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

    # Initialize activity logger
    job_id = input_data.get("job_id")
    alog = ActivityLogger(job_id, "code_analysis", "analyzing") if job_id else None

    if alog:
        await alog.start("Starting code analysis", {
            "github_urls_count": len(github_urls),
            "jd_tech_stack": jd_tech_stack,
            "candidate_username": candidate_username,
        })

    # Phase 1: JD 매칭 레포 선별
    activity.heartbeat("Phase 1: Filtering repos by JD tech stack...")
    if alog:
        await alog.progress("Phase 1: Filtering repos by JD tech stack", {
            "phase": 1,
            "target_languages": jd_tech_stack,
        })

    target_repos = await github.filter_repos_by_language(
        github_urls=github_urls,
        target_languages=jd_tech_stack,
        min_language_ratio=0.3,
    )

    if not target_repos:
        if alog:
            await alog.result("No matching repositories found", {
                "repositories_count": 0,
                "top_question_candidates_count": 0,
            })
        return {"repositories": [], "top_question_candidates": []}

    if alog:
        await alog.progress("Phase 1 complete: Repos filtered", {
            "filtered_repos_count": len(target_repos),
            "repos": [r.get("name", "unknown") for r in target_repos],
        })

    # Phase 2-4: 레포별 분석
    repositories = []
    for i, repo_info in enumerate(target_repos):
        repo_url = repo_info.get("url", "")
        repo_name = repo_info.get("name", "unknown")

        # Phase 2: PyDriller
        activity.heartbeat(f"Phase 2: Analyzing {repo_name} ({i+1}/{len(target_repos)})")
        if alog:
            await alog.progress(f"Phase 2: Analyzing {repo_name}", {
                "phase": 2,
                "repo_index": i + 1,
                "total_repos": len(target_repos),
                "repo_name": repo_name,
            })
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
        if alog:
            await alog.progress(f"Phase 3: AST analysis for {repo_name}", {
                "phase": 3,
                "repo_name": repo_name,
                "files_count": len(driller_result.get("files", [])),
            })
        top_files = analyzer.select_top_files(
            files=driller_result["files"],
            jd_tech_stack=jd_tech_stack,
            max_files=20,
        )
        primary_lang = max(repo_info.get("languages", {}), key=repo_info.get("languages", {}).get, default=None)
        ast_result = await analyzer.analyze_ast(files=top_files, primary_language=primary_lang)

        # Phase 4: LLM
        activity.heartbeat(f"Phase 4: LLM analysis for {repo_name}...")
        if alog:
            await alog.progress(f"Phase 4: LLM analysis for {repo_name}", {
                "phase": 4,
                "repo_name": repo_name,
                "ast_functions_count": len(ast_result.get("functions", [])),
                "ast_classes_count": len(ast_result.get("classes", [])),
            })
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

    # Build code analysis result
    code_analysis_result = {
        "repositories": repositories,
        "combined_tech_stack": list(set(tech for repo in repositories for tech in repo.get("analysis", {}).get("tech_stack", []))),
        "total_patterns": sum(len(repo.get("analysis", {}).get("patterns", [])) for repo in repositories),
        "total_notable_implementations": len(all_notables),
        "top_question_candidates": all_notables[:20],
    }

    # Extract and store KG entities (non-blocking)
    job_id = input_data.get("job_id")
    kg_entity_count = 0

    if job_id:
        activity.heartbeat("Extracting KG entities from code analysis...")
        try:
            from app.services.knowledge_graph import get_knowledge_graph
            kg = get_knowledge_graph(job_id)
            extraction_result = await kg.extract_and_store_code_entities(code_analysis_result)
            kg_entity_count = len(extraction_result.entities)
            logger.info(f"Extracted {kg_entity_count} KG entities from code analysis for job {job_id}")
        except Exception as e:
            logger.warning(f"KG extraction failed (non-fatal): {e}")

    # Log final result
    if alog:
        await alog.result("Code analysis completed", {
            "repositories_analyzed": len(repositories),
            "combined_tech_stack": code_analysis_result.get("combined_tech_stack", []),
            "total_patterns": code_analysis_result.get("total_patterns", 0),
            "total_notable_implementations": code_analysis_result.get("total_notable_implementations", 0),
            "top_question_candidates_count": len(code_analysis_result.get("top_question_candidates", [])),
            "kg_entity_count": kg_entity_count,
        })

    return {
        **code_analysis_result,
        "kg_entity_count": kg_entity_count,
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
