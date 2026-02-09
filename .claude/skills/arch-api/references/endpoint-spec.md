# API Endpoint Specification Reference

전체 API 엔드포인트 상세 명세.

## Job Lifecycle Endpoints

### POST /api/v1/jobs — Job 생성
```python
@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    request: CreateJobRequest,
    user: User = Depends(get_current_user),
    temporal: TemporalClient = Depends(get_temporal_client),
):
    job_id = str(uuid4())
    # 1. DB에 Job 레코드 생성 (status=PENDING)
    # 2. S3에 파일 업로드 (resume, portfolio)
    # 3. Temporal Workflow 시작 (workflow_id = job_id)
    # 4. JobResponse 반환
```

**Request Body** (multipart/form-data):
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| job_description | string | O | 채용공고 텍스트 |
| experience_level | enum | O | junior/mid/senior/cto |
| output_language | enum | O | ko/en |
| num_questions | int | X | 5-25 (기본 20) |
| resume | UploadFile | X | PDF/DOCX |
| portfolio | UploadFile | X | PDF/DOCX |
| linkedin_url | string | X | LinkedIn 프로필 URL |
| github_urls | list[str] | X | GitHub 레포 URL 목록 |

### GET /api/v1/jobs/{id} — 상태 조회
```json
{
  "id": "uuid",
  "status": "pending|running|completed|failed",
  "progress": {"phase": 2, "phase_name": "analysis", "percent": 45},
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:05:00Z"
}
```

### GET /api/v1/jobs/{id}/result — 결과 조회
- status=completed일 때만 200 반환
- 4탭 데이터 전체 (intel_brief, deep_analysis, live_interview, decision)

### POST /api/v1/jobs/{id}/retry — 재시도
- status=failed일 때만 허용
- 마지막 checkpoint부터 재개

### GET /api/v1/jobs/{id}/checkpoint — 체크포인트 조회
- 현재 진행 단계 및 완료된 Phase 목록

### DELETE /api/v1/jobs/{id} — Job 삭제
- 소유자만 삭제 가능
- 실행 중이면 Temporal Workflow도 취소

### GET /api/v1/jobs — 목록 조회
- 현재 사용자의 Job 목록 (user_id 필터)
- 페이지네이션: `?page=1&per_page=20`

## Auth Endpoints

### GET /auth/{provider}/login
- OAuth 시작 (Google)
- redirect_uri 동적 감지 (X-Forwarded-Proto 보존)

### GET /auth/{provider}/callback
- OAuth 콜백 처리
- JWT 토큰 발급 → 프론트엔드 리다이렉트

## Utility Endpoints

### GET /health
```json
{"status": "ok", "version": "4.0.0", "services": {"db": "ok", "redis": "ok", "temporal": "ok"}}
```

### POST /api/v1/translate
- on-demand 번역 (ko ↔ en)

## Error Response Format

```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job not found",
    "details": {"job_id": "uuid"}
  }
}
```

## Exception Hierarchy

```
VantictBaseError
├── JobNotFoundError (404)
├── InvalidInputError (400)
├── WorkflowError (500)
├── AuthenticationError (401)
└── ForbiddenError (403)
```
