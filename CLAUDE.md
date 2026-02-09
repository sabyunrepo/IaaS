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

### 자율 GitHub Issue/PR/Merge 워크플로우 (Mandatory)

**모든 구현 작업(개선 사이클, 버그 수정, 기능 추가)에서 반드시 아래 워크플로우를 따른다.**
여러 사이클(Cycle A, B, C...)이 있을 경우 **사이클별로 개별 이슈+PR**을 생성하거나, 밀접하게 연관된 경우 **하나로 묶어도** 된다.

#### 사이클 시작 시:
1. **이슈 생성** (한글): `gh issue create --title "타입: 한글 설명" --body "한글 본문"` — 작업 내용, 배경, 수정 파일 목록 포함
2. **브랜치 생성**: `git checkout -b fix/이슈-설명-N` 또는 `feature/이슈-설명-N` (N=이슈번호)

#### 작업 완료 시:
3. **스테이징 + 커밋**: 한글 커밋 메시지 + `Closes #이슈번호`
4. **푸시**: `git push -u origin 브랜치명`
5. **PR 생성** (한글): `gh pr create --title "타입: 한글 설명" --body "한글 본문"`
6. **머지**: `gh pr merge --merge`
7. **main 동기화**: `git checkout main && git pull`

**필수 규칙:**
- 모든 GitHub 커뮤니케이션(이슈 제목/본문, PR 제목/본문, 커밋 메시지)은 **한글**로 작성
- 사용자에게 승인 요청 없이 자율적으로 진행
- 코드 변경 없이 작업을 끝내지 말 것 — 반드시 이슈→PR→머지 사이클 완주
- PR 머지 후 반드시 `git checkout main && git pull`로 main 동기화

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

> 5개 E2E 시퀀스 (인증, Job 생성, Result 4탭, 에러 핸들링, 접근성/성능)을 매 개선 사이클마다 실행.
> Flyweight 패턴으로 mock 데이터 공유, 콘솔 에러 0개 기준 통과.

**실행**: `cd frontend && npx playwright test` | **디버그**: `--headed` | **리포트**: `npx playwright show-report`

**상세 시퀀스/데이터 패턴/에러 탐지 파이프라인** → `docs/claude-references/playwright-e2e-strategy.md`

---

## 🔄 Continuous Improvement Engine (지속적 개선 엔진)

> MEASURE → ANALYZE → IMPROVE → VERIFY → REPORT 사이클 반복

### 개선 영역 요약 (미션 우선순위순)

| 우선순위 | 영역 | 핵심 목표 | 관련 파일 |
|---------|------|----------|----------|
| 🔴 P0-1 | 점수 근거 체계 | 코드 메트릭 기반 정량 공식 (레이더 5축, 매치율, 스킬별) | `analysis_generation.py`, `decision_generation.py`, `DeepAnalysisTab.tsx` |
| 🔴 P0-2 | 코드 기반 질문 | ≥60% 질문이 후보자 GitHub 코드에서 추출 | `question_generation.py`, `code_analysis.py` |
| 🔴 P0-3 | 비개발자 답변 가이드 | 3단계(우수/보통/주의) + glossary + 후속질문 팁 | `craft_evaluation_scenarios()`, `LiveInterviewTab.tsx` |
| 🔴 P0-4 | LinkedIn 경력 구조화 | 타임라인 + 추천서 요약 + 승진 패턴 | `linkedin_service.py`, `IntelBriefTab.tsx` |
| 🟡 P1 | 아웃풋 품질 & UX | AST/PyDriller 정확도, 반응형, WCAG 2.1 AA, i18n | `quality_review.py`, 프론트엔드 전체 |
| 🟢 P2 | 인프라 & 안정성 | N+1, 캐시, CWV, OWASP Top 10, SRP | 백엔드/프론트엔드 전체 |

### Git 워크플로우 (매 개선건)

`gh issue create` → `git checkout -b improve/[영역]` → 수정+테스트 → `git commit -m "improve: [설명] Closes #N"` → `gh pr create` → merge → main sync

**P0 상세 TODO, P1/P2 세부, 보고서 형식** → `docs/claude-references/improvement-engine.md`

