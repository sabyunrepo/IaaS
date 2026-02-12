"""
backend/app/workflows/activities/code_analysis.py
코드 분석 Activity (PyGithub + PyDriller + AST + LLM)

HYBRID 3-Stage Multi-Agent 아키텍처 지원:
- Stage 1: Overview Agent (전체 diff 분석, 핵심 파일 선별)
- Stage 2: Deep Analysis Agents (선별 파일별 심층 분석) [PARALLEL]
- Stage 3: Synthesis Agent (분석 결과 종합)

shallow clone 통합 (JIT-20):
- shallow clone을 static analysis와 코드 분석이 공유
- PyDriller diff가 0일 때 clone 소스 기반 분석으로 자동 fallback
"""
import asyncio
import shutil

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
    jd_text = input_data.get("jd_text", "") or (execution_plan or {}).get("jd_text", "")

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

    target_repos = await github.select_relevant_repos(
        github_urls=github_urls,
        target_languages=jd_tech_stack,
        min_language_ratio=0.2,
        jd_text=jd_text,
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

    # JIT-25: feature flag로 HYBRID/레거시 분기
    use_clone_based = settings.USE_CLONE_BASED_ANALYSIS

    # Phase 2-4: 레포별 분석
    repositories = []
    for i, repo_info in enumerate(target_repos):
        repo_url = repo_info.get("url", "")
        repo_name = repo_info.get("name", "unknown")

        if use_clone_based:
            # ---- JIT-25: HYBRID 경로 (analyze_single_repo 위임) ----
            activity.heartbeat(f"HYBRID analysis for {repo_name} ({i+1}/{len(target_repos)})")
            if alog:
                await alog.progress(f"HYBRID analysis for {repo_name}", {
                    "phase": "2-4 (HYBRID)",
                    "repo_index": i + 1,
                    "total_repos": len(target_repos),
                    "repo_name": repo_name,
                    "pipeline": "clone_based",
                })

            # analyze_single_repo는 @activity.defn이므로
            # 내부 로직만 직접 호출 (같은 Activity context 내에서)
            repo_result = await _run_single_repo_hybrid(
                repo_info=repo_info,
                jd_tech_stack=jd_tech_stack,
                candidate_username=candidate_username,
                job_id=job_id or "",
            )
            repositories.append(repo_result)
        else:
            # ---- 레거시 경로 (deprecated: JIT-25) ----
            # Phase 2: PyDriller
            activity.heartbeat(f"Phase 2: Analyzing {repo_name} ({i+1}/{len(target_repos)})")
            if alog:
                await alog.progress(f"Phase 2: Analyzing {repo_name}", {
                    "phase": 2,
                    "repo_index": i + 1,
                    "total_repos": len(target_repos),
                    "repo_name": repo_name,
                    "pipeline": "legacy",
                })
            file_types = _jd_to_file_types(jd_tech_stack)
            driller_result = await analyzer.analyze_with_pydriller(
                repo_url=repo_url,
                job_id="",
                author=candidate_username,
                since_years=settings.GITHUB_ANALYSIS_YEARS,
                file_types=file_types,
            )

            # JIT-34: Legacy fallback — GitHub username ≠ git author 시 재시도
            if driller_result["stats"]["total_commits"] == 0 and candidate_username:
                logger.warning(
                    f"Legacy: 0 commits for {repo_name} with author={candidate_username}, "
                    f"retrying without author filter"
                )
                driller_result = await analyzer.analyze_with_pydriller(
                    repo_url=repo_url,
                    job_id="",
                    author=None,
                    since_years=settings.GITHUB_ANALYSIS_YEARS,
                    file_types=file_types,
                )

            # Phase 3: AST (deprecated)
            activity.heartbeat(f"Phase 3: AST analysis for {repo_name}...")
            top_files = analyzer.select_top_files(
                files=driller_result["files"],
                jd_tech_stack=jd_tech_stack,
                max_files=20,
            )
            primary_lang = max(repo_info.get("languages", {}), key=repo_info.get("languages", {}).get, default=None)
            ast_result = await analyzer.analyze_ast(files=top_files, primary_language=primary_lang)

            # Phase 4: LLM (deprecated: rank_files_for_llm + llm_analyze_code)
            activity.heartbeat(f"Phase 4: LLM analysis for {repo_name}...")
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
                "commit_count": total_commits,
                "candidate_additions": driller_result["stats"]["total_additions"],
                "avg_complexity": driller_result["stats"]["avg_complexity"],
                "monthly_contributions": driller_result.get("monthly_contributions", []),
                "ast_analysis": ast_result,
                "analysis": analysis,
                "notable_implementations": analysis.get("notable_implementations", []),
            })

    # ================================================================
    # JIT-37: Cross-Repo 검증 — 모든 레포 분석 완료 후
    # ================================================================
    if use_clone_based and len(repositories) >= 2:
        activity.heartbeat("Cross-repo author verification...")
        try:
            from app.services.github_service import GitHubService
            results_by_repo = {}
            for repo in repositories:
                ir = repo.get("_identity_result")
                if ir is not None:
                    results_by_repo[repo["repo_name"]] = ir

            if len(results_by_repo) >= 2:
                cross_result = GitHubService.verify_cross_repo(results_by_repo)
                # 검증 결과를 각 repo의 candidate_identification에 반영
                for repo in repositories:
                    ci = repo.get("candidate_identification", {})
                    ci["cross_repo_verified"] = cross_result.cross_repo_verified
                    if cross_result.best_match:
                        ci["cross_repo_best_author"] = cross_result.best_match.name
                        ci["cross_repo_confidence"] = cross_result.best_match.confidence
                        ci["cross_repo_repos_matched"] = cross_result.best_match.repos_matched
                    repo["candidate_identification"] = ci

                logger.info(
                    f"Cross-repo verification: verified={cross_result.cross_repo_verified}, "
                    f"best={cross_result.best_match.name if cross_result.best_match else None}, "
                    f"repos_matched={len(results_by_repo)}"
                )
        except Exception as e:
            logger.warning(f"Cross-repo verification failed (non-fatal): {e}")

    # JIT-37: _identity_result 내부 필드 제거 (외부 결과에 포함시키지 않음)
    for repo in repositories:
        repo.pop("_identity_result", None)

    # ================================================================
    # JIT-39: Zero-Contribution 레포 필터링 + 기여도 정합성 검증
    # ================================================================
    from app.services.github_service import GitHubService as _GHSvc

    repo_contribution_breakdown: list[dict] = []
    filtered_repositories: list[dict] = []
    zero_excluded_count = 0

    for repo in repositories:
        validation = _GHSvc.validate_repo_contributions(repo)
        repo_contribution_breakdown.append(validation)

        if validation["is_zero_contribution"]:
            zero_excluded_count += 1
            logger.info(
                f"[JIT-39] Excluding {validation['repo_name']}: "
                f"zero contributions after author filtering"
            )
            continue

        # 기여도 보정 적용
        if validation["correction_applied"]:
            repo["candidate_commits"] = validation["validated_contributions"]
            repo["commit_count"] = validation["validated_contributions"]

        filtered_repositories.append(repo)

    # 전체 레포 Zero인 경우 → 원본 유지 + 경고
    if not filtered_repositories and repositories:
        logger.warning(
            "[JIT-39] All repos have zero contributions — "
            "keeping original results as fallback"
        )
        filtered_repositories = repositories

    if zero_excluded_count > 0:
        logger.info(
            f"[JIT-39] Filtered {zero_excluded_count} zero-contribution repos "
            f"({len(filtered_repositories)} remaining)"
        )

    repositories = filtered_repositories

    # Langfuse span에 repo_contribution_breakdown 기록
    try:
        from langfuse.decorators import langfuse_context
        langfuse_context.update_current_observation(
            metadata={"repo_contribution_breakdown": repo_contribution_breakdown}
        )
    except Exception:
        pass  # Langfuse 비활성 환경에서 무시

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
    # LLM tech_stack + 레포 primary_language 합산 (LLM이 누락해도 GitHub API 언어는 보장)
    combined_tech_set = set(tech for repo in repositories for tech in repo.get("analysis", {}).get("tech_stack", []))
    for repo in repositories:
        lang = repo.get("language")
        if lang and lang not in combined_tech_set:
            combined_tech_set.add(lang)
    combined_tech = list(combined_tech_set)
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
        # JIT-25: 파이프라인 메타데이터
        "pipeline_type": "clone_based" if use_clone_based else "legacy",
        # JIT-39: Zero-contribution 필터링 메타데이터
        "zero_contribution_excluded": zero_excluded_count,
        "repo_contribution_breakdown": repo_contribution_breakdown,
    }

    # JIT-44: HYBRID 분석 집계 필드
    total_ast_chunks = 0
    total_analyzed_functions = 0
    has_hybrid = False
    for repo in repositories:
        meta = repo.get("hybrid_metadata", {})
        if meta:
            has_hybrid = True
            total_ast_chunks += meta.get("ranked_chunks_count", 0)
        ast = repo.get("ast_analysis", {})
        total_analyzed_functions += len(ast.get("functions", []))

    if has_hybrid:
        code_analysis_result["ast_chunk_count"] = total_ast_chunks
        code_analysis_result["analyzed_functions_count"] = total_analyzed_functions
        code_analysis_result["hybrid_metadata"] = {
            "method": "hybrid",
            "total_repos": len(repositories),
            "total_ast_chunks": total_ast_chunks,
            "total_deep_analyses": sum(
                repo.get("hybrid_metadata", {}).get("deep_analyses_count", 0) for repo in repositories
            ),
        }

    # JIT-25: A/B 비교 메트릭 로깅
    _log_pipeline_metrics(code_analysis_result, use_clone_based)

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

    # Store static analysis vectors (non-blocking)
    if job_id:
        for repo in repositories:
            sa = repo.get("static_analysis")
            if sa:
                try:
                    vs = get_vector_store(job_id)
                    await vs.store_static_analysis(sa)
                except Exception as e:
                    logger.warning(f"vector_store_static_analysis_failed: {e}", exc_info=False)

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


