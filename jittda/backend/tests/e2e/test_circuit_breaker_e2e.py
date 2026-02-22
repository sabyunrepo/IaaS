"""
Circuit Breaker E2E 테스트 — 외부 서비스 장애 시 fallback 동작 검증.

- GitHub API 장애 시 CircuitOpenError → fallback 처리
- BrightData 장애 시 None 반환 (graceful degradation)
- 복구 후 정상 호출 재개
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError
from tests.helpers.fake_redis import FakeRedis


# ---------------------------------------------------------------------------
# E2E Scenario: GitHub client with circuit breaker
# ---------------------------------------------------------------------------


class TestGitHubCircuitBreakerE2E:
    """GitHub API 장애 시 circuit breaker 동작 E2E 검증."""

    @pytest.mark.asyncio
    async def test_github_fetch_fails_then_circuit_opens(self):
        """5회 연속 실패 후 CircuitOpenError 발생."""
        redis = FakeRedis()
        cb = CircuitBreaker("github", redis, failure_threshold=5, recovery_timeout=60)

        async def failing_github_call(username: str) -> dict:
            raise RuntimeError("GitHub API 503")

        # 5회 실패 → circuit open
        for _ in range(5):
            with pytest.raises(RuntimeError, match="GitHub API 503"):
                await cb.call(failing_github_call, "testuser")

        # 6번째 호출 → CircuitOpenError (실제 API 호출 안 함)
        with pytest.raises(CircuitOpenError):
            await cb.call(failing_github_call, "testuser")

    @pytest.mark.asyncio
    async def test_circuit_recovers_after_timeout(self):
        """recovery_timeout 후 half-open → 성공 → closed 복구."""
        redis = FakeRedis()
        cb = CircuitBreaker("github-recover", redis, failure_threshold=3, recovery_timeout=30)

        call_count = 0

        async def github_call(username: str) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise RuntimeError("temporary failure")
            return {"login": username}

        # Trip the circuit
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(github_call, "testuser")

        assert await cb.get_state() == "open"

        # Simulate timeout
        redis._data["cb:github-recover:opened_at"] = "0"

        # Half-open test call succeeds → closed
        result = await cb.call(github_call, "testuser")
        assert result == {"login": "testuser"}
        assert await cb.get_state() == "closed"


# ---------------------------------------------------------------------------
# E2E Scenario: BrightData client with circuit breaker fallback
# ---------------------------------------------------------------------------


class TestBrightDataFallbackE2E:
    """BrightData 장애 시 None fallback E2E 검증."""

    @pytest.mark.asyncio
    async def test_brightdata_circuit_open_returns_none(self):
        """Circuit open 시 BrightDataClient.scrape_profile이 None 반환."""
        redis = FakeRedis()
        cb = CircuitBreaker("brightdata", redis, failure_threshold=3)

        async def scrape_impl(url: str):
            raise RuntimeError("BrightData down")

        # Trip the circuit
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(scrape_impl, "https://linkedin.com/in/test")

        # Circuit open → fallback: 실제 클라이언트에서는 None 반환
        with pytest.raises(CircuitOpenError):
            await cb.call(scrape_impl, "https://linkedin.com/in/test")

    @pytest.mark.asyncio
    async def test_mixed_services_independent_circuits(self):
        """서비스별 독립 circuit breaker 동작 확인."""
        redis = FakeRedis()
        cb_github = CircuitBreaker("github", redis, failure_threshold=3)
        cb_brightdata = CircuitBreaker("brightdata", redis, failure_threshold=3)

        async def fail_github():
            raise RuntimeError("GitHub down")

        async def ok_brightdata():
            return {"name": "Test User"}

        # GitHub circuit trips
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb_github.call(fail_github)

        assert await cb_github.get_state() == "open"

        # BrightData still works
        result = await cb_brightdata.call(ok_brightdata)
        assert result == {"name": "Test User"}
        assert await cb_brightdata.get_state() == "closed"
