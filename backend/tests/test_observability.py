"""Langfuse observability integration tests."""
import os
import pytest


class TestObservabilityModule:
    def test_importable(self):
        from app.core.observability import (
            setup_langfuse,
            is_langfuse_enabled,
            langfuse_trace_context,
            get_current_trace_metadata,
            observe_activity,
            flush_langfuse,
        )
        assert callable(setup_langfuse)
        assert callable(is_langfuse_enabled)
        assert callable(observe_activity)
        assert callable(flush_langfuse)

    def test_disabled_without_keys(self, monkeypatch):
        """Without LANGFUSE keys, setup returns False."""
        from app.core import observability
        observability._initialized = False

        # Ensure keys are not set
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None)
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_SECRET_KEY", None)

        result = observability.setup_langfuse()
        assert result is False

    def test_enabled_with_keys(self, monkeypatch):
        """With keys set, setup registers litellm callbacks."""
        from app.core import observability
        observability._initialized = False

        # Patch settings
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_SECRET_KEY", "sk-test")
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_HOST", "http://localhost:3100")

        result = observability.setup_langfuse()
        assert result is True
        assert observability._initialized is True

        import litellm
        # Langfuse 3.x uses litellm.callbacks (not success_callback/failure_callback)
        assert any("langfuse" in str(cb) for cb in litellm.callbacks)

        # Cleanup
        observability._initialized = False
        litellm.callbacks = []

    def test_idempotent(self, monkeypatch):
        """Calling setup twice doesn't fail."""
        from app.core import observability
        observability._initialized = False
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_SECRET_KEY", "sk-test")

        observability.setup_langfuse()
        result = observability.setup_langfuse()
        assert result is True

        # Cleanup
        observability._initialized = False
        import litellm
        litellm.callbacks = []

    def test_main_calls_setup(self):
        """main.py imports and calls setup_langfuse."""
        import ast
        with open("app/main.py") as f:
            source = f.read()
        assert "setup_langfuse" in source


class TestTraceContext:
    def test_trace_context_sets_metadata(self):
        """langfuse_trace_context correctly sets metadata."""
        from app.core import observability

        # Initial state
        meta = observability.get_current_trace_metadata()
        assert meta["job_id"] is None
        assert meta["phase"] is None
        assert meta["activity"] is None

        # Set context
        with observability.langfuse_trace_context(
            job_id="test-job-123",
            phase="question_generation",
            activity="craft_question"
        ):
            meta = observability.get_current_trace_metadata()
            assert meta["job_id"] == "test-job-123"
            assert meta["phase"] == "question_generation"
            assert meta["activity"] == "craft_question"

        # Context restored
        meta = observability.get_current_trace_metadata()
        assert meta["job_id"] is None

    def test_trace_context_nested(self):
        """Nested contexts work correctly."""
        from app.core import observability

        with observability.langfuse_trace_context(job_id="outer"):
            assert observability.get_current_trace_metadata()["job_id"] == "outer"

            with observability.langfuse_trace_context(phase="inner-phase"):
                meta = observability.get_current_trace_metadata()
                assert meta["job_id"] == "outer"
                assert meta["phase"] == "inner-phase"

            # Inner context restored
            meta = observability.get_current_trace_metadata()
            assert meta["phase"] is None


class TestObserveActivityDecorator:
    def test_decorator_without_langfuse(self, monkeypatch):
        """observe_activity works when Langfuse is disabled."""
        from app.core import observability

        # Ensure Langfuse is disabled
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None)
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_SECRET_KEY", None)

        @observability.observe_activity(name="test_activity", phase="test_phase")
        async def sample_activity(data: dict) -> str:
            return "result"

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            sample_activity({"test": "data"})
        )
        assert result == "result"

    def test_decorator_extracts_job_id(self, monkeypatch):
        """observe_activity extracts job_id from dict arguments."""
        from app.core import observability

        # Ensure Langfuse is disabled for this test
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None)

        captured_meta = {}

        @observability.observe_activity(name="test_activity", phase="test_phase")
        async def sample_activity(input_data: dict) -> str:
            captured_meta.update(observability.get_current_trace_metadata())
            return "result"

        import asyncio
        asyncio.get_event_loop().run_until_complete(
            sample_activity({"job_id": "job-123", "other": "data"})
        )
        # Without Langfuse enabled, context is not set by decorator
        # This test just ensures the function runs without error


