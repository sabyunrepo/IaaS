---
title: Identity Resolution Domain Models
type: component
parent: "[[domain/identity-resolution/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# Identity Resolution Domain Models

`domain/identity/models.py`에 정의된 Pydantic v2 모델들이다. 모든 모델은 `pydantic.BaseModel`을 상속하며, 필요 시 `ConfigDict(strict=True)`를 적용한다.

## 소스 파일

```
domain/identity/models.py
```

## 모델 정의

```python
# domain/identity/models.py
from pydantic import BaseModel

class MailmapEntry(BaseModel):
    canonical: str             # 정규 이름
    canonical_email: str       # 정규 이메일
    alias_name: str            # 별칭 이름
    alias_email: str           # 별칭 이메일
    confidence: str            # "high" | "medium" | "low"

class IdentityCluster(BaseModel):
    github_node_id: str
    canonical_name: str
    canonical_email: str
    aliases: list[MailmapEntry]
    total_commits: int
    verified_commits: int

class BlameLineAttribution(BaseModel):
    file_path: str
    line_number: int
    content: str
    author_name: str
    author_email: str
    commit_sha: str
    is_move: bool              # -M 감지
    is_copy: bool              # -C 감지
    is_whitespace_only: bool   # -w 감지

class PureContribution(BaseModel):
    file_path: str
    language: str
    total_lines: int           # 전체 blame 라인
    pure_logic_lines: int      # 노이즈 제거 후 순수 로직
    removed_imports: int
    removed_comments: int
    removed_config: int
    removed_generated: int
    function_bodies: list[str] # 보존된 함수/클래스 본문
```

## 모델 관계도

```
IdentityCluster
  ├── github_node_id: str          ← Step 1 GitHub Node ID에서 수집
  ├── canonical_name: str
  ├── canonical_email: str
  ├── aliases: list[MailmapEntry]  ← Step 2 MailmapBuilder 출력
  ├── total_commits: int
  └── verified_commits: int

MailmapEntry
  ├── canonical: str
  ├── canonical_email: str
  ├── alias_name: str
  ├── alias_email: str
  └── confidence: "high" | "medium" | "low"

BlameLineAttribution             ← Step 3 Level 1 git blame 출력
  ├── file_path, line_number, content
  ├── author_name, author_email, commit_sha
  ├── is_move: bool              (-M 옵션으로 감지)
  ├── is_copy: bool              (-C -C 옵션으로 감지)
  └── is_whitespace_only: bool   (-w 옵션으로 감지)

PureContribution                 ← Step 3 Level 2 AST Pruning 출력
  ├── file_path, language
  ├── total_lines: int
  ├── pure_logic_lines: int      (노이즈 제거 후 순수 로직)
  ├── removed_imports: int
  ├── removed_comments: int
  ├── removed_config: int
  ├── removed_generated: int
  └── function_bodies: list[str]  (보존된 함수/클래스 본문)
```

## confidence 필드 허용값

`MailmapEntry.confidence`는 [[domain/identity-resolution/dynamic-mailmap]]에서 4가지 매칭 규칙에 따라 결정된다.

| 값 | 매핑 규칙 |
|----|----------|
| `"high"` | noreply 패턴 매칭 또는 GitHub 프로필 email 정확 일치 |
| `"medium"` | 이름 Levenshtein similarity >= 0.75 |
| `"low"` | 동일 커스텀 도메인 이메일 |

## BlameLineAttribution 노이즈 플래그

`is_move`, `is_copy`, `is_whitespace_only`가 `True`인 라인은 `PureContribution` 집계에서 제외된다. 이 라인들은 실제 로직 작성이 아닌 리팩토링/정리 작업으로 간주한다.

## 연관 Linear 티켓

- JIT-86: Identity Resolution 모델 정의 및 구현
