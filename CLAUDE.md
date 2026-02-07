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
| LLM | Kimi K2.5 (moonshot-v1-auto) — Langfuse-first, fallback: GPT-4o / Claude |
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

### Utility Scripts (`backend/scripts/`)

| 스크립트 | 용도 | 사용법 |
|----------|------|--------|
| `create_test_job.py` | 테스트 Job 생성 (프론트엔드 확인용) | `docker compose exec backend python scripts/create_test_job.py` |
| `upload_prompts_to_langfuse.py` | Langfuse 프롬프트 업로드 | `docker compose exec backend python scripts/upload_prompts_to_langfuse.py --production` |

**테스트 Job 생성 예시:**
```bash
# 기본 (hoone0802@gmail.com, CTO/VP, en, 20문제, LinkedIn+GitHub)
docker compose exec backend python scripts/create_test_job.py

# 커스텀
docker compose exec backend python scripts/create_test_job.py \
    --email hoone0802@gmail.com --level 시니어 --lang ko --questions 15

# 미리보기
docker compose exec backend python scripts/create_test_job.py --dry-run
```

**Langfuse 프롬프트 업로드 주의사항:**
- 반드시 `--production` 플래그 사용 (없으면 워커가 구버전 사용)
- 모델 설정은 `llm_config.py` 단일 소스 — 스크립트에서 자동 참조

### 자율 GitHub Issue/PR/Merge 워크플로우 (Autonomous QA)

자체 디버깅/검증 과정에서 문제를 발견하면 다음 워크플로우를 **자동으로** 수행:

1. **이슈 생성**: `gh issue create` — 한글 제목 + 한글 본문 (문제 요약, 영향, 재현 방법)
2. **브랜치 생성**: `git checkout -b fix/이슈-설명` 또는 `feature/이슈-설명`
3. **수정 → 커밋**: 한글 커밋 메시지 + `Closes #이슈번호`
4. **PR 생성**: `gh pr create` — 한글 제목 + 한글 본문 (요약, 수정 파일, 테스트 결과)
5. **머지**: `gh pr merge --merge`
6. **이슈 클로즈 확인**: `Closes #N`으로 자동 클로즈, 안 되면 `gh issue close` 수동 실행
7. **main 동기화**: `git checkout main && git pull`

**규칙:**
- 모든 GitHub 커뮤니케이션(이슈/PR/커밋 메시지)은 **한글**로 작성
- 사용자에게 승인 요청 없이 자율적으로 진행 (자율 QA 권한 부여 시)
- 이슈 본문에 반드시 포함: 문제 요약, 영향 범위, 테스트 Job ID (있으면)
- PR 본문에 반드시 포함: 수정 요약, 파일 목록, 이전/이후 비교 결과

### Temporal Patterns (Mandatory)
1. 모든 Activity는 `@activity.defn` 데코레이터 필수
2. 긴 Activity(>30s)는 반드시 `activity.heartbeat()` 사용
3. LLM 호출 Activity는 `CachedLLMService` 사용 (Redis 캐시)
4. 각 Phase 완료 시 checkpoint 저장
5. `worker.py`에 새 Activity 등록 필수

### 고아 서브에이전트 프로세스 관리 (Mandatory)

Task 도구로 생성된 서브에이전트가 작업 완료 후에도 종료되지 않아 메모리 누수 발생 가능.

**규칙:**
1. 작업 완료 후 고아 프로세스 확인: `ps aux | grep '[c]laude' | grep -v grep | wc -l`
2. 불필요한 서브에이전트 정리: `ps aux | grep '[/]Users/sabyun/.local/bin/claude' | awk '{print $2}' | xargs kill 2>/dev/null`
3. 메인 세션(interactive tty) 프로세스는 유지
4. 세션 종료 시 반드시 고아 프로세스 확인 + 정리

**경고 기준:**
- claude 프로세스 5개 초과 시 정리 필요
- macOS PhysMem unused < 2GB 시 즉시 정리

---

## 🔄 Continuous Improvement Engine (지속적 개선 엔진)

> **핵심 원칙**: 한 번의 개선으로 끝나지 않는다. 매 사이클마다 측정 → 분석 → 개선 → 검증을 반복하여 프로젝트 품질을 지속적으로 향상시킨다.

