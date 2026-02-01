# 05. API 명세

> RESTful API 엔드포인트 정의

---

## 개요

FastAPI 기반 REST API로, 면접 질문 생성 작업을 관리합니다.

### Base URL

| 환경 | URL |
|------|-----|
| 로컬 | `http://localhost:8000/api/v1` |
| 스테이징 | `https://api-staging.vantict.com/api/v1` |
| 프로덕션 | `https://api.vantict.com/api/v1` |

---

## 인증

### API Key 인증

```http
Authorization: Bearer <api_key>
```

```python
# backend/app/api/deps.py
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """API Key 검증 → 사용자 정보 반환"""
    api_key = credentials.credentials

    user = await get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {"user_id": user.id, "tenant_id": user.tenant_id}
```

---

## 엔드포인트

### 1. 작업 생성

면접 질문 생성 작업을 시작합니다.

```http
POST /api/v1/jobs
```

#### Request

```typescript
// Content-Type: multipart/form-data

interface CreateJobRequest {
  // 파일 업로드
  resume?: File;           // PDF, 최대 10MB
  portfolio?: File;        // DOCX, 최대 20MB

  // JSON 데이터
  data: {
    github_urls?: string[];  // GitHub 저장소 URL 목록
    jd_text: string;         // 채용공고 텍스트
    language: string;        // 출력 언어 (ko, en, ja, zh, etc.)
    question_count?: number; // 질문 개수 (기본: 10)
    options?: {
      include_code_questions?: boolean;  // 코드 기반 질문 포함
      difficulty_preference?: "easy" | "balanced" | "hard";
    };
  };
}
```

#### Response

```typescript
// 201 Created
interface CreateJobResponse {
  job_id: string;           // UUID
  session_id: string;       // UUID (서버 자동생성)
  status: "pending";
  created_at: string;       // ISO 8601
  estimated_time_seconds: number;
  links: {
    self: string;
    status: string;
    result: string;
  };
}
```

#### 예시

```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Authorization: Bearer $API_KEY" \
  -F "resume=@resume.pdf" \
  -F "portfolio=@portfolio.docx" \
  -F 'data={"github_urls":["https://github.com/user/repo"],"jd_text":"백엔드 개발자 모집...","language":"ko"}'
```

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "estimated_time_seconds": 120,
  "links": {
    "self": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000",
    "status": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/status",
    "result": "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/result"
  }
}
```

---

### 2. 작업 상태 조회

작업의 현재 진행 상황을 조회합니다.

```http
GET /api/v1/jobs/{job_id}/status
```

#### Response

```typescript
// 200 OK
interface JobStatusResponse {
  job_id: string;
  status: "pending" | "planning" | "analyzing" | "generating" | "validating" | "completed" | "failed";
  progress_percent: number;  // 0-100
  current_phase: string | null;
  phases: {
    [phase_name: string]: {
      status: "pending" | "running" | "completed" | "failed" | "skipped";
      started_at?: string;
      completed_at?: string;
      error?: string;
    };
  };
  created_at: string;
  updated_at: string;
  estimated_remaining_seconds?: number;
}
```

#### 예시

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "analyzing",
  "progress_percent": 45,
  "current_phase": "code_analysis",
  "phases": {
    "input_enrichment": {
      "status": "completed",
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:30:01Z"
    },
    "planning": {
      "status": "completed",
      "started_at": "2024-01-15T10:30:01Z",
      "completed_at": "2024-01-15T10:30:05Z"
    },
    "document_analysis": {
      "status": "completed",
      "started_at": "2024-01-15T10:30:05Z",
      "completed_at": "2024-01-15T10:30:20Z"
    },
    "code_analysis": {
      "status": "running",
      "started_at": "2024-01-15T10:30:05Z"
    },
    "jd_analysis": {
      "status": "completed",
      "started_at": "2024-01-15T10:30:05Z",
      "completed_at": "2024-01-15T10:30:15Z"
    },
    "question_generation": {
      "status": "pending"
    },
    "validation": {
      "status": "pending"
    }
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:45Z",
  "estimated_remaining_seconds": 60
}
```