def _log_pipeline_metrics(result: dict, use_clone_based: bool) -> None:
    """JIT-25/37: A/B 비교용 파이프라인 메트릭 로깅"""
    repos = result.get("repositories", [])
    pipeline_label = "HYBRID" if use_clone_based else "LEGACY"

    # 핵심 품질 메트릭 수집
    notables_count = result.get("total_notable_implementations", 0)
    patterns_count = result.get("total_patterns", 0)
    tech_count = len(result.get("combined_tech_stack", []))
    question_candidates = len(result.get("top_question_candidates", []))

    # HYBRID 전용 메트릭
    hybrid_chunks = 0
    hybrid_deep = 0
    for repo in repos:
        meta = repo.get("hybrid_metadata", {})
        if meta:
            hybrid_chunks += meta.get("ranked_chunks_count", 0)
            hybrid_deep += meta.get("deep_analyses_count", 0)

    # JIT-37: author 식별 메트릭
    from collections import Counter
    methods = []
    confidences = []
    cross_repo_count = 0
    for repo in repos:
        ci = repo.get("candidate_identification", {})
        method = ci.get("method", "none")
        if "/" in method:
            method = method.split("/")[-1]  # "git_author_validation/name_exact" → "name_exact"
        methods.append(method)
        score = ci.get("confidence_score")
        if score is not None:
            confidences.append(score)
        if ci.get("cross_repo_verified"):
            cross_repo_count += 1

    method_counter = Counter(methods)
    author_match_method = method_counter.most_common(1)[0][0] if method_counter else "none"
    author_avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    # JIT-39: Zero-contribution 메트릭
    zero_excluded = result.get("zero_contribution_excluded", 0)
    corrections = sum(
        1 for b in result.get("repo_contribution_breakdown", [])
        if b.get("correction_applied")
    )

    logger.info(
        f"[A/B] pipeline={pipeline_label} "
        f"repos={len(repos)} "
        f"notables={notables_count} "
        f"patterns={patterns_count} "
        f"tech={tech_count} "
        f"question_candidates={question_candidates} "
        f"hybrid_chunks={hybrid_chunks} "
        f"hybrid_deep={hybrid_deep} "
        f"author_method={author_match_method} "
        f"author_avg_confidence={author_avg_confidence} "
        f"cross_repo_match={cross_repo_count} "
        f"zero_excluded={zero_excluded} "
        f"contribution_corrections={corrections}"
    )


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


