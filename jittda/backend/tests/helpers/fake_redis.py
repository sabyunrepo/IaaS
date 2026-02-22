"""
FakeRedis — 테스트용 인메모리 Redis + Pipeline Mock.

Redis 의존 모듈(CircuitBreaker, RequestCache 등)의 단위 테스트에서 사용.
"""
from __future__ import annotations


class FakeRedis:
    """인메모리 Redis mock — get/set/incr/delete/expire/pipeline/ttl 지원."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}
        self._ttl: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return self._data.get(key)

    async def set(self, key: str, value: str, *, ex: int | None = None) -> None:
        self._data[key] = str(value)
        if ex:
            self._ttl[key] = ex

    async def incr(self, key: str) -> int:
        current = int(self._data.get(key, "0"))
        current += 1
        self._data[key] = str(current)
        return current

    async def delete(self, *keys: str) -> None:
        for key in keys:
            self._data.pop(key, None)
            self._ttl.pop(key, None)

    async def expire(self, key: str, seconds: int) -> None:
        self._ttl[key] = seconds

    async def ttl(self, key: str) -> int:
        return self._ttl.get(key, -2)

    async def ping(self) -> bool:
        return True

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)


class FakePipeline:
    """Pipeline mock — 명령을 순차 실행."""

    def __init__(self, redis: FakeRedis) -> None:
        self._redis = redis
        self._commands: list[tuple] = []

    def set(self, key: str, value: str, *, ex: int | None = None) -> FakePipeline:
        self._commands.append(("set", key, value, ex))
        return self

    def incr(self, key: str) -> FakePipeline:
        self._commands.append(("incr", key))
        return self

    def delete(self, key: str) -> FakePipeline:
        self._commands.append(("delete", key))
        return self

    def expire(self, key: str, seconds: int) -> FakePipeline:
        self._commands.append(("expire", key, seconds))
        return self

    async def execute(self) -> list:
        results = []
        for cmd in self._commands:
            if cmd[0] == "set":
                await self._redis.set(cmd[1], cmd[2], ex=cmd[3])
                results.append(True)
            elif cmd[0] == "incr":
                val = await self._redis.incr(cmd[1])
                results.append(val)
            elif cmd[0] == "delete":
                await self._redis.delete(cmd[1])
                results.append(1)
            elif cmd[0] == "expire":
                await self._redis.expire(cmd[1], cmd[2])
                results.append(True)
        return results
