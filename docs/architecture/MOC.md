---
title: "Jittda v5.0 Architecture"
type: moc
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# Jittda v5.0 Architecture

> AI 면접 스크립트 생성기. v5.0 HMAS + Jittda Live 통합 아키텍처.

## DDD 4계층

| 계층 | 역할 | 진입점 |
|------|------|--------|
| [[domain/MOC\|Domain]] | 순수 비즈니스 로직 (외부 의존성 0) | Identity, Scoring, Funnel, Questions |
| [[application/MOC\|Application]] | LangGraph 오케스트레이션 | HMAS Graph, Live Session, State |
| [[infrastructure/MOC\|Infrastructure]] | 외부 서비스 어댑터 | Git, GitHub, AST, LLM, Vector |
| [[interface/MOC\|Interface]] | API + UI | REST, WebSocket, Electron, D3 |

## 횡단 관심사

- [[decisions/MOC|Decisions (ADR)]] — 아키텍처 결정 기록
- [[crosscutting/MOC|Crosscutting]] — 보안, 성능, 배포, 테스트
- [[tech-stack/MOC|Tech Stack]] — 기술 스택 레지스트리
- [[RELATION-MAP]] — 전체 의존성 그래프

## 최근 업데이트

```dataview
TABLE status, updated, type
FROM "docs/architecture"
WHERE file.name != "MOC" AND type != "moc"
SORT file.mtime DESC
LIMIT 15
```

## 문서 현황

```dataview
TABLE length(rows) as "문서 수"
FROM "docs/architecture"
WHERE type != "moc"
GROUP BY type
```
