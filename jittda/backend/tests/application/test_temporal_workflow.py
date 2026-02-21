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
