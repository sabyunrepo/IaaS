# Vantict Sniper v4.0 — MVP 단계별 구현 계획

> 각 단계는 **테스트/검증 통과 후** 다음 단계로 진행합니다.
> 브랜치: `feature/mvp-implementation`

---

## 의존성 그래프

```
Step 1: 프로젝트 스캐폴딩 + Docker Compose
  ↓
Step 2: 데이터 모델 (Pydantic + SQLAlchemy)
  ↓
Step 3: DB 초기화 + Settings + Core 모듈
  ↓
Step 4: FastAPI 기본 서버 + 헬스체크
  ↓
Step 5: OAuth 인증 시스템 (JWT + API Key)
  ↓
Step 6: Job CRUD API 엔드포인트
  ↓
Step 7: Temporal Worker 기본 설정
  ↓
Step 8: Phase 0 — Smart Input Extraction
  ↓
Step 9: Phase 1 — Planning Activity
  ↓
Step 10: Phase 2 — Parallel Analysis (Document + Code + JD)
  ↓
Step 11: Phase 3 — Question Generation (25개)
  ↓
Step 12: Phase 4 — Quality Review + Finalization
  ↓
Step 13: Frontend — React SPA 기본 구조
  ↓
Step 14: Frontend — 로그인 + Job 생성/조회
  ↓
Step 15: Frontend — 면접 스크립트 뷰어
  ↓
Step 16: 통합 테스트 + E2E
```

---

## Step 1: 프로젝트 스캐폴딩 + Docker Compose

### 목표
프로젝트 디렉토리 구조 생성, Docker Compose로 전체 인프라 컨테이너 실행 확인.

### 구현 내용
- [ ] `backend/` 디렉토리 + `pyproject.toml` (FastAPI, Temporal SDK, SQLAlchemy, Pydantic 등)
- [ ] `backend/Dockerfile`
- [ ] `backend/app/__init__.py`, `backend/app/main.py` (빈 FastAPI 앱)
- [ ] `frontend/` 디렉토리 + `package.json` (Vite + React + Tailwind)
- [ ] `frontend/Dockerfile`
- [ ] `docker-compose.yml` (postgres, redis, temporal, temporal-ui, localstack, langfuse)
- [ ] `.env.local` (환경 변수 템플릿)
- [ ] `scripts/setup.sh` (초기 설정 스크립트)

### 검증 기준
```bash
# 모든 컨테이너 정상 기동
docker compose up -d
docker compose ps  # 모든 서비스 healthy/running

# PostgreSQL 접속
docker compose exec postgres psql -U postgres -d vantict -c "SELECT 1;"

# Redis 접속
docker compose exec redis redis-cli ping  # → PONG

# Temporal UI 접근
curl -s http://localhost:8080 | head -1  # → HTML 응답

# Backend 응답 (빈 앱)
curl http://localhost:8000/  # → 200 또는 404 (앱 실행 확인)
```

### 커밋: `feat: Step 1 — 프로젝트 스캐폴딩 및 Docker Compose 인프라`

---

## Step 2: 데이터 모델 (Pydantic + SQLAlchemy)

### 목표
아키텍처 `02-data-models.md` 기반으로 전체 Pydantic 모델 + SQLAlchemy ORM 모델 정의.

### 구현 내용
- [ ] `backend/app/models/enums.py` — JobStatus, QuestionCategory, Difficulty, ExperienceLevel 등
- [ ] `backend/app/models/user.py` — User, OAuthAccount, APIKey (Pydantic + SQLAlchemy)
- [ ] `backend/app/models/job.py` — Job, CreateJobRequest, JobResponse
- [ ] `backend/app/models/input.py` — InputData, EnrichedInput, FileAttachment
- [ ] `backend/app/models/analysis.py` — CandidateProfile, CodeAnalysis, JDAnalysis
- [ ] `backend/app/models/question.py` — InterviewQuestion, FollowUp, Evaluation, Terminology, CodeReference
- [ ] `backend/app/models/output.py` — InterviewScript, CandidateSummary, DecisionGuide
- [ ] `backend/app/models/__init__.py` — 모든 모델 re-export

