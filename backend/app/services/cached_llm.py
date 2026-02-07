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

# ─── 상수 ───────────────────────────────────────────────
CACHE_TTL_SECONDS = 86400  # 24시간
REDIS_MAX_CONNECTIONS = 20
PROMPT_TRUNCATE_LIMIT = 5000  # Langfuse 로깅 시 프롬프트/출력 최대 길이
OUTPUT_TRUNCATE_LIMIT = 5000

# 모듈 레벨 Redis 연결 풀 싱글톤
_redis_pool = None


async def _get_shared_redis():
    """모듈 레벨 Redis 연결 풀 (싱글톤)"""
    global _redis_pool
    if _redis_pool is None:
        import redis.asyncio as aioredis
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            max_connections=REDIS_MAX_CONNECTIONS,
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

        # Active trace 여부 확인 — trace 없으면 독립 generation으로 기록
        has_active_trace = False
        try:
            try:
                from langfuse import langfuse_context
            except ImportError:
                from langfuse.decorators import langfuse_context
            current_trace = langfuse_context.get_current_trace_id()
            has_active_trace = current_trace is not None
        except Exception:
            pass

        output_str = str(output)[:OUTPUT_TRUNCATE_LIMIT] if output else None
        gen_kwargs = dict(
            name=activity_name or "llm_call",
            model=model_name,
            input=prompt[:PROMPT_TRUNCATE_LIMIT] if isinstance(prompt, str) else str(prompt)[:PROMPT_TRUNCATE_LIMIT],
            usage_details=usage_details,
            metadata={
                **trace_meta,
                "configured_model": model,
            },
        )

        if has_active_trace:
            # trace 컨텍스트 내에서 span으로 연결
            generation = client.start_generation(**gen_kwargs)
            generation.update(output=output_str)
            generation.end()
        else:
            # trace 없으면 독립 trace 생성 후 generation 기록 (SDK v3 호환)
            try:
                trace = client.trace(name=f"standalone-{activity_name}")
                generation = trace.generation(**gen_kwargs, output=output_str)
                generation.end()
            except Exception:
                logger.debug(f"Langfuse standalone generation skipped: {activity_name}")

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

    Tries multiple extraction strategies:
    1. Direct JSON parse (after stripping markdown blocks)
    2. Extract first JSON object from mixed text (e.g., "Here is the result: {...}")
    3. Return original data if all strategies fail

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
        if not data.strip():
            logger.warning("LLM returned empty string response")
            return data

        # Strategy 1: Strip markdown blocks and parse directly
        cleaned = _strip_markdown_json(data)
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, (dict, list)):
                logger.debug("Successfully parsed JSON from string LLM response")
                return parsed
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract first JSON object or array from mixed text
        # Handles cases like "Here is the analysis:\n{...}\nLet me know..."
        # or "Here are the topics:\n[...]\nI hope this helps"
        for open_ch, close_ch, type_name in [('{', '}', 'object'), ('[', ']', 'array')]:
            start_pos = cleaned.find(open_ch)
            if start_pos < 0:
                continue
            depth = 0
            in_string = False
            escape_next = False
            for i in range(start_pos, len(cleaned)):
                ch = cleaned[i]
                if escape_next:
                    escape_next = False
                    continue
                if ch == '\\':
                    escape_next = True
                    continue
                if ch == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == open_ch:
                    depth += 1
                elif ch == close_ch:
                    depth -= 1
                    if depth == 0:
                        json_candidate = cleaned[start_pos:i + 1]
                        try:
                            parsed = json.loads(json_candidate)
                            if isinstance(parsed, (dict, list)):
                                logger.debug(f"Extracted JSON {type_name} from mixed LLM response text")
                                return parsed
                        except json.JSONDecodeError:
                            pass
                        break

        logger.warning(
            f"Failed to parse LLM response as JSON "
            f"(length={len(data)}, preview={data[:150]!r})"
        )

    return data


