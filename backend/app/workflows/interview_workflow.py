"""
backend/app/workflows/interview_workflow.py
메인 워크플로우: InterviewGenerationWorkflow
"""
import asyncio
import logging
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.models.enums import JobStatus
    from app.workflows.activities.input_enrichment import enrich_input
    from app.workflows.activities.planning import create_execution_plan
    from app.workflows.activities.document_analysis import analyze_documents
    from app.workflows.activities.code_analysis import analyze_code
    from app.workflows.activities.jd_analysis import analyze_jd
    from app.workflows.activities.question_generation import select_topics, craft_question
    from app.workflows.activities.quality_review import review_questions
    from app.workflows.activities.finalization import finalize_output

logger = logging.getLogger(__name__)


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
        logger.info(f"Starting interview generation workflow")

        try:
            # Phase 0: Input Enrichment
            self._update_status(JobStatus.ENRICHING, "Phase 0: Input Enrichment", 5)
            enriched = await workflow.execute_activity(
                enrich_input,
                input_data,
                start_to_close_timeout=timedelta(minutes=5),
                heartbeat_timeout=timedelta(seconds=60),
            )

            # Phase 1: Planning
            self._update_status(JobStatus.PLANNING, "Phase 1: Planning", 15)
            execution_plan = await workflow.execute_activity(
                create_execution_plan,
                enriched,
                start_to_close_timeout=timedelta(minutes=3),
                heartbeat_timeout=timedelta(seconds=60),
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
                    )
                )

            # Code Analysis (조건부)
            if phases.get("code_analysis"):
                analysis_tasks.append(
                    workflow.execute_activity(
                        analyze_code,
                        args=[
                            enriched.get("github_urls", []),
                            raw_input,
                            execution_plan,
                        ],
                        start_to_close_timeout=timedelta(minutes=10),
                        heartbeat_timeout=timedelta(seconds=120),
                    )
                )

            analysis_results = await asyncio.gather(*analysis_tasks)

            # Aggregate results
            analysis = {"jd_analysis": analysis_results[0]}
            idx = 1
            if phases.get("document_analysis"):
                analysis["document_analysis"] = analysis_results[idx]
                idx += 1
            if phases.get("code_analysis"):
                analysis["code_analysis"] = analysis_results[idx]

            # Phase 3: Question Generation
            self._update_status(JobStatus.GENERATING, "Phase 3: Generation", 60)

            # 3a. 토픽 선정
            topics = await workflow.execute_activity(
                select_topics,
                args=[analysis, enriched],
                start_to_close_timeout=timedelta(minutes=3),
            )

            # 3b. 개별 질문 생성 (병렬)
            question_tasks = []
            for topic in topics:
                question_tasks.append(
                    workflow.execute_activity(
                        craft_question,
                        args=[topic, analysis, enriched],
                        start_to_close_timeout=timedelta(minutes=2),
                    )
                )
            questions = await asyncio.gather(*question_tasks)
            questions = list(questions)

            # Phase 4: Quality Review + Finalization
            self._update_status(JobStatus.REVIEWING, "Phase 4: Review", 85)

            # 4a. 품질 검토
            review = await workflow.execute_activity(
                review_questions,
                questions,
                start_to_close_timeout=timedelta(minutes=3),
            )

            # 4b. 최종화
            self._update_status(JobStatus.REVIEWING, "Phase 4: Finalization", 90)
            final_script = await workflow.execute_activity(
                finalize_output,
                args=[questions, analysis, enriched],
                start_to_close_timeout=timedelta(minutes=5),
                heartbeat_timeout=timedelta(seconds=60),
            )

            self._update_status(JobStatus.COMPLETED, "completed", 100)
            return {"status": "completed", "script": final_script}

        except Exception as e:
            self._status = JobStatus.FAILED.value
            self._current_phase = "failed"
            logger.error(f"Workflow failed: {e}")
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
