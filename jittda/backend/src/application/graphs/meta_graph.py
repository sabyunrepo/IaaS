"""
MetaAgent Graph — 전체 파이프라인 오케스트레이션 (Level 1).

Phase 0-1: input_router → plan_generator (순차)
Phase 2: forensic_supervisor || logic_supervisor → stack_supervisor (Fan-out)
Phase 2.5: profile_synthesizer (Fan-in)
Phase 3-4: question_orchestrator → quality_gate (조건부 루프, 최대 2회)
Phase 5: output_assembler → END
"""
from langgraph.graph import END, START, StateGraph

from application.nodes.meta.input_router import input_router_node
from application.nodes.meta.output_assembler import output_assembler_node
from application.nodes.meta.plan_generator import plan_generator_node
from application.nodes.meta.profile_synthesizer import profile_synthesizer_node
from application.nodes.meta.quality_gate import quality_gate_node, should_revise
from application.nodes.meta.supervisor_adapters import (
    forensic_supervisor_node,
    logic_supervisor_node,
    stack_supervisor_node,
)
from application.states.meta_state import MetaState


def build_meta_graph() -> StateGraph:
    """MetaAgent 전체 파이프라인 그래프를 구성한다."""
    builder = StateGraph(MetaState)

    # 노드 등록
    builder.add_node("input_router", input_router_node)
    builder.add_node("plan_generator", plan_generator_node)
    builder.add_node("forensic_supervisor", forensic_supervisor_node)
    builder.add_node("logic_supervisor", logic_supervisor_node)
    builder.add_node("stack_supervisor", stack_supervisor_node)
    builder.add_node("profile_synthesizer", profile_synthesizer_node)
    builder.add_node("quality_gate", quality_gate_node)
    builder.add_node("output_assembler", output_assembler_node)

    # Phase 0-1: 순차
    builder.add_edge(START, "input_router")
    builder.add_edge("input_router", "plan_generator")

    # Phase 2: Fan-out (forensic || logic → stack)
    builder.add_edge("plan_generator", "forensic_supervisor")
    builder.add_edge("plan_generator", "logic_supervisor")
    builder.add_edge("logic_supervisor", "stack_supervisor")  # AST 의존

    # Phase 2.5: Fan-in
    builder.add_edge("forensic_supervisor", "profile_synthesizer")
    builder.add_edge("stack_supervisor", "profile_synthesizer")

    # Phase 3-4: quality_gate → 조건부 루프
    builder.add_edge("profile_synthesizer", "quality_gate")

    builder.add_conditional_edges(
        "quality_gate",
        should_revise,
        {"revise": "quality_gate", "approve": "output_assembler"},
    )

    # Phase 5: 최종 출력
    builder.add_edge("output_assembler", END)

    return builder