class CachedLLMService:
    """LLM 호출 결과를 Redis에 캐싱하는 래퍼

    DRY 패턴: 모든 run 메서드는 _execute_with_cache()를 통해 동작.
    캐시 조회 → LLM 호출(폴백) → JSON 파싱 → Langfuse 로깅 → 캐시 저장
    """

    def __init__(self, ttl: int = CACHE_TTL_SECONDS):
        self.ttl = ttl

    async def _get_redis(self):
        return await _get_shared_redis()

    @staticmethod
    def _model_settings(model: str | None = None, override_max_tokens: int | None = None):
        """모델별 최적 ModelSettings 반환"""
        from pydantic_ai import ModelSettings
        from app.services.llm_config import get_max_output_tokens
        if override_max_tokens:
            max_tokens = override_max_tokens
        elif model:
            max_tokens = get_max_output_tokens(model)
        else:
            max_tokens = settings.LLM_MAX_OUTPUT_TOKENS
        return ModelSettings(max_tokens=max_tokens)

    @staticmethod
    def _make_cache_key(prompt: str, model: str, activity_name: str | None = None, job_id: str | None = None) -> str:
        """캐시 키 생성 (Activity + Job 스코프 통합)

        키 형식:
          글로벌:   llm_cache:{activity}:{hash}
          잡스코프: llm_cache:job:{job_id}:{activity}:{hash}
        """
        content = f"{model}:{prompt}"
        hash_part = hashlib.sha256(content.encode()).hexdigest()
        parts = ["llm_cache"]
        if job_id:
            parts.extend(["job", job_id])
        if activity_name:
            parts.append(activity_name)
        parts.append(hash_part)
        return ":".join(parts)

    # ─── 캐시 I/O (공통) ─────────────────────────────────

    async def _cache_get(self, key: str, trace_meta: dict) -> Any | None:
        """캐시에서 읽기. 히트 시 파싱된 데이터 반환, 미스 시 None."""
        if not settings.LLM_CACHE_ENABLED:
            return None
        try:
            redis = await self._get_redis()
            cached = await redis.get(key)
            if cached:
                logger.debug(f"LLM cache hit: {key[:30]}...")
                self._log_cache_event("hit", trace_meta)
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")
        self._log_cache_event("miss", trace_meta)
        return None

    async def _cache_set(self, key: str, data: Any) -> None:
        """캐시에 저장."""
        if not settings.LLM_CACHE_ENABLED:
            return
        try:
            redis = await self._get_redis()
            await redis.setex(key, self.ttl, json.dumps(data, default=str))
        except Exception as e:
            logger.warning(f"Redis cache write failed: {e}")

    # ─── LLM 호출 (공통 — DRY 핵심) ─────────────────────

    async def _call_llm_with_fallback(
        self,
        prompt: str,
        model: str,
        result_type: Any,
        override_max_tokens: int | None = None,
        trace_meta: dict | None = None,
    ) -> tuple[Any, Any]:
        """LLM 호출 + 폴백 + 결과 정규화. (data, run_result) 반환."""
        from app.services.llm_config import get_llm_agent

        ms = self._model_settings(model, override_max_tokens)
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
                if trace_meta:
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

        data = _parse_llm_json_response(data)
        return data, run_result

    async def _execute_with_cache(
        self,
        prompt: str,
        model: str,
        cache_key: str,
        trace_meta: dict,
        result_type: Any = None,
        activity_name: str | None = None,
        override_max_tokens: int | None = None,
    ) -> Any:
        """캐시 조회 → LLM 호출 → Langfuse 로깅 → 캐시 저장 (공통 파이프라인)"""
        # 1. 캐시 조회
        cached = await self._cache_get(cache_key, trace_meta)
        if cached is not None:
            return cached

        # 2. LLM 호출 + 폴백
        data, run_result = await self._call_llm_with_fallback(
            prompt, model, result_type, override_max_tokens, trace_meta,
        )

        # 3. Langfuse 로깅
        _log_llm_generation(
            model=model, prompt=prompt, output=data,
            run_result=run_result, trace_meta=trace_meta,
            activity_name=activity_name,
        )

        # 4. 캐시 저장
        await self._cache_set(cache_key, data)
        return data

    # ─── 공개 API ────────────────────────────────────────

    async def run(
        self,
        prompt: str,
        model: str | None = None,
        result_type: Any = None,
        activity_name: str | None = None,
    ) -> Any:
        """LLM 호출 (캐시 우선) + Langfuse 추적"""
        if model is None and activity_name:
            from app.services.llm_config import get_model_for_activity
            model = get_model_for_activity(activity_name)
        model = model or settings.LLM_MODEL

        return await self._execute_with_cache(
            prompt=prompt,
            model=model,
            cache_key=self._make_cache_key(prompt, model, activity_name),
            trace_meta=get_current_trace_metadata(),
            result_type=result_type,
            activity_name=activity_name,
        )

    async def run_for_job(
        self,
        job_id: str,
        prompt: str,
        model: str | None = None,
        result_type: Any = None,
        activity_name: str | None = None,
    ) -> Any:
        """Job 단위 캐시를 사용하는 LLM 호출 + Langfuse 추적"""
        if model is None and activity_name:
            from app.services.llm_config import get_model_for_activity
            model = get_model_for_activity(activity_name)
        model = model or settings.LLM_MODEL

        return await self._execute_with_cache(
            prompt=prompt,
            model=model,
            cache_key=self._make_cache_key(prompt, model, activity_name, job_id=job_id),
            trace_meta={**get_current_trace_metadata(), "job_id": job_id},
            result_type=result_type,
            activity_name=activity_name,
        )

    async def run_with_prompt_config(
        self,
        prompt_config: Any,  # PromptWithConfig from app.prompts
        result_type: Any = None,
    ) -> Any:
        """Langfuse PromptWithConfig를 사용하는 LLM 호출"""
        prompt = prompt_config.prompt
        model = prompt_config.model or settings.LLM_MODEL
        prompt_name = prompt_config.name if prompt_config else None

        trace_meta = get_current_trace_metadata()
        trace_meta["prompt_source"] = prompt_config.source
        trace_meta["prompt_name"] = prompt_config.name
        if prompt_config.version:
            trace_meta["prompt_version"] = prompt_config.version

        config_max_tokens = None
        if prompt_config.config:
            config_max_tokens = prompt_config.config.get("max_output_tokens")

        return await self._execute_with_cache(
            prompt=prompt,
            model=model,
            cache_key=self._make_cache_key(prompt, model, prompt_name),
            trace_meta=trace_meta,
            result_type=result_type,
            activity_name=prompt_name,
            override_max_tokens=config_max_tokens,
        )

    # ─── Langfuse 이벤트 로깅 ────────────────────────────

    def _log_cache_event(self, event_type: str, metadata: dict):
        """Langfuse에 캐시 이벤트 기록"""
        if not is_langfuse_enabled():
            return
        try:
            client = get_langfuse_client()
            if client:
                client.update_current_span(
                    metadata={**metadata, "cache_event": event_type}
                )
        except Exception:
            pass

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
            pass

    # ─── 캐시 무효화 ────────────────────────────────────

    async def invalidate_for_job(self, job_id: str) -> int:
        """특정 Job 관련 캐시 전체 무효화"""
        return await self._invalidate_by_pattern(f"llm_cache:job:{job_id}:*")

    async def invalidate_activity_cache(self, activity_name: str) -> int:
        """특정 Activity의 글로벌 캐시 무효화 (선택적 재실행용)

        예: 분석 로직을 수정한 후 해당 Activity만 캐시 삭제
        """
        return await self._invalidate_by_pattern(f"llm_cache:{activity_name}:*")

    async def invalidate_activity_for_job(self, job_id: str, activity_name: str) -> int:
        """특정 Job의 특정 Activity 캐시만 무효화 (최소 범위 재실행)"""
        return await self._invalidate_by_pattern(f"llm_cache:job:{job_id}:{activity_name}:*")

    async def _invalidate_by_pattern(self, pattern: str) -> int:
        """패턴 기반 캐시 삭제 (공통)"""
        try:
            redis = await self._get_redis()
            deleted = 0
            async for key in redis.scan_iter(match=pattern):
                await redis.delete(key)
                deleted += 1
            logger.info(f"Invalidated {deleted} cache entries matching '{pattern}'")
            return deleted
        except Exception as e:
            logger.warning(f"Cache invalidation failed for pattern '{pattern}': {e}")
            return 0