### 검증 기준
```bash
cd backend

# 모델 import 성공
python -c "from app.models import *; print('All models imported')"

# Pydantic 모델 직렬화 테스트
python -c "
from app.models.job import CreateJobRequest
req = CreateJobRequest(jd_text='test', experience_level='junior', output_language='ko')
print(req.model_dump_json(indent=2))
"

# SQLAlchemy 모델 테이블 생성 확인
python -c "
from app.models.user import UserTable
print(UserTable.__tablename__)
"
```

### 커밋: `feat: Step 2 — Pydantic + SQLAlchemy 데이터 모델`

---

## Step 3: DB 초기화 + Settings + Core 모듈

### 목표
DB 연결, 환경설정, Temporal 클라이언트 팩토리 등 핵심 인프라 코드 구현.

### 구현 내용
- [ ] `backend/app/core/config.py` — Settings (pydantic-settings, 모든 환경변수)
- [ ] `backend/app/core/database.py` — AsyncEngine, AsyncSession, get_db()
- [ ] `backend/app/core/temporal.py` — get_temporal_client()
- [ ] `backend/app/core/__init__.py`
- [ ] `backend/app/exceptions.py` — VantictBaseError, JobNotFoundError 등 예외 계층
- [ ] DB 마이그레이션: `CREATE EXTENSION IF NOT EXISTS vector;` + 테이블 생성

### 검증 기준
```bash
# Settings 로드 테스트
python -c "from app.core.config import settings; print(settings.DATABASE_URL)"

# DB 연결 + 테이블 생성
python -c "
import asyncio
from app.core.database import engine, Base
async def test():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Tables created')
asyncio.run(test())
"

# 예외 계층 확인
python -c "
from app.exceptions import JobNotFoundError
try:
    raise JobNotFoundError('test-id')
except JobNotFoundError as e:
    print(f'Code: {e.code}, Message: {e.message}')
"
```

### 커밋: `feat: Step 3 — Core 모듈 (Settings, DB, Temporal, 예외)`

---

## Step 4: FastAPI 기본 서버 + 헬스체크

### 목표
FastAPI 앱 구성, 미들웨어, 헬스체크, CORS, 에러 핸들러 설정.

### 구현 내용
- [ ] `backend/app/main.py` — FastAPI 앱, 미들웨어 (CORS, Session), 에러 핸들러
- [ ] `backend/app/api/health.py` — `/health` 엔드포인트 (DB, Redis, Temporal 상태)
- [ ] `backend/app/api/__init__.py`

### 검증 기준
```bash
# 서버 기동 (Docker 또는 로컬)
curl http://localhost:8000/health
# → {"status":"healthy","database":"connected","redis":"connected","temporal":"connected"}

# CORS 헤더 확인
curl -I -X OPTIONS http://localhost:8000/health \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET"
# → access-control-allow-origin: http://localhost:5173

# OpenAPI 문서
curl -s http://localhost:8000/docs | head -1  # → HTML
```

### 커밋: `feat: Step 4 — FastAPI 서버, 헬스체크, 미들웨어`

---

## Step 5: OAuth 인증 시스템

### 목표
Google/GitHub OAuth 로그인 + JWT 발급 + API Key 인증 구현.

### 구현 내용
- [ ] `backend/app/api/routes/auth.py` — OAuth login/callback, JWT 발급
- [ ] `backend/app/api/deps.py` — get_current_user(), get_current_user_or_api_key()
- [ ] `backend/app/services/auth_service.py` — JWT 생성/검증, API Key 생성/검증
- [ ] SessionMiddleware 등록 (OAuth state용)
- [ ] Fernet 암호화 (access_token 저장용)

