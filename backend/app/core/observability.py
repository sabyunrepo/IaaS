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

        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]

        # LiteLLM reads these env vars automatically, but set explicitly
        os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.LANGFUSE_PUBLIC_KEY)
        os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.LANGFUSE_SECRET_KEY)
        os.environ.setdefault("LANGFUSE_HOST", settings.LANGFUSE_HOST)

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

        trace = client.trace(
            name=f"interview-generation-{job_id}",
            session_id=job_id,
            user_id=user_id,
            metadata={
                "job_id": job_id,
                "workflow": "InterviewGenerationWorkflow",
                **(metadata or {}),
            },
            tags=["workflow", "interview-generation"],
        )
        logger.debug(f"Created Langfuse trace for job {job_id}: {trace.id}")
        return trace.id
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

        span = client.span(
            name=f"phase-{phase}",
            trace_id=trace_id,
            metadata={
                "job_id": job_id,
                "phase": phase,
                **(metadata or {}),
            },
        )
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
            client.score(
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
        trace_id: 연결할 Trace ID
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

        observation = client.span(
            trace_id=trace_id,
            name=name,
            input=input_data,
            output=output_data,
            metadata={
                "observation_type": "agent",
                **(metadata or {}),
            },
            parent_observation_id=parent_observation_id,
        )
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
        trace_id: 연결할 Trace ID
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

        observation = client.span(
            trace_id=trace_id,
            name=name,
            input=input_data,
            output=output_data,
            metadata={
                "observation_type": "tool",
                **(metadata or {}),
            },
            parent_observation_id=parent_observation_id,
        )
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
        trace_id: 연결할 Trace ID
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

        observation = client.span(
            trace_id=trace_id,
            name=name,
            input={"query": query} if query else None,
            output={"documents": documents} if documents else None,
            metadata={
                "observation_type": "retrieval",
                "document_count": len(documents) if documents else 0,
                **(metadata or {}),
            },
            parent_observation_id=parent_observation_id,
        )
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

def observe_activity(name: str, phase: str = "unknown"):
    """Activity용 Langfuse @observe 래퍼 데코레이터

    Temporal Activity에 Langfuse 추적을 추가합니다.
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
            # job_id 추출 시도 (dict 인자에서)
            job_id = None
            for arg in args:
                if isinstance(arg, dict):
                    if "job_id" in arg:
                        job_id = arg.get("job_id")
                        break
                    # enriched_input 또는 input_data 내부 검사
                    if "raw_input" in arg and isinstance(arg["raw_input"], dict):
                        job_id = arg["raw_input"].get("job_id")
                        break
            for v in kwargs.values():
                if isinstance(v, dict):
                    if "job_id" in v:
                        job_id = v.get("job_id")
                        break

            if is_langfuse_enabled():
                try:
                    from langfuse.decorators import observe
                    observed_func = observe(name=name)(func)
                    with langfuse_trace_context(job_id=job_id, phase=phase, activity=name):
                        return await observed_func(*args, **kwargs)
                except Exception as e:
                    logger.debug(f"@observe wrapper failed, running without: {e}")
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)
        return wrapper
    return decorator