async def _run_single_repo_hybrid(
    repo_info: dict,
    jd_tech_stack: list[str],
    candidate_username: str | None,
    job_id: str | None = None,
) -> dict:
    """JIT-25: analyze_code()에서 HYBRID 경로 호출용 내부 함수

    analyze_single_repo()의 핵심 로직을 직접 호출합니다.
    @activity.defn을 경유하지 않으므로 같은 Activity context 내에서 실행됩니다.
    """
    return await _analyze_single_repo_impl(
        repo_info=repo_info,
        jd_tech_stack=jd_tech_stack,
        candidate_username=candidate_username,
        job_id=job_id,
    )


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

    shallow clone 통합 (JIT-20):
    - shallow clone을 static analysis와 공유 (중복 clone 방지)
    - PyDriller diff가 0일 때 clone 소스 기반 분석으로 자동 fallback

    Args:
        repo_info: 레포지토리 정보 (url, name, languages 등)
        jd_tech_stack: JD에서 추출한 기술 스택
        candidate_username: 후보자 GitHub username
        job_id: Job ID (로깅용)

    Returns:
        레포지토리 분석 결과 (HYBRID 메타데이터 포함)
    """
    return await _analyze_single_repo_impl(
        repo_info=repo_info,
        jd_tech_stack=jd_tech_stack,
        candidate_username=candidate_username,
        job_id=job_id,
    )


async def _analyze_single_repo_impl(
    repo_info: dict,
    jd_tech_stack: list[str],
    candidate_username: str | None,
    job_id: str | None = None,
) -> dict:
    """analyze_single_repo 핵심 구현 (Activity wrapper와 내부 호출 공유)"""
    from app.services.code_analyzer import CodeAnalyzer
    from app.services.static_analysis_runner import StaticAnalysisRunner

    analyzer = CodeAnalyzer()
    repo_url = repo_info.get("url", "")
    repo_name = repo_info.get("name", "unknown")
    candidate_name = repo_info.get("_candidate_name")  # git log fallback용

    # 후보자 식별 메타데이터 초기화
    candidate_identification = {
        "method": "provided" if candidate_username else "none",
        "confidence": "high" if candidate_username else "low",
        "original_username": candidate_username,
        "resolved_username": candidate_username,
    }

    # Activity Logger 초기화
    alog = ActivityLogger(job_id, "analyze_single_repo", "analyzing") if job_id else None
    if alog:
        await alog.start(f"Analyzing {repo_name} (HYBRID 3-Stage)", {
            "repo_url": repo_url,
            "jd_tech_stack": jd_tech_stack,
        })

    # ================================================================
    # Phase 1.5: Shallow Clone (공유 — static analysis + source fallback)
    # ================================================================
    clone_dir = None
    runner = StaticAnalysisRunner()
    try:
        activity.heartbeat(f"Shallow clone for {repo_name}")
        clone_dir = await runner.shallow_clone(repo_url)
    except Exception as e:
        logger.warning(f"Shallow clone failed for {repo_name} (non-fatal): {e}")

    try:
        # ================================================================
        # Stage 4: Git log fallback — candidate_username 미제공 시
        # ================================================================
        if not candidate_username and candidate_name and clone_dir:
            activity.heartbeat(f"Git log fallback for {repo_name}")
            try:
                from app.services.github_service import GitHubService
                github_svc = GitHubService()
                git_match = await github_svc.match_candidate_from_git_log(
                    clone_dir=clone_dir,
                    candidate_name=candidate_name,
                )
                if git_match:
                    # PyDriller author 필터용: author name 사용
                    candidate_username = git_match["name"]
                    candidate_identification = {
                        "method": "git_log",
                        "confidence": "medium",
                        "original_username": None,
                        "resolved_username": git_match.get("username"),
                        "matched_author": git_match["name"],
                        "matched_email": git_match["email"],
                        "matched_commits": git_match["commits"],
                    }
                    logger.info(
                        f"Git log fallback matched: {git_match['name']} "
                        f"for {repo_name}"
                    )
            except Exception as e:
                logger.warning(f"Git log fallback failed for {repo_name}: {e}")

        # ================================================================
        # Stage 4.5: GitHub username → git author 검증 (JIT-35/37)
        # 7단계 휴리스틱 + AuthorIdentityResult 배열 반환.
        # JIT-37: confidence < 0.5 → author 필터 비적용 (전체 커밋 수집)
        # ================================================================
        # JIT-36: 다중 author 목록 (PyDriller에 list[str]로 전달)
        candidate_author_names: list[str] = []
        # JIT-37: cross-repo 검증용 identity_result 보존
        repo_identity_result = None

        if candidate_username and clone_dir:
            try:
                from app.services.github_service import GitHubService
                git_authors = await GitHubService.extract_git_authors(clone_dir)
                if git_authors:
                    author_names = [a["name"] for a in git_authors]
                    if candidate_username not in author_names:
                        identity_result = GitHubService.resolve_author_by_identity(
                            candidate_username, git_authors, repo_name=repo_name,
                        )
                        repo_identity_result = identity_result  # JIT-37: cross-repo용 보존

                        if identity_result.best_match:
                            best = identity_result.best_match

                            # JIT-37: confidence < 0.5 → author 필터 비적용
                            if best.confidence < 0.5:
                                logger.warning(
                                    f"Low confidence ({best.confidence}) for "
                                    f"{candidate_username} in {repo_name} — "
                                    f"skipping author filter (full commit collection)"
                                )
                                candidate_username = None
                                candidate_identification = {
                                    "method": f"git_author_validation/{best.method}",
                                    "confidence": "low",
                                    "confidence_score": best.confidence,
                                    "original_username": candidate_username,
                                    "resolved_username": None,
                                    "skipped_low_confidence": True,
                                }
                            else:
                                original = candidate_username
                                candidate_username = best.name
                                confidence = (
                                    "high" if best.confidence >= 0.9
                                    else "medium" if best.confidence >= 0.6
                                    else "low"
                                )
                                # JIT-36: identity-linked 매칭에서 모든 author name 수집
                                candidate_author_names = list(dict.fromkeys(
                                    m.name for m in identity_result.matches
                                    if m.method != "commit_pattern_analysis"
                                ))
                                candidate_identification = {
                                    "method": f"git_author_validation/{best.method}",
                                    "confidence": confidence,
                                    "confidence_score": best.confidence,
                                    "original_username": original,
                                    "resolved_username": candidate_username,
                                    "matched_author": best.name,
                                    "matched_email": best.email,
                                    "matched_commits": best.commits,
                                    "match_candidates": len(identity_result.matches),
                                    "author_names": candidate_author_names,
                                }
                                logger.info(
                                    f"Git author resolved: {original} → "
                                    f"{candidate_username} for {repo_name} "
                                    f"(method={best.method}, "
                                    f"confidence={best.confidence}, "
                                    f"all_authors={candidate_author_names})"
                                )
            except Exception as e:
                logger.warning(f"Git author validation failed for {repo_name}: {e}")

        # Stage 5: 모든 식별 실패 시 → 전체 분석
        if not candidate_username:
            candidate_identification = {
                "method": "none",
                "confidence": "low",
                "original_username": None,
                "resolved_username": None,
            }
            logger.warning(
                f"No candidate identified for {repo_name} — "
                f"analyzing all commits (confidence: low)"
            )

        # ================================================================
        # Phase 2: PyDriller - diff 추출 (클론 자동 처리)
        # ================================================================
        activity.heartbeat(f"Phase 2: PyDriller for {repo_name}")
        if alog:
            await alog.progress(f"Phase 2: PyDriller for {repo_name}", {"phase": 2})

        file_types = _jd_to_file_types(jd_tech_stack)
        # JIT-36: 다중 author 목록이 있으면 list로 전달, 없으면 단일 author 호환
        pydriller_author = candidate_author_names if candidate_author_names else candidate_username
        driller_result = await analyzer.analyze_with_pydriller(
            repo_url=repo_url,
            job_id=job_id or "",
            author=pydriller_author,
            since_years=settings.GITHUB_ANALYSIS_YEARS,
            file_types=file_types,
        )

        # ================================================================
        # Phase 2.1: PyDriller 빈 결과 → clone 소스 fallback (JIT-20)
        # ================================================================
        used_clone_fallback = False
        driller_files = driller_result.get("files", [])
        if not driller_files and clone_dir:
            activity.heartbeat(f"Clone source fallback for {repo_name}")
            if alog:
                await alog.progress(f"Clone source fallback for {repo_name}", {
                    "phase": "2.1",
                    "reason": "PyDriller returned 0 files",
                })
            clone_files = analyzer.read_source_files_from_clone(
                clone_dir=clone_dir,
                file_types=file_types,
                max_files=30,
                token_budget=50_000,
            )
            if clone_files:
                driller_result["files"] = clone_files
                driller_result["stats"]["total_additions"] = sum(f.get("nloc", 0) for f in clone_files)
                used_clone_fallback = True
                logger.info(f"Clone fallback: {len(clone_files)} files for {repo_name}")

        # ================================================================
        # Phase 2.5: Static Analysis (optional, non-blocking)
        # clone_dir 공유 — 중복 clone 방지
        # ================================================================
        static_analysis = None
        candidate_file_paths = [f.get("filename", "") for f in driller_result.get("files", []) if f.get("filename")]
        if candidate_file_paths:
            activity.heartbeat(f"Phase 2.5: Static analysis for {repo_name}")
            if alog:
                await alog.progress(f"Phase 2.5: Static analysis for {repo_name}", {
                    "phase": 2.5,
                    "target_files_count": len(candidate_file_paths),
                })
            try:
                static_result = await runner.run_analysis(
                    repo_url=repo_url,
                    target_files=candidate_file_paths,
                    clone_dir=clone_dir,
                    cleanup=False,
                )
                static_analysis = static_result.model_dump()
                activity.heartbeat("Static analysis completed")
            except Exception as e:
                logger.warning(f"Static analysis failed for {repo_name} (non-fatal): {e}")

        # ================================================================
        # Phase 3: AST 분석 + JD Scoring (JIT-24: feature flag 분기)
        # ================================================================
        primary_lang = max(
            repo_info.get("languages", {}),
            key=repo_info.get("languages", {}).get,
            default=None
        )
        use_ast_pipeline = settings.USE_AST_PIPELINE

        # 공통: AST 분석 (기존 호환용)
        activity.heartbeat(f"Phase 3: AST for {repo_name}")
        if alog:
            await alog.progress(f"Phase 3: AST for {repo_name}", {
                "phase": 3,
                "files_count": len(driller_result.get("files", [])),
                "use_ast_pipeline": use_ast_pipeline,
            })

        top_files = analyzer.select_top_files(
            files=driller_result["files"],
            jd_tech_stack=jd_tech_stack,
            max_files=20,
        )
        ast_result = await analyzer.analyze_ast(files=top_files, primary_language=primary_lang)

        # JIT-24: AST 파이프라인 — clone_dir에서 직접 청크 추출 + JD 스코어링
        ranked_chunks: list[dict] = []
        token_budget = 8000  # JIT-28: 기본값 (AST 파이프라인 비활성 시)
        if use_ast_pipeline and clone_dir:
            activity.heartbeat(f"Phase 3.5: AST chunk extraction + JD scoring for {repo_name}")
            if alog:
                await alog.progress(f"Phase 3.5: JD-Aware chunk scoring for {repo_name}", {
                    "phase": 3.5,
                })

            file_types = _jd_to_file_types(jd_tech_stack)
            all_chunks = analyzer.analyze_directory(
                clone_dir=clone_dir,
                file_types=file_types,
                max_files=50,
            )

            # 동적 토큰 예산 (레포 크기 비례)
            total_nloc = driller_result["stats"].get("total_additions", 0)
            token_budget = analyzer.calculate_dynamic_token_budget(total_nloc)

            ranked_chunks = analyzer.select_top_chunks(
                chunks=all_chunks,
                jd_tech_stack=jd_tech_stack,
                token_budget=token_budget,
            )

            logger.info(
                f"JIT-24 AST pipeline: {len(all_chunks)} chunks → "
                f"{len(ranked_chunks)} selected (budget={token_budget}) for {repo_name}"
            )

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
            ranked_chunks=ranked_chunks if use_ast_pipeline else None,
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
                "use_ast_pipeline": use_ast_pipeline,
            })

        # JIT-24: 청크 기반 소스코드 매핑 (AST 파이프라인)
        chunk_by_file: dict[str, dict] = {}
        if use_ast_pipeline and ranked_chunks:
            for chunk in ranked_chunks:
                fp = chunk.get("file_path", "")
                # 파일별 가장 큰(고점수) 청크를 우선 매핑
                if fp not in chunk_by_file:
                    chunk_by_file[fp] = chunk

        deep_analysis_tasks = []
        for file_info in key_files:
            file_path = file_info.get("path", file_info.get("filename", ""))
            commit_history = _get_file_commits(driller_result, file_path)

            # JIT-24: AST 청크에서 완전한 소스코드 + 메타데이터 가져오기
            if use_ast_pipeline and file_path in chunk_by_file:
                chunk = chunk_by_file[file_path]
                enriched_file_info = {
                    **file_info,
                    "source_code": chunk.get("source_code", ""),
                    "identifiers": chunk.get("identifiers", []),
                    "imports": chunk.get("imports", []),
                    "decorators": chunk.get("decorators", []),
                    "relevance_score": chunk.get("relevance_score", {}),
                }
            else:
                # 레거시 경로: diff 기반
                enriched_file_info = {
                    **file_info,
                    "diff": next(
                        (f.get("diff", "") or f.get("source", "") for f in driller_result["files"]
                         if f.get("filename") == file_path),
                        ""
                    ),
                }

            # JIT-28: 동적 토큰 예산 전달 (AST 파이프라인 시 레포 크기 비례)
            file_token_budget = token_budget if use_ast_pipeline else 8000
            task = analyzer.llm_deep_file_analysis(
                file_info=enriched_file_info,
                commit_history=commit_history,
                jd_tech_stack=jd_tech_stack,
                model=KIMI_CODER_MODEL,
                token_budget=file_token_budget,
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
        # Build quality_metrics from static analysis (if available)
        quality_metrics = {}
        if static_analysis:
            quality_metrics["security_score"] = static_analysis.get("security_score", 100)
            quality_metrics["documentation_ratio"] = static_analysis.get("documentation_ratio", 0.0)
            quality_metrics["test_coverage"] = static_analysis.get("test_to_code_ratio", 0) * 100
            if static_analysis.get("maintainability_index") is not None:
                quality_metrics["maintainability_index"] = static_analysis["maintainability_index"]
            # Lizard multi-language CC takes precedence over PyDriller Python-only CC
            if static_analysis.get("overall_avg_cc", 0) > 0:
                quality_metrics["avg_cc"] = static_analysis["overall_avg_cc"]

        total_commits = driller_result["stats"]["total_commits"]
        result = {
            "repo_url": repo_url,
            "repo_name": repo_name,
            "language": primary_lang,
            "candidate_commits": total_commits,
            "commit_count": total_commits,
            "candidate_additions": driller_result["stats"]["total_additions"],
            "avg_complexity": driller_result["stats"]["avg_complexity"],
            "monthly_contributions": driller_result.get("monthly_contributions", []),
            "ast_analysis": ast_result,
            "analysis": synthesis_result,
            "notable_implementations": synthesis_result.get("notable_implementations", []),
            "quality_metrics": quality_metrics,
            # 정적 분석 결과 (KG/Scoring에서 활용)
            "static_analysis": static_analysis,
            # 후보자 식별 메타데이터
            "candidate_identification": candidate_identification,
            # JIT-37: cross-repo 검증용 identity_result (내부 전용, 최종 결과에서 제거)
            "_identity_result": repo_identity_result,
            # HYBRID 분석 메타데이터
            "hybrid_metadata": {
                "key_files_count": len(key_files),
                "deep_analyses_count": len(successful_analyses),
                "failed_analyses_count": failed_count,
                "model_used": KIMI_CODER_MODEL,
                "has_static_analysis": static_analysis is not None,
                "used_clone_fallback": used_clone_fallback,
                "use_ast_pipeline": use_ast_pipeline,
                "ranked_chunks_count": len(ranked_chunks),
            },
        }

        if alog:
            await alog.result(f"Completed {repo_name} (HYBRID)", {
                "commits": result["candidate_commits"],
                "notables": len(result["notable_implementations"]),
                "key_files": len(key_files),
                "quality_score": synthesis_result.get("quality_score", 0),
                "used_clone_fallback": used_clone_fallback,
                "use_ast_pipeline": use_ast_pipeline,
                "ranked_chunks_count": len(ranked_chunks),
            })

        return result

    finally:
        if clone_dir:
            shutil.rmtree(clone_dir, ignore_errors=True)


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
