"""
backend/app/core/observability.py
Langfuse LLM observability — LiteLLM callback + @observe 데코레이터 방식
"""
import logging
import os
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_initialized = False
_langfuse_client = None

# Context variables for trace metadata
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

        # Langfuse 3.x 호환을 위해 langfuse_otel (OpenTelemetry 기반) 사용
        # 참고: https://docs.litellm.ai/docs/observability/langfuse_otel_integration
        litellm.callbacks = ["langfuse_otel"]

        # LiteLLM reads these env vars automatically, but set explicitly
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.LANGFUSE_PUBLIC_KEY)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.LANGFUSE_SECRET_KEY)
        os.environ.setdefault("LANGFUSE_HOST", settings.LANGFUSE_HOST)
        # langfuse_otel은 LANGFUSE_OTEL_HOST 환경 변수 사용
        os.environ.setdefault("LANGFUSE_OTEL_HOST", settings.LANGFUSE_HOST)

        # Initialize Langfuse client for @observe decorator
        get_langfuse_client()

        _initialized = True
        logger.info(f"Langfuse enabled → {settings.LANGFUSE_HOST}")
        return True
    except Exception as e:
        logger.warning(f"Langfuse setup failed: {e}")
        return False


@contextmanager
def langfuse_trace_context(
    job_id: str | None = None,
    phase: str | None = None,
    activity: str | None = None,
):
    """Langfuse 추적 컨텍스트 설정

    Usage:
        with langfuse_trace_context(job_id="123", phase="question_generation"):
            await llm.run(prompt)
    """
    # Save previous values
    prev_job_id = _current_job_id.get()
    prev_phase = _current_phase.get()
    prev_activity = _current_activity.get()

    # Set new values
    if job_id:
        _current_job_id.set(job_id)
    if phase:
        _current_phase.set(phase)
    if activity:
        _current_activity.set(activity)

    try:
        # Update langfuse context if available
        if is_langfuse_enabled():
            try:
                # Langfuse v3.x: import from langfuse directly
                try:
                    from langfuse import langfuse_context
                except ImportError:
                    # Fallback for older versions
                    from langfuse.decorators import langfuse_context
                langfuse_context.update_current_trace(
                    session_id=job_id,
                    metadata={
                        "job_id": job_id,
                        "phase": phase,
                        "activity": activity,
                    },
                    tags=[f"phase:{phase}", f"activity:{activity}"] if phase else None,
                )
            except Exception as e:
                logger.debug(f"langfuse_context update skipped: {e}")
        yield
    finally:
        # Restore previous values
        _current_job_id.set(prev_job_id)
        _current_phase.set(prev_phase)
        _current_activity.set(prev_activity)


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

    Returns:
        trace_id if successful, None otherwise
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        # Langfuse v3.x: Use start_span which automatically creates a trace
        # The span.trace_id contains the generated trace ID
        span = client.start_span(
            name=f"interview-generation-{job_id}",
            input={
                "job_id": job_id,
                "workflow": "InterviewGenerationWorkflow",
                **(metadata or {}),
            },
        )

        # Update trace metadata
        span.update_trace(
            name=f"interview-generation-{job_id}",
            session_id=job_id,
            user_id=user_id,
            tags=["workflow", "interview-generation"],
            metadata={
                "job_id": job_id,
                "workflow": "InterviewGenerationWorkflow",
            },
        )

        trace_id = span.trace_id
        span.end()  # End immediately, just to register the trace

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
    """Phase용 Langfuse Span 생성

    Returns:
        span object if successful, None otherwise
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        # Langfuse v3.x: Use start_span (trace_id is not a parameter)
        # If trace_id is needed, it should be managed externally
        span = client.start_span(
            name=f"phase-{phase}",
            input={
                "job_id": job_id,
                "phase": phase,
                **(metadata or {}),
            },
        )

        # Set session_id via update_trace
        span.update_trace(session_id=job_id)

        logger.debug(f"Created Langfuse span for phase {phase}")
        return span
    except Exception as e:
        logger.warning(f"Failed to create Langfuse span for phase {phase}: {e}")
        return None


def end_span(span, status: str = "success", metadata: dict | None = None):
    """Span 종료"""
    if span is None:
        return

    try:
        span.end(
            metadata={
                "status": status,
                **(metadata or {}),
            }
        )
    except Exception as e:
        logger.debug(f"Failed to end span: {e}")


def log_event(
    name: str,
    metadata: dict | None = None,
    level: str = "DEFAULT",
):
    """Langfuse 이벤트 로깅

    Args:
        name: 이벤트 이름
        metadata: 추가 메타데이터
        level: 로그 레벨 (DEFAULT, DEBUG, WARNING, ERROR)
    """
    if not is_langfuse_enabled():
        return

    try:
        # Langfuse v3.x: import from langfuse directly
        try:
            from langfuse import langfuse_context
        except ImportError:
            from langfuse.decorators import langfuse_context
        langfuse_context.update_current_observation(
            metadata={
                "event": name,
                "level": level,
                **(metadata or {}),
            }
        )
    except Exception:
        pass  # 이벤트 로깅 실패는 무시


def score_trace(
    trace_id: str | None,
    name: str,
    value: float,
    comment: str | None = None,
):
    """Trace에 점수 추가 (품질 평가용)

    Args:
        trace_id: Langfuse trace ID
        name: 점수 이름 (e.g., "quality", "relevance")
        value: 점수 값 (0.0 ~ 1.0)
        comment: 코멘트
    """
    if not is_langfuse_enabled() or not trace_id:
        return

    try:
        client = get_langfuse_client()
        if client:
            # Langfuse v3.x: Use create_score
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

def create_agent_observation(
    trace_id: str,
    name: str,
    input_data: dict | None = None,
    output_data: dict | None = None,
    metadata: dict | None = None,
    parent_observation_id: str | None = None,
):
    """Agent 타입 Observation 생성 (Agent Graph 시각화용).

    Args:
        trace_id: 연결할 Trace ID (v3에서는 무시됨)
        name: Agent 이름
        input_data: 입력 데이터
        output_data: 출력 데이터
        metadata: 추가 메타데이터
        parent_observation_id: 부모 Observation ID (계층 구조)

    Returns:
        생성된 Observation 또는 None
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        # Langfuse v3.x: Use start_span (without trace_id parameter)
        observation = client.start_span(
            name=name,
            input=input_data,
            metadata={
                "observation_type": "agent",
                "trace_id_hint": trace_id,  # Store for reference
                **(metadata or {}),
            },
        )
        if output_data:
            observation.update(output=output_data)
        logger.debug(f"Created agent observation: {name}")
        return observation
    except Exception as e:
        logger.warning(f"Failed to create agent observation: {e}")
        return None


