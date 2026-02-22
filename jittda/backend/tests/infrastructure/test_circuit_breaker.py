"""
Circuit Breaker 테스트

- 상태 전이: Closed → Open → Half-Open → Closed
- 실패 임계치 도달 시 Open 전환
- recovery_timeout 경과 후 Half-Open 전환
- Half-Open 성공 시 Closed 복구
- Half-Open 실패 시 Open 재전환
- 동시 Half-Open 호출 수 제한
- CircuitOpenError 발생
- get_stats() 모니터링 정보
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError
from tests.helpers.fake_redis import FakeRedis


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def cb(redis: FakeRedis) -> CircuitBreaker:
    return CircuitBreaker(
        "test-service",
        redis,
        failure_threshold=3,
        recovery_timeout=30,
        half_open_max_calls=1,
    )


# ---------------------------------------------------------------------------
# 기본 상태 (Closed)
# ---------------------------------------------------------------------------


class TestClosedState:
    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, cb: CircuitBreaker):
        assert await cb.get_state() == "closed"

    @pytest.mark.asyncio
    async def test_successful_call_stays_closed(self, cb: CircuitBreaker):
        async def ok_fn():
            return "success"

        result = await cb.call(ok_fn)
        assert result == "success"
        assert await cb.get_state() == "closed"

    @pytest.mark.asyncio
    async def test_single_failure_stays_closed(self, cb: CircuitBreaker):
        async def fail_fn():
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            await cb.call(fail_fn)
        assert await cb.get_state() == "closed"

    @pytest.mark.asyncio
    async def test_success_resets_failure_counter(self, cb: CircuitBreaker, redis: FakeRedis):
        call_count = 0

        async def sometimes_fail():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("fail")
            return "ok"

        # 2 failures
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await cb.call(sometimes_fail)

        # 1 success → resets counter
        result = await cb.call(sometimes_fail)
        assert result == "ok"

        failures_key = "cb:test-service:failures"
        assert redis._data.get(failures_key) is None  # deleted on success


# ---------------------------------------------------------------------------
# Open 전환
# ---------------------------------------------------------------------------


class TestOpenTransition:
    @pytest.mark.asyncio
    async def test_trips_open_after_threshold_failures(self, cb: CircuitBreaker):
        async def fail_fn():
            raise RuntimeError("service down")

        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(fail_fn)

        assert await cb.get_state() == "open"

    @pytest.mark.asyncio
    async def test_open_state_raises_circuit_open_error(self, cb: CircuitBreaker):
        async def fail_fn():
            raise RuntimeError("service down")

        # Trip the breaker
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(fail_fn)

        # Subsequent call should raise CircuitOpenError
        async def ok_fn():
            return "should not reach"

        with pytest.raises(CircuitOpenError) as exc_info:
            await cb.call(ok_fn)
        assert exc_info.value.service_name == "test-service"


# ---------------------------------------------------------------------------
# Half-Open 전환
# ---------------------------------------------------------------------------


class TestHalfOpenTransition:
    @pytest.mark.asyncio
    async def test_transitions_to_half_open_after_timeout(
        self, cb: CircuitBreaker, redis: FakeRedis
    ):
        async def fail_fn():
            raise RuntimeError("down")

        # Trip
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(fail_fn)

        # Simulate timeout by setting opened_at far in the past
        redis._data["cb:test-service:opened_at"] = "0"

        async def ok_fn():
            return "recovered"

        result = await cb.call(ok_fn)
        assert result == "recovered"
        assert await cb.get_state() == "closed"

    @pytest.mark.asyncio
    async def test_half_open_failure_re_trips(
        self, cb: CircuitBreaker, redis: FakeRedis
    ):
        async def fail_fn():
            raise RuntimeError("still down")

        # Trip
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(fail_fn)

        # Simulate timeout
        redis._data["cb:test-service:opened_at"] = "0"

        # Half-open call fails → re-trip
        with pytest.raises(RuntimeError, match="still down"):
            await cb.call(fail_fn)

        assert await cb.get_state() == "open"

    @pytest.mark.asyncio
    async def test_half_open_max_calls_exceeded(
        self, cb: CircuitBreaker, redis: FakeRedis
    ):
        async def fail_fn():
            raise RuntimeError("down")

        # Trip
        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(fail_fn)

        # Simulate half_open state with max calls already reached
        redis._data["cb:test-service:state"] = "half_open"
        redis._data["cb:test-service:half_open_calls"] = "1"

        async def ok_fn():
            return "should not reach"

        with pytest.raises(CircuitOpenError):
            await cb.call(ok_fn)


# ---------------------------------------------------------------------------
# get_stats()
# ---------------------------------------------------------------------------


class TestGetStats:
    @pytest.mark.asyncio
    async def test_returns_monitoring_info(self, cb: CircuitBreaker):
        stats = await cb.get_stats()
        assert stats["service"] == "test-service"
        assert stats["state"] == "closed"
        assert stats["failures"] == 0
        assert stats["threshold"] == 3
        assert stats["recovery_timeout"] == 30

    @pytest.mark.asyncio
    async def test_shows_failure_count(self, cb: CircuitBreaker):
        async def fail_fn():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            await cb.call(fail_fn)

        stats = await cb.get_stats()
        assert stats["failures"] == 1


# ---------------------------------------------------------------------------
# TTL 검증
# ---------------------------------------------------------------------------


class TestTTL:
    @pytest.mark.asyncio
    async def test_trip_sets_ttl_on_keys(self, cb: CircuitBreaker, redis: FakeRedis):
        async def fail_fn():
            raise RuntimeError("down")

        for _ in range(3):
            with pytest.raises(RuntimeError):
                await cb.call(fail_fn)

        # _trip() sets ex=recovery_timeout*3 (30*3=90)
        assert redis._ttl.get("cb:test-service:state") == 90
        assert redis._ttl.get("cb:test-service:opened_at") == 90


# ---------------------------------------------------------------------------
# 함수 인자 전달
# ---------------------------------------------------------------------------


class TestArgumentPassing:
    @pytest.mark.asyncio
    async def test_passes_args_and_kwargs(self, cb: CircuitBreaker):
        async def add(a: int, b: int, *, extra: int = 0) -> int:
            return a + b + extra

        result = await cb.call(add, 3, 5, extra=10)
        assert result == 18
