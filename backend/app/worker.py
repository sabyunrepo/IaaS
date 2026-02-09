"""
backend/app/worker.py
Temporal Worker 엔트리포인트
"""
import asyncio

from temporalio.worker import Worker

from app.core.config import settings
from app.core.temporal import get_temporal_client
from app.core.observability import setup_langfuse, flush_langfuse
from app.core.logging import setup_logging, get_logger
from app.core.temporal_interceptors import get_worker_interceptors
from app.workflows.interview_workflow import InterviewGenerationWorkflow, WORKFLOW_VERSION

# Structlog 기반 구조화 로깅 설정
setup_logging()
logger = get_logger(__name__)

# Worker build ID for Temporal versioning
WORKER_BUILD_ID = f"vantict-worker-v{WORKFLOW_VERSION}"

# Activity 함수 등록
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
    log_phase_event,
)
from app.workflows.activities.knowledge_graph_activities import (
    build_knowledge_graph,
    get_kg_question_candidates,
    get_evidence_chain,
    clear_knowledge_graph,
)
from app.workflows.activities.intel_generation import generate_intel_brief
from app.workflows.activities.analysis_generation import generate_deep_analysis
from app.workflows.activities.decision_generation import generate_decision_support
from app.workflows.activities.profile_builder import build_candidate_profile
from app.workflows.activities.jd_matching import match_candidate_to_jd

ACTIVITIES = [
    enrich_input,
    create_execution_plan,
    analyze_documents,
    analyze_code,
    analyze_single_repo,      # HYBRID 3-Stage 단일 레포 분석
    validate_code_analysis,   # 코드 분석 품질 검증
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
    # Knowledge Graph activities
    build_knowledge_graph,
    get_kg_question_candidates,
    get_evidence_chain,
    clear_knowledge_graph,
    # v2 Intel/Analysis/Decision generation
    generate_intel_brief,
    generate_deep_analysis,
    generate_decision_support,
    # Profile Builder
    build_candidate_profile,
    # JD Matching
    match_candidate_to_jd,
]


async def main():
    # Initialize Langfuse for LLM observability
    if setup_langfuse():
        logger.info("Langfuse observability enabled")

    logger.info("connecting_to_temporal", host=settings.TEMPORAL_HOST)
    client = await get_temporal_client()

    # Interceptors for Activity monitoring (로깅, 타이밍, 에러 추적)
    interceptors = get_worker_interceptors()

    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[InterviewGenerationWorkflow],
        activities=ACTIVITIES,
        interceptors=interceptors,
    )

    logger.info(
        "worker_started",
        build_id=WORKER_BUILD_ID,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflow_count=len([InterviewGenerationWorkflow]),
        activity_count=len(ACTIVITIES),
        interceptor_count=len(interceptors),
    )
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        # Flush Langfuse on shutdown
        flush_langfuse()
