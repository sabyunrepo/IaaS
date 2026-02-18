---
title: Identity Resolution Overview
type: component
parent: "[[domain/identity-resolution/MOC]]"
depends-on:
  - "[[decisions/0002-clean-slate-not-migration]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# Identity Resolution Overview

## AS-IS vs TO-BE

| 항목 | AS-IS (v4.0) | TO-BE (v5.0) |
|------|-------------|-------------|
| 사용자 식별 | 단순 `git clone` + `git blame` | GitHub Node ID (`databaseId`) 기반 추적 |
| 이메일 처리 | 단일 이메일만 고려 | 개인/회사/학교 이메일, 닉네임 변경 모두 클러스터링 |
| 기여분 계산 | 전체 blame 라인 = 기여로 집계 | 공백 수정, 파일 이동, 리팩토링 제외 후 순수 로직만 |
| 노이즈 | 거품 섞인 분석 | AST Pruning으로 import/주석/config/generated 제거 |

## 3단계 파이프라인 전체 흐름도

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INPUT: GitHub username                       │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: GitHub Node ID 기반 추적                                    │
│                                                                     │
│  GraphQL → user.databaseId  (이메일 변경에도 불변)                    │
│  contributionsCollection → 레포별 커밋 수 수집                        │
└─────────────────────────────┬───────────────────────────────────────┘
                              │  github_node_id: str
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: 동적 .mailmap 생성 (MailmapBuilder)                         │
│                                                                     │
│  Rule 1. noreply email 패턴 매칭          → confidence: "high"       │
│  Rule 2. GitHub 프로필 name/email 교차 매칭 → confidence: "high"      │
│  Rule 3. 이름 Levenshtein distance 유사도  → confidence: "medium"    │
│  Rule 4. 동일 커스텀 도메인 이메일          → confidence: "low"       │
│                                                                     │
│  출력: list[MailmapEntry] → IdentityCluster                          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │  identity_cluster: IdentityCluster
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: 3단계 포렌식 쿼리 (Blame Forensics)                          │
│                                                                     │
│  Level 1 (Git Internal)                                             │
│    git blame -w -M -C -C --line-porcelain                           │
│    공백(-w), 파일 이동(-M), 코드 복사(-C -C) 제외                       │
│    → BlameLineAttribution (is_move, is_copy, is_whitespace_only)    │
│                                                                     │
│  Level 2 (Semantic Pruning)                                         │
│    Tree-sitter AST 파싱                                             │
│    import 구문, 주석, Config 설정, Generated Code 제거               │
│    → 함수/클래스 본문만 보존                                           │
│                                                                     │
│  Level 3 (Authenticity Check)                                       │
│    Vibector(WPM) + CLAVE(스타일로메트리) + Datasketch(표절) 교차 검증  │
│                                                                     │
│  출력: PureContribution (pure_logic_lines, function_bodies)          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    OUTPUT: PureContribution[]                        │
│              순수 로직 기여분 (노이즈 제거 후)                          │
└─────────────────────────────────────────────────────────────────────┘
```

## 하위 컴포넌트

- [[domain/identity-resolution/github-node-id]] — Step 1: GraphQL 기반 불변 ID 추적
- [[domain/identity-resolution/dynamic-mailmap]] — Step 2: 이메일 클러스터링
- [[domain/identity-resolution/blame-forensics]] — Step 3: 포렌식 Blame 분석
- [[domain/identity-resolution/models]] — Pydantic v2 도메인 모델 정의
