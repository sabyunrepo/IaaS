"""
Temporal Activities — 각 분석 단계를 자율 에이전트 Activity로 래핑.

기존 노드 함수를 Temporal Activity로 래핑하여 재사용한다.
각 Activity는 MetaState dict를 받아 state delta dict를 반환한다.
Redis PubSub을 통해 실시간 진행률 이벤트를 발행한다.

에러 분류:
  - Recoverable (재시도 대상): 네트워크, 타임아웃, LLM 파싱 실패
  - Fatal (즉시 실패): 입력 검증, 키 누락, 코드 버그
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, NoReturn

from temporalio import activity
from temporalio.exceptions import ApplicationError

from infrastructure.observability import traced_activity

logger = logging.getLogger(__name__)

# Fatal (non-retryable) 에러 타입: 재시도해도 결과 동일
_FATAL_ERROR_TYPES = (
    ValueError,
    KeyError,
    TypeError,
    AttributeError,
    ImportError,
    PermissionError,
    FileNotFoundError,
)


def _classify_and_raise(e: Exception, activity_name: str) -> NoReturn:
    """에러를 분류하여 Temporal에 적절히 전파한다.

    Fatal 에러: ApplicationError(non_retryable=True) → 재시도 안 함
    Recoverable 에러: 원본 예외를 그대로 raise → Temporal 재시도 정책 적용
    """
    if isinstance(e, _FATAL_ERROR_TYPES):
        logger.error(
            "Fatal error in %s (non-retryable): %s: %s",
            activity_name, type(e).__name__, e,
        )
        raise ApplicationError(
            f"{activity_name}: {type(e).__name__}: {e}",
            non_retryable=True,
        ) from e
    # Recoverable: 그대로 raise → Temporal retry policy 적용
    logger.warning(
        "Recoverable error in %s (will retry): %s: %s",
        activity_name, type(e).__name__, e,
    )
    raise e

# 노드별 진행률 + 라벨 (events.py 대체)
NODE_PROGRESS: dict[str, tuple[float, str]] = {
    "input_router": (0.05, "입력 분석"),
    "plan_generator": (0.10, "실행 계획 수립"),
    "repo_collector": (0.15, "리포 수집"),
    "forensic_supervisor": (0.35, "코드 포렌식 분석"),
    "logic_supervisor": (0.50, "로직 분석"),
    "stack_supervisor": (0.60, "스택 분석"),
    "profile_synthesizer": (0.70, "프로필 종합"),
    "question_orchestrator": (0.80, "질문 생성"),
    "enhancement_agents": (0.88, "질문 보강"),
    "quality_gate": (0.93, "품질 검증"),
    "output_assembler": (0.98, "결과 조립"),
}


# 모듈 레벨 Redis 연결 풀 (Worker 프로세스당 1개)
_redis_pool: Any = None
_redis_lock = asyncio.Lock()


async def _get_redis() -> Any:
    """Redis 연결 풀 싱글턴을 반환한다 (concurrency-safe)."""
    global _redis_pool
    if _redis_pool is not None:
        return _redis_pool
    async with _redis_lock:
        # double-check after acquiring lock
        if _redis_pool is not None:
            return _redis_pool
        import redis.asyncio as aioredis

        redis_url = os.environ.get("REDIS_URL", "")
        if not redis_url:
            return None
        _redis_pool = aioredis.from_url(redis_url)
    return _redis_pool


async def init_redis_pool() -> None:
    """Worker startup 시 Redis 풀을 미리 초기화한다."""
    await _get_redis()


async def close_redis_pool() -> None:
    """Worker 종료 시 Redis 연결 풀을 정리한다."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


async def _publish_event(job_id: str, node_name: str, extra: dict[str, Any] | None = None) -> None:
    """Redis PubSub으로 진행률 이벤트 발행."""
    try:
        r = await _get_redis()
        if r is None:
            return

        progress, label = NODE_PROGRESS.get(node_name, (0.0, node_name))
        event = {
            "type": "node_complete",
            "node": node_name,
            "progress": progress,
            "label": label,
        }
        if extra:
            event.update(extra)

        await r.publish(f"job:{job_id}:events", json.dumps(event, default=str))
    except Exception as e:
        logger.warning("Failed to publish event for %s/%s: %s", job_id, node_name, e)


def _build_meta_state(job_id: str, state_data: dict[str, Any]) -> dict[str, Any]:
    """Activity가 받은 state dict에서 MetaState를 구성한다."""
    return {
        "job_id": job_id,
        "input_data_ref": state_data.get("input_data_ref", job_id),
        "identity_cluster_ref": state_data.get("identity_cluster_ref"),
        "repo_paths_ref": state_data.get("repo_paths_ref"),
        "forensic_result_ref": state_data.get("forensic_result_ref"),
        "logic_result_ref": state_data.get("logic_result_ref"),
        "stack_result_ref": state_data.get("stack_result_ref"),
        "profile_ref": state_data.get("profile_ref"),
        "candidate_scores": state_data.get("candidate_scores"),
        "questions_ref": state_data.get("questions_ref"),
        "status": state_data.get("status", "pending"),
        "current_phase": state_data.get("current_phase", "input_router"),
        "revision_count": state_data.get("revision_count", 0),
        "_quality_verdict": state_data.get("_quality_verdict", ""),
        "errors": state_data.get("errors", []),
    }


# ===========================================================================
# Agent Activities — 기존 노드 함수 래핑
# ===========================================================================


@activity.defn
@traced_activity
async def input_agent(args: dict[str, Any]) -> dict[str, Any]:
    """InputAgent — 입력 파싱 + 분석 경로 결정."""
    from application.nodes.meta.input_router import input_router_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)
    try:
        result = await input_router_node(state)
    except Exception as e:
        _classify_and_raise(e, "input_agent")
    await _publish_event(job_id, "input_router")
    return result


