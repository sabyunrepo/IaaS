# Architecture Guide Skill

> 구현 에이전트용 아키텍처 참조 가이드 (최종본)

---

## 목적

이 스킬은 구현 에이전트가 **코드를 작성할 때 반드시 참조**해야 하는 아키텍처 규칙, 패턴, 의존성 관계를 정의한다. 모든 구현은 이 가이드에 따라야 한다.

---

## 시스템 개요

**Verdict (Vantict Sniper v4.0)**: AI 기술면접 스크립트 생성기

```
입력: 이력서(PDF) + 포트폴리오(DOCX) + GitHub URL + 채용공고(JD)
  ↓
처리: 4-Phase 파이프라인 (Temporal 워크플로우)
  ↓
출력: 10개 맞춤형 면접 질문 + 예상답변 + 평가기준 + 용어설명
```

---

## 기술 스택 (변경 금지)

| 레이어 | 기술 | 버전 |
|--------|------|------|
| Frontend | Next.js + React + i18n | 14+ |
| Backend | FastAPI + Python | 3.11+ |
| Orchestration | Temporal.io | 1.22+ |
| Database | PostgreSQL + pgvector | 16+ |
| Cache | Redis | 7+ |
| Storage | LocalStack S3 → AWS S3 | - |
| LLM | OpenAI GPT-4o / Anthropic Claude | - |
| Container | Docker Compose → AWS Copilot | - |

---

## 프로젝트 구조 (필수 준수)

```
backend/
├── app/
│   ├── main.py                     # FastAPI 엔트리포인트
│   ├── config.py                   # 환경 기반 설정 (pydantic-settings)
│   ├── api/
│   │   ├── v1/
│   │   │   └── jobs.py             # REST API 라우터
│   │   └── deps.py                 # 의존성 주입
│   ├── workflows/
│   │   ├── interview_workflow.py   # 메인 Temporal 워크플로우
│   │   └── activities/
│   │       ├── planning.py
│   │       ├── document_analysis.py
│   │       ├── code_analysis.py
│   │       ├── jd_analysis.py
│   │       ├── question_generation.py
│   │       ├── quality_review.py
│   │       ├── finalization.py
│   │       └── checkpoint_activities.py
│   ├── services/
│   │   ├── llm_service.py          # CachedLLMService
│   │   ├── llm_cache.py            # LLMResultCache
│   │   ├── checkpoint_store.py     # CheckpointStore
│   │   ├── github_service.py
│   │   ├── document_parser.py
│   │   ├── code_analyzer.py
│   │   └── vector_store.py
│   ├── models/
│   │   ├── job.py
│   │   ├── question.py
│   │   ├── analysis.py
│   │   ├── checkpoint.py
│   │   └── types.py
│   ├── prompts/                    # LLM 프롬프트 YAML
│   └── worker.py                   # Temporal Worker 엔트리
├── tests/
├── Dockerfile
└── pyproject.toml
```

---

## 파이프라인 단계 (9 Steps)

```
Step 1: plan                 → Planner Activity
Step 2: document_analysis    → Document Manager Activity (병렬)
Step 3: code_analysis        → Code Manager Activity (병렬)
Step 4: jd_analysis          → JD Manager Activity (병렬)
Step 5: aggregate_analysis   → 분석 결과 집계
Step 6: select_topics        → Question Generator (토픽 선정)
Step 7: craft_questions      → Question Generator (10개 병렬 생성)
Step 8: review_quality       → Quality Review Loop (최대 3회)
Step 9: finalize             → Finalization Activity
```

**병렬 실행**: Step 2~4는 `workflow.wait_all()`로 병렬 실행
**체크포인트**: 각 Step 완료 시 `checkpoint_activities.save_checkpoint()` 호출

---

## 필수 구현 규칙

### 1. LLM 호출은 반드시 CachedLLMService를 사용

```python
# ✅ CORRECT
from app.services.llm_service import CachedLLMService

llm = CachedLLMService(openai_client, redis)
result = await llm.chat(messages, model="gpt-4o")

# ❌ WRONG — 직접 호출하면 캐시 미적용, 재시도 시 비용 낭비
result = await openai_client.chat.completions.create(...)
```

### 2. Activity는 멱등성(Idempotent) 보장

```python
# ✅ CORRECT — 같은 입력에 같은 결과
@activity.defn
async def analyze_jd(job_id: str, jd_text: str) -> dict:
    llm = CachedLLMService(client, redis)  # 캐시로 멱등성 보장
    return await llm.chat(messages)

# ❌ WRONG — 부수효과가 멱등하지 않음
@activity.defn
async def analyze_jd(job_id: str, jd_text: str) -> dict:
    await db.insert(...)  # 재시도 시 중복 삽입
    return result
```

### 3. 긴 Activity는 heartbeat 필수

```python
# ✅ CORRECT
@activity.defn
async def analyze_code(job_id: str, urls: list[str]) -> dict:
    heartbeat_details = activity.info().heartbeat_details
    start_idx = heartbeat_details[0] if heartbeat_details else 0
    results = heartbeat_details[1] if heartbeat_details else []

    for i in range(start_idx, len(urls)):
        result = await _analyze(urls[i])
        results.append(result)
        activity.heartbeat(i + 1, results)  # 중간 저장

    return aggregate(results)

# ❌ WRONG — 3개 repo 중 2번째에서 실패하면 처음부터 재실행
@activity.defn
async def analyze_code(job_id: str, urls: list[str]) -> dict:
    results = []
    for url in urls:
        results.append(await _analyze(url))
    return aggregate(results)
```

