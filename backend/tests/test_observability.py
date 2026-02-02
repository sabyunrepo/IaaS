"""Langfuse observability integration tests."""
import os
import pytest


class TestObservabilityModule:
    def test_importable(self):
        from app.core.observability import setup_langfuse
        assert callable(setup_langfuse)

    def test_disabled_without_keys(self):
        """Without LANGFUSE keys, setup returns False."""
        from app.core import observability
        observability._initialized = False
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
