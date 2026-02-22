# Jittda Sniper v5.0 — Project Intelligence

> AI 면접 스크립트 생성기. 비개발자가 코드 분석 근거로 개발자 실력을 판단할 수 있게 돕는다.
> **v5.0 재건축 진행 중** — `jittda/` Clean Slate (LangGraph HMAS + DDD)

## 핵심 설계 원칙
1. 모든 점수에 코드/경력 데이터 근거 표시
2. 질문은 후보자 실제 GitHub 코드에서 추출
3. 답변 가이드/전문 용어는 비개발자도 이해 가능하게
4. 출력 일관성 보장 (동일 입력 → 동일 결과)
5. 모든 판단에 신뢰도 표시

## Tech Stack (요약)
Frontend: Vite + React 19 + Tailwind 4 + D3.js v7 | Backend: FastAPI + Python 3.11 | Orchestration: LangGraph 1.0.8+ (HMAS)
DB: PostgreSQL 16 + pgvector | Cache: Redis 7 | LLM: Kimi K2.5 (Instructor + Langfuse) | AST: Tree-sitter 0.24+ | Testing: Playwright + pytest

## 🔴 디렉토리 규칙

| 경로 | 권한 |
|------|------|
| `frontend/`, `backend/`, 루트 레거시 | **READ-ONLY** — v4.0 참조만, 수정/생성 금지 |
| `jittda/` | **READ-WRITE** — v5.0 모든 구현은 여기서만 |
| `docs/`, `.claude/`, `plan/` | **READ-WRITE** — 문서, 스킬, 설계 |

> **절대 규칙**: 루트 레거시 디렉토리 수정 금지. 구현은 반드시 `jittda/` 하위에서.

## 🛠 Operation Rules

1. 참조 문서는 **해당 작업에 직접 필요할 때만** Read (토큰 효율 원칙)
2. v5.0 작업 시 → 해당 Phase 설계 문서를 **반드시 먼저 Read** (아래 Phase Map 참조)
3. v5.0 참조 시 → **Obsidian vault에서 먼저 확인** (`/obsidian-api` 스킬 사용)
4. Linear 작업 시 → `docs/claude-refs/dev-rules.md` 먼저 읽기
5. UI/UX 작업 시 → `docs/claude-refs/ux-guidelines.md` + `jittda-design-system` 스킬
6. Git: feature branch → PR → merge
7. DDD: domain → infrastructure import 금지, Thin Wrapper 노드, Reference Passing

## 🔵 Obsidian 연동 규칙

> Vault 구조: DDD 4계층 (domain/ application/ infrastructure/ interface/) + decisions/ + crosscutting/

### 구현 전 (필수)
- `/obsidian-api` 스킬로 해당 컴포넌트의 Obsidian 문서 **먼저 확인**
- Vault 경로: `domain/`, `infrastructure/`, `application/`, `interface/` 하위 MOC.md 참조

### Phase 완료 후 (필수)
1. **Obsidian 업데이트**: 구현 중 변경된 설계/구조를 vault에 반영 (수정/마이그레이션)
2. **Linear 업데이트**: 해당 Phase 티켓 상태 업데이트 (`/linear-ops`)
3. **관련 문서 전파**: 변경으로 영향받는 다른 vault 문서도 함께 수정
4. **이슈 정리**: 구현 중 발견된 이슈를 Linear에 기록

### 🔴 PR/머지 전 Obsidian 정합성 검증 (필수)
> Phase 4 교훈: 구현만 하고 Obsidian sync를 미루면 문서 부정확성이 누적됨.

**어떤 워크플로우**(`/execute-plan`, `/subagent-driven-development`, 수동 구현)를 쓰든, PR 생성/머지 전 반드시:
1. `git diff --stat` → 변경된 `jittda/` 파일 목록 추출
2. 변경 파일의 DDD 계층 판별 (domain/infrastructure/application/interface)
3. 대응 Obsidian MOC 확인 (`obsidian_vault_get "{layer}/MOC.md"`)
4. 불일치 발견 시 → Obsidian 즉시 수정 후 PR 진행

