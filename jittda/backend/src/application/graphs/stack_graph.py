"""
StackSupervisor Subgraph — 기술 스택 전문성 분석 파이프라인.

Level 2 Supervisor: START → [skill_extractor, api_depth, architecture_evaluator] (완전 병렬)
                    → stack_aggregator → END

의존성: LogicSupervisor 완료 후 실행 (AST 결과 필요)
"""
from langgraph.graph import END, START, StateGraph

from application.nodes.stack.aggregator import stack_aggregator
from application.nodes.stack.api_depth import api_depth_worker
from application.nodes.stack.architecture_evaluator import architecture_evaluator_worker
from application.nodes.stack.skill_extractor import skill_extractor_worker
from application.states.stack_state import StackState


def build_stack_graph() -> StateGraph:
    """StackSupervisor 서브그래프를 구성한다."""
    builder = StateGraph(StackState)

    # 노드 등록
    builder.add_node("skill_extractor", skill_extractor_worker)
    builder.add_node("api_depth_analyzer", api_depth_worker)
    builder.add_node("architecture_evaluator", architecture_evaluator_worker)
    builder.add_node("stack_aggregator", stack_aggregator)

    # 3개 Worker 완전 병렬
    builder.add_edge(START, "skill_extractor")
    builder.add_edge(START, "api_depth_analyzer")
    builder.add_edge(START, "architecture_evaluator")

    # Fan-in
    builder.add_edge("skill_extractor", "stack_aggregator")
    builder.add_edge("api_depth_analyzer", "stack_aggregator")
    builder.add_edge("architecture_evaluator", "stack_aggregator")

    builder.add_edge("stack_aggregator", END)

    return builder
