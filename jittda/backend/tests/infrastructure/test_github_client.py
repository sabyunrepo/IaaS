"""
GitHubClient 테스트

- GraphQL 응답 파싱 (mock)
- REST 프로필 응답 파싱 (mock)
- Rate limit 재시도 (exponential backoff)
- 존재하지 않는 유저 처리 (ValueError)
"""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from infrastructure.github.github_client import (
    GitHubClient,
    _backoff_seconds,
    _normalize_repo_node,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> GitHubClient:
    return GitHubClient(token="test-token")


def _make_response(
    status_code: int,
    json_body: dict | None = None,
    text: str = "",
) -> MagicMock:
    """httpx.Response 모의 객체를 생성한다."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_body or {}
    response.text = text
    return response


# ---------------------------------------------------------------------------
# Helper: _backoff_seconds
# ---------------------------------------------------------------------------


class TestBackoffSeconds:
    def test_attempt_0_returns_1(self):
        assert _backoff_seconds(0) == 1.0

    def test_attempt_1_returns_2(self):
        assert _backoff_seconds(1) == 2.0

    def test_attempt_2_returns_4(self):
        assert _backoff_seconds(2) == 4.0


# ---------------------------------------------------------------------------
# Helper: _normalize_repo_node
# ---------------------------------------------------------------------------


class TestNormalizeRepoNode:
    def test_full_node(self):
        node = {
            "name": "my-repo",
            "url": "https://github.com/user/my-repo",
            "description": "A test repo",
            "isPrivate": False,
            "stargazerCount": 42,
            "forkCount": 3,
            "defaultBranchRef": {"name": "main"},
            "languages": {"nodes": [{"name": "Python"}, {"name": "TypeScript"}]},
        }
        result = _normalize_repo_node(node)
        assert result["name"] == "my-repo"
        assert result["url"] == "https://github.com/user/my-repo"
        assert result["description"] == "A test repo"
        assert result["isPrivate"] is False
        assert result["stargazerCount"] == 42
        assert result["forkCount"] == 3
        assert result["defaultBranchRef"] == "main"
        assert result["languages"] == ["Python", "TypeScript"]

    def test_node_without_default_branch(self):
        node = {
            "name": "empty",
            "url": "",
            "description": None,
            "isPrivate": True,
            "stargazerCount": 0,
            "forkCount": 0,
            "defaultBranchRef": None,
            "languages": {"nodes": []},
        }
        result = _normalize_repo_node(node)
        assert result["defaultBranchRef"] is None
        assert result["languages"] == []

    def test_node_missing_keys_uses_defaults(self):
        result = _normalize_repo_node({})
        assert result["name"] == ""
        assert result["stargazerCount"] == 0
        assert result["forkCount"] == 0
        assert result["isPrivate"] is False
        assert result["languages"] == []
        assert result["defaultBranchRef"] is None


# ---------------------------------------------------------------------------
# fetch_profile — REST 응답 파싱
# ---------------------------------------------------------------------------


class TestFetchProfile:
    @pytest.mark.asyncio
    async def test_parses_rest_response_correctly(self, client: GitHubClient):
        rest_body = {
            "login": "octocat",
            "name": "The Octocat",
            "email": "octocat@github.com",
        }
        graphql_body = {
            "data": {"user": {"databaseId": 583231}},
        }
        rest_response = _make_response(200, rest_body)
        graphql_response = _make_response(200, graphql_body)

        mock_client_rest = AsyncMock()
        mock_client_rest.get.return_value = rest_response
        mock_client_graphql = AsyncMock()
        mock_client_graphql.post.return_value = graphql_response

        call_count = 0

        async def _async_client_factory(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_client_rest
            return mock_client_graphql

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = _async_client_factory
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            # Patch each call individually via _rest_get and get_node_id
            with (
                patch.object(client, "_rest_get", AsyncMock(return_value=rest_body)),
                patch.object(client, "get_node_id", AsyncMock(return_value="583231")),
            ):
                profile = await client.fetch_profile("octocat")

        assert profile.login == "octocat"
        assert profile.name == "The Octocat"
        assert profile.email == "octocat@github.com"
        assert profile.database_id == "583231"

    @pytest.mark.asyncio
    async def test_name_and_email_default_to_empty_string_when_null(
        self, client: GitHubClient
    ):
        rest_body = {"login": "ghost", "name": None, "email": None}
        with (
            patch.object(client, "_rest_get", AsyncMock(return_value=rest_body)),
            patch.object(client, "get_node_id", AsyncMock(return_value="10137")),
        ):
            profile = await client.fetch_profile("ghost")

        assert profile.name == ""
        assert profile.email == ""
        assert profile.login == "ghost"

    @pytest.mark.asyncio
    async def test_raises_value_error_for_missing_user(self, client: GitHubClient):
        with patch.object(
            client,
            "_rest_get",
            AsyncMock(side_effect=ValueError("GitHub user not found: '/users/no-such-user'")),
        ):
            with pytest.raises(ValueError, match="GitHub user not found"):
                await client.fetch_profile("no-such-user")


# ---------------------------------------------------------------------------
# get_node_id — GraphQL 파싱
# ---------------------------------------------------------------------------


class TestGetNodeId:
    @pytest.mark.asyncio
    async def test_returns_database_id_as_string(self, client: GitHubClient):
        graphql_body = {"data": {"user": {"databaseId": 583231}}}
        response = _make_response(200, graphql_body)

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            node_id = await client.get_node_id("octocat")

        assert node_id == "583231"

    @pytest.mark.asyncio
    async def test_raises_value_error_when_user_is_none(self, client: GitHubClient):
        graphql_body = {
            "data": {"user": None},
            "errors": [{"type": "NOT_FOUND", "message": "Could not resolve to a User"}],
        }
        response = _make_response(200, graphql_body)

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(ValueError, match="GitHub user not found"):
                await client.get_node_id("no-such-user")

    @pytest.mark.asyncio
    async def test_raises_runtime_error_on_generic_graphql_error(
        self, client: GitHubClient
    ):
        graphql_body = {
            "errors": [{"type": "FORBIDDEN", "message": "Resource not accessible by token"}]
        }
        response = _make_response(200, graphql_body)

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(RuntimeError, match="FORBIDDEN"):
                await client.get_node_id("octocat")


# ---------------------------------------------------------------------------
# get_user_repos — GraphQL 응답 파싱
# ---------------------------------------------------------------------------


class TestGetUserRepos:
    @pytest.mark.asyncio
    async def test_parses_repo_list(self, client: GitHubClient):
        graphql_body = {
            "data": {
                "user": {
                    "repositories": {
                        "nodes": [
                            {
                                "name": "repo-a",
                                "url": "https://github.com/user/repo-a",
                                "description": "First repo",
                                "isPrivate": False,
                                "stargazerCount": 10,
                                "forkCount": 2,
                                "defaultBranchRef": {"name": "main"},
                                "languages": {
                                    "nodes": [{"name": "Python"}]
                                },
                            },
                            {
                                "name": "repo-b",
                                "url": "https://github.com/user/repo-b",
                                "description": None,
                                "isPrivate": True,
                                "stargazerCount": 0,
                                "forkCount": 0,
                                "defaultBranchRef": None,
                                "languages": {"nodes": []},
                            },
                        ]
                    }
                }
            }
        }
        response = _make_response(200, graphql_body)

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            repos = await client.get_user_repos("user")

        assert len(repos) == 2
        assert repos[0]["name"] == "repo-a"
        assert repos[0]["languages"] == ["Python"]
        assert repos[0]["defaultBranchRef"] == "main"
        assert repos[1]["name"] == "repo-b"
        assert repos[1]["isPrivate"] is True
        assert repos[1]["defaultBranchRef"] is None

    @pytest.mark.asyncio
    async def test_raises_value_error_for_missing_user(self, client: GitHubClient):
        graphql_body = {
            "data": {"user": None},
            "errors": [{"type": "NOT_FOUND", "message": "Could not resolve to a User"}],
        }
        response = _make_response(200, graphql_body)

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(ValueError, match="GitHub user not found"):
                await client.get_user_repos("no-such-user")


# ---------------------------------------------------------------------------
# Rate limit — 재시도 및 backoff
# ---------------------------------------------------------------------------


class TestRateLimit:
    @pytest.mark.asyncio
    async def test_rest_retries_on_429_then_succeeds(self, client: GitHubClient):
        rate_limit_response = _make_response(429)
        success_response = _make_response(200, {"login": "user", "name": "User", "email": ""})

        call_count = 0

        async def post_side_effect(*args, **kwargs):  # noqa: ARG001
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_limit_response
            return success_response

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = post_side_effect
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("infrastructure.github.github_client.asyncio.sleep", AsyncMock()) as mock_sleep:
                result = await client._rest_get("/users/user")

        mock_sleep.assert_called_once_with(1.0)
        assert result["login"] == "user"

    @pytest.mark.asyncio
    async def test_rest_raises_after_max_retries_on_429(self, client: GitHubClient):
        rate_limit_response = _make_response(429)

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = rate_limit_response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("infrastructure.github.github_client.asyncio.sleep", AsyncMock()):
                with pytest.raises(RuntimeError, match="rate limit exceeded"):
                    await client._rest_get("/users/user")

    @pytest.mark.asyncio
    async def test_graphql_retries_on_429_then_succeeds(self, client: GitHubClient):
        rate_limit_response = _make_response(429)
        success_body = {"data": {"user": {"databaseId": 1}}}
        success_response = _make_response(200, success_body)

        call_count = 0

        async def post_side_effect(*args, **kwargs):  # noqa: ARG001
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_limit_response
            return success_response

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = post_side_effect
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("infrastructure.github.github_client.asyncio.sleep", AsyncMock()) as mock_sleep:
                result = await client._graphql("query { viewer { login } }")

        mock_sleep.assert_called_once_with(1.0)
        assert result["data"]["user"]["databaseId"] == 1

    @pytest.mark.asyncio
    async def test_graphql_raises_after_max_retries_on_429(self, client: GitHubClient):
        rate_limit_response = _make_response(429)

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = rate_limit_response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with patch("infrastructure.github.github_client.asyncio.sleep", AsyncMock()):
                with pytest.raises(RuntimeError, match="rate limit exceeded"):
                    await client._graphql("query { viewer { login } }")


# ---------------------------------------------------------------------------
# HTTP 4xx/5xx 오류 처리
# ---------------------------------------------------------------------------


class TestHttpErrors:
    @pytest.mark.asyncio
    async def test_rest_raises_value_error_on_404(self, client: GitHubClient):
        response = _make_response(404, text="Not Found")

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(ValueError, match="GitHub user not found"):
                await client._rest_get("/users/nobody")

    @pytest.mark.asyncio
    async def test_rest_raises_runtime_error_on_500(self, client: GitHubClient):
        response = _make_response(500, text="Internal Server Error")

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(RuntimeError, match="500"):
                await client._rest_get("/users/user")

    @pytest.mark.asyncio
    async def test_graphql_raises_runtime_error_on_http_error(self, client: GitHubClient):
        response = _make_response(401, text="Unauthorized")

        with patch("infrastructure.github.github_client.httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = response
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(RuntimeError, match="401"):
                await client._graphql("query { viewer { login } }")
