---
name: arch-api
description: REST API 엔드포인트 구현. FastAPI 라우트, Job 관리, 상태 조회, 헬스체크 관련 구현 시 사용.
argument-hint: [endpoint] (예: create-job, get-status, retry, health)
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# API Architecture Skill

FastAPI REST API 엔드포인트 구현 가이드.

## 반드시 먼저 읽을 문서
1. `docs/architecture/05-api-spec.md` — 전체 API 명세
2. `docs/architecture/02-data-models.md` — 요청/응답 모델

## API 엔드포인트 목록

### Job Lifecycle
| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/v1/jobs` | 면접 스크립트 생성 요청 |
| GET | `/api/v1/jobs/{id}` | Job 상태 조회 |
| GET | `/api/v1/jobs/{id}/result` | 완료된 결과 조회 |
| POST | `/api/v1/jobs/{id}/retry` | 실패 Job 재시도 |
| GET | `/api/v1/jobs/{id}/checkpoint` | 체크포인트 조회 |
| DELETE | `/api/v1/jobs/{id}` | Job 삭제 |
| GET | `/api/v1/jobs` | 사용자 Job 목록 |

### Auth (별도 스킬: /arch-auth)
| Method | Path | 설명 |
|--------|------|------|
| GET | `/auth/{provider}/login` | OAuth 시작 |
| GET | `/auth/{provider}/callback` | OAuth 콜백 |

### Utility
| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| POST | `/api/v1/translate` | on-demand 번역 |

## 구현 패턴

### Job 생성 (POST /api/v1/jobs)
```python
@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    request: CreateJobRequest,
    user: User = Depends(get_current_user),
    temporal: TemporalClient = Depends(get_temporal_client),
):
    job_id = str(uuid4())
    # 1. DB에 Job 레코드 생성 (status=PENDING)
    # 2. Temporal Workflow 시작
    # 3. JobResponse 반환
```

### 에러 응답 형식
```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job not found",
    "details": {}
  }
}
```

### 예외 계층
- `VantictBaseError` → `JobNotFoundError`, `InvalidInputError`, `WorkflowError`
- FastAPI exception handler로 일관된 에러 응답

## 파일 배치
```
backend/app/api/routes/jobs.py     — Job CRUD 라우트
backend/app/api/routes/auth.py     — OAuth 라우트
backend/app/api/routes/translate.py — 번역 라우트
backend/app/api/deps.py            — 공통 의존성
backend/app/api/health.py          — 헬스체크
backend/app/exceptions.py          — 예외 계층
backend/app/models/job.py          — Job 모델
```

## 규칙
- 모든 라우트에 타입 힌트 + Pydantic 모델 필수
- `user_id` 소유자 모델: 본인 Job만 접근 가능
- 파일 업로드: `UploadFile` + S3 저장
- Temporal Workflow ID = Job ID (1:1 매핑)
