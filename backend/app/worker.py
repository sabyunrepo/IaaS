"""
backend/app/worker.py
Temporal Worker 엔트리포인트
"""
import asyncio
import logging

from temporalio.worker import Worker

from app.core.config import settings
from app.core.temporal import get_temporal_client
from app.core.observability import setup_langfuse, flush_langfuse
from app.workflows.interview_workflow import InterviewGenerationWorkflow, WORKFLOW_VERSION

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Worker build ID for Temporal versioning
WORKER_BUILD_ID = f"vantict-worker-v{WORKFLOW_VERSION}"

# Activity 함수 등록
from app.workflows.activities.input_enrichment import enrich_input
from app.workflows.activities.planning import create_execution_plan
from app.workflows.activities.document_analysis import analyze_documents
from app.workflows.activities.code_analysis import analyze_code
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
    log_phase_event,
)

ACTIVITIES = [
    enrich_input,
    create_execution_plan,
    analyze_documents,
    analyze_code,
    analyze_jd,
    select_topics,
    craft_question,
    enhance_terminology,
    craft_evaluation_scenarios,
    design_follow_ups,
    generate_interviewer_notes,
    generate_decision_guide,
    revise_questions,
    review_questions,
    finalize_output,
    persist_result,
    send_webhook,
    # Observability activities
    start_job_trace,
    end_job_trace,
    log_phase_event,
]


async def main():
    # Initialize Langfuse for LLM observability
    if setup_langfuse():
        logger.info("Langfuse observability enabled")

    logger.info(f"Connecting to Temporal at {settings.TEMPORAL_HOST}")
    client = await get_temporal_client()

    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[InterviewGenerationWorkflow],
        activities=ACTIVITIES,
    )

    logger.info(
        f"Worker started (build={WORKER_BUILD_ID}), "
        f"listening on task queue: {settings.TEMPORAL_TASK_QUEUE}"
    )
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        # Flush Langfuse on shutdown
        flush_langfuse()
