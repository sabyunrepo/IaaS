"""
AnalysisPipeline Workflow — Temporal 메인 오케스트레이션.

LangGraph MetaGraph를 완전 대체한다.
각 Activity가 자율 에이전트로서 Observe→Reason→Act 패턴으로 동작한다.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

# Activity 함수 참조는 문자열 기반으로 해결 (sandbox 호환)
with workflow.unsafe.imports_passed_through():
    from application.temporal.activities import (
        collector_agent,
        enhancement_agent,
        forensic_agent,
        input_agent,
        logic_agent,
        output_agent,
        plan_agent,
        profile_agent,
        quality_gate_agent,
        question_orchestrator_agent,
        stack_agent,
    )

# 기본 재시도 정책: 최대 3회, 1초 간격, 2배 백오프
DEFAULT_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_attempts=3,
    maximum_interval=timedelta(seconds=30),
)

# LLM 호출이 포함된 Activity 재시도: 더 관대한 정책
LLM_RETRY = RetryPolicy(
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_attempts=2,
    maximum_interval=timedelta(seconds=60),
)


@workflow.defn
class AnalysisPipeline:
    """메인 분석 파이프라인 — Temporal이 오케스트레이션, 각 Activity가 자율 에이전트."""

    @workflow.run
    async def run(self, job_id: str) -> dict:
        state = {
            "job_id": job_id,
            "input_data_ref": job_id,
            "identity_cluster_ref": None,
            "repo_paths_ref": None,
            "forensic_result_ref": None,
            "logic_result_ref": None,
            "stack_result_ref": None,
            "profile_ref": None,
            "candidate_scores": None,
            "questions_ref": None,
            "status": "pending",
            "current_phase": "input_router",
            "revision_count": 0,
            "_quality_verdict": "",
            "errors": [],
        }

        try:
            return await self._execute_pipeline(state)
        except Exception as e:
            state["status"] = "failed"
            state["errors"].append(f"workflow: {e!s}")
            # 실패해도 output_agent로 결과 조립 시도
            try:
                delta = await workflow.execute_activity(
                    output_agent,
                    state,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=DEFAULT_RETRY,
                )
                state.update(delta)
            except Exception:
                pass  # output_agent도 실패하면 현재 state 그대로 반환
            return state

    async def _execute_pipeline(self, state: dict) -> dict:
        """파이프라인 실행 — 워크플로우 본체."""
        # Phase 1: Input + Plan (순차)
        delta = await workflow.execute_activity(
            input_agent,
            state,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=DEFAULT_RETRY,
        )
        state.update(delta)

        delta = await workflow.execute_activity(
            plan_agent,
            state,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=DEFAULT_RETRY,
        )
        state.update(delta)

        # Phase 2: Collection
        delta = await workflow.execute_activity(
            collector_agent,
            state,
            start_to_close_timeout=timedelta(minutes=3),
            heartbeat_timeout=timedelta(seconds=30),
            retry_policy=DEFAULT_RETRY,
        )
        state.update(delta)

        # Phase 3: Analysis (Forensic + Logic 병렬)
        forensic_task = workflow.execute_activity(
            forensic_agent,
            state,
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=LLM_RETRY,
        )
        logic_task = workflow.execute_activity(
            logic_agent,
            state,
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=LLM_RETRY,
        )
        forensic_delta, logic_delta = await asyncio.gather(forensic_task, logic_task)
        state.update(forensic_delta)
        state.update(logic_delta)

        # Phase 3.5: Stack (Forensic + Logic 완료 후)
        delta = await workflow.execute_activity(
            stack_agent,
            state,
            start_to_close_timeout=timedelta(minutes=3),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=LLM_RETRY,
        )
        state.update(delta)

        # Phase 4: Profile Synthesis
        delta = await workflow.execute_activity(
            profile_agent,
            state,
            start_to_close_timeout=timedelta(seconds=90),
            retry_policy=LLM_RETRY,
        )
        state.update(delta)

        # Phase 5: Question Generation + Enhancement
        delta = await workflow.execute_activity(
            question_orchestrator_agent,
            state,
            start_to_close_timeout=timedelta(minutes=3),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=LLM_RETRY,
        )
        state.update(delta)

        delta = await workflow.execute_activity(
            enhancement_agent,
            state,
            start_to_close_timeout=timedelta(minutes=3),
            heartbeat_timeout=timedelta(seconds=60),
            retry_policy=LLM_RETRY,
        )
        state.update(delta)

        # Phase 6: Quality Gate (최대 3회 루프)
        for _attempt in range(3):
            delta = await workflow.execute_activity(
                quality_gate_agent,
                state,
                start_to_close_timeout=timedelta(seconds=90),
                retry_policy=LLM_RETRY,
            )
            state.update(delta)

            if state.get("_quality_verdict") == "approve":
                break

            # Revise: 질문 재생성 + 보강
            delta = await workflow.execute_activity(
                question_orchestrator_agent,
                state,
                start_to_close_timeout=timedelta(minutes=3),
                heartbeat_timeout=timedelta(seconds=60),
                retry_policy=LLM_RETRY,
            )
            state.update(delta)

            delta = await workflow.execute_activity(
                enhancement_agent,
                state,
                start_to_close_timeout=timedelta(minutes=3),
                heartbeat_timeout=timedelta(seconds=60),
                retry_policy=LLM_RETRY,
            )
            state.update(delta)

        # Phase 7: Output Assembly
        delta = await workflow.execute_activity(
            output_agent,
            state,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=DEFAULT_RETRY,
        )
        state.update(delta)

        return state
