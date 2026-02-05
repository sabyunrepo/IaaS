"""
backend/app/core/rate_limit.py
slowapi 기반 Rate Limiting 설정 (IP + 사용자별 할당량)
"""
from starlette.requests import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def _get_rate_limit_key(request: Request) -> str:
    """사용자 인증 정보 기반 키, 미인증 시 IP 기반 키"""
    # Authorization header에서 사용자 식별
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        # JWT sub claim으로 식별 (간략 해시)
        import hashlib
        return f"user:{hashlib.sha256(auth[7:].encode()).hexdigest()[:16]}"

    api_key = request.headers.get("x-api-key", "")
    if api_key.startswith("vnt_"):
        import hashlib
        return f"apikey:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"

    return get_remote_address(request)


limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=["100/minute"],
    storage_uri=settings.REDIS_URL,  # Redis 기반 분산 Rate Limiting
)

# 사용자 플랜별 Rate Limit 상수
PLAN_LIMITS = {
    "free": "5/day",
    "pro": "100/day",
    "enterprise": "1000/day",
}

# Job 생성 엔드포인트별 제한
JOB_CREATE_LIMIT = "10/minute"
JOB_CREATE_LIMIT_FREE = "5/day"
