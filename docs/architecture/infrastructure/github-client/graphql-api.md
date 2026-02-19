---
title: "GitHub GraphQL API"
type: note
layer: infrastructure
component: github-client
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[github-client/MOC]]"
linear: JIT-93
depends-on:
  - "[[domain/identity-resolution/github-node-id]]"
tags: [github, graphql, identity-resolution, collector]
---

# GitHub GraphQL API

> `infrastructure/github/graphql_client.py` 구현 설계.
> GitHub GraphQL v4 API를 사용하여 `databaseId`, 레포 목록, contributions를 수집한다.
> `gql[aiohttp]>=3.5.0` 라이브러리를 사용한다.

## 왜 GraphQL인가

| 항목 | REST | GraphQL |
|------|------|---------|
| 레포 목록 + 언어 + 최근 push | 3회 요청 | 1회 요청 |
| databaseId (Node ID) | X (별도 엔드포인트) | user.databaseId |
| contributions 수 | X (GraphQL only) | contributionsCollection |
| Rate Limit | 5000 req/hour | 5000 points/hour (복잡도 기반) |

복수 레포 수집과 Node ID 조회를 단일 쿼리로 처리할 수 있으므로 GraphQL이 적합하다.

## 구현

```python
# infrastructure/github/graphql_client.py
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from pydantic import BaseModel

class GitHubProfile(BaseModel):
    username: str
    database_id: int        # GitHub 고유 숫자 ID (불변)
    email: str
    name: str
    public_repos: int

class RepoMetadata(BaseModel):
    name: str
    name_with_owner: str    # "owner/repo"
    clone_url: str
    is_fork: bool
    is_private: bool
    size_kb: int
    primary_language: str | None
    languages: list[str]    # 사용 언어 전체 목록
    days_since_push: int
    stargazer_count: int
    user_contribution_count: int  # commitContributionsByRepository.totalCount


class GitHubGraphQLClient:
    """GitHub GraphQL v4 클라이언트"""

    API_URL = "https://api.github.com/graphql"

    def __init__(self, token: str):
        transport = AIOHTTPTransport(
            url=self.API_URL,
            headers={"Authorization": f"bearer {token}"},
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=False)

    async def get_user_node_id(self, username: str) -> str:
        """GitHub 고유 databaseId 조회 — 이메일/이름 변경에도 불변.

        Identity Resolution의 핵심. 동일인 추적의 기준값.
        관련 도메인 원칙: [[domain/identity-resolution/github-node-id]]
        """
        query = gql("""
        query GetUserNodeId($login: String!) {
            user(login: $login) {
                databaseId
                email
                name
            }
        }
        """)
        result = await self.client.execute_async(query, {"login": username})
        user = result["user"]
        return str(user["databaseId"])

    async def get_user_profile(self, username: str) -> GitHubProfile:
        """사용자 프로필 + databaseId 조회"""
        query = gql("""
        query GetUserProfile($login: String!) {
            user(login: $login) {
                databaseId
                email
                name
                login
                repositories { totalCount }
            }
        }
        """)
        result = await self.client.execute_async(query, {"login": username})
        u = result["user"]
        return GitHubProfile(
            username=u["login"],
            database_id=u["databaseId"],
            email=u["email"] or "",
            name=u["name"] or u["login"],
            public_repos=u["repositories"]["totalCount"],
        )

    async def get_user_repos_graphql(
        self,
        username: str,
        max_repos: int = 20,
    ) -> list[RepoMetadata]:
        """레포 목록 + 언어 + 기여도 수집 (단일 GraphQL 쿼리).

        Args:
            username: GitHub 로그인 이름
            max_repos: 수집 상한 (FunnelConfig.max_repos)

        Returns:
            list[RepoMetadata]: Funnel Stage 1/2 입력 데이터
        """
        query = gql("""
        query GetUserRepos($login: String!, $first: Int!) {
            user(login: $login) {
                repositories(
                    first: $first,
                    orderBy: { field: PUSHED_AT, direction: DESC },
                    ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]
                ) {
                    nodes {
                        name
                        nameWithOwner
                        url
                        isFork
                        isPrivate
                        diskUsage
                        stargazerCount
                        pushedAt
                        primaryLanguage { name }
                        languages(first: 10) {
                            nodes { name }
                        }
                    }
                }
                contributionsCollection {
                    commitContributionsByRepository {
                        repository { nameWithOwner }
                        contributions { totalCount }
                    }
                }
            }
        }
        """)
        result = await self.client.execute_async(
            query, {"login": username, "first": max_repos}
        )

        # contributions 맵 (nameWithOwner → count)
        contributions_map: dict[str, int] = {}
        for contrib in result["user"]["contributionsCollection"][
            "commitContributionsByRepository"
        ]:
            nwo = contrib["repository"]["nameWithOwner"]
            contributions_map[nwo] = contrib["contributions"]["totalCount"]

        repos = []
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        for node in result["user"]["repositories"]["nodes"]:
            pushed_at = datetime.fromisoformat(
                node["pushedAt"].replace("Z", "+00:00")
            )
            days_since = (now - pushed_at).days

            repos.append(RepoMetadata(
                name=node["name"],
                name_with_owner=node["nameWithOwner"],
                clone_url=node["url"],
                is_fork=node["isFork"],
                is_private=node["isPrivate"],
                size_kb=node.get("diskUsage", 0),
                primary_language=(
                    node["primaryLanguage"]["name"]
                    if node["primaryLanguage"] else None
                ),
                languages=[
                    lang["name"] for lang in node["languages"]["nodes"]
                ],
                days_since_push=days_since,
                stargazer_count=node["stargazerCount"],
                user_contribution_count=contributions_map.get(
                    node["nameWithOwner"], 0
                ),
            ))

        return repos
```

