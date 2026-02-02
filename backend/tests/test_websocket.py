"""WebSocket progress endpoint tests."""
import pytest


class TestWebSocketRoute:
    def test_ws_route_exists(self):
        from app.api.routes.ws import job_progress_ws
        assert callable(job_progress_ws)

    def test_ws_router_registered(self):
        from app.main import app
        ws_routes = [
            r.path for r in app.routes
            if hasattr(r, "path") and "/ws" in r.path
        ]
        assert "/api/v1/jobs/{job_id}/ws" in ws_routes


class TestValidateApiKey:
    def test_validate_api_key_exists(self):
        from app.api.deps import validate_api_key
        assert callable(validate_api_key)

    def test_validate_api_key_signature(self):
        import inspect
        from app.api.deps import validate_api_key
        sig = inspect.signature(validate_api_key)
        params = list(sig.parameters.keys())
        assert "token" in params
        assert "db" in params
