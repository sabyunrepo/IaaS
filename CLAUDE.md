# Vantict Sniper v4.0 — Project Intelligence

> AI 면접 스크립트 생성기. 비개발자가 코드 분석 근거로 개발자 실력을 판단할 수 있게 돕는다.

## 핵심 설계 원칙
1. 모든 점수에 코드/경력 데이터 근거 표시
2. 질문은 후보자 실제 GitHub 코드에서 추출
3. 답변 가이드/전문 용어는 비개발자도 이해 가능하게
4. 출력 일관성 보장 (동일 입력 → 동일 결과)
5. 모든 판단에 신뢰도(🟢높음/🟡중간/🔴낮음) 표시

## Tech Stack (요약)
Frontend: Vite + React 19 + Tailwind 4 | Backend: FastAPI + Python 3.11 | Orchestration: Temporal.io
DB: PostgreSQL 16 + pgvector | Cache: Redis 7 | LLM: Kimi K2.5 (Langfuse-first) | Testing: Playwright + pytest

## 🛠 Operation Rules
1. 아래 참조 문서는 **해당 작업에 직접 필요할 때만** Read로 로딩할 것
2. Linear 작업 시 → `docs/claude-refs/dev-rules.md` 먼저 읽기
3. UI/UX 작업 시 → `docs/claude-refs/ux-guidelines.md` 먼저 읽기
4. 점수/평가 작업 시 → `docs/claude-refs/output-consistency.md` 먼저 읽기
5. Git 워크플로우: 한글 이슈→feature branch→한글 PR→merge→main sync (자율 진행)
6. Temporal Activity: `@activity.defn` 필수, >30s→heartbeat, LLM→CachedLLMService

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

상세 라우팅 프로토콜 → `.claude/skills/routing/SKILL.md`

## 📁 Context Mapping (필요 시만 Read)

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
