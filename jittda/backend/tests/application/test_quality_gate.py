"""
QualityGate 노드 + should_revise 라우터 테스트.

외부 의존성(DB, LLM)을 모킹하여 순수 로직만 검증한다.
"""
from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# langfuse import 문제 우회 (Python 3.14 + pydantic v1 호환 문제)
# infrastructure.llm.__init__.py가 langfuse_client를 import할 때
# langfuse가 pydantic v1에서 폭발하므로, langfuse 모듈 트리를 사전 등록한다.
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
        # langfuse 최상위에 Langfuse 클래스 더미 등록
        if _mod_name == "langfuse":
            _m.Langfuse = MagicMock  # type: ignore[attr-defined]
        sys.modules[_mod_name] = _m

from application.nodes.meta.quality_gate import (  # noqa: E402
    MAX_REVISIONS,
    QualityReview,
    _summarize_questions,
    quality_gate_node,
    should_revise,
)


# ===========================================================================
# should_revise — 조건부 라우터 단위 테스트
# ===========================================================================


class TestShouldRevise:
    """should_revise 함수 테스트."""

    def test_approve_when_max_revisions_reached(self):
        state = {
            "revision_count": MAX_REVISIONS,
            "questions_ref": "some-ref",
            "_quality_verdict": "revise",
        }
        assert should_revise(state) == "approve"

    def test_approve_when_no_questions_ref(self):
        state = {"revision_count": 0}
        assert should_revise(state) == "approve"

    def test_approve_when_questions_ref_none(self):
        state = {"revision_count": 0, "questions_ref": None}
        assert should_revise(state) == "approve"

    def test_approve_when_verdict_is_approve(self):
        state = {
            "revision_count": 0,
            "questions_ref": "ref-123",
            "_quality_verdict": "approve",
        }
        assert should_revise(state) == "approve"

    def test_revise_when_verdict_is_revise(self):
        state = {
            "revision_count": 0,
            "questions_ref": "ref-123",
            "_quality_verdict": "revise",
        }
        assert should_revise(state) == "revise"

    def test_revise_at_revision_1(self):
        state = {
            "revision_count": 1,
            "questions_ref": "ref-123",
            "_quality_verdict": "revise",
        }
        assert should_revise(state) == "revise"

    def test_approve_when_verdict_missing(self):
        state = {"revision_count": 0, "questions_ref": "ref-123"}
        assert should_revise(state) == "approve"

    def test_approve_when_verdict_invalid(self):
        state = {
            "revision_count": 0,
            "questions_ref": "ref-123",
            "_quality_verdict": "garbage",
        }
        assert should_revise(state) == "approve"

    def test_approve_when_revision_count_exceeds_max(self):
        state = {
            "revision_count": 5,
            "questions_ref": "ref-123",
            "_quality_verdict": "revise",
        }
        assert should_revise(state) == "approve"


# ===========================================================================
# QualityReview — Pydantic 모델 테스트
# ===========================================================================


