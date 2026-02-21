"""
MetaGraph E2E 통합 테스트 — 5개 시나리오 (JIT-278).

Mock LLM/DB/파이프라인 러너를 사용하여 외부 의존성 없이
전체 파이프라인의 End-to-End 흐름을 검증한다.

Phase 9: LangGraph → Temporal 전환. supervisor_adapters가 run_*_pipeline을
직접 호출하므로, 해당 함수를 mock한다.

Scenario 1: Happy Path (모든 데이터 소스 사용 가능)
Scenario 2: Partial Data (GitHub만 사용 가능)
Scenario 3: Quality Gate Rejection -> Revision
Scenario 4: Worker Failure (Graceful Degradation)
Scenario 5: Concurrent Jobs
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.e2e.conftest import (
    InMemoryStore,
    MockAnalysisRepository,
    MockEmbeddingService,
    MockIdentityRepository,
    MockInstructorClient,
    MockJobRepository,
    MockPgvectorStore,
    MockScoreRepository,
    make_forensic_result,
    make_full_input_data,
    make_github_only_input_data,
    make_logic_result,
    make_sample_questions,
    make_stack_result,
)

# ---------------------------------------------------------------------------
# Node imports
# ---------------------------------------------------------------------------
from application.nodes.meta.input_router import input_router_node
from application.nodes.meta.plan_generator import plan_generator_node
from application.nodes.meta.supervisor_adapters import (
    forensic_supervisor_node,
    logic_supervisor_node,
    stack_supervisor_node,
)
from application.nodes.meta.profile_synthesizer import profile_synthesizer_node
from application.nodes.meta.question_orchestrator import question_orchestrator_node
from application.nodes.meta.enhancement_agents import enhancement_agents_node
from application.nodes.meta.quality_gate import (
    quality_gate_node,
    should_revise,
    QualityReview,
)
from application.nodes.meta.output_assembler import output_assembler_node


# ===========================================================================
# Helper: Pipeline Runner
# ===========================================================================


class PipelineRunner:
    """MetaGraph 노드를 순차 호출하며 상태를 누적하는 E2E 테스트 러너."""

    def __init__(self, store: InMemoryStore) -> None:
        self.store = store
        self.state: dict[str, Any] = {}

    def init_state(self, job_id: str) -> None:
        """MetaState 초기 상태를 설정한다."""
        self.state = {
            "job_id": job_id,
            "input_data_ref": "",
            "identity_cluster_ref": None,
            "repo_paths_ref": None,
            "forensic_result_ref": None,
            "logic_result_ref": None,
            "stack_result_ref": None,
            "profile_ref": None,
            "candidate_scores": None,
            "questions_ref": None,
            "status": "pending",
            "current_phase": "input_router",
            "revision_count": 0,
            "_quality_verdict": "",
            "errors": [],
        }

    async def run_node(self, node_fn: Any) -> dict[str, Any]:
        """노드를 실행하고 반환값으로 상태를 갱신한다."""
        result = await node_fn(self.state)
        if result:
            self.state.update(result)
        return result


def _make_repo_factory(store: InMemoryStore, repo_cls: type) -> Any:
    """Repository 생성자를 MockRepository로 교체하는 팩토리."""
    def factory(conninfo: str = "") -> Any:
        return repo_cls(store=store)
    return factory


def _build_patches(store: InMemoryStore, llm_responses: dict[str, Any] | None = None) -> dict:
    """모든 노드에 필요한 patch 대상을 구성한다."""
    job_factory = _make_repo_factory(store, MockJobRepository)
    analysis_factory = _make_repo_factory(store, MockAnalysisRepository)
    identity_factory = _make_repo_factory(store, MockIdentityRepository)
    score_factory = _make_repo_factory(store, MockScoreRepository)

    def mock_instructor_factory(**kwargs: Any) -> MockInstructorClient:
        return MockInstructorClient(responses=llm_responses or {})

    def mock_embedding_factory(**kwargs: Any) -> MockEmbeddingService:
        return MockEmbeddingService()

    def mock_pgvector_factory(**kwargs: Any) -> MockPgvectorStore:
        return MockPgvectorStore()

    return {
        # input_router
        "application.nodes.meta.input_router.JobRepository": job_factory,
        # plan_generator
        "application.nodes.meta.plan_generator.JobRepository": job_factory,
        # supervisor_adapters
        "application.nodes.meta.supervisor_adapters.JobRepository": job_factory,
        "application.nodes.meta.supervisor_adapters.AnalysisRepository": analysis_factory,
        "application.nodes.meta.supervisor_adapters.IdentityRepository": identity_factory,
        # profile_synthesizer
        "application.nodes.meta.profile_synthesizer.AnalysisRepository": analysis_factory,
        "application.nodes.meta.profile_synthesizer.JobRepository": job_factory,
        "application.nodes.meta.profile_synthesizer.ScoreRepository": score_factory,
        # question_orchestrator
        "application.nodes.meta.question_orchestrator.AnalysisRepository": analysis_factory,
        "application.nodes.meta.question_orchestrator.InstructorClient": mock_instructor_factory,
        "application.nodes.meta.question_orchestrator.EmbeddingService": mock_embedding_factory,
        "application.nodes.meta.question_orchestrator.PgvectorStore": mock_pgvector_factory,
        "infrastructure.persistence.repository.JobRepository": job_factory,
        # enhancement_agents
        "application.nodes.meta.enhancement_agents.AnalysisRepository": analysis_factory,
        "application.nodes.meta.enhancement_agents.InstructorClient": mock_instructor_factory,
        # quality_gate
        "application.nodes.meta.quality_gate.AnalysisRepository": analysis_factory,
        "application.nodes.meta.quality_gate.InstructorClient": mock_instructor_factory,
        # output_assembler
        "application.nodes.meta.output_assembler.AnalysisRepository": analysis_factory,
        "application.nodes.meta.output_assembler.JobRepository": job_factory,
    }


# ===========================================================================
# Helper: Mock InterviewQuestion (question_orchestrator용 Pydantic 모델)
# ===========================================================================


def _make_question_batch_response(questions: list[dict[str, Any]]) -> Any:
    """question_orchestrator가 기대하는 QuestionBatch 응답을 생성한다."""
    from domain.question.models import InterviewQuestion, QuestionCategory, QuestionStrategy

    pydantic_questions = []
    for q in questions:
        pydantic_questions.append(InterviewQuestion(
            question_id=q["question_id"],
            category=QuestionCategory(q["category"]),
            strategy=QuestionStrategy(q["strategy"]),
            difficulty=q["difficulty"],
            question_text=q["question_text"],
            intent=q["intent"],
            code_reference=q.get("code_reference"),
            expected_answer_guide=q["expected_answer_guide"],
            red_flags=q["red_flags"],
            follow_up_triggers=q["follow_up_triggers"],
            terminology=q["terminology"],
        ))

    from pydantic import BaseModel

    class QuestionBatch(BaseModel):
        questions: list[InterviewQuestion]

    return QuestionBatch(questions=pydantic_questions)


def _make_enhancement_batch_response() -> Any:
    """enhancement_agents가 기대하는 EnhancementBatch 응답을 생성한다."""
    from application.nodes.meta.enhancement_agents import EnhancementBatch

    return EnhancementBatch(items=[])


# ===========================================================================
# Scenario 1: Happy Path — 모든 데이터 소스 사용 가능
# ===========================================================================


class TestHappyPath:
    """
    입력: GitHub 3 repos + LinkedIn + Resume + JD
    예상: 4대 지표 산출 + 질문 생성 + 신뢰도 "low" (calculate_weighted_score 기본값)
    검증: candidate_scores 존재, 주요 노드 결과 ref 존재, status = completed
    """

    @pytest.mark.asyncio
    async def test_full_pipeline_happy_path(self) -> None:
        store = InMemoryStore()
        runner = PipelineRunner(store)

        # --- Job 사전 등록 ---
        job_id = str(uuid.uuid4())
        input_data = make_full_input_data()
        store.jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "progress": 0.0,
            "input_data": input_data,
            "result_data": None,
            "error_message": None,
        }
        runner.init_state(job_id)

        # --- 파이프라인 러너 Mock 결과 ---
        forensic_result = make_forensic_result(authenticity_score=0.85, total_files=42)
        logic_result = make_logic_result(logic_score=72.0, files_analyzed=38)
        stack_result = make_stack_result(mastery_score=78.0, total_skills=15)

        # --- LLM Mock 응답 ---
        sample_questions = make_sample_questions(9)
        question_batch = _make_question_batch_response(sample_questions[:3])
        enhancement_batch = _make_enhancement_batch_response()
        quality_review_approve = QualityReview(
            overall_quality=0.85,
            issues=[],
            suggestions=[],
            verdict="approve",
        )

        llm_responses = {
            "QuestionBatch": question_batch,
            "EnhancementBatch": enhancement_batch,
            "QualityReview": quality_review_approve,
        }

        # --- Build patches ---
        patches = _build_patches(store, llm_responses)

        # Phase 9: run_*_pipeline mock (LangGraph graph builder 대체)
        patches["application.nodes.meta.supervisor_adapters.run_forensic_pipeline"] = (
            AsyncMock(return_value=forensic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_logic_pipeline"] = (
            AsyncMock(return_value=logic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_stack_pipeline"] = (
            AsyncMock(return_value=stack_result)
        )

        # --- 파이프라인 실행 ---
        with _apply_patches(patches):
            # Phase 0: InputRouter
            result = await runner.run_node(input_router_node)
            assert result["status"] == "collecting"
            assert result["input_data_ref"] == job_id

            # Phase 1: PlanGenerator
            result = await runner.run_node(plan_generator_node)
            assert result["status"] == "analyzing"

            # Phase 2: Forensic → Logic → Stack
            result = await runner.run_node(forensic_supervisor_node)
            assert result.get("forensic_result_ref") is not None
            assert result.get("identity_cluster_ref") is not None

            result = await runner.run_node(logic_supervisor_node)
            assert result.get("logic_result_ref") is not None

            result = await runner.run_node(stack_supervisor_node)
            assert result.get("stack_result_ref") is not None

            # Phase 2.5: ProfileSynthesizer
            result = await runner.run_node(profile_synthesizer_node)
            assert result.get("profile_ref") is not None
            assert result.get("candidate_scores") is not None
            scores = result["candidate_scores"]
            assert "logic" in scores
            assert "mastery" in scores
            assert "stability" in scores
            assert "authenticity" in scores
            assert "weighted_total" in scores

            # Phase 3: QuestionOrchestrator
            result = await runner.run_node(question_orchestrator_node)
            assert result.get("questions_ref") is not None
            assert result["status"] == "questioning"

            # Phase 3.5: EnhancementAgents
            result = await runner.run_node(enhancement_agents_node)
            assert result.get("questions_ref") is not None

            # Phase 4: QualityGate
            result = await runner.run_node(quality_gate_node)
            assert result["_quality_verdict"] == "approve"
            assert result["revision_count"] == 0

            route = should_revise(runner.state)
            assert route == "approve"

            # Phase 5: OutputAssembler
            result = await runner.run_node(output_assembler_node)
            assert result["status"] == "completed"
            assert result["current_phase"] == "output"

        # --- 최종 상태 검증 ---
        assert runner.state["status"] == "completed"
        assert runner.state["candidate_scores"] is not None
        assert runner.state["forensic_result_ref"] is not None
        assert runner.state["logic_result_ref"] is not None
        assert runner.state["stack_result_ref"] is not None
        assert runner.state["profile_ref"] is not None
        assert runner.state["questions_ref"] is not None
        assert runner.state["errors"] == []

        # DB에 최종 결과 저장 확인
        job_data = store.jobs.get(job_id)
        assert job_data is not None
        assert job_data["status"] == "completed"
        assert job_data["progress"] == 1.0
        assert job_data["result_data"] is not None
        assert job_data["result_data"]["version"] == "5.0"
        assert "intel_brief" in job_data["result_data"]
        assert "deep_analysis" in job_data["result_data"]
        assert "interview_script" in job_data["result_data"]
        assert "decision_support" in job_data["result_data"]


# ===========================================================================
# Scenario 2: Partial Data — GitHub만 사용 가능
# ===========================================================================


class TestPartialData:
    """
    입력: GitHub 1 repo + JD (LinkedIn/Resume 없음)
    예상: 4대 지표 산출 (낮은 점수) + confidence = "low"
    검증: confidence = "low", 에러 없이 완료
    """

    @pytest.mark.asyncio
    async def test_github_only_pipeline(self) -> None:
        store = InMemoryStore()
        runner = PipelineRunner(store)

        # --- Job 사전 등록 (GitHub만) ---
        job_id = str(uuid.uuid4())
        input_data = make_github_only_input_data()
        store.jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "progress": 0.0,
            "input_data": input_data,
            "result_data": None,
            "error_message": None,
        }
        runner.init_state(job_id)

        # --- 낮은 점수의 파이프라인 결과 ---
        forensic_result = make_forensic_result(
            authenticity_score=0.55,
            total_files=8,
            ai_suspicion=0.25,
            style_consistency=0.60,
        )
        logic_result = make_logic_result(
            logic_score=45.0,
            avg_complexity=8.5,
            avg_maintainability=42.0,
            files_analyzed=8,
        )
        stack_result = make_stack_result(
            mastery_score=38.0,
            total_skills=4,
            avg_api_depth=1.5,
            architecture_score=35.0,
        )

        # --- LLM Mock ---
        sample_questions = make_sample_questions(6)
        question_batch = _make_question_batch_response(sample_questions[:3])
        enhancement_batch = _make_enhancement_batch_response()
        quality_review = QualityReview(
            overall_quality=0.72,
            issues=[],
            suggestions=["Could use more code references"],
            verdict="approve",
        )

        llm_responses = {
            "QuestionBatch": question_batch,
            "EnhancementBatch": enhancement_batch,
            "QualityReview": quality_review,
        }

        patches = _build_patches(store, llm_responses)
        patches["application.nodes.meta.supervisor_adapters.run_forensic_pipeline"] = (
            AsyncMock(return_value=forensic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_logic_pipeline"] = (
            AsyncMock(return_value=logic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_stack_pipeline"] = (
            AsyncMock(return_value=stack_result)
        )

        # --- 파이프라인 실행 ---
        with _apply_patches(patches):
            await runner.run_node(input_router_node)
            await runner.run_node(plan_generator_node)
            await runner.run_node(forensic_supervisor_node)
            await runner.run_node(logic_supervisor_node)
            await runner.run_node(stack_supervisor_node)
            await runner.run_node(profile_synthesizer_node)
            await runner.run_node(question_orchestrator_node)
            await runner.run_node(enhancement_agents_node)
            await runner.run_node(quality_gate_node)

            route = should_revise(runner.state)
            assert route == "approve"

            await runner.run_node(output_assembler_node)

        # --- 검증: 완료되었지만 점수가 낮음 ---
        assert runner.state["status"] == "completed"
        assert runner.state["errors"] == []

        scores = runner.state["candidate_scores"]
        assert scores is not None
        assert scores["confidence"] == "low"
        assert scores["weighted_total"] < 60

        job_data = store.jobs.get(job_id)
        assert job_data is not None
        assert job_data["status"] == "completed"
        assert job_data["result_data"]["decision_support"]["recommendation"] in (
            "no_hire",
            "conditional_hire",
        )


# ===========================================================================
# Scenario 3: Quality Gate Rejection -> Revision
# ===========================================================================


class TestQualityGateRejection:
    """
    입력: 정상 데이터 + 의도적으로 낮은 품질 질문
    예상: QualityGate 1회 거부 -> revision -> 재검증 시 통과
    검증: revision_count >= 1
    """

    @pytest.mark.asyncio
    async def test_quality_gate_revise_then_approve(self) -> None:
        store = InMemoryStore()
        runner = PipelineRunner(store)

        job_id = str(uuid.uuid4())
        input_data = make_full_input_data()
        store.jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "progress": 0.0,
            "input_data": input_data,
            "result_data": None,
            "error_message": None,
        }
        runner.init_state(job_id)

        forensic_result = make_forensic_result()
        logic_result = make_logic_result()
        stack_result = make_stack_result()

        sample_questions = make_sample_questions(9)
        question_batch = _make_question_batch_response(sample_questions[:3])
        enhancement_batch = _make_enhancement_batch_response()

        call_count = {"n": 0}

        def quality_review_factory(_call_num: int) -> QualityReview:
            call_count["n"] += 1
            if call_count["n"] <= 1:
                return QualityReview(
                    overall_quality=0.35,
                    issues=["Questions are too generic", "No code references"],
                    suggestions=["Add specific file references"],
                    verdict="revise",
                )
            return QualityReview(
                overall_quality=0.82,
                issues=[],
                suggestions=[],
                verdict="approve",
            )

        llm_responses = {
            "QuestionBatch": question_batch,
            "EnhancementBatch": enhancement_batch,
            "QualityReview": quality_review_factory,
        }

        patches = _build_patches(store, llm_responses)
        patches["application.nodes.meta.supervisor_adapters.run_forensic_pipeline"] = (
            AsyncMock(return_value=forensic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_logic_pipeline"] = (
            AsyncMock(return_value=logic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_stack_pipeline"] = (
            AsyncMock(return_value=stack_result)
        )

        with _apply_patches(patches):
            await runner.run_node(input_router_node)
            await runner.run_node(plan_generator_node)
            await runner.run_node(forensic_supervisor_node)
            await runner.run_node(logic_supervisor_node)
            await runner.run_node(stack_supervisor_node)
            await runner.run_node(profile_synthesizer_node)
            await runner.run_node(question_orchestrator_node)
            await runner.run_node(enhancement_agents_node)

            # QualityGate — 첫 번째 호출 (revise)
            result = await runner.run_node(quality_gate_node)
            assert result["_quality_verdict"] == "revise"
            assert result["revision_count"] == 1

            route = should_revise(runner.state)
            assert route == "revise"

            # QualityGate 루프: 두 번째 호출 (approve)
            result = await runner.run_node(quality_gate_node)
            assert result["_quality_verdict"] == "approve"

            route = should_revise(runner.state)
            assert route == "approve"

            await runner.run_node(output_assembler_node)

        assert runner.state["status"] == "completed"
        assert runner.state["revision_count"] >= 1
        assert runner.state["errors"] == []

    @pytest.mark.asyncio
    async def test_quality_gate_max_revisions_force_approve(self) -> None:
        """MAX_REVISIONS 도달 시 강제 승인 검증."""
        store = InMemoryStore()
        runner = PipelineRunner(store)

        job_id = str(uuid.uuid4())
        input_data = make_full_input_data()
        store.jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "progress": 0.0,
            "input_data": input_data,
            "result_data": None,
            "error_message": None,
        }
        runner.init_state(job_id)

        forensic_result = make_forensic_result()
        logic_result = make_logic_result()
        stack_result = make_stack_result()

        sample_questions = make_sample_questions(9)
        question_batch = _make_question_batch_response(sample_questions[:3])
        enhancement_batch = _make_enhancement_batch_response()

        always_revise = QualityReview(
            overall_quality=0.2,
            issues=["Always bad"],
            suggestions=["Rewrite everything"],
            verdict="revise",
        )

        llm_responses = {
            "QuestionBatch": question_batch,
            "EnhancementBatch": enhancement_batch,
            "QualityReview": always_revise,
        }

        patches = _build_patches(store, llm_responses)
        patches["application.nodes.meta.supervisor_adapters.run_forensic_pipeline"] = (
            AsyncMock(return_value=forensic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_logic_pipeline"] = (
            AsyncMock(return_value=logic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_stack_pipeline"] = (
            AsyncMock(return_value=stack_result)
        )

        with _apply_patches(patches):
            await runner.run_node(input_router_node)
            await runner.run_node(plan_generator_node)
            await runner.run_node(forensic_supervisor_node)
            await runner.run_node(logic_supervisor_node)
            await runner.run_node(stack_supervisor_node)
            await runner.run_node(profile_synthesizer_node)
            await runner.run_node(question_orchestrator_node)
            await runner.run_node(enhancement_agents_node)

            # 1회차 revise
            result = await runner.run_node(quality_gate_node)
            assert result["_quality_verdict"] == "revise"
            assert result["revision_count"] == 1

            # 2회차 revise
            result = await runner.run_node(quality_gate_node)
            assert result["_quality_verdict"] == "revise"
            assert result["revision_count"] == 2

            # 3회차: 강제 approve
            result = await runner.run_node(quality_gate_node)
            assert result["_quality_verdict"] == "approve"

            route = should_revise(runner.state)
            assert route == "approve"

            await runner.run_node(output_assembler_node)

        assert runner.state["status"] == "completed"
        assert runner.state["revision_count"] >= 2


# ===========================================================================
# Scenario 4: Worker Failure (Graceful Degradation)
# ===========================================================================


class TestWorkerFailure:
    """
    입력: 정상 데이터 + 1개 Worker(LogicSupervisor) 실패 주입
    예상: 해당 Worker 결과 없이 나머지 정상 완료
    검증: errors 리스트에 실패 기록, status = "completed"
    """

    @pytest.mark.asyncio
    async def test_logic_supervisor_failure_graceful_degradation(self) -> None:
        store = InMemoryStore()
        runner = PipelineRunner(store)

        job_id = str(uuid.uuid4())
        input_data = make_full_input_data()
        store.jobs[job_id] = {
            "id": job_id,
            "status": "pending",
            "progress": 0.0,
            "input_data": input_data,
            "result_data": None,
            "error_message": None,
        }
        runner.init_state(job_id)

        forensic_result = make_forensic_result()
        stack_result = make_stack_result()

        sample_questions = make_sample_questions(9)
        question_batch = _make_question_batch_response(sample_questions[:3])
        enhancement_batch = _make_enhancement_batch_response()
        quality_review = QualityReview(
            overall_quality=0.75,
            issues=[],
            suggestions=[],
            verdict="approve",
        )

        llm_responses = {
            "QuestionBatch": question_batch,
            "EnhancementBatch": enhancement_batch,
            "QualityReview": quality_review,
        }

        patches = _build_patches(store, llm_responses)
        patches["application.nodes.meta.supervisor_adapters.run_forensic_pipeline"] = (
            AsyncMock(return_value=forensic_result)
        )
        # Logic pipeline 실패
        patches["application.nodes.meta.supervisor_adapters.run_logic_pipeline"] = (
            AsyncMock(side_effect=RuntimeError("AST parser crash: out of memory"))
        )
        patches["application.nodes.meta.supervisor_adapters.run_stack_pipeline"] = (
            AsyncMock(return_value=stack_result)
        )

        with _apply_patches(patches):
            await runner.run_node(input_router_node)
            await runner.run_node(plan_generator_node)
            await runner.run_node(forensic_supervisor_node)

            # Logic supervisor 실패 — 에러를 포착하고 계속 진행
            result = await runner.run_node(logic_supervisor_node)
            assert result.get("logic_result_ref") is not None
            assert any("logic supervisor" in e for e in result.get("errors", []))

            await runner.run_node(stack_supervisor_node)
            await runner.run_node(profile_synthesizer_node)
            assert runner.state["candidate_scores"] is not None

            await runner.run_node(question_orchestrator_node)
            await runner.run_node(enhancement_agents_node)
            await runner.run_node(quality_gate_node)

            route = should_revise(runner.state)
            assert route == "approve"

            await runner.run_node(output_assembler_node)

        assert runner.state["status"] == "completed"
        assert len(runner.state["errors"]) > 0
        assert any("logic supervisor" in e for e in runner.state["errors"])

        job_data = store.jobs.get(job_id)
        assert job_data is not None
        assert job_data["status"] == "completed"
        assert len(job_data["result_data"]["errors"]) > 0


# ===========================================================================
# Scenario 5: Concurrent Jobs
# ===========================================================================


class TestConcurrentJobs:
    """
    입력: 2개 job 동시 실행
    예상: 서로 간섭 없이 각각 완료
    검증: 각 job의 결과가 독립적
    """

    @pytest.mark.asyncio
    async def test_two_jobs_interleaved_execution(self) -> None:
        store = InMemoryStore()

        # --- Job A: 높은 점수 ---
        job_a_id = str(uuid.uuid4())
        input_a = make_full_input_data()
        store.jobs[job_a_id] = {
            "id": job_a_id,
            "status": "pending",
            "progress": 0.0,
            "input_data": input_a,
            "result_data": None,
            "error_message": None,
        }

        # --- Job B: 낮은 점수 ---
        job_b_id = str(uuid.uuid4())
        input_b = make_github_only_input_data()
        store.jobs[job_b_id] = {
            "id": job_b_id,
            "status": "pending",
            "progress": 0.0,
            "input_data": input_b,
            "result_data": None,
            "error_message": None,
        }

        runner_a = PipelineRunner(store)
        runner_a.init_state(job_a_id)
        runner_b = PipelineRunner(store)
        runner_b.init_state(job_b_id)

        forensic_a = make_forensic_result(authenticity_score=0.92, total_files=50)
        logic_a = make_logic_result(logic_score=85.0)
        stack_a = make_stack_result(mastery_score=88.0)

        forensic_b = make_forensic_result(authenticity_score=0.45, total_files=5)
        logic_b = make_logic_result(logic_score=35.0)
        stack_b = make_stack_result(mastery_score=30.0)

        sample_questions = make_sample_questions(9)
        question_batch = _make_question_batch_response(sample_questions[:3])
        enhancement_batch = _make_enhancement_batch_response()
        quality_review = QualityReview(
            overall_quality=0.85,
            issues=[],
            suggestions=[],
            verdict="approve",
        )

        llm_responses = {
            "QuestionBatch": question_batch,
            "EnhancementBatch": enhancement_batch,
            "QualityReview": quality_review,
        }

        patches = _build_patches(store, llm_responses)

        # 파이프라인 러너를 side_effect로 순서별 결과 반환
        forensic_results_queue = [forensic_a, forensic_b]
        logic_results_queue = [logic_a, logic_b]
        stack_results_queue = [stack_a, stack_b]

        forensic_call_idx = {"n": 0}
        logic_call_idx = {"n": 0}
        stack_call_idx = {"n": 0}

        async def mock_forensic_pipeline(initial_state: dict) -> dict:
            idx = forensic_call_idx["n"]
            forensic_call_idx["n"] += 1
            return forensic_results_queue[idx] if idx < len(forensic_results_queue) else forensic_a

        async def mock_logic_pipeline(initial_state: dict) -> dict:
            idx = logic_call_idx["n"]
            logic_call_idx["n"] += 1
            return logic_results_queue[idx] if idx < len(logic_results_queue) else logic_a

        async def mock_stack_pipeline(initial_state: dict) -> dict:
            idx = stack_call_idx["n"]
            stack_call_idx["n"] += 1
            return stack_results_queue[idx] if idx < len(stack_results_queue) else stack_a

        patches["application.nodes.meta.supervisor_adapters.run_forensic_pipeline"] = mock_forensic_pipeline
        patches["application.nodes.meta.supervisor_adapters.run_logic_pipeline"] = mock_logic_pipeline
        patches["application.nodes.meta.supervisor_adapters.run_stack_pipeline"] = mock_stack_pipeline

        with _apply_patches(patches):
            # --- 인터리브 실행: A와 B를 번갈아 호출 ---
            await runner_a.run_node(input_router_node)
            await runner_b.run_node(input_router_node)
            await runner_a.run_node(plan_generator_node)
            await runner_b.run_node(plan_generator_node)

            await runner_a.run_node(forensic_supervisor_node)
            await runner_b.run_node(forensic_supervisor_node)
            await runner_a.run_node(logic_supervisor_node)
            await runner_b.run_node(logic_supervisor_node)
            await runner_a.run_node(stack_supervisor_node)
            await runner_b.run_node(stack_supervisor_node)

            await runner_a.run_node(profile_synthesizer_node)
            await runner_b.run_node(profile_synthesizer_node)

            await runner_a.run_node(question_orchestrator_node)
            await runner_b.run_node(question_orchestrator_node)
            await runner_a.run_node(enhancement_agents_node)
            await runner_b.run_node(enhancement_agents_node)

            await runner_a.run_node(quality_gate_node)
            await runner_b.run_node(quality_gate_node)

            await runner_a.run_node(output_assembler_node)
            await runner_b.run_node(output_assembler_node)

        # --- 각 job이 독립적으로 완료 ---
        assert runner_a.state["status"] == "completed"
        assert runner_b.state["status"] == "completed"

        assert runner_a.state["job_id"] == job_a_id
        assert runner_b.state["job_id"] == job_b_id

        scores_a = runner_a.state["candidate_scores"]
        scores_b = runner_b.state["candidate_scores"]

        assert scores_a is not None
        assert scores_b is not None

        # Job A는 높은 점수, Job B는 낮은 점수
        assert scores_a["weighted_total"] > scores_b["weighted_total"]
        assert scores_a["logic"]["normalized_score"] > scores_b["logic"]["normalized_score"]
        assert scores_a["mastery"]["normalized_score"] > scores_b["mastery"]["normalized_score"]

        # DB 저장이 독립적
        job_data_a = store.jobs.get(job_a_id)
        job_data_b = store.jobs.get(job_b_id)

        assert job_data_a is not None
        assert job_data_b is not None
        assert job_data_a["status"] == "completed"
        assert job_data_b["status"] == "completed"
        assert job_data_a["result_data"]["job_id"] == job_a_id
        assert job_data_b["result_data"]["job_id"] == job_b_id

        assert runner_a.state["errors"] == []
        assert runner_b.state["errors"] == []

        # Ref가 서로 다름
        assert runner_a.state["forensic_result_ref"] != runner_b.state["forensic_result_ref"]
        assert runner_a.state["logic_result_ref"] != runner_b.state["logic_result_ref"]
        assert runner_a.state["stack_result_ref"] != runner_b.state["stack_result_ref"]
        assert runner_a.state["profile_ref"] != runner_b.state["profile_ref"]
        assert runner_a.state["questions_ref"] != runner_b.state["questions_ref"]


# ===========================================================================
# Helper: Patch Context Manager
# ===========================================================================


class _apply_patches:
    """여러 patch를 한 번에 적용하는 컨텍스트 매니저."""

    def __init__(self, patches: dict[str, Any]) -> None:
        self._patches = patches
        self._patchers: list[Any] = []

    def __enter__(self) -> None:
        for target, replacement in self._patches.items():
            patcher = patch(target, replacement)
            patcher.start()
            self._patchers.append(patcher)

    def __exit__(self, *args: Any) -> None:
        for patcher in self._patchers:
            patcher.stop()
