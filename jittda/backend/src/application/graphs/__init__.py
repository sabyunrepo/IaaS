"""Application Graphs — LangGraph StateGraph 정의.

langgraph는 Docker 환경에서만 설치되므로 lazy import 적용.
"""

__all__ = [
    "build_meta_graph",
    "build_forensic_graph",
    "build_logic_graph",
    "build_stack_graph",
]


def __getattr__(name: str):
    if name == "build_meta_graph":
        from application.graphs.meta_graph import build_meta_graph

        return build_meta_graph
    if name == "build_forensic_graph":
        from application.graphs.forensic_graph import build_forensic_graph

        return build_forensic_graph
    if name == "build_logic_graph":
        from application.graphs.logic_graph import build_logic_graph

        return build_logic_graph
    if name == "build_stack_graph":
        from application.graphs.stack_graph import build_stack_graph

        return build_stack_graph
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