@activity.defn
@traced_activity
async def plan_agent(args: dict[str, Any]) -> dict[str, Any]:
    """PlanAgent — 실행 계획 수립."""
    from application.nodes.meta.plan_generator import plan_generator_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)
    try:
        result = await plan_generator_node(state)
    except Exception as e:
        _classify_and_raise(e, "plan_agent")
    await _publish_event(job_id, "plan_generator")
    return result


@activity.defn
@traced_activity
async def collector_agent(args: dict[str, Any]) -> dict[str, Any]:
    """CollectorAgent — 리포 수집 + 필터링 + Clone."""
    from application.nodes.meta.repo_collector import repo_collector_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)

    activity.heartbeat("리포 수집 시작")
    try:
        result = await repo_collector_node(state)
    except Exception as e:
        _classify_and_raise(e, "collector_agent")
    activity.heartbeat("리포 수집 완료")

    await _publish_event(job_id, "repo_collector")
    return result


@activity.defn
@traced_activity
async def forensic_agent(args: dict[str, Any]) -> dict[str, Any]:
    """ForensicAgent — 포렌식 분석 파이프라인."""
    from application.nodes.meta.supervisor_adapters import forensic_supervisor_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)

    activity.heartbeat("포렌식 분석 시작")
    try:
        result = await forensic_supervisor_node(state)
    except Exception as e:
        _classify_and_raise(e, "forensic_agent")
    activity.heartbeat("포렌식 분석 완료")

    await _publish_event(job_id, "forensic_supervisor")
    return result


@activity.defn
@traced_activity
async def logic_agent(args: dict[str, Any]) -> dict[str, Any]:
    """LogicAgent — 로직 분석 파이프라인."""
    from application.nodes.meta.supervisor_adapters import logic_supervisor_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)

    activity.heartbeat("로직 분석 시작")
    try:
        result = await logic_supervisor_node(state)
    except Exception as e:
        _classify_and_raise(e, "logic_agent")
    activity.heartbeat("로직 분석 완료")

    await _publish_event(job_id, "logic_supervisor")
    return result


@activity.defn
@traced_activity
async def stack_agent(args: dict[str, Any]) -> dict[str, Any]:
    """StackAgent — 기술 스택 분석."""
    from application.nodes.meta.supervisor_adapters import stack_supervisor_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)

    activity.heartbeat("스택 분석 시작")
    try:
        result = await stack_supervisor_node(state)
    except Exception as e:
        _classify_and_raise(e, "stack_agent")
    activity.heartbeat("스택 분석 완료")

    await _publish_event(job_id, "stack_supervisor")
    return result


@activity.defn
@traced_activity
async def profile_agent(args: dict[str, Any]) -> dict[str, Any]:
    """ProfileAgent — 4축 점수 + 신뢰도 산출."""
    from application.nodes.meta.profile_synthesizer import profile_synthesizer_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)
    try:
        result = await profile_synthesizer_node(state)
    except Exception as e:
        _classify_and_raise(e, "profile_agent")
    await _publish_event(job_id, "profile_synthesizer")
    return result


@activity.defn
@traced_activity
async def question_orchestrator_agent(args: dict[str, Any]) -> dict[str, Any]:
    """QuestionOrchestratorAgent — 전략 기반 질문 생성."""
    from application.nodes.meta.question_orchestrator import question_orchestrator_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)

    activity.heartbeat("질문 생성 시작")
    try:
        result = await question_orchestrator_node(state)
    except Exception as e:
        _classify_and_raise(e, "question_orchestrator_agent")
    activity.heartbeat("질문 생성 완료")

    await _publish_event(job_id, "question_orchestrator")
    return result


@activity.defn
@traced_activity
async def enhancement_agent(args: dict[str, Any]) -> dict[str, Any]:
    """EnhancementAgent — 5개 보강 에이전트 병렬 실행."""
    from application.nodes.meta.enhancement_agents import enhancement_agents_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)

    activity.heartbeat("질문 보강 시작")
    try:
        result = await enhancement_agents_node(state)
    except Exception as e:
        _classify_and_raise(e, "enhancement_agent")
    activity.heartbeat("질문 보강 완료")

    await _publish_event(job_id, "enhancement_agents")
    return result


@activity.defn
@traced_activity
async def quality_gate_agent(args: dict[str, Any]) -> dict[str, Any]:
    """QualityGateAgent — 개별 질문 평가 + 타겟 개선."""
    from application.nodes.meta.quality_gate import quality_gate_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)
    try:
        result = await quality_gate_node(state)
    except Exception as e:
        _classify_and_raise(e, "quality_gate_agent")
    await _publish_event(job_id, "quality_gate")
    return result


@activity.defn
@traced_activity
async def output_agent(args: dict[str, Any]) -> dict[str, Any]:
    """OutputAgent — 최종 면접 스크립트 조립."""
    from application.nodes.meta.output_assembler import output_assembler_node

    job_id = args["job_id"]
    state = _build_meta_state(job_id, args)
    try:
        result = await output_assembler_node(state)
    except Exception as e:
        _classify_and_raise(e, "output_agent")
    await _publish_event(job_id, "output_assembler")
    return result


# 모든 Activity 함수 목록 (Worker 등록용)
ALL_ACTIVITIES = [
    input_agent,
    plan_agent,
    collector_agent,
    forensic_agent,
    logic_agent,
    stack_agent,
    profile_agent,
    question_orchestrator_agent,
    enhancement_agent,
    quality_gate_agent,
    output_agent,
]