### 검증 기준
```bash
# OAuth 리다이렉트 확인 (Google)
curl -s -o /dev/null -w "%{http_code} %{redirect_url}" \
  http://localhost:8000/auth/google/login
# → 307 (Google OAuth 페이지로 리다이렉트)

# JWT 검증 테스트 (유닛)
python -c "
from app.services.auth_service import create_jwt, verify_jwt
token = create_jwt({'sub': 'test-user', 'email': 'test@test.com', 'plan': 'free'})
payload = verify_jwt(token)
print(f'Verified: {payload[\"sub\"]}')
"

# API Key 생성/검증 테스트
python -c "
from app.services.auth_service import create_api_key, verify_api_key
raw_key, hashed = create_api_key()
assert raw_key.startswith('vnt_')
assert verify_api_key(raw_key, hashed)
print(f'API Key: {raw_key[:12]}...')
"

# 보호된 엔드포인트 접근 거부
curl -s -w "%{http_code}" http://localhost:8000/api/v1/jobs
# → 401
```

### 커밋: `feat: Step 5 — OAuth 인증 (JWT + API Key)`

---

## Step 6: Job CRUD API 엔드포인트

### 목표
면접 스크립트 생성 요청(Job) 관리 API 전체 구현.

### 구현 내용
- [ ] `backend/app/api/routes/jobs.py` — POST/GET/DELETE /api/v1/jobs
- [ ] `backend/app/services/job_service.py` — Job 비즈니스 로직
- [ ] 파일 업로드 (S3/LocalStack 저장)

### 검증 기준
```bash
# Job 생성 (JWT 인증 필요, 테스트용 토큰 사용)
TOKEN=$(python -c "from app.services.auth_service import create_jwt; print(create_jwt({'sub':'test','email':'t@t.com','plan':'free'}))")

curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jd_text":"React 개발자 채용","experience_level":"junior","output_language":"ko"}'
# → 201 + {"job_id": "...", "status": "pending"}

# Job 목록 조회
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/jobs
# → 200 + [{"job_id": "...", ...}]

# Job 상태 조회
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/jobs/{job_id}
# → 200 + {"job_id": "...", "status": "pending"}

# Job 삭제
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/jobs/{job_id}
# → 204
```

### 커밋: `feat: Step 6 — Job CRUD API 엔드포인트`

---

## Step 7: Temporal Worker 기본 설정

### 목표
Temporal Worker 연결, 메인 워크플로우 스켈레톤, Activity 등록 구조 확립.

### 구현 내용
- [ ] `backend/app/worker.py` — Worker 엔트리포인트 (Activity 등록)
- [ ] `backend/app/workflows/interview_workflow.py` — InterviewGenerationWorkflow 스켈레톤
- [ ] `backend/app/workflows/__init__.py`
- [ ] `backend/app/workflows/activities/__init__.py`
- [ ] Job 생성 시 Temporal Workflow 시작 연동

### 검증 기준
```bash
# Worker 기동 확인
docker compose up -d worker
docker compose logs worker | tail -5
# → "Worker started, listening on task queue: interview-generation"

# Temporal UI에서 워크플로우 확인
curl -s http://localhost:8080/api/v1/namespaces/default/workflows | python -m json.tool
# → 워크플로우 목록 또는 빈 배열

# Job 생성 → Temporal Workflow 시작 확인
TOKEN=$(...)
JOB_ID=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jd_text":"test","experience_level":"junior","output_language":"ko"}' | python -c "import sys,json;print(json.load(sys.stdin)['job_id'])")
echo "Workflow started for job: $JOB_ID"
# Temporal UI에서 실행 중인 워크플로우 확인
```

### 커밋: `feat: Step 7 — Temporal Worker + Workflow 스켈레톤`

---

## Step 8: Phase 0 — Smart Input Extraction

### 목표
입력 교차 추출 Activity 구현 (PDF/DOCX 파싱, URL 발견, LinkedIn 수집).

### 구현 내용
- [ ] `backend/app/workflows/activities/input_enrichment.py` — enrich_input()
- [ ] `backend/app/services/document_parser.py` — PDF/DOCX 텍스트 추출 (Docling + pymupdf4llm fallback)
- [ ] `backend/app/services/linkedin_service.py` — Proxycurl API 연동
- [ ] URL 교차 추출 로직 (GitHub URL, LinkedIn URL 자동 발견)
- [ ] Worker에 Activity 등록

