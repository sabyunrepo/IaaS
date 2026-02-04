"""
backend/app/services/activity_logger.py
Activity Logger - Temporal Activity에서 사용하는 로깅 헬퍼

Temporal Activity는 별도 프로세스에서 실행되므로 직접 DB 접근 대신
내부 API를 통해 로그를 기록합니다.
"""
import logging
import time
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class ActivityLogger:
    """Temporal Activity용 로깅 헬퍼.

    Usage:
        log = ActivityLogger(job_id, "document_analysis", "analyzing")
        await log.start("Starting document analysis", {"doc_count": 3})
        await log.progress("Processing document 1/3", {"current": 1})
        await log.result("Completed", {"profiles": [...], "duration_ms": 1234})
    """

    def __init__(
        self,
        job_id: str,
        activity_name: str,
        phase: str,
        base_url: Optional[str] = None,
    ):
        self.job_id = job_id
        self.activity_name = activity_name
        self.phase = phase
        self.base_url = base_url or settings.INTERNAL_API_URL
        self._start_time: Optional[float] = None

    async def _post_log(
        self,
        log_type: str,
        message: Optional[str] = None,
        data: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> bool:
        """Internal API로 로그 전송."""
        payload = {
            "job_id": self.job_id,
            "activity_name": self.activity_name,
            "phase": self.phase,
            "log_type": log_type,
            "message": message,
            "data": data or {},
            "duration_ms": duration_ms,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/internal/analysis-logs",
                    json=payload,
                )
                if response.status_code != 201:
                    logger.warning(f"Failed to post log: {response.status_code} - {response.text}")
                    return False
                return True
        except Exception as e:
            logger.warning(f"Failed to post analysis log: {e}")
            return False

    async def start(
        self,
        message: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> bool:
        """Activity 시작 로그."""
        self._start_time = time.time()
        return await self._post_log(
            log_type="start",
            message=message or f"Starting {self.activity_name}",
            data=data,
        )

    async def progress(
        self,
        message: str,
        data: Optional[dict] = None,
    ) -> bool:
        """Activity 진행 상황 로그."""
        return await self._post_log(
            log_type="progress",
            message=message,
            data=data,
        )

    async def result(
        self,
        message: Optional[str] = None,
        data: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> bool:
        """Activity 결과 로그."""
        if duration_ms is None and self._start_time:
            duration_ms = int((time.time() - self._start_time) * 1000)

        return await self._post_log(
            log_type="result",
            message=message or f"Completed {self.activity_name}",
            data=data,
            duration_ms=duration_ms,
        )

    async def error(
        self,
        message: str,
        data: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> bool:
        """Activity 에러 로그."""
        if duration_ms is None and self._start_time:
            duration_ms = int((time.time() - self._start_time) * 1000)

        return await self._post_log(
            log_type="error",
            message=message,
            data=data,
            duration_ms=duration_ms,
        )


class SyncActivityLogger:
    """동기 Activity용 로깅 헬퍼 (httpx 동기 버전)."""

    def __init__(
        self,
        job_id: str,
        activity_name: str,
        phase: str,
        base_url: Optional[str] = None,
    ):
        self.job_id = job_id
        self.activity_name = activity_name
        self.phase = phase
        self.base_url = base_url or settings.INTERNAL_API_URL
        self._start_time: Optional[float] = None

    def _post_log(
        self,
        log_type: str,
        message: Optional[str] = None,
        data: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> bool:
        """Internal API로 로그 전송 (동기)."""
        payload = {
            "job_id": self.job_id,
            "activity_name": self.activity_name,
            "phase": self.phase,
            "log_type": log_type,
            "message": message,
            "data": data or {},
            "duration_ms": duration_ms,
        }

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{self.base_url}/api/internal/analysis-logs",
                    json=payload,
                )
                if response.status_code != 201:
                    logger.warning(f"Failed to post log: {response.status_code}")
                    return False
                return True
        except Exception as e:
            logger.warning(f"Failed to post analysis log: {e}")
            return False

    def start(
        self,
        message: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> bool:
        """Activity 시작 로그."""
        self._start_time = time.time()
        return self._post_log(
            log_type="start",
            message=message or f"Starting {self.activity_name}",
            data=data,
        )

    def progress(
        self,
        message: str,
        data: Optional[dict] = None,
    ) -> bool:
        """Activity 진행 상황 로그."""
        return self._post_log(
            log_type="progress",
            message=message,
            data=data,
        )

    def result(
        self,
        message: Optional[str] = None,
        data: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> bool:
        """Activity 결과 로그."""
        if duration_ms is None and self._start_time:
            duration_ms = int((time.time() - self._start_time) * 1000)

        return self._post_log(
            log_type="result",
            message=message or f"Completed {self.activity_name}",
            data=data,
            duration_ms=duration_ms,
        )

    def error(
        self,
        message: str,
        data: Optional[dict] = None,
        duration_ms: Optional[int] = None,
    ) -> bool:
        """Activity 에러 로그."""
        if duration_ms is None and self._start_time:
            duration_ms = int((time.time() - self._start_time) * 1000)

        return self._post_log(
            log_type="error",
            message=message,
            data=data,
            duration_ms=duration_ms,
        )
