"""
Request Cache 테스트

- 캐시 hit / miss
- TTL 만료
- force_refresh
- 캐시 키 생성
- @cached 데코레이터 동작
"""
from __future__ import annotations

import json

import pytest

from infrastructure.cache.request_cache import RequestCache, _make_key, cached
from tests.helpers.fake_redis import FakeRedis


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def cache(redis: FakeRedis) -> RequestCache:
    return RequestCache(redis, default_ttl=3600)


# ---------------------------------------------------------------------------
# _make_key helper
# ---------------------------------------------------------------------------


class TestMakeKey:
    def test_deterministic_key(self):
        key1 = _make_key("github_meta", {"repo": "test/repo"})
        key2 = _make_key("github_meta", {"repo": "test/repo"})
        assert key1 == key2

    def test_different_params_different_keys(self):
        key1 = _make_key("github_meta", {"repo": "repo-1"})
        key2 = _make_key("github_meta", {"repo": "repo-2"})
        assert key1 != key2

    def test_different_services_different_keys(self):
        key1 = _make_key("github_meta", {"repo": "test/repo"})
        key2 = _make_key("embeddings", {"repo": "test/repo"})
        assert key1 != key2

    def test_key_format(self):
        key = _make_key("github_meta", {"repo": "test"})
        assert key.startswith("cache:github_meta:")
        assert len(key.split(":")[-1]) == 16  # sha256 truncated to 16


# ---------------------------------------------------------------------------
# RequestCache 기본 동작
# ---------------------------------------------------------------------------


class TestRequestCache:
    @pytest.mark.asyncio
    async def test_miss_returns_none(self, cache: RequestCache):
        result = await cache.get("github_meta", {"repo": "nonexistent"})
        assert result is None

    @pytest.mark.asyncio
    async def test_set_then_get_returns_value(self, cache: RequestCache):
        params = {"repo": "test/repo"}
        data = {"stars": 42, "language": "Python"}
        await cache.set("github_meta", params, data)

        result = await cache.get("github_meta", params)
        assert result == data

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache: RequestCache, redis: FakeRedis):
        params = {"repo": "test/repo"}
        await cache.set("github_meta", params, {"data": True}, ttl=120)

        key = _make_key("github_meta", params)
        assert redis._ttl[key] == 120

    @pytest.mark.asyncio
    async def test_invalidate_removes_entry(self, cache: RequestCache):
        params = {"repo": "test/repo"}
        await cache.set("github_meta", params, {"data": True})

        await cache.invalidate("github_meta", params)
        result = await cache.get("github_meta", params)
        assert result is None

    @pytest.mark.asyncio
    async def test_complex_value_serialization(self, cache: RequestCache):
        params = {"query": "complex"}
        data = {
            "repos": [{"name": "repo-1"}, {"name": "repo-2"}],
            "count": 2,
            "nested": {"a": [1, 2, 3]},
        }
        await cache.set("github_meta", params, data)
        result = await cache.get("github_meta", params)
        assert result == data


# ---------------------------------------------------------------------------
# @cached 데코레이터
# ---------------------------------------------------------------------------


class FakeService:
    """캐시 데코레이터 테스트용 서비스."""

    def __init__(self, cache_instance: RequestCache) -> None:
        self._cache = cache_instance
        self.call_count = 0

    @cached("github_meta", ttl=3600)
    async def fetch_metadata(self, repo: str) -> dict:
        self.call_count += 1
        return {"repo": repo, "stars": self.call_count * 10}


class TestCachedDecorator:
    @pytest.mark.asyncio
    async def test_first_call_misses_cache(self, cache: RequestCache):
        svc = FakeService(cache)
        result = await svc.fetch_metadata("test/repo")
        assert result["repo"] == "test/repo"
        assert svc.call_count == 1

    @pytest.mark.asyncio
    async def test_second_call_hits_cache(self, cache: RequestCache):
        svc = FakeService(cache)

        result1 = await svc.fetch_metadata("test/repo")
        result2 = await svc.fetch_metadata("test/repo")

        assert result1 == result2
        assert svc.call_count == 1  # 한 번만 호출됨

    @pytest.mark.asyncio
    async def test_different_args_different_cache(self, cache: RequestCache):
        svc = FakeService(cache)

        r1 = await svc.fetch_metadata("repo-1")
        r2 = await svc.fetch_metadata("repo-2")

        assert r1 != r2
        assert svc.call_count == 2

    @pytest.mark.asyncio
    async def test_force_refresh_bypasses_cache(self, cache: RequestCache):
        svc = FakeService(cache)

        r1 = await svc.fetch_metadata("test/repo")
        r2 = await svc.fetch_metadata("test/repo", force_refresh=True)

        # force_refresh=True → 실제 함수 재호출
        assert svc.call_count == 2
        assert r2["stars"] == 20  # 두 번째 호출 결과

    @pytest.mark.asyncio
    async def test_no_cache_attribute_calls_directly(self):
        """_cache 속성이 없으면 캐시 없이 직접 호출."""

        class NoCacheService:
            def __init__(self):
                self.call_count = 0

            @cached("github_meta")
            async def fetch(self, repo: str) -> dict:
                self.call_count += 1
                return {"repo": repo}

        svc = NoCacheService()
        r1 = await svc.fetch("test")
        r2 = await svc.fetch("test")
        assert svc.call_count == 2  # 캐시 없으므로 매번 호출
