"""Unit tests for webhook callback activity."""
import pytest


class TestSendWebhookImport:
    def test_importable(self):
        from app.workflows.activities.send_webhook import send_webhook
        assert callable(send_webhook)

    def test_is_activity(self):
        from app.workflows.activities.send_webhook import send_webhook
        assert hasattr(send_webhook, "__temporal_activity_definition")

    def test_registered_in_worker(self):
        from app.worker import ACTIVITIES
        names = [a.__name__ for a in ACTIVITIES]
        assert "send_webhook" in names

    def test_workflow_imports_webhook(self):
        """Verify workflow file imports send_webhook."""
        import inspect
        from app.workflows import interview_workflow
        source = inspect.getsource(interview_workflow)
        assert "send_webhook" in source
        assert "callback_url" in source