---

### 3. 작업 결과 조회

완료된 작업의 결과를 조회합니다.

```http
GET /api/v1/jobs/{job_id}/result
```

#### Query Parameters

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `format` | string | 응답 형식: `json` (기본), `markdown`, `pdf` |
| `include_script` | boolean | 면접 스크립트 포함 여부 (기본: true) |

#### Response

```typescript
// 200 OK
// 02-data-models.md InterviewScript 모델과 일치
interface JobResultResponse {
  job_id: string;
  status: "completed";
  generated_at: string;              // ISO 8601
  output_language: string;

  // 후보자 요약 (CandidateSummary)
  candidate_summary: {
    name: string;
    experience_level: string;
    experience_years: number;
    key_skills: string[];
    jd_match_score: number;
    strengths: string[];
    areas_to_probe: string[];
  };

  // 질문 목록
  questions: InterviewQuestion[];

  // 면접관 가이드 (InterviewerGuide)
  interviewer_guide: {
    total_duration_minutes: number;
    question_order_rationale: string;
    tips: string[];
    warning_signs: string[];
  };

  // 용어 총집합
  full_glossary: TerminologyEntry[];

  // 생성 통계
  metadata: { [key: string]: any };
}

// 02-data-models.md InterviewQuestion 모델과 일치
interface InterviewQuestion {
  id: string;                        // q1, q2, ...
  sequence: number;                  // 순서
  topic: string;                     // 질문 주제

  // 질문 텍스트
  question_text: string;
  alternative_phrasings: string[];   // 대체 표현

  // 코드 참조
  code_reference: CodeReference | null;

  // 평가 기준
  evaluation_scenarios: EvaluationScenario;

  // 꼬리질문
  follow_ups: string[];

  // 예상 답변
  expected_answer: ExpectedAnswer;

  // 언어
  language: string;                  // "ko", "en" 등

  // 용어집
  terminology: TerminologyEntry[];

  // 메타데이터
  difficulty: "basic" | "intermediate" | "advanced";
  estimated_time_minutes: number;
  skills_assessed: string[];
}

interface CodeReference {
  file_path: string;
  line_start: number;
  line_end: number;
  code_snippet: string;
  explanation: string | null;
}

interface EvaluationScenario {
  excellent: string;                 // 우수한 답변 시나리오
  good: string;                      // 양호한 답변 시나리오
  poor: string;                      // 미흡한 답변 시나리오
}

interface ExpectedAnswer {
  core_answer: string;               // 불릿 포인트 형식
  example_script: string;            // 자연스러운 답변 예시
  code_evidence: CodeEvidence[];
  key_points: string[];
  depth_expectations: { [level: string]: string };  // {"신입": "...", "시니어": "..."}
}

interface CodeEvidence {
  file_path: string;
  snippet: string;
  relevance: string;
}

interface TerminologyEntry {
  term: string;
  definition: string;
  category: string;
  difficulty: string;
  related_terms: string[];
}
```

