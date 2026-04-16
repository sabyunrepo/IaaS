"""
backend/app/core/observability.py
Langfuse LLM observability — Langfuse Python SDK v4 (OpenTelemetry-based)

v4 API mapping (from legacy v3):
- client.start_span(...)          → client.start_as_current_observation(..., as_type="span")
- span.update_trace(session_id=…) → OTel span attrs (session.id / user.id / langfuse.trace.tags)
                                     set on the current span; Langfuse OTel exporter promotes
                                     them to trace-level fields so Sessions/User/Tag UIs populate.
- langfuse_context.update_*       → client.update_current_span (only valid inside an active span)
- client.create_score(trace_id=…) → unchanged

Structlog integration:
- langfuse_trace_context() also binds structlog context so logs and traces
  share the same job_id / phase / activity metadata.
"""
import os
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from app.core.config import settings


# OTel attribute keys used by the Langfuse v4 exporter to surface trace-level
# fields (Sessions tab, User filter, Tag filter). Defined in
# langfuse._client.attributes.LangfuseOtelSpanAttributes. Hard-coding here so
# we don't depend on a private module path.
_OTEL_ATTR_SESSION_ID = "session.id"
_OTEL_ATTR_USER_ID = "user.id"
_OTEL_ATTR_TAGS = "langfuse.trace.tags"


# Lazy import to avoid circular dependency
def _get_logger():
    try:
        from app.core.logging import get_logger
        return get_logger(__name__)
    except ImportError:
        import logging
        return logging.getLogger(__name__)


logger = _get_logger()

_initialized = False
_langfuse_client = None

_current_job_id: ContextVar[str | None] = ContextVar("current_job_id", default=None)
_current_phase: ContextVar[str | None] = ContextVar("current_phase", default=None)
_current_activity: ContextVar[str | None] = ContextVar("current_activity", default=None)


def get_langfuse_client():
    """Langfuse 클라이언트 싱글톤 반환"""
    global _langfuse_client
    if _langfuse_client is None and is_langfuse_enabled():
        from langfuse import Langfuse
        _langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
    return _langfuse_client


def is_langfuse_enabled() -> bool:
    """Langfuse 활성화 여부 확인"""
    return bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY)


def setup_langfuse() -> bool:
    """Langfuse를 LiteLLM success/failure callback으로 등록.

    LANGFUSE_PUBLIC_KEY가 설정되지 않으면 skip.
    Returns True if enabled.
    """
    global _initialized
    if _initialized:
        return True

    if not is_langfuse_enabled():
        logger.info("Langfuse disabled (LANGFUSE_PUBLIC_KEY not set)")
        return False

    try:
        import litellm

        # v4는 OpenTelemetry 기반 → LiteLLM은 langfuse_otel 콜백 사용
        # https://docs.litellm.ai/docs/observability/langfuse_otel_integration
        litellm.callbacks = ["langfuse_otel"]

        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.LANGFUSE_PUBLIC_KEY)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.LANGFUSE_SECRET_KEY)
        os.environ.setdefault("LANGFUSE_HOST", settings.LANGFUSE_HOST)
        os.environ.setdefault("LANGFUSE_OTEL_HOST", settings.LANGFUSE_HOST)

        get_langfuse_client()

        _initialized = True
        logger.info(f"Langfuse enabled → {settings.LANGFUSE_HOST}")
        return True
    except Exception as e:
        logger.warning(f"Langfuse setup failed: {e}")
        return False


# =============================================================================
# Internal helpers for v4 API
# =============================================================================

def _trace_context_for_job(client, job_id: str | None) -> dict | None:
    """job_id 기반 안정적인 trace_id를 생성해 trace_context dict로 반환.

    job_id가 None이면 None을 반환해 기본 trace 사용.
    """
    if not job_id or client is None:
        return None
    try:
        trace_id = client.create_trace_id(seed=job_id)
        return {"trace_id": trace_id}
    except Exception:
        return None


def _span_metadata(
    job_id: str | None = None,
    phase: str | None = None,
    activity: str | None = None,
    extra: dict | None = None,
) -> dict:
    """observation(span)에 붙일 메타데이터 조립."""
    meta: dict[str, Any] = {}
    if job_id:
        meta["job_id"] = job_id
    if phase:
        meta["phase"] = phase
    if activity:
        meta["activity"] = activity
    if extra:
        meta.update(extra)
    return meta