def create_tool_observation(
    trace_id: str,
    name: str,
    input_data: dict | None = None,
    output_data: dict | None = None,
    metadata: dict | None = None,
    parent_observation_id: str | None = None,
):
    """Tool 타입 Observation 생성 (Agent Graph 시각화용).

    Args:
        trace_id: 연결할 Trace ID (v3에서는 무시됨)
        name: Tool 이름
        input_data: 입력 데이터
        output_data: 출력 데이터
        metadata: 추가 메타데이터
        parent_observation_id: 부모 Observation ID

    Returns:
        생성된 Observation 또는 None
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        # Langfuse v3.x: Use start_span (without trace_id parameter)
        observation = client.start_span(
            name=name,
            input=input_data,
            metadata={
                "observation_type": "tool",
                "trace_id_hint": trace_id,  # Store for reference
                **(metadata or {}),
            },
        )
        if output_data:
            observation.update(output=output_data)
        logger.debug(f"Created tool observation: {name}")
        return observation
    except Exception as e:
        logger.warning(f"Failed to create tool observation: {e}")
        return None


def create_retrieval_observation(
    trace_id: str,
    name: str,
    query: str | None = None,
    documents: list[dict] | None = None,
    metadata: dict | None = None,
    parent_observation_id: str | None = None,
):
    """Retrieval 타입 Observation 생성 (RAG Agent Graph 시각화용).

    Args:
        trace_id: 연결할 Trace ID (v3에서는 무시됨)
        name: Retrieval 이름
        query: 검색 쿼리
        documents: 검색된 문서 목록
        metadata: 추가 메타데이터
        parent_observation_id: 부모 Observation ID

    Returns:
        생성된 Observation 또는 None
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        # Langfuse v3.x: Use start_span (without trace_id parameter)
        observation = client.start_span(
            name=name,
            input={"query": query} if query else None,
            metadata={
                "observation_type": "retrieval",
                "document_count": len(documents) if documents else 0,
                "trace_id_hint": trace_id,  # Store for reference
                **(metadata or {}),
            },
        )
        if documents:
            observation.update(output={"documents": documents})
        logger.debug(f"Created retrieval observation: {name}")
        return observation
    except Exception as e:
        logger.warning(f"Failed to create retrieval observation: {e}")
        return None


