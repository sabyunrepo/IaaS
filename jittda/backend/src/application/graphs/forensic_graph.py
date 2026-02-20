"""
ForensicSupervisor Subgraph — 수집/정제/진정성 검증 파이프라인.

Level 2 Supervisor: collector → identity_resolver → semantic_pruner
                    → [vibector, clave, datasketch] (병렬) → aggregator
"""
from langgraph.graph import END, START, StateGraph

from application.nodes.forensic.aggregator import forensic_aggregator
from application.nodes.forensic.clave import clave_worker
from application.nodes.forensic.collector import collector_worker
from application.nodes.forensic.datasketch_node import datasketch_worker
from application.nodes.forensic.identity_resolver import identity_resolver_worker
from application.nodes.forensic.semantic_pruner_node import semantic_pruner_worker
from application.nodes.forensic.vibector import vibector_worker
from application.states.forensic_state import ForensicState


def build_forensic_graph() -> StateGraph:
    """ForensicSupervisor 서브그래프를 구성한다."""
    builder = StateGraph(ForensicState)

    # 노드 등록
    builder.add_node("collector", collector_worker)
    builder.add_node("identity_resolver", identity_resolver_worker)
    builder.add_node("semantic_pruner", semantic_pruner_worker)
    builder.add_node("vibector", vibector_worker)
    builder.add_node("clave", clave_worker)
    builder.add_node("datasketch", datasketch_worker)
    builder.add_node("forensic_aggregator", forensic_aggregator)

    # 순차: collector → identity_resolver → semantic_pruner
    builder.add_edge(START, "collector")
    builder.add_edge("collector", "identity_resolver")
    builder.add_edge("identity_resolver", "semantic_pruner")

    # 병렬: pruner 후 진정성 검증 3개 동시
    builder.add_edge("semantic_pruner", "vibector")
    builder.add_edge("semantic_pruner", "clave")
    builder.add_edge("semantic_pruner", "datasketch")

    # Fan-in: 3개 결과 → aggregator
    builder.add_edge("vibector", "forensic_aggregator")
    builder.add_edge("clave", "forensic_aggregator")
    builder.add_edge("datasketch", "forensic_aggregator")

    builder.add_edge("forensic_aggregator", END)

    return builder
