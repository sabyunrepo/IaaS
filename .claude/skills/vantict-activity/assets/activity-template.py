"""
Activity Template — Vantict Sniper v4.0

사용법:
1. 이 파일을 복사하여 backend/app/workflows/activities/{name}.py 생성
2. {Name}, {name}, {description} 플레이스홀더를 실제 값으로 교체
3. backend/app/workflows/worker.py에 Activity 등록
"""

from dataclasses import dataclass
from temporalio import activity

from app.services.cached_llm import CachedLLMService
from app.services.activity_logger import ActivityLogger


# ============================================================
# Input / Output
# ============================================================


@dataclass
class {Name}Input:
    """Activity 입력 데이터."""

    job_id: str
    # TODO: 필요한 입력 필드 추가


@dataclass
class {Name}Output:
    """Activity 출력 데이터."""

    job_id: str
    # TODO: 필요한 출력 필드 추가


# ============================================================
# Activity
# ============================================================


@activity.defn
async def {name}(input: {Name}Input) -> {Name}Output:
    """
    {description}

    Args:
        input: {Name}Input

    Returns:
        {Name}Output
    """
    logger = ActivityLogger("{name}")
    logger.info(f"Starting {name} for job {input.job_id}")

    try:
        # --- Heartbeat (30초 이상 작업 시 필수) ---
        activity.heartbeat(f"Starting {name}")

        # --- LLM 호출 (필요 시) ---
        llm = CachedLLMService()
        # result = await llm.generate(
        #     prompt="...",
        #     cache_key=f"{name}:{input.job_id}",
        # )

        # --- 비즈니스 로직 ---
        # TODO: 구현

        activity.heartbeat(f"Completed {name}")

        return {Name}Output(
            job_id=input.job_id,
            # TODO: 출력 필드 설정
        )

    except Exception as e:
        logger.error(f"Failed {name}: {e}")
        # RetryableError: 재시도 가능 (외부 API 장애 등)
        # NonRetryableError: 재시도 불가 (입력 검증 실패 등)
        raise


# ============================================================
# Worker 등록 (worker.py에 추가)
# ============================================================
# from app.workflows.activities.{name} import {name}
# activities=[..., {name}]
