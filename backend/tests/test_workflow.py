"""Unit tests for workflow and activity registration."""
import pytest
from app.worker import ACTIVITIES
from app.workflows.interview_workflow import InterviewGenerationWorkflow
from app.models.enums import JobStatus


class TestActivityRegistration:
    def test_all_activities_registered(self):
        names = [a.__name__ for a in ACTIVITIES]
        expected = [
            "enrich_input",
            "create_execution_plan",
            "analyze_documents",
            "analyze_code",
            "analyze_jd",
            "select_topics",
            "craft_question",
            "review_questions",
            "finalize_output",
            "persist_result",
            "send_webhook",
        ]
        assert names == expected

    def test_activity_count(self):
        assert len(ACTIVITIES) == 11


class TestWorkflow:
    def test_workflow_importable(self):
        assert InterviewGenerationWorkflow is not None

    def test_workflow_has_run_method(self):
        assert hasattr(InterviewGenerationWorkflow, "run")


class TestJobStatusCompleteness:
    def test_all_phases_covered(self):
        statuses = [s.value for s in JobStatus]
        required = ["pending", "completed", "failed"]
        for r in required:
            assert r in statuses
