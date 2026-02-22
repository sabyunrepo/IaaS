"""
QuestionOrchestrator 노드 — 면접 질문 생성 (Phase 3).

TopicSelector(pgvector) + 3전략 QuestionCrafter를 조합하여
후보자 코드 기반 면접 질문을 생성한다.

1. TopicSelector: JD 관련성 높은 코드 청크를 벡터 검색으로 선별
2. QuestionCrafter x 3: Negative Selection / Intentional Complexity / Code Evolution
3. InterviewScript aggregate로 조립 후 DB 저장, ref 반환
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import Any

from domain.analysis.context_budget import ContextBudget
from domain.question.models import (
    InterviewQuestion,
    InterviewScript,
    QuestionCategory,
    QuestionStrategy,
)
from application.states.meta_state import MetaState
from infrastructure.embedding.embedding_service import EmbeddingService
from infrastructure.embedding.pgvector_store import PgvectorStore
from infrastructure.llm.instructor_client import InstructorClient
from infrastructure.persistence.repository import AnalysisRepository

logger = logging.getLogger(__name__)

# ─── 3전략 프롬프트 ────────────────────────────────────────────────

NEGATIVE_SELECTION_PROMPT = """\
You are an expert technical interviewer using the **Negative Selection** strategy.
Given the candidate's code analysis, identify technologies/patterns that COULD have been used but WERE NOT.
Generate interview questions that probe whether this was an intentional trade-off or a knowledge gap.

Rules:
- Each question MUST reference specific code the candidate wrote
- Focus on what's MISSING, not what's present
- Questions should distinguish deliberate choices from ignorance
- Generate 3 questions with varied difficulty (easy, medium, hard)

Candidate Profile:
{profile_context}

Code Analysis:
{code_context}

JD Requirements:
{jd_context}
"""

INTENTIONAL_COMPLEXITY_PROMPT = """\
You are an expert technical interviewer using the **Intentional Complexity** strategy.
Given the candidate's code analysis, find functions/modules with unusually HIGH complexity
(high cyclomatic complexity, deep nesting, many branches).
Generate questions that probe whether this complexity was intentional and justified.

Rules:
- Each question MUST cite specific metrics (e.g., cyclomatic complexity, branch count)
- Questions should distinguish "necessary complexity" from "poor design"
- Generate 3 questions with varied difficulty (easy, medium, hard)

Candidate Profile:
{profile_context}

Code Analysis:
{code_context}

Complexity Metrics:
{complexity_context}
"""

CODE_EVOLUTION_PROMPT = """\
You are an expert technical interviewer using the **Code Evolution** strategy.
Given the candidate's code analysis, examine patterns that suggest the code has evolved over time
(refactoring signs, multiple approaches in different files, inconsistent patterns).
Generate questions about the evolution process that only the actual author could answer.

Rules:
- Each question should probe knowledge of WHY changes were made, not just WHAT changed
- Focus on design decisions that evolved over time
- Generate 3 questions with varied difficulty (easy, medium, hard)

Candidate Profile:
{profile_context}

Code Analysis:
{code_context}

