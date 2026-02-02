"""
backend/app/services/cached_llm.py
CachedLLMService — Redis 기반 LLM 응답 캐시
"""
import hashlib
import json
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class CachedLLMService:
    """LLM 호출 결과를 Redis에 캐싱하는 래퍼"""

    def __init__(self, ttl: int = 86400):
        self.ttl = ttl
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(settings.REDIS_URL)
        return self._redis

    def _cache_key(self, prompt: str, model: str) -> str:
        content = f"{model}:{prompt}"
        return f"llm_cache:{hashlib.sha256(content.encode()).hexdigest()}"

    async def run(self, prompt: str, model: str | None = None, result_type: Any = None) -> Any:
        """LLM 호출 (캐시 우선)"""
        model = model or settings.LLM_MODEL
        key = self._cache_key(prompt, model)

        # 캐시 조회
        try:
            redis = await self._get_redis()
            cached = await redis.get(key)
            if cached:
                logger.debug(f"LLM cache hit: {key[:20]}...")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")

        # LLM 호출
        from app.services.llm_config import get_llm_agent
        agent = get_llm_agent(result_type=result_type)
        run_result = await agent.run(prompt)
        data = run_result.data
        if hasattr(data, "model_dump"):
            data = data.model_dump()

        # 캐시 저장
        try:
            redis = await self._get_redis()
            await redis.setex(key, self.ttl, json.dumps(data, default=str))
        except Exception as e:
            logger.warning(f"Redis cache write failed: {e}")

        return data
