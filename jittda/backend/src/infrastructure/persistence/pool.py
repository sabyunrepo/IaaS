"""
DB Connection Pool — psycopg_pool 기반 AsyncConnectionPool 싱글턴.

FastAPI lifespan 및 Worker main()에서 init_pool()/close_pool() 호출.
Repository 클래스는 get_pool()로 풀을 획득한다.
"""
from __future__ import annotations

from psycopg_pool import AsyncConnectionPool

_pool: AsyncConnectionPool | None = None


async def init_pool(
    conninfo: str, min_size: int = 2, max_size: int = 10
) -> AsyncConnectionPool:
    """커넥션 풀을 초기화하고 열린 풀을 반환한다."""
    global _pool
    if _pool is not None:
        raise RuntimeError("DB pool already initialized")
    _pool = AsyncConnectionPool(conninfo, min_size=min_size, max_size=max_size)
    await _pool.open()
    return _pool


def get_pool() -> AsyncConnectionPool:
    """초기화된 커넥션 풀을 반환한다. 미초기화 시 RuntimeError."""
    if _pool is None:
        raise RuntimeError("DB pool not initialized — call init_pool() first")
    return _pool


async def close_pool() -> None:
    """커넥션 풀을 종료한다."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