#### 예시 (일부)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "generated_at": "2024-01-15T10:32:00Z",
  "output_language": "ko",
  "candidate_summary": {
    "name": "김개발",
    "experience_level": "중급",
    "experience_years": 5,
    "key_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
    "jd_match_score": 0.82,
    "strengths": ["캐싱 설계 경험", "비동기 처리 이해"],
    "areas_to_probe": ["대규모 트래픽 경험", "팀 리딩 경험"]
  },
  "questions": [
    {
      "id": "q1",
      "sequence": 1,
      "topic": "Redis 캐싱 설계",
      "question_text": "GitHub 프로젝트에서 Redis 캐싱을 구현하셨는데, 캐시 무효화 전략은 어떻게 설계하셨나요?",
      "alternative_phrasings": [
        "캐시 데이터의 일관성은 어떻게 보장하셨나요?",
        "Redis 캐시 갱신 정책을 설명해 주세요."
      ],
      "code_reference": {
        "file_path": "user-service/cache.py",
        "line_start": 45,
        "line_end": 78,
        "code_snippet": "class CacheManager:\n    async def invalidate(self, key: str)...",
        "explanation": "Redis 캐시 관리 클래스에서 무효화 로직 구현"
      },
      "evaluation_scenarios": {
        "excellent": "TTL + 이벤트 기반 무효화 + 캐시 스탬피드 방지까지 설명",
        "good": "TTL과 명시적 삭제를 모두 설명",
        "poor": "캐시 무효화 개념 자체를 이해하지 못함"
      },
      "follow_ups": [
        "캐시 스탬피드가 발생하면 어떻게 대응하시겠습니까?",
        "분산 환경에서 캐시 일관성은 어떻게 유지하나요?"
      ],
      "expected_answer": {
        "core_answer": "- TTL 기반 자동 만료\n- 데이터 변경 시 명시적 캐시 삭제\n- 캐시 스탬피드 방지 (분산 락)",
        "example_script": "TTL을 설정하여 자동 만료시키고, 사용자 정보 업데이트 시 해당 키를 삭제합니다. 캐시 스탬피드 방지를 위해 분산 락을 사용합니다.",
        "code_evidence": [
          {
            "file_path": "user-service/cache.py",
            "snippet": "await redis.delete(f'user:{user_id}')",
            "relevance": "명시적 캐시 무효화 구현"
          }
        ],
        "key_points": ["TTL", "명시적 삭제", "캐시 스탬피드 방지"],
        "depth_expectations": {
          "신입": "TTL 개념과 기본 캐시 삭제 이해",
          "시니어": "분산 환경에서의 일관성 전략과 스탬피드 방지까지 설명"
        }
      },
      "language": "ko",
      "terminology": [
        {
          "term": "TTL",
          "definition": "Time To Live. 캐시 데이터의 유효 기간을 설정하는 값",
          "category": "concept",
          "difficulty": "basic",
          "related_terms": ["Cache", "Expiration", "Redis"]
        }
      ],
      "difficulty": "intermediate",
      "estimated_time_minutes": 5,
      "skills_assessed": ["Redis", "캐싱 전략", "분산 시스템"]
    }
  ],
  "interviewer_guide": {
    "total_duration_minutes": 60,
    "question_order_rationale": "기술적 난이도 순서로 배치하여 후보자가 점진적으로 몰입할 수 있도록 구성",
    "tips": ["코드 기반 질문에서는 실제 구현 의도를 물어볼 것", "꼬리질문으로 깊이를 확인할 것"],
    "warning_signs": ["구체적 사례 없이 일반론만 답변", "본인 코드에 대한 설명이 불명확"]
  },
  "full_glossary": [
    {
      "term": "TTL",
      "definition": "Time To Live. 캐시 데이터의 유효 기간을 설정하는 값으로, 설정된 시간이 지나면 자동으로 삭제됩니다.",
      "category": "concept",
      "difficulty": "basic",
      "related_terms": ["Cache", "Expiration", "Redis"]
    }
  ],
  "metadata": {
    "quality_score": 0.87,
    "sources_used": ["resume.pdf", "portfolio.docx", "https://github.com/user/repo"],
    "total_questions": 10,
    "token_usage": {"prompt": 15000, "completion": 8000}
  }
}
```

---

### 4. 작업 목록 조회

인증된 사용자의 작업 히스토리를 조회합니다. `user_id`로 자동 필터되어 본인 작업만 반환됩니다.

```http
GET /api/v1/jobs
```

#### Query Parameters

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `status` | string | - | 상태 필터 |
| `session_id` | string | - | 특정 세션의 작업만 조회 |
| `limit` | number | 20 | 페이지 크기 (최대 100) |
| `offset` | number | 0 | 오프셋 |
| `sort` | string | `-created_at` | 정렬 기준 |

#### Response

```typescript
// 200 OK
interface JobListResponse {
  items: JobSummary[];
  total: number;
  limit: number;
  offset: number;
}

