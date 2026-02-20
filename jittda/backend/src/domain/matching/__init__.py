"""
Funnel Selection 도메인 패키지

공개 API: models, funnel_rules 전체를 여기서 re-export.
"""
from domain.matching.funnel_rules import (
    stage1_hard_filter,
    stage2_relevance_score,
    stage3_should_include,
)
from domain.matching.models import FunnelConfig, RepoMetadata

__all__ = [
    # models
    "RepoMetadata",
    "FunnelConfig",
    # funnel rules
    "stage1_hard_filter",
    "stage2_relevance_score",
    "stage3_should_include",
]
