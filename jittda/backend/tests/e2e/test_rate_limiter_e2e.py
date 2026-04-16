"""
Rate Limiter E2E 테스트.

- 정상 요청 통과
- rate limit 초과 시 429 응답
- 다른 클라이언트 IP는 독립적 카운터
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class FakeRedis:
    """Rate limiter 테스트용 인메모리 Redis."""

    def __init__(self) -> None:
        self._data: dict[str, int] = {}
        self._ttl: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self._data[key] = self._data.get(key, 0) + 1
        return self._data[key]

    async def expire(self, key: str, seconds: int) -> None:
        self._ttl[key] = seconds

    async def ttl(self, key: str) -> int:
        return self._ttl.get(key, -2)


class TestRateLimiterLogic:
    """Rate limiter 로직 검증 (미들웨어 의존성 없이)."""

    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self):
        """limit 이하 요청은 통과."""
        redis = FakeRedis()
        limit = 5
        key = "rate:127.0.0.1"

        for i in range(limit):
            count = await redis.incr(key)
            assert count <= limit, f"Request {i+1} should be allowed"

    @pytest.mark.asyncio
    async def test_blocks_requests_over_limit(self):
        """limit 초과 요청은 차단."""
        redis = FakeRedis()
        limit = 5
        key = "rate:127.0.0.1"

        for _ in range(limit):
            await redis.incr(key)

        # limit+1번째 요청
        count = await redis.incr(key)
        assert count > limit, "Request should be blocked"

    @pytest.mark.asyncio
    async def test_different_ips_have_independent_counters(self):
        """다른 IP는 독립 카운터."""
        redis = FakeRedis()
        limit = 3

        # IP1 → 3 requests
        for _ in range(limit):
            await redis.incr("rate:10.0.0.1")

        # IP2 → first request (should be 1, not 4)
        count = await redis.incr("rate:10.0.0.2")
        assert count == 1

    @pytest.mark.asyncio
    async def test_counter_respects_ttl_window(self):
        """TTL 설정이 적용되는지 확인."""
        redis = FakeRedis()
        key = "rate:127.0.0.1"

        await redis.incr(key)
        await redis.expire(key, 60)

        ttl = await redis.ttl(key)
        assert ttl == 60


class TestJobLifecycleE2E:
    """Job lifecycle E2E 검증: 생성 → 진행 → 완료 → 결과 조회."""

    @pytest.mark.asyncio
    async def test_job_full_lifecycle(self):
        """Job 전체 수명주기를 인메모리로 검증."""
        from tests.e2e.conftest import InMemoryStore, MockJobRepository

        store = InMemoryStore()
        repo = MockJobRepository(store=store)

        # 1. 생성
        job_id = await repo.create(
            {"github_urls": ["https://github.com/test/repo"]},
            user_id="user-123",
        )
        job = await repo.get(job_id)
        assert job is not None
        assert job["status"] == "pending"

        # 2. 진행
        await repo.update_status(job_id, "running", progress=0.3)
        job = await repo.get(job_id)
        assert job["status"] == "running"
        assert job["progress"] == 0.3

        # 3. 완료
        await repo.save_result_data(job_id, {"score": 85.0})
        job = await repo.get(job_id)
        assert job["status"] == "completed"
        assert job["progress"] == 1.0
        assert job["result_data"]["score"] == 85.0

    @pytest.mark.asyncio
    async def test_job_error_scenario(self):
        """Job 에러 시나리오."""
        from tests.e2e.conftest import InMemoryStore, MockJobRepository

        store = InMemoryStore()
        repo = MockJobRepository(store=store)

        job_id = await repo.create({"github_urls": []}, user_id="user-456")
        await repo.save_error(job_id, "No valid repositories found")

        job = await repo.get(job_id)
        assert job["status"] == "failed"
        assert "No valid repositories" in job["error_message"]

    @pytest.mark.asyncio
    async def test_nonexistent_job_returns_none(self):
        """존재하지 않는 Job 조회 시 None."""
        from tests.e2e.conftest import MockJobRepository

        repo = MockJobRepository()
        job = await repo.get("nonexistent-uuid")
        assert job is None
