"""
backend/app/workflows/interview_workflow.py
메인 워크플로우: InterviewGenerationWorkflow
"""
import asyncio
import logging
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.models.enums import JobStatus
    from app.workflows.activities.input_enrichment import enrich_input
    from app.workflows.activities.planning import create_execution_plan
    from app.workflows.activities.document_analysis import analyze_documents
    from app.workflows.activities.code_analysis import (
        analyze_code,
        analyze_single_repo,
        validate_code_analysis,
    )
    from app.workflows.activities.jd_analysis import analyze_jd
    from app.workflows.activities.question_generation import (
        select_topics, craft_question,
        enhance_terminology, craft_evaluation_scenarios,
        design_follow_ups, generate_interviewer_notes,
        generate_decision_guide, revise_questions,
    )
    from app.workflows.activities.quality_review import review_questions
    from app.workflows.activities.finalization import finalize_output
    from app.workflows.activities.persist_result import persist_result
    from app.workflows.activities.send_webhook import send_webhook
    from app.workflows.activities.observability_activities import (
        start_job_trace,
        end_job_trace,
    )

logger = logging.getLogger(__name__)

# Workflow version — increment when making breaking changes to the workflow logic.
# Use workflow.patched() for backward-compatible changes to running workflows.
WORKFLOW_VERSION = "1.0.0"

# Retry policies
DEFAULT_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
)

LLM_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=60),
    maximum_attempts=3,
    non_retryable_error_types=["ValueError"],
)

EXTERNAL_API_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=3),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=120),
    maximum_attempts=4,
)


