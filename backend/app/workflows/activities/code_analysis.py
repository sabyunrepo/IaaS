"""
backend/app/workflows/activities/code_analysis.py
코드 분석 Activity (PyGithub + PyDriller + AST + LLM)

HYBRID 3-Stage Multi-Agent 아키텍처 지원:
- Stage 1: Overview Agent (전체 diff 분석, 핵심 파일 선별)
- Stage 2: Deep Analysis Agents (선별 파일별 심층 분석) [PARALLEL]
- Stage 3: Synthesis Agent (분석 결과 종합)
"""
import asyncio

from temporalio import activity

from app.core.config import settings
from app.core.observability import observe_activity
from app.core.logging import get_logger, JobContextMiddleware
from app.services.activity_logger import ActivityLogger
from app.services.llm_config import KIMI_CODER_MODEL

logger = get_logger(__name__)


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
            since_years=settings.GITHUB_ANALYSIS_YEARS,
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

        total_commits = driller_result["stats"]["total_commits"]
        repositories.append({
            "repo_url": repo_url,
            "repo_name": repo_name,
            "language": primary_lang,
            "candidate_commits": total_commits,
            "commit_count": total_commits,  # alias for intel_generation compatibility
            "candidate_additions": driller_result["stats"]["total_additions"],
            "avg_complexity": driller_result["stats"]["avg_complexity"],
            "monthly_contributions": driller_result.get("monthly_contributions", []),
            "ast_analysis": ast_result,
            "analysis": analysis,
            "notable_implementations": analysis.get("notable_implementations", []),
        })

    # Aggregate
    all_notables = []
    for repo in repositories:
        all_notables.extend(repo.get("notable_implementations", []))

    # Aggregate monthly contributions across all repos
    aggregated_monthly = [0] * 12
    for repo in repositories:
        repo_monthly = repo.get("monthly_contributions", [])
        for idx, count in enumerate(repo_monthly[:12]):
            aggregated_monthly[idx] += count

    # Build code analysis result
    # target_repos 포함: 워크플로우에서 병렬 처리 활성화 기반
    combined_tech = list(set(tech for repo in repositories for tech in repo.get("analysis", {}).get("tech_stack", [])))
    code_analysis_result = {
        "repositories": repositories,
        "target_repos": target_repos,  # Step 2 병렬 처리용
        "jd_tech_stack": jd_tech_stack,
        "candidate_username": candidate_username,
        "combined_tech_stack": combined_tech,
        "tech_stack": combined_tech,  # alias for intel/analysis_generation compatibility
        "total_patterns": sum(len(repo.get("analysis", {}).get("patterns", [])) for repo in repositories),
        "total_notable_implementations": len(all_notables),
        "top_question_candidates": all_notables[:20],
        "monthly_contributions": aggregated_monthly,
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

    # Store code vectors for semantic search (non-blocking)
    if job_id:
        try:
            from app.services.vector_store import get_vector_store
            vs = get_vector_store(job_id)
            await vs.store_code(code_analysis_result)
        except Exception as e:
            logger.warning(f"vector_store_code_failed: {e}", exc_info=False)

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


def _get_file_commits(driller_result: dict, file_path: str) -> list[dict]:
    """특정 파일의 커밋 이력 추출"""
    commits = []
    for diff in driller_result.get("commit_diffs", []):
        if diff.get("file_path") == file_path:
            commits.append({
                "commit_hash": diff.get("commit_hash"),
                "message": diff.get("message"),
                "date": diff.get("date"),
                "additions": diff.get("additions"),
                "deletions": diff.get("deletions"),
            })
    return commits[:10]  # 최대 10개


@activity.defn
@observe_activity(name="analyze_single_repo", phase="analysis")
async def analyze_single_repo(
    repo_info: dict,
    jd_tech_stack: list[str],
    candidate_username: str | None,
    job_id: str | None = None,
) -> dict:
    """
    단일 레포 분석 (HYBRID 3-Stage Multi-Agent)

    Stage 1: Overview Agent - 전체 diff 분석, 핵심 파일 선별
    Stage 2: Deep Analysis Agents - 선별 파일별 심층 분석 [PARALLEL]
    Stage 3: Synthesis Agent - 분석 결과 종합

    모든 LLM 호출은 Kimi K2.5 모델 사용 (비용 최적화)

    Args:
        repo_info: 레포지토리 정보 (url, name, languages 등)
        jd_tech_stack: JD에서 추출한 기술 스택
        candidate_username: 후보자 GitHub username
        job_id: Job ID (로깅용)

    Returns:
        레포지토리 분석 결과 (HYBRID 메타데이터 포함)
    """
    from app.services.code_analyzer import CodeAnalyzer

    analyzer = CodeAnalyzer()
    repo_url = repo_info.get("url", "")
    repo_name = repo_info.get("name", "unknown")

    # Activity Logger 초기화
    alog = ActivityLogger(job_id, "analyze_single_repo", "analyzing") if job_id else None
    if alog:
        await alog.start(f"Analyzing {repo_name} (HYBRID 3-Stage)", {
            "repo_url": repo_url,
            "jd_tech_stack": jd_tech_stack,
        })

    # ================================================================
    # Phase 2: PyDriller - diff 추출 (클론 자동 처리)
    # ================================================================
    activity.heartbeat(f"Phase 2: PyDriller for {repo_name}")
    if alog:
        await alog.progress(f"Phase 2: PyDriller for {repo_name}", {"phase": 2})

    file_types = _jd_to_file_types(jd_tech_stack)
    driller_result = await analyzer.analyze_with_pydriller(
        repo_url=repo_url,
        job_id=job_id or "",
        author=candidate_username,
        since_years=settings.GITHUB_ANALYSIS_YEARS,
        file_types=file_types,
    )

    # ================================================================
    # Phase 3: AST 분석
    # ================================================================
    activity.heartbeat(f"Phase 3: AST for {repo_name}")
    if alog:
        await alog.progress(f"Phase 3: AST for {repo_name}", {
            "phase": 3,
            "files_count": len(driller_result.get("files", [])),
        })

    primary_lang = max(
        repo_info.get("languages", {}),
        key=repo_info.get("languages", {}).get,
        default=None
    )
    top_files = analyzer.select_top_files(
        files=driller_result["files"],
        jd_tech_stack=jd_tech_stack,
        max_files=20,
    )
    ast_result = await analyzer.analyze_ast(files=top_files, primary_language=primary_lang)

    # ================================================================
    # Phase 4: HYBRID 3-Stage LLM 분석 (Kimi Coder 모델 사용)
    # ================================================================

    # ---- Stage 1: Overview Agent ----
    activity.heartbeat(f"Stage 1: Overview Agent for {repo_name}")
    if alog:
        await alog.progress(f"Stage 1: Overview Agent for {repo_name}", {
            "stage": 1,
            "model": KIMI_CODER_MODEL,
        })

    overview_result = await analyzer.llm_overview_analysis(
        files=driller_result["files"],
        commit_diffs=driller_result.get("commit_diffs", []),
        ast_summary=ast_result,
        jd_tech_stack=jd_tech_stack,
        model=KIMI_CODER_MODEL,
    )

    # 핵심 파일 추출 (최대 10개)
    key_files = overview_result.get("key_files", [])[:10]
    if not key_files:
        # Fallback: Overview 실패 시 상위 파일 사용
        key_files = [
            {"path": f.get("filename"), "relevance_score": 0.5, "reason": "Top by complexity"}
            for f in top_files[:5]
        ]

    # ---- Stage 2: Deep Analysis Agents (PARALLEL) ----
    activity.heartbeat(f"Stage 2: Deep Analysis ({len(key_files)} files) for {repo_name}")
    if alog:
        await alog.progress(f"Stage 2: Deep Analysis for {repo_name}", {
            "stage": 2,
            "key_files_count": len(key_files),
        })

    deep_analysis_tasks = []
    for file_info in key_files:
        file_path = file_info.get("path", file_info.get("filename", ""))
        commit_history = _get_file_commits(driller_result, file_path)

        # 파일 diff 정보 추가
        enriched_file_info = {
            **file_info,
            "diff": next(
                (f.get("diff", "") for f in driller_result["files"]
                 if f.get("filename") == file_path),
                ""
            ),
        }

        task = analyzer.llm_deep_file_analysis(
            file_info=enriched_file_info,
            commit_history=commit_history,
            jd_tech_stack=jd_tech_stack,
            model=KIMI_CODER_MODEL,
        )
        deep_analysis_tasks.append(task)

    # 병렬 실행 (asyncio.gather)
    deep_results = await asyncio.gather(*deep_analysis_tasks, return_exceptions=True)

    # 실패한 분석 필터링
    successful_analyses = [
        r for r in deep_results
        if not isinstance(r, Exception) and isinstance(r, dict)
    ]
    failed_count = len(deep_results) - len(successful_analyses)
    if failed_count > 0:
        logger.warning(f"{failed_count} deep analyses failed for {repo_name}")

    # ---- Stage 3: Synthesis Agent ----
    activity.heartbeat(f"Stage 3: Synthesis Agent for {repo_name}")
    if alog:
        await alog.progress(f"Stage 3: Synthesis Agent for {repo_name}", {
            "stage": 3,
            "successful_analyses": len(successful_analyses),
        })

    synthesis_result = await analyzer.llm_synthesize_analysis(
        overview=overview_result,
        deep_analyses=successful_analyses,
        repo_info=repo_info,
        jd_tech_stack=jd_tech_stack,
        model=KIMI_CODER_MODEL,
    )

    # ================================================================
    # 결과 조립
    # ================================================================
    result = {
        "repo_url": repo_url,
        "repo_name": repo_name,
        "language": primary_lang,
        "candidate_commits": driller_result["stats"]["total_commits"],
        "candidate_additions": driller_result["stats"]["total_additions"],
        "avg_complexity": driller_result["stats"]["avg_complexity"],
        "monthly_contributions": driller_result.get("monthly_contributions", []),
        "ast_analysis": ast_result,
        "analysis": synthesis_result,
        "notable_implementations": synthesis_result.get("notable_implementations", []),
        # HYBRID 분석 메타데이터
        "hybrid_metadata": {
            "key_files_count": len(key_files),
            "deep_analyses_count": len(successful_analyses),
            "failed_analyses_count": failed_count,
            "model_used": KIMI_CODER_MODEL,
        },
    }

    if alog:
        await alog.result(f"Completed {repo_name} (HYBRID)", {
            "commits": result["candidate_commits"],
            "notables": len(result["notable_implementations"]),
            "key_files": len(key_files),
            "quality_score": synthesis_result.get("quality_score", 0),
        })

    return result


@activity.defn
@observe_activity(name="validate_code_analysis", phase="analysis")
async def validate_code_analysis(
    repo_result: dict,
    min_commits: int = 1,
    min_notables: int = 0,
) -> dict:
    """
    코드 분석 결과 품질 검증

    Args:
        repo_result: analyze_single_repo 결과
        min_commits: 최소 커밋 수 (기본: 1)
        min_notables: 최소 notable_implementations 수 (기본: 0)

    Returns:
        {
            "valid": bool,
            "issues": list[str],
            "suggestions": list[str],
            "repo_name": str,
        }
    """
    issues = []
    suggestions = []
    repo_name = repo_result.get("repo_name", "unknown")

    # 1. 기본 데이터 검증
    commit_count = repo_result.get("candidate_commits", 0)
    if commit_count < min_commits:
        issues.append(f"커밋 수 부족: {commit_count} < {min_commits}")
        suggestions.append("분석 기간 확대 (since_years + 1)")

    # 2. AST 분석 결과 검증
    ast = repo_result.get("ast_analysis", {})
    functions_count = len(ast.get("functions", []))
    classes_count = len(ast.get("classes", []))
    if not functions_count and not classes_count:
        issues.append("AST에서 함수/클래스 미발견")
        suggestions.append("max_files 증가 또는 file_types 확장")

    # 3. LLM 분석 결과 검증
    analysis = repo_result.get("analysis", {})
    notables = repo_result.get("notable_implementations", [])
    if len(notables) < min_notables:
        issues.append(f"notable_implementations 부족: {len(notables)} < {min_notables}")
        suggestions.append("LLM 프롬프트에 더 구체적 지시 추가")

    # 4. 데이터 일관성 검증
    if functions_count > 0 and not analysis.get("patterns"):
        issues.append("함수는 있으나 패턴 미식별")
        suggestions.append("Deep Analysis 재실행 권장")

    # 5. HYBRID 메타데이터 검증
    hybrid_meta = repo_result.get("hybrid_metadata", {})
    if hybrid_meta.get("deep_analyses_count", 0) == 0 and hybrid_meta.get("key_files_count", 0) > 0:
        issues.append("Deep Analysis 전체 실패")
        suggestions.append("Kimi 모델 연결 확인 필요")

    # 6. 품질 점수 검증
    quality_score = analysis.get("quality_score", 0)
    if quality_score < 0.3 and commit_count > 10:
        issues.append(f"낮은 품질 점수: {quality_score}")
        suggestions.append("코드 품질 평가 기준 재검토")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions,
        "repo_name": repo_name,
        "metrics": {
            "commit_count": commit_count,
            "functions_count": functions_count,
            "classes_count": classes_count,
            "notables_count": len(notables),
            "quality_score": quality_score,
        },
    }
