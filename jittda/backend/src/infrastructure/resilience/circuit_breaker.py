"""
Circuit Breaker — 외부 서비스 복원력 패턴.

상태 머신: Closed → Open → Half-Open → Closed
Redis 기반 상태 저장 (Temporal Worker 다중 프로세스 간 공유).

사용 예:
    cb = CircuitBreaker("github", redis_client)
    result = await cb.call(github_client.fetch_profile, "username")
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# 환경변수 오버라이드 가능한 기본값
_DEFAULT_FAILURE_THRESHOLD = int(os.environ.get("CB_FAILURE_THRESHOLD", "5"))
_DEFAULT_RECOVERY_TIMEOUT = int(os.environ.get("CB_RECOVERY_TIMEOUT", "60"))
_DEFAULT_HALF_OPEN_MAX_CALLS = int(os.environ.get("CB_HALF_OPEN_MAX_CALLS", "2"))


class CircuitOpenError(Exception):
    """Circuit이 Open 상태일 때 호출 차단."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker open for {service_name}")


class CircuitBreaker:
    """Redis 기반 비동기 Circuit Breaker.

    Args:
        service_name: 서비스 식별자 (Redis 키 prefix).
        redis: redis.asyncio 클라이언트.
        failure_threshold: Open 전환까지의 연속 실패 횟수.
        recovery_timeout: Open → Half-Open 전환 대기 시간(초).
        half_open_max_calls: Half-Open에서 허용할 테스트 호출 수.
    """

    # Redis 키 패턴
    _KEY_STATE = "cb:{name}:state"
    _KEY_FAILURES = "cb:{name}:failures"
    _KEY_OPENED_AT = "cb:{name}:opened_at"
    _KEY_HALF_OPEN_CALLS = "cb:{name}:half_open_calls"

    def __init__(
        self,
        service_name: str,
        redis: Any,
        *,
        failure_threshold: int = _DEFAULT_FAILURE_THRESHOLD,
        recovery_timeout: int = _DEFAULT_RECOVERY_TIMEOUT,
        half_open_max_calls: int = _DEFAULT_HALF_OPEN_MAX_CALLS,
    ):
        self._name = service_name
        self._redis = redis
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max_calls = half_open_max_calls

    def _key(self, pattern: str) -> str:
        return pattern.format(name=self._name)

    async def get_state(self) -> str:
        """현재 상태를 반환한다 (closed/open/half_open)."""
        raw = await self._redis.get(self._key(self._KEY_STATE))
        if raw is None:
            return "closed"
        return raw if isinstance(raw, str) else raw.decode()

    async def call(
        self,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Circuit Breaker를 통해 함수를 호출한다.

        Raises:
            CircuitOpenError: Circuit이 Open이고 recovery_timeout 미경과.
        """
        state = await self.get_state()

        if state == "open":
            if await self._should_try_half_open():
                return await self._try_half_open(fn, *args, **kwargs)
            raise CircuitOpenError(self._name)

        if state == "half_open":
            return await self._try_half_open(fn, *args, **kwargs)

        # closed: 정상 호출
        try:
            result = await fn(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    async def _should_try_half_open(self) -> bool:
        """recovery_timeout이 경과했는지 확인."""
        raw = await self._redis.get(self._key(self._KEY_OPENED_AT))
        if raw is None:
            return True
        opened_at = float(raw if isinstance(raw, str) else raw.decode())
        return (time.time() - opened_at) >= self._recovery_timeout

    async def _try_half_open(
        self,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Half-Open 상태에서 테스트 호출.

        Pipeline으로 상태 전환 + 호출 카운터 증가를 원자적으로 수행하여
        다중 Worker 간 race condition을 방지한다.
        """
        key_state = self._key(self._KEY_STATE)
        key_calls = self._key(self._KEY_HALF_OPEN_CALLS)
        ttl = self._recovery_timeout * 3

        # 원자적 상태 전환 + 카운터 증가
        pipe = self._redis.pipeline()
        pipe.set(key_state, "half_open", ex=ttl)
        pipe.incr(key_calls)
        pipe.expire(key_calls, ttl)
        results = await pipe.execute()

        current = results[1]  # incr 결과
        if current > self._half_open_max_calls:
            raise CircuitOpenError(self._name)

        try:
            result = await fn(*args, **kwargs)
            # 성공 → Closed로 복구
            await self._reset()
            logger.info("Circuit breaker %s recovered (closed)", self._name)
            return result
        except Exception:
            # 실패 → Open으로 재전환
            await self._trip()
            raise

    async def _on_success(self) -> None:
        """호출 성공 시 실패 카운터 리셋."""
        await self._redis.delete(self._key(self._KEY_FAILURES))

    async def _on_failure(self) -> None:
        """호출 실패 시 카운터 증가, 임계치 도달 시 Open 전환."""
        key = self._key(self._KEY_FAILURES)
        failures = await self._redis.incr(key)
        # TTL 설정 (recovery_timeout * 2 후 자동 만료)
        await self._redis.expire(key, self._recovery_timeout * 2)

        if failures >= self._failure_threshold:
            await self._trip()
            logger.warning(
                "Circuit breaker %s tripped (open) after %d failures",
                self._name,
                failures,
            )

    async def _trip(self) -> None:
        """Circuit을 Open 상태로 전환.

        모든 키에 TTL(recovery_timeout * 3)을 설정하여
        Redis 키 누수를 방지한다.
        """
        ttl = self._recovery_timeout * 3
        pipe = self._redis.pipeline()
        pipe.set(self._key(self._KEY_STATE), "open", ex=ttl)
        pipe.set(self._key(self._KEY_OPENED_AT), str(time.time()), ex=ttl)
        pipe.delete(self._key(self._KEY_HALF_OPEN_CALLS))
        await pipe.execute()
        _update_metrics(self._name, "open")

    async def _reset(self) -> None:
        """Circuit을 Closed 상태로 리셋.

        state 키를 삭제한다 (get_state()에서 None → "closed" 처리).
        불필요한 영구 키 누적을 방지.
        """
        pipe = self._redis.pipeline()
        pipe.delete(self._key(self._KEY_STATE))
        pipe.delete(self._key(self._KEY_FAILURES))
        pipe.delete(self._key(self._KEY_OPENED_AT))
        pipe.delete(self._key(self._KEY_HALF_OPEN_CALLS))
        await pipe.execute()
        _update_metrics(self._name, "closed")

    async def get_stats(self) -> dict[str, Any]:
        """모니터링용 상태 정보를 반환한다."""
        state = await self.get_state()
        raw_failures = await self._redis.get(self._key(self._KEY_FAILURES))
        failures = int(raw_failures) if raw_failures else 0
        return {
            "service": self._name,
            "state": state,
            "failures": failures,
            "threshold": self._failure_threshold,
            "recovery_timeout": self._recovery_timeout,
        }


def _update_metrics(service_name: str, state: str) -> None:
    """Prometheus 메트릭 업데이트 (prometheus-client 미설치 시 no-op)."""
    try:
        from infrastructure.observability.metrics import (
            circuit_breaker_trips_total,
            update_circuit_breaker_metric,
        )

        update_circuit_breaker_metric(service_name, state)
        if state == "open":
            circuit_breaker_trips_total.labels(service=service_name).inc()
    except ImportError:
        pass
