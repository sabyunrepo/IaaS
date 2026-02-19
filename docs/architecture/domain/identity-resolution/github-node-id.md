---
title: GitHub Node ID 기반 추적
type: component
parent: "[[domain/identity-resolution/MOC]]"
affects:
  - "[[domain/identity-resolution/dynamic-mailmap]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# GitHub Node ID 기반 추적

Identity Resolution Step 1. 이메일이 바뀌어도 변하지 않는 GitHub 고유 ID(`databaseId`)를 GraphQL로 조회하여 유저를 특정한다.

## databaseId의 불변성

GitHub에서 사용자가 이메일, 닉네임, 프로필 정보를 변경해도 `databaseId`는 변하지 않는다.
이를 기반으로 커밋 저자(이름/이메일)가 여러 형태로 나타나더라도 동일인임을 보장할 수 있다.

- `login` (username): 변경 가능
- `email`: 변경 가능, 여러 개 사용 가능
- `databaseId`: 계정 생성 시 부여, **불변**

## GraphQL 쿼리 코드

```python
# infrastructure/github/graphql_client.py
async def get_user_node_id(username: str) -> str:
    """GitHub 고유 ID 조회 -- 이메일 변경에도 불변"""
    query = """
    query($login: String!) {
        user(login: $login) {
            databaseId
            email
            name
            contributionsCollection {
                commitContributionsByRepository {
                    repository { nameWithOwner }
                    contributions { totalCount }
                }
            }
        }
    }
    """
    result = await gql_client.execute(query, {"login": username})
    return str(result["user"]["databaseId"])
```

## 수집 데이터

| 필드 | 설명 | 용도 |
|------|------|------|
| `databaseId` | GitHub 불변 고유 ID | IdentityCluster의 기본키 |
| `email` | GitHub 프로필 공개 이메일 | Step 2 mailmap 교차 매칭 기준 |
| `name` | GitHub 프로필 표시 이름 | Step 2 Levenshtein 비교 기준 |
| `commitContributionsByRepository` | 레포별 커밋 수 | Funnel Stage 1 기여도 필터 |

## 다음 단계

Step 1에서 수집한 `github_node_id`, `github_profile.email`, `github_profile.name`은 Step 2([[domain/identity-resolution/dynamic-mailmap]])의 `build_dynamic_mailmap` 함수로 전달된다.
