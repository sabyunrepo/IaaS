"""
Rate Limiter — Redis Sliding Window Counter.

FastAPI 미들웨어로 사용. Redis 장애 시 fail-open (요청 허용 + WARNING).
"""
from __future__ import annotations

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Rate limit 규칙: (path_prefix, key_type, max_requests, window_seconds)
RATE_LIMIT_RULES: list[tuple[str, str, int, int]] = [
    ("/api/jobs", "user", 5, 60),       # POST /api/jobs: 사용자당 5/min
    ("/api/auth", "ip", 10, 60),        # POST /api/auth/*: IP당 10/min
]


def _get_client_ip(request: Request) -> str:
    """프록시 뒤에서도 실제 클라이언트 IP를 추출한다."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis 기반 sliding window counter rate limiter."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # POST 요청만 rate limit 적용
        if request.method != "POST":
            return await call_next(request)

        path = request.url.path
        matched_rule = None
        for prefix, key_type, max_req, window in RATE_LIMIT_RULES:
            if path.startswith(prefix):
                matched_rule = (prefix, key_type, max_req, window)
                break

        if not matched_rule:
            return await call_next(request)

        prefix, key_type, max_req, window = matched_rule

        # key 결정
        if key_type == "user":
            # Authorization 헤더에서 user 식별 (미인증이면 rate limit 스킵 — auth에서 차단됨)
            auth_header = request.headers.get("authorization", "")
            if not auth_header:
                return await call_next(request)
            # JWT에서 sub 추출 대신 토큰 해시를 key로 사용 (간단하고 안전)
            import hashlib
            rate_key = f"rl:{prefix}:{hashlib.sha256(auth_header.encode()).hexdigest()[:16]}"
        else:
            rate_key = f"rl:{prefix}:{_get_client_ip(request)}"

        # Redis sliding window counter
        try:
            redis_bridge = getattr(request.app.state, "redis_bridge", None)
            if redis_bridge and redis_bridge._redis:
                redis = redis_bridge._redis
            else:
                # Redis 미연결 → fail-open
                return await call_next(request)

            now = int(time.time())
            window_key = f"{rate_key}:{now // window}"

            count = await redis.incr(window_key)
            if count == 1:
                await redis.expire(window_key, window)

            if count > max_req:
                retry_after = window - (now % window)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                    headers={"Retry-After": str(retry_after)},
                )
        except Exception as e:
            # Redis 장애 → fail-open
            logger.warning("Rate limit check failed (fail-open): %s", e)

        return await call_next(request)
