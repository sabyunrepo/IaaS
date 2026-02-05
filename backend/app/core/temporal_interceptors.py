"""
backend/app/core/temporal_interceptors.py
Temporal Worker Interceptors for Activity Monitoring

Features:
- Activity 시작/완료/실패 로깅
- 실행 시간 측정
- 에러 컨텍스트 캡처
- Structlog 통합
"""
import time
from typing import Any

from temporalio import activity
from temporalio.worker import (
    ActivityInboundInterceptor,
    ExecuteActivityInput,
    Interceptor,
)

from app.core.logging import get_logger, bind_job_context, clear_job_context

logger = get_logger("temporal.interceptor")


def _extract_job_id(input: ExecuteActivityInput) -> str | None:
    """Activity 입력에서 job_id 추출

    다양한 Activity 시그니처를 지원:
    - dict 형태의 첫 번째 인자 (input_data, enriched_input 등)
    - kwargs에서 job_id
    """
    # Check args
    for arg in input.args:
        if isinstance(arg, dict):
            # 직접 job_id
            if "job_id" in arg:
                return arg.get("job_id")
            # raw_input 내부 (enriched_input 구조)
            if "raw_input" in arg and isinstance(arg.get("raw_input"), dict):
                return arg["raw_input"].get("job_id")

    # String args에서 job_id 패턴 탐지 (fallback)
    for arg in input.args:
        if isinstance(arg, str) and len(arg) == 36 and "-" in arg:
            # UUID 패턴 (job_id일 가능성)
            return arg

    return None


class ActivityLoggingInterceptor(ActivityInboundInterceptor):
    """Activity 실행 로깅 인터셉터

    모든 Activity 실행을 가로채서:
    1. 시작 시 로깅 (activity_type, workflow_id, job_id)
    2. 완료 시 로깅 (duration_ms)
    3. 실패 시 로깅 (error_type, error_message)
    """

    async def execute_activity(self, input: ExecuteActivityInput) -> Any:
        activity_type = input.fn.__name__
        # Activity 메타데이터는 temporalio.activity.info()로 접근해야 함
        # (ExecuteActivityInput.info는 존재하지 않음)
        info = activity.info()
        workflow_id = info.workflow_id
        task_queue = info.task_queue
        attempt = info.attempt
        job_id = _extract_job_id(input)

        # Structlog 컨텍스트 바인딩
        bind_job_context(job_id=job_id, activity=activity_type)

        # Activity 시작 로깅
        logger.info(
            "activity_started",
            activity_type=activity_type,
            workflow_id=workflow_id,
            task_queue=task_queue,
            attempt=attempt,
            job_id=job_id,
            args_count=len(input.args),
        )

        start_time = time.perf_counter()

        try:
            # 실제 Activity 실행
            result = await super().execute_activity(input)

            # 완료 로깅
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "activity_completed",
                activity_type=activity_type,
                workflow_id=workflow_id,
                job_id=job_id,
                duration_ms=round(duration_ms, 2),
                attempt=attempt,
            )

            return result

        except Exception as e:
            # 실패 로깅
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "activity_failed",
                activity_type=activity_type,
                workflow_id=workflow_id,
                job_id=job_id,
                duration_ms=round(duration_ms, 2),
                attempt=attempt,
                error_type=type(e).__name__,
                error_message=str(e)[:500],
                exc_info=True,
            )
            raise

        finally:
            # 컨텍스트 정리
            clear_job_context()


class MetricsInterceptor(Interceptor):
    """Temporal Worker용 메인 인터셉터

    Worker에 등록하면 모든 Activity 실행에 로깅 인터셉터가 적용됩니다.
    """

    def intercept_activity(
        self,
        next: ActivityInboundInterceptor,
    ) -> ActivityInboundInterceptor:
        """Activity 인바운드 인터셉터 체인에 로깅 인터셉터 추가"""
        return ActivityLoggingInterceptor(next)


def get_worker_interceptors() -> list[Interceptor]:
    """Worker에 등록할 인터셉터 목록 반환

    Usage:
        worker = Worker(
            client,
            task_queue=...,
            workflows=[...],
            activities=[...],
            interceptors=get_worker_interceptors(),
        )
    """
    return [MetricsInterceptor()]
