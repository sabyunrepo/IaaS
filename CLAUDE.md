# Vantict Sniper v4.0 - Project Intelligence

> AI Technical Interview Script Generator
> 이 파일은 Claude Code가 프롬프트를 받으면 **자동으로** 최적의 MCP 서버와 스킬을 선택하도록 하는 마스터 라우팅 시스템입니다.

---

## Auto-Routing Engine

**작동 원리**: 사용자 프롬프트를 받으면 아래 라우팅 테이블을 기반으로 자동 판단하여 최적의 MCP 서버, 스킬, 페르소나를 활성화합니다. 명시적 `/sc:` 커맨드 없이도 프롬프트 키워드만으로 자동 라우팅됩니다.

### Routing Decision Table

프롬프트를 받으면 아래 규칙을 **위에서 아래로 순서대로** 매칭하고, **첫 번째 매칭되는 규칙**의 MCP + 스킬을 활성화합니다. 복수 매칭 시 모두 활성화합니다.

```yaml
# ========================================
# TIER 1: 프로젝트 고유 라우팅 (최우선)
# ========================================

temporal_workflow:
  keywords: [workflow, activity, temporal, worker, signal, query, heartbeat, retry, checkpoint, 워크플로우, 액티비티]
  file_patterns: ["**/workflows/**", "**/activities/**", "**/worker.py"]
  activate:
    skill: /temporal-dev
    mcp: [context7, sequential]
    persona: backend
    context_files:
      - docs/architecture/03-workflow.md
      - docs/architecture/02-data-models.md

temporal_activity_create:
  keywords: [activity 생성, activity 만들, 새 activity, new activity, boilerplate]
  activate:
    skill: /vantict-activity
    mcp: [context7]
    persona: backend
    context_files:
      - docs/architecture/03-workflow.md

database_query:
  keywords: [database, DB, PostgreSQL, pgvector, 벡터, embedding, 쿼리, query, schema, migration, 스키마, 마이그레이션, SQL]
  file_patterns: ["**/models/**", "**/init-db.sql", "**/vector_store.py"]
  activate:
    mcp: [db, context7]
    persona: backend
    context_files:
      - docs/architecture/02-data-models.md

redis_cache:
  keywords: [redis, cache, 캐시, session, LLM 캐시, llm_cache, checkpoint_store]
  file_patterns: ["**/llm_cache.py", "**/checkpoint_store.py"]
  activate:
    mcp: [redis]
    persona: backend
    context_files:
      - docs/architecture/03-workflow.md

github_analysis:
  keywords: [github, repository, 레포, clone, git 분석, code analysis, AST, 코드 분석, PyDriller, PyGithub, 커밋, commit, 기여도, contribution, 오픈소스]
  file_patterns: ["**/github_service.py", "**/code_analysis.py", "**/code_analyzer.py"]
  activate:
    mcp: [github, context7]
    persona: backend
    context_files:
      - docs/architecture/03-workflow.md
      - docs/humanprocess/03-code-analysis.md

docker_infra:
  keywords: [docker, compose, container, 컨테이너, localstack, 인프라, infrastructure, deploy, 배포]
  file_patterns: ["docker-compose*.yml", "Dockerfile*", "Makefile"]
  activate:
    mcp: [docker]
    persona: devops
    context_files:
      - docs/architecture/04-infrastructure.md

# ========================================
# TIER 2: 도메인별 라우팅
# ========================================

fastapi_backend:
  keywords: [FastAPI, API, endpoint, 엔드포인트, route, 라우터, REST, 서버]
  file_patterns: ["**/api/**", "**/routes/**", "**/main.py"]
  activate:
    skill: /implement --type api
    mcp: [context7, db]
    persona: backend
    context_files:
      - docs/architecture/05-api-spec.md

react_frontend:
  keywords: [React, Vite, component, 컴포넌트, UI, 프론트엔드, frontend, i18n, 다국어, 번역, Tailwind]
  file_patterns: ["**/frontend/**", "**/*.tsx", "**/*.jsx"]
  activate:
    skill: /implement --type component
    mcp: [context7, magic]
    persona: frontend
    context_files:
      - docs/architecture/01-overview.md

llm_prompt:
  keywords: [LLM, prompt, 프롬프트, GPT, Claude, OpenAI, Anthropic, 질문 생성, question generation]
  file_patterns: ["**/prompts/**", "**/llm_service.py"]
  activate:
    mcp: [context7, sequential]
    persona: backend
    context_files:
      - docs/architecture/03-workflow.md
      - docs/humanprocess/05-question-generation.md

document_parsing:
  keywords: [PDF, DOCX, 이력서, resume, portfolio, 포트폴리오, 문서 파싱, document parser]
  file_patterns: ["**/document_parser.py", "**/document_analysis.py"]
  activate:
    mcp: [context7]
    persona: backend
    context_files:
      - docs/humanprocess/02-document-analysis.md

# ========================================
# TIER 3: 일반 작업 라우팅
# ========================================

testing:
  keywords: [test, 테스트, E2E, pytest, coverage, 커버리지]
  activate:
    skill: /test
    mcp: [playwright, context7]
    persona: qa

security:
  keywords: [security, 보안, vulnerability, 취약점, authentication, 인증, JWT, token]
  activate:
    skill: /analyze --focus security
    mcp: [sequential, context7]
    persona: security

performance:
  keywords: [performance, 성능, 최적화, optimize, bottleneck, 병목, slow, 느린]
  activate:
    skill: /improve --perf
    mcp: [sequential, playwright]
    persona: performance

architecture:
  keywords: [architecture, 아키텍처, design, 설계, 구조, structure, system design]
  activate:
    skill: /design
    mcp: [sequential, context7]
    persona: architect
    context_files:
      - docs/architecture/ARCHITECTURE.md
      - docs/architecture/01-overview.md

documentation:
  keywords: [document, 문서, README, 가이드, guide, 설명]
  activate:
    skill: /document
    mcp: [context7]
    persona: scribe

debugging:
  keywords: [bug, 버그, error, 에러, fix, 수정, debug, 디버그, 오류, traceback, exception]
  activate:
    skill: /troubleshoot
    mcp: [sequential, db, redis]
    persona: analyzer

research:
  keywords: [조사, research, 검색, search, 찾아, 알아봐, investigate]
  activate:
    skill: /research
    mcp: [brave-search, context7]
    persona: analyzer

screenshot_crawl:
  keywords: [screenshot, 스크린샷, crawl, 크롤링, render, 렌더링, 캡처, capture, headless]
  activate:
    mcp: [puppeteer, playwright]
    persona: qa

memory_recall:
  keywords: [이전 대화, 기억, remember, 지난번, 저번에, recall, history]
  activate:
    mcp: [claude-mem]
    persona: analyzer
```

