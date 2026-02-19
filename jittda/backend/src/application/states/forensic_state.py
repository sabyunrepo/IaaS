"""
ForensicState — ForensicSupervisor Subgraph (Level 2) 상태 정의.

수집 → 정제 → 진정성 검증 파이프라인의 Worker간 데이터 전달 상태.
서브그래프 내부이므로 Reference Passing보다 직접 전달이 효율적인 경우 허용.
"""
from typing import TypedDict


class ForensicState(TypedDict):
    """ForensicSupervisor 서브그래프 상태."""

    # Input (MetaState에서 주입)
    job_id: str
    github_urls: list[str]
    candidate_username: str | None
    linkedin_url: str | None
    jd_languages: list[str]
    jd_tech_stack: list[str]

    # Collector Worker (W1) 결과
    collected_repos: list[dict]  # [{name, url, languages, loc, ...}]
    repo_local_paths: list[str]  # 클론된 로컬 경로

    # Identity Resolver (W2) 결과
    identity_cluster: dict | None  # IdentityCluster 직렬화
    blame_attributions: list[dict]  # BlameLineAttribution 리스트

    # Semantic Pruner (W3) 결과
    pure_contributions: list[dict]  # PureContribution 리스트
    cleaned_diffs: list[dict]  # 노이즈 제거된 diff

    # 진정성 검증 Workers (W3-5) 결과
    vibector_scores: list[dict]  # WPM 기반 AI 코드 탐지 점수
    clave_fingerprint: dict | None  # 스타일로메트리 지문
    plagiarism_report: dict | None  # MinHash/LSH 표절 보고서

    # Aggregator 통합 결과
    forensic_summary: dict | None  # 전체 포렌식 분석 요약
    authenticity_score: float | None  # 0.0 ~ 1.0
