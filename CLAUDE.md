# Vantict Sniper v4.0 - Project Intelligence

> **비개발자 출신 CEO/인사담당자가 개발자·CTO를 채용할 때, 코드 기반 근거로 실력을 판단하고 면접을 진행할 수 있도록 돕는 AI 면접 스크립트 생성기**
>
> 이 파일은 Claude Code가 프롬프트를 받으면 **자동으로** 최적의 MCP 서버와 스킬을 선택하도록 하는 마스터 라우팅 시스템입니다.

---

## Product Mission (제품 핵심 미션)

### 타겟 사용자
- **비개발자 출신 CEO**: 개발팀 빌딩을 위해 CTO/VP급 채용이 필요하지만 기술 평가 역량이 없음
- **HR 담당자/리크루터**: 개발자 이력서를 받아도 실력을 판단할 기준이 없음
- **스타트업 대표**: 초기 개발자 채용에서 잘못된 선택을 방지하고 싶음

### 핵심 가치
```
"개발을 모르는 사람도, 코드 분석 근거를 바탕으로 개발자 실력을 판단하고
면접에서 무엇을 물어보고, 어떤 대답이 좋은 대답인지 알 수 있게 해준다"
```

### 우리가 해결하는 문제

| 문제 | 현재 상태 | 목표 |
|------|----------|------|
| 점수 기준 부재 | 레이더 차트 점수가 임의 배점, 근거 불명확 | 코드 메트릭 기반 정량 공식으로 산출 |
| 실력 분류 근거 없음 | "Junior/Senior" 분류가 주관적 | 커밋 패턴, 코드 복잡도, 기여도 등 데이터 기반 분류 |
| 질문이 범용적 | "경험을 설명해주세요" 같은 일반 질문 | 후보자 코드/프로젝트에서 추출한 구체적 질문 |
| 답변 가이드 부재 | 면접관이 좋은 답변을 모름 | 기대 답변 예시 + 평가 기준을 비개발자 언어로 제공 |
| 경력 정보 미활용 | LinkedIn 데이터를 충분히 정리하지 않음 | 경력, 추천서, 학력, 승진 이력을 구조화하여 표시 |
| 출력이 개발자 전문 용어 | 기술 용어 그대로 노출 | 비개발자도 이해할 수 있는 비유/설명 병기 |

### 제품 설계 원칙

1. **모든 점수에 근거가 있어야 한다** — "70점"이면 왜 70점인지 코드/경력 데이터 출처가 보여야 함
2. **질문은 후보자의 실제 코드에서 나와야 한다** — GitHub 레포 분석에서 나온 구체적 기술 질문
3. **답변 가이드는 비개발자도 이해해야 한다** — "이런 대답이 좋고, 이런 대답은 주의" 형식
4. **경력 정보를 한눈에 보여줘야 한다** — LinkedIn 경력 타임라인, 추천서 요약, 학력 정리
5. **전문 용어에는 항상 쉬운 설명이 붙어야 한다** — 비개발자 친화적 UI/UX
6. **출력 결과는 항상 일관되어야 한다** — 동일 입력에 대해 동일한 구조/기준의 결과 산출, 매 실행마다 결과가 달라지면 안 됨
7. **모든 판단에는 신뢰도가 표시되어야 한다** — 점수, 매칭, 추천에 confidence level(높음/중간/낮음) + 근거 데이터량 명시
8. **기준은 학술적/산업 표준에 근거해야 한다** — 점수 공식, 역량 분류 기준은 논문/기술 문서/업계 표준 참조 후 설계

---

## 출력 일관성 & 신뢰도 보장 체계 (Output Consistency & Reliability)

> **목표**: 동일한 후보자 데이터를 넣으면 항상 같은 기준으로 평가하고, 결과에 신뢰도와 근거를 명시한다.

### 일관성 보장 원칙

| 원칙 | 구현 방법 |
|------|----------|
| **점수 공식 고정** | LLM 주관이 아닌, 코드 메트릭 → 점수 변환 공식 (deterministic) 사용 |
| **분류 기준표** | Junior/Mid/Senior/Lead 분류를 경력 연수 + 코드 메트릭 + 기여 패턴 조합으로 정의 |
| **프롬프트 버전 관리** | Langfuse에서 프롬프트 버전을 고정, 변경 시 A/B 테스트 후 배포 |
| **출력 스키마 강제** | LLM 출력에 Pydantic 스키마 검증 → 누락 필드/형식 오류 시 재생성 |
| **캐시 활용** | 동일 입력은 Redis 캐시에서 동일 결과 반환 (비결정적 LLM 호출 최소화) |

### 신뢰도 표시 체계

```
모든 주요 판단에 다음 3가지를 표시:

1. 신뢰도 등급: 🟢 높음 / 🟡 중간 / 🔴 낮음
2. 근거 데이터: "GitHub 12개 레포 분석 + LinkedIn 경력 8년 + 이력서 3장"
3. 데이터 완전성: "분석 가능 데이터 85% 확보" (LinkedIn 없으면 → 60%, GitHub 없으면 → 40%)
```

**신뢰도 산출 기준:**
- 🟢 높음 (≥80%): GitHub + LinkedIn + 이력서/포트폴리오 모두 확보, 코드 분석 성공
- 🟡 중간 (50-79%): 2개 소스 확보, 일부 분석 실패 또는 데이터 부족
- 🔴 낮음 (<50%): 1개 소스만 확보, 대부분 LLM 추론에 의존

### 기준 수립을 위한 리서치 프로세스

개선 사이클에서 점수 공식 / 역량 분류 기준을 새로 만들거나 수정할 때:

1. **학술 논문 검색**: Brave Search / WebSearch로 관련 연구 조사
   - 예: "software engineer skill assessment metrics", "code quality metrics research"
   - ACM, IEEE, arXiv 등 학술 소스 우선
2. **산업 표준 참조**: 기존 개발자 평가 프레임워크 조사
   - 예: Google Engineering Levels, SFIA Framework, Dreyfus Model
   - Context7으로 관련 라이브러리/도구 공식 문서 참조
3. **기준 문서화**: 채택한 기준의 출처와 근거를 `docs/scoring/` 에 기록
4. **A/B 검증**: 새 기준 적용 전후 결과를 테스트 Job으로 비교

---

## 비개발자 UX 가이드라인 (Non-Developer UX Guidelines)

> 모든 UI 요소와 출력물은 비개발자 사용자가 이해하고 활용할 수 있어야 한다.

### 용어 처리 규칙

| 규칙 | 예시 |
|------|------|
| 기술 용어 처음 등장 시 쉬운 설명 병기 | "Docker (프로그램을 상자에 넣어 어디서든 동일하게 실행하는 기술)" |
| 약어 사용 금지 (첫 등장 시) | "CI/CD" → "CI/CD (코드를 자동으로 테스트하고 배포하는 시스템)" |
| 점수 옆에 한줄 해석 | "코드 품질: 78점 — 업계 평균 이상, 읽기 쉽고 정돈된 코드를 작성함" |
| 비유/일상 언어 사용 | "마이크로서비스" → "기능별로 독립된 작은 프로그램들이 협력하는 구조" |

### 답변 가이드 형식 (면접관용)

모든 질문 카드에 아래 구조 포함:

```
✅ 좋은 답변 신호:
  - 구체적 숫자/사례를 들어 설명함 (예: "응답시간을 3초에서 0.5초로 단축")
  - 팀 내 역할과 본인 기여를 명확히 구분함
  - 실패 경험과 그로부터 배운 점을 솔직히 공유함

⚠️ 주의 신호:
  - "많이 개선했습니다" 같은 추상적 표현만 사용
  - 질문을 회피하거나 다른 주제로 전환
  - 모든 성과를 혼자 한 것처럼 표현

💡 후속 질문 팁:
  - "그 개선에서 본인이 구체적으로 어떤 부분을 담당했나요?"
  - "그 결정에 반대 의견은 없었나요? 어떻게 해결했나요?"
```

### 결과 페이지 정보 계층

```
[1단계] 한눈에 결론: 채용 추천 여부 + 전체 매치율 + 신뢰도
  ↓
[2단계] 핵심 근거: 레이더 차트(5축) + 각 축 한줄 해석
  ↓
[3단계] 상세 분석: 스킬별 매칭 근거 + 코드 사례 + 경력 타임라인
  ↓
[4단계] 면접 도구: 질문 카드 + 답변 가이드 + 꼬리질문
```

### Playwright 비개발자 UX 검증 체크리스트

매 개선 사이클마다 확인:
- [ ] 모든 기술 용어에 `glossary_term` 설명이 표시되는지
- [ ] 점수/등급 옆에 "근거 보기" 또는 한줄 해석이 있는지
- [ ] 답변 가이드(좋은 답변/주의 신호)가 모든 질문 카드에 있는지
- [ ] 경력 타임라인이 Intel Brief 탭에 구조화되어 있는지
- [ ] 신뢰도 등급(🟢🟡🔴)이 주요 판단 항목에 표시되는지

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