def end_observation(observation, output_data: dict | None = None, status: str = "success"):
    """Observation 종료 (Agent Graph 노드 완료 마킹).

    Args:
        observation: 종료할 Observation 객체
        output_data: 출력 데이터
        status: 완료 상태 (success/error)
    """
    if observation is None:
        return

    try:
        observation.end(
            output=output_data,
            metadata={"status": status},
        )
    except Exception as e:
        logger.debug(f"Failed to end observation: {e}")


# =============================================================================
# Phase 1: @observe 데코레이터 래퍼
# =============================================================================

def _extract_job_id(args: tuple, kwargs: dict) -> str | None:
    """Activity 인자에서 job_id 추출"""
    # Check positional args
    for arg in args:
        if isinstance(arg, dict):
            if "job_id" in arg:
                return arg.get("job_id")
            # enriched_input 또는 input_data 내부 검사
            if "raw_input" in arg and isinstance(arg["raw_input"], dict):
                return arg["raw_input"].get("job_id")
    # Check kwargs
    for v in kwargs.values():
        if isinstance(v, dict):
            if "job_id" in v:
                return v.get("job_id")
    # Check direct job_id kwarg
    return kwargs.get("job_id")


def _safe_serialize(obj: Any, max_length: int = 5000) -> dict | str | list | None:
    """결과를 Langfuse-safe 포맷으로 직렬화

    Args:
        obj: 직렬화할 객체
        max_length: 최대 문자열 길이

    Returns:
        직렬화된 결과 (dict, str, list, or None)
    """
    try:
        if obj is None:
            return None
        if isinstance(obj, dict):
            # 딕셔너리: 최대 20개 키, 각 값 500자 제한
            return {
                str(k)[:100]: (
                    _safe_serialize(v, max_length=500) if isinstance(v, (dict, list))
                    else str(v)[:500] if v is not None else None
                )
                for k, v in list(obj.items())[:20]
            }
        if isinstance(obj, list):
            # 리스트: 최대 10개 항목
            return [
                _safe_serialize(item, max_length=500) if isinstance(item, (dict, list))
                else str(item)[:500] if item is not None else None
                for item in obj[:10]
            ]
        # 기타 타입: 문자열로 변환
        return str(obj)[:max_length]
    except Exception as e:
        return {"type": str(type(obj)), "preview": "serialization_failed", "error": str(e)[:100]}


def observe_activity(name: str, phase: str = "unknown"):
    """Activity용 Langfuse span 래퍼 데코레이터

    Temporal Activity에 Langfuse 추적을 추가합니다.
    동적 @observe 대신 직접 span을 생성하여 output을 명시적으로 기록합니다.
    @activity.defn 데코레이터 아래에 위치해야 합니다.

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
            job_id = _extract_job_id(args, kwargs)

            if is_langfuse_enabled():
                span = None
                try:
                    client = get_langfuse_client()
                    if client:
                        # 1. Span 시작 (동적 @observe 대신 직접 생성)
                        span = client.start_span(
                            name=name,
                            input={
                                "args_count": len(args),
                                "kwargs_keys": list(kwargs.keys()),
                                "job_id": job_id,
                            },
                        )
                        # Trace 메타데이터 업데이트
                        span.update_trace(
                            session_id=job_id,
                            tags=[f"phase:{phase}", f"activity:{name}"],
                        )

                    # 2. Activity 실행
                    with langfuse_trace_context(job_id=job_id, phase=phase, activity=name):
                        result = await func(*args, **kwargs)

                    # 3. Output 명시적 기록 (update 후 end)
                    if span:
                        span.update(
                            output=_safe_serialize(result),
                            metadata={"status": "success", "activity": name, "phase": phase},
                        )
                        span.end()

                    return result
                except Exception as e:
                    # 에러 시에도 span 종료
                    if span:
                        span.update(
                            output={"error": str(e)[:500]},
                            metadata={"status": "error", "activity": name, "phase": phase},
                        )
                        span.end()
                    raise
            else:
                return await func(*args, **kwargs)
        return wrapper
    return decorator