## Rate Limit 관리

```python
# infrastructure/github/graphql_client.py (추가)
import asyncio

class RateLimitedGraphQLClient(GitHubGraphQLClient):
    """Rate Limit 자동 관리 래퍼"""

    def __init__(self, token: str, max_concurrent: int = 3):
        super().__init__(token)
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._retry_delays = [1, 2, 4, 8]  # exponential backoff (초)

    async def execute_with_retry(self, query, variables: dict):
        async with self._semaphore:
            for i, delay in enumerate(self._retry_delays):
                try:
                    return await self.client.execute_async(query, variables)
                except Exception as e:
                    if "rate limit" in str(e).lower() and i < len(self._retry_delays) - 1:
                        await asyncio.sleep(delay)
                        continue
                    raise
```

## contributionsCollection 활용

`contributionsCollection.commitContributionsByRepository`는 **지원자가 실제로 커밋한 레포**와 **커밋 수**를 제공한다. 이 값은 Funnel Stage 1의 `org_contribution_threshold` 검증에 사용된다.

```python
# domain/matching/funnel_rules.py (발췌)
def stage1_hard_filter(repos, jd_languages, config):
    for repo in repos:
        # Org 레포: 기여도 임계치 확인
        if repo.is_org_repo:
            total_commits = repo.user_contribution_count
            # 전체 커밋 대비 비율은 REST API로 보완 (github_client/rest-api 참조)
            if total_commits < 10:  # 최소 절대값 기준
                continue
```

## 쿼리 비용 (GitHub Points)

| 쿼리 | 예상 Points |
|------|------------|
| `get_user_node_id` | ~1 |
| `get_user_profile` | ~1 |
| `get_user_repos_graphql` (20개) | ~5-10 |

GitHub GraphQL Rate Limit은 시간당 5000 points. 분석 1회당 약 10-15 points 소비.

## 관련 문서

- [[rest-api]] — 언어 분포, 커밋 세부 정보는 REST로 보완
- [[github-client/MOC]] — 전체 클라이언트 구성
- [[domain/identity-resolution/github-node-id]] — databaseId 활용 원칙
- [[infrastructure/git-adapter/blame-extraction]] — 수집한 clone_url을 CloneManager에 전달
