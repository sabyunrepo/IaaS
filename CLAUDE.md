# Jittda Sniper v5.0 — Project Intelligence

> AI 면접 스크립트 생성기. 비개발자가 코드 분석 근거로 개발자 실력을 판단할 수 있게 돕는다.
> **v5.0 재건축 진행 중** — `jittda/` Clean Slate (LangGraph HMAS + DDD)

## 핵심 설계 원칙
1. 모든 점수에 코드/경력 데이터 근거 표시
2. 질문은 후보자 실제 GitHub 코드에서 추출
3. 답변 가이드/전문 용어는 비개발자도 이해 가능하게
4. 출력 일관성 보장 (동일 입력 → 동일 결과)
5. 모든 판단에 신뢰도(🟢높음/🟡중간/🔴낮음) 표시

## Tech Stack (요약)
Frontend: Vite + React 19 + Tailwind 4 + D3.js v7 | Backend: FastAPI + Python 3.11 | Orchestration: LangGraph 1.0.8+ (HMAS)
DB: PostgreSQL 16 + pgvector | Cache: Redis 7 | LLM: Kimi K2.5 (Instructor + Langfuse) | AST: Tree-sitter 0.24+ | Testing: Playwright + pytest

## 🛠 Operation Rules
1. 아래 참조 문서는 **해당 작업에 직접 필요할 때만** Read로 로딩할 것
2. **v5.0 작업 시 → 해당 Phase 설계 문서를 반드시 먼저 Read** (아래 Context Mapping 참조)
3. Linear 작업 시 → `docs/claude-refs/dev-rules.md` 먼저 읽기
4. UI/UX 작업 시 → `docs/claude-refs/ux-guidelines.md` 먼저 읽기
5. 점수/평가 작업 시 → `docs/claude-refs/output-consistency.md` 먼저 읽기
6. Git 워크플로우: GitButler CLI(`but`) 사용 → `/but-ops` 스킬 참조
7. jittda/ DDD 규칙: domain → infrastructure import 금지, 노드는 Thin Wrapper, State에 Raw Data 금지 (Reference Passing)

## Auto-Routing (키워드 → MCP/스킬)

| 키워드 | MCP | 스킬 |
|--------|-----|------|
| linear, 티켓, sprint | linear, sequential | /linear-ops |
| workflow, temporal, heartbeat | context7, sequential | /temporal-dev |
| activity 생성, boilerplate | context7 | /vantict-activity |
| DB, PostgreSQL, SQL | db, context7 | - |
| docker, compose, 인프라 | Bash(docker:*) | - |
| e2e, playwright | playwright, context7 | /test |
| API, endpoint, REST | context7, db | /implement --type api |
| React, UI, Tailwind | context7, magic | /implement --type component |
| quality, eval, 환각 | context7, sequential | - |
| LLM, prompt, 질문 생성 | context7, sequential | - |
| 코드 검색, 구현 위치, 사용처, 호출 관계 | qmd | - |
| bug, error, debug | sequential, qmd | /troubleshoot |
| 조사, research | brave-search, context7 | /research |
| 아키텍처, design | sequential, context7, qmd | /design |
| security, 보안 | sequential, context7 | /analyze --focus security |
| 성능, optimize | sequential, playwright | /improve --perf |
| 스크린샷, 크롤링 | playwright | - |
| 이전 대화, 기억 | claude-mem | - |
| 프로젝트, 기획, lifecycle | linear, sequential | - |
| 기능 구현, 설계, plan | superpowers | /brainstorm → /write-plan → /execute-plan |
| TDD, 테스트 주도 | superpowers | test-driven-development 스킬 |
| 디버깅, 근본 원인 | superpowers, sequential | systematic-debugging 스킬 |
| git, commit, branch, push, pr | - | /but-ops |
| jittda, v5, HMAS, LangGraph | context7, sequential | → Phase별 설계문서 참조 |
| identity, mailmap, blame | sequential | → `plan/v5-design/phase1-domain.md` |
| funnel, scoring, 지표 | sequential | → `plan/v5-design/phase1-domain.md` |
| tree-sitter, AST, radon | context7 | → `plan/v5-design/phase2-infrastructure.md` |
| instructor, langfuse, 프롬프트 | context7 | → `plan/v5-design/phase2-infrastructure.md` + `phase4-questions.md` |
| StateGraph, supervisor, worker | context7 | → `plan/v5-design/phase3-application.md` |
| D3, 차트, radar, treemap, heatmap | context7, magic | → `plan/v5-design/phase5-output-frontend.md` |

상세 라우팅 프로토콜 → `.claude/skills/routing/SKILL.md`

## 📁 Context Mapping (필요 시만 Read)

