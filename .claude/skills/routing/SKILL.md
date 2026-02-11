# Auto-Routing Engine (상세 규칙)

> 프롬프트 키워드 → 최적 MCP/스킬/페르소나 자동 활성화. 핵심 매핑은 CLAUDE.md 참조.

## Routing Execution Protocol

1. **키워드 스캔**: 프롬프트에서 라우팅 테이블의 keywords 매칭
2. **파일 패턴 매칭**: 프롬프트에 파일 경로 포함 시 file_patterns로 추가 매칭
3. **MCP 활성화**: 매칭된 규칙의 mcp 서버를 우선 사용
4. **스킬 제안**: 매칭된 규칙에 skill이 있으면 해당 스킬 패턴으로 동작
5. **컨텍스트 로딩**: context_files가 있으면 해당 아키텍처 문서를 먼저 읽기
6. **페르소나 적용**: 매칭된 persona의 우선순위와 원칙을 적용

## Multi-Match Behavior

- **MCP**: 모든 매칭된 MCP 서버를 활성화 (합집합)
- **Skill**: 가장 높은 Tier의 스킬 우선 (Tier 1 > Tier 2 > Tier 3)
- **Persona**: 가장 구체적인 페르소나 우선
- **Context files**: 모든 매칭된 파일을 로딩

## Tier 1: 프로젝트 고유 라우팅 (최우선)

| 라우트 | 키워드 | MCP | 스킬 | 페르소나 | 컨텍스트 |
|--------|--------|-----|------|----------|----------|
| linear_ops | linear, 티켓, issue, sprint | linear, sequential, context7 | /linear-ops | backend | 01-overview.md |
| temporal_workflow | workflow, activity, temporal, heartbeat | context7, sequential | /temporal-dev | backend | 03-workflow.md, 02-data-models.md |
| temporal_activity | activity 생성, boilerplate | context7 | /vantict-activity | backend | 03-workflow.md |
| database | DB, PostgreSQL, pgvector, SQL | db, context7 | - | backend | 02-data-models.md |
| redis | redis, cache, 캐시 | redis | - | backend | 03-workflow.md |
| github | github, 레포, code analysis, AST | github, context7 | - | backend | 03-workflow.md |
| docker | docker, compose, 인프라, deploy | - | - | devops | 04-infrastructure.md |
| playwright_e2e | e2e, playwright, UI 테스트 | playwright, context7 | /test | qa | e2e/*.spec.ts |

## Tier 2: 도메인별 라우팅

| 라우트 | 키워드 | MCP | 스킬 | 페르소나 | 컨텍스트 |
|--------|--------|-----|------|----------|----------|
| fastapi | API, endpoint, REST | context7, db | /implement --type api | backend | 05-api-spec.md |
| react | React, Vite, UI, Tailwind | context7, magic | /implement --type component | frontend | 01-overview.md |
| quality | quality, eval, 환각, evidence | context7, sequential | - | backend | quality_review.py |
| llm_prompt | LLM, prompt, 질문 생성 | context7, sequential | - | backend | 03-workflow.md |
| document_parsing | PDF, 이력서, resume | context7 | - | backend | 02-document-analysis.md |

## Tier 3: 일반 작업 라우팅

| 라우트 | 키워드 | MCP | 스킬 | 페르소나 |
|--------|--------|-----|------|----------|
| testing | test, pytest, vitest | playwright, context7 | /test | qa |
| security | security, 보안, JWT | sequential, context7 | /analyze --focus security | security |
| performance | 성능, optimize, 병목 | sequential, playwright | /improve --perf | performance |
| architecture | 아키텍처, design, 설계 | sequential, context7 | /design | architect |
| documentation | 문서, README, guide | context7 | /document | scribe |
| debugging | bug, error, fix, debug | sequential | /troubleshoot | analyzer |
| research | 조사, research, 검색 | brave-search, context7 | /research | analyzer |
| screenshot | 스크린샷, 크롤링, headless | playwright | - | qa |
| memory | 이전 대화, 기억, recall | claude-mem | - | analyzer |

## Example Routing

```
"analyze_documents Activity에 heartbeat 패턴 추가해줘"
→ temporal_workflow + temporal_activity → MCP: context7 → Skill: /vantict-activity → Persona: backend

"ResultPage에서 콘솔 에러 나는데 Playwright로 테스트해줘"
→ playwright_e2e + react + debugging → MCP: playwright, context7, sequential → Skill: /test → Persona: qa
```
