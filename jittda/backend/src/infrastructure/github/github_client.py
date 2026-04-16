"""
GitHubClient — GitHub REST v3 + GraphQL API 클라이언트.

GitHubProfileFetcher 포트를 구현한다.
- REST v3: 프로필 기본 정보 조회
- GraphQL: node ID(databaseId) 및 레포 목록 조회
- Rate limit 429 → exponential backoff (최대 3회 재시도)
"""
import asyncio
import logging
from typing import Any

import httpx

from domain.identity.models import GitHubProfile
from infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError

logger = logging.getLogger(__name__)

_GITHUB_REST_BASE = "https://api.github.com"
_GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

_REPOS_QUERY = """
query GetUserRepos($login: String!, $first: Int!) {
  user(login: $login) {
    repositories(first: $first, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        name
        url
        description
        isPrivate
        stargazerCount
        forkCount
        defaultBranchRef {
          name
        }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          nodes {
            name
          }
        }
      }
    }
  }
}
"""

_NODE_ID_QUERY = """
query GetUserNodeId($login: String!) {
  user(login: $login) {
    databaseId
  }
}
"""

_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0  # seconds


class GitHubClient:
    """GitHub REST v3 + GraphQL API를 통해 프로필/레포 정보를 가져오는 클라이언트.

    GitHubProfileFetcher Protocol을 구현한다.

    Args:
        token: GitHub personal access token (classic 또는 fine-grained).
    """

    def __init__(self, token: str, *, circuit_breaker: CircuitBreaker | None = None) -> None:
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._cb = circuit_breaker

    async def fetch_profile(self, username: str) -> GitHubProfile:
        """REST API v3로 GitHub 사용자 프로필을 가져온다.

        Args:
            username: GitHub 사용자명 (login).

        Returns:
            GitHubProfile 도메인 모델.

        Raises:
            ValueError: 존재하지 않는 사용자 요청 시.
            RuntimeError: API 통신 오류 시.
            CircuitOpenError: Circuit breaker가 Open 상태일 때.
        """
        if self._cb:
            return await self._cb.call(self._fetch_profile_impl, username)
        return await self._fetch_profile_impl(username)

    async def _fetch_profile_impl(self, username: str) -> GitHubProfile:
        data = await self._rest_get(f"/users/{username}")
        database_id = await self._get_node_id(username)
        return GitHubProfile(
            name=data.get("name") or "",
            email=data.get("email") or "",
            login=data["login"],
            database_id=database_id,
        )

    async def _get_node_id(self, username: str) -> str:
        """GraphQL로 사용자의 databaseId(global integer ID)를 조회한다.

        _fetch_profile_impl() 내부에서만 호출되므로 private.
        Circuit breaker는 fetch_profile() 레벨에서 적용된다.

        Args:
            username: GitHub 사용자명 (login).

        Returns:
            databaseId 문자열.

        Raises:
            ValueError: 존재하지 않는 사용자 요청 시.
            RuntimeError: GraphQL 오류 또는 통신 오류 시.
        """
        result = await self._graphql(
            _NODE_ID_QUERY,
            variables={"login": username},
        )
        user = result.get("data", {}).get("user")
        if user is None:
            raise ValueError(f"GitHub user not found: {username!r}")
        return str(user["databaseId"])

    async def get_user_repos(self, username: str, *, first: int = 100) -> list[dict]:
        """GraphQL로 사용자의 공개/비공개 레포 목록을 가져온다.

        반환 딕셔너리 스키마:
            - name (str)
            - url (str)
            - description (str | None)
            - languages (list[str])
            - stargazerCount (int)
            - forkCount (int)
            - isPrivate (bool)
            - defaultBranchRef (str | None)

        Args:
            username: GitHub 사용자명 (login).
            first: 가져올 최대 레포 수 (기본 100).

        Returns:
            레포 정보 딕셔너리 목록.

        Raises:
            ValueError: 존재하지 않는 사용자 요청 시.
            RuntimeError: GraphQL 오류 또는 통신 오류 시.
            CircuitOpenError: Circuit breaker가 Open 상태일 때.
        """
        if self._cb:
            return await self._cb.call(self._get_user_repos_impl, username, first=first)
        return await self._get_user_repos_impl(username, first=first)

    async def _get_user_repos_impl(self, username: str, *, first: int = 100) -> list[dict]:
        result = await self._graphql(
            _REPOS_QUERY,
            variables={"login": username, "first": first},
        )
        user = result.get("data", {}).get("user")
        if user is None:
            raise ValueError(f"GitHub user not found: {username!r}")

        nodes = user.get("repositories", {}).get("nodes", [])
        return [_normalize_repo_node(node) for node in nodes]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _rest_get(self, path: str) -> dict[str, Any]:
        """GET /path를 실행하고 JSON 응답을 반환한다.

        Raises:
            ValueError: 404 응답(사용자 없음) 시.
            RuntimeError: 기타 HTTP 오류 시.
        """
        url = f"{_GITHUB_REST_BASE}{path}"
        for attempt in range(_MAX_RETRIES):
            async with httpx.AsyncClient(headers=self._headers, timeout=30.0) as client:
                response = await client.get(url)

            if response.status_code == 429:
                wait = _backoff_seconds(attempt)
                logger.warning(
                    "GitHub REST rate limit hit (attempt %d/%d). Retrying in %.1fs.",
                    attempt + 1,
                    _MAX_RETRIES,
                    wait,
                )
                await asyncio.sleep(wait)
                continue

            if response.status_code == 404:
                raise ValueError(f"GitHub user not found: {path!r}")

            if response.status_code >= 400:
                raise RuntimeError(
                    f"GitHub REST API error {response.status_code}: {response.text[:200]}"
                )

            return response.json()

        raise RuntimeError(
            f"GitHub REST API rate limit exceeded after {_MAX_RETRIES} retries: {url}"
        )

    async def _graphql(
        self,
        query: str,
        *,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """GraphQL 쿼리를 실행하고 응답을 반환한다.

        Raises:
            ValueError: 사용자 없음 오류(errors[0].type == NOT_FOUND) 시.
            RuntimeError: 기타 GraphQL/HTTP 오류 시.
        """
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        for attempt in range(_MAX_RETRIES):
            async with httpx.AsyncClient(headers=self._headers, timeout=30.0) as client:
                response = await client.post(_GITHUB_GRAPHQL_URL, json=payload)

            if response.status_code == 429:
                wait = _backoff_seconds(attempt)
                logger.warning(
                    "GitHub GraphQL rate limit hit (attempt %d/%d). Retrying in %.1fs.",
                    attempt + 1,
                    _MAX_RETRIES,
                    wait,
                )
                await asyncio.sleep(wait)
                continue

            if response.status_code >= 400:
                raise RuntimeError(
                    f"GitHub GraphQL HTTP error {response.status_code}: {response.text[:200]}"
                )

            body = response.json()

            # GraphQL application-level errors
            errors = body.get("errors")
            if errors:
                first_error = errors[0]
                error_type = first_error.get("type", "")
                message = first_error.get("message", "GraphQL error")
                if error_type == "NOT_FOUND":
                    # username을 variables에서 추출
                    login = (variables or {}).get("login", "<unknown>")
                    raise ValueError(f"GitHub user not found: {login!r}")
                raise RuntimeError(f"GitHub GraphQL error [{error_type}]: {message}")

            return body

        raise RuntimeError(
            f"GitHub GraphQL rate limit exceeded after {_MAX_RETRIES} retries."
        )


# ------------------------------------------------------------------
# Module-level pure helpers
# ------------------------------------------------------------------


def _backoff_seconds(attempt: int) -> float:
    """Exponential backoff: 1s → 2s → 4s."""
    return _BACKOFF_BASE * (2**attempt)


def _normalize_repo_node(node: dict[str, Any]) -> dict[str, Any]:
    """GraphQL 레포 노드를 평탄한 딕셔너리로 변환한다."""
    language_nodes = node.get("languages", {}).get("nodes", [])
    languages = [lang["name"] for lang in language_nodes if lang.get("name")]

    default_branch_ref = node.get("defaultBranchRef")
    default_branch = default_branch_ref["name"] if default_branch_ref else None

    return {
        "name": node.get("name", ""),
        "url": node.get("url", ""),
        "description": node.get("description"),
        "languages": languages,
        "stargazerCount": node.get("stargazerCount", 0),
        "forkCount": node.get("forkCount", 0),
        "isPrivate": node.get("isPrivate", False),
        "defaultBranchRef": default_branch,
    }
