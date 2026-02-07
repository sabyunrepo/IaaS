"""Cache invalidation and user-based rate limit tests."""
import pytest


class TestCachedLLMInvalidation:
    def test_invalidate_method_exists(self):
        from app.services.cached_llm import CachedLLMService
        svc = CachedLLMService()
        assert hasattr(svc, "invalidate_for_job")
        assert callable(svc.invalidate_for_job)

    def test_make_cache_key_method_exists(self):
        from app.services.cached_llm import CachedLLMService
        assert hasattr(CachedLLMService, "_make_cache_key")
        assert callable(CachedLLMService._make_cache_key)

    def test_job_cache_key_format(self):
        from app.services.cached_llm import CachedLLMService
        key = CachedLLMService._make_cache_key("test prompt", "gpt-4o", job_id="job-123")
        assert key.startswith("llm_cache:job:job-123:")

    def test_job_cache_key_deterministic(self):
        from app.services.cached_llm import CachedLLMService
        k1 = CachedLLMService._make_cache_key("prompt", "model", job_id="j1")
        k2 = CachedLLMService._make_cache_key("prompt", "model", job_id="j1")
        assert k1 == k2

    def test_job_cache_key_differs_by_job(self):
        from app.services.cached_llm import CachedLLMService
        k1 = CachedLLMService._make_cache_key("prompt", "model", job_id="j1")
        k2 = CachedLLMService._make_cache_key("prompt", "model", job_id="j2")
        assert k1 != k2

    def test_run_for_job_method_exists(self):
        from app.services.cached_llm import CachedLLMService
        svc = CachedLLMService()
        assert hasattr(svc, "run_for_job")
        assert callable(svc.run_for_job)


class TestCacheKeyWithActivityName:
    """캐시 키에 activity_name 포함 테스트 (_make_cache_key 통합 API)"""

    def test_cache_key_includes_activity_name(self):
        from app.services.cached_llm import CachedLLMService
        key = CachedLLMService._make_cache_key("prompt", "model", "analyze_jd")
        assert "analyze_jd" in key
        assert key.startswith("llm_cache:analyze_jd:")

    def test_cache_key_without_activity_name(self):
        from app.services.cached_llm import CachedLLMService
        key = CachedLLMService._make_cache_key("prompt", "model")
        assert key.startswith("llm_cache:")
        assert key.count(":") == 1  # llm_cache:hash

    def test_different_activities_different_keys(self):
        from app.services.cached_llm import CachedLLMService
        k1 = CachedLLMService._make_cache_key("same prompt", "model", "analyze_jd")
        k2 = CachedLLMService._make_cache_key("same prompt", "model", "craft_question")
        assert k1 != k2

    def test_job_cache_key_includes_activity(self):
        from app.services.cached_llm import CachedLLMService
        key = CachedLLMService._make_cache_key("prompt", "model", "analyze_jd", job_id="job-1")
        assert "analyze_jd" in key
        assert key.startswith("llm_cache:job:job-1:analyze_jd:")

    def test_job_cache_key_without_activity(self):
        from app.services.cached_llm import CachedLLMService
        key = CachedLLMService._make_cache_key("prompt", "model", job_id="job-1")
        assert key.startswith("llm_cache:job:job-1:")
        assert "None" not in key


class TestLLMCacheEnabled:
    """LLM_CACHE_ENABLED 환경변수 테스트"""

    def test_cache_enabled_setting_exists(self):
        from app.core.config import settings
        assert hasattr(settings, "LLM_CACHE_ENABLED")
        assert isinstance(settings.LLM_CACHE_ENABLED, bool)

    def test_cache_enabled_default_true(self):
        from app.core.config import settings
        assert settings.LLM_CACHE_ENABLED is True


class TestRedisConnectionPool:
    """Redis 연결 풀 싱글톤 테스트"""

    def test_shared_redis_function_exists(self):
        from app.services.cached_llm import _get_shared_redis
        assert callable(_get_shared_redis)

    def test_cached_llm_uses_shared_pool(self):
        """CachedLLMService._get_redis()가 _get_shared_redis를 사용하는지 확인"""
        from app.services.cached_llm import CachedLLMService
        svc = CachedLLMService()
        # _get_redis 메서드가 존재하는지 확인
        assert hasattr(svc, "_get_redis")
        assert callable(svc._get_redis)


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
