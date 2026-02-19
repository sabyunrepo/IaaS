"""
Funnel Selection 도메인 모델

순수 Pydantic v2 모델 — 외부 의존성 없음 (pydantic만 허용).
RepoMetadata: 리포지토리 메타데이터 (퍼널 필터링 대상).
FunnelConfig: 3단계 퍼널 설정값.
"""
from pydantic import BaseModel, Field


class RepoMetadata(BaseModel, strict=True):
    """
    리포지토리 메타데이터.

    퍼널 3단계 전반에 걸쳐 사용되는 리포지토리 정보.
    strict=True: 타입 안전성 보장.
    """

    name: str
    owner: str
    url: str
    is_fork: bool
    is_org_repo: bool = False
    days_since_push: int = Field(ge=0)
    languages: list[str] = []
    total_loc: int = Field(ge=0, default=0)
    detected_tech_stack: list[str] = []
    user_contribution_ratio: float = Field(ge=0.0, le=1.0, default=1.0)
    description: str = ""


class FunnelConfig(BaseModel, strict=True):
    """
    퍼널 설정값.

    3단계 퍼널 각각의 임계치와 파라미터를 보유한다.
    strict=True: 타입 안전성 보장.
    """

    min_push_days: int = 365
    min_stars: int = 0
    max_repos: int = 20
    top_k: int = 5
    org_contribution_threshold: float = 0.10
    vector_similarity_min: float = 0.60
