"""
G6/G7/G9 인프라 갭 해결 테스트.

G6: Worker 에러 핸들링 — 각 노드에서 예외 발생 시 기본값으로 계속 진행
G7: WebSocket 이벤트 — build_node_event로 구조화된 이벤트 생성
G9: Checkpoint — MemorySaver 폴백
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# langfuse import 문제 우회 (기존 테스트 패턴 준수)
# ---------------------------------------------------------------------------
_langfuse_modules = [
    "langfuse",
    "langfuse.api",
    "langfuse.api.core",
    "langfuse.api.core.pydantic_utilities",
    "langfuse.api.resources",
    "langfuse.api.resources.annotation_queues",
    "langfuse.api.resources.annotation_queues.types",
    "langfuse.api.resources.commons",
    "langfuse.api.resources.commons.types",
    "langfuse.batch_evaluation",
    "langfuse.decorators",
]
for _mod_name in _langfuse_modules:
    if _mod_name not in sys.modules:
        _m = ModuleType(_mod_name)
        if _mod_name == "langfuse":
            _m.Langfuse = MagicMock  # type: ignore[attr-defined]
        sys.modules[_mod_name] = _m

from application.events import NODE_PROGRESS, build_node_event  # noqa: E402


# ===========================================================================
# G7: WebSocket 이벤트 — build_node_event 테스트
# ===========================================================================


class TestBuildNodeEvent:
    """build_node_event 함수의 구조화된 이벤트 생성을 검증한다."""

    def test_known_node_returns_correct_progress(self):
        event = build_node_event("forensic_supervisor", {"status": "analyzing"})
        assert event["type"] == "node_complete"
        assert event["node"] == "forensic_supervisor"
        assert event["progress"] == 0.30
        assert event["label"] == "코드 포렌식 분석"
        assert event["status"] == "analyzing"
        assert event["has_errors"] is False

    def test_unknown_node_returns_zero_progress(self):
        event = build_node_event("unknown_node", {})
        assert event["progress"] == 0.0
        assert event["label"] == "unknown_node"

    def test_event_with_errors(self):
        event = build_node_event("logic_supervisor", {
            "status": "analyzing",
            "errors": ["logic supervisor: timeout"],
        })
        assert event["has_errors"] is True

    def test_event_without_errors(self):
        event = build_node_event("input_router", {"status": "collecting"})
        assert event["has_errors"] is False

    def test_all_meta_nodes_have_progress_mapping(self):
        """MetaGraph의 모든 노드가 NODE_PROGRESS에 매핑되어 있어야 한다."""
        expected_nodes = [
            "input_router",
            "plan_generator",
            "forensic_supervisor",
            "logic_supervisor",
            "stack_supervisor",
            "profile_synthesizer",
            "question_orchestrator",
            "enhancement_agents",
            "quality_gate",
            "output_assembler",
        ]
        for node in expected_nodes:
            assert node in NODE_PROGRESS, f"Missing node in NODE_PROGRESS: {node}"

    def test_progress_values_are_monotonically_increasing(self):
        """노드 진행률이 파이프라인 순서대로 단조 증가해야 한다."""
        ordered_nodes = [
            "input_router",
            "plan_generator",
            "forensic_supervisor",
            "logic_supervisor",
            "stack_supervisor",
            "profile_synthesizer",
            "question_orchestrator",
            "enhancement_agents",
            "quality_gate",
            "output_assembler",
        ]
        prev_progress = -1.0
        for node in ordered_nodes:
            progress = NODE_PROGRESS[node][0]
            assert progress > prev_progress, (
                f"{node} progress ({progress}) <= previous ({prev_progress})"
            )
            prev_progress = progress

    def test_progress_values_within_range(self):
        """모든 진행률 값이 0.0 ~ 1.0 범위 내여야 한다."""
        for node, (progress, _) in NODE_PROGRESS.items():
            assert 0.0 <= progress <= 1.0, f"{node} progress out of range: {progress}"

    def test_empty_state_update(self):
        event = build_node_event("output_assembler", {})
        assert event["status"] == ""
        assert event["has_errors"] is False


# ===========================================================================
# G6: Worker 에러 핸들링 — input_router_node 테스트
# ===========================================================================


class TestInputRouterErrorHandling:
    """input_router_node의 예외 처리를 검증한다."""

    @pytest.mark.asyncio
    async def test_db_exception_returns_error_state(self):
        from application.nodes.meta.input_router import input_router_node

        state = {"job_id": "job-1", "errors": []}

        with patch("application.nodes.meta.input_router.JobRepository") as MockRepo:
            MockRepo.return_value.get = AsyncMock(
                side_effect=Exception("DB connection refused")
            )
            result = await input_router_node(state)

        assert result["status"] == "failed"
        assert any("input_router" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_preserves_existing_errors(self):
        from application.nodes.meta.input_router import input_router_node

        state = {"job_id": "job-1", "errors": ["previous error"]}

        with patch("application.nodes.meta.input_router.JobRepository") as MockRepo:
            MockRepo.return_value.get = AsyncMock(
                side_effect=Exception("DB timeout")
            )
            result = await input_router_node(state)

        assert "previous error" in result["errors"]
        assert len(result["errors"]) == 2


# ===========================================================================
# G6: Worker 에러 핸들링 — plan_generator_node 테스트
# ===========================================================================


class TestPlanGeneratorErrorHandling:
    """plan_generator_node의 예외 처리를 검증한다."""

    @pytest.mark.asyncio
    async def test_db_exception_returns_error_state(self):
        from application.nodes.meta.plan_generator import plan_generator_node

        state = {"job_id": "job-1", "errors": []}

        with patch("application.nodes.meta.plan_generator.JobRepository") as MockRepo:
            MockRepo.return_value.get = AsyncMock(
                side_effect=Exception("DB connection refused")
            )
            result = await plan_generator_node(state)

        assert result["status"] == "failed"
        assert any("plan_generator" in e for e in result["errors"])


# ===========================================================================
# G6: Worker 에러 핸들링 — profile_synthesizer_node 테스트
# ===========================================================================


class TestProfileSynthesizerErrorHandling:
    """profile_synthesizer_node의 예외 처리를 검증한다."""

    @pytest.mark.asyncio
    async def test_db_exception_returns_default_scores(self):
        from application.nodes.meta.profile_synthesizer import profile_synthesizer_node

        state = {
            "job_id": "job-1",
            "forensic_result_ref": "ref-f",
            "logic_result_ref": "ref-l",
            "stack_result_ref": "ref-s",
            "errors": [],
        }

        with patch(
            "application.nodes.meta.profile_synthesizer.AnalysisRepository"
        ) as MockRepo:
            MockRepo.return_value.get_result = AsyncMock(
                side_effect=Exception("DB read failed")
            )
            result = await profile_synthesizer_node(state)

        # 기본 점수로 계속 진행
        assert result["candidate_scores"] is not None
        assert result["candidate_scores"]["weighted_total"] == 50.0
        assert result["candidate_scores"]["confidence"] == "low"
        assert result["profile_ref"] is None
        assert result["status"] == "synthesizing"
        assert any("profile_synthesizer" in e for e in result["errors"])


# ===========================================================================
# G6: Worker 에러 핸들링 — question_orchestrator_node 테스트
# ===========================================================================


class TestQuestionOrchestratorErrorHandling:
    """question_orchestrator_node의 예외 처리를 검증한다."""

    @pytest.mark.asyncio
    async def test_db_exception_returns_none_questions_ref(self):
        from application.nodes.meta.question_orchestrator import question_orchestrator_node

        state = {
            "job_id": "job-1",
            "profile_ref": "ref-p",
            "forensic_result_ref": "ref-f",
            "logic_result_ref": "ref-l",
            "stack_result_ref": "ref-s",
            "errors": [],
        }

        with patch(
            "application.nodes.meta.question_orchestrator.AnalysisRepository"
        ) as MockRepo:
            MockRepo.return_value.get_result = AsyncMock(
                side_effect=Exception("DB read failed")
            )
            result = await question_orchestrator_node(state)

        assert result["questions_ref"] is None
        assert result["status"] == "questioning"
        assert any("question_orchestrator" in e for e in result["errors"])


# ===========================================================================
# G6: Worker 에러 핸들링 — enhancement_agents_node 테스트
# ===========================================================================


class TestEnhancementAgentsErrorHandling:
    """enhancement_agents_node의 예외 처리를 검증한다."""

    @pytest.mark.asyncio
    async def test_db_exception_preserves_questions_ref(self):
        from application.nodes.meta.enhancement_agents import enhancement_agents_node

        state = {
            "job_id": "job-1",
            "questions_ref": "ref-q",
            "errors": [],
        }

        with patch(
            "application.nodes.meta.enhancement_agents.AnalysisRepository"
        ) as MockRepo:
            MockRepo.return_value.get_result = AsyncMock(
                side_effect=Exception("DB read failed")
            )
            result = await enhancement_agents_node(state)

        # 기존 questions_ref는 변경되지 않음 (에러만 추가)
        assert "questions_ref" not in result  # 보강 실패 시 questions_ref를 덮어쓰지 않음
        assert any("enhancement_agents" in e for e in result["errors"])


# ===========================================================================
# G6: Worker 에러 핸들링 — output_assembler_node 테스트
# ===========================================================================


class TestOutputAssemblerErrorHandling:
    """output_assembler_node의 예외 처리를 검증한다."""

    @pytest.mark.asyncio
    async def test_db_exception_returns_failed_state(self):
        from application.nodes.meta.output_assembler import output_assembler_node

        state = {
            "job_id": "job-1",
            "profile_ref": "ref-p",
            "questions_ref": "ref-q",
            "forensic_result_ref": "ref-f",
            "logic_result_ref": "ref-l",
            "stack_result_ref": "ref-s",
            "candidate_scores": None,
            "errors": [],
        }

        with patch(
            "application.nodes.meta.output_assembler.AnalysisRepository"
        ) as MockRepo:
            MockRepo.return_value.get_result = AsyncMock(
                side_effect=Exception("DB read failed")
            )
            result = await output_assembler_node(state)

        assert result["status"] == "failed"
        assert result["current_phase"] == "output"
        assert any("output_assembler" in e for e in result["errors"])


# ===========================================================================
# G9: Checkpoint — _create_checkpointer 테스트
# ===========================================================================


class TestCreateCheckpointer:
    """_create_checkpointer의 PostgreSQL → MemorySaver 폴백을 검증한다."""

    @pytest.mark.asyncio
    async def test_empty_db_url_uses_memory_saver(self):
        from application.use_cases.run_analysis import _create_checkpointer

        checkpointer = await _create_checkpointer("")

        # MemorySaver 인스턴스인지 확인
        from langgraph.checkpoint.memory import MemorySaver
        assert isinstance(checkpointer, MemorySaver)

    @pytest.mark.asyncio
    async def test_postgres_failure_falls_back_to_memory(self):
        from application.use_cases.run_analysis import _create_checkpointer

        with patch(
            "application.use_cases.run_analysis.AsyncPostgresSaver",
            create=True,
        ) as MockSaver:
            # from_conn_string 자체가 예외를 발생
            MockSaver.from_conn_string.side_effect = Exception("PG connection refused")

            # langgraph.checkpoint.postgres.aio 모듈을 모킹
            with patch.dict(sys.modules, {
                "langgraph.checkpoint.postgres": MagicMock(),
                "langgraph.checkpoint.postgres.aio": MagicMock(
                    AsyncPostgresSaver=MockSaver,
                ),
            }):
                checkpointer = await _create_checkpointer("postgresql://fake:5432/test")

        from langgraph.checkpoint.memory import MemorySaver
        assert isinstance(checkpointer, MemorySaver)
