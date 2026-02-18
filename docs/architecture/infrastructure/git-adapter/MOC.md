---
title: "Git Adapter"
type: moc
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[infrastructure/MOC]]"
linear: JIT-92
---

# Git Adapter

> `jittda/backend/src/infrastructure/git/` 디렉토리에 위치하는 어댑터 묶음.
> Git CLI를 직접 호출하여 clone, blame, mailmap 파일 생성을 담당한다.
> Domain Layer에 의존하지 않으며, domain 모델(MailmapEntry, BlameLineAttribution)을 리턴한다.

## 구성 모듈

| 모듈 | 파일 | 역할 |
|------|------|------|
| CloneManager | `clone_manager.py` | shallow clone + sparse checkout 전략 |
| BlameRunner | `blame_runner.py` | `git blame -w -M -C -C` 실행 + 파싱 |
| MailmapWriter | `mailmap_writer.py` | `.mailmap` 파일 생성 및 적용 |

## 설계 원칙

- **CLI Wrapper**: subprocess/asyncio로 git CLI를 호출. GitPython/PyDriller 레이어 추가 금지.
- **Pure Output**: 반환 타입은 항상 domain 모델 (`BlameLineAttribution`, `MailmapEntry`).
- **No Business Logic**: 필터링/클러스터링은 `domain/identity/`에 위임.
- **DDD 의존성 규칙**: `infrastructure/git/` → `domain/identity/` import 금지.

## 상위 파이프라인 위치

```
CollectorWorker (W1) — github_urls 수집
        │
        ▼
CloneManager.shallow_clone()
        │
        ▼ identity_resolver_node
MailmapWriter.write()  ←  domain: mailmap_builder.build_dynamic_mailmap()
        │
        ▼
BlameRunner.run_git_blame()
        │
        ▼  domain: blame_filter.filter_blame_lines()
CleanerWorker (W2) 입력: pure_contributions
```

## 문서 목록

- [[clone-strategy]] — shallow clone, sparse checkout 전략 상세
- [[blame-extraction]] — `git blame -w -M -C -C` 실행 및 파싱
- [[mailmap-generation]] — `.mailmap` 파일 생성 및 적용

## 관련 도메인 문서

- [[domain/identity-resolution/MOC]] — IdentityCluster, MailmapBuilder, BlameFilter
- [[domain/identity-resolution/github-node-id]] — GraphQL 기반 Node ID 조회
