"""
backend/app/services/cached_llm.py
CachedLLMService — Redis 기반 LLM 응답 캐시 + Langfuse 추적
"""
import asyncio
import hashlib
import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.core.observability import get_current_trace_metadata, is_langfuse_enabled, get_langfuse_client

logger = logging.getLogger(__name__)

# 모듈 레벨 Redis 연결 풀 싱글톤
_redis_pool = None


async def _get_shared_redis():
    """모듈 레벨 Redis 연결 풀 (싱글톤)"""
    global _redis_pool
    if _redis_pool is None:
        import redis.asyncio as aioredis
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            max_connections=20,
            decode_responses=False,
        )
    return _redis_pool


def _log_llm_generation(
    model: str,
    prompt: str,
    output: Any,
    run_result: Any,
    trace_meta: dict,
    activity_name: str | None = None,
) -> None:
    """Langfuse에 LLM generation 기록 (비용 추적용)

    Langfuse SDK v3에서는 start_generation()을 사용하여 현재 트레이스 내에
    generation span을 생성합니다.

    Args:
        model: LLM 모델명
        prompt: 입력 프롬프트
        output: LLM 출력
        run_result: Pydantic AI RunResult 객체
        trace_meta: 트레이스 메타데이터
        activity_name: Activity 이름
    """
    if not is_langfuse_enabled():
        return

    try:
        client = get_langfuse_client()
        if not client:
            return

        # Pydantic AI RunResult에서 usage 정보 추출
        usage_details = None
        model_name = model
        if hasattr(run_result, 'usage'):
            try:
                usage_obj = run_result.usage()
                if usage_obj:
                    input_tokens = getattr(usage_obj, 'input_tokens', 0) or 0
                    output_tokens = getattr(usage_obj, 'output_tokens', 0) or 0
                    usage_details = {
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens,
                    }
            except Exception as e:
                logger.debug(f"Failed to get usage from run_result: {e}")

        # all_messages에서 실제 model_name 추출
        if hasattr(run_result, 'all_messages'):
            try:
                messages = run_result.all_messages()
                for msg in reversed(messages):
                    if hasattr(msg, 'model_name') and msg.model_name:
                        model_name = msg.model_name
                        break
            except Exception:
                pass

        # Langfuse SDK v3: start_generation으로 LLM 호출 기록
        # 현재 trace 컨텍스트 내에서 자동으로 연결됨
        output_str = str(output)[:5000] if output else None
        generation = client.start_generation(
            name=activity_name or "llm_call",
            model=model_name,
            input=prompt[:5000] if isinstance(prompt, str) else str(prompt)[:5000],
            usage_details=usage_details,
            metadata={
                **trace_meta,
                "configured_model": model,
            },
        )
        # Langfuse 3.x: output은 update()로 설정 후 end() 호출 (end()에 output 파라미터 없음)
        generation.update(output=output_str)
        generation.end()

        logger.info(
            f"Logged Langfuse generation: {activity_name}, "
            f"model={model_name}, tokens={usage_details}"
        )
    except Exception as e:
        logger.warning(f"Failed to log Langfuse generation: {e}")


def _strip_markdown_json(text: str) -> str:
    """Strip markdown code blocks from LLM response.

    LLMs sometimes wrap JSON responses in ```json ... ``` blocks.
    This function extracts the raw JSON content.

    Args:
        text: Raw LLM response string

    Returns:
        Cleaned JSON string without markdown formatting
    """
    if not isinstance(text, str):
        return text

    # Strip leading/trailing whitespace
    text = text.strip()

    # Pattern 1: ```json ... ```
    json_block_pattern = r'^```(?:json)?\s*\n?(.*?)\n?```$'
    match = re.match(json_block_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        logger.debug("Stripped markdown code block from LLM response")
        return match.group(1).strip()

    # Pattern 2: ``` ... ``` (without language specifier)
    generic_block_pattern = r'^```\s*\n?(.*?)\n?```$'
    match = re.match(generic_block_pattern, text, re.DOTALL)
    if match:
        logger.debug("Stripped generic code block from LLM response")
        return match.group(1).strip()

    return text


def _parse_llm_json_response(data: Any) -> Any:
    """Parse LLM response, handling markdown-wrapped JSON.

    Args:
        data: Raw LLM response (string or dict)

    Returns:
        Parsed JSON object (dict or list) if parsing succeeds,
        original data otherwise
    """
    # If already a dict/list, return as-is
    if isinstance(data, (dict, list)):
        return data

    # If string, try to parse as JSON
    if isinstance(data, str):
        # First strip any markdown code blocks
        cleaned = _strip_markdown_json(data)
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, (dict, list)):
                logger.debug("Successfully parsed JSON from string LLM response")
                return parsed
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Return original string if parsing fails
            pass

    return data


