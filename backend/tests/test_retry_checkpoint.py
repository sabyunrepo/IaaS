"""Retry and checkpoint API endpoint tests."""
import pytest


class TestRetryEndpoint:
    def test_retry_route_exists(self):
        from app.api.routes.jobs import retry_job
        assert callable(retry_job)

    def test_retry_request_model(self):
        from app.api.routes.jobs import RetryRequest
        req = RetryRequest()
        assert req.from_step is None
        assert req.force_rerun is False

    def test_retry_request_with_step(self):
        from app.api.routes.jobs import RetryRequest
        req = RetryRequest(from_step="craft_questions", force_rerun=True)
        assert req.from_step == "craft_questions"
        assert req.force_rerun is True


class TestCheckpointEndpoint:
    def test_checkpoint_route_exists(self):
        from app.api.routes.jobs import get_checkpoints
        assert callable(get_checkpoints)

    def test_workflow_steps_defined(self):
        from app.api.routes.jobs import WORKFLOW_STEPS
        assert len(WORKFLOW_STEPS) == 11
        assert "enrich_input" == WORKFLOW_STEPS[0]
        assert "finalize" == WORKFLOW_STEPS[-1]

    def test_workflow_steps_contains_all_phases(self):
        from app.api.routes.jobs import WORKFLOW_STEPS
        required = [
            "enrich_input", "plan", "document_analysis",
            "code_analysis", "jd_analysis", "select_topics",
            "craft_questions", "review_quality", "finalize",
        ]
        for step in required:
            assert step in WORKFLOW_STEPS, f"Missing step: {step}"


class TestCheckpointDB:
    def test_checkpoint_model_importable(self):
        from app.models.database import CheckpointDB
        assert CheckpointDB.__tablename__ == "checkpoints"

    def test_checkpoint_has_required_columns(self):
        from app.models.database import CheckpointDB
        columns = {c.name for c in CheckpointDB.__table__.columns}
        assert {"id", "job_id", "phase", "data", "created_at"} <= columns