### 개선 사이클 구조

```
┌─────────────────────────────────────────────┐
│         CONTINUOUS IMPROVEMENT LOOP          │
│                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │ MEASURE │ →  │ ANALYZE │ →  │ IMPROVE │ │
│  │ (측정)  │    │ (분석)  │    │ (개선)  │ │
│  └────↑────┘    └─────────┘    └────│────┘ │
│       │                              │      │
│  ┌────│────┐                   ┌────↓────┐ │
│  │ REPORT │ ←──────────────── │ VERIFY  │ │
│  │ (보고) │                   │ (검증)  │ │
│  └─────────┘                   └─────────┘ │
└─────────────────────────────────────────────┘
```

### 6대 개선 영역 (매 사이클 반복)

#### 1. 성능 최적화 (`/improve --perf`)

**백엔드:**
- DB 쿼리: N+1 쿼리 탐지, 인덱스 활용도, 커넥션 풀 사용량
- Redis 캐시: 히트율 측정, TTL 최적화, 메모리 사용량
- API 응답: 엔드포인트별 p50/p95 응답시간 기록
- LLM 호출: 토큰 사용량, 캐시 히트율, 모델별 비용 추적
- Temporal: Activity 실행 시간, heartbeat 간격, 재시도 빈도

**프론트엔드:**
- 번들 사이즈: chunk별 크기 추적 (목표: 초기 <300KB)
- 렌더링 성능: 불필요한 re-render 탐지, React.memo/useMemo 적용
- 네트워크: API 호출 워터폴 분석, 캐싱 전략
- Core Web Vitals: LCP <2.5s, FID <100ms, CLS <0.1

**측정 명령:**
```bash
# 백엔드 API 응답시간
docker compose exec backend python -c "from app.core.config import settings; print(settings)"
# 프론트엔드 번들 분석
cd frontend && npx vite-bundle-visualizer
```

#### 2. 보안 향상 (`/analyze --focus security`)

**체크리스트 (OWASP Top 10 기반):**
- [ ] A01 접근 제어: 모든 API 엔드포인트에 인증/인가 확인
- [ ] A02 암호화: JWT 시크릿 강도, 비밀번호 해싱, HTTPS 강제
- [ ] A03 주입: SQL injection, Command injection, YAML injection 방지
- [ ] A04 설계: Rate limiting, 입력 크기 제한, 파일 업로드 유효성
- [ ] A05 설정: 디버그 모드 비활성화, 기본 계정 제거, 헤더 보안
- [ ] A06 취약 컴포넌트: 의존성 CVE 스캔 (`pip audit`, `npm audit`)
- [ ] A07 인증: 세션 관리, 토큰 만료, OAuth PKCE
- [ ] A08 무결성: Docker 이미지 검증, 의존성 잠금
- [ ] A09 로깅: 보안 이벤트 로깅, 민감 데이터 마스킹
- [ ] A10 SSRF: 외부 URL 검증 (GitHub/LinkedIn API 호출)

**자동 스캔:**
```bash
docker compose exec backend pip audit --format json
cd frontend && npm audit --json
```

#### 3. 에이전트 아웃풋 품질 향상

**코드 분석 파이프라인 (`code_analyzer.py` + `code_analysis.py`):**
- AST 분석: Python `ast`, JS/TS `tree-sitter` — 의미있는 메트릭 추출 확인
- 기여도 분석: `PyDriller` — 커밋 빈도, 코드 변경량, 핫스팟 파일
- 기술 스택: `requirements.txt`, `package.json`, `Dockerfile` 등에서 정확한 추출
- 코드 품질: 복잡도 (cyclomatic), 테스트 커버리지 유무, 문서화 수준

**레포 분석 데이터 품질 검증:**
- [ ] tech_stack이 실제 사용 기술을 반영하는지
- [ ] contributions가 의미있는 기여 패턴을 보여주는지
- [ ] complexity_metrics가 코드 복잡도를 정확히 측정하는지
- [ ] 분석 실패 시 fallback이 유의미한 데이터를 제공하는지