playwright_e2e:
  keywords: [e2e, playwright, 브라우저 테스트, 프론트 테스트, UI 테스트, 화면 테스트, visual regression, 스크린샷 비교]
  file_patterns: ["**/e2e/**", "playwright.config.*"]
  activate:
    skill: /test
    mcp: [playwright, context7]
    persona: qa
    context_files:
      - frontend/e2e/result-page.spec.ts
      - frontend/playwright.config.ts

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

agent_quality:
  keywords: [quality, 품질, 검증, evaluation, eval, 평가, 중복, duplicate, hallucination, 환각, evidence, 근거, scoring, 점수, langfuse eval, phoenix eval, A/B test, 실험, experiment, golden dataset, 골든 데이터셋, 프롬프트 비교, prompt comparison]
  file_patterns: ["**/quality_review.py", "**/evaluation.py", "**/phoenix_eval.py", "**/observability_activities.py"]
  activate:
    mcp: [context7, sequential]
    persona: backend
    context_files:
      - backend/app/workflows/activities/quality_review.py
      - backend/app/core/evaluation.py
      - backend/app/prompts/quality_review.yaml
      - backend/app/workflows/activities/observability_activities.py

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
  keywords: [test, 테스트, E2E, pytest, coverage, 커버리지, vitest]
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

사용자: "ResultPage에서 콘솔 에러 나는데 Playwright로 테스트해줘"
→ 매칭: playwright_e2e + react_frontend + debugging
→ MCP: playwright, context7, sequential
→ Skill: /test (Tier 1 우선)
→ Context: result-page.spec.ts, playwright.config.ts
→ Persona: qa

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
| Frontend | Vite + React 19 + Tailwind CSS 4, react-i18next |
| Backend | FastAPI, Python 3.11 |
| Orchestration | Temporal.io |
| Database | PostgreSQL 16 + pgvector |
| Cache | Redis 7 |
| Storage | LocalStack S3 → AWS S3 |
| LLM | Kimi K2.5 (moonshot-v1-auto) — Langfuse-first, fallback: GPT-4o / Claude |
| Container | Docker Compose |
| Git Analysis | PyGithub (API), PyDriller (로컬 분석), ast (Python), tree-sitter (JS/TS) |
| LinkedIn | Proxycurl API (프로필 수집) |
| Testing | Playwright (E2E) + pytest (Backend, 474 passed) |

### Architecture Documents
| Document | Path |
|----------|------|
| Master | `docs/architecture/ARCHITECTURE.md` |
| Overview | `docs/architecture/01-overview.md` |
| Data Models | `docs/architecture/02-data-models.md` |
| Workflow | `docs/architecture/03-workflow.md` |
| Infrastructure | `docs/architecture/04-infrastructure.md` |
| API Spec | `docs/architecture/05-api-spec.md` |
| LLM Activity Flow | `docs/architecture/06-llm-activity-flow.md` |
| Prompt Guide | `docs/architecture/07-prompt-guide.md` |
| Human Process | `docs/humanprocess/` |

### Available MCP Servers
| Server | Purpose | Auto-Route Trigger | Status |
|--------|---------|-------------------|--------|
| `db` | PostgreSQL + pgvector 직접 쿼리 | DB/SQL/스키마 키워드 | ⚠️ DB 연결 문자열 필요 |
| `redis` | Redis 캐시 관리 | cache/캐시/Redis 키워드 | ❌ 미설치 |
| `github` | GitHub API 통합 (플러그인) | GitHub/레포/코드분석 키워드 | ⚠️ 재인증 필요 |
| `docker` | Docker 컨테이너 관리 | Docker/컨테이너/인프라 키워드 | ✅ |
| `context7` | 라이브러리 공식 문서 | 프레임워크/SDK 질문 | ✅ |
| `sequential` | 복잡한 분석/추론 | 디버깅/설계/분석 | ✅ |
| `magic` | UI 컴포넌트 생성 | 프론트엔드/컴포넌트 | ✅ |
| `brave-search` | 웹 검색 | 조사/리서치 | ✅ |
| `playwright` | 브라우저 테스트/자동화 | E2E/테스트 | ✅ |
| `puppeteer` | 브라우저 스크린샷/크롤링 | 스크린샷/크롤링/렌더링 | ✅ |
| `claude-mem` | 대화 메모리/검색 (플러그인) | 이전 대화 참조/기억 | ✅ |

### Project-Specific Skills (`.claude/skills/`)
| Skill | Purpose | Status |
|-------|---------|--------|
| `/temporal-dev` | Temporal 워크플로우/Activity 개발 | ✅ |
| `/vantict-activity` | Activity 보일러플레이트 생성 | ✅ |
| `/implement` | API/컴포넌트/서비스 구현 (`--type api\|component\|service`) | ✅ |
| `/test` | 테스트 작성 및 실행 (pytest, Playwright, Vitest) | ✅ |
| `/design` | 시스템 아키텍처 설계 | ✅ |
| `/document` | 문서 작성/업데이트 | ✅ |
| `/troubleshoot` | 버그 수정/디버깅 | ✅ |
| `/research` | 조사/탐색 | ✅ |
| `/analyze` | 보안/코드 품질/의존성 분석 | ✅ |
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
frontend/src/components/tabs/      → 탭 컴포넌트 (IntelBrief, DeepAnalysis 등)
frontend/src/components/charts/    → 차트 컴포넌트 (RadarChart 등)
frontend/src/pages/                → React 페이지
frontend/src/hooks/                → Custom React Hooks
frontend/src/lib/                  → API 클라이언트, 유틸리티
frontend/src/types/                → TypeScript 타입 정의
frontend/public/locales/           → i18n 번역 파일
frontend/e2e/                      → Playwright E2E 테스트
```

### Naming Conventions
- Activity 함수: `snake_case` (예: `analyze_documents`, `craft_question`)
- Workflow 클래스: `PascalCase` + `Workflow` 접미사 (예: `InterviewGenerationWorkflow`)
- API 라우터: `snake_case` (예: `create_job`, `get_job_status`)
- 프론트엔드 컴포넌트: `PascalCase` (예: `InterviewForm`, `QuestionCard`)
- E2E 테스트: `kebab-case.spec.ts` (예: `result-page.spec.ts`, `create-job.spec.ts`)
- Hooks: `use` 접두사 + `PascalCase` (예: `useJob`, `useAuth`)

### File Size & Separation Rules
- 단일 파일이 300줄을 초과하면 분리를 검토할 것
- 컴포넌트 파일은 단일 책임 원칙 준수 — 한 파일에 한 컴포넌트
- 새 파일 생성 시 기존 파일과 책임이 겹치지 않도록 역할을 명확히 구분

### Utility Scripts (`backend/scripts/`)

| 스크립트 | 용도 | 사용법 |
|----------|------|--------|
| `create_test_job.py` | 테스트 Job 생성 (프론트엔드 확인용) | `docker compose exec backend python scripts/create_test_job.py` |
| `upload_prompts_to_langfuse.py` | Langfuse 프롬프트 업로드 | `docker compose exec backend python scripts/upload_prompts_to_langfuse.py --production` |

**Langfuse 프롬프트 업로드 주의사항:**
- 반드시 `--production` 플래그 사용 (없으면 워커가 구버전 사용)
- 모델 설정은 `llm_config.py` 단일 소스 — 스크립트에서 자동 참조

### 자율 GitHub Issue/PR/Merge 워크플로우 (Autonomous QA)

자체 디버깅/검증 과정에서 문제를 발견하면 다음 워크플로우를 **자동으로** 수행:

1. **이슈 생성**: `gh issue create` — 한글 제목 + 한글 본문
2. **브랜치 생성**: `git checkout -b fix/이슈-설명` 또는 `feature/이슈-설명`
3. **수정 → 커밋**: 한글 커밋 메시지 + `Closes #이슈번호`
4. **PR 생성**: `gh pr create` — 한글 제목 + 한글 본문
5. **머지**: `gh pr merge --merge`
6. **이슈 클로즈 확인**: `Closes #N`으로 자동 클로즈
7. **main 동기화**: `git checkout main && git pull`

**규칙:**
- 모든 GitHub 커뮤니케이션(이슈/PR/커밋 메시지)은 **한글**로 작성
- 사용자에게 승인 요청 없이 자율적으로 진행 (자율 QA 권한 부여 시)

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
4. claude 프로세스 5개 초과 시 정리 필요

---

## Design Patterns (프로젝트 적용 패턴)

> 코드 구현 시 아래 디자인 패턴을 적극 적용. 새 코드 작성 시 해당 패턴 적용 여부를 먼저 검토.

