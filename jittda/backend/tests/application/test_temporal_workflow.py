"""
Temporal Workflow 단위 테스트 — AnalysisPipeline + Activities.

Mock 환경에서 Workflow 흐름과 Activity 래핑을 검증한다.
"""
from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest


# ===========================================================================
# Activity 래핑 테스트
# ===========================================================================


class TestActivities:
    """Activities가 기존 노드 함수를 올바르게 래핑하는지 검증."""

    @pytest.mark.asyncio
    async def test_build_meta_state_basic(self) -> None:
        """_build_meta_state가 기본 필드를 올바르게 구성한다."""
        from application.temporal.activities import _build_meta_state

        args = {"job_id": "job-1", "input_data_ref": "job-1"}
        state = _build_meta_state("job-1", args)

        assert state["job_id"] == "job-1"
        assert state["input_data_ref"] == "job-1"
        assert state["errors"] == []
        assert state["revision_count"] == 0

    @pytest.mark.asyncio
    async def test_build_meta_state_preserves_refs(self) -> None:
        """_build_meta_state가 기존 ref를 보존한다."""
        from application.temporal.activities import _build_meta_state

        args = {
            "job_id": "j1",
            "forensic_result_ref": "fr-1",
            "logic_result_ref": "lr-1",
            "candidate_scores": {"weighted_total": 75},
            "revision_count": 1,
            "errors": ["some error"],
        }
        state = _build_meta_state("j1", args)

        assert state["forensic_result_ref"] == "fr-1"
        assert state["logic_result_ref"] == "lr-1"
        assert state["candidate_scores"] == {"weighted_total": 75}
        assert state["revision_count"] == 1
        assert state["errors"] == ["some error"]

    @pytest.mark.asyncio
    async def test_build_meta_state_defaults(self) -> None:
        """_build_meta_state가 누락된 필드에 기본값을 채운다."""
        from application.temporal.activities import _build_meta_state

        state = _build_meta_state("j1", {"job_id": "j1"})

        assert state["identity_cluster_ref"] is None
        assert state["repo_paths_ref"] is None
        assert state["forensic_result_ref"] is None
        assert state["logic_result_ref"] is None
        assert state["stack_result_ref"] is None
        assert state["profile_ref"] is None
        assert state["candidate_scores"] is None
        assert state["questions_ref"] is None
        assert state["status"] == "pending"
        assert state["current_phase"] == "input_router"
        assert state["revision_count"] == 0
        assert state["_quality_verdict"] == ""
        assert state["errors"] == []


# ===========================================================================
# Node Progress 매핑 테스트
# ===========================================================================


class TestNodeProgress:
    """NODE_PROGRESS 매핑 검증 — events.py 대체."""

    def test_all_nodes_have_progress(self) -> None:
        """모든 파이프라인 노드가 progress 매핑에 존재한다."""
        from application.temporal.activities import NODE_PROGRESS

        expected_nodes = {
            "input_router",
            "plan_generator",
            "repo_collector",
            "forensic_supervisor",
            "logic_supervisor",
            "stack_supervisor",
            "profile_synthesizer",
            "question_orchestrator",
            "enhancement_agents",
            "quality_gate",
            "output_assembler",
        }
        assert expected_nodes == set(NODE_PROGRESS.keys())

    def test_progress_monotonically_increasing(self) -> None:
        """진행률이 단조 증가한다."""
        from application.temporal.activities import NODE_PROGRESS

        ordered_nodes = [
            "input_router",
            "plan_generator",
            "repo_collector",
            "forensic_supervisor",
            "logic_supervisor",
            "stack_supervisor",
            "profile_synthesizer",
            "question_orchestrator",
            "enhancement_agents",
            "quality_gate",
            "output_assembler",
        ]
        prev = 0.0
        for node in ordered_nodes:
            progress = NODE_PROGRESS[node][0]
            assert progress > prev, f"{node} progress {progress} <= {prev}"
            prev = progress

    def test_progress_in_valid_range(self) -> None:
        """진행률이 0.0-1.0 범위 내이다."""
        from application.temporal.activities import NODE_PROGRESS

        for node, (progress, label) in NODE_PROGRESS.items():
            assert 0.0 < progress <= 1.0, f"{node}: {progress}"
            assert isinstance(label, str) and len(label) > 0