### 검증 기준
```bash
# 문서 파서 단위 테스트
python -m pytest tests/test_document_parser.py -v
# → PDF/DOCX 텍스트 추출 성공

# Activity 단위 테스트 (mock 사용)
python -m pytest tests/test_input_enrichment.py -v
# → EnrichedInput 생성 확인, URL 교차 추출 확인

# 통합 테스트: Job 생성 → Phase 0 완료 → status=planning
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/jobs/{job_id}
# → status: "planning"
```

### 커밋: `feat: Step 8 — Phase 0 Smart Input Extraction`

---

## Step 9: Phase 1 — Planning Activity

### 목표
실행 계획 수립 Activity (GitHub 워크로드 추정, 분석 전략 결정).

### 구현 내용
- [ ] `backend/app/workflows/activities/planning.py` — create_plan()
- [ ] `backend/app/services/github_service.py` — PyGithub API 레포 메타데이터 조회
- [ ] ExecutionPlan 모델 생성

### 검증 기준
```bash
# Planning Activity 단위 테스트
python -m pytest tests/test_planning.py -v
# → ExecutionPlan 생성 확인, 레포별 분석 전략 포함

# 통합: Phase 0 → Phase 1 흐름
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/jobs/{job_id}
# → status: "analyzing" (Phase 2 진입)
```

### 커밋: `feat: Step 9 — Phase 1 Planning Activity`

---

## Step 10: Phase 2 — Parallel Analysis

### 목표
문서/코드/JD 3개 분석 Activity 병렬 실행.

### 구현 내용
- [ ] `backend/app/workflows/activities/document_analysis.py` — analyze_documents()
- [ ] `backend/app/workflows/activities/code_analysis.py` — analyze_code()
- [ ] `backend/app/workflows/activities/jd_analysis.py` — analyze_jd()
- [ ] `backend/app/services/code_analyzer.py` — PyGithub + PyDriller + AST + LLM 4-Phase
- [ ] `backend/app/services/vector_store.py` — pgvector 저장/검색
- [ ] `backend/app/services/llm_config.py` — Pydantic AI Agent + LiteLLM 초기화
- [ ] `backend/app/services/cached_llm.py` — CachedLLMService (Redis 캐시)
- [ ] Workflow에서 3개 Activity 병렬 실행 (`asyncio.gather`)
- [ ] 체크포인트 저장

### 검증 기준
```bash
# 개별 Activity 단위 테스트
python -m pytest tests/test_document_analysis.py -v
python -m pytest tests/test_code_analysis.py -v
python -m pytest tests/test_jd_analysis.py -v

# CachedLLMService 캐시 동작 확인
python -m pytest tests/test_cached_llm.py -v
# → 동일 입력 2회 호출 시 Redis 캐시 히트

# 병렬 실행 확인: 3개 Activity 동시 시작 (Temporal UI에서 확인)
# 체크포인트 저장 확인
python -c "
import asyncio
from app.services.checkpoint_store import CheckpointStore
async def test():
    store = CheckpointStore()
    cp = await store.load('test-job-id')
    print(f'Phase: {cp.phase}')
asyncio.run(test())
"
```

### 커밋: `feat: Step 10 — Phase 2 병렬 분석 (Document + Code + JD)`

---

## Step 11: Phase 3 — Question Generation

### 목표
25개 면접 질문 생성 (토픽 선정 → 병렬 생성 → 보강).

### 구현 내용
- [ ] `backend/app/workflows/activities/question_generation.py` — generate_questions()
- [ ] `backend/app/prompts/topic_selection.j2` — 토픽 선정 프롬프트
- [ ] `backend/app/prompts/question_craft.j2` — 질문 생성 프롬프트
- [ ] `backend/app/prompts/terminology.j2` — 용어 정의 프롬프트
- [ ] `backend/app/prompts/follow_up.j2` — 후속질문 프롬프트
- [ ] `backend/app/prompts/evaluation.j2` — 평가 시나리오 프롬프트
- [ ] `backend/app/prompts/interviewer_note.j2` — 면접관 노트 프롬프트
- [ ] 10개 Worker 병렬 질문 생성 로직
- [ ] 8-Agent 파이프라인 (Topic → Craft → Terminology → FollowUp → Evaluation → CodeLink → Note)