**스킬 매칭 검증:**
- [ ] JD 요구사항 ↔ 후보자 스킬 매칭 정확도
- [ ] 매칭 confidence 값의 현실성
- [ ] evidence 출처의 추적 가능성

#### 4. UI/UX 프론트엔드 향상 + Playwright 테스트

**UI/UX 점검:**
- 디자인 일관성: 색상, 타이포그래피, 간격, 버튼 스타일 통일
- 반응형: 모바일(375px), 태블릿(768px), 데스크탑(1280px) 검증
- 접근성: WCAG 2.1 AA — 키보드 네비게이션, 스크린 리더, 색상 대비
- 로딩 상태: 스켈레톤 UI, 에러 바운더리, 빈 상태 처리
- i18n: 모든 사용자 대면 텍스트 번역 키 사용

**Playwright 자동 테스트 플로우:**
```
1. OAuth 우회 로그인 → 토큰 직접 주입
2. Job 목록 페이지 → Job 존재 확인
3. Result 페이지 → 4탭 순회:
   - Intel Brief: 후보자 정보 렌더링
   - Deep Analysis: 레이더 차트 + 스킬 매칭
   - Live Interview: 질문 카드 + 카테고리 배분
   - Decision: 점수 + 추천 + 위험 평가
4. 콘솔 에러 수집 → 0개 확인
5. 스크린샷 캡처 → 이전 버전과 비교
```

#### 5. 아키텍처 최적화

**디자인 패턴 적용:**
- Strategy Pattern: LLM 모델 선택 (현재 if/else → 전략 패턴)
- Factory Pattern: Activity 생성 (보일러플레이트 표준화)
- Observer Pattern: 워크플로우 상태 변경 알림
- Repository Pattern: 데이터 접근 계층 분리

**하드코딩 제거:**
- 매직 넘버 → 상수 파일 (`constants.py`) 또는 환경변수
- 한국어 문자열 → `i18n_labels.py` `_t()` 함수
- URL/경로 → 설정 파일 (`config.py`)
- 모델명/온도 → `llm_config.py` 단일 소스

**코드 구조:**
- 300줄 초과 파일 분리 (SRP 적용)
- 공통 로직 추출 → 유틸리티 모듈
- 타입 힌트 100% 적용 (Python 함수 시그니처)
- docstring 표준화 (Google style)

#### 6. 선택적 캐시 무효화 전략

**목표**: 문제되는 에이전트 로직만 캐시 초기화, 나머지는 기존 캐시 유지 → 토큰 절약

**메커니즘:**
```python
# 캐시 키 구조: {activity_name}:{input_hash}
# 예: "generate_intel_brief:a1b2c3d4"

# 특정 Activity만 캐시 무효화
async def invalidate_activity_cache(activity_name: str, job_id: str):
    pattern = f"llm_cache:{activity_name}:*"
    keys = await redis.keys(pattern)
    await redis.delete(*keys)

# 전체 Job의 특정 Phase만 재실행
async def rerun_from_phase(job_id: str, phase: int):
    # phase 이전 결과는 캐시 유지
    # phase 이후만 캐시 삭제 + 재실행
```

**테스트 시 캐시 전략:**
- 동일 입력값 → 기존 캐시 재사용 (토큰 0)
- 로직 변경된 Activity → 해당 Activity + 하위 의존 Activity만 캐시 삭제
- 프롬프트 변경 → Langfuse 프롬프트 버전 올리면 자동으로 새 캐시 생성

### Git 워크플로우 (매 개선건마다)

```
1. gh issue create --title "개선: [영역] [구체적 설명]"
2. git checkout -b improve/[영역]-[설명]
3. 코드 수정 + 테스트
4. git commit -m "improve: [설명] Closes #N"
5. gh pr create + gh pr merge --merge
6. git checkout main && git pull
```

### 개선 사이클 보고서 형식

매 사이클 완료 시 다음 형식으로 보고:

```markdown
## 개선 사이클 #N 보고서

### 측정 결과
| 영역 | 이전 | 이후 | 변화 |
|------|------|------|------|

### 수정 내역
| Issue | PR | 영역 | 설명 |
|-------|-----|------|------|

### 다음 사이클 목표
- [ ] ...
```