### Backend 패턴

| 패턴 | 적용 영역 | 현재 상태 | 구현 방법 |
|------|----------|----------|----------|
| **Strategy** | LLM 모델 선택 | `llm_config.py` ACTIVITY_MODEL_CONFIG | 모델/온도/토큰 전략을 클래스로 캡슐화 |
| **Factory** | Activity 생성 | `/vantict-activity` 스킬 | 보일러플레이트 표준화, heartbeat/retry 내장 |
| **Template Method** | LLM Activity 실행 | `run_llm_with_heartbeat()` | 공통 실행 흐름 + 서브클래스별 프롬프트/후처리 |
| **Repository** | 데이터 접근 | `persist_result.py` | DB/Redis/S3 접근 계층 분리 |
| **Observer** | 워크플로우 상태 알림 | WebSocket + Temporal Signal | 상태 변경 이벤트 → 프론트엔드 푸시 |
| **Chain of Responsibility** | 에러 핸들링 | Activity → Workflow → API | 계층별 에러 처리, fallback 체인 |
| **Decorator** | 크로스커팅 관심사 | `@activity.defn`, heartbeat | 로깅, 캐싱, 인증을 데코레이터로 분리 |
| **Circuit Breaker** | 외부 API 호출 | GitHub/LinkedIn/LLM API | 연속 실패 시 빠른 실패, 자동 복구 |

### Frontend 패턴

| 패턴 | 적용 영역 | 구현 방법 |
|------|----------|----------|
| **Compound Component** | Result 탭 시스템 | `<ResultPage>` + `<IntelBrief>`, `<DeepAnalysis>` 등 |
| **Custom Hook** | 상태/로직 추출 | `useJob`, `useAuth`, `useAnalysisLogs`, `useWebSocket` |
| **Error Boundary** | 에러 격리 | 탭별 `<ErrorBoundary>` 래핑 — 한 탭 에러가 전체 앱 크래시 방지 |
| **Render Props / HOC** | 조건부 렌더링 | 로딩/에러/빈 상태별 분기 렌더링 |
| **Flyweight** | 테스트 데이터 공유 | E2E 테스트에서 mock 데이터 오브젝트 풀 재사용 |
| **Lazy Loading** | 코드 분할 | `React.lazy()` + `Suspense` (8개 페이지 모두 적용) |
| **Adapter** | API 응답 변환 | API 응답 → 컴포넌트 props 변환 레이어 |

### AI/LLM 파이프라인 패턴

| 패턴 | 적용 영역 | 구현 방법 |
|------|----------|----------|
| **Tiered Model Strategy** | 모델 비용 최적화 | Tier 1 (빠른 분류) → Tier 2 (Kimi K2.5) → Tier 3 (GPT-4o/Claude) |
| **Guardrails** | 입출력 안전성 | 이력서 입력 검증 + 생성 질문 편향 필터링 |
| **Evals (LLM-as-Judge)** | 질문 품질 평가 | `quality_review.py`에서 자동 품질 검증 |
| **Context Management** | 긴 이력서 처리 | 문서 청킹 + 핵심 정보 추출 후 압축 |
| **Selective Cache Invalidation** | 토큰 절약 | Activity 단위 캐시 키, 변경분만 무효화 |

---

## Playwright E2E 테스트 전략

> 프론트엔드 오류를 체계적으로 잡기 위한 Playwright 기반 테스트 프레임워크

### 테스트 피라미드

```
         /  E2E (Playwright)  \          ← 3-5 Critical User Flows
        /  Integration (Vitest+RTL) \    ← 컴포넌트 조합 테스트 (추가 예정)
       /  Unit (Vitest)              \   ← 순수 로직 함수 (추가 예정)
      /  Static (TypeScript + ESLint)  \ ← 컴파일 타임 검증
```

### E2E 테스트 시퀀스 (Playwright)

아래 5개 시퀀스를 매 개선 사이클마다 실행:

#### Sequence 1: 인증 플로우
```
1. LoginPage 렌더링 확인
2. OAuth 버튼 존재 확인 (Google)
3. 토큰 직접 주입 (localStorage) → 인증 우회
4. /jobs 리다이렉트 확인
5. 비인증 상태 → /login 리다이렉트 확인
```

#### Sequence 2: Job 생성 플로우
```
1. CreateJobPage 렌더링 확인
2. 필수 필드 입력: JD, experience_level, output_language
3. 선택 필드: LinkedIn URL, GitHub URL, portfolio PDF
4. 질문 수 슬라이더 (5-25) 조작
5. 제출 → API 호출 확인 → JobStatusPage 리다이렉트
6. 폼 유효성 검사 (빈 필드 제출 시 에러)
```

#### Sequence 3: Result 페이지 4탭 순회 (핵심)
```
1. ResultPage 로딩 → API mock 주입 (/api/v1/results/{id})
2. Intel Brief 탭:
   - 후보자 이름, 직함, 요약 렌더링 확인
   - Competency 매칭 카드 존재 확인
3. Deep Analysis 탭:
   - RadarChart SVG 렌더링 확인
   - 스킬 매칭 테이블 행 수 확인
   - Engineering DNA 섹션 존재 확인
4. Live Interview 탭:
   - 질문 카드 렌더링 (최소 5개)
   - 카테고리별 배분 확인
   - 질문 클릭 → 상세 패널 열림
   - follow-up 질문 존재 확인
5. Decision 탭:
   - 종합 점수 렌더링
   - 추천/비추천 배지 확인
   - 위험 평가 항목 존재
6. 전 탭 콘솔 에러 0개 확인
7. 스크린샷 캡처 → 이전 버전과 비교
```

#### Sequence 4: 에러 핸들링 & 엣지 케이스
```
1. 404 페이지 렌더링 확인
2. API 500 에러 시 ErrorBoundary 동작 확인
3. 네트워크 오프라인 시 graceful degradation
4. 빈 결과 데이터 시 빈 상태 UI 확인
5. 긴 텍스트 오버플로우 처리 확인
6. 모바일 뷰포트 (375px) 레이아웃 깨짐 확인
```

#### Sequence 5: 접근성 & 성능
```
1. 키보드 네비게이션 (Tab, Enter, Escape)
2. ARIA 라벨 존재 확인
3. 색상 대비 비율 (WCAG 2.1 AA)
4. LCP < 2.5s, CLS < 0.1 측정
5. 번들 사이즈 확인 (초기 로딩 < 300KB)
```

### E2E 테스트 실행 명령

```bash
# 전체 E2E 테스트
cd frontend && npx playwright test

# 특정 시퀀스만
npx playwright test result-page.spec.ts
npx playwright test create-job.spec.ts

# 시각적 확인 (headed 모드)
npx playwright test --headed

# 디버그 모드
npx playwright test --debug

# HTML 리포트
npx playwright show-report
```

### Flyweight 패턴 적용 (테스트 데이터)

E2E 테스트에서 mock 데이터를 Flyweight 패턴으로 관리:

```typescript
// e2e/fixtures/mock-data.ts — 공유 테스트 데이터 풀
export const SHARED_CANDIDATE = {
  name: "Alex Kim",
  title: "Senior AI Engineer",
  experience_years: 8,
  // ... 모든 테스트에서 공유
};

export const SHARED_QUESTIONS = [
  { id: 1, category: "technical_depth", text: "..." },
  // ... 20개 질문 풀
];

// 테스트별로 필요한 부분만 확장 (intrinsic + extrinsic 분리)
export function createMockResult(overrides?: Partial<ResultData>): ResultData {
  return { ...SHARED_CANDIDATE, ...SHARED_QUESTIONS, ...overrides };
}
```

**장점:**
- 테스트 파일 간 데이터 중복 제거
- mock 데이터 변경 시 단일 소스에서 수정
- 테스트 실행 메모리 절약

---

## 🔄 Continuous Improvement Engine (지속적 개선 엔진)

> **핵심 원칙**: 매 사이클마다 측정 → 분석 → 개선 → 검증을 반복하여 프로젝트 품질을 지속적으로 향상시킨다.

### 최근 변경

| PR | 내용 |
|----|------|
| #120 | ResultPage useCallback Hook 호출 순서 수정 |
| #118 | nginx X-Forwarded-Proto Cloudflare 보존 |
| #117 | OAuth redirect_uri 동적 감지 |
| #116 | 견고성 사이클 3: type guards + SSRF 방어 |
| #115 | OAuth localhost 리다이렉트 수정 |
| #113 | 테스트 mock 대상 Langfuse-first 동기화 (474 passed) |

### 개선 사이클 구조

```
 MEASURE → ANALYZE → IMPROVE → VERIFY → REPORT
   (측정)    (분석)    (개선)    (검증)    (보고)
     ↑                                      │
     └──────────────────────────────────────┘
```

### 개선 영역 (미션 우선순위순)

