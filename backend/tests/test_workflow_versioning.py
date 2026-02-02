"""Workflow versioning tests."""
import pytest
import inspect


class TestWorkflowVersion:
    def test_version_constant_exists(self):
        from app.workflows.interview_workflow import WORKFLOW_VERSION
        assert isinstance(WORKFLOW_VERSION, str)

    def test_version_semver_format(self):
        from app.workflows.interview_workflow import WORKFLOW_VERSION
        parts = WORKFLOW_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_workflow_uses_patched(self):
        from app.workflows.interview_workflow import InterviewGenerationWorkflow
        source = inspect.getsource(InterviewGenerationWorkflow.run)
        assert "workflow.patched" in source

    def test_workflow_logs_version(self):
        from app.workflows.interview_workflow import InterviewGenerationWorkflow
        source = inspect.getsource(InterviewGenerationWorkflow.run)
        assert "WORKFLOW_VERSION" in source


class TestWorkerBuildId:
    def test_build_id_exists(self):
        from app.worker import WORKER_BUILD_ID
        assert isinstance(WORKER_BUILD_ID, str)

    def test_build_id_contains_version(self):
        from app.worker import WORKER_BUILD_ID
        from app.workflows.interview_workflow import WORKFLOW_VERSION
        assert WORKFLOW_VERSION in WORKER_BUILD_ID

    def test_build_id_prefix(self):
        from app.worker import WORKER_BUILD_ID
        assert WORKER_BUILD_ID.startswith("vantict-worker-v")


class TestHealthVersionInfo:
    def test_health_imports_workflow_version(self):
        source = inspect.getsource(__import__("app.api.health", fromlist=["health"]))
        assert "WORKFLOW_VERSION" in source
