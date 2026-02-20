---
title: "GitHub REST API"
type: note
layer: infrastructure
component: github-client
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[github-client/MOC]]"
linear: JIT-93
tags: [github, rest, pygithub, repos, languages]
---

# GitHub REST API

> `infrastructure/github/rest_client.py` 구현 설계.
> `PyGithub>=2.5.0` 라이브러리로 GitHub REST API v3를 래핑한다.
> GraphQL로 대체할 수 없는 상세 데이터(언어 바이트 분포, 커밋 상세, 파일 트리)를 수집한다.

## GraphQL과의 역할 분담

| 데이터 | GraphQL | REST |
|--------|---------|------|
| databaseId (Node ID) | O | X |
| 레포 목록 + contributions | O | X (비효율) |
| 언어 바이트 분포 | 이름만 | **바이트 수 포함** |
| 커밋 상세 (diff, stats) | X | O |
| 파일 트리 (recursive) | X | O |
| Topics | X | O |
| Releases | X | O |

REST는 GraphQL이 제공하지 못하는 **정량적 상세 데이터** 수집에 특화한다.

## 구현

```python
# infrastructure/github/rest_client.py
from github import Github, GithubException
from pydantic import BaseModel

class LanguageBreakdown(BaseModel):
    """레포 언어 분포 (바이트 기준)"""
    repo_name: str
    languages: dict[str, int]   # {"Python": 45231, "JavaScript": 12045}
    total_bytes: int
    primary_language: str       # 가장 많은 비율의 언어
    language_percentages: dict[str, float]  # {"Python": 78.5, "JavaScript": 21.5}

class CommitMetadata(BaseModel):
    sha: str
    message: str
    author_name: str
    author_email: str
    authored_at: str    # ISO 8601
    additions: int
    deletions: int
    total_changes: int
    files_changed: list[str]

class RepoDetail(BaseModel):
    """REST API로만 얻을 수 있는 레포 상세 정보"""
    name_with_owner: str
    topics: list[str]
    default_branch: str
    clone_url: str
    open_issues_count: int
    forks_count: int
    watchers_count: int


class GitHubRestClient:
    """PyGithub 기반 GitHub REST API v3 클라이언트"""

    def __init__(self, token: str):
        self.github = Github(login_or_token=token, per_page=100)

    def get_repo_languages(self, repo_full_name: str) -> LanguageBreakdown:
        """레포 언어 분포 (바이트 기준) 조회.

        Funnel Stage 1에서 JD 언어 매칭 시 단순 이름뿐 아니라
        비율 기반 필터링에 사용한다.

        Args:
            repo_full_name: "owner/repo" 형식

        Returns:
            LanguageBreakdown: 언어별 바이트 수 및 비율
        """
        repo = self.github.get_repo(repo_full_name)
        languages = repo.get_languages()  # dict[str, int]

        if not languages:
            return LanguageBreakdown(
                repo_name=repo_full_name,
                languages={},
                total_bytes=0,
                primary_language="",
                language_percentages={},
            )

        total_bytes = sum(languages.values())
        primary = max(languages, key=languages.get)
        percentages = {
            lang: round(bytes_ / total_bytes * 100, 1)
            for lang, bytes_ in languages.items()
        }

        return LanguageBreakdown(
            repo_name=repo_full_name,
            languages=languages,
            total_bytes=total_bytes,
            primary_language=primary,
            language_percentages=percentages,
        )

    def get_recent_commits(
        self,
        repo_full_name: str,
        author_login: str,
        max_commits: int = 100,
    ) -> list[CommitMetadata]:
        """지원자의 최근 커밋 메타데이터 수집.

        VibectorWorker(W3) 입력 — 커밋 타임스탬프와 코드 변경량으로
        WPM(Words Per Minute) 계산 시 활용.

        Args:
            repo_full_name: "owner/repo"
            author_login: GitHub 로그인 이름 (blame 필터와 동일 기준)
            max_commits: 수집 상한

        Returns:
            list[CommitMetadata]: 커밋 상세 (additions, deletions, files)
        """
        repo = self.github.get_repo(repo_full_name)
        commits = repo.get_commits(author=author_login)

        results = []
        for commit in commits[:max_commits]:
            try:
                c = commit.commit
                stats = commit.stats
                files = [f.filename for f in commit.files]
                results.append(CommitMetadata(
                    sha=commit.sha,
                    message=c.message.split("\n")[0],
                    author_name=c.author.name,
                    author_email=c.author.email,
                    authored_at=c.author.date.isoformat(),
                    additions=stats.additions,
                    deletions=stats.deletions,
                    total_changes=stats.total,
                    files_changed=files,
                ))
            except GithubException:
                # 개별 커밋 조회 실패 시 건너뜀 (삭제된 커밋 등)
                continue

        return results

    def get_repo_detail(self, repo_full_name: str) -> RepoDetail:
        """GraphQL에서 누락된 레포 상세 정보 (topics, default_branch 등)"""
        repo = self.github.get_repo(repo_full_name)
        return RepoDetail(
            name_with_owner=repo.full_name,
            topics=repo.get_topics(),
            default_branch=repo.default_branch,
            clone_url=repo.clone_url,
            open_issues_count=repo.open_issues_count,
            forks_count=repo.forks_count,
            watchers_count=repo.watchers_count,
        )

    def get_file_tree(
        self,
        repo_full_name: str,
        branch: str = "main",
        max_files: int = 500,
    ) -> list[str]:
        """레포 파일 트리 (recursive) 조회.

        Sparse checkout 대상 디렉토리 선정 및
        Tree-sitter 분석 대상 파일 목록 구성에 활용.

        Returns:
            list[str]: 파일 경로 목록 (레포 루트 기준)
        """
        repo = self.github.get_repo(repo_full_name)
        try:
            tree = repo.get_git_tree(branch, recursive=True)
            return [
                item.path for item in tree.tree
                if item.type == "blob"
            ][:max_files]
        except GithubException:
            return []
```

