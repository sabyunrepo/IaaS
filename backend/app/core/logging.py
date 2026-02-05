"""
backend/app/core/logging.py
Structlog 기반 구조화 로깅 설정

Features:
- JSON 포맷 (production) / 컬러 콘솔 (development)
- 컨텍스트 변수 자동 바인딩 (job_id, phase, activity)
- 표준 logging 모듈과 통합
"""
import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.typing import EventDict

from app.core.config import settings


# =============================================================================
# Context Variables for Structured Logging
# =============================================================================

_job_id: ContextVar[str | None] = ContextVar("log_job_id", default=None)
_phase: ContextVar[str | None] = ContextVar("log_phase", default=None)
_activity: ContextVar[str | None] = ContextVar("log_activity", default=None)


def bind_job_context(
    job_id: str | None = None,
    phase: str | None = None,
    activity: str | None = None,
) -> None:
    """로깅 컨텍스트에 Job 관련 정보 바인딩

    Usage:
        bind_job_context(job_id="abc123", phase="analysis")
        logger.info("Processing started")  # job_id, phase 자동 포함
    """
    if job_id is not None:
        _job_id.set(job_id)
    if phase is not None:
        _phase.set(phase)
    if activity is not None:
        _activity.set(activity)


def clear_job_context() -> None:
    """로깅 컨텍스트 초기화"""
    _job_id.set(None)
    _phase.set(None)
    _activity.set(None)


class JobContextMiddleware:
    """Context Manager for Job-scoped logging"""

    def __init__(
        self,
        job_id: str | None = None,
        phase: str | None = None,
        activity: str | None = None,
    ):
        self.job_id = job_id
        self.phase = phase
        self.activity = activity
        self._prev_job_id: str | None = None
        self._prev_phase: str | None = None
        self._prev_activity: str | None = None

    def __enter__(self):
        # Save previous values
        self._prev_job_id = _job_id.get()
        self._prev_phase = _phase.get()
        self._prev_activity = _activity.get()
        # Set new values
        bind_job_context(
            job_id=self.job_id,
            phase=self.phase,
            activity=self.activity,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous values
        _job_id.set(self._prev_job_id)
        _phase.set(self._prev_phase)
        _activity.set(self._prev_activity)
        return False


# =============================================================================
# Structlog Processors
# =============================================================================

def add_job_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """컨텍스트 변수에서 Job 정보를 자동으로 추가"""
    job_id = _job_id.get()
    phase = _phase.get()
    activity = _activity.get()

    if job_id:
        event_dict["job_id"] = job_id
    if phase:
        event_dict["phase"] = phase
    if activity:
        event_dict["activity"] = activity

    return event_dict


def add_service_info(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """서비스 정보 추가"""
    event_dict["service"] = "vantict-sniper"
    event_dict["version"] = "4.0.0"
    return event_dict


def drop_color_message_key(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """uvicorn의 color_message 키 제거 (JSON 출력 시)"""
    event_dict.pop("color_message", None)
    return event_dict


# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging() -> None:
    """Structlog + 표준 logging 통합 설정

    - Development: 컬러 콘솔 출력
    - Production: JSON 포맷 출력
    """
    # JSON vs Console 포맷 결정
    is_json = not settings.is_local

    # Shared processors (전처리)
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,  # contextvars 병합
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_job_context,  # Job 컨텍스트 자동 추가
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_json:
        # Production: JSON 포맷
        shared_processors.extend([
            add_service_info,
            drop_color_message_key,
            structlog.processors.format_exc_info,
        ])
        renderer = structlog.processors.JSONRenderer()
    else:
        # Development: 컬러 콘솔 포맷
        shared_processors.append(
            structlog.dev.set_exc_info,
        )
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Structlog 설정
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 표준 logging 설정 (structlog와 통합)
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Root handler 설정
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)

    # Temporal 로거는 INFO 유지 (디버깅 유용)
    logging.getLogger("temporalio").setLevel(logging.INFO)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Structlog 로거 인스턴스 반환

    Usage:
        logger = get_logger(__name__)
        logger.info("Processing", item_count=42)
    """
    return structlog.get_logger(name)


# =============================================================================
# Convenience Functions
# =============================================================================

def log_activity_start(
    activity_name: str,
    job_id: str | None = None,
    **extra: Any,
) -> None:
    """Activity 시작 로깅 (표준화된 포맷)"""
    logger = get_logger("activity")
    with JobContextMiddleware(job_id=job_id, activity=activity_name):
        logger.info(
            "activity_started",
            activity=activity_name,
            **extra,
        )


def log_activity_complete(
    activity_name: str,
    job_id: str | None = None,
    duration_ms: float | None = None,
    **extra: Any,
) -> None:
    """Activity 완료 로깅 (표준화된 포맷)"""
    logger = get_logger("activity")
    with JobContextMiddleware(job_id=job_id, activity=activity_name):
        logger.info(
            "activity_completed",
            activity=activity_name,
            duration_ms=duration_ms,
            **extra,
        )


def log_activity_error(
    activity_name: str,
    error: Exception,
    job_id: str | None = None,
    **extra: Any,
) -> None:
    """Activity 에러 로깅 (표준화된 포맷)"""
    logger = get_logger("activity")
    with JobContextMiddleware(job_id=job_id, activity=activity_name):
        logger.error(
            "activity_failed",
            activity=activity_name,
            error_type=type(error).__name__,
            error_message=str(error)[:500],
            **extra,
            exc_info=True,
        )


def log_llm_call(
    activity_name: str,
    model: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    duration_ms: float | None = None,
    cache_hit: bool = False,
    job_id: str | None = None,
    **extra: Any,
) -> None:
    """LLM 호출 로깅 (표준화된 포맷)"""
    logger = get_logger("llm")
    with JobContextMiddleware(job_id=job_id, activity=activity_name):
        logger.info(
            "llm_call",
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=duration_ms,
            cache_hit=cache_hit,
            **extra,
        )
