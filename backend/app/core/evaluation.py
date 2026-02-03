"""
backend/app/core/evaluation.py
Langfuse 평가 기능: Dataset, Score, Metrics 유틸리티
"""
import logging
from typing import Any

from app.core.observability import is_langfuse_enabled, get_langfuse_client

logger = logging.getLogger(__name__)


# =============================================================================
# Score Configuration - 사전 정의된 평가 점수 타입
# =============================================================================

SCORE_CONFIGS = {
    # 품질 평가 점수
    "question_quality": {
        "name": "question_quality",
        "data_type": "NUMERIC",
        "description": "면접 질문의 전반적인 품질 (0.0-1.0)",
        "min_value": 0.0,
        "max_value": 1.0,
    },
    "relevance": {
        "name": "relevance",
        "data_type": "NUMERIC",
        "description": "JD와 질문의 관련성 (0.0-1.0)",
        "min_value": 0.0,
        "max_value": 1.0,
    },
    "difficulty_accuracy": {
        "name": "difficulty_accuracy",
        "data_type": "CATEGORICAL",
        "description": "난이도 적절성",
        "categories": ["too_easy", "appropriate", "too_hard"],
    },
    "completion_status": {
        "name": "completion_status",
        "data_type": "CATEGORICAL",
        "description": "Job 완료 상태",
        "categories": ["success", "partial", "failed"],
    },
    # Boolean 평가
    "has_follow_ups": {
        "name": "has_follow_ups",
        "data_type": "BOOLEAN",
        "description": "후속 질문 포함 여부",
    },
    "has_terminology": {
        "name": "has_terminology",
        "data_type": "BOOLEAN",
        "description": "용어 설명 포함 여부",
    },
}


def get_score_config(score_name: str) -> dict | None:
    """사전 정의된 Score 설정 반환."""
    return SCORE_CONFIGS.get(score_name)


def list_score_configs() -> list[str]:
    """사용 가능한 Score 이름 목록 반환."""
    return list(SCORE_CONFIGS.keys())


# =============================================================================
# Score 생성 유틸리티
# =============================================================================

def create_score(
    trace_id: str,
    name: str,
    value: float | str | bool,
    observation_id: str | None = None,
    comment: str | None = None,
    data_type: str | None = None,
) -> dict | None:
    """Langfuse Score 생성.

    Args:
        trace_id: 연결할 Trace ID
        name: Score 이름 (SCORE_CONFIGS에 정의된 것 권장)
        value: 점수 값 (NUMERIC: float, CATEGORICAL: str, BOOLEAN: bool)
        observation_id: 특정 Observation에 연결 (선택)
        comment: 코멘트 (선택)
        data_type: 데이터 타입 (자동 추론 가능)

    Returns:
        생성된 Score 정보 또는 None (Langfuse 비활성화 시)
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        # Score config에서 data_type 자동 설정
        if data_type is None and name in SCORE_CONFIGS:
            data_type = SCORE_CONFIGS[name].get("data_type")

        score = client.score(
            trace_id=trace_id,
            name=name,
            value=value,
            observation_id=observation_id,
            comment=comment,
            data_type=data_type,
        )

        logger.debug(f"Created score: {name}={value} for trace {trace_id}")
        return {"id": score.id if hasattr(score, "id") else None, "name": name, "value": value}

    except Exception as e:
        logger.warning(f"Failed to create score: {e}")
        return None


def create_scores_batch(
    trace_id: str,
    scores: list[dict],
) -> list[dict]:
    """여러 Score 일괄 생성.

    Args:
        trace_id: 연결할 Trace ID
        scores: [{"name": str, "value": any, "comment": str | None}, ...]

    Returns:
        생성된 Score 목록
    """
    results = []
    for score_data in scores:
        result = create_score(
            trace_id=trace_id,
            name=score_data["name"],
            value=score_data["value"],
            comment=score_data.get("comment"),
        )
        if result:
            results.append(result)
    return results


# =============================================================================
# Dataset 관리 유틸리티
# =============================================================================

def create_dataset(
    name: str,
    description: str | None = None,
    metadata: dict | None = None,
) -> dict | None:
    """평가용 Dataset 생성.

    Args:
        name: Dataset 이름
        description: 설명
        metadata: 추가 메타데이터

    Returns:
        생성된 Dataset 정보 또는 None
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        dataset = client.create_dataset(
            name=name,
            description=description,
            metadata=metadata or {},
        )

        logger.info(f"Created dataset: {name}")
        return {
            "id": dataset.id if hasattr(dataset, "id") else None,
            "name": name,
            "description": description,
        }

    except Exception as e:
        logger.warning(f"Failed to create dataset: {e}")
        return None


