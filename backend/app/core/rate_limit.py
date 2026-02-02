"""
backend/app/core/rate_limit.py
slowapi 기반 Rate Limiting 설정
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=None,  # in-memory (프로덕션에서는 Redis URI 사용)
)