def _set_trace_level_attrs(
    session_id: str | None = None,
    user_id: str | None = None,
    tags: list[str] | None = None,
) -> None:
    """현재 OTel span에 trace-level 속성을 세팅 (Sessions/User/Tag UI용).

    v4.2.x에는 `client.update_current_trace` / `propagate_attributes`가 없어,
    Langfuse OTel exporter가 읽는 span attribute를 직접 설정한다.
    Active span이 없으면 no-op.
    """
    if not (session_id or user_id or tags):
        return
    try:
        from opentelemetry import trace as _otel_trace
        current = _otel_trace.get_current_span()
        if current is None or not current.is_recording():
            return
        if session_id:
            current.set_attribute(_OTEL_ATTR_SESSION_ID, session_id)
        if user_id:
            current.set_attribute(_OTEL_ATTR_USER_ID, user_id)
        if tags:
            # Langfuse expects tags as a list of strings
            current.set_attribute(_OTEL_ATTR_TAGS, list(tags))
    except Exception as e:
        logger.debug(f"set trace-level attrs skipped: {e}")


def _update_current_span_safe(client, **kwargs) -> None:
    """update_current_span을 안전 호출 (없거나 실패 시 무시).

    주의: 호출 시점에 active span이 없으면 Langfuse가 경고 로그를 찍고 no-op.
    observe_activity 데코레이터 안에서 호출될 때만 실효가 있다.
    """
    if client is None:
        return
    updater = getattr(client, "update_current_span", None)
    if updater is None:
        return
    try:
        updater(**kwargs)
    except Exception as e:
        logger.debug(f"update_current_span skipped: {e}")


@contextmanager
def langfuse_trace_context(
    job_id: str | None = None,
    phase: str | None = None,
    activity: str | None = None,
):
    """Langfuse 추적 컨텍스트 설정 + Structlog 컨텍스트 바인딩"""
    prev_job_id = _current_job_id.get()
    prev_phase = _current_phase.get()
    prev_activity = _current_activity.get()

    if job_id:
        _current_job_id.set(job_id)
    if phase:
        _current_phase.set(phase)
    if activity:
        _current_activity.set(activity)

    try:
        from app.core.logging import bind_job_context
        bind_job_context(job_id=job_id, phase=phase, activity=activity)
    except ImportError:
        pass

    try:
        if is_langfuse_enabled():
            client = get_langfuse_client()
            _update_current_span_safe(
                client,
                metadata=_span_metadata(job_id=job_id, phase=phase, activity=activity),
            )
            # trace-level 필드: 현재 span이 있으면 Sessions/User/Tag 필드도 갱신
            tags: list[str] = []
            if phase:
                tags.append(f"phase:{phase}")
            if activity:
                tags.append(f"activity:{activity}")
            _set_trace_level_attrs(session_id=job_id, tags=tags or None)
        yield
    finally:
        _current_job_id.set(prev_job_id)
        _current_phase.set(prev_phase)
        _current_activity.set(prev_activity)

        try:
            from app.core.logging import bind_job_context
            bind_job_context(
                job_id=prev_job_id,
                phase=prev_phase,
                activity=prev_activity,
            )
        except ImportError:
            pass


def get_current_trace_metadata() -> dict[str, Any]:
    """현재 추적 메타데이터 반환"""
    return {
        "job_id": _current_job_id.get(),
        "phase": _current_phase.get(),
        "activity": _current_activity.get(),
    }


def flush_langfuse():
    """Langfuse 버퍼 플러시 (graceful shutdown 시 호출)"""
    global _langfuse_client
    if _langfuse_client:
        try:
            _langfuse_client.flush()
            logger.info("Langfuse flushed successfully")
        except Exception as e:
            logger.warning(f"Langfuse flush failed: {e}")


# =============================================================================
# Phase 2: 세션/추적 계층 구조
# =============================================================================

