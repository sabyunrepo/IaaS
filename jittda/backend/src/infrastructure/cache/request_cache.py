"""
Request Cache — Redis TTL 기반 요청 캐싱.

동일 데이터 반복 요청 시 외부 API 호출을 줄인다.
캐시 키: {service}:{hash(params)}
TTL: 환경변수로 조정 가능.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# 환경변수 기반 TTL 설정 (초)
DEFAULT_TTL = {
    "github_meta": int(os.environ.get("CACHE_TTL_GITHUB_META", "3600")),
    "github_commits": int(os.environ.get("CACHE_TTL_GITHUB_COMMITS", "1800")),
    "embeddings": int(os.environ.get("CACHE_TTL_EMBEDDINGS", "86400")),
}


def _make_key(service: str, params: dict[str, Any]) -> str:
    """캐시 키를 생성한다: {service}:{sha256(params)[:16]}."""
    serialized = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(serialized.encode()).hexdigest()[:16]
    return f"cache:{service}:{digest}"


class RequestCache:
    """Redis 기반 request-level 캐시.

    Args:
        redis: redis.asyncio 클라이언트.
        default_ttl: 기본 TTL(초). 0이면 캐싱 비활성.
    """

    def __init__(self, redis: Any, *, default_ttl: int = 3600):
        self._redis = redis
        self._default_ttl = default_ttl

    async def get(self, service: str, params: dict[str, Any]) -> Any | None:
        """캐시에서 값을 조회한다.

        Returns:
            캐시된 JSON 값 또는 None (miss).
        """
        key = _make_key(service, params)
        raw = await self._redis.get(key)
        if raw is None:
            return None
        try:
            value = raw if isinstance(raw, str) else raw.decode()
            return json.loads(value)
        except (json.JSONDecodeError, AttributeError):
            return None

    async def set(
        self, service: str, params: dict[str, Any], value: Any, *, ttl: int | None = None
    ) -> None:
        """캐시에 값을 저장한다."""
        key = _make_key(service, params)
        serialized = json.dumps(value, default=str)
        await self._redis.set(key, serialized, ex=ttl or self._default_ttl)

    async def invalidate(self, service: str, params: dict[str, Any]) -> None:
        """특정 캐시 항목을 무효화한다."""
        key = _make_key(service, params)
        await self._redis.delete(key)


def cached(
    service: str,
    *,
    ttl: int | None = None,
    key_params: Callable[..., dict[str, Any]] | None = None,
) -> Callable:
    """Redis 캐시 데코레이터.

    Args:
        service: 서비스 식별자 (캐시 키 prefix).
        ttl: TTL(초). None이면 DEFAULT_TTL[service] 또는 3600.
        key_params: 함수 인자에서 캐시 키 파라미터를 추출하는 함수.
            None이면 모든 인자를 키로 사용.

    사용:
        @cached("github_meta", ttl=3600)
        async def fetch_repo_metadata(self, repo_url: str) -> dict:
            ...
    """
    resolved_ttl = ttl or DEFAULT_TTL.get(service, 3600)

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(fn)
        async def wrapper(self_or_first: Any, *args: Any, **kwargs: Any) -> T:
            # force_refresh 옵션 지원
            force_refresh = kwargs.pop("force_refresh", False)

            # 캐시 클라이언트 확인 (self._cache 속성)
            cache: RequestCache | None = getattr(self_or_first, "_cache", None)
            if cache is None or force_refresh:
                return await fn(self_or_first, *args, **kwargs)

            # 캐시 키 생성
            if key_params:
                params = key_params(self_or_first, *args, **kwargs)
            else:
                params = {"args": list(args), "kwargs": kwargs}

            # 캐시 조회
            cached_value = await cache.get(service, params)
            if cached_value is not None:
                logger.debug("Cache HIT: %s", _make_key(service, params))
                return cached_value

            # 캐시 미스 → 실제 호출
            result = await fn(self_or_first, *args, **kwargs)

            # 결과 캐싱
            await cache.set(service, params, result, ttl=resolved_ttl)
            logger.debug("Cache SET: %s (ttl=%ds)", _make_key(service, params), resolved_ttl)
            return result

        return wrapper

    return decorator