---

## 🔍 Agent Output Quality Verification Engine (에이전트 아웃풋 품질 검증 엔진)

> 전체 파이프라인(Phase 0-4, 16+ Activity)의 LLM 아웃풋을 자동 검증하는 통합 품질 시스템.

### 핵심 게이트: Evidence Score

| 점수 | 판정 | 조치 |
|------|------|------|
| 70-100 | PASS | 통과 |
| 40-69 | REVISE | 근거 보강 후 재생성 |
| 0-39 | REJECT | 삭제 및 재생성 |

### 품질 차원 요약

| Phase | 핵심 검증 | 합격 기준 |
|-------|----------|----------|
| P2 분석 | 프로필 완전성, 스킬 정확도, JD 구조화, HYBRID 완수 | ≥90% 필드, 환각 0, 누락 ≤2 |
| P3 질문 | 10차원 (Relevance/Clarity/Depth/Bias/Evidence/Hallucination/Duplicate/Specificity/EvalScenario/Terminology) | Evidence ≥70, 범용 <20%, 중복 0 |
| P4 결과물 | Intel 정확성, 레이더 근거, 추천 일관성, 4탭 교차 일관성 | 사실오류 0, 모순 0 |

### 구현 상태

| ✅ 완료 | ⚠️ 미연결 (HIGH) |
|---------|-----------------|
| `quality_review.py` 구조적+LLM 8차원 검증 | Langfuse 스코어 미호출 |
| Evidence Score 게이트 (0-100) | 품질 결과 DB 미저장 |
| 중복 탐지 + `revise_questions` 자동 수정 | Phase 2/4 품질 게이트 없음 |
| `validate_code_analysis()` HYBRID 검증 | 교차 일관성 검증 없음 |
| Langfuse 트레이싱 (Job 단위) | 프론트엔드 품질 지표 미표시 |

**Phase별 상세 품질 차원, 파이프라인 아키텍처, 체크리스트** → `docs/claude-references/quality-verification-engine.md`

---

## 🧪 Prompt A/B Testing Strategy (프롬프트 A/B 테스트 전략)

> GOLDEN DATASET → PROMPT A/B 실행 → EVALUATORS → COMPARE → PROMOTE/ROLLBACK

### 대상 프롬프트 (6개)

| YAML | Activity | 우선순위 |
|------|----------|---------|
| `question_generation.yaml` | `select_topics()` | P0 |
| `quality_review.yaml` | `review_questions()` | P0 |
| `document_analysis.yaml` | `analyze_documents()` | P1 |
| `v2_generation.yaml` | Intel/Deep/Decision | P1 |
| `jd_analysis.yaml` | `analyze_jd()` | P2 |
| `finalization.yaml` | `finalize_output()` | P2 |

### 승격/롤백 기준

| 항목 | 승격 (B→Prod) | 롤백 |
|------|--------------|------|
| 품질 | avg(B) > avg(A) + 5% | avg(B) < avg(A) |
| 환각 | hallu(B) ≤ hallu(A) | hallu(B) > hallu(A) + 2% |
| 비용 | cost(B) ≤ cost(A) × 1.2 | cost(B) > cost(A) × 1.5 |
| 샘플 | n ≥ 50 | n < 30 |

### 실행 주기

- **Daily**: 6개 프롬프트 × (A 5회 + B 5회) = 60회/일
- **5일 누적** → 통계적 유의성 → 승격/롤백
- **졸업 기준**: P0 Evidence ≥80, P1 정확도 ≥85%, 환각 0% (50회 연속)

### 품질 개선 전략 (권장 순서)

프롬프트 최적화 → Few-shot 강화 → Eval 게이트 (Langfuse+Phoenix) → 파인튜닝 (Fireworks AI LoRA)

### 자동 개선 루프

`GENERATE → EVALUATE → SCORE & RECORD → ANALYZE TRENDS → (low score) → REVISE → GENERATE` + A/B 승자 자동 승격

**Langfuse API/Phoenix 코드, 12개 LLM-as-Judge 평가자, 골든 데이터셋, 파인튜닝 현황** → `docs/claude-references/prompt-ab-testing.md`
