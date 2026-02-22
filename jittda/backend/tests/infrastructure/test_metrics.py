"""
Prometheus Metrics 테스트

- 메트릭 등록 확인
- 카운터 증가
- Histogram 기록
- Circuit breaker gauge 업데이트
- get_metrics_response() 포맷 확인
"""
import pytest

from infrastructure.observability.metrics import (
    _CB_STATE_MAP,
    circuit_breaker_state,
    circuit_breaker_trips_total,
    get_metrics_response,
    http_requests_total,
    job_duration_seconds,
    jobs_total,
    llm_calls_total,
    llm_call_duration_seconds,
    update_circuit_breaker_metric,
)


class TestMetricDefinitions:
    """메트릭이 올바르게 정의되었는지 확인."""

    def test_jobs_total_has_status_label(self):
        # Counter에 labels가 정의되어 있는지 확인
        labeled = jobs_total.labels(status="completed")
        assert labeled is not None

    def test_llm_calls_total_has_model_and_response_model_labels(self):
        labeled = llm_calls_total.labels(model="kimi-k2.5", response_model="JDSummary")
        assert labeled is not None

    def test_circuit_breaker_state_has_service_label(self):
        labeled = circuit_breaker_state.labels(service="github")
        assert labeled is not None

    def test_http_requests_total_has_method_path_status_labels(self):
        labeled = http_requests_total.labels(method="GET", path="/health", status="200")
        assert labeled is not None


class TestCounterIncrement:
    """카운터 증가 동작 확인."""

    def test_jobs_total_increments(self):
        before = jobs_total.labels(status="test_inc")._value.get()
        jobs_total.labels(status="test_inc").inc()
        after = jobs_total.labels(status="test_inc")._value.get()
        assert after == before + 1

    def test_llm_calls_total_increments(self):
        before = llm_calls_total.labels(
            model="test-model", response_model="TestModel"
        )._value.get()
        llm_calls_total.labels(model="test-model", response_model="TestModel").inc()
        after = llm_calls_total.labels(
            model="test-model", response_model="TestModel"
        )._value.get()
        assert after == before + 1


class TestHistogram:
    """Histogram 기록 동작 확인."""

    def test_job_duration_observes(self):
        # observe() 호출이 에러 없이 실행되는지 확인
        job_duration_seconds.observe(45.2)

    def test_llm_call_duration_observes(self):
        llm_call_duration_seconds.labels(model="kimi-k2.5").observe(3.5)


class TestCircuitBreakerMetric:
    """Circuit breaker gauge 업데이트 확인."""

    def test_cb_state_map_values(self):
        assert _CB_STATE_MAP == {"closed": 0, "open": 1, "half_open": 2}

    def test_update_sets_gauge(self):
        update_circuit_breaker_metric("test-svc", "open")
        val = circuit_breaker_state.labels(service="test-svc")._value.get()
        assert val == 1

    def test_update_closed_sets_zero(self):
        update_circuit_breaker_metric("test-svc2", "closed")
        val = circuit_breaker_state.labels(service="test-svc2")._value.get()
        assert val == 0

    def test_update_half_open_sets_two(self):
        update_circuit_breaker_metric("test-svc3", "half_open")
        val = circuit_breaker_state.labels(service="test-svc3")._value.get()
        assert val == 2


class TestGetMetricsResponse:
    """Prometheus scrape 응답 포맷 확인."""

    def test_returns_bytes_and_content_type(self):
        body, content_type = get_metrics_response()
        assert isinstance(body, bytes)
        assert "text/plain" in content_type or "text/openmetrics" in content_type

    def test_response_contains_metric_names(self):
        body, _ = get_metrics_response()
        text = body.decode("utf-8")
        assert "jittda_jobs_total" in text
        assert "jittda_llm_calls_total" in text
        assert "jittda_circuit_breaker_state" in text
        assert "jittda_http_requests_total" in text
