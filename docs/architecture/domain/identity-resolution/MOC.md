---
title: Identity Resolution
type: moc
layer: domain
parent: "[[domain/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# Identity Resolution

`review1.md 2.1`에서 지적된 **사용자 식별 및 기여분 추출** 결함을 해결하는 핵심 도메인 모듈이다.

## 3단계 파이프라인 개요

```
Step 1: GitHub Node ID 기반 추적
        이메일이 바뀌어도 불변인 databaseId로 유저 특정

        ↓

Step 2: 동적 .mailmap 생성
        커밋 히스토리에서 동일인 이메일/이름 클러스터링
        (noreply / 프로필 교차 / Levenshtein / 도메인 매칭)

        ↓

Step 3: 3단계 포렌식 쿼리 (Blame Forensics)
        Level 1 — git blame -w -M -C -C (Git Internal)
        Level 2 — Tree-sitter AST Pruning (Semantic)
        Level 3 — Vibector + CLAVE + Datasketch (Authenticity)
```

## 하위 문서

```dataview
TABLE title, status, type
FROM "docs/architecture/domain/identity-resolution"
WHERE type = "component"
SORT file.name ASC
```

## 관련 Linear 티켓

| 티켓 | 제목 |
|------|------|
| JIT-86 | Identity Resolution 모델 (MailmapEntry, IdentityCluster, BlameLineAttribution, PureContribution) |
| JIT-87 | Mailmap Builder (동적 .mailmap 생성: noreply + Levenshtein + domain) |
| JIT-88 | Blame Filter (blame 라인 필터링, identity_cluster 기반) |
| JIT-89 | Semantic Pruner 규칙 (AST 노이즈 제거: import, 주석, config, generated) |