### 검증 기준
```bash
# 토픽 선정 테스트
python -m pytest tests/test_topic_selection.py -v
# → 25개 토픽, 5카테고리 × 5, 난이도 분배 확인

# 개별 질문 생성 테스트
python -m pytest tests/test_question_craft.py -v
# → InterviewQuestion 모델 필드 완전성 확인

# 전체 질문 생성 통합 테스트
python -m pytest tests/test_question_generation.py -v
# → 25개 질문, 카테고리/난이도 분배, code_reference 존재 확인

# 프롬프트 렌더링 테스트
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('app/prompts'))
tmpl = env.get_template('question_craft.j2')
print(tmpl.render(topic='React hooks', category='technical', difficulty='medium')[:200])
"
```

### 커밋: `feat: Step 11 — Phase 3 질문 생성 (25개, 8-Agent 파이프라인)`

---

## Step 12: Phase 4 — Quality Review + Finalization

### 목표
품질 검토 루프 + Supervisor 검증 + 최종 InterviewScript 조합.

### 구현 내용
- [ ] `backend/app/workflows/activities/quality_review.py` — review_questions()
- [ ] `backend/app/workflows/activities/finalization.py` — finalize_script()
- [ ] `backend/app/prompts/quality_review.j2` — 검토 프롬프트
- [ ] `backend/app/services/checkpoint_store.py` — 체크포인트 저장/복구
- [ ] `backend/app/workflows/activities/checkpoint_activities.py`
- [ ] 최대 3회 검토 루프 로직
- [ ] Hallucination 검증 (코드 참조 유효성)
- [ ] 최종 InterviewScript 조합 + DB/S3 저장

### 검증 기준
```bash
# 품질 검토 테스트
python -m pytest tests/test_quality_review.py -v
# → 중복 질문 감지, 연관성 점수, 흐름 최적화

# 전체 파이프라인 E2E (Phase 0 → 4)
python -m pytest tests/test_full_pipeline.py -v --timeout=600
# → Job 생성 → 완료, InterviewScript 25개 질문 확인

# 결과 조회 API
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/jobs/{job_id}/result
# → 200 + InterviewScript JSON (25개 질문)
```

### 커밋: `feat: Step 12 — Phase 4 품질 검토 + 최종화`

---

## Step 13: Frontend — React SPA 기본 구조

### 목표
Vite + React + Tailwind 프로젝트 초기화, 라우팅, 레이아웃.

### 구현 내용
- [ ] Vite + React + TypeScript 프로젝트 생성
- [ ] Tailwind CSS 설정
- [ ] react-router-dom 라우팅
- [ ] react-i18next 설정 (ko/en)
- [ ] 공통 레이아웃 (Navbar, Footer)
- [ ] AuthProvider (JWT 메모리 관리)

### 검증 기준
```bash
cd frontend
npm run dev  # → http://localhost:5173 접근 가능

# 빌드 성공
npm run build  # → 에러 없음

# 라우팅 확인
# / → 로그인 페이지
# /jobs → Job 목록 (인증 필요)
# /jobs/:id → Job 상태/결과
```

### 커밋: `feat: Step 13 — React SPA 기본 구조 (Vite + Tailwind + Router)`

---

## Step 14: Frontend — 로그인 + Job 생성/조회

### 목표
OAuth 로그인 UI, Job 생성 폼, Job 목록/상태 페이지.

### 구현 내용
- [ ] `LoginPage.tsx` — Google/GitHub OAuth 버튼, JWT 추출
- [ ] `CreateJobPage.tsx` — 파일 업로드, JD 입력, 옵션 선택
- [ ] `JobListPage.tsx` — 사용자 Job 목록
- [ ] `JobStatusPage.tsx` — 진행률 표시 (Phase별)
- [ ] `useAuth.ts` — JWT 관리 훅
- [ ] `useJob.ts` — Job API 호출 훅
- [ ] API 통신 유틸리티