# ===========================================================================
# Workflow 구조 테스트
# ===========================================================================


class TestWorkflowStructure:
    """AnalysisPipeline Workflow 구조 검증."""

    def test_workflow_is_registered(self) -> None:
        """AnalysisPipeline이 Temporal workflow로 등록되어 있다."""
        from application.temporal.workflows import AnalysisPipeline

        assert hasattr(AnalysisPipeline, "run")

    def test_all_activities_registered(self) -> None:
        """모든 Activity가 ALL_ACTIVITIES에 등록되어 있다."""
        from application.temporal.activities import ALL_ACTIVITIES

        assert len(ALL_ACTIVITIES) == 11

        activity_names = {a.__name__ for a in ALL_ACTIVITIES}
        expected = {
            "input_agent",
            "plan_agent",
            "collector_agent",
            "forensic_agent",
            "logic_agent",
            "stack_agent",
            "profile_agent",
            "question_orchestrator_agent",
            "enhancement_agent",
            "quality_gate_agent",
            "output_agent",
        }
        assert activity_names == expected

    def test_task_queue_constant(self) -> None:
        """TASK_QUEUE 상수가 정의되어 있다."""
        from application.temporal import TASK_QUEUE

        assert TASK_QUEUE == "jittda-analysis"


# ===========================================================================
# 에러 분류 테스트
# ===========================================================================


class TestClassifyAndRaise:
    """_classify_and_raise 에러 분류 로직 검증."""

    def test_fatal_errors_raise_non_retryable(self) -> None:
        """Fatal 에러 타입은 ApplicationError(non_retryable=True)로 래핑된다."""
        from temporalio.exceptions import ApplicationError

        from application.temporal.activities import _classify_and_raise

        fatal_errors = [
            ValueError("bad value"),
            KeyError("missing_key"),
            TypeError("wrong type"),
            AttributeError("no attr"),
            ImportError("no module"),
        ]
        for err in fatal_errors:
            with pytest.raises(ApplicationError) as exc_info:
                _classify_and_raise(err, "test_activity")
            assert exc_info.value.non_retryable is True
            assert "test_activity" in str(exc_info.value)

    def test_recoverable_errors_reraise_original(self) -> None:
        """Recoverable 에러는 원본 예외를 그대로 re-raise한다."""
        from application.temporal.activities import _classify_and_raise

        recoverable_errors = [
            ConnectionError("network down"),
            TimeoutError("timed out"),
            OSError("io error"),
            RuntimeError("runtime fail"),
        ]
        for err in recoverable_errors:
            with pytest.raises(type(err)):
                _classify_and_raise(err, "test_activity")

    def test_fatal_error_preserves_cause(self) -> None:
        """Fatal 에러가 원본 예외를 __cause__로 보존한다."""
        from temporalio.exceptions import ApplicationError

        from application.temporal.activities import _classify_and_raise

        original = ValueError("original error")
        with pytest.raises(ApplicationError) as exc_info:
            _classify_and_raise(original, "test_activity")
        assert exc_info.value.__cause__ is original


# ===========================================================================
# Worker 환경변수 검증 테스트
# ===========================================================================