> **원칙**: 제품 미션(비개발자가 개발자를 판단할 수 있게 돕기)에 직결되는 문제부터 해결한다.

---

#### 🔴 P0: 제품 미션 핵심 (최우선)

##### 1. 점수 근거 체계 확립 (Evidence-Based Scoring)

**현재 문제**: 레이더 차트 5축 점수, 전체 매치율(%), 스킬별 점수가 **LLM이 임의로 부여**하여 근거 불명확

**목표**: 모든 점수에 코드 메트릭 / 경력 데이터 기반 **정량 공식** 적용

**구체적 개선 항목:**
- [ ] **레이더 차트 5축 공식 정의**: 각 축(technical_depth, problem_solving, code_quality, system_design, leadership)에 대해 입력 메트릭 → 점수 변환 공식 수립
  - 예: `code_quality = f(avg_complexity, test_coverage, docstring_ratio, lint_score)`
  - 예: `technical_depth = f(language_count, framework_diversity, commit_depth, PR_complexity)`
- [ ] **전체 매치율(%) 공식**: `match_score = Σ(axis_score × weight) / Σ(weights)` — 가중치는 JD 요구사항에서 자동 산출
- [ ] **스킬별 매칭 근거**: 각 스킬에 `evidence_source` 필수 (GitHub 레포명, 파일 경로, 커밋 수, 사용 빈도)
- [ ] **점수 출처 UI 표시**: 프론트엔드에서 점수 클릭 시 "이 점수의 근거" 팝업/툴팁 표시

**관련 파일:**
- `analysis_generation.py` — 레이더 차트 점수 생성
- `decision_generation.py` — 최종 추천/점수 생성
- `intel_generation.py` — 스킬 매칭 점수
- `DeepAnalysisTab.tsx` — 레이더 차트 UI
- `DecisionTab.tsx` — 최종 점수 UI

##### 2. 코드 기반 구체적 질문 생성

**현재 문제**: "경험을 설명해주세요" 같은 범용 질문이 다수, 후보자 GitHub 코드에서 나온 구체적 질문 비율 낮음

**목표**: 질문의 ≥60%가 후보자의 실제 코드/프로젝트에서 추출된 구체적 질문

**구체적 개선 항목:**
- [ ] **코드 기반 질문 비율 측정**: 현재 `craft_question` 출력에서 `evidence_source`가 GitHub인 질문 비율 추적
- [ ] **코드 스니펫 첨부 질문**: 후보자의 실제 코드 조각을 보여주며 "이 코드에서 왜 이런 패턴을 선택했나요?" 형태
- [ ] **커밋 히스토리 기반 질문**: PyDriller 분석 결과(핫스팟 파일, 리팩토링 패턴)에서 질문 도출
- [ ] **범용 질문 비율 제한**: `quality_review`에서 evidence_score < 40인 범용 질문을 20% 이하로 강제

**관련 파일:**
- `question_generation.py`, `question_generation_utils.py` — 질문 생성
- `question_enhancement.py` — 질문 강화
- `code_analysis.py` — GitHub 코드 분석
- `question_generation.yaml` — 질문 생성 프롬프트

##### 3. 비개발자 친화 답변 가이드

**현재 문제**: 면접관(비개발자)이 좋은 답변과 나쁜 답변을 구분할 기준이 없음

**목표**: 모든 질문에 비개발자도 이해하는 "기대 답변 예시 + 평가 기준" 제공

**구체적 개선 항목:**
- [ ] **3단계 답변 가이드**: 각 질문에 "우수한 답변 특징 / 보통 답변 특징 / 주의 신호" 를 비개발자 언어로 제공
  - 예: 우수 — "구체적 숫자(성능 50% 향상)나 팀 협업 사례를 언급"
  - 예: 주의 — "추상적 표현만 사용('많이 개선했습니다')하거나 질문을 회피"
- [ ] **전문 용어 자동 번역**: 질문/답변의 모든 기술 용어에 `glossary_term` + `plain_explanation` 쌍 추가
  - 예: "Docker 컨테이너" → "프로그램을 독립된 상자에 넣어 어디서든 동일하게 실행하는 기술"
- [ ] **면접관 액션 가이드**: 각 질문에 "이 질문 후 이런 반응이면 이렇게 후속 질문하세요" 안내
- [ ] **비개발자 이해도 검증**: Playwright 테스트에서 용어 설명 누락 여부 자동 체크

**관련 파일:**
- `craft_evaluation_scenarios()` — 평가 시나리오 생성
- `enhance_terminology()` — 용어 설명 강화
- `design_follow_ups()` — 꼬리질문 설계
- `LiveInterviewTab.tsx` — 질문 카드 UI

##### 4. LinkedIn 경력 정보 구조화

**현재 문제**: LinkedIn 데이터(경력, 추천서, 학력)를 충분히 정리/활용하지 않음

**목표**: 비개발자가 한눈에 이해하는 경력 타임라인 + 추천서 요약 + 학력 정리 제공

**구체적 개선 항목:**
- [ ] **경력 타임라인**: 회사명, 직급, 기간, 주요 성과를 시각적 타임라인으로 정리
- [ ] **추천서 요약**: LinkedIn 추천서에서 핵심 평가 키워드 추출 + 요약 (예: "3명이 '리더십' 언급, 2명이 '기술 깊이' 언급")
- [ ] **학력/자격증 정리**: 관련 학위, 부트캠프, 자격증을 구조화하여 표시
- [ ] **승진 패턴 분석**: 경력 이동에서 승진/이직 패턴을 비개발자 언어로 해석 (예: "3년마다 직급 상승 → 성장 속도 빠름")
- [ ] **Intel Brief 탭 강화**: 위 정보를 IntelBriefTab에 구조화 섹션으로 추가

**관련 파일:**
- `linkedin_service.py` — LinkedIn 데이터 수집
- `intel_generation.py` — Intel Brief 생성
- `finalization.py` — 최종 데이터 조합
- `IntelBriefTab.tsx` — Intel Brief UI

---

#### 🟡 P1: 아웃풋 품질 & UX

##### 5. 에이전트 아웃풋 품질 향상

- AST 분석: Python `ast`, JS/TS `tree-sitter` — 메트릭 추출 정확도
- 기여도 분석: `PyDriller` — 커밋 빈도, 코드 변경량, 핫스팟 파일
- 스킬 매칭: JD ↔ 후보자 스킬 매칭 정확도, confidence 현실성
- 분석 실패 시 fallback 데이터 유의미성
- P0 항목(점수 근거, 코드 기반 질문, 답변 가이드)의 품질 검증

##### 6. UI/UX 프론트엔드 향상 + Playwright 테스트

**비개발자 UX 최우선 점검:**
- 전문 용어에 쉬운 설명이 병기되는지 (glossary 표시 확인)
- 점수/등급 옆에 "왜 이 점수인지" 근거가 보이는지
- 답변 가이드가 카드 형태로 쉽게 읽히는지

**기존 UI/UX 점검:**
- 디자인 일관성: 색상, 타이포그래피, 간격, 버튼 스타일 통일
- 반응형: 모바일(375px), 태블릿(768px), 데스크탑(1280px) 검증
- 접근성: WCAG 2.1 AA — 키보드 네비게이션, 스크린 리더, 색상 대비
- i18n: 모든 사용자 대면 텍스트 번역 키 사용

**Playwright 자동 검증:**
- 매 개선 사이클마다 E2E 시퀀스 전체 실행
- 콘솔 에러 0개 기준 통과
- 용어 설명 누락/점수 근거 누락 자동 탐지
- 모바일/데스크탑 뷰포트 모두 검증

##### 7. Playwright 기반 프론트엔드 에러 탐지

**자동화된 에러 탐지 파이프라인:**
```
1. Playwright 테스트 실행 → 2. 콘솔 에러 수집 → 3. 에러 분류 → 4. 이슈 생성 → 5. 수정 + 재테스트
```

| 에러 유형 | 탐지 방법 | 대응 패턴 |
|----------|----------|----------|
| Hook 순서 위반 | 콘솔 에러 + Playwright | 조건부 렌더링 전에 모든 Hook 호출 |
| undefined 프로퍼티 접근 | Playwright + TypeScript | optional chaining `?.` + nullish coalescing `??` |
| API 데이터 타입 불일치 | Playwright + type guard | 런타임 검증 또는 type guard 함수 |
| i18n 누락 | Playwright 텍스트 검증 | `t()` 함수 + 번역 키 자동 추출 |

---

#### 🟢 P2: 인프라 & 안정성

##### 8. 성능 최적화 (`/improve --perf`)

**백엔드:** DB 쿼리 N+1, Redis 캐시 히트율, API p50/p95 응답시간, LLM 토큰 비용
**프론트엔드:** 번들 <300KB, Core Web Vitals (LCP <2.5s, FID <100ms, CLS <0.1)

