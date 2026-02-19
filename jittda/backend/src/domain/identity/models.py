"""
Identity Resolution 도메인 모델

순수 Pydantic v2 모델 — 외부 의존성 없음 (pydantic만 허용).
모든 데이터는 불변(frozen=True) 또는 strict=True로 타입 안전성을 보장.
"""
from enum import StrEnum

from pydantic import BaseModel, Field


class ConfidenceLevel(StrEnum):
    """신뢰도 수준 — Git 저자 동일인 판별 신뢰도."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GitAuthor(BaseModel, frozen=True):
    """Git 커밋 로그에서 추출한 저자 정보."""

    name: str
    email: str


class GitHubProfile(BaseModel, frozen=True):
    """GitHub API에서 가져온 프로필 정보."""

    name: str
    email: str
    login: str
    database_id: str


class MailmapEntry(BaseModel, frozen=True):
    """
    Git mailmap 매핑 엔트리.

    하나의 canonical 정체성(canonical_name / canonical_email)에
    alias 이름/이메일을 연결하고, 그 신뢰도를 기록한다.
    """

    canonical: str
    canonical_email: str
    alias_name: str
    alias_email: str
    confidence: ConfidenceLevel


class IdentityCluster(BaseModel, strict=True):
    """
    동일인으로 판정된 Git 저자 클러스터.

    하나의 GitHub 계정(github_node_id)에 복수의 alias를 묶고,
    전체 커밋 수 및 검증된 커밋 수를 추적한다.
    """

    github_node_id: str
    canonical_name: str
    canonical_email: str
    aliases: list[MailmapEntry]
    total_commits: int = Field(default=0, ge=0)
    verified_commits: int = Field(default=0, ge=0)

    @property
    def verification_ratio(self) -> float:
        """검증된 커밋 비율. total_commits == 0 이면 0.0 반환."""
        if self.total_commits == 0:
            return 0.0
        return self.verified_commits / self.total_commits


class BlameLineAttribution(BaseModel, strict=True):
    """
    git blame 라인 하나에 대한 저자 귀속 정보.

    is_move / is_copy / is_whitespace_only 플래그로
    순수 로직 기여 여부를 판별한다.
    """

    file_path: str
    line_number: int = Field(ge=1)
    content: str
    author_name: str
    author_email: str
    commit_sha: str
    is_move: bool
    is_copy: bool
    is_whitespace_only: bool

    @property
    def is_meaningful_contribution(self) -> bool:
        """
        실질적 기여 여부.

        이동(move), 복사(copy), 공백 전용(whitespace) 라인이 아닐 때만 True.
        """
        return not (self.is_move or self.is_copy or self.is_whitespace_only)


class PureContribution(BaseModel, strict=True):
    """
    파일 단위 순수 로직 기여량.

    import / 주석 / 설정 / 자동생성 코드를 제거한 후의
    실질 로직 라인 수와 함수 본문을 기록한다.
    """

    file_path: str
    language: str
    total_lines: int = Field(ge=0)
    pure_logic_lines: int = Field(ge=0)
    removed_imports: int = Field(ge=0)
    removed_comments: int = Field(ge=0)
    removed_config: int = Field(ge=0)
    removed_generated: int = Field(ge=0)
    function_bodies: list[str]

    @property
    def purity_ratio(self) -> float:
        """순수 로직 비율. total_lines == 0 이면 0.0 반환."""
        if self.total_lines == 0:
            return 0.0
        return self.pure_logic_lines / self.total_lines

    @property
    def noise_lines(self) -> int:
        """제거된 노이즈 라인 합계 (imports + comments + config + generated)."""
        return (
            self.removed_imports
            + self.removed_comments
            + self.removed_config
            + self.removed_generated
        )
