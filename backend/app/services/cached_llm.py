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

    async def invalidate_for_job(self, job_id: str) -> int:
        """특정 Job 관련 캐시 무효화 (Job 재시도 시 사용)

        Returns:
            삭제된 키 수
        """
        try:
            redis = await self._get_redis()
            # Job별 캐시 키 패턴 삭제
            pattern = f"llm_cache:job:{job_id}:*"
            deleted = 0
            async for key in redis.scan_iter(match=pattern):
                await redis.delete(key)
                deleted += 1
            logger.info(f"Invalidated {deleted} cache entries for job {job_id}")
            return deleted
        except Exception as e:
            logger.warning(f"Cache invalidation failed for job {job_id}: {e}")
            return 0

    def _job_cache_key(self, job_id: str, prompt: str, model: str) -> str:
        """Job 단위 캐시 키 생성 (무효화 가능)"""
        content = f"{model}:{prompt}"
        return f"llm_cache:job:{job_id}:{hashlib.sha256(content.encode()).hexdigest()}"

    async def run_for_job(
        self, job_id: str, prompt: str, model: str | None = None, result_type: Any = None
    ) -> Any:
        """Job 단위 캐시를 사용하는 LLM 호출"""
        model = model or settings.LLM_MODEL
        key = self._job_cache_key(job_id, prompt, model)

        # 캐시 조회
        try:
            redis = await self._get_redis()
            cached = await redis.get(key)
            if cached:
                logger.debug(f"LLM job cache hit: {key[:30]}...")
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