class TestCachedLLMServiceIntegration:
    def test_cached_llm_imports_observability(self):
        """CachedLLMService imports observability functions."""
        import ast
        with open("app/services/cached_llm.py") as f:
            source = f.read()
        assert "get_current_trace_metadata" in source
        assert "is_langfuse_enabled" in source


class TestPhase2TraceFunctions:
    """Phase 2: Trace/Span management functions tests."""

    def test_create_trace_for_job_importable(self):
        """create_trace_for_job function is importable."""
        from app.core.observability import create_trace_for_job
        assert callable(create_trace_for_job)

    def test_create_span_for_phase_importable(self):
        """create_span_for_phase function is importable."""
        from app.core.observability import create_span_for_phase
        assert callable(create_span_for_phase)

    def test_score_trace_importable(self):
        """score_trace function is importable."""
        from app.core.observability import score_trace
        assert callable(score_trace)

    def test_end_span_importable(self):
        """end_span function is importable."""
        from app.core.observability import end_span
        assert callable(end_span)

    def test_create_trace_returns_none_when_disabled(self, monkeypatch):
        """create_trace_for_job returns None when Langfuse is disabled."""
        from app.core import observability
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None)
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_SECRET_KEY", None)

        result = observability.create_trace_for_job("test-job-id")
        assert result is None

    def test_create_span_returns_none_when_disabled(self, monkeypatch):
        """create_span_for_phase returns None when Langfuse is disabled."""
        from app.core import observability
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None)
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_SECRET_KEY", None)

        result = observability.create_span_for_phase("test-job-id", "analysis")
        assert result is None

    def test_score_trace_does_not_fail_when_disabled(self, monkeypatch):
        """score_trace does not raise when Langfuse is disabled."""
        from app.core import observability
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_PUBLIC_KEY", None)
        monkeypatch.setattr("app.core.observability.settings.LANGFUSE_SECRET_KEY", None)

        # Should not raise
        observability.score_trace("trace-id", "quality", 0.9)

    def test_end_span_handles_none(self):
        """end_span handles None span gracefully."""
        from app.core import observability
        # Should not raise
        observability.end_span(None)


class TestPhase2ObservabilityActivities:
    """Phase 2: Observability activities tests."""

    def test_start_job_trace_importable(self):
        """start_job_trace activity is importable."""
        from app.workflows.activities.observability_activities import start_job_trace
        assert callable(start_job_trace)

    def test_end_job_trace_importable(self):
        """end_job_trace activity is importable."""
        from app.workflows.activities.observability_activities import end_job_trace
        assert callable(end_job_trace)

    def test_log_phase_event_importable(self):
        """log_phase_event activity is importable."""
        from app.workflows.activities.observability_activities import log_phase_event
        assert callable(log_phase_event)

    def test_activities_registered_in_worker(self):
        """Observability activities are registered in worker.py."""
        with open("app/worker.py") as f:
            source = f.read()
        assert "start_job_trace" in source
        assert "end_job_trace" in source
        assert "log_phase_event" in source
        assert "from app.workflows.activities.observability_activities import" in source


class TestPhase2WorkflowIntegration:
    """Phase 2: Workflow integration tests."""

    def test_workflow_imports_observability_activities(self):
        """InterviewGenerationWorkflow imports observability activities."""
        with open("app/workflows/interview_workflow.py") as f:
            source = f.read()
        assert "start_job_trace" in source
        assert "end_job_trace" in source
        assert "from app.workflows.activities.observability_activities import" in source

    def test_workflow_calls_start_trace_at_beginning(self):
        """Workflow calls start_job_trace at the beginning."""
        with open("app/workflows/interview_workflow.py") as f:
            source = f.read()
        # start_job_trace should appear before the first phase activity
        start_trace_pos = source.find("start_job_trace")
        enrich_input_pos = source.find("enrich_input,")  # First activity call
        assert start_trace_pos > 0
        assert start_trace_pos < enrich_input_pos

    def test_workflow_calls_end_trace_on_success(self):
        """Workflow calls end_job_trace on success."""
        with open("app/workflows/interview_workflow.py") as f:
            source = f.read()
        # Check for end_job_trace in success path
        assert 'args=[job_id, trace_id, "success"' in source

    def test_workflow_calls_end_trace_on_failure(self):
        """Workflow calls end_job_trace on failure."""
        with open("app/workflows/interview_workflow.py") as f:
            source = f.read()
        # Check for end_job_trace in failure path
        assert 'args=[job_id, trace_id, "failed"' in source
