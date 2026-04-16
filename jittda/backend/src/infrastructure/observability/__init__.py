"""Observability — Langfuse tracing + Prometheus metrics."""

from infrastructure.observability.trace_decorator import traced_activity

__all__ = ["traced_activity"]
