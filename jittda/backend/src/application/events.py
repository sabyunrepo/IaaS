"""
Pipeline Event Publisher — 노드 실행 이벤트를 구조화하여 발행한다.

MetaGraph의 astream 업데이트를 사용자 친화적 이벤트로 변환한다.
WebSocket을 통해 클라이언트에 실시간 진행률을 전달하는 데 사용된다.
"""
from __future__ import annotations

from typing import Any

# 노드별 진행률 매핑 (progress: 0.0 ~ 1.0, label: 한국어 UI 표시용)
NODE_PROGRESS: dict[str, tuple[float, str]] = {
    "input_router": (0.05, "입력 분석"),
    "plan_generator": (0.10, "실행 계획 수립"),
    "forensic_supervisor": (0.30, "코드 포렌식 분석"),
    "logic_supervisor": (0.45, "로직 분석"),
    "stack_supervisor": (0.55, "스택 분석"),
    "profile_synthesizer": (0.65, "프로필 종합"),
    "question_orchestrator": (0.75, "질문 생성"),
    "enhancement_agents": (0.85, "질문 보강"),
    "quality_gate": (0.90, "품질 검증"),
    "output_assembler": (0.95, "결과 조립"),
}


def build_node_event(node_name: str, state_update: dict[str, Any]) -> dict[str, Any]:
    """astream 업데이트로부터 구조화된 노드 이벤트를 생성한다.

    Args:
        node_name: LangGraph 노드 이름.
        state_update: 해당 노드가 반환한 state delta.

    Returns:
        클라이언트에 전달할 구조화된 이벤트 dict.
    """
    progress, label = NODE_PROGRESS.get(node_name, (0.0, node_name))
    errors = state_update.get("errors", [])
    status = state_update.get("status", "")

    return {
        "type": "node_complete",
        "node": node_name,
        "progress": progress,
        "label": label,
        "status": status,
        "has_errors": bool(errors),
    }