### Routing Execution Protocol

프롬프트를 받으면 다음 순서로 처리:

1. **키워드 스캔**: 프롬프트에서 위 테이블의 keywords를 매칭
2. **파일 패턴 매칭**: 프롬프트에 파일 경로가 포함된 경우 file_patterns로 추가 매칭
3. **MCP 활성화**: 매칭된 규칙의 mcp 서버를 우선 사용
4. **스킬 제안**: 매칭된 규칙에 skill이 있으면 해당 스킬 패턴으로 동작
5. **컨텍스트 로딩**: context_files가 있으면 해당 아키텍처 문서를 먼저 읽기
6. **페르소나 적용**: 매칭된 persona의 우선순위와 원칙을 적용

### Multi-Match Behavior

여러 규칙이 동시에 매칭될 경우:
- **MCP**: 모든 매칭된 MCP 서버를 활성화 (합집합)
- **Skill**: 가장 높은 Tier의 스킬 우선 (Tier 1 > Tier 2 > Tier 3)
- **Persona**: 가장 구체적인 페르소나 우선
- **Context files**: 모든 매칭된 파일을 로딩

### Example Routing

```
사용자: "analyze_documents Activity에 heartbeat 패턴 추가해줘"
→ 매칭: temporal_workflow + temporal_activity_create
→ MCP: context7
→ Skill: /vantict-activity (Tier 1 우선)
→ Context: 03-workflow.md
→ Persona: backend

사용자: "pgvector에 새 인덱스 추가하고 싶어"
→ 매칭: database_query
→ MCP: db, context7
→ Context: 02-data-models.md
→ Persona: backend

사용자: "Docker Compose에서 Redis가 안 뜨는데"
→ 매칭: docker_infra + redis_cache + debugging
→ MCP: docker, redis, sequential
→ Skill: /troubleshoot
→ Context: 04-infrastructure.md
→ Persona: devops (가장 구체적)

사용자: "면접 질문 생성 프롬프트를 개선해줘"
→ 매칭: llm_prompt
→ MCP: context7, sequential
→ Context: 03-workflow.md, 05-question-generation.md
→ Persona: backend
```

---

## Project Context

### Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | Vite + React + Tailwind CSS, react-i18next |
| Backend | FastAPI, Python 3.11 |
| Orchestration | Temporal.io |
| Database | PostgreSQL 16 + pgvector |
| Cache | Redis 7 |
| Storage | LocalStack S3 → AWS S3 |
| LLM | OpenAI GPT-4o / Anthropic Claude |
| Container | Docker Compose |
| Git Analysis | PyGithub (API), PyDriller (로컬 분석), ast (Python), tree-sitter (JS/TS) |
| LinkedIn | Proxycurl API (프로필 수집) |

