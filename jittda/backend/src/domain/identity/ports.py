"""
Identity Resolution 도메인 포트 (인터페이스)

Protocol 기반의 순수 인터페이스 — 구체 구현은 infrastructure 계층에서 담당.
도메인 계층은 이 Protocol만 의존하므로 infrastructure import 없음.
"""
from typing import Protocol

from domain.identity.models import GitAuthor, GitHubProfile


class GitAuthorReader(Protocol):
    """Git 저장소에서 저자 목록을 읽는 포트."""

    async def list_authors(self, repo_path: str) -> list[GitAuthor]:
        """주어진 로컬 저장소 경로에서 모든 커밋 저자를 반환한다."""
        ...


class GitHubProfileFetcher(Protocol):
    """GitHub API를 통해 프로필 정보를 가져오는 포트."""

    async def fetch_profile(self, username: str) -> GitHubProfile:
        """GitHub 사용자명으로 전체 프로필을 반환한다."""
        ...

    async def get_node_id(self, username: str) -> str:
        """GitHub 사용자명으로 GraphQL node ID(global ID)를 반환한다."""
        ...
