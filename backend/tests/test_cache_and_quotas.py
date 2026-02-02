"""Cache invalidation and user-based rate limit tests."""
import pytest


class TestCachedLLMInvalidation:
    def test_invalidate_method_exists(self):
        from app.services.cached_llm import CachedLLMService
        svc = CachedLLMService()
        assert hasattr(svc, "invalidate_for_job")
        assert callable(svc.invalidate_for_job)

    def test_job_cache_key_method_exists(self):
        from app.services.cached_llm import CachedLLMService
        svc = CachedLLMService()
        assert hasattr(svc, "_job_cache_key")

    def test_job_cache_key_format(self):
        from app.services.cached_llm import CachedLLMService
        svc = CachedLLMService()
        key = svc._job_cache_key("job-123", "test prompt", "gpt-4o")
        assert key.startswith("llm_cache:job:job-123:")

    def test_job_cache_key_deterministic(self):
        from app.services.cached_llm import CachedLLMService
        svc = CachedLLMService()
        k1 = svc._job_cache_key("j1", "prompt", "model")
        k2 = svc._job_cache_key("j1", "prompt", "model")
        assert k1 == k2

    def test_job_cache_key_differs_by_job(self):
        from app.services.cached_llm import CachedLLMService
        svc = CachedLLMService()
        k1 = svc._job_cache_key("j1", "prompt", "model")
        k2 = svc._job_cache_key("j2", "prompt", "model")
        assert k1 != k2

    def test_run_for_job_method_exists(self):
        from app.services.cached_llm import CachedLLMService
        svc = CachedLLMService()
        assert hasattr(svc, "run_for_job")
        assert callable(svc.run_for_job)


class TestRateLimitKeyFunc:
    def test_key_func_exists(self):
        from app.core.rate_limit import _get_rate_limit_key
        assert callable(_get_rate_limit_key)

    def test_plan_limits_defined(self):
        from app.core.rate_limit import PLAN_LIMITS
        assert "free" in PLAN_LIMITS
        assert "pro" in PLAN_LIMITS
        assert "enterprise" in PLAN_LIMITS

    def test_job_create_limit(self):
        from app.core.rate_limit import JOB_CREATE_LIMIT
        assert "minute" in JOB_CREATE_LIMIT

    def test_job_create_limit_free(self):
        from app.core.rate_limit import JOB_CREATE_LIMIT_FREE
        assert "day" in JOB_CREATE_LIMIT_FREE

    def test_limiter_uses_custom_key_func(self):
        from app.core.rate_limit import limiter, _get_rate_limit_key
        assert limiter._key_func == _get_rate_limit_key