### Architecture Documents
| Document | Path |
|----------|------|
| Master | `docs/architecture/ARCHITECTURE.md` |
| Overview | `docs/architecture/01-overview.md` |
| Data Models | `docs/architecture/02-data-models.md` |
| Workflow | `docs/architecture/03-workflow.md` |
| Infrastructure | `docs/architecture/04-infrastructure.md` |
| API Spec | `docs/architecture/05-api-spec.md` |
| Human Process | `docs/humanprocess/` |

### Available MCP Servers
| Server | Purpose | Auto-Route Trigger | Status |
|--------|---------|-------------------|--------|
| `db` | PostgreSQL + pgvector 직접 쿼리 | DB/SQL/스키마 키워드 | ⚠️ DB 연결 문자열 필요 |
| `redis` | Redis 캐시 관리 | cache/캐시/Redis 키워드 | ❌ 미설치 (Redis 서버+패키지 필요) |
| `github` | GitHub API 통합 (플러그인) | GitHub/레포/코드분석 키워드 | ⚠️ 재인증 필요 |
| `docker` | Docker 컨테이너 관리 | Docker/컨테이너/인프라 키워드 | ✅ |
| `context7` | 라이브러리 공식 문서 | 프레임워크/SDK 질문 | ✅ |
| `sequential` | 복잡한 분석/추론 | 디버깅/설계/분석 | ✅ |
| `magic` | UI 컴포넌트 생성 | 프론트엔드/컴포넌트 | ✅ |
| `brave-search` | 웹 검색 | 조사/리서치 | ✅ (BRAVE_API_KEY 필요) |
| `playwright` | 브라우저 테스트/자동화 | E2E/테스트 | ✅ |
| `puppeteer` | 브라우저 스크린샷/크롤링 | 스크린샷/크롤링/렌더링 | ✅ |
| `claude-mem` | 대화 메모리/검색 (플러그인) | 이전 대화 참조/기억 | ✅ |

### Project-Specific Skills (`.claude/skills/`)
| Skill | Purpose | Status |
|-------|---------|--------|
| `/temporal-dev` | Temporal 워크플로우/Activity 개발 | ✅ |
| `/vantict-activity` | Activity 보일러플레이트 생성 | ✅ |
| `/implement` | API/컴포넌트/서비스 구현 (`--type api\|component\|service`) | ✅ |
| `/test` | 테스트 작성 및 실행 (pytest, Playwright) | ✅ |
| `/design` | 시스템 아키텍처 설계 | ✅ |
| `/document` | 문서 작성/업데이트 | ✅ |
| `/troubleshoot` | 버그 수정/디버깅 | ✅ |
| `/research` | 조사/탐색 | ✅ |
| `/analyze` | 보안/코드 품질/의존성 분석 (`--focus security\|quality\|dependency`) | ✅ |
| `/improve` | 성능 최적화 (`--perf`) | ✅ |

---

## Development Rules (Project-Specific)

### File Placement
```
backend/app/workflows/activities/  → 새 Activity 파일
backend/app/workflows/             → 새 Workflow 파일
backend/app/services/              → 비즈니스 로직 서비스
backend/app/api/routes/            → API 엔드포인트
backend/app/models/                → 데이터 모델
backend/app/prompts/               → LLM 프롬프트 YAML
frontend/src/components/           → React 컴포넌트
frontend/src/pages/                → React 페이지
frontend/public/locales/           → i18n 번역 파일
```

### Naming Conventions
- Activity 함수: `snake_case` (예: `analyze_documents`, `craft_question`)
- Workflow 클래스: `PascalCase` + `Workflow` 접미사 (예: `InterviewGenerationWorkflow`)
- API 라우터: `snake_case` (예: `create_job`, `get_job_status`)
- 프론트엔드 컴포넌트: `PascalCase` (예: `InterviewForm`, `QuestionCard`)

### File Size & Separation Rules
- 단일 파일이 300줄을 초과하면 분리를 검토할 것
- HTML 파일에 인라인 `<script>` / `<style>` 블록을 넣지 말 것 — 외부 `.js` / `.css` 파일로 분리
- 시나리오 데이터(`scenario-*.js`)는 후보자별 개별 파일로 관리
- 데모 UI의 앱 로직은 `app.js`, HTML 구조는 `index.html`에 분리 유지
- 새 파일 생성 시 기존 파일과 책임이 겹치지 않도록 역할을 명확히 구분

### Temporal Patterns (Mandatory)
1. 모든 Activity는 `@activity.defn` 데코레이터 필수
2. 긴 Activity(>30s)는 반드시 `activity.heartbeat()` 사용
3. LLM 호출 Activity는 `CachedLLMService` 사용 (Redis 캐시)
4. 각 Phase 완료 시 checkpoint 저장
5. `worker.py`에 새 Activity 등록 필수