class TestQualityReview:
    """QualityReview 모델 유효성 검증."""

    def test_approve_review(self):
        r = QualityReview(
            overall_quality=0.85,
            issues=[],
            suggestions=[],
            verdict="approve",
        )
        assert r.overall_quality == 0.85
        assert r.verdict == "approve"
        assert r.issues == []

    def test_revise_review(self):
        r = QualityReview(
            overall_quality=0.4,
            issues=["Questions are too generic"],
            suggestions=["Add code references"],
            verdict="revise",
        )
        assert r.overall_quality == 0.4
        assert r.verdict == "revise"
        assert len(r.issues) == 1

    def test_quality_boundary_zero(self):
        r = QualityReview(overall_quality=0.0, issues=[], suggestions=[], verdict="revise")
        assert r.overall_quality == 0.0

    def test_quality_boundary_one(self):
        r = QualityReview(overall_quality=1.0, issues=[], suggestions=[], verdict="approve")
        assert r.overall_quality == 1.0

    def test_quality_out_of_range_high(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            QualityReview(overall_quality=1.5, issues=[], suggestions=[], verdict="approve")

    def test_quality_out_of_range_low(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            QualityReview(overall_quality=-0.1, issues=[], suggestions=[], verdict="approve")

    def test_default_empty_lists(self):
        r = QualityReview(overall_quality=0.7, verdict="approve")
        assert r.issues == []
        assert r.suggestions == []


# ===========================================================================
# _summarize_questions — 헬퍼 함수 테스트
# ===========================================================================


class TestSummarizeQuestions:
    """질문 요약 헬퍼 함수 테스트."""

    def test_dict_questions(self):
        questions = [
            {
                "question_id": "Q-001",
                "category": "technical_depth",
                "strategy": "negative_selection",
                "difficulty": "medium",
                "question_text": "Why did you not use connection pooling?",
                "code_reference": "src/db.py:42",
                "expected_answer_guide": "Should explain the trade-off",
                "red_flags": ["Cannot explain why"],
            },
        ]
        result = _summarize_questions(questions)
        assert "Q-001" in result
        assert "technical_depth" in result
        assert "negative_selection" in result
        assert "connection pooling" in result
        assert "src/db.py:42" in result

    def test_empty_questions(self):
        result = _summarize_questions([])
        assert result == ""

    def test_multiple_questions(self):
        questions = [
            {
                "question_id": f"Q-{i}",
                "category": "technical_depth",
                "strategy": "negative_selection",
                "difficulty": "medium",
                "question_text": f"Question {i} text here for testing",
            }
            for i in range(3)
        ]
        result = _summarize_questions(questions)
        assert "Q-0" in result
        assert "Q-1" in result
        assert "Q-2" in result

    def test_truncates_long_text(self):
        questions = [
            {
                "question_id": "Q-1",
                "question_text": "x" * 500,
                "expected_answer_guide": "y" * 500,
            },
        ]
        result = _summarize_questions(questions)
        # question_text truncated to 300, answer_guide to 200
        assert len(result) < 500 + 500


# ===========================================================================
# quality_gate_node — 비동기 노드 테스트
# ===========================================================================


class TestQualityGateNode:
    """quality_gate_node 비동기 테스트 (외부 의존성 모킹)."""

    @pytest.mark.asyncio
    async def test_force_approve_at_max_revisions(self):
        state = {
            "job_id": "job-1",
            "questions_ref": "ref-123",
            "revision_count": MAX_REVISIONS,
        }
        result = await quality_gate_node(state)
        assert result["_quality_verdict"] == "approve"
        assert result["status"] == "reviewing"

    @pytest.mark.asyncio
    async def test_approve_when_no_questions_ref(self):
        state = {"job_id": "job-1", "revision_count": 0}
        result = await quality_gate_node(state)
        assert result["_quality_verdict"] == "approve"

    @pytest.mark.asyncio
    async def test_approve_when_questions_ref_none(self):
        state = {"job_id": "job-1", "questions_ref": None, "revision_count": 0}
        result = await quality_gate_node(state)
        assert result["_quality_verdict"] == "approve"

    @pytest.mark.asyncio
    async def test_approve_when_db_read_fails(self):
        state = {
            "job_id": "job-1",
            "questions_ref": "ref-123",
            "revision_count": 0,
        }
        with patch(
            "application.nodes.meta.quality_gate.AnalysisRepository"
        ) as MockRepo:
            MockRepo.return_value.get_result = AsyncMock(
                side_effect=Exception("DB connection refused")
            )
            result = await quality_gate_node(state)

        assert result["_quality_verdict"] == "approve"

    @pytest.mark.asyncio
    async def test_approve_when_no_data_found(self):
        state = {
            "job_id": "job-1",
            "questions_ref": "ref-123",
            "revision_count": 0,
        }
        with patch(
            "application.nodes.meta.quality_gate.AnalysisRepository"
        ) as MockRepo:
            MockRepo.return_value.get_result = AsyncMock(return_value=None)
            result = await quality_gate_node(state)

        assert result["_quality_verdict"] == "approve"

    @pytest.mark.asyncio
    async def test_approve_when_empty_questions(self):
        state = {
            "job_id": "job-1",
            "questions_ref": "ref-123",
            "revision_count": 0,
        }
        with patch(
            "application.nodes.meta.quality_gate.AnalysisRepository"
        ) as MockRepo:
            MockRepo.return_value.get_result = AsyncMock(
                return_value={"result_data": {"questions": []}}
            )
            result = await quality_gate_node(state)

        assert result["_quality_verdict"] == "approve"

    @pytest.mark.asyncio
    async def test_llm_approve_verdict(self):
        state = {
            "job_id": "job-1",
            "questions_ref": "ref-123",
            "revision_count": 0,
        }
        mock_review = QualityReview(
            overall_quality=0.85,
            issues=[],
            suggestions=[],
            verdict="approve",
        )
        with (
            patch(
                "application.nodes.meta.quality_gate.AnalysisRepository"
            ) as MockRepo,
            patch(
                "application.nodes.meta.quality_gate.InstructorClient"
            ) as MockClient,
        ):
            MockRepo.return_value.get_result = AsyncMock(
                return_value={
                    "result_data": {
                        "questions": [
                            {"question_id": "Q-1", "question_text": "Why no pooling?"}
                        ]
                    }
                }
            )
            MockRepo.return_value.save_result = AsyncMock(return_value="review-ref-1")
            MockClient.return_value.create = AsyncMock(return_value=mock_review)

            result = await quality_gate_node(state)

        assert result["_quality_verdict"] == "approve"
        assert result["revision_count"] == 0  # no increment on approve

    @pytest.mark.asyncio
    async def test_llm_revise_verdict(self):
        state = {
            "job_id": "job-1",
            "questions_ref": "ref-123",
            "revision_count": 0,
        }
        mock_review = QualityReview(
            overall_quality=0.4,
            issues=["Questions are too generic"],
            suggestions=["Reference specific code files"],
            verdict="revise",
        )
        with (
            patch(
                "application.nodes.meta.quality_gate.AnalysisRepository"
            ) as MockRepo,
            patch(
                "application.nodes.meta.quality_gate.InstructorClient"
            ) as MockClient,
        ):
            MockRepo.return_value.get_result = AsyncMock(
                return_value={
                    "result_data": {
                        "questions": [
                            {"question_id": "Q-1", "question_text": "Why no pooling?"}
                        ]
                    }
                }
            )
            MockRepo.return_value.save_result = AsyncMock(return_value="review-ref-1")
            MockClient.return_value.create = AsyncMock(return_value=mock_review)

            result = await quality_gate_node(state)

        assert result["_quality_verdict"] == "revise"
        assert result["revision_count"] == 1  # incremented on revise

    @pytest.mark.asyncio
    async def test_llm_failure_falls_back_to_approve(self):
        state = {
            "job_id": "job-1",
            "questions_ref": "ref-123",
            "revision_count": 0,
        }
        with (
            patch(
                "application.nodes.meta.quality_gate.AnalysisRepository"
            ) as MockRepo,
            patch(
                "application.nodes.meta.quality_gate.InstructorClient"
            ) as MockClient,
        ):
            MockRepo.return_value.get_result = AsyncMock(
                return_value={
                    "result_data": {
                        "questions": [
                            {"question_id": "Q-1", "question_text": "Why no pooling?"}
                        ]
                    }
                }
            )
            MockClient.return_value.create = AsyncMock(
                side_effect=Exception("LLM API error")
            )

            result = await quality_gate_node(state)

        assert result["_quality_verdict"] == "approve"

    @pytest.mark.asyncio
    async def test_db_save_failure_does_not_block(self):
        """DB 저장 실패해도 파이프라인이 계속 진행되는지 확인."""
        state = {
            "job_id": "job-1",
            "questions_ref": "ref-123",
            "revision_count": 0,
        }
        mock_review = QualityReview(
            overall_quality=0.85,
            issues=[],
            suggestions=[],
            verdict="approve",
        )
        with (
            patch(
                "application.nodes.meta.quality_gate.AnalysisRepository"
            ) as MockRepo,
            patch(
                "application.nodes.meta.quality_gate.InstructorClient"
            ) as MockClient,
        ):
            MockRepo.return_value.get_result = AsyncMock(
                return_value={
                    "result_data": {
                        "questions": [
                            {"question_id": "Q-1", "question_text": "Why no pooling?"}
                        ]
                    }
                }
            )
            MockRepo.return_value.save_result = AsyncMock(
                side_effect=Exception("DB write failed")
            )
            MockClient.return_value.create = AsyncMock(return_value=mock_review)

            result = await quality_gate_node(state)

        # 여전히 정상적인 verdict 반환
        assert result["_quality_verdict"] == "approve"

    @pytest.mark.asyncio
    async def test_revision_count_increments_on_revise(self):
        """revision_count가 revise 시에만 증가하는지 확인."""
        state = {
            "job_id": "job-1",
            "questions_ref": "ref-123",
            "revision_count": 1,  # 이미 1회 리비전
        }
        mock_review = QualityReview(
            overall_quality=0.5,
            issues=["Still too generic"],
            suggestions=["Needs more code refs"],
            verdict="revise",
        )
        with (
            patch(
                "application.nodes.meta.quality_gate.AnalysisRepository"
            ) as MockRepo,
            patch(
                "application.nodes.meta.quality_gate.InstructorClient"
            ) as MockClient,
        ):
            MockRepo.return_value.get_result = AsyncMock(
                return_value={
                    "result_data": {
                        "questions": [
                            {"question_id": "Q-1", "question_text": "Why no pooling?"}
                        ]
                    }
                }
            )
            MockRepo.return_value.save_result = AsyncMock(return_value="review-ref-2")
            MockClient.return_value.create = AsyncMock(return_value=mock_review)

            result = await quality_gate_node(state)

        assert result["revision_count"] == 2  # 1 + 1
        assert result["_quality_verdict"] == "revise"

    @pytest.mark.asyncio
    async def test_invalid_verdict_from_llm_defaults_to_approve(self):
        """LLM이 approve/revise 이외의 값을 반환해도 approve로 처리."""
        state = {
            "job_id": "job-1",
            "questions_ref": "ref-123",
            "revision_count": 0,
        }
        mock_review = QualityReview(
            overall_quality=0.6,
            issues=[],
            suggestions=[],
            verdict="maybe",  # invalid
        )
        with (
            patch(
                "application.nodes.meta.quality_gate.AnalysisRepository"
            ) as MockRepo,
            patch(
                "application.nodes.meta.quality_gate.InstructorClient"
            ) as MockClient,
        ):
            MockRepo.return_value.get_result = AsyncMock(
                return_value={
                    "result_data": {
                        "questions": [
                            {"question_id": "Q-1", "question_text": "Why no pooling?"}
                        ]
                    }
                }
            )
            MockRepo.return_value.save_result = AsyncMock(return_value="review-ref-3")
            MockClient.return_value.create = AsyncMock(return_value=mock_review)

            result = await quality_gate_node(state)

        assert result["_quality_verdict"] == "approve"
        assert result["revision_count"] == 0  # no increment for approve