## Rate Limit 관리

PyGithub는 기본적으로 Rate Limit 도달 시 자동 대기한다 (`retry_after`). 추가 설정:

```python
from github import Github
from github import RateLimitExceededException
import time

class RateLimitedRestClient(GitHubRestClient):
    def __init__(self, token: str):
        super().__init__(token)

    def _safe_call(self, func, *args, **kwargs):
        """Rate Limit 초과 시 reset time까지 대기 후 재시도"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except RateLimitExceededException:
                if attempt == max_retries - 1:
                    raise
                reset_time = self.github.get_rate_limit().core.reset.timestamp()
                wait = max(0, reset_time - time.time()) + 5
                time.sleep(wait)
```

## REST vs GraphQL 선택 기준

```
필요 데이터:
├── databaseId, contributions, 레포 목록     → graphql_client.py
├── 언어 바이트 분포                           → rest_client.get_repo_languages()
├── 커밋 타임스탬프 + 변경량                   → rest_client.get_recent_commits()
├── 파일 트리 (sparse checkout 결정용)        → rest_client.get_file_tree()
└── 레포 topics (Funnel Stage 2 보조 신호)   → rest_client.get_repo_detail()
```

## CollectorWorker(W1) 호출 패턴

```python
# application/nodes/collector_worker.py (발췌)
async def collector_worker(state: ForensicState) -> dict:
    # 1. GraphQL: 레포 목록 + contributions (단일 쿼리)
    repos = await graphql_client.get_user_repos_graphql(
        state["candidate_username"], max_repos=20
    )

    # 2. REST: 언어 분포 보완 (Funnel Stage 1 정밀화)
    enriched_repos = []
    for repo in repos:
        lang_breakdown = rest_client.get_repo_languages(repo.name_with_owner)
        enriched_repos.append({**repo.model_dump(), "lang_breakdown": lang_breakdown})

    # 3. GraphQL: Node ID 조회 (Identity Resolution 기준)
    node_id = await graphql_client.get_user_node_id(state["candidate_username"])

    return {
        "collected_repos_ref": await repo_store.save(enriched_repos, state["job_id"]),
        "github_node_id": node_id,
    }
```

## 관련 문서

- [[graphql-api]] — Node ID, 레포 목록, contributions
- [[github-client/MOC]] — 전체 클라이언트 구성
- [[infrastructure/git-adapter/clone-strategy]] — clone_url 소비
