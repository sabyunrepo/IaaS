---
title: "GitHub Client"
type: moc
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[infrastructure/MOC]]"
linear: JIT-93
depends-on:
  - "[[domain/identity-resolution/github-node-id]]"
---

# GitHub Client

> `jittda/backend/src/infrastructure/github/` 디렉토리에 위치하는 어댑터 묶음.
> GitHub API v4 (GraphQL)와 v3 (REST/PyGithub) 를 분리하여 캡슐화한다.
> CollectorWorker(W1) 및 identity_resolver_node에서 호출된다.

## 구성 모듈

| 모듈 | 파일 | 역할 | API |
|------|------|------|-----|
| GraphQL Client | `graphql_client.py` | `databaseId`, 레포 목록, contributions 수집 | GitHub GraphQL v4 |
| REST Client | `rest_client.py` | 레포 상세, 언어 분포, 커밋 메타데이터 수집 | PyGithub REST v3 |

## 설계 원칙

- **GraphQL 우선**: 복수 레포 목록 수집, Node ID 조회, contributions 수집은 GraphQL로.
- **REST 보완**: 언어 분포(`/languages`), 커밋 세부 정보, 파일 트리 등 GraphQL로 불가한 항목은 REST로.
- **Rate Limit 자체 관리**: `asyncio.Semaphore` + exponential backoff 내장.
- **Pure Output**: 반환 타입은 `RepoMetadata`, `GitHubProfile`, `str`(node_id) 등 domain/interface 모델.

## Identity Resolution 파이프라인 위치

```
github_username (입력)
        │
        ▼ graphql_client.get_user_node_id()
github_node_id (str)  →  IdentityCluster 구성
        │
        ▼ graphql_client.get_user_repos_graphql()
repos[] (RepoMetadata)  →  Funnel Stage 1/2 입력
        │
        ▼ rest_client.get_repo_languages()
languages{}  →  Stage 1 Hard Filter 언어 매칭
```

## 문서 목록

- [[graphql-api]] — GraphQL 쿼리 (databaseId, contributions, repos)
- [[rest-api]] — PyGithub REST API (repos, languages, commits)

## 관련 도메인 문서

- [[domain/identity-resolution/github-node-id]] — Node ID 기반 동일인 추적 원칙
- [[infrastructure/git-adapter/MOC]] — clone_manager가 이 client의 clone_url을 소비
