"""
backend/app/workflows/interview_workflow.py
메인 워크플로우: InterviewGenerationWorkflow
"""
import logging
from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.models.enums import JobStatus
    from app.workflows.activities.input_enrichment import enrich_input

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
            # TODO: Step 9 — planning activity

            # Phase 2: Parallel Analysis
            self._update_status(JobStatus.ANALYZING, "Phase 2: Analysis", 25)
            # TODO: Step 10 — parallel analysis activities

            # Phase 3: Question Generation
            self._update_status(JobStatus.GENERATING, "Phase 3: Generation", 60)
            # TODO: Step 11 — question generation activities

            # Phase 4: Quality Review + Finalization
            self._update_status(JobStatus.REVIEWING, "Phase 4: Review", 85)
            # TODO: Step 12 — review + finalize activities

            self._update_status(JobStatus.COMPLETED, "completed", 100)
            return {"status": "completed", "message": "Interview script generated"}

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