interface JobSummary {
  job_id: string;
  session_id: string;
  status: string;
  position: string | null;
  candidate_name: string | null;
  question_count: number | null;
  created_at: string;
  completed_at: string | null;
}
```

---

### 5. 작업 취소

진행 중인 작업을 취소합니다.

```http
DELETE /api/v1/jobs/{job_id}
```

#### Response

```typescript
// 200 OK
interface CancelJobResponse {
  job_id: string;
  status: "cancelled";
  cancelled_at: string;
}
```

---

### 6. 작업 재시작 (Retry)

실패한 작업을 특정 단계부터 재시작합니다. 이전 단계 결과는 캐시에서 로드됩니다.

```http
POST /api/v1/jobs/{job_id}/retry
```

#### Request Body

```typescript
interface RetryRequest {
  from_step?: string;    // 재시작 지점 (null이면 자동 감지)
  force_rerun?: boolean; // true면 캐시 무시하고 재실행 (기본: false)
}
```

**사용 가능한 step 값:**
`input_enrichment`, `plan`, `document_analysis`, `code_analysis`, `jd_analysis`, `select_topics`, `craft_questions`, `review_quality`, `finalize`

#### Response

```typescript
// 200 OK
interface RetryResponse {
  job_id: string;
  status: "retrying";
  resume_from: string;      // 재시작 지점
  skipped_steps: string[];  // 건너뛴 단계 (캐시 사용)
  cached_steps: string[];   // 캐시에 있는 단계
}
```

#### 예시

```bash
# 자동 감지 (마지막 실패 지점부터)
curl -X POST "http://localhost:8000/api/v1/jobs/${JOB_ID}/retry" \
  -H "Authorization: Bearer $API_KEY"

# 특정 단계부터 재시작
curl -X POST "http://localhost:8000/api/v1/jobs/${JOB_ID}/retry" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"from_step": "craft_questions"}'
```

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "retrying",
  "resume_from": "craft_questions",
  "skipped_steps": ["input_enrichment", "plan", "document_analysis", "code_analysis", "jd_analysis", "select_topics"],
  "cached_steps": ["input_enrichment", "plan", "select_topics"]
}
```

---

### 7. 체크포인트 상태 조회

작업의 단계별 체크포인트 상태를 조회합니다.

```http
GET /api/v1/jobs/{job_id}/checkpoints
```

#### Response

```typescript
// 200 OK
interface CheckpointStatusResponse {
  job_id: string;
  steps: {
    name: string;
    status: "completed" | "pending";
  }[];
  resume_point: string | null;  // 다음 실행할 단계
  total_steps: number;
  completed_count: number;
}
```

#### 예시

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "steps": [
    {"name": "input_enrichment", "status": "completed"},
    {"name": "plan", "status": "completed"},
    {"name": "document_analysis", "status": "completed"},
    {"name": "code_analysis", "status": "completed"},
    {"name": "jd_analysis", "status": "completed"},
    {"name": "select_topics", "status": "completed"},
    {"name": "craft_questions", "status": "pending"},
    {"name": "review_quality", "status": "pending"},
    {"name": "finalize", "status": "pending"}
  ],
  "resume_point": "craft_questions",
  "total_steps": 9,
  "completed_count": 6
}
```

---

### 8. 실시간 상태 업데이트 (WebSocket)

작업 상태를 실시간으로 수신합니다.

```
WS /api/v1/jobs/{job_id}/ws?token=<api_key>
```

> **인증**: 쿼리 파라미터 `token`으로 API Key 전달. 유효하지 않은 토큰 시 즉시 연결 종료 (4001 Unauthorized).
> 해당 `job_id`의 소유자(user_id)가 아닌 경우에도 연결 거부.

#### 메시지 형식

```typescript
// 서버 → 클라이언트
interface StatusUpdate {
  type: "status_update";
  data: {
    job_id: string;
    status: string;
    progress_percent: number;
    current_phase: string | null;
    message?: string;
  };
}