##### 9. 보안 향상 (`/analyze --focus security`)

OWASP Top 10 기반: 접근 제어, 암호화, 주입 방지, Rate limiting, CVE 스캔, SSRF 방어

##### 10. 아키텍처 최적화

- 디자인 패턴: Strategy (LLM 선택), Factory (Activity 생성), Template Method, Circuit Breaker
- 하드코딩 제거 → 상수/환경변수/i18n/`llm_config.py`
- 300줄 초과 파일 분리 (SRP), 타입 힌트 100%

##### 11. 선택적 캐시 무효화 전략

```python
# 특정 Activity만 캐시 무효화 (나머지 유지 → 토큰 절약)
async def invalidate_activity_cache(activity_name: str):
    pattern = f"llm_cache:{activity_name}:*"
    keys = await redis.keys(pattern)
    await redis.delete(*keys)
```

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

```markdown
## 개선 사이클 #N 보고서

### 측정 결과
| 영역 | 이전 | 이후 | 변화 |
|------|------|------|------|

### 에이전트 아웃풋 품질 지표
| Phase | 지표 | 값 | 목표 | 상태 |
|-------|------|-----|------|------|
| P2 | 프로필 추출 완전성 | ? | ≥90% | |
| P2 | JD 기술 스택 누락 | ? | ≤2개 | |
| P2 | 코드 분석 HYBRID 완수율 | ? | 100% | |
| P3 | 평균 Evidence Score | ?/100 | ≥70 | |
| P3 | 환각 탐지율 | ? | 0% | |
| P3 | 중복 질문 비율 | ? | 0% | |
| P3 | 카테고리 균형도 | ? | ≥3/cat | |
| P4 | Intel Brief 사실 오류 | ? | 0개 | |
| P4 | 교차 일관성 (4탭 모순) | ? | 0개 | |
| P4 | 추천 일관성 | ? | 100% | |

### 프롬프트 A/B 테스트 결과
| 프롬프트 | Version A | Version B | 승자 | 차이 |
|----------|-----------|-----------|------|------|

### Playwright 테스트 결과
| 시퀀스 | 통과 | 실패 | 콘솔 에러 |
|--------|------|------|----------|

### 수정 내역
| Issue | PR | 영역 | 설명 |
|-------|-----|------|------|

### 다음 사이클 목표
- [ ] ...
```

---

## 🔍 Agent Output Quality Verification Engine (에이전트 아웃풋 품질 검증 엔진)

> 전체 파이프라인(32개 Activity)의 LLM 생성 결과물을 자동으로 검증하고 지속적으로 개선하는 통합 품질 시스템

### 품질 검증 대상: 전체 파이프라인 아웃풋 매트릭스

```
Phase 0-1: INPUT & PLANNING
  enrich_input()          → URL 추출 정확도, LinkedIn/GitHub 유효성
  create_execution_plan() → 분석 대상 선정 정확도, 시간 추정 현실성

Phase 2: PARALLEL ANALYSIS (품질 영향도 HIGH)
  analyze_documents()     → 프로필 추출 완전성, 스킬 정확도
  analyze_jd()            → JD 요구사항 구조화 정확도, 누락 항목
  analyze_code()          → 코드 분석 깊이, 기술 스택 매칭, HYBRID 품질
  build_knowledge_graph() → KG 엔티티 정확도, 관계 타당성, 충돌 탐지

Phase 3: QUESTION GENERATION (품질 영향도 CRITICAL)
  select_topics()         → 토픽 균형, 후보자 특화도, 카테고리 배분
  craft_question()        → 질문 품질 8차원 (기존 quality_review)
  enhance_terminology()   → 용어 설명 정확성, 비전문가 이해도
  craft_evaluation_scenarios() → 평가 기준 구분도, 현실성
  design_follow_ups()     → 꼬리질문 깊이/연관성, 난이도 분기
  generate_decision_guide() → 채용 가이드 근거 타당성

Phase 4: RESULT GENERATION (품질 영향도 CRITICAL)
  generate_intel_brief()      → 요약 정확성, 역량 매칭 근거
  generate_deep_analysis()    → 레이더 차트 점수 근거, 스킬 매칭 정밀도
  generate_decision_support() → 추천 일관성, 위험 평가 근거
  finalize_output()           → 전체 조합 일관성, 데이터 무결성
```

### Phase별 품질 차원 정의

#### Phase 2: 분석 품질 (Analysis Quality)

| Activity | 품질 차원 | 측정 방법 | 합격 기준 |
|----------|----------|----------|----------|
| `analyze_documents` | 프로필 완전성 | 필수 필드 채워짐 비율 | ≥90% 필드 추출 |
| `analyze_documents` | 스킬 정확도 | 추출 스킬 ↔ 실제 이력서 대조 | 환각 스킬 0개 |
| `analyze_jd` | 요구사항 구조화 | 필수/우대 분류 정확도 | ≥85% 정확도 |
| `analyze_jd` | 기술 스택 추출 | 명시 기술 vs 추출 기술 | 누락 ≤2개 |
| `analyze_code` | 레포 선별 정확도 | JD 관련 레포 선택 비율 | ≥80% 관련성 |
| `analyze_code` | 코드 분석 깊이 | AST 메트릭 + LLM 분석 완전성 | HYBRID 3단계 완수 |
| `build_knowledge_graph` | 엔티티 정확도 | 추출 엔티티 ↔ 원본 데이터 대조 | 환각 엔티티 0개 |
| `build_knowledge_graph` | 관계 타당성 | 관계 추론의 논리적 근거 | 근거 없는 관계 0개 |

#### Phase 3: 질문 품질 (Question Quality) — 기존 8차원 확장

```
┌──────────────────────────────────────────────────────────┐
│            QUESTION QUALITY DIMENSIONS (8+2)              │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐    │
│  │Relevance │ │ Clarity  │ │  Depth   │ │Bias-Free│    │
│  │ (0-10)   │ │ (0-10)   │ │ (0-10)   │ │ (0-10)  │    │
│  └──────────┘ └──────────┘ └──────────┘ └─────────┘    │
│                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │Evidence Score │ │ Hallucination│ │  Duplicate   │    │
│  │  (0-100)     │ │ Risk (L/M/H) │ │ Detection    │    │
│  └──────────────┘ └──────────────┘ └──────────────┘    │
│                                                          │
│  ┌──────────────────┐ ┌──────────────────┐              │
│  │ Specificity      │ │ Follow-up Quality│              │
│  │ (generic vs      │ │ (꼬리질문 품질)   │              │
│  │  candidate-based)│ │                  │              │
│  └──────────────────┘ └──────────────────┘              │
│                                                          │
│  ── 신규 추가 ──────────────────────────────────────     │
│  ┌──────────────────┐ ┌──────────────────┐              │
│  │ Eval Scenario    │ │ Terminology      │              │
│  │ Discriminability │ │ Accuracy         │              │
│  │ (우수/보통/미흡  │ │ (용어 설명       │              │
│  │  구분 명확도)    │ │  정확성)         │              │
│  └──────────────────┘ └──────────────────┘              │
└──────────────────────────────────────────────────────────┘
```

#### Phase 4: 결과물 품질 (Output Quality)

| Activity | 품질 차원 | 측정 방법 | 합격 기준 |
|----------|----------|----------|----------|
| `generate_intel_brief` | 요약 정확성 | 요약 ↔ 원본 분석 데이터 일치 | 사실 오류 0개 |
| `generate_intel_brief` | 역량 매칭 근거 | 각 매칭에 evidence_source 존재 | 근거 없는 매칭 0개 |
| `generate_deep_analysis` | 레이더 점수 근거 | 5축 점수에 대한 설명/근거 존재 | 각 축 근거 ≥1개 |
| `generate_deep_analysis` | 스킬 매칭 정밀도 | JD 요구 스킬 ↔ 후보자 스킬 대조 | F1 ≥0.8 |
| `generate_deep_analysis` | Engineering DNA | 코드 분석 기반 특성 추출 | 코드 근거 필수 |
| `generate_decision_support` | 추천 일관성 | 점수/근거/추천이 상충 없음 | 모순 0개 |
| `generate_decision_support` | 위험 평가 근거 | 각 risk flag에 출처 존재 | 근거 없는 위험 0개 |
| `finalize_output` | 데이터 무결성 | 4탭 데이터 누락/불일치 | 누락 필드 0개 |
| `finalize_output` | 교차 일관성 | Intel Brief ↔ Deep Analysis ↔ Decision 간 일관 | 모순 0개 |

### Evidence Score 기준 (환각 방지 핵심 게이트)

