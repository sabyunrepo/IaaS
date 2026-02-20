"""
StackState — StackSupervisor Subgraph (Level 2) 상태 정의.

기술 스택 전문성 분석 파이프라인 상태.
LogicSupervisor의 AST 결과에 의존한다.
"""
from typing import TypedDict


class StackState(TypedDict):
    """StackSupervisor 서브그래프 상태."""

    # Input (MetaState + LogicSupervisor에서 주입)
    job_id: str
    ast_analysis: list[dict]  # LogicSupervisor의 ASTAnalyzer 결과 (의존)
    cleaned_diffs: list[dict]
    jd_tech_stack: list[str]

    # SkillExtractor Worker (W9) 결과
    skill_extraction: dict | None  # {skills: [SkillAssessment], ...}

    # APIDepthAnalyzer Worker (W10) 결과
    api_depth_scores: list[dict]  # [{api, depth, usage_count, ...}]

    # ArchitectureEvaluator Worker (W11) 결과
    architecture_eval: dict | None  # {patterns, layers, coupling, ...}

    # Aggregator 통합 결과
    stack_summary: dict | None  # 전체 스택 분석 요약
    mastery_score: float | None  # 0.0 ~ 100.0