### 4. 워크플로우 내 체크포인트 저장 패턴

```python
# 모든 Phase 완료 후 반드시 체크포인트 저장
result = await workflow.execute_activity(some_activity, args=[...])

await workflow.execute_activity(
    checkpoint_activities.save_checkpoint,
    args=[job_id, "step_name", result],
    start_to_close_timeout=timedelta(minutes=2),
)
```

### 5. 환경 설정은 pydantic-settings 사용

```python
# ✅ CORRECT
from app.config import get_settings
settings = get_settings()
url = settings.DATABASE_URL

# ❌ WRONG — 직접 환경변수 접근
import os
url = os.environ["DATABASE_URL"]
```

### 6. 에러 분류

```python
# 재시도 가능한 에러 (Temporal이 자동 재시도)
class RetryableError(Exception): pass
# → RateLimitError, TimeoutError, ConnectionError

# 재시도 불가능한 에러 (즉시 실패)
class NonRetryableError(Exception): pass
# → ValidationError, AuthenticationError, InvalidInputError

# RetryPolicy에서 non_retryable_error_types 설정
retry_policy = RetryPolicy(
    non_retryable_error_types=["ValueError", "ValidationError"],
)
```

---

## 데이터 흐름

```
InputData (API 요청)
  │
  ├─[Phase 1]──→ ExecutionPlan
  │                 │
  ├─[Phase 2]──→ ┌─┴──────────────────────────────┐
  │              │ CandidateProfile (문서 분석)     │
  │              │ CodeAnalysis (코드 분석)          │
  │              │ JDAnalysis (JD 분석)              │
  │              └─┬──────────────────────────────┘
  │                │ aggregate
  │                ▼
  ├─[Phase 3]──→ selected_topics → InterviewQuestion[10]
  │              → review_quality loop (최대 3회)
  │                │
  ├─[Phase 4]──→ InterviewScript (최종 출력)
  │
  └─[저장]────→ Redis (체크포인트) + S3 (결과) + PostgreSQL (메타)
```

---

## Redis 키 구조

```
# Job 상태
job:{job_id}:status           → JSON
job:{job_id}:progress         → JSON
job:{job_id}:input            → JSON (원본 입력, TTL 7d)

# 체크포인트
checkpoint:{job_id}:{step}    → JSON (TTL 7d)
checkpoint:{job_id}:_meta     → Hash (TTL 7d)

# LLM 캐시
llm_cache:{model}:{hash}     → JSON (TTL 24h)

# Rate Limiting
ratelimit:github:{hash}      → Counter
ratelimit:llm:{hash}         → Counter
```

---

## API 엔드포인트 목록

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/v1/jobs` | 작업 생성 |
| GET | `/api/v1/jobs/{id}/status` | 상태 조회 |
| GET | `/api/v1/jobs/{id}/result` | 결과 조회 (json/md/pdf) |
| GET | `/api/v1/jobs` | 작업 목록 |
| DELETE | `/api/v1/jobs/{id}` | 작업 취소 |
| POST | `/api/v1/jobs/{id}/retry` | 실패 재시작 |
| GET | `/api/v1/jobs/{id}/checkpoints` | 체크포인트 상태 |
| WS | `/api/v1/jobs/{id}/ws` | 실시간 상태 |

---

## 에이전트별 참조 스킬

| 에이전트 스킬 | 참조 문서 | 핵심 책임 |
|--------------|----------|----------|
| [Planner](../planner/SKILL.md) | 01-overview, 03-workflow | 입력 검증, 워크로드 추정 |
| [Document Manager](../document-manager/SKILL.md) | 02-data-models | PDF/DOCX 파싱, 프로필 추출 |
| [Code Manager](../code-manager/SKILL.md) | 02-data-models | GitHub 클론, AST 분석, 패턴 탐지 |
| [JD Manager](../jd-manager/SKILL.md) | 02-data-models | JD 파싱, 요구사항/스킬 추출 |
| [Question Generator](../question-generator/SKILL.md) | 02-data-models, 03-workflow | 토픽 선정, 질문 생성, 수정 |
| [Supervisor](../supervisor/SKILL.md) | 03-workflow | 상태 관리, 에러 복구, 품질 검증 |
| [Checkpoint Manager](../checkpoint-manager/SKILL.md) | 03-workflow, 04-infra | LLM 캐시, 스냅샷, 재시작 |

---

## 구현 체크리스트

에이전트가 코드를 작성할 때 확인해야 할 항목:

- [ ] LLM 호출은 `CachedLLMService`를 통해서만 한다
- [ ] Activity는 멱등성을 보장한다
- [ ] 긴 Activity(>1분)는 `activity.heartbeat()`를 사용한다
- [ ] Phase 완료 시 `checkpoint_activities.save_checkpoint()`를 호출한다
- [ ] 설정값은 `get_settings()`로 접근한다
- [ ] 에러는 `RetryableError`/`NonRetryableError`로 분류한다
- [ ] 데이터 모델은 `02-data-models.md`의 Pydantic 모델을 따른다
- [ ] API 응답은 `05-api-spec.md`의 TypeScript 인터페이스를 따른다
- [ ] Docker 환경에서 테스트한다 (`docker compose up`)
- [ ] 벡터 저장은 `pgvector` 1536 차원을 사용한다
