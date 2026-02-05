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
            "analyze_single_repo",      # HYBRID 3-Stage 단일 레포 분석
            "validate_code_analysis",   # 코드 분석 품질 검증
            "analyze_jd",
            "select_topics",
            "craft_question",
            "enhance_terminology",
            "craft_evaluation_scenarios",
            "design_follow_ups",
            "generate_interviewer_notes",
            "generate_decision_guide",
            "revise_questions",
            "review_questions",
            "finalize_output",
            "persist_result",
            "send_webhook",
            # Observability activities (Phase 2 Langfuse)
            "start_job_trace",
            "end_job_trace",
            "log_phase_event",
            # Knowledge Graph activities
            "build_knowledge_graph",
            "get_kg_question_candidates",
            "get_evidence_chain",
            "clear_knowledge_graph",
            # v2 Generation activities
            "generate_intel_brief",
            "generate_deep_analysis",
            "generate_decision_support",
        ]
        assert names == expected

    def test_activity_count(self):
        assert len(ACTIVITIES) == 29


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
