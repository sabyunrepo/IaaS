"""Git Author 식별 결과 모델 (JIT-35)."""

from pydantic import BaseModel, Field


class AuthorMatch(BaseModel):
    """단일 author 매칭 결과."""

    name: str
    email: str = ""
    commits: int = 0
    confidence: float = Field(ge=0.0, le=1.0, description="매칭 신뢰도 0.0~1.0")
    method: str = Field(description="매칭 방법 (name_exact, noreply_email 등)")
    repos_matched: list[str] = Field(default_factory=list, description="매칭된 레포 목록")


class AuthorIdentityResult(BaseModel):
    """Author 식별 최종 결과 — 복수 후보 + cross-repo 검증."""

    matches: list[AuthorMatch] = Field(default_factory=list)
    best_match: AuthorMatch | None = None
    cross_repo_verified: bool = False