interface PhaseComplete {
  type: "phase_complete";
  data: {
    phase: string;
    status: "completed" | "failed";
    duration_seconds: number;
  };
}

interface JobComplete {
  type: "job_complete";
  data: {
    job_id: string;
    status: "completed" | "failed";
    result_url?: string;
    error?: string;
  };
}
```

#### 예시 (JavaScript)

```javascript
const ws = new WebSocket(`ws://localhost:8000/api/v1/jobs/${jobId}/ws?token=${apiKey}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'status_update':
      console.log(`Progress: ${message.data.progress_percent}%`);
      break;
    case 'phase_complete':
      console.log(`Phase ${message.data.phase} completed`);
      break;
    case 'job_complete':
      console.log('Job finished!', message.data);
      ws.close();
      break;
  }
};
```

---

## 에러 응답

### 에러 형식

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any;
  };
  request_id: string;
}
```

### 에러 코드

| HTTP 코드 | 에러 코드 | 설명 |
|-----------|-----------|------|
| 400 | `INVALID_INPUT` | 입력 데이터 유효성 검증 실패 |
| 400 | `FILE_TOO_LARGE` | 파일 크기 초과 |
| 400 | `UNSUPPORTED_FILE_TYPE` | 지원하지 않는 파일 형식 |
| 401 | `UNAUTHORIZED` | 인증 실패 |
| 403 | `FORBIDDEN` | 권한 없음 |
| 404 | `JOB_NOT_FOUND` | 작업을 찾을 수 없음 |
| 409 | `JOB_ALREADY_COMPLETED` | 이미 완료된 작업 |
| 422 | `GITHUB_ACCESS_DENIED` | GitHub 저장소 접근 불가 |
| 429 | `RATE_LIMIT_EXCEEDED` | 요청 한도 초과 |
| 500 | `INTERNAL_ERROR` | 내부 서버 오류 |
| 503 | `SERVICE_UNAVAILABLE` | 서비스 일시 중단 |

### 에러 예시

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "JD 텍스트는 필수입니다",
    "details": {
      "field": "jd_text",
      "constraint": "required"
    }
  },
  "request_id": "req-abc123"
}
```

---

## Rate Limiting

| 플랜 | 요청 한도 | 동시 작업 |
|------|-----------|-----------|
| Free | 10 req/min | 1 |
| Pro | 60 req/min | 5 |
| Enterprise | 300 req/min | 20 |

### Rate Limit 헤더

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1705312800
```

---

## API 라우터 구현

```python
# backend/app/api/v1/jobs.py
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse
from temporalio.client import Client
import json

router = APIRouter(prefix="/jobs", tags=["jobs"])


ALLOWED_RESUME_TYPES = {".pdf"}
ALLOWED_PORTFOLIO_TYPES = {".pdf", ".docx"}
MAX_RESUME_SIZE = 10 * 1024 * 1024   # 10MB
MAX_PORTFOLIO_SIZE = 20 * 1024 * 1024  # 20MB


def _validate_upload(file: UploadFile, allowed_exts: set, max_size: int) -> None:
    """파일 확장자 + 크기 검증"""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(400, f"Unsupported file type: {ext}")
    # Content-Length가 없을 수 있으므로 실제 read 후 검증은 upload_file 내부에서 수행
    if file.size and file.size > max_size:
        raise HTTPException(400, f"File too large: {file.size} bytes (max {max_size})")