### v5.0 재건축 설계 참조 (jittda/)

> **규칙:** 아래 작업을 할 때 해당 Phase 설계 문서를 **반드시 먼저 Read**할 것.
> 구현 계획 전체: `docs/plans/2026-02-15-jittda-v5-reconstruction.md`
> 원본 설계서: `plan/2026-02-15-v5-final-design.md`

| 작업 | 먼저 읽을 참조 문서 | Linear 티켓 |
|------|-------------------|------------|
| 프로젝트 구조, Docker, DB, Makefile | `plan/v5-design/phase0-scaffolding.md` | JIT-82~85 |
| Identity Resolution, Mailmap, Blame Filter | `plan/v5-design/phase1-domain.md` | JIT-86~89 |
| LinkedIn 프로필 도메인 모델 | `plan/v5-design/phase1-domain.md` | JIT-124 |
| Funnel Selection, Scoring Calculator | `plan/v5-design/phase1-domain.md` | JIT-90~91 |
| Git 어댑터, GitHub GraphQL | `plan/v5-design/phase2-infrastructure.md` | JIT-92~93 |
| Tree-sitter AST, Radon/Lizard 복잡도 | `plan/v5-design/phase2-infrastructure.md` | JIT-94~95 |
| SonarQube, Datasketch 표절 탐지 | `plan/v5-design/phase2-infrastructure.md` | JIT-96~97 |
| LinkedIn 어댑터 (BrightData 스크레이핑) | `plan/v5-design/phase2-infrastructure.md` | JIT-125 |
| Instructor + Langfuse LLM 클라이언트 | `plan/v5-design/phase2-infrastructure.md` | JIT-98 |
| pgvector 벡터 검색, 임베딩 | `plan/v5-design/phase2-infrastructure.md` | JIT-99 |
| LangGraph State, Reference Passing | `plan/v5-design/phase3-application.md` | JIT-100 |
| Forensic/Logic/Stack Supervisor Graph | `plan/v5-design/phase3-application.md` | JIT-101~103 |
| MetaAgent Graph 조립, HMAS 전체 | `plan/v5-design/phase3-application.md` | JIT-104 |
| FastAPI + WebSocket 통합 | `plan/v5-design/phase3-application.md` | JIT-105 |
| 질문 생성 (TopicSelector, 3전략) | `plan/v5-design/phase4-questions.md` | JIT-106~107 |
| Enhancement Agents, QualityGate | `plan/v5-design/phase4-questions.md` | JIT-108~109 |
| Langfuse 프롬프트 관리 | `plan/v5-design/phase4-questions.md` | JIT-110 |
| OutputAssembler, 4대 지표 산출 | `plan/v5-design/phase5-output-frontend.md` | JIT-111~112 |
| D3.js 차트 (Radar, Treemap, Heatmap) | `plan/v5-design/phase5-output-frontend.md` | JIT-113~116 |
| ResultPage 탭 (Overview, DeepDive, Interview) | `plan/v5-design/phase5-output-frontend.md` | JIT-117~119 |
| 단위 테스트, E2E, Playwright | `plan/v5-design/phase6-testing.md` | JIT-120~122 |
| 성능 벤치마크, 아키텍처 문서 | `plan/v5-design/phase6-testing.md` | JIT-123 |

### 기존 참조 문서 (v4.0 레거시 — Read-only 참고)

| 영역 | 참조 파일 |
|------|----------|
| 제품 미션/타겟 | `docs/claude-refs/product-mission.md` |
| 출력 일관성/신뢰도 | `docs/claude-refs/output-consistency.md` |
| 비개발자 UX | `docs/claude-refs/ux-guidelines.md` |
| Tech Stack/아키텍처/MCP | `docs/claude-refs/tech-stack.md` |
| 개발 규칙/네이밍/Git | `docs/claude-refs/dev-rules.md` |
| 라우팅 상세 | `.claude/skills/routing/SKILL.md` |
| 개선 엔진 (P0~P2) | `.claude/skills/improvement-engine/SKILL.md` |
| 품질 검증 엔진 | `.claude/skills/quality-engine/SKILL.md` |
| A/B 테스트 전략 | `.claude/skills/ab-testing/SKILL.md` |
| 디자인 패턴 | `docs/claude-references/` (기존) |
| E2E 테스트 전략 | `docs/claude-references/playwright-e2e-strategy.md` |
| 프로젝트 생애주기 | `docs/claude-refs/project-lifecycle.md` |
| 프로젝트 컨텍스트 | `docs/projects/{slug}/CONTEXT.md` |
| QMD 코드 검색 | `.claude/skills/qmd-search/SKILL.md` |
| 아키텍처 문서 | `docs/architecture/*.md` |