@workflow.defn
class InterviewGenerationWorkflow:
    """면접 스크립트 생성 워크플로우 (4-Phase Pipeline)"""

    def __init__(self):
        self._status = JobStatus.PENDING.value
        self._progress = 0
        self._current_phase = "pending"

    @workflow.run
    async def run(self, input_data: dict) -> dict:
        """메인 실행"""
        logger.info(f"Starting interview generation workflow v{WORKFLOW_VERSION}")

        job_id = input_data.get("job_id")
        user_id = input_data.get("user_id")
        trace_id = None

        # Start Langfuse trace for this job
        if job_id:
            trace_result = await workflow.execute_activity(
                start_job_trace,
                args=[job_id, user_id, {"workflow_version": WORKFLOW_VERSION}],
                start_to_close_timeout=timedelta(seconds=30),
            )
            trace_id = trace_result.get("trace_id")

        try:
            # Version gate: 향후 워크플로우 로직 변경 시 patched()로 분기
            use_enhanced_pipeline = workflow.patched("enhanced-pipeline-v1")

            # Phase 0: Input Enrichment
            self._update_status(JobStatus.ENRICHING, "Phase 0: Input Enrichment", 5)
            enriched = await workflow.execute_activity(
                enrich_input,
                input_data,
                start_to_close_timeout=timedelta(minutes=5),
                heartbeat_timeout=timedelta(seconds=60),
                retry_policy=EXTERNAL_API_RETRY,
            )

            # Phase 1: Planning
            self._update_status(JobStatus.PLANNING, "Phase 1: Planning", 15)
            execution_plan = await workflow.execute_activity(
                create_execution_plan,
                enriched,
                start_to_close_timeout=timedelta(minutes=3),
                heartbeat_timeout=timedelta(seconds=60),
                retry_policy=LLM_RETRY,
            )

            # Phase 2: Parallel Analysis
            self._update_status(JobStatus.ANALYZING, "Phase 2: Analysis", 25)
            raw_input = enriched.get("raw_input", {})
            phases = {p["name"]: p["enabled"] for p in execution_plan.get("phases", [])}

            analysis_tasks = []

            # JD Analysis (항상 실행)
            analysis_tasks.append(
                workflow.execute_activity(
                    analyze_jd,
                    raw_input.get("jd_text", ""),
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=LLM_RETRY,
                )
            )

            # Document Analysis (조건부)
            if phases.get("document_analysis"):
                analysis_tasks.append(
                    workflow.execute_activity(
                        analyze_documents,
                        raw_input,
                        start_to_close_timeout=timedelta(minutes=5),
                        heartbeat_timeout=timedelta(seconds=60),
                        retry_policy=DEFAULT_RETRY,
                    )
                )

            # Code Analysis (조건부) - HYBRID 병렬 처리
            code_analysis_result = None
            if phases.get("code_analysis"):
                code_analysis_result = await self._run_parallel_code_analysis(
                    enriched=enriched,
                    raw_input=raw_input,
                    execution_plan=execution_plan,
                    job_id=job_id,
                )

            analysis_results = await asyncio.gather(*analysis_tasks)

            # Aggregate results
            analysis = {"jd_analysis": analysis_results[0]}
            idx = 1
            if phases.get("document_analysis"):
                analysis["document_analysis"] = analysis_results[idx]
                idx += 1
            if phases.get("code_analysis") and code_analysis_result:
                analysis["code_analysis"] = code_analysis_result

            # Phase 3: Question Generation
            self._update_status(JobStatus.GENERATING, "Phase 3: Generation", 60)

            # 3a. 토픽 선정
            topics = await workflow.execute_activity(
                select_topics,
                args=[analysis, enriched],
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=LLM_RETRY,
            )

            # 3b. 개별 질문 생성 (병렬)
            question_tasks = []
            for topic in topics:
                question_tasks.append(
                    workflow.execute_activity(
                        craft_question,
                        args=[topic, analysis, enriched],
                        start_to_close_timeout=timedelta(minutes=2),
                        retry_policy=LLM_RETRY,
                    )
                )
            questions = await asyncio.gather(*question_tasks)
            questions = list(questions)

            # Phase 3c-3g: Enhancement Agents (병렬)
            self._update_status(JobStatus.GENERATING, "Phase 3: Enhancement", 70)

            enhancement_tasks = [
                # 3c. Terminology Agent
                workflow.execute_activity(
                    enhance_terminology,
                    args=[questions, enriched],
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=LLM_RETRY,
                ),
                # 3d. Scenario Writer Agent
                workflow.execute_activity(
                    craft_evaluation_scenarios,
                    args=[questions, enriched],
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=LLM_RETRY,
                ),
                # 3e. Follow-up Designer Agent
                workflow.execute_activity(
                    design_follow_ups,
                    args=[questions, enriched],
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=LLM_RETRY,
                ),
            ]

            guide_tasks = [
                # 3f. Interviewer Note Agent
                workflow.execute_activity(
                    generate_interviewer_notes,
                    args=[questions, enriched],
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=LLM_RETRY,
                ),
                # 3g. Decision Guide Agent
                workflow.execute_activity(
                    generate_decision_guide,
                    args=[analysis, enriched],
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=LLM_RETRY,
                ),
            ]

            # Run all enhancement agents in parallel
            all_enhancements = await asyncio.gather(
                *enhancement_tasks, *guide_tasks
            )
            terminology = all_enhancements[0]
            scenarios = all_enhancements[1]
            follow_ups = all_enhancements[2]
            interviewer_notes = all_enhancements[3]
            decision_guide = all_enhancements[4]

            # Merge enhancements into questions
            for q in questions:
                q_id = q.get("question_id") or q.get("topic", "")
                if q_id in terminology:
                    q["terminology"] = terminology[q_id]
                if q_id in scenarios:
                    q["evaluation_scenarios"] = scenarios[q_id]
                if q_id in follow_ups:
                    q["follow_up_questions"] = follow_ups[q_id]
                if q_id in interviewer_notes:
                    q["interviewer_note"] = interviewer_notes[q_id]

            # Phase 4: Quality Review + Finalization
            self._update_status(JobStatus.REVIEWING, "Phase 4: Review", 85)

            # 4a. 품질 검토
            review = await workflow.execute_activity(
                review_questions,
                questions,
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=LLM_RETRY,
            )

            # 4a-1. Revision loop (최대 3회)
            revision_count = 0
            max_revisions = 3
            while (
                isinstance(review, dict)
                and review.get("verdict") == "NEEDS_REVISION"
                and revision_count < max_revisions
            ):
                revision_count += 1
                self._update_status(
                    JobStatus.REVIEWING,
                    f"Phase 4: Revision {revision_count}/{max_revisions}",
                    85 + revision_count,
                )
                questions = await workflow.execute_activity(
                    revise_questions,
                    args=[questions, review, enriched],
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=LLM_RETRY,
                )
                review = await workflow.execute_activity(
                    review_questions,
                    questions,
                    start_to_close_timeout=timedelta(minutes=3),
                    retry_policy=LLM_RETRY,
                )

            # 4b. 최종화
            self._update_status(JobStatus.REVIEWING, "Phase 4: Finalization", 90)
            final_script = await workflow.execute_activity(
                finalize_output,
                args=[questions, analysis, enriched],
                start_to_close_timeout=timedelta(minutes=5),
                heartbeat_timeout=timedelta(seconds=60),
                retry_policy=LLM_RETRY,
            )
            # Attach decision guide to final output
            if isinstance(final_script, dict) and decision_guide:
                final_script["decision_guide"] = decision_guide

            # DB에 결과 저장
            job_id = input_data.get("job_id")
            if job_id:
                self._update_status(JobStatus.REVIEWING, "Persisting result", 95)
                await workflow.execute_activity(
                    persist_result,
                    args=[job_id, final_script],
                    start_to_close_timeout=timedelta(minutes=1),
                    retry_policy=DEFAULT_RETRY,
                )

            # Webhook callback (fire-and-forget, 실패해도 워크플로우 성공)
            callback_url = input_data.get("callback_url")
            if callback_url and job_id:
                try:
                    await workflow.execute_activity(
                        send_webhook,
                        args=[job_id, callback_url, "completed", final_script],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                except Exception as we:
                    logger.warning(f"Webhook delivery failed (non-fatal): {we}")

            self._update_status(JobStatus.COMPLETED, "completed", 100)

            # End Langfuse trace with success
            if job_id and trace_id:
                await workflow.execute_activity(
                    end_job_trace,
                    args=[job_id, trace_id, "success", None],
                    start_to_close_timeout=timedelta(seconds=30),
                )

            return {"status": "completed", "script": final_script}

        except Exception as e:
            self._status = JobStatus.FAILED.value
            self._current_phase = "failed"
            logger.error(f"Workflow failed: {e}")

            # End Langfuse trace with failure
            if job_id and trace_id:
                try:
                    await workflow.execute_activity(
                        end_job_trace,
                        args=[job_id, trace_id, "failed", None],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                except Exception:
                    logger.warning("Failed to end Langfuse trace")

            # DB에 실패 상태 저장
            if job_id:
                try:
                    await workflow.execute_activity(
                        persist_result,
                        args=[job_id, {"error": str(e)}],
                        start_to_close_timeout=timedelta(minutes=1),
                    )
                except Exception:
                    logger.error("Failed to persist error status to DB")

            # Webhook callback for failure
            callback_url = input_data.get("callback_url")
            if callback_url and job_id:
                try:
                    await workflow.execute_activity(
                        send_webhook,
                        args=[job_id, callback_url, "failed", {"error": str(e)}],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                except Exception:
                    logger.warning("Webhook delivery for failure failed (non-fatal)")
            raise

    @workflow.query
    def get_status(self) -> str:
        return self._status

    @workflow.query
    def get_progress(self) -> dict:
        return {
            "status": self._status,
            "phase": self._current_phase,
            "progress": self._progress,
        }

    def _update_status(self, status: JobStatus, phase: str, progress: int):
        self._status = status.value
        self._current_phase = phase
        self._progress = progress
        logger.info(f"Phase: {phase} ({progress}%)")

    async def _run_parallel_code_analysis(
        self,
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
        github_urls = enriched.get("github_urls", [])
        if not github_urls:
            return {"repositories": [], "top_question_candidates": []}

        # Step 1: Manager가 레포 필터링
        manager_result = await workflow.execute_activity(
            analyze_code,
            args=[github_urls, raw_input, execution_plan],
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=EXTERNAL_API_RETRY,
        )

        target_repos = manager_result.get("target_repos", [])
        if not target_repos:
            # Fallback: 기존 방식의 결과 사용
            return manager_result

        jd_tech_stack = manager_result.get("jd_tech_stack", [])
        candidate_username = manager_result.get("candidate_username")

        # Step 2: 각 레포 병렬 분석 (Sub-Agents)
        repo_tasks = []
        for repo in target_repos:
            task = workflow.execute_activity(
                analyze_single_repo,
                args=[repo, jd_tech_stack, candidate_username, job_id],
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

                # 원본 repo_info 찾기
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
                        final_results.append(result)  # 원본 결과 사용
                else:
                    final_results.append(result)

        # Step 5: 결과 집계
        return _aggregate_code_analysis(final_results)


def _aggregate_code_analysis(repo_results: list[dict]) -> dict:
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
        # Notable implementations 수집
        notables = repo.get("notable_implementations", [])
        if isinstance(notables, list):
            all_notables.extend(notables)

        # Tech stack 수집
        analysis = repo.get("analysis", {})
        tech_stack = analysis.get("tech_stack", [])
        if isinstance(tech_stack, list):
            all_tech_stack.update(tech_stack)

        # Patterns 카운트
        patterns = analysis.get("patterns", [])
        if isinstance(patterns, list):
            total_patterns += len(patterns)

    # Notable implementations 정렬 (question_potential 기준)
    sorted_notables = sorted(
        all_notables,
        key=lambda x: x.get("question_potential", 0) if isinstance(x, dict) else 0,
        reverse=True,
    )

    # HYBRID 메타데이터 집계
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