@router.post("", status_code=201)
async def create_job(
    resume: UploadFile | None = File(None),
    portfolio: UploadFile | None = File(None),
    data: str = Form(...),
    auth: dict = Depends(verify_api_key),
    temporal: Client = Depends(get_temporal_client),
):
    """면접 질문 생성 작업 생성"""
    # 입력 파싱
    try:
        input_data = json.loads(data)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON in data field")

    # 유효성 검증
    if not input_data.get("jd_text"):
        raise HTTPException(400, "jd_text is required")

    # 파일 검증
    if resume:
        _validate_upload(resume, ALLOWED_RESUME_TYPES, MAX_RESUME_SIZE)
    if portfolio:
        _validate_upload(portfolio, ALLOWED_PORTFOLIO_TYPES, MAX_PORTFOLIO_SIZE)

    # 작업 ID + 세션 ID 자동 생성
    job_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    user_id = auth["user_id"]

    # 파일 업로드 (Storage 추상화 — local/R2/S3)
    file_urls = {}
    if resume:
        file_urls["resume"] = await upload_file(job_id, resume)
    if portfolio:
        file_urls["portfolio"] = await upload_file(job_id, portfolio)

    # raw_input 구성 (Phase 0 enrich_input이 이 dict를 받아 enriched_input 생성)
    raw_input = {
        "resume_url": file_urls.get("resume"),
        "portfolio_url": file_urls.get("portfolio"),
        "github_urls": input_data.get("github_urls", []),
        "jd_text": input_data["jd_text"],
        "language_config": {
            "output_language": input_data.get("language", "ko"),
        },
        "question_count": input_data.get("question_count", 10),
        "options": input_data.get("options", {}),
    }

    # Temporal 워크플로우 시작
    await temporal.start_workflow(
        InterviewGenerationWorkflow.run,
        args=[job_id, raw_input],
        id=f"interview-{job_id}",
        task_queue="interview-generation",
    )

    # DB에 작업 저장 (user_id, session_id 포함)
    await save_job(
        job_id=job_id,
        session_id=session_id,
        user_id=user_id,
        tenant_id=auth.get("tenant_id"),
        input_data=raw_input,
    )

    return {
        "job_id": job_id,
        "session_id": session_id,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "estimated_time_seconds": estimate_time(input_data),
        "links": {
            "self": f"/api/v1/jobs/{job_id}",
            "status": f"/api/v1/jobs/{job_id}/status",
            "result": f"/api/v1/jobs/{job_id}/result",
        },
    }


@router.get("/{job_id}/status")
async def get_job_status(
    job_id: str,
    auth: dict = Depends(verify_api_key),
    redis: Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    """작업 상태 조회 (소유자 검증)"""
    # 소유자 검증
    job = await db.get(Job, job_id)
    if not job or job.user_id != auth["user_id"]:
        raise HTTPException(404, "Job not found")

    state = await redis.hgetall(f"job:{job_id}:state")

    return {
        "job_id": job_id,
        "status": state.get("status", job.status),
        "progress_percent": int(state.get("progress_percent", 0)),
        "current_phase": state.get("current_phase") or None,
        "phases": json.loads(state.get("phases", "{}")),
        "updated_at": state.get("updated_at"),
    }


@router.get("/{job_id}/result")
async def get_job_result(
    job_id: str,
    format: str = "json",
    include_script: bool = True,
    auth: dict = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """작업 결과 조회 (소유자 검증)"""
    job = await db.get(Job, job_id)
    if not job or job.user_id != auth["user_id"]:
        raise HTTPException(404, "Job not found")

    if job.status != "completed":
        raise HTTPException(400, f"Job is not completed: {job.status}")

    result = {**job.result}  # 원본 mutation 방지

    if not include_script:
        result.pop("interview_script", None)

    if format == "markdown":
        return StreamingResponse(
            generate_markdown(result),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=interview-{job_id}.md"},
        )
    elif format == "pdf":
        return StreamingResponse(
            generate_pdf(result),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=interview-{job_id}.pdf"},
        )

    return result
```

---

## 다음 단계

이 문서들을 기반으로 개발을 시작할 수 있습니다:

1. **백엔드 구현**: FastAPI 앱 구조 설정
2. **Temporal 워크플로우**: Activity 구현
3. **프론트엔드**: Next.js 앱 구축
4. **통합 테스트**: E2E 테스트 작성
