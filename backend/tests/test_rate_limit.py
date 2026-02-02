"""Rate limiting configuration tests."""
import pytest

from app.core.rate_limit import limiter


class TestRateLimitConfig:
    def test_limiter_importable(self):
        assert limiter is not None

    def test_default_limits(self):
        assert limiter._default_limits is not None

    def test_key_func_set(self):
        assert limiter._key_func is not None


class TestRateLimitIntegration:
    def test_main_registers_limiter(self):
        from app.main import app
        assert hasattr(app.state, "limiter")
        assert app.state.limiter is limiter

    def test_rate_limit_exception_handler(self):
        from slowapi.errors import RateLimitExceeded
        from app.main import app
        handlers = app.exception_handlers
        assert RateLimitExceeded in handlers

    def test_create_job_has_rate_limit(self):
        from app.api.routes.jobs import create_job
        # slowapi adds _rate_limit attribute to decorated functions
        assert hasattr(create_job, "__wrapped__") or hasattr(create_job, "_rate_limit")

    def test_jobs_router_request_param(self):
        """create_job must accept Request as first param for slowapi."""
        import inspect
        from app.api.routes.jobs import create_job
        sig = inspect.signature(create_job)
        params = list(sig.parameters.keys())
        assert "request" in params