```
구현 전: Obsidian 확인 → Phase 설계문서 Read → 구현
구현 후: Obsidian 정합성 검증 → Obsidian 수정 → Linear 업데이트 → 이슈 정리 → PR
```

## Auto-Routing (키워드 → MCP/스킬)

| 카테고리 | 키워드 | MCP | 스킬 |
|----------|--------|-----|------|
| v5 도메인 | identity, funnel, scoring, question | sequential | → Phase 설계문서 |
| v5 인프라 | tree-sitter, AST, git adapter, LLM, langfuse, pgvector, linkedin | context7 | → Phase 설계문서 |
| v5 앱 | StateGraph, supervisor, HMAS, LangGraph | context7, sequential | → Phase 설계문서 |
| v5 프론트 | D3, radar, treemap, heatmap, React, Tailwind, Seed Design | context7, magic, seed-docs | → Phase 설계문서, /jittda-design-system |
| 프로젝트 | linear, 티켓, sprint, lifecycle | sequential | /linear-ops |
| 개발도구 | bug, debug, TDD, test | sequential, qmd | /troubleshoot, /test |
| 인프라/배포 | docker, compose, DB, SQL | context7 | /arch-infra |
| 설계/분석 | architecture, design, security, 성능 | sequential, context7 | /design, /analyze |
| 검색/조사 | research, 코드 검색, 사용처 | brave-search, qmd | /research |
| 문서/기억 | obsidian, vault, 이전 대화 | claude-mem | /obsidian-api |
| Git/워크플로 | git, commit, PR, plan, brainstorm | superpowers | /git-ops, /brainstorm |
| Phase 자동화 | phase-plan, phase-sync, pipeline, 마일스톤, 동기화, 회고 | - | /phase-plan, /phase-sync, /phase-pipeline |

상세 → `.claude/skills/routing/SKILL.md`

## 📁 Phase Map (v5.0 — 필요 시만 Read)

> 구현 계획: `docs/plans/2026-02-15-jittda-v5-reconstruction.md`
> 원본 설계서: `plan/2026-02-15-v5-final-design.md`

| Phase | 설계문서 | Linear | 범위 |
|-------|---------|--------|------|
| 0 | `plan/v5-design/phase0-scaffolding.md` | JIT-82~85 | 프로젝트 구조, Docker, DB, Makefile |
| 1 | `plan/v5-design/phase1-domain.md` | JIT-86~91, 124 | Identity, Funnel, Scoring, LinkedIn 모델 |
| 2 | `plan/v5-design/phase2-infrastructure.md` | JIT-92~99, 125 | Git, AST, LLM, Vector, LinkedIn 어댑터 |
| 3 | `plan/v5-design/phase3-application.md` | JIT-100~105 | LangGraph State, HMAS Graph, FastAPI |
| 4 | `plan/v5-design/phase4-questions.md` | JIT-106~110 | 질문 생성, Enhancement, QualityGate |
| 5 | `plan/v5-design/phase5-output-frontend.md` | JIT-111~119 | OutputAssembler, D3 차트, ResultPage |
| 6 | `plan/v5-design/phase6-testing.md` | JIT-120~123 | 단위/E2E 테스트, 성능 벤치마크 |

## 📁 레거시 참조 (v4.0 — Read-only)

| 영역 | 파일 |
|------|------|
| 제품 미션 | `docs/claude-refs/product-mission.md` |
| 출력 일관성 | `docs/claude-refs/output-consistency.md` |
| UX 가이드 | `docs/claude-refs/ux-guidelines.md` |
| 개발 규칙 | `docs/claude-refs/dev-rules.md` |
| Tech Stack | `docs/claude-refs/tech-stack.md` |
| E2E 전략 | `docs/claude-references/playwright-e2e-strategy.md` |
| 아키텍처 | `docs/architecture/*.md` |