| 점수 범위 | 판정 | 의미 | 조치 |
|----------|------|------|------|
| 100 | PASS | 이력서/코드에서 직접 확인 가능한 근거 | 통과 |
| 70-99 | PASS | 명시된 스킬 기반, 일부 일반화 포함 | 통과 |
| 40-69 | REVISE | 간접적 관련성, 과도한 추론 | 근거 보강 후 재생성 |
| 0-39 | REJECT | 근거 없는 가정/환각 | 삭제 및 재생성 |

### 현재 품질 검증 시스템 상태

#### 구현 완료 (✅)
| 컴포넌트 | 파일 | 기능 |
|----------|------|------|
| 구조적 검증 | `quality_review.py` | 카테고리 분포 (5종 × 3개 이상), 난이도 균형 (<60% easy/hard) |
| LLM 기반 리뷰 | `quality_review.yaml` | 8차원 평가 (관련성, 명확성, 깊이, 편향, 근거, 환각 등) |
| Evidence Score | `quality_review.yaml` | 근거 점수 0-100 (70+ PASS, 40-69 REVISE, <40 REJECT) |
| 중복 탐지 | `quality_review.yaml` | 의미적/완전 중복 질문 탐지 |
| 질문 수정 | `question_generation.py` | `revise_questions` Activity로 REVISE 판정 질문 자동 수정 |
| Langfuse 스코어 설정 | `evaluation.py` | SCORE_CONFIGS 정의 (question_quality, relevance 등) |
| 코드 분석 검증 | `code_analysis.py` | `validate_code_analysis()` Activity — HYBRID 완전성 검증 |
| Langfuse 트레이싱 | `observability_activities.py` | Job 단위 트레이스 시작/종료 + 메타데이터 |

#### 미연결/미사용 (⚠️ — 개선 필요)
| 갭 | 영향도 | 설명 |
|----|--------|------|
| Langfuse 스코어 미연결 | 🔴 HIGH | `evaluation.py`에 `create_score()` 존재하나 `quality_review.py`에서 호출 안 함 |
| 품질 결과 미저장 | 🔴 HIGH | 질문별 evidence_score, hallucination_risk가 DB에 저장되지 않음 |
| 프론트엔드 미표시 | 🔴 HIGH | 품질 지표가 Result 페이지에 노출되지 않음 |
| 수정 후 재평가 없음 | 🟡 MED | revise_questions 후 quality score 재계산 없음 |
| Phoenix eval 미사용 | 🟡 MED | `phoenix_eval.py` 존재하나 메인 플로우에 미연결 |
| Phase 2 분석 품질 미검증 | 🔴 HIGH | analyze_documents/jd/code 결과에 대한 품질 게이트 없음 |
| Phase 4 결과물 품질 미검증 | 🔴 HIGH | intel_brief/deep_analysis/decision에 대한 사후 검증 없음 |
| 교차 일관성 검증 없음 | 🟡 MED | 4탭 간 데이터 모순 탐지 로직 없음 |

### 전체 파이프라인 품질 검증 아키텍처

```
Phase 0-1: INPUT ENRICHMENT & PLANNING
    ├─ 구조적 검증 (URL 유효성, 파일 포맷)
    └─ 실행 계획 합리성 검증
    ↓
Phase 2: PARALLEL ANALYSIS
    ├─ analyze_documents → 프로필 완전성 검증 (필드 커버리지)
    ├─ analyze_jd → 구조화 정확도 검증
    ├─ analyze_code → validate_code_analysis() [구현완료]
    └─ build_knowledge_graph → 엔티티/관계 품질 검증 [TO-DO]
    ↓
Phase 3: QUESTION GENERATION
    ├─ select_topics → 카테고리 균형 + 후보자 특화도 검증
    ├─ craft_question × 20 → 8+2차원 품질 평가
    ├─ quality_review → 구조적 + LLM 기반 검증 [구현완료]
    └─ revise_questions → 재평가 루프 [구현완료, 재평가 미연결]
    ↓
Phase 4: RESULT GENERATION
    ├─ generate_intel_brief → 요약 정확성 + 역량 매칭 근거 검증 [TO-DO]
    ├─ generate_deep_analysis → 레이더 점수 근거 + 스킬 매칭 정밀도 [TO-DO]
    ├─ generate_decision_support → 추천 일관성 + 위험 평가 근거 [TO-DO]
    └─ finalize_output → 교차 일관성 검증 (4탭 모순 탐지) [TO-DO]
    ↓
Phase 5: SCORING & RECORDING
    ├─ Langfuse 스코어 기록 (Activity별 품질 점수)
    ├─ DB 저장 (품질 메트릭 영구 저장)
    └─ 품질 추세 대시보드 (주간 리포트)
```

### 품질 검증 체크리스트

#### Phase 2: 분석 품질
- [ ] **프로필 추출 완전성**: 이름, 경력, 스킬, 학력, 프로젝트 등 필수 필드 추출
- [ ] **스킬 정확도**: 추출 스킬이 실제 이력서에 존재하는지 (환각 스킬 0)
- [ ] **JD 구조화 정확도**: 필수/우대 요건 분류, 기술 스택 추출 누락 ≤2개
- [ ] **코드 분석 깊이**: HYBRID 3단계(Overview→Deep→Synthesis) 완수 여부
- [ ] **KG 엔티티 정확도**: 추출 엔티티가 원본 데이터에 근거하는지

#### Phase 3: 질문 품질
- [ ] **지원자 데이터 기반 여부**: 질문이 이력서/포트폴리오/GitHub 분석 결과에 근거하는지
- [ ] **중복 질문 제거**: 의미적으로 동일한 질문이 없는지 (유사도 >0.85 탐지)
- [ ] **수준 적절성**: 경력 수준(주니어/시니어/CTO)에 맞는 난이도인지
- [ ] **원론적 답변 방지**: 구체적 경험 기반 질문 (범용 질문 비율 <20%)
- [ ] **카테고리 균형**: 5개 카테고리 균형 (최소 3개/카테고리)
- [ ] **꼬리질문 품질**: expert/mid/low 분기 논리성, 메인과 비중복
- [ ] **평가 시나리오 구분도**: 우수/보통/미흡 답변의 차이 명확

#### Phase 4: 결과물 품질
- [ ] **Intel Brief 정확성**: 요약 내용이 분석 데이터와 일치
- [ ] **역량 매칭 근거**: 각 매칭에 evidence_source(이력서/코드/JD) 존재
- [ ] **레이더 점수 근거**: 5축 각각에 정량적 근거 (코드 메트릭, 경력 등)
- [ ] **추천 일관성**: 점수/분석/추천이 상충하지 않음
- [ ] **교차 일관성**: Intel Brief ↔ Deep Analysis ↔ Decision 간 데이터 모순 없음

---

## 🧪 Prompt A/B Testing Strategy (프롬프트 A/B 테스트 전략)

> 프롬프트를 과학적으로 비교/검증하여 더 나은 버전을 자동 선택하는 시스템

### A/B 테스트 대상 프롬프트 (6개)

| 프롬프트 YAML | Activity | 품질 영향도 | A/B 테스트 우선순위 |
|---------------|----------|-----------|-------------------|
| `question_generation.yaml` (select_topics) | `select_topics()` | CRITICAL | P0 |
| `quality_review.yaml` (review) | `review_questions()` | CRITICAL | P0 |
| `document_analysis.yaml` (extract_profile) | `analyze_documents()` | HIGH | P1 |
| `v2_generation.yaml` (competency_matching) | Intel/Deep/Decision | HIGH | P1 |
| `jd_analysis.yaml` (analyze) | `analyze_jd()` | MEDIUM | P2 |
| `finalization.yaml` (candidate_summary) | `finalize_output()` | MEDIUM | P2 |

### Langfuse Experiments 기반 A/B 테스트 워크플로우

```
┌─────────────────────────────────────────────────────────┐
│              PROMPT A/B TESTING WORKFLOW                  │
│                                                         │
│  ┌────────────┐                                         │
│  │ 1. GOLDEN  │  고품질 입출력 쌍 수집                   │
│  │  DATASET   │  (실제 운영 데이터 큐레이션)             │
│  └─────┬──────┘                                         │
│        ↓                                                │
│  ┌────────────┐   ┌────────────┐                        │
│  │ 2. PROMPT  │   │ 2. PROMPT  │  동일 입력으로          │
│  │ VERSION A  │   │ VERSION B  │  두 프롬프트 실행       │
│  │ (현재)     │   │ (후보)     │                        │
│  └─────┬──────┘   └─────┬──────┘                        │
│        ↓                ↓                                │
│  ┌────────────────────────────┐                          │
│  │ 3. EVALUATORS (자동 평가)   │                          │
│  │  ├─ LLM-as-Judge 평가자    │                          │
│  │  ├─ 구조적 검증기          │                          │
│  │  └─ Phoenix 배치 평가      │                          │
│  └───────────┬────────────────┘                          │
│              ↓                                           │
│  ┌────────────────────────────┐                          │
│  │ 4. COMPARE & DECIDE       │                          │
│  │  ├─ 통계적 유의성 검증     │                          │
│  │  ├─ 품질 지표 비교 (≥5%)   │                          │
│  │  └─ 비용/속도 트레이드오프  │                          │
│  └───────────┬────────────────┘                          │
│              ↓                                           │
│  ┌────────────────────────────┐                          │
│  │ 5. PROMOTE or ROLLBACK    │                          │
│  │  ├─ 승자 → Langfuse production label                 │
│  │  └─ 패자 → 아카이브 + 분석 기록                      │
│  └────────────────────────────┘                          │
└─────────────────────────────────────────────────────────┘
```