class TestValidateEnv:
    """_validate_env 환경변수 검증 로직."""

    def test_all_required_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """모든 필수 변수 설정 시 required missing 없음."""
        from worker import _validate_env

        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
        monkeypatch.setenv("TEMPORAL_HOST", "localhost:7233")
        monkeypatch.setenv("LLM_API_KEY", "sk-test")
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")

        missing = _validate_env()
        required_missing = [m for m in missing if m.startswith("[REQUIRED]")]
        assert len(required_missing) == 0

    def test_missing_required_detected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """필수 변수 누락 시 감지된다."""
        from worker import _validate_env

        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.delenv("TEMPORAL_HOST", raising=False)

        missing = _validate_env()
        required_missing = [m for m in missing if m.startswith("[REQUIRED]")]
        assert len(required_missing) == 3

    def test_missing_recommended_detected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """추천 변수 누락 시 감지되지만 required는 아님."""
        from worker import _validate_env

        monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
        monkeypatch.setenv("TEMPORAL_HOST", "localhost:7233")
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        missing = _validate_env()
        required_missing = [m for m in missing if m.startswith("[REQUIRED]")]
        recommended_missing = [m for m in missing if m.startswith("[RECOMMENDED]")]
        assert len(required_missing) == 0
        assert len(recommended_missing) == 2


# ===========================================================================
# Activity 이벤트 발행 테스트
# ===========================================================================


class TestPublishEvent:
    """_publish_event Redis 이벤트 발행 로직."""

    @pytest.mark.asyncio
    async def test_publish_event_formats_correctly(self) -> None:
        """노드 진행률 이벤트가 올바른 형식으로 발행된다."""
        import json

        from application.temporal.activities import _publish_event, NODE_PROGRESS

        published = {}

        async def mock_publish(channel, data):
            published["channel"] = channel
            published["data"] = json.loads(data)

        mock_redis = AsyncMock()
        mock_redis.publish = mock_publish

        with patch("application.temporal.activities._get_redis", return_value=mock_redis):
            await _publish_event("job-123", "input_router")

        assert published["channel"] == "job:job-123:events"
        assert published["data"]["type"] == "node_complete"
        assert published["data"]["node"] == "input_router"
        assert published["data"]["progress"] == 0.05
        assert published["data"]["label"] == "입력 분석"

    @pytest.mark.asyncio
    async def test_publish_event_ignores_redis_failure(self) -> None:
        """Redis 실패 시 예외를 삼키고 경고만 출력한다."""
        from application.temporal.activities import _publish_event

        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(side_effect=ConnectionError("redis down"))

        with patch("application.temporal.activities._get_redis", return_value=mock_redis):
            # 예외가 전파되지 않아야 함
            await _publish_event("job-123", "input_router")

    @pytest.mark.asyncio
    async def test_publish_event_noop_when_no_redis(self) -> None:
        """Redis가 없으면 아무 동작도 하지 않는다."""
        from application.temporal.activities import _publish_event

        with patch("application.temporal.activities._get_redis", return_value=None):
            await _publish_event("job-123", "input_router")  # 에러 없이 완료


# ===========================================================================
# API 스키마 테스트
# ===========================================================================


class TestJobSchemas:
    """Job API 스키마 검증."""

    def test_jd_text_alias(self) -> None:
        """jd_text alias가 jd_description으로 매핑된다."""
        from interface.api.schemas.job_schemas import JobCreateRequest

        req = JobCreateRequest(
            candidate_username="test",
            jd_text="Backend Engineer",
        )
        assert req.jd_description == "Backend Engineer"

    def test_jd_description_direct(self) -> None:
        """jd_description 직접 사용도 가능하다."""
        from interface.api.schemas.job_schemas import JobCreateRequest

        req = JobCreateRequest(
            candidate_username="test",
            jd_description="Frontend Developer",
        )
        assert req.jd_description == "Frontend Developer"

    def test_uuid_validation_helper(self) -> None:
        """_validate_uuid가 잘못된 UUID에서 HTTPException을 발생시킨다."""
        from fastapi import HTTPException

        from interface.api.routes.jobs import _validate_uuid

        # 유효한 UUID — 에러 없음
        _validate_uuid("44f54959-b564-427e-915b-c1a063c41ef4")

        # 잘못된 UUID — 400
        with pytest.raises(HTTPException) as exc_info:
            _validate_uuid("not-a-uuid")
        assert exc_info.value.status_code == 400
