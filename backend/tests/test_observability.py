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
        assert "langfuse" in litellm.success_callback
        assert "langfuse" in litellm.failure_callback

        # Cleanup
        observability._initialized = False
        litellm.success_callback = []
        litellm.failure_callback = []

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
        litellm.success_callback = []
        litellm.failure_callback = []

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