### 실행 방법: Langfuse Experiments API

```python
from langfuse import Langfuse

langfuse = Langfuse()

# 1. 골든 데이터셋 구축 (최소 20-50개 입출력 쌍)
dataset = langfuse.create_dataset(name="interview_questions_golden_v1")

# 실제 운영에서 고품질 결과를 큐레이션하여 추가
for item in curated_high_quality_results:
    langfuse.create_dataset_item(
        dataset_name="interview_questions_golden_v1",
        input=item["input"],       # candidate_profile + jd + code_analysis
        expected_output=item["output"],  # 고품질 질문 세트
        metadata={"source": "production", "quality_score": item["score"]}
    )

# 2. 실험 실행 (프롬프트 A vs B)
def run_prompt_variant(dataset_item, prompt_version: str):
    """특정 프롬프트 버전으로 질문 생성"""
    prompt = langfuse.get_prompt(
        name="select_topics",
        version=prompt_version,  # "v2.0" vs "v2.1"
    )
    result = llm_service.generate(prompt, dataset_item.input)
    return result

# 3. 평가자 정의
def evaluate_question_quality(output, expected_output) -> dict:
    """LLM-as-Judge + 구조적 검증 결합"""
    scores = {
        "relevance": llm_judge(output, expected_output, "relevance"),
        "specificity": structural_check(output, "specificity"),
        "evidence_grounding": evidence_check(output),
        "category_balance": distribution_check(output),
        "cost": calculate_token_cost(output),
    }
    return scores

# 4. 실험 실행 + 비교
experiment_a = langfuse.run_experiment(
    name="select_topics_v2.0",
    dataset_name="interview_questions_golden_v1",
    task=lambda item: run_prompt_variant(item, "v2.0"),
    evaluators=[evaluate_question_quality],
)

experiment_b = langfuse.run_experiment(
    name="select_topics_v2.1",
    dataset_name="interview_questions_golden_v1",
    task=lambda item: run_prompt_variant(item, "v2.1"),
    evaluators=[evaluate_question_quality],
)

# 5. 비교 결과 → Langfuse UI에서 시각적 확인
# avg(v2.1) > avg(v2.0) + 5% → v2.1을 production label로 승격
```

### Phoenix 기반 병렬 A/B 평가 (고속)

```python
from phoenix.evals import create_classifier, LLM, run_evals
import pandas as pd

llm = LLM(provider="openai", model="gpt-4o")

# Activity별 커스텀 평가자
evaluators = {
    # 프로필 추출 품질 (Phase 2)
    "profile_completeness": create_classifier(
        name="profile_completeness", llm=llm,
        prompt_template="""
        [추출된 프로필]: {extracted_profile}
        [원본 이력서]: {resume_text}
        프로필 추출이 완전한가? (이름, 경력, 스킬, 학력, 프로젝트 포함)
        답변: "complete", "partial", "incomplete"
        """,
        choices={"complete": 1.0, "partial": 0.5, "incomplete": 0.0},
    ),
    # Intel Brief 정확성 (Phase 4)
    "intel_brief_accuracy": create_classifier(
        name="intel_brief_accuracy", llm=llm,
        prompt_template="""
        [Intel Brief 요약]: {intel_brief}
        [분석 데이터]: {analysis_data}
        요약이 분석 데이터와 정확히 일치하는가? 환각이나 과장이 없는가?
        답변: "accurate", "mostly_accurate", "inaccurate"
        """,
        choices={"accurate": 1.0, "mostly_accurate": 0.5, "inaccurate": 0.0},
    ),
    # Decision 일관성 (Phase 4)
    "decision_consistency": create_classifier(
        name="decision_consistency", llm=llm,
        prompt_template="""
        [Deep Analysis 점수]: {radar_scores}
        [Decision 추천]: {recommendation}
        [위험 평가]: {risk_assessment}
        점수, 추천, 위험 평가가 서로 일관적인가? 모순이 없는가?
        답변: "consistent", "minor_inconsistency", "contradictory"
        """,
        choices={"consistent": 1.0, "minor_inconsistency": 0.5, "contradictory": 0.0},
    ),
    # 질문 특화도 (Phase 3)
    "question_specificity": create_classifier(
        name="specificity", llm=llm,
        prompt_template="""
        [지원자 배경]: {candidate_summary}
        [면접 질문]: {question}
        이 질문이 지원자의 구체적 경험에 기반한 맞춤 질문인가?
        답변: "specific", "somewhat_specific", "generic"
        """,
        choices={"specific": 1.0, "somewhat_specific": 0.5, "generic": 0.0},
    ),
}

# 배치 평가 (20x 속도 향상 — async + concurrency)
df = pd.DataFrame(test_data)
results = run_evals(df, evaluators=list(evaluators.values()), concurrency=10)
```

### A/B 테스트 승격/롤백 기준

| 항목 | 승격 조건 (B → Production) | 롤백 조건 (B → Archive) |
|------|--------------------------|------------------------|
| 품질 점수 | avg(B) > avg(A) + 5% | avg(B) < avg(A) |
| 환각 비율 | hallucination(B) ≤ hallucination(A) | hallucination(B) > hallucination(A) + 2% |
| 토큰 비용 | cost(B) ≤ cost(A) × 1.2 | cost(B) > cost(A) × 1.5 |
| 샘플 수 | n ≥ 50 (5일 × 10회, 통계적 유의성) | n < 30 (불충분) |
| 응답 속도 | latency(B) ≤ latency(A) × 1.3 | latency(B) > latency(A) × 2.0 |

### A/B 테스트 실행 주기 (사전 런칭 집중 모드)

> **현재 상태**: 서비스 미출시 — 자체 품질 업그레이드 집중 기간. 매일 테스트를 돌려 빠르게 프롬프트 품질을 수렴시킨다.

```
Daily (매일 — 프롬프트당 A 5회 + B 5회 = 총 10회):
  ┌─────────────────────────────────────────────────────────┐
  │  P0 (select_topics, quality_review)                      │
  │    → A 버전 5회 실행 + B 버전 5회 실행 = 10회/일         │
  │    → 평가자 자동 채점 → 일간 비교 리포트                  │
  │                                                         │
  │  P1 (document_analysis, v2_generation)                   │
  │    → A 버전 5회 실행 + B 버전 5회 실행 = 10회/일         │
  │    → 프로필 완전성 + 역량 매칭 평가                       │
  │                                                         │
  │  P2 (jd_analysis, finalization)                          │
  │    → A 버전 5회 실행 + B 버전 5회 실행 = 10회/일         │
  │    → JD 구조화 + 교차 일관성 평가                         │
  └─────────────────────────────────────────────────────────┘

  총 일일 테스트: 6개 프롬프트 × 10회 = 60회/일

  일간 판정 흐름:
    1. 매일 테스트 실행 (create_test_job.py 활용, 다양한 입력 조합)
    2. Langfuse/Phoenix 평가자 자동 채점
    3. 5일간 누적 데이터 (각 프롬프트 50회) → 통계적 유의성 확보
    4. 5일 누적 avg(B) > avg(A) + 5% → B를 production label로 승격
    5. 승격 후 → B가 새 A가 되고, 다음 후보 C 개발 → 반복

On-demand (즉시):
  - 프롬프트 수정 시 → 당일 10회 테스트 즉시 실행
  - 새 Activity 추가 시 → 관련 평가자 추가 + 10회 베이스라인 측정
  - 품질 하락 감지 시 → 즉시 원인 분석 + 롤백 판단

런칭 전 졸업 기준:
  - 모든 P0 프롬프트 Evidence Score 평균 ≥ 80
  - 모든 P1 프롬프트 정확도 ≥ 85%
  - Phase 4 교차 일관성 모순 0개 (10회 연속)
  - 환각 비율 0% (50회 연속)
  → 졸업 후 운영 모드 전환 (주간 벤치마크로 축소)
```

### 일일 A/B 테스트 실행 방법

