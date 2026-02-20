"""
LogicSupervisor Subgraph — AST/복잡도/품질 병렬 분석 파이프라인.

Level 2 Supervisor: START → [ast_analyzer, complexity_meter, quality_scanner] (완전 병렬)
                    → logic_aggregator → END
"""
from langgraph.graph import END, START, StateGraph

from application.nodes.logic.aggregator import logic_aggregator
from application.nodes.logic.ast_analyzer import ast_analyzer_worker
from application.nodes.logic.complexity_meter import complexity_meter_worker
from application.nodes.logic.quality_scanner import quality_scanner_worker
from application.states.logic_state import LogicState


def build_logic_graph() -> StateGraph:
    """LogicSupervisor 서브그래프를 구성한다."""
    builder = StateGraph(LogicState)

    # 노드 등록
    builder.add_node("ast_analyzer", ast_analyzer_worker)
    builder.add_node("complexity_meter", complexity_meter_worker)
    builder.add_node("quality_scanner", quality_scanner_worker)
    builder.add_node("logic_aggregator", logic_aggregator)

    # 3개 Worker 완전 병렬
    builder.add_edge(START, "ast_analyzer")
    builder.add_edge(START, "complexity_meter")
    builder.add_edge(START, "quality_scanner")

    # Fan-in
    builder.add_edge("ast_analyzer", "logic_aggregator")
    builder.add_edge("complexity_meter", "logic_aggregator")
    builder.add_edge("quality_scanner", "logic_aggregator")

    builder.add_edge("logic_aggregator", END)

    return builder