def create_trace_for_job(
    job_id: str,
    user_id: str | None = None,
    metadata: dict | None = None,
) -> str | None:
    """Job용 Langfuse Trace 생성 (세션 레벨)

    결정론적 trace_id(seed=job_id)로 루트 span을 만들고 session/user/tags를
    설정한 뒤 즉시 종료한다. 루트 span duration=0은 의도적인 placeholder —
    실제 작업 구간은 각 activity의 observe_activity 래퍼가 자체 span으로 기록하며,
    모두 같은 trace_id로 귀속된다.
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        trace_context = _trace_context_for_job(client, job_id)
        with client.start_as_current_observation(
            trace_context=trace_context,
            name=f"interview-generation-{job_id}",
            as_type="span",
            input={
                "job_id": job_id,
                "workflow": "InterviewGenerationWorkflow",
                **(metadata or {}),
            },
            metadata=_span_metadata(
                job_id=job_id, extra={"workflow": "InterviewGenerationWorkflow"}
            ),
        ) as span:
            _set_trace_level_attrs(
                session_id=job_id,
                user_id=user_id,
                tags=["workflow", "interview-generation"],
            )
            trace_id = span.trace_id

        logger.debug(f"Created Langfuse trace for job {job_id}: {trace_id}")
        return trace_id
    except Exception as e:
        logger.warning(f"Failed to create Langfuse trace for job {job_id}: {e}")
        return None


def create_span_for_phase(
    job_id: str,
    phase: str,
    trace_id: str | None = None,
    metadata: dict | None = None,
):
    """Phase용 Langfuse Span 생성"""
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        trace_context = (
            {"trace_id": trace_id} if trace_id else _trace_context_for_job(client, job_id)
        )
        span = client.start_observation(
            trace_context=trace_context,
            name=f"phase-{phase}",
            as_type="span",
            input={
                "job_id": job_id,
                "phase": phase,
                **(metadata or {}),
            },
            metadata=_span_metadata(job_id=job_id, phase=phase),
        )

        logger.debug(f"Created Langfuse span for phase {phase}")
        return span
    except Exception as e:
        logger.warning(f"Failed to create Langfuse span for phase {phase}: {e}")
        return None


def end_span(span, status: str = "success", metadata: dict | None = None):
    """Span 종료 (v4: update로 metadata 기록 후 end)"""
    if span is None:
        return

    try:
        span.update(
            metadata={
                "status": status,
                **(metadata or {}),
            }
        )
        span.end()
    except Exception as e:
        logger.debug(f"Failed to end span: {e}")


def log_event(
    name: str,
    metadata: dict | None = None,
    level: str = "DEFAULT",
):
    """Langfuse 이벤트 로깅 — 현재 span의 metadata에 이벤트 정보 병합"""
    if not is_langfuse_enabled():
        return

    try:
        client = get_langfuse_client()
        _update_current_span_safe(
            client,
            metadata={
                "event": name,
                "level": level,
                **(metadata or {}),
            },
        )
    except Exception:
        pass


def score_trace(
    trace_id: str | None,
    name: str,
    value: float,
    comment: str | None = None,
):
    """Trace에 점수 추가 (품질 평가용)"""
    if not is_langfuse_enabled() or not trace_id:
        return

    try:
        client = get_langfuse_client()
        if client:
            client.create_score(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment,
            )
    except Exception as e:
        logger.debug(f"Failed to add score to trace: {e}")


# =============================================================================
# Phase 4: Agent Graph Visualization (Custom Observation Types)
# =============================================================================

def _create_typed_observation(
    as_type: str,
    trace_id: str | None,
    name: str,
    input_data: dict | None,
    output_data: dict | None,
    metadata: dict | None,
):
    """agent/tool/retrieval 공통 observation 생성 헬퍼."""
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        trace_context = {"trace_id": trace_id} if trace_id else None
        observation = client.start_observation(
            trace_context=trace_context,
            name=name,
            as_type=as_type,
            input=input_data,
            output=output_data,
            metadata={
                "observation_type": as_type,
                **(metadata or {}),
            },
        )
        return observation
    except Exception as e:
        logger.warning(f"Failed to create {as_type} observation: {e}")
        return None


def create_agent_observation(
    trace_id: str,
    name: str,
    input_data: dict | None = None,
    output_data: dict | None = None,
    metadata: dict | None = None,
    parent_observation_id: str | None = None,  # kept for signature compatibility
):
    """Agent 타입 Observation 생성"""
    obs = _create_typed_observation(
        as_type="agent",
        trace_id=trace_id,
        name=name,
        input_data=input_data,
        output_data=output_data,
        metadata=metadata,
    )
    if obs:
        logger.debug(f"Created agent observation: {name}")
    return obs


def create_tool_observation(
    trace_id: str,
    name: str,
    input_data: dict | None = None,
    output_data: dict | None = None,
    metadata: dict | None = None,
    parent_observation_id: str | None = None,
):
    """Tool 타입 Observation 생성"""
    obs = _create_typed_observation(
        as_type="tool",
        trace_id=trace_id,
        name=name,
        input_data=input_data,
        output_data=output_data,
        metadata=metadata,
    )
    if obs:
        logger.debug(f"Created tool observation: {name}")
    return obs


def create_retrieval_observation(
    trace_id: str,
    name: str,
    query: str | None = None,
    documents: list[dict] | None = None,
    metadata: dict | None = None,
    parent_observation_id: str | None = None,
):
    """Retrieval 타입 Observation 생성 (RAG)"""
    obs = _create_typed_observation(
        as_type="retriever",
        trace_id=trace_id,
        name=name,
        input_data={"query": query} if query else None,
        output_data={"documents": documents} if documents else None,
        metadata={
            "document_count": len(documents) if documents else 0,
            **(metadata or {}),
        },
    )
    if obs:
        logger.debug(f"Created retrieval observation: {name}")
    return obs


def end_observation(observation, output_data: dict | None = None, status: str = "success"):
    """Observation 종료 (v4: update로 output/metadata 기록 후 end)"""
    if observation is None:
        return

    try:
        update_kwargs: dict[str, Any] = {"metadata": {"status": status}}
        if output_data is not None:
            update_kwargs["output"] = output_data
        observation.update(**update_kwargs)
        observation.end()
    except Exception as e:
        logger.debug(f"Failed to end observation: {e}")


# =============================================================================
# Phase 1: observe_activity 데코레이터
# =============================================================================

def _extract_job_id(args: tuple, kwargs: dict) -> str | None:
    """Activity 인자에서 job_id 추출"""
    for arg in args:
        if isinstance(arg, dict):
            if "job_id" in arg:
                return arg.get("job_id")
            if "raw_input" in arg and isinstance(arg["raw_input"], dict):
                return arg["raw_input"].get("job_id")
    for v in kwargs.values():
        if isinstance(v, dict):
            if "job_id" in v:
                return v.get("job_id")
    return kwargs.get("job_id")


def _safe_serialize(obj: Any, max_length: int = 5000) -> dict | str | list | None:
    """결과를 Langfuse-safe 포맷으로 직렬화"""
    try:
        if obj is None:
            return None
        if isinstance(obj, dict):
            return {
                str(k)[:100]: (
                    _safe_serialize(v, max_length=500) if isinstance(v, (dict, list))
                    else str(v)[:500] if v is not None else None
                )
                for k, v in list(obj.items())[:20]
            }
        if isinstance(obj, list):
            return [
                _safe_serialize(item, max_length=500) if isinstance(item, (dict, list))
                else str(item)[:500] if item is not None else None
                for item in obj[:10]
            ]
        return str(obj)[:max_length]
    except Exception as e:
        return {"type": str(type(obj)), "preview": "serialization_failed", "error": str(e)[:100]}


def observe_activity(name: str, phase: str = "unknown"):
    """Activity용 Langfuse span 래퍼 데코레이터 (Langfuse v4 API)

    start_as_current_observation을 사용해 span을 OTel context의 current span으로
    올려, activity 내부의 LLM generation, 중첩 observe_activity, update_current_span
    호출이 모두 이 span의 자식으로 올바르게 귀속되도록 한다.

    Usage:
        @activity.defn
        @observe_activity(name="analyze_code", phase="analysis")
        async def analyze_code(...):
            ...
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not is_langfuse_enabled():
                return await func(*args, **kwargs)

            job_id = _extract_job_id(args, kwargs)
            client = get_langfuse_client()
            if client is None:
                return await func(*args, **kwargs)

            trace_context = _trace_context_for_job(client, job_id)
            try:
                async_cm = client.start_as_current_observation(
                    trace_context=trace_context,
                    name=name,
                    as_type="span",
                    input={
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                        "job_id": job_id,
                    },
                    metadata=_span_metadata(job_id=job_id, phase=phase, activity=name),
                )
            except Exception as e:
                logger.debug(f"Failed to start Langfuse span for {name}: {e}")
                return await func(*args, **kwargs)

            with async_cm as span:
                _set_trace_level_attrs(
                    session_id=job_id,
                    tags=[f"phase:{phase}", f"activity:{name}"],
                )
                try:
                    with langfuse_trace_context(job_id=job_id, phase=phase, activity=name):
                        result = await func(*args, **kwargs)
                    try:
                        span.update(
                            output=_safe_serialize(result),
                            metadata={"status": "success", "activity": name, "phase": phase},
                        )
                    except Exception:
                        pass
                    return result
                except Exception as e:
                    try:
                        span.update(
                            output={"error": str(e)[:500]},
                            metadata={"status": "error", "activity": name, "phase": phase},
                        )
                    except Exception:
                        pass
                    raise
        return wrapper
    return decorator