class CachedLLMService:
    """LLM 호출 결과를 Redis에 캐싱하는 래퍼"""

    def __init__(self, ttl: int = 86400):
        self.ttl = ttl

    async def _get_redis(self):
        return await _get_shared_redis()

    @staticmethod
    def _model_settings(model: str | None = None, override_max_tokens: int | None = None):
        """모델별 최적 ModelSettings 반환 (max_tokens 등)

        Args:
            model: LLM 모델명
            override_max_tokens: Langfuse config 등에서 지정한 max_tokens (모델 기본값보다 우선)
        """
        from pydantic_ai import ModelSettings
        from app.services.llm_config import get_max_output_tokens
        if override_max_tokens:
            max_tokens = override_max_tokens
        elif model:
            max_tokens = get_max_output_tokens(model)
        else:
            max_tokens = settings.LLM_MAX_OUTPUT_TOKENS
        return ModelSettings(max_tokens=max_tokens)

    def _cache_key(self, prompt: str, model: str, activity_name: str | None = None) -> str:
        """Activity 컨텍스트를 포함한 캐시 키 생성

        기존: llm_cache:SHA256(model:prompt)
        개선: llm_cache:activity_name:SHA256(model:prompt)
        """
        content = f"{model}:{prompt}"
        hash_part = hashlib.sha256(content.encode()).hexdigest()
        if activity_name:
            return f"llm_cache:{activity_name}:{hash_part}"
        return f"llm_cache:{hash_part}"

    async def run(
        self,
        prompt: str,
        model: str | None = None,
        result_type: Any = None,
        activity_name: str | None = None,
    ) -> Any:
        """LLM 호출 (캐시 우선) + Langfuse 추적

        Args:
            prompt: LLM 프롬프트
            model: 명시적 모델명 (지정하면 activity_name보다 우선)
            result_type: Pydantic 모델 (구조화 출력용)
            activity_name: Activity 이름 (자동 모델 선택용)
        """
        if model is None and activity_name:
            from app.services.llm_config import get_model_for_activity
            model = get_model_for_activity(activity_name)
        model = model or settings.LLM_MODEL
        key = self._cache_key(prompt, model, activity_name)
        trace_meta = get_current_trace_metadata()

        # 캐시 조회 (LLM_CACHE_ENABLED일 때만)
        if settings.LLM_CACHE_ENABLED:
            try:
                redis = await self._get_redis()
                cached = await redis.get(key)
                if cached:
                    logger.debug(f"LLM cache hit: {key[:20]}...")
                    self._log_cache_event("hit", trace_meta)
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")

        self._log_cache_event("miss", trace_meta)

        # LLM 호출 (폴백 체인: primary → fallback)
        # asyncio.shield로 감싸서 Temporal Activity 취소로 인한 CancelledError 방지
        from app.services.llm_config import get_llm_agent
        ms = self._model_settings(model)
        try:
            agent = get_llm_agent(result_type=result_type, model=model)
            run_result = await asyncio.shield(agent.run(prompt, model_settings=ms))
        except asyncio.CancelledError:
            logger.warning(f"LLM call cancelled for model {model}")
            raise
        except Exception as primary_err:
            fallback_model = settings.LLM_FALLBACK_MODEL
            if fallback_model and fallback_model != model:
                logger.warning(f"Primary LLM ({model}) failed: {primary_err}. Trying fallback: {fallback_model}")
                self._log_fallback_event(model, fallback_model, trace_meta)
                agent = get_llm_agent(result_type=result_type, model=fallback_model)
                run_result = await asyncio.shield(agent.run(prompt, model_settings=ms))
            else:
                raise

        # Pydantic AI v1.x uses .output, older versions use .data
        data = getattr(run_result, 'output', None) or getattr(run_result, 'data', None)
        if data is None:
            raise ValueError(f"AgentRunResult has neither 'output' nor 'data' attribute: {type(run_result)}")
        if hasattr(data, "model_dump"):
            data = data.model_dump()

        # Parse JSON from string responses (handles markdown-wrapped JSON)
        data = _parse_llm_json_response(data)

        # Langfuse에 generation 기록 (비용 추적)
        _log_llm_generation(
            model=model,
            prompt=prompt,
            output=data,
            run_result=run_result,
            trace_meta=trace_meta,
            activity_name=activity_name,
        )

        # 캐시 저장 (LLM_CACHE_ENABLED일 때만)
        if settings.LLM_CACHE_ENABLED:
            try:
                redis = await self._get_redis()
                await redis.setex(key, self.ttl, json.dumps(data, default=str))
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")

        return data

    def _log_cache_event(self, event_type: str, metadata: dict):
        """Langfuse에 캐시 이벤트 기록"""
        if not is_langfuse_enabled():
            return
        try:
            client = get_langfuse_client()
            if client:
                client.update_current_span(
                    metadata={
                        **metadata,
                        "cache_event": event_type,
                    }
                )
        except Exception:
            pass  # 캐시 이벤트 로깅 실패는 무시

    def _log_fallback_event(self, primary_model: str, fallback_model: str, metadata: dict):
        """Langfuse에 폴백 이벤트 기록"""
        if not is_langfuse_enabled():
            return
        try:
            client = get_langfuse_client()
            if client:
                client.update_current_span(
                    metadata={
                        **metadata,
                        "fallback_event": True,
                        "primary_model": primary_model,
                        "fallback_model": fallback_model,
                    }
                )
        except Exception:
            pass  # 폴백 이벤트 로깅 실패는 무시

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

    def _job_cache_key(self, job_id: str, prompt: str, model: str, activity_name: str | None = None) -> str:
        """Job 단위 캐시 키 생성 (무효화 가능)"""
        content = f"{model}:{prompt}"
        hash_part = hashlib.sha256(content.encode()).hexdigest()
        if activity_name:
            return f"llm_cache:job:{job_id}:{activity_name}:{hash_part}"
        return f"llm_cache:job:{job_id}:{hash_part}"

    async def run_with_prompt_config(
        self,
        prompt_config: Any,  # PromptWithConfig from app.prompts
        result_type: Any = None,
    ) -> Any:
        """Langfuse PromptWithConfig를 사용하는 LLM 호출

        Langfuse에서 가져온 프롬프트의 config에 있는 model, temperature를 사용합니다.

        Args:
            prompt_config: PromptWithConfig 객체 (get_prompt_with_config 결과)
            result_type: Pydantic 모델 (구조화 출력용)
        """
        prompt = prompt_config.prompt
        # Langfuse config의 model 사용, 없으면 fallback
        model = prompt_config.model or settings.LLM_MODEL
        temperature = prompt_config.temperature
        prompt_name = prompt_config.name if prompt_config else None

        key = self._cache_key(prompt, model, prompt_name)
        trace_meta = get_current_trace_metadata()

        # Langfuse 프롬프트 소스 정보 추가
        trace_meta["prompt_source"] = prompt_config.source
        trace_meta["prompt_name"] = prompt_config.name
        if prompt_config.version:
            trace_meta["prompt_version"] = prompt_config.version

        # 캐시 조회 (LLM_CACHE_ENABLED일 때만)
        if settings.LLM_CACHE_ENABLED:
            try:
                redis = await self._get_redis()
                cached = await redis.get(key)
                if cached:
                    logger.debug(f"LLM cache hit: {key[:20]}... (prompt: {prompt_config.name})")
                    self._log_cache_event("hit", trace_meta)
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")

        self._log_cache_event("miss", trace_meta)

        # LLM 호출
        from app.services.llm_config import get_llm_agent
        # Langfuse config에서 max_output_tokens 추출 (있으면 모델 기본값보다 우선)
        config_max_tokens = None
        if prompt_config.config:
            config_max_tokens = prompt_config.config.get("max_output_tokens")
        ms = self._model_settings(model, override_max_tokens=config_max_tokens)
        try:
            # temperature가 있으면 agent에 전달
            agent = get_llm_agent(result_type=result_type, model=model)
            run_result = await agent.run(prompt, model_settings=ms)

            logger.info(
                f"LLM call: {prompt_config.name} (source={prompt_config.source}, "
                f"model={model})"
            )
        except Exception as primary_err:
            fallback_model = settings.LLM_FALLBACK_MODEL
            if fallback_model and fallback_model != model:
                logger.warning(f"Primary LLM ({model}) failed: {primary_err}. Trying fallback: {fallback_model}")
                self._log_fallback_event(model, fallback_model, trace_meta)
                agent = get_llm_agent(result_type=result_type, model=fallback_model)
                run_result = await agent.run(prompt, model_settings=ms)
            else:
                raise

        # Pydantic AI v1.x uses .output, older versions use .data
        data = getattr(run_result, 'output', None) or getattr(run_result, 'data', None)
        if data is None:
            raise ValueError(f"AgentRunResult has neither 'output' nor 'data' attribute: {type(run_result)}")
        if hasattr(data, "model_dump"):
            data = data.model_dump()

        # Parse JSON from string responses (handles markdown-wrapped JSON)
        data = _parse_llm_json_response(data)

        # Langfuse에 generation 기록 (비용 추적)
        _log_llm_generation(
            model=model,
            prompt=prompt,
            output=data,
            run_result=run_result,
            trace_meta=trace_meta,
            activity_name=prompt_name,
        )

        # 캐시 저장 (LLM_CACHE_ENABLED일 때만)
        if settings.LLM_CACHE_ENABLED:
            try:
                redis = await self._get_redis()
                await redis.setex(key, self.ttl, json.dumps(data, default=str))
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")

        return data

    async def run_for_job(
        self,
        job_id: str,
        prompt: str,
        model: str | None = None,
        result_type: Any = None,
        activity_name: str | None = None,
    ) -> Any:
        """Job 단위 캐시를 사용하는 LLM 호출 + Langfuse 추적

        Args:
            job_id: Job ID
            prompt: LLM 프롬프트
            model: 명시적 모델명 (지정하면 activity_name보다 우선)
            result_type: Pydantic 모델 (구조화 출력용)
            activity_name: Activity 이름 (자동 모델 선택용)
        """
        if model is None and activity_name:
            from app.services.llm_config import get_model_for_activity
            model = get_model_for_activity(activity_name)
        model = model or settings.LLM_MODEL
        key = self._job_cache_key(job_id, prompt, model, activity_name)
        trace_meta = {**get_current_trace_metadata(), "job_id": job_id}

        # 캐시 조회 (LLM_CACHE_ENABLED일 때만)
        if settings.LLM_CACHE_ENABLED:
            try:
                redis = await self._get_redis()
                cached = await redis.get(key)
                if cached:
                    logger.debug(f"LLM job cache hit: {key[:30]}...")
                    self._log_cache_event("hit", trace_meta)
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")

        self._log_cache_event("miss", trace_meta)

        # LLM 호출 (폴백 체인: primary → fallback)
        # asyncio.shield로 감싸서 Temporal Activity 취소로 인한 CancelledError 방지
        from app.services.llm_config import get_llm_agent
        ms = self._model_settings(model)
        try:
            agent = get_llm_agent(result_type=result_type, model=model)
            run_result = await asyncio.shield(agent.run(prompt, model_settings=ms))
        except asyncio.CancelledError:
            logger.warning(f"LLM call cancelled for model {model}")
            raise
        except Exception as primary_err:
            fallback_model = settings.LLM_FALLBACK_MODEL
            if fallback_model and fallback_model != model:
                logger.warning(f"Primary LLM ({model}) failed: {primary_err}. Trying fallback: {fallback_model}")
                self._log_fallback_event(model, fallback_model, trace_meta)
                agent = get_llm_agent(result_type=result_type, model=fallback_model)
                run_result = await asyncio.shield(agent.run(prompt, model_settings=ms))
            else:
                raise

        # Pydantic AI v1.x uses .output, older versions use .data
        data = getattr(run_result, 'output', None) or getattr(run_result, 'data', None)
        if data is None:
            raise ValueError(f"AgentRunResult has neither 'output' nor 'data' attribute: {type(run_result)}")
        if hasattr(data, "model_dump"):
            data = data.model_dump()

        # Parse JSON from string responses (handles markdown-wrapped JSON)
        data = _parse_llm_json_response(data)

        # Langfuse에 generation 기록 (비용 추적)
        _log_llm_generation(
            model=model,
            prompt=prompt,
            output=data,
            run_result=run_result,
            trace_meta=trace_meta,
            activity_name=activity_name,
        )

        # 캐시 저장 (LLM_CACHE_ENABLED일 때만)
        if settings.LLM_CACHE_ENABLED:
            try:
                redis = await self._get_redis()
                await redis.setex(key, self.ttl, json.dumps(data, default=str))
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")

        return data