def add_dataset_item(
    dataset_name: str,
    input_data: dict,
    expected_output: dict | None = None,
    metadata: dict | None = None,
) -> dict | None:
    """Dataset에 평가 항목 추가.

    Args:
        dataset_name: Dataset 이름
        input_data: 입력 데이터
        expected_output: 기대 출력 (선택)
        metadata: 추가 메타데이터

    Returns:
        생성된 Item 정보 또는 None
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        item = client.create_dataset_item(
            dataset_name=dataset_name,
            input=input_data,
            expected_output=expected_output,
            metadata=metadata or {},
        )

        logger.debug(f"Added item to dataset: {dataset_name}")
        return {
            "id": item.id if hasattr(item, "id") else None,
            "dataset_name": dataset_name,
        }

    except Exception as e:
        logger.warning(f"Failed to add dataset item: {e}")
        return None


def get_dataset(name: str) -> Any | None:
    """Dataset 조회.

    Args:
        name: Dataset 이름

    Returns:
        Dataset 객체 또는 None
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        return client.get_dataset(name)

    except Exception as e:
        logger.warning(f"Failed to get dataset: {e}")
        return None


# =============================================================================
# Interview Generation 전용 Dataset 템플릿
# =============================================================================

def create_interview_evaluation_dataset(
    name: str = "interview-generation-benchmark",
    description: str = "면접 스크립트 생성 품질 평가용 데이터셋",
) -> dict | None:
    """면접 생성 평가용 Dataset 템플릿 생성."""
    return create_dataset(
        name=name,
        description=description,
        metadata={
            "type": "evaluation",
            "domain": "interview-generation",
            "version": "v1",
            "expected_fields": {
                "input": ["jd_text", "experience_level", "output_language"],
                "output": ["question_count", "categories", "has_follow_ups"],
            },
        },
    )


def add_interview_test_case(
    dataset_name: str,
    jd_text: str,
    experience_level: str = "시니어",
    output_language: str = "ko",
    expected_question_count: int = 25,
    expected_categories: list[str] | None = None,
    metadata: dict | None = None,
) -> dict | None:
    """면접 생성 평가 테스트 케이스 추가."""
    if expected_categories is None:
        expected_categories = [
            "role_fit",
            "technical_depth",
            "execution_ownership",
            "communication",
            "risk_flags",
        ]

    return add_dataset_item(
        dataset_name=dataset_name,
        input_data={
            "jd_text": jd_text,
            "experience_level": experience_level,
            "output_language": output_language,
        },
        expected_output={
            "question_count": expected_question_count,
            "categories": expected_categories,
            "has_follow_ups": True,
            "has_terminology": True,
            "has_evaluation_scenarios": True,
        },
        metadata=metadata or {},
    )


# =============================================================================
# Metrics 조회 유틸리티
# =============================================================================

def get_trace_metrics(
    trace_id: str,
) -> dict | None:
    """특정 Trace의 메트릭 조회.

    Args:
        trace_id: Trace ID

    Returns:
        메트릭 정보 또는 None
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        # Trace 조회
        trace = client.get_trace(trace_id)
        if not trace:
            return None

        return {
            "trace_id": trace_id,
            "name": trace.name if hasattr(trace, "name") else None,
            "input_tokens": trace.input if hasattr(trace, "input") else None,
            "output_tokens": trace.output if hasattr(trace, "output") else None,
            "total_cost": trace.total_cost if hasattr(trace, "total_cost") else None,
            "latency_ms": trace.latency if hasattr(trace, "latency") else None,
            "scores": trace.scores if hasattr(trace, "scores") else [],
        }

    except Exception as e:
        logger.warning(f"Failed to get trace metrics: {e}")
        return None


def get_session_metrics(
    session_id: str,
) -> dict | None:
    """특정 Session(Job)의 메트릭 조회.

    Args:
        session_id: Session ID (= Job ID)

    Returns:
        세션 메트릭 정보 또는 None
    """
    if not is_langfuse_enabled():
        return None

    try:
        client = get_langfuse_client()
        if not client:
            return None

        # Session의 모든 Trace 조회
        traces = client.get_traces(session_id=session_id)
        if not traces:
            return None

        total_cost = 0.0
        total_latency = 0
        trace_count = 0

        for trace in traces.data if hasattr(traces, "data") else []:
            trace_count += 1
            if hasattr(trace, "total_cost") and trace.total_cost:
                total_cost += trace.total_cost
            if hasattr(trace, "latency") and trace.latency:
                total_latency += trace.latency

        return {
            "session_id": session_id,
            "trace_count": trace_count,
            "total_cost": total_cost,
            "total_latency_ms": total_latency,
            "avg_latency_ms": total_latency / trace_count if trace_count > 0 else 0,
        }

    except Exception as e:
        logger.warning(f"Failed to get session metrics: {e}")
        return None
