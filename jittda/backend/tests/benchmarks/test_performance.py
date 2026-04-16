"""
성능 벤치마크 테스트 — 파이프라인 성능 기준선 수립 (JIT-280).

Mock 환경에서의 성능 기준선을 측정하여 회귀 감지 기반을 만든다.
절대 수치보다 상대적 비교와 기준선 수립이 목적이다.

Categories:
  a) Domain 순수 함수 성능 (calculate_weighted_score, build_dynamic_mailmap, stage1_hard_filter)
  b) 노드 개별 실행 시간 (input_router, output_assembler, quality_gate)
  c) 전체 파이프라인 Mock 실행 시간
  d) 동시 실행 테스트 (3개 job asyncio.gather)
  e) 메모리/크기 추정 (MetaState dict, checkpoint 등가 크기)
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.benchmarks.conftest import (
    BenchmarkReport,
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
    make_logic_result,
    make_mock_graph,
    make_sample_questions,
    make_stack_result,
    measure_time,
)

# Domain imports
from domain.scoring.calculator import calculate_weighted_score
from domain.scoring.models import MetricScore, MetricType
from domain.identity.mailmap_builder import build_dynamic_mailmap
from domain.identity.models import GitAuthor, GitHubProfile
from domain.matching.funnel_rules import stage1_hard_filter
from domain.matching.models import FunnelConfig, RepoMetadata

# Node imports
from application.nodes.meta.input_router import input_router_node
from application.nodes.meta.output_assembler import output_assembler_node
from application.nodes.meta.quality_gate import quality_gate_node, QualityReview

# E2E Pipeline Runner 재사용
from tests.e2e.test_pipeline_scenarios import (
    PipelineRunner,
    _apply_patches,
    _build_patches,
    _make_enhancement_batch_response,
    _make_question_batch_response,
)

pytestmark = pytest.mark.benchmark


# ===========================================================================
# Helper: 테스트 데이터 생성
# ===========================================================================


def _make_metric_scores() -> dict[MetricType, MetricScore]:
    """벤치마크용 4대 지표 MetricScore 세트."""
    return {
        MetricType.LOGIC: MetricScore(
            metric_type=MetricType.LOGIC,
            raw_score=72.0,
            normalized_score=72.0,
            sub_scores={"complexity": 65.0, "maintainability": 78.0},
            evidence_count=38,
        ),
        MetricType.MASTERY: MetricScore(
            metric_type=MetricType.MASTERY,
            raw_score=78.0,
            normalized_score=78.0,
            sub_scores={"api_depth": 75.0, "architecture": 80.0},
            evidence_count=15,
        ),
        MetricType.STABILITY: MetricScore(
            metric_type=MetricType.STABILITY,
            raw_score=65.0,
            normalized_score=65.0,
            sub_scores={"test_coverage": 60.0, "error_handling": 70.0},
            evidence_count=20,
        ),
        MetricType.AUTHENTICITY: MetricScore(
            metric_type=MetricType.AUTHENTICITY,
            raw_score=85.0,
            normalized_score=85.0,
            sub_scores={"ai_suspicion": 8.0, "style_consistency": 92.0},
            evidence_count=42,
        ),
    }


def _make_git_authors(count: int) -> list[GitAuthor]:
    """벤치마크용 Git 저자 목록."""
    authors = []
    for i in range(count):
        # 다양한 패턴 혼합
        if i % 4 == 0:
            # noreply 패턴
            authors.append(GitAuthor(
                name=f"Author {i}",
                email=f"{i}+author{i}@users.noreply.github.com",
            ))
        elif i % 4 == 1:
            # 정확 매칭
            authors.append(GitAuthor(
                name="Candidate Name",
                email="candidate@example.com",
            ))
        elif i % 4 == 2:
            # 유사 이름
            authors.append(GitAuthor(
                name=f"Candidate Nam{i}",
                email=f"alias{i}@company.com",
            ))
        else:
            # 비매칭
            authors.append(GitAuthor(
                name=f"Other Person {i}",
                email=f"other{i}@random.org",
            ))
    return authors


def _make_github_profile() -> GitHubProfile:
    """벤치마크용 GitHub 프로필."""
    return GitHubProfile(
        name="Candidate Name",
        email="candidate@example.com",
        login="candidate",
        database_id="MDQ6VXNlcjEyMzQ1",
    )


def _make_repo_metadata_list(count: int) -> list[RepoMetadata]:
    """벤치마크용 RepoMetadata 목록."""
    repos = []
    for i in range(count):
        repos.append(RepoMetadata(
            name=f"repo-{i}",
            owner="candidate",
            url=f"https://github.com/candidate/repo-{i}",
            is_fork=(i % 5 == 0),  # 20%가 포크
            is_org_repo=(i % 7 == 0),  # ~14%가 조직 레포
            days_since_push=i * 10 % 500,  # 0~490일 분포
            languages=["Python", "JavaScript"] if i % 2 == 0 else ["Go", "Rust"],
            total_loc=i * 100 + 200,
            detected_tech_stack=["FastAPI", "PostgreSQL"] if i % 3 == 0 else ["Django"],
            user_contribution_ratio=0.5 + (i % 5) * 0.1,
        ))
    return repos


# ===========================================================================
# a) Domain 순수 함수 성능
# ===========================================================================


class TestDomainFunctionPerformance:
    """Domain 순수 함수의 실행 시간을 측정한다."""

    def test_calculate_weighted_score_1000x(self, report: BenchmarkReport) -> None:
        """calculate_weighted_score 1000회 반복 시간."""
        scores = _make_metric_scores()
        iterations = 1000

        start = time.perf_counter()
        for _ in range(iterations):
            result = calculate_weighted_score(scores)
        elapsed_ms = (time.perf_counter() - start) * 1000

        report.add("Domain: calculate_weighted_score", elapsed_ms, iterations)

        # 검증: 결과가 올바름
        assert result.weighted_total > 0
        assert result.weighted_total <= 100

        # 기준: 1회 평균 < 10ms
        avg_ms = elapsed_ms / iterations
        assert avg_ms < 10, f"calculate_weighted_score too slow: {avg_ms:.2f}ms avg"

        report.print_report()

    def test_build_dynamic_mailmap_100_authors(self, report: BenchmarkReport) -> None:
        """build_dynamic_mailmap 100명 저자 처리 시간."""
        authors = _make_git_authors(100)
        profile = _make_github_profile()
        node_id = "MDQ6VXNlcjEyMzQ1"

        start = time.perf_counter()
        result = build_dynamic_mailmap(authors, profile, node_id)
        elapsed_ms = (time.perf_counter() - start) * 1000

        report.add("Domain: build_dynamic_mailmap (100 authors)", elapsed_ms)

        # 검증: 매칭된 엔트리가 있음
        assert len(result) > 0

        # 기준: < 10ms
        assert elapsed_ms < 10, f"build_dynamic_mailmap too slow: {elapsed_ms:.2f}ms"

        report.print_report()

    def test_stage1_hard_filter_100_repos(self, report: BenchmarkReport) -> None:
        """stage1_hard_filter 100개 레포 필터링 시간."""
        repos = _make_repo_metadata_list(100)
        jd_languages = ["Python", "JavaScript"]
        config = FunnelConfig()

        start = time.perf_counter()
        result = stage1_hard_filter(repos, jd_languages, config)
        elapsed_ms = (time.perf_counter() - start) * 1000

        report.add("Domain: stage1_hard_filter (100 repos)", elapsed_ms)

        # 검증: 필터링 결과가 있음 (포크/오래된 것 일부 제거)
        assert 0 < len(result) < 100

        # 기준: < 10ms
        assert elapsed_ms < 10, f"stage1_hard_filter too slow: {elapsed_ms:.2f}ms"

        report.print_report()

    def test_domain_functions_combined(self, report: BenchmarkReport) -> None:
        """모든 Domain 함수를 한 번에 측정하여 종합 리포트를 출력한다."""
        # calculate_weighted_score
        scores = _make_metric_scores()
        with measure_time() as t1:
            for _ in range(1000):
                calculate_weighted_score(scores)
        report.add("Domain: calculate_weighted_score", t1["elapsed_ms"], 1000)

        # build_dynamic_mailmap
        authors = _make_git_authors(100)
        profile = _make_github_profile()
        with measure_time() as t2:
            build_dynamic_mailmap(authors, profile, "MDQ6VXNlcjEyMzQ1")
        report.add("Domain: build_dynamic_mailmap (100 authors)", t2["elapsed_ms"])

        # stage1_hard_filter
        repos = _make_repo_metadata_list(100)
        config = FunnelConfig()
        with measure_time() as t3:
            stage1_hard_filter(repos, ["Python", "JavaScript"], config)
        report.add("Domain: stage1_hard_filter (100 repos)", t3["elapsed_ms"])

        report.print_report()

        # 모든 Domain 함수가 기준 이내
        assert t1["elapsed_ms"] / 1000 < 10  # avg < 10ms
        assert t2["elapsed_ms"] < 10
        assert t3["elapsed_ms"] < 10


# ===========================================================================
# b) 노드 개별 실행 시간 (Mock)
# ===========================================================================


class TestNodeExecutionPerformance:
    """개별 노드의 Mock 환경 실행 시간을 측정한다."""

    @pytest.mark.asyncio
    async def test_input_router_node(self, report: BenchmarkReport) -> None:
        """input_router_node 실행 시간 (Mock DB)."""
        store = InMemoryStore()
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

        state = {
            "job_id": job_id,
            "input_data_ref": "",
            "status": "pending",
            "current_phase": "input_router",
            "errors": [],
        }

        def job_factory(conninfo: str = "") -> MockJobRepository:
            return MockJobRepository(store=store)

        with measure_time() as t:
            with patch("application.nodes.meta.input_router.JobRepository", job_factory):
                result = await input_router_node(state)

        report.add("Node: input_router_node", t["elapsed_ms"])

        assert result["status"] == "collecting"
        assert t["elapsed_ms"] < 100, f"input_router_node too slow: {t['elapsed_ms']:.2f}ms"

        report.print_report()

    @pytest.mark.asyncio
    async def test_output_assembler_node(self, report: BenchmarkReport) -> None:
        """output_assembler_node 실행 시간 (Mock DB)."""
        store = InMemoryStore()
        job_id = str(uuid.uuid4())
        store.jobs[job_id] = {
            "id": job_id,
            "status": "analyzing",
            "progress": 0.8,
            "input_data": make_full_input_data(),
            "result_data": None,
            "error_message": None,
        }

        # 분석 결과를 store에 미리 저장
        forensic_ref = str(uuid.uuid4())
        logic_ref = str(uuid.uuid4())
        stack_ref = str(uuid.uuid4())
        profile_ref = str(uuid.uuid4())
        questions_ref = str(uuid.uuid4())

        store.analysis_results[forensic_ref] = {
            "id": forensic_ref,
            "job_id": job_id,
            "worker_name": "forensic",
            "supervisor_name": "meta",
            "result_data": {
                "total_files_analyzed": 42,
                "ai_detection": {"avg_suspicion": 0.08, "flagged_files": 1},
                "style_consistency": 0.92,
                "plagiarism": {"plagiarism_detected": False},
            },
        }
        store.analysis_results[logic_ref] = {
            "id": logic_ref,
            "job_id": job_id,
            "worker_name": "logic",
            "supervisor_name": "meta",
            "result_data": {
                "files_analyzed": 38,
                "avg_cyclomatic_complexity": 4.2,
                "avg_maintainability_index": 68.5,
                "logic_summary": {"total_functions": 120},
            },
        }
        store.analysis_results[stack_ref] = {
            "id": stack_ref,
            "job_id": job_id,
            "worker_name": "stack",
            "supervisor_name": "meta",
            "result_data": {
                "total_skills_detected": 15,
                "avg_api_depth": 3.2,
                "architecture_score": 72.0,
                "stack_summary": {"top_skills": ["Python"]},
            },
        }
        store.analysis_results[profile_ref] = {
            "id": profile_ref,
            "job_id": job_id,
            "worker_name": "profile",
            "supervisor_name": "meta",
            "result_data": {"candidate_name": "Test Candidate"},
        }
        store.analysis_results[questions_ref] = {
            "id": questions_ref,
            "job_id": job_id,
            "worker_name": "questions",
            "supervisor_name": "meta",
            "result_data": {
                "questions": make_sample_questions(9),
                "strategy_distribution": {"negative_selection": 3},
                "category_distribution": {"technical_depth": 2},
                "enhancement_applied": True,
            },
        }

        candidate_scores = {
            "logic": {"normalized_score": 72.0},
            "mastery": {"normalized_score": 78.0},
            "stability": {"normalized_score": 65.0},
            "authenticity": {"normalized_score": 85.0},
            "weighted_total": 74.5,
            "confidence": "low",
        }

        state = {
            "job_id": job_id,
            "profile_ref": profile_ref,
            "questions_ref": questions_ref,
            "forensic_result_ref": forensic_ref,
            "logic_result_ref": logic_ref,
            "stack_result_ref": stack_ref,
            "candidate_scores": candidate_scores,
            "status": "assembling",
            "current_phase": "output_assembler",
            "errors": [],
        }

        def analysis_factory(conninfo: str = "") -> MockAnalysisRepository:
            return MockAnalysisRepository(store=store)

        def job_factory(conninfo: str = "") -> MockJobRepository:
            return MockJobRepository(store=store)

        with measure_time() as t:
            with patch("application.nodes.meta.output_assembler.AnalysisRepository", analysis_factory):
                with patch("application.nodes.meta.output_assembler.JobRepository", job_factory):
                    result = await output_assembler_node(state)

        report.add("Node: output_assembler_node", t["elapsed_ms"])

        assert result["status"] == "completed"
        assert t["elapsed_ms"] < 100, f"output_assembler_node too slow: {t['elapsed_ms']:.2f}ms"

        report.print_report()

    @pytest.mark.asyncio
    async def test_quality_gate_node(self, report: BenchmarkReport) -> None:
        """quality_gate_node 실행 시간 (Mock LLM)."""
        store = InMemoryStore()
        job_id = str(uuid.uuid4())

        # 질문 데이터 저장
        questions_ref = str(uuid.uuid4())
        store.analysis_results[questions_ref] = {
            "id": questions_ref,
            "job_id": job_id,
            "worker_name": "questions",
            "supervisor_name": "meta",
            "result_data": {"questions": make_sample_questions(9)},
        }

        state = {
            "job_id": job_id,
            "questions_ref": questions_ref,
            "revision_count": 0,
            "status": "reviewing",
            "current_phase": "quality_gate",
            "_quality_verdict": "",
            "errors": [],
        }

        quality_review = QualityReview(
            overall_quality=0.85,
            issues=[],
            suggestions=[],
            verdict="approve",
        )

        def analysis_factory(conninfo: str = "") -> MockAnalysisRepository:
            return MockAnalysisRepository(store=store)

        def mock_instructor_factory(**kwargs: Any) -> MockInstructorClient:
            return MockInstructorClient(responses={"QualityReview": quality_review})

        with measure_time() as t:
            with patch("application.nodes.meta.quality_gate.AnalysisRepository", analysis_factory):
                with patch("application.nodes.meta.quality_gate.InstructorClient", mock_instructor_factory):
                    result = await quality_gate_node(state)

        report.add("Node: quality_gate_node", t["elapsed_ms"])

        assert result["_quality_verdict"] == "approve"
        assert t["elapsed_ms"] < 100, f"quality_gate_node too slow: {t['elapsed_ms']:.2f}ms"

        report.print_report()


# ===========================================================================
# c) 전체 파이프라인 Mock 실행 시간
# ===========================================================================


class TestPipelinePerformance:
    """전체 파이프라인의 Mock 환경 실행 시간을 측정한다."""

    @pytest.mark.asyncio
    async def test_full_pipeline_mock_execution_time(self, report: BenchmarkReport) -> None:
        """E2E Happy Path 시나리오 전체 실행 시간 (Mock 환경)."""
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
        from application.nodes.meta.quality_gate import quality_gate_node, should_revise
        from application.nodes.meta.output_assembler import output_assembler_node

        store = InMemoryStore()
        runner = PipelineRunner(store)

        # Job 사전 등록
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

        # Mock 결과
        forensic_result = make_forensic_result(authenticity_score=0.85, total_files=42)
        logic_result = make_logic_result(logic_score=72.0, files_analyzed=38)
        stack_result = make_stack_result(mastery_score=78.0, total_skills=15)

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
        patches["application.nodes.meta.supervisor_adapters.run_forensic_pipeline"] = (
            AsyncMock(return_value=forensic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_logic_pipeline"] = (
            AsyncMock(return_value=logic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_stack_pipeline"] = (
            AsyncMock(return_value=stack_result)
        )

        with measure_time() as t:
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

        report.add("Pipeline: Full pipeline (Mock)", t["elapsed_ms"])

        # 검증
        assert runner.state["status"] == "completed"
        assert runner.state["errors"] == []

        # 기준: Mock 환경에서 < 5초
        assert t["elapsed_ms"] < 5000, f"Full pipeline too slow: {t['elapsed_ms']:.0f}ms"

        report.print_report()


# ===========================================================================
# d) 동시 실행 테스트
# ===========================================================================


class TestConcurrentPerformance:
    """동시 실행 시 성능과 격리를 측정한다."""

    @pytest.mark.asyncio
    async def test_concurrent_3_jobs(self, report: BenchmarkReport) -> None:
        """3개 job을 asyncio.gather로 동시 실행하고 순차 대비 속도를 비교한다.

        unittest.mock.patch는 글로벌 모듈 네임스페이스를 변경하므로
        동시 실행 시 각 task가 독립적으로 patch를 적용/해제하면 충돌한다.
        따라서 공유 InMemoryStore + 단일 patch 컨텍스트 안에서
        asyncio.gather를 실행한다.
        """
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
        from application.nodes.meta.quality_gate import quality_gate_node, should_revise
        from application.nodes.meta.output_assembler import output_assembler_node

        async def run_pipeline_nodes(runner: PipelineRunner) -> float:
            """patch가 이미 적용된 상태에서 노드만 순차 호출한다."""
            start = time.perf_counter()
            await runner.run_node(input_router_node)
            await runner.run_node(plan_generator_node)
            await runner.run_node(forensic_supervisor_node)
            await runner.run_node(logic_supervisor_node)
            await runner.run_node(stack_supervisor_node)
            await runner.run_node(profile_synthesizer_node)
            await runner.run_node(question_orchestrator_node)
            await runner.run_node(enhancement_agents_node)
            await runner.run_node(quality_gate_node)
            await runner.run_node(output_assembler_node)
            elapsed = (time.perf_counter() - start) * 1000
            assert runner.state["status"] == "completed"
            return elapsed

        def _prepare_runner(store: InMemoryStore) -> PipelineRunner:
            """store에 job을 등록하고 runner를 초기화한다."""
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
            return runner

        # 공유 Mock 설정
        shared_store = InMemoryStore()
        forensic_result = make_forensic_result()
        logic_result = make_logic_result()
        stack_result = make_stack_result()

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

        patches = _build_patches(shared_store, llm_responses)
        patches["application.nodes.meta.supervisor_adapters.run_forensic_pipeline"] = (
            AsyncMock(return_value=forensic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_logic_pipeline"] = (
            AsyncMock(return_value=logic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_stack_pipeline"] = (
            AsyncMock(return_value=stack_result)
        )

        # 순차 실행: 3개 job (단일 patch 컨텍스트)
        sequential_times = []
        with _apply_patches(patches):
            with measure_time() as seq_total:
                for _ in range(3):
                    runner = _prepare_runner(shared_store)
                    t = await run_pipeline_nodes(runner)
                    sequential_times.append(t)
        sequential_total_ms = seq_total["elapsed_ms"]

        report.add("Concurrency: Sequential 3 pipelines", sequential_total_ms)
        report.add("Concurrency: Sequential avg per pipeline", sum(sequential_times) / 3)

        # 동시 실행: 3개 job (단일 patch 컨텍스트 안에서 gather)
        with _apply_patches(patches):
            runners = [_prepare_runner(shared_store) for _ in range(3)]
            with measure_time() as conc_total:
                results = await asyncio.gather(
                    run_pipeline_nodes(runners[0]),
                    run_pipeline_nodes(runners[1]),
                    run_pipeline_nodes(runners[2]),
                )
        concurrent_total_ms = conc_total["elapsed_ms"]

        report.add("Concurrency: Concurrent 3 pipelines (gather)", concurrent_total_ms)

        # 속도 비교
        if concurrent_total_ms > 0:
            speedup = sequential_total_ms / concurrent_total_ms
            report.add(f"Concurrency: Speedup ratio ({speedup:.1f}x)", speedup)

        report.print_report()

        # 기준: 동시 실행이 순차보다 빠르지 않더라도 크게 느리지 않아야 함
        # (Mock 환경에서는 CPU bound이므로 큰 차이 없을 수 있음)
        # 동시 실행이 순차의 2배 이상 느리면 문제
        assert concurrent_total_ms < sequential_total_ms * 2, (
            f"Concurrent execution too slow: {concurrent_total_ms:.0f}ms "
            f"vs sequential {sequential_total_ms:.0f}ms"
        )


# ===========================================================================
# e) 메모리/크기 추정
# ===========================================================================


class TestMemoryEstimation:
    """MetaState와 checkpoint 등가 크기를 추정한다."""

    def test_meta_state_size(self, report: BenchmarkReport) -> None:
        """MetaState dict의 메모리 크기를 추정한다."""
        state: dict[str, Any] = {
            "job_id": str(uuid.uuid4()),
            "input_data_ref": str(uuid.uuid4()),
            "identity_cluster_ref": str(uuid.uuid4()),
            "forensic_result_ref": str(uuid.uuid4()),
            "logic_result_ref": str(uuid.uuid4()),
            "stack_result_ref": str(uuid.uuid4()),
            "profile_ref": str(uuid.uuid4()),
            "candidate_scores": {
                "logic": {"metric_type": "logic", "raw_score": 72.0, "normalized_score": 72.0,
                          "sub_scores": {"complexity": 65.0, "maintainability": 78.0}, "evidence_count": 38},
                "mastery": {"metric_type": "mastery", "raw_score": 78.0, "normalized_score": 78.0,
                            "sub_scores": {"api_depth": 75.0, "architecture": 80.0}, "evidence_count": 15},
                "stability": {"metric_type": "stability", "raw_score": 65.0, "normalized_score": 65.0,
                              "sub_scores": {"test_coverage": 60.0, "error_handling": 70.0}, "evidence_count": 20},
                "authenticity": {"metric_type": "authenticity", "raw_score": 85.0, "normalized_score": 85.0,
                                 "sub_scores": {"ai_suspicion": 8.0, "style_consistency": 92.0}, "evidence_count": 42},
                "weighted_total": 74.5,
                "confidence": "low",
            },
            "questions_ref": str(uuid.uuid4()),
            "status": "completed",
            "current_phase": "output",
            "revision_count": 0,
            "_quality_verdict": "approve",
            "errors": [],
        }

        # sys.getsizeof는 shallow size만 반환하므로 JSON 직렬화 크기로 추정
        json_bytes = len(json.dumps(state).encode("utf-8"))
        shallow_size = sys.getsizeof(state)

        report.add("Memory: MetaState dict shallow size (bytes)", shallow_size)
        report.add("Memory: MetaState JSON serialized (bytes)", json_bytes)

        report.print_report()

        # 기준: checkpoint 등가 크기 < 10KB
        assert json_bytes < 10240, f"MetaState checkpoint too large: {json_bytes} bytes"

    def test_checkpoint_equivalent_size(self, report: BenchmarkReport) -> None:
        """실제 파이프라인 완료 후 상태의 checkpoint 등가 크기를 측정한다."""
        # 최대 크기 시나리오: 모든 ref가 채워지고, errors에 메시지가 있는 경우
        state: dict[str, Any] = {
            "job_id": str(uuid.uuid4()),
            "input_data_ref": str(uuid.uuid4()),
            "identity_cluster_ref": str(uuid.uuid4()),
            "forensic_result_ref": str(uuid.uuid4()),
            "logic_result_ref": str(uuid.uuid4()),
            "stack_result_ref": str(uuid.uuid4()),
            "profile_ref": str(uuid.uuid4()),
            "candidate_scores": {
                "logic": {"metric_type": "logic", "raw_score": 72.0, "normalized_score": 72.0,
                          "sub_scores": {"complexity": 65.0, "maintainability": 78.0,
                                         "design_patterns": 70.0, "code_organization": 75.0},
                          "evidence_count": 38},
                "mastery": {"metric_type": "mastery", "raw_score": 78.0, "normalized_score": 78.0,
                            "sub_scores": {"api_depth": 75.0, "architecture": 80.0,
                                           "framework_usage": 82.0, "advanced_patterns": 68.0},
                            "evidence_count": 15},
                "stability": {"metric_type": "stability", "raw_score": 65.0, "normalized_score": 65.0,
                              "sub_scores": {"test_coverage": 60.0, "error_handling": 70.0,
                                             "code_consistency": 62.0, "documentation": 55.0},
                              "evidence_count": 20},
                "authenticity": {"metric_type": "authenticity", "raw_score": 85.0, "normalized_score": 85.0,
                                 "sub_scores": {"ai_suspicion": 8.0, "style_consistency": 92.0,
                                                "commit_pattern": 88.0, "contribution_depth": 85.0},
                                 "evidence_count": 42},
                "weighted_total": 74.5,
                "confidence": "medium",
            },
            "questions_ref": str(uuid.uuid4()),
            "status": "completed",
            "current_phase": "output",
            "revision_count": 2,
            "_quality_verdict": "approve",
            "errors": [
                "logic supervisor failed: AST parser timeout on file_42.py",
                "enhancement_agents: LLM rate limit reached, skipping enhancement",
            ],
        }

        json_bytes = len(json.dumps(state).encode("utf-8"))

        report.add("Memory: Max checkpoint equivalent (bytes)", json_bytes)

        report.print_report()

        # Reference Passing 패턴 덕분에 < 10KB 유지
        assert json_bytes < 10240, f"Checkpoint too large: {json_bytes} bytes (> 10KB)"


# ===========================================================================
# 종합 벤치마크 — 모든 카테고리를 한 번에 실행
# ===========================================================================


class TestComprehensiveBenchmark:
    """전체 벤치마크를 한 번에 실행하고 종합 리포트를 출력한다."""

    @pytest.mark.asyncio
    async def test_comprehensive_benchmark(self, report: BenchmarkReport) -> None:
        """모든 벤치마크를 순차 실행하여 종합 리포트를 생성한다."""
        # --- a) Domain Functions ---
        scores = _make_metric_scores()
        with measure_time() as t_score:
            for _ in range(1000):
                calculate_weighted_score(scores)
        report.add("Domain: calculate_weighted_score", t_score["elapsed_ms"], 1000)

        authors = _make_git_authors(100)
        profile = _make_github_profile()
        with measure_time() as t_mailmap:
            build_dynamic_mailmap(authors, profile, "MDQ6VXNlcjEyMzQ1")
        report.add("Domain: build_dynamic_mailmap (100 authors)", t_mailmap["elapsed_ms"])

        repos = _make_repo_metadata_list(100)
        config = FunnelConfig()
        with measure_time() as t_filter:
            stage1_hard_filter(repos, ["Python", "JavaScript"], config)
        report.add("Domain: stage1_hard_filter (100 repos)", t_filter["elapsed_ms"])

        # --- b) Node Execution (measured within the pipeline) ---
        # --- c) Full Pipeline ---
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
        from application.nodes.meta.quality_gate import quality_gate_node, should_revise
        from application.nodes.meta.output_assembler import output_assembler_node

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

        forensic_result = make_forensic_result(authenticity_score=0.85, total_files=42)
        logic_result = make_logic_result(logic_score=72.0, files_analyzed=38)
        stack_result = make_stack_result(mastery_score=78.0, total_skills=15)

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
        patches["application.nodes.meta.supervisor_adapters.run_forensic_pipeline"] = (
            AsyncMock(return_value=forensic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_logic_pipeline"] = (
            AsyncMock(return_value=logic_result)
        )
        patches["application.nodes.meta.supervisor_adapters.run_stack_pipeline"] = (
            AsyncMock(return_value=stack_result)
        )

        # 노드별 시간 측정
        node_times: dict[str, float] = {}

        with _apply_patches(patches):
            with measure_time() as t_ir:
                await runner.run_node(input_router_node)
            node_times["input_router"] = t_ir["elapsed_ms"]

            with measure_time() as t_pg:
                await runner.run_node(plan_generator_node)
            node_times["plan_generator"] = t_pg["elapsed_ms"]

            with measure_time() as t_fs:
                await runner.run_node(forensic_supervisor_node)
            node_times["forensic_supervisor"] = t_fs["elapsed_ms"]

            with measure_time() as t_ls:
                await runner.run_node(logic_supervisor_node)
            node_times["logic_supervisor"] = t_ls["elapsed_ms"]

            with measure_time() as t_ss:
                await runner.run_node(stack_supervisor_node)
            node_times["stack_supervisor"] = t_ss["elapsed_ms"]

            with measure_time() as t_ps:
                await runner.run_node(profile_synthesizer_node)
            node_times["profile_synthesizer"] = t_ps["elapsed_ms"]

            with measure_time() as t_qo:
                await runner.run_node(question_orchestrator_node)
            node_times["question_orchestrator"] = t_qo["elapsed_ms"]

            with measure_time() as t_ea:
                await runner.run_node(enhancement_agents_node)
            node_times["enhancement_agents"] = t_ea["elapsed_ms"]

            with measure_time() as t_qg:
                await runner.run_node(quality_gate_node)
            node_times["quality_gate"] = t_qg["elapsed_ms"]

            route = should_revise(runner.state)
            assert route == "approve"

            with measure_time() as t_oa:
                await runner.run_node(output_assembler_node)
            node_times["output_assembler"] = t_oa["elapsed_ms"]

        assert runner.state["status"] == "completed"

        # 노드별 결과 기록
        for name, elapsed in node_times.items():
            report.add(f"Node: {name}", elapsed)

        pipeline_total = sum(node_times.values())
        report.add("Pipeline: Total (sum of nodes)", pipeline_total)

        # --- e) Memory ---
        state_json = json.dumps(runner.state, default=str).encode("utf-8")
        report.add("Memory: Final state JSON (bytes)", len(state_json))

        report.print_report()

        # 종합 assertions
        assert t_score["elapsed_ms"] / 1000 < 10  # Domain: avg < 10ms
        assert t_mailmap["elapsed_ms"] < 10
        assert t_filter["elapsed_ms"] < 10
        assert pipeline_total < 5000  # Pipeline: < 5s
        assert len(state_json) < 10240  # Memory: < 10KB
