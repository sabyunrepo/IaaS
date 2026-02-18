---
title: 동적 .mailmap 생성 (MailmapBuilder)
type: component
parent: "[[domain/identity-resolution/MOC]]"
depends-on:
  - "[[domain/identity-resolution/github-node-id]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# 동적 .mailmap 생성

Identity Resolution Step 2. 레포지토리 내 커밋 히스토리에서 이름/이메일 유사도를 분석하여, 동일인으로 추정되는 커밋을 하나로 묶는 클러스터링을 수행한다.

## 문제 배경

Git 커밋에는 여러 이메일/이름이 혼재할 수 있다.

- 개인 이메일 (`user@gmail.com`)
- 회사 이메일 (`user@company.com`)
- GitHub noreply 이메일 (`12345+username@users.noreply.github.com`)
- 학교 이메일 (`user@university.edu`)
- 닉네임 변경 전 이름

`.mailmap` 파일은 이 별칭들을 정규 이름/이메일로 매핑하는 Git 표준 기능이다. `MailmapBuilder`는 이를 **동적으로** 생성한다.

## MailmapBuilder 코드

```python
# domain/identity/mailmap_builder.py
def build_dynamic_mailmap(
    git_authors: list[GitAuthor],
    github_profile: GitHubProfile,
    github_node_id: str,
    threshold: float = 0.75,
) -> list[MailmapEntry]:
    """동적 .mailmap 생성 -- 동일인 이메일 클러스터링"""
    entries = []

    # 1. noreply email 패턴 매칭 (확정적)
    # 예: 12345+username@users.noreply.github.com
    for author in git_authors:
        if "noreply.github.com" in author.email:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="high",
            ))

    # 2. GitHub profile name/email 교차 매칭 (확정적)
    for author in git_authors:
        if author.email == github_profile.email:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="high",
            ))

    # 3. 이름 Levenshtein distance < threshold -> 클러스터링 (휴리스틱)
    for author in git_authors:
        similarity = 1 - (levenshtein(author.name, github_profile.name)
                         / max(len(author.name), len(github_profile.name)))
        if similarity >= threshold:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="medium",
            ))

    # 4. 동일 커스텀 도메인 이메일 -> 후보 추가 (약한 신호)
    profile_domain = github_profile.email.split("@")[-1]
    for author in git_authors:
        if author.email.split("@")[-1] == profile_domain:
            entries.append(MailmapEntry(
                canonical=github_profile.name,
                canonical_email=github_profile.email,
                alias_name=author.name,
                alias_email=author.email,
                confidence="low",
            ))

    return deduplicate(entries)
```

## 4가지 매칭 규칙

| 순서 | 규칙 | 신호 강도 | Confidence |
|------|------|----------|-----------|
| Rule 1 | `noreply.github.com` 포함 이메일 패턴 매칭 | 확정적 | `high` |
| Rule 2 | GitHub 프로필 `email`과 정확히 일치하는 커밋 이메일 | 확정적 | `high` |
| Rule 3 | 이름 Levenshtein similarity >= `threshold` (기본값: 0.75) | 휴리스틱 | `medium` |
| Rule 4 | 커밋 이메일 도메인 == GitHub 프로필 이메일 도메인 | 약한 신호 | `low` |

## Confidence 레벨

| 레벨 | 값 | 의미 |
|------|-----|------|
| CONFIRMED | `"high"` (Rule 1, 2) | 수학적으로 동일인 확정 가능 |
| HIGH | `"high"` | GitHub API에서 직접 확인 |
| MEDIUM | `"medium"` | 이름 유사도 기반 추정, 오분류 가능성 낮음 |
| LOW | `"low"` | 도메인 기반 약한 신호, 같은 회사 다른 사람일 수 있음 |

## 출력

`list[MailmapEntry]` → [[domain/identity-resolution/models]] 참조

중복 제거(`deduplicate`)된 엔트리 목록이 `IdentityCluster.aliases`에 저장된다. Step 3([[domain/identity-resolution/blame-forensics]])에서 blame 라인을 필터링할 때 이 클러스터를 사용한다.