### 검증 기준
```bash
# OAuth 리다이렉트 동작 확인 (브라우저에서)
# Google 로그인 → 콜백 → JWT 저장 → /jobs 리다이렉트

# Job 생성 폼 제출 → API 호출 → Job 생성 확인
# Job 목록에 새 Job 표시
# Job 상태 폴링 → Phase 진행 표시
```

### 커밋: `feat: Step 14 — Frontend 로그인 + Job 관리 UI`

---

## Step 15: Frontend — 면접 스크립트 뷰어

### 목표
완성된 면접 스크립트를 비개발자 면접관이 사용할 수 있는 UI로 표시.

### 구현 내용
- [ ] `ResultPage.tsx` — 메인 뷰어 (카테고리 탭)
- [ ] `QuestionCard.tsx` — 질문 카드 (접기/펼치기)
- [ ] `FollowUpBranch.tsx` — 후속질문 분기 (Expert/Mid/Low)
- [ ] `EvaluationScenario.tsx` — 평가 시나리오 (색상 구분)
- [ ] `KeywordChecklist.tsx` — 키워드 체크리스트
- [ ] `TerminologyTooltip.tsx` — 용어 설명 툴팁
- [ ] `DecisionGuide.tsx` — 의사결정 가이드 (가중 점수, 추천)
- [ ] `CandidateSummary.tsx` — 후보자 요약

### 검증 기준
```bash
# 결과 페이지 접근 → 25개 질문 표시
# 카테고리별 필터링 동작
# 질문 접기/펼치기
# 후속질문 분기 표시
# 키워드 체크 가능
# 용어 설명 툴팁 표시
# 평가 시나리오 색상 구분 (초록/주황/빨강)
# 의사결정 가이드 가중 점수 계산
```

### 커밋: `feat: Step 15 — 면접 스크립트 뷰어 UI`

---

## Step 16: 통합 테스트 + E2E

### 목표
전체 시스템 E2E 테스트, 에러 케이스, 성능 검증.

### 구현 내용
- [ ] E2E 테스트: 프론트엔드 → 백엔드 → Temporal → 결과 조회
- [ ] 에러 케이스: 잘못된 입력, 네트워크 실패, LLM 타임아웃
- [ ] 체크포인트 복구 테스트: 중간 실패 → 재시도 → 이어서 진행
- [ ] Rate Limiting 테스트
- [ ] CORS 검증
- [ ] 전체 처리 시간 측정 (목표: 25개 질문 8분 이내)

### 검증 기준
```bash
# Backend 전체 테스트
cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

# Frontend 빌드 + 린트
cd frontend && npm run build && npm run lint

# E2E (Playwright)
npx playwright test

# 성능 측정
time curl -X POST ... (Job 생성 → 완료까지 시간 측정)
```

### 커밋: `feat: Step 16 — 통합 테스트 + E2E`

---

## 진행 상태 추적

| Step | 제목 | 상태 | 커밋 |
|------|------|------|------|
| 1 | 프로젝트 스캐폴딩 + Docker | ⬜ 대기 | — |
| 2 | 데이터 모델 | ⬜ 대기 | — |
| 3 | Core 모듈 (Settings, DB) | ⬜ 대기 | — |
| 4 | FastAPI 서버 + 헬스체크 | ⬜ 대기 | — |
| 5 | OAuth 인증 | ⬜ 대기 | — |
| 6 | Job CRUD API | ⬜ 대기 | — |
| 7 | Temporal Worker | ⬜ 대기 | — |
| 8 | Phase 0 — Input Extraction | ⬜ 대기 | — |
| 9 | Phase 1 — Planning | ⬜ 대기 | — |
| 10 | Phase 2 — Parallel Analysis | ⬜ 대기 | — |
| 11 | Phase 3 — Question Generation | ⬜ 대기 | — |
| 12 | Phase 4 — Quality Review | ⬜ 대기 | — |
| 13 | Frontend 기본 구조 | ⬜ 대기 | — |
| 14 | Frontend 로그인 + Job UI | ⬜ 대기 | — |
| 15 | Frontend 스크립트 뷰어 | ⬜ 대기 | — |
| 16 | 통합 테스트 + E2E | ⬜ 대기 | — |
