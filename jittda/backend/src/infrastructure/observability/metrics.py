"""Prometheus Metrics — 애플리케이션 메트릭 수집.

prometheus_client를 래핑하여 Jittda 전용 메트릭을 정의한다.
/metrics 엔드포인트에서 Prometheus scrape 포맷으로 노출.
"""
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# --- Job Metrics ---
jobs_total = Counter(
    "jittda_jobs_total",
    "Total jobs processed",
    ["status"],  # created, completed, failed
)

job_duration_seconds = Histogram(
    "jittda_job_duration_seconds",
    "Job processing duration in seconds",
    buckets=[30, 60, 120, 300, 600, 900, 1800],
)

# --- LLM Metrics ---
llm_calls_total = Counter(
    "jittda_llm_calls_total",
    "Total LLM API calls",
    ["model", "response_model"],
)

llm_call_duration_seconds = Histogram(
    "jittda_llm_call_duration_seconds",
    "LLM call duration in seconds",
    ["model"],
    buckets=[1, 2, 5, 10, 30, 60],
)

# --- Circuit Breaker Metrics ---
circuit_breaker_state = Gauge(
    "jittda_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["service"],
)

circuit_breaker_trips_total = Counter(
    "jittda_circuit_breaker_trips_total",
    "Total circuit breaker trips to open state",
    ["service"],
)

# --- HTTP Metrics ---
http_requests_total = Counter(
    "jittda_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "jittda_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)


def get_metrics_response() -> tuple[bytes, str]:
    """Prometheus scrape 응답을 생성한다.

    Returns:
        (body_bytes, content_type) 튜플.
    """
    return generate_latest(), CONTENT_TYPE_LATEST


_CB_STATE_MAP = {"closed": 0, "open": 1, "half_open": 2}


def update_circuit_breaker_metric(service: str, state: str) -> None:
    """Circuit breaker gauge를 업데이트한다."""
    circuit_breaker_state.labels(service=service).set(
        _CB_STATE_MAP.get(state, 0)
    )
