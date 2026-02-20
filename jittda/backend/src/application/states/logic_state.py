"""
LogicState — LogicSupervisor Subgraph (Level 2) 상태 정의.

AST 분석 + 복잡도 측정 + 정적 분석 병렬 파이프라인 상태.
"""
from typing import TypedDict


class LogicState(TypedDict):
    """LogicSupervisor 서브그래프 상태."""

    # Input (MetaState에서 주입)
    job_id: str
    cleaned_diffs: list[dict]  # ForensicSupervisor 또는 직접 주입
    repo_local_paths: list[str]
    jd_languages: list[str]  # JD 요구 언어 (확장자 필터링용, 비어있으면 전체)

    # ASTAnalyzer Worker (W6) 결과
    ast_analysis: list[dict]  # 함수/클래스 구조, 패턴, 의존성

    # ComplexityMeter Worker (W7) 결과
    complexity_metrics: list[dict]  # CC, Halstead, MI (ComplexityMetrics 직렬화)

    # QualityScanner Worker (W8) 결과
    quality_report: dict | None  # SonarQube 정적 분석 결과

    # Aggregator 통합 결과
    logic_summary: dict | None  # 전체 로직 분석 요약
    logic_score: float | None  # 0.0 ~ 100.0