Evolution Evidence:
{evolution_context}
"""


# ─── TopicSelector ─────────────────────────────────────────────────

async def _select_topics(
    job_id: str,
    jd_tech_stack: list[str],
    embedding_service: EmbeddingService,
    vector_store: PgvectorStore,
) -> list[dict[str, Any]]:
    """JD 관련성이 높은 코드 청크를 벡터 검색으로 선별한다."""
    if not jd_tech_stack:
        return []

    query_text = "Technical skills: " + ", ".join(jd_tech_stack)

    try:
        query_embedding = await embedding_service.embed(query_text)
        results = await vector_store.search_similar(
            query_embedding=query_embedding,
            kind="code",
            job_id=job_id,
            top_k=15,
        )
        return [
            {
                "content": r.content,
                "metadata": r.metadata,
                "similarity": r.similarity,
            }
            for r in results
        ]
    except Exception as e:
        logger.warning("TopicSelector vector search failed: %s", e)
        return []


# ─── QuestionCrafter ───────────────────────────────────────────────

async def _craft_questions_for_strategy(
    strategy: QuestionStrategy,
    prompt_template: str,
    profile_context: str,
    code_context: str,
    extra_context: str,
    extra_context_key: str,
    client: InstructorClient,
) -> list[InterviewQuestion]:
    """하나의 전략으로 질문 3개를 생성한다."""
    prompt = prompt_template.format(
        profile_context=profile_context,
        code_context=code_context,
        **{extra_context_key: extra_context},
    )

    # 배치 응답을 위한 래퍼 모델
    from pydantic import BaseModel

    class QuestionBatch(BaseModel):
        questions: list[InterviewQuestion]

    try:
        result = await client.create(
            response_model=QuestionBatch,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Generate exactly 3 interview questions following the strategy above. Each question must have a unique question_id."},
            ],
            temperature=0.7,
        )
        # question_id와 strategy 보정
        for i, q in enumerate(result.questions):
            q.question_id = f"{strategy.value}_{i+1}_{uuid.uuid4().hex[:8]}"
            q.strategy = strategy
        return result.questions[:3]
    except Exception as e:
        logger.error("QuestionCrafter failed for strategy %s: %s", strategy.value, e)
        return []


# ─── 메인 노드 ─────────────────────────────────────────────────────

async def question_orchestrator_node(state: MetaState) -> dict[str, Any]:
    """면접 질문을 생성한다. (TopicSelector + 3전략 QuestionCrafter)"""
    job_id = state["job_id"]

    try:
        db_url = os.environ.get("DATABASE_URL", "")
        analysis_repo = AnalysisRepository()

        # 1. DB에서 분석 결과 로드
        profile_ref = state.get("profile_ref")
        profile_data = await analysis_repo.get_result(profile_ref) if profile_ref else None
        profile_result = profile_data.get("result_data", {}) if profile_data else {}

        forensic_ref = state.get("forensic_result_ref")
        forensic_data = await analysis_repo.get_result(forensic_ref) if forensic_ref else None
        forensic_result = forensic_data.get("result_data", {}) if forensic_data else {}

        logic_ref = state.get("logic_result_ref")
        logic_data = await analysis_repo.get_result(logic_ref) if logic_ref else None
        logic_result = logic_data.get("result_data", {}) if logic_data else {}

        stack_ref = state.get("stack_result_ref")
        stack_data = await analysis_repo.get_result(stack_ref) if stack_ref else None
        stack_result = stack_data.get("result_data", {}) if stack_data else {}

        # 2. JD 요구사항 로드
        from infrastructure.persistence.repository import JobRepository

        job_repo = JobRepository()
        job = await job_repo.get(job_id)
        input_data = job.get("input_data", {}) if job else {}
        jd_tech_stack = input_data.get("jd_tech_stack", [])

        # 3. TopicSelector — pgvector로 관련 코드 청크 검색
        embedding_api_key = os.environ.get("EMBEDDING_API_KEY", os.environ.get("LLM_API_KEY", ""))
        embedding_base_url = os.environ.get("EMBEDDING_BASE_URL", "https://api.openai.com/v1")

        embedding_service = EmbeddingService(
            api_key=embedding_api_key,
            base_url=embedding_base_url,
        )
        vector_store = PgvectorStore()

        relevant_chunks = await _select_topics(
            job_id, jd_tech_stack, embedding_service, vector_store
        )

        # 4. 컨텍스트 구성 (ContextBudget으로 토큰 예산 관리)
        budget = ContextBudget()

        scores = profile_result.get("scores", {})
        raw_profile = (
            f"Logic score: {scores.get('logic', {}).get('normalized_score', 'N/A')}\n"
            f"Mastery score: {scores.get('mastery', {}).get('normalized_score', 'N/A')}\n"
            f"Authenticity score: {scores.get('authenticity', {}).get('normalized_score', 'N/A')}\n"
            f"Stability score: {scores.get('stability', {}).get('normalized_score', 'N/A')}\n"
            f"Skills detected: {stack_result.get('stack_summary', {}).get('total_skills_detected', 0)}\n"
            f"Architecture score: {stack_result.get('stack_summary', {}).get('architecture_score', 'N/A')}\n"
        )
        profile_context = budget.allocate("candidate_profile", raw_profile)

        raw_code = ""
        for chunk in relevant_chunks[:10]:
            raw_code += f"[similarity={chunk['similarity']:.2f}] {chunk['content']}\n---\n"
        if not raw_code:
            raw_code = f"Forensic summary: {str(forensic_result.get('forensic_summary', {}))}\n"
        code_context = budget.allocate("code_chunks", raw_code)

        raw_complexity = (
            f"Logic summary: {str(logic_result.get('logic_summary', {}))}\n"
            f"Avg cyclomatic complexity: {logic_result.get('avg_cyclomatic_complexity', 'N/A')}\n"
            f"Avg maintainability index: {logic_result.get('avg_maintainability_index', 'N/A')}\n"
        )
        complexity_context = budget.allocate("topic_context", raw_complexity)

        evolution_context = (
            f"Total files analyzed: {forensic_result.get('total_files_analyzed', 0)}\n"
            f"Style consistency: {forensic_result.get('style_consistency', 'N/A')}\n"
            f"AI detection: {str(forensic_result.get('ai_detection', {}))}\n"
        )

        jd_context = budget.allocate("jd_context", f"Required tech stack: {jd_tech_stack}")
        logger.info("Context budget: %s", budget.summary())

        # 5. 3전략 병렬 실행
        llm_client = InstructorClient(
            api_key=os.environ.get("LLM_API_KEY", ""),
            base_url=os.environ.get("LLM_BASE_URL", "https://api.moonshot.cn/v1"),
        )

        strategy_tasks = [
            _craft_questions_for_strategy(
                strategy=QuestionStrategy.NEGATIVE_SELECTION,
                prompt_template=NEGATIVE_SELECTION_PROMPT,
                profile_context=profile_context,
                code_context=code_context,
                extra_context=jd_context,
                extra_context_key="jd_context",
                client=llm_client,
            ),
            _craft_questions_for_strategy(
                strategy=QuestionStrategy.INTENTIONAL_COMPLEXITY,
                prompt_template=INTENTIONAL_COMPLEXITY_PROMPT,
                profile_context=profile_context,
                code_context=code_context,
                extra_context=complexity_context,
                extra_context_key="complexity_context",
                client=llm_client,
            ),
            _craft_questions_for_strategy(
                strategy=QuestionStrategy.CODE_EVOLUTION,
                prompt_template=CODE_EVOLUTION_PROMPT,
                profile_context=profile_context,
                code_context=code_context,
                extra_context=evolution_context,
                extra_context_key="evolution_context",
                client=llm_client,
            ),
        ]

        results = await asyncio.gather(*strategy_tasks, return_exceptions=True)

        # 6. 질문 수집 + InterviewScript 조립
        all_questions: list[InterviewQuestion] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                strategy_name = list(QuestionStrategy)[i].value
                logger.error("Strategy %s failed: %s", strategy_name, result)
                continue
            all_questions.extend(result)

        if not all_questions:
            logger.error("question_orchestrator: No questions generated for job %s", job_id)
            error_ref = await analysis_repo.save_result(
                job_id,
                "question_orchestrator",
                "meta",
                {"error": "No questions generated", "status": "failed"},
            )
            return {
                "questions_ref": error_ref,
                "status": "questioning",
                "current_phase": "questions",
                "errors": state.get("errors", []) + ["question_orchestrator: No questions generated"],
            }

        script = InterviewScript(job_id=job_id, questions=all_questions)

        # 7. DB 저장
        result_id = await analysis_repo.save_result(
            job_id,
            "question_orchestrator",
            "meta",
            script.model_dump(),
        )

        logger.info(
            "question_orchestrator completed: %d questions (%s)",
            script.total_count,
            script.strategy_distribution,
        )

        return {
            "questions_ref": result_id,
            "status": "questioning",
            "current_phase": "questions",
        }
    except Exception as e:
        logger.error("question_orchestrator_node failed for job %s: %s", job_id, e)
        return {
            "questions_ref": None,
            "status": "questioning",
            "current_phase": "questions",
            "errors": state.get("errors", []) + [f"question_orchestrator: {e}"],
        }