```bash
# 1. 다양한 입력 조합으로 테스트 Job 5개 생성
for i in 1 2 3 4 5; do
  docker compose exec backend python scripts/create_test_job.py \
    --email test${i}@example.com \
    --level $(echo "주니어 시니어 CTO/VP 리드 미들" | cut -d' ' -f$i) \
    --lang $(echo "ko en ko en ko" | cut -d' ' -f$i) \
    --questions $(echo "15 20 25 10 20" | cut -d' ' -f$i)
done

# 2. Temporal 워크플로우 실행 대기 (Phase 0-5 완료)

# 3. Langfuse에서 실험 결과 비교
#    Langfuse UI → Experiments → 프롬프트 버전별 품질 점수 비교

# 4. Phoenix 배치 평가 (선택)
docker compose exec backend python scripts/run_phoenix_eval.py \
  --prompt select_topics --versions "v2.0,v2.1" --runs 5
```

### Langfuse Eval 통합 방안 (LLM-as-Judge + SDK)

> Langfuse는 이미 프로젝트에 통합되어 있으므로, Eval 기능을 활용하여 전체 파이프라인 품질 검증을 자동화

#### 1. LLM-as-Judge 평가자 (전체 파이프라인)

Langfuse UI → Evaluators → 아래 평가자 생성:

| 평가자 | 타입 | 대상 Activity | 평가 내용 |
|--------|------|--------------|----------|
| `profile_extraction_quality` | NUMERIC (0-1) | `analyze_documents` | 프로필 추출 완전성 + 정확도 |
| `jd_analysis_quality` | NUMERIC (0-1) | `analyze_jd` | 요구사항 구조화 정확도 |
| `code_analysis_depth` | NUMERIC (0-1) | `analyze_code` | HYBRID 분석 깊이 + 정확도 |
| `kg_entity_accuracy` | NUMERIC (0-1) | `build_knowledge_graph` | KG 엔티티/관계 정확도 |
| `question_relevance` | NUMERIC (0-1) | `craft_question` | JD + 후보자 경험 ↔ 질문 관련성 |
| `question_specificity` | NUMERIC (0-1) | `craft_question` | 후보자 특화 vs 범용 |
| `evidence_grounding` | NUMERIC (0-1) | `craft_question` | 근거 기반 vs 환각 |
| `followup_quality` | NUMERIC (0-1) | `design_follow_ups` | 꼬리질문 논리성/연관성 |
| `intel_brief_accuracy` | NUMERIC (0-1) | `generate_intel_brief` | 요약 정확성 + 매칭 근거 |
| `radar_score_grounding` | NUMERIC (0-1) | `generate_deep_analysis` | 레이더 점수 근거 타당성 |
| `decision_consistency` | NUMERIC (0-1) | `generate_decision_support` | 추천/점수/위험 일관성 |
| `cross_tab_consistency` | NUMERIC (0-1) | `finalize_output` | 4탭 교차 일관성 |

#### 2. SDK 기반 스코어 기록 (전 Activity 확장)

```python
# 각 Activity 완료 후 품질 스코어 자동 기록
from app.core.evaluation import create_score

# Phase 2: 분석 Activity 스코어
async def score_analysis_quality(trace_id, activity_name, result):
    completeness = calculate_completeness(result)
    create_score(trace_id, f"{activity_name}_completeness", completeness)
    create_score(trace_id, f"{activity_name}_accuracy", calculate_accuracy(result))

# Phase 3: 질문 Activity 스코어 (기존)
async def score_question_quality(trace_id, question_review):
    create_score(trace_id, "question_quality", question_review["score"] / 10)
    create_score(trace_id, "evidence_score", question_review["evidence_score"] / 100)

# Phase 4: 결과물 Activity 스코어 (신규)
async def score_output_quality(trace_id, tab_name, output, analysis_data):
    consistency = check_cross_consistency(output, analysis_data)
    create_score(trace_id, f"{tab_name}_consistency", consistency)
    create_score(trace_id, f"{tab_name}_grounding", check_evidence(output))
```

#### 3. 골든 데이터셋 (Activity별)

```python
# Activity별 골든 데이터셋 구축
datasets = {
    "profile_extraction_golden":   "analyze_documents 고품질 결과",
    "jd_analysis_golden":          "analyze_jd 고품질 결과",
    "topic_selection_golden":      "select_topics 고품질 결과",
    "question_generation_golden":  "craft_question 고품질 결과",
    "intel_brief_golden":          "generate_intel_brief 고품질 결과",
    "deep_analysis_golden":        "generate_deep_analysis 고품질 결과",
    "decision_support_golden":     "generate_decision_support 고품질 결과",
}

# 각 데이터셋은 최소 20개 입출력 쌍
# 실제 운영 데이터에서 높은 품질 점수를 받은 결과를 자동 큐레이션
```

#### 4. Annotation Queue (사람 평가)

- 채용 담당자가 생성된 전체 결과물(4탭)을 직접 평가
- LLM-as-Judge 점수 ↔ 사람 평가 점수 상관관계 검증
- Cohen's Kappa로 자동 평가 신뢰도 측정
- 신뢰도 낮은 평가자 → 프롬프트 개선 트리거

### Kimi K2.5 파인튜닝 현황

| 항목 | 상태 | 비고 |
|------|------|------|
| Moonshot Platform API 파인튜닝 | ❌ 미지원 | `moonshot-v1-auto` API는 추론만 가능 |
| Open-source 모델 (HuggingFace) | ✅ 가능 | `moonshotai/Kimi-K2.5` (1T params, 32B active, MoE) |
| LoRA 파인튜닝 | ✅ 가능 | LlamaFactory + KTransformers (2x RTX 4090 필요) |
| Fireworks AI 관리형 | ✅ 가능 | LoRA 파인튜닝 지원, Full RL은 대기 목록 |
| NVIDIA NeMo | ✅ 가능 | AutoModel 기반 커스터마이징 |

#### 파인튜닝 대비 현실적 품질 개선 전략 (권장 순서)

```
Phase 1 (현재): 프롬프트 최적화 (Langfuse 프롬프트 관리)
    ↓ 효과 부족 시
Phase 2: Few-shot 예시 강화 (골든 데이터셋 기반)
    ↓ 효과 부족 시
Phase 3: Eval 기반 자동 품질 게이트 (Langfuse + Phoenix)
    + Prompt A/B Testing (실험적 검증)
    ↓ 효과 부족 시
Phase 4: 파인튜닝 검토 (Fireworks AI LoRA 또는 self-hosted)
```

**현재 권장**: Phase 1-3에 집중. 파인튜닝은 GPU 인프라 비용 대비 프롬프트 최적화 + Eval 게이트 + A/B 테스트가 더 비용 효율적.

### 전체 품질 자동 개선 루프

```
┌──────────────────────────────────────────────────────────┐
│        AGENT OUTPUT QUALITY AUTO-IMPROVEMENT LOOP         │
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌───────────────────────┐│
│  │ GENERATE │ → │ EVALUATE │ → │ SCORE & RECORD        ││
│  │ (전체    │   │ (Phase별 │   │ (Langfuse + DB 기록)  ││
│  │ 파이프   │   │  평가자)  │   │                       ││
│  │ 라인)    │   │          │   │                       ││
│  └──────────┘   └──────────┘   └──────────┬────────────┘│
│       ↑                                    │             │
│  ┌────┴────┐                    ┌─────────↓───────────┐ │
│  │ REVISE  │ ←  LOW SCORE ←── │ ANALYZE TRENDS       │ │
│  │ (재생성 │                   │ (Activity별 품질     │ │
│  │  / 수정)│                   │  추세 분석)          │ │
│  └─────────┘                   └─────────┬───────────┘ │
│                                           │             │
│                              ┌────────────↓───────────┐ │
│                              │ A/B TEST & PROMOTE     │ │
│                              │ (프롬프트 실험 →       │ │
│                              │  승자 승격)            │ │
│                              └────────────────────────┘ │
└──────────────────────────────────────────────────────────┘

자동화 트리거:
Phase 2:
- 프로필 추출 완전성 < 90% → analyze_documents 프롬프트 A/B 테스트 트리거
- JD 기술 누락 > 2개 → analyze_jd 프롬프트 검토
- HYBRID 분석 미완수 → analyze_code 재실행

Phase 3:
- Evidence Score < 70 → revise_questions 자동 호출
- 환각 탐지 → 해당 질문 REJECT + 재생성
- 중복 발견 → 중복 제거 + 대체 질문 생성
- 카테고리 불균형 → 부족 카테고리 추가 질문 생성

Phase 4:
- Intel Brief 사실 오류 탐지 → 재생성
- 레이더 점수 근거 부족 → 분석 데이터 재참조
- Decision-Analysis 모순 탐지 → 교차 검증 후 수정

전체:
- Langfuse 주간 리포트 → Activity별 품질 추세 대시보드
- 품질 하락 Activity → 자동 A/B 테스트 트리거
- A/B 테스트 승자 → Langfuse production label 자동 승격
```
