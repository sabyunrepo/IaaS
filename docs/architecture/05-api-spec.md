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

### 이중 인증 구조

| 경로 | 인증 방식 | 토큰 형태 | 용도 |
|------|----------|----------|------|
| Frontend (React SPA) | OAuth → FastAPI JWT | `Authorization: Bearer <jwt>` | 사용자 웹 로그인 |
| Programmatic API | API Key | `Authorization: Bearer vnt_xxx` | 외부 시스템 연동 |

### OAuth 엔드포인트 (FastAPI)

FastAPI가 OAuth를 직접 처리. React SPA는 리다이렉트만 수행.

```python
# backend/app/main.py — SessionMiddleware 필수 (OAuth state 저장용)
from starlette.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)
```

```python
# backend/app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.github import GitHubOAuth2
import httpx
import jwt
import secrets
from datetime import datetime, timedelta, UTC
from cryptography.fernet import Fernet

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

google_client = GoogleOAuth2(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
)
github_client = GitHubOAuth2(
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
)

PROVIDERS = {"google": google_client, "github": github_client}
FRONTEND_URL = settings.FRONTEND_URL  # http://localhost:5173

# OAuth access_token 암호화 (DB 저장 시)
_fernet = Fernet(settings.OAUTH_TOKEN_ENCRYPTION_KEY)  # 32-byte base64 key


# ── Step 1: 로그인 시작 (React → FastAPI → OAuth Provider) ──

@router.get("/login/{provider}")
async def oauth_login(provider: str, request: Request):
    """OAuth 로그인 시작 → Provider 동의 화면으로 리다이렉트"""
    if provider not in PROVIDERS:
        raise HTTPException(400, f"Unsupported provider: {provider}")

    client = PROVIDERS[provider]
    callback_url = f"{settings.BACKEND_URL}/api/v1/auth/callback/{provider}"

    # CSRF 방지: state 파라미터 생성 → 세션에 저장
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state

    authorization_url = await client.get_authorization_url(
        callback_url,
        state=state,
        scope=["openid", "email", "profile"] if provider == "google"
              else ["user:email", "read:user"],
    )
    return RedirectResponse(authorization_url)


# ── Step 2: OAuth 콜백 (Provider → FastAPI → React) ──

@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str, code: str, state: str,
    request: Request, db: AsyncSession = Depends(get_db),
):
    """OAuth 콜백 처리 → JWT 발급 → React로 리다이렉트"""
    if provider not in PROVIDERS:
        raise HTTPException(400, f"Unsupported provider: {provider}")

    # CSRF 검증: state 파라미터 일치 확인
    expected_state = request.session.pop("oauth_state", None)
    if not expected_state or state != expected_state:
        raise HTTPException(400, "Invalid OAuth state — possible CSRF attack")

    client = PROVIDERS[provider]
    callback_url = f"{settings.BACKEND_URL}/api/v1/auth/callback/{provider}"

    # 1. code → access_token 교환
    token = await client.get_access_token(code, callback_url)
    access_token = token["access_token"]

    # 2. 사용자 정보 조회
    user_info = await _fetch_user_info(provider, access_token)
    if not user_info.get("email"):
        return RedirectResponse(f"{FRONTEND_URL}/auth/error?reason=no_email")

    # 3. DB upsert (트랜잭션)
    async with db.begin():
        # users upsert
        result = await db.execute(
            text("""
                INSERT INTO users (email, name, image)
                VALUES (:email, :name, :image)
                ON CONFLICT (email) DO UPDATE SET
                    name = :name, image = :image, updated_at = NOW()
                RETURNING id, plan
            """),
            {"email": user_info["email"], "name": user_info["name"], "image": user_info["image"]},
        )
        row = result.first()
        user_id, plan = str(row.id), row.plan

        # oauth_accounts upsert
        await db.execute(
            text("""
                INSERT INTO oauth_accounts (user_id, provider, provider_account_id, access_token, token_type, scope)
                VALUES (:user_id, :provider, :provider_account_id, :access_token, :token_type, :scope)
                ON CONFLICT (provider, provider_account_id) DO UPDATE SET
                    access_token = :access_token
            """),
            {
                "user_id": user_id, "provider": provider,
                "provider_account_id": user_info["provider_id"],
                "access_token": _fernet.encrypt(access_token.encode()).decode(),
                "token_type": "bearer", "scope": token.get("scope", ""),
            },
        )

    # 4. 자체 JWT 발급
    jwt_token = _create_jwt(user_id=user_id, email=user_info["email"], plan=plan)

    # 5. React SPA로 리다이렉트 (JWT를 URL fragment로 전달 — 서버에 노출 안됨)
    return RedirectResponse(f"{FRONTEND_URL}/auth/callback#token={jwt_token}")


# ── Step 3: 현재 사용자 정보 ──

@router.get("/me")
async def get_me(user: dict = Depends(verify_user)):
    """현재 로그인 사용자 정보"""
    return user


# ── 헬퍼 함수 ──

async def _fetch_user_info(provider: str, access_token: str) -> dict:
    """OAuth access_token으로 사용자 정보 조회"""
    async with httpx.AsyncClient() as client:
        if provider == "google":
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            data = resp.json()
            return {
                "email": data["email"],
                "name": data.get("name"),
                "image": data.get("picture"),
                "provider_id": data["id"],
            }
        elif provider == "github":
            resp = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            data = resp.json()
            # GitHub 이메일 비공개 대응: /user/emails API로 primary email 조회
            email = data.get("email")
            if not email:
                emails_resp = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                emails = emails_resp.json()
                primary = next((e for e in emails if e["primary"] and e["verified"]), None)
                email = primary["email"] if primary else None
            return {
                "email": email,
                "name": data.get("name") or data.get("login"),
                "image": data.get("avatar_url"),
                "provider_id": str(data["id"]),
            }


def _create_jwt(user_id: str, email: str, plan: str) -> str:
    """자체 JWT 발급 (HS256)"""
    payload = {
        "sub": user_id,
        "email": email,
        "plan": plan,
        "exp": datetime.now(UTC) + timedelta(hours=24),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
```

### React SPA 연동

```typescript
// frontend/src/lib/auth.ts

const API_URL = import.meta.env.VITE_API_URL  // http://localhost:8000

// OAuth 로그인 시작 (새 창 또는 리다이렉트)
export function loginWith(provider: "google" | "github") {
  window.location.href = `${API_URL}/api/v1/auth/login/${provider}`
}

// /auth/callback 페이지에서 JWT 추출 후 URL에서 즉시 제거
export function extractTokenFromCallback(): string | null {
  const hash = window.location.hash  // #token=eyJhbG...
  const match = hash.match(/token=([^&]+)/)
  if (match) {
    // 브라우저 히스토리에서 토큰 제거 (보안)
    window.history.replaceState(null, "", window.location.pathname)
    return match[1]
  }
  return null
}

// JWT를 메모리에 저장 (XSS 대응: localStorage 사용 안 함)
let accessToken: string | null = null

export function setToken(token: string) { accessToken = token }
export function getToken() { return accessToken }
export function clearToken() { accessToken = null }

// API 호출 헬퍼
export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken()
  return fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
}
```

### Bearer 토큰 검증 (FastAPI)

JWT와 API Key를 자동 판별:

```python
# backend/app/api/deps.py
import jwt
import hashlib
from fastapi import Security, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Bearer 토큰 검증 (JWT 또는 API Key 자동 판별)

    - JWT: FastAPI OAuth에서 발급한 토큰 (프론트엔드)
    - API Key: vnt_ 접두사 (프로그래밍 API)
    """
    token = credentials.credentials

    # API Key 판별 (vnt_ 접두사)
    if token.startswith("vnt_"):
        return await _verify_api_key(token, db)

    # JWT 검증
    return _verify_jwt(token)


def _verify_jwt(token: str) -> dict:
    """FastAPI 발급 JWT 검증 (HS256)"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return {"user_id": payload["sub"], "email": payload["email"], "plan": payload.get("plan", "free")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def _verify_api_key(api_key: str, db: AsyncSession) -> dict:
    """API Key 검증 → 사용자 정보 반환"""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    result = await db.execute(
        select(User, APIKey)
        .join(APIKey, User.id == APIKey.user_id)
        .where(APIKey.key_hash == key_hash, APIKey.is_active == True, User.is_active == True)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")

    user, api_key_record = row
    api_key_record.last_used_at = datetime.now(UTC)
    await db.commit()

    return {"user_id": str(user.id), "email": user.email, "plan": user.plan}
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
  // 파일 업로드 (S3에 저장 후 path 전달)
  resume?: File;             // PDF, 최대 10MB
  portfolio?: File;          // PDF/DOCX, 최대 20MB
  cover_letter?: File;       // PDF/DOCX, 최대 5MB

  // JSON 데이터
  data: {
    // URL 입력 (직접 입력 또는 이력서/포트폴리오에서 자동 추출)
    linkedin_url?: string;     // LinkedIn 프로필 URL (Bright Data로 수집)
    github_urls?: string[];    // GitHub 저장소 URL 목록

    // 필수 입력
    jd_text: string;           // 채용공고 텍스트 (최소 50자)
    experience_level: "신입" | "주니어" | "미들" | "시니어" | "CTO/VP";

    // 옵션
    language_config?: {
      output_language?: string;            // 출력 언어 (기본: "ko")
      terminology_languages?: string[];    // 용어집 언어 (기본: ["ko", "en"])
    };
    max_questions?: number;    // 생성할 질문 수 (기본: 25, 5~25)
    include_expected_answers?: boolean;  // 예상 답변 포함 (기본: true)
    focus_areas?: string[];    // 집중할 기술 영역

    callback_url?: string;     // 완료 시 호출할 웹훅 URL
    priority?: "low" | "normal" | "high";  // 우선순위 (기본: normal)
  };
}
```

#### Response

```typescript
// 201 Created
interface CreateJobResponse {
  job_id: string;           // UUID
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
  -F "cover_letter=@cover_letter.pdf" \
  -F 'data={"linkedin_url":"https://linkedin.com/in/user","github_urls":["https://github.com/user/repo"],"jd_text":"백엔드 개발자 모집...","experience_level":"시니어","max_questions":25}'
```

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
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
  status: "pending" | "enriching" | "planning" | "analyzing" | "generating" | "reviewing" | "finalizing" | "completed" | "failed" | "cancelled";
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

  // 질문 목록 (25문항, 5카테고리 × 5개)
  questions: InterviewQuestion[];

  // 면접관 가이드 (InterviewerGuide)
  interviewer_guide: {
    total_duration_minutes: number;
    question_order_rationale: string;
    tips: string[];
    warning_signs: string[];
  };

  // 의사결정 가이드 (Decision Tab 데이터)
  decision_guide: { [key: string]: any };

  // 용어 총집합
  full_glossary: TerminologyEntry[];

  // 생성 통계
  metadata: { [key: string]: any };
}

// 02-data-models.md InterviewQuestion 모델과 일치
interface InterviewQuestion {
  id: string;                        // q1, q2, ...
  sequence: number;                  // 순서
  category: QuestionCategory;        // 질문 카테고리
  topic: string;                     // 질문 주제
  difficulty: "Easy" | "Medium" | "Hard";

  // 질문 본체
  question_text: string;
  context_bridge: string;            // 상황 설정 (면접관이 읽어줄 맥락)
  alternative_phrasings: string[];   // 대체 표현

  // 면접관 가이드
  why_matters: string;               // 이 질문이 중요한 이유
  listen_for: string;                // 답변에서 들어야 할 것

  // 코드 참조 (확장)
  code_reference: CodeReference | null;

  // 채점 루브릭 (3단계: expert/mid/low)
  evaluation_scenarios: EvaluationScenario;

  // 꼬리질문 (답변 수준별 분기)
  follow_ups: FollowUpQuestion[];

  // 예상 답변 (키워드 포함)
  expected_answer: ExpectedAnswer;

  // 용어집
  terminology: TerminologyEntry[];

  // 메타데이터
  language: string;                  // "ko", "en" 등
  estimated_time_minutes: number;
  skills_assessed: string[];

  // 면접관 노트 (비기술 면접관용)
  interviewer_note?: {
    business_interpretation: string;  // 비즈니스적으로 무엇을 확인하는지
    daily_analogy: string;            // 일상 비유로 설명
    level_expectations?: Record<string, string>;  // 직급별 기대 수준
  };

  // 질문 생성 근거
  generation_rationale: string;      // 왜 이 질문이 선택되었는지
  jd_competency_link: string;        // JD 역량 요구사항과의 연결
}

type QuestionCategory = "role_fit" | "technical_depth" | "execution_ownership" | "communication" | "risk_flags";

interface CodeReference {
  repo_name: string;                 // "username/project-name"
  file_path: string;                 // "src/services/auth.py"
  line_range: string;                // "L45-L67"
  permalink: string;                 // GitHub permalink URL
  snippet: string;                   // 코드 스니펫
  explanation: string;               // 이 코드가 왜 중요한지
  plain_language_summary: string;    // 비개발자용 설명
}

interface EvaluationScenarioLevel {
  description: string;               // 이 수준의 답변 시나리오
  indicators: string[];              // 이 수준을 나타내는 구체적 지표
  score: number;                     // 점수 (expert: 15-25, mid: 8-12, low: -10~5)
}

interface EvaluationScenario {
  expert: EvaluationScenarioLevel;   // 🟢 우수
  mid: EvaluationScenarioLevel;      // 🟡 보통
  low: EvaluationScenarioLevel;      // 🔴 미흡
}

interface FollowUpScoring {
  good: string;                      // 좋은 답변 시나리오
  good_score: number;                // +5 ~ +10
  poor: string;                      // 부족한 답변 시나리오
  poor_score: number;                // 0 ~ -5
}

interface FollowUpQuestion {
  id: string;                        // "q1-f1"
  trigger_level: "expert" | "mid" | "low" | "any";
  question_text: string;
  why_matters: string;
  listen_for: string;
  scoring: FollowUpScoring;
  terminology: TerminologyEntry[];
}

interface AnswerKeyword {
  keyword: string;                   // "Strangler Fig Pattern"
  importance: "must" | "good_to_have";
  explanation: string;               // 왜 이 키워드가 중요한지
}

interface ExpectedAnswer {
  core_answer: string;               // 불릿 포인트 형식
  example_script: string;            // 자연스러운 답변 예시
  answer_keywords: AnswerKeyword[];  // 핵심 키워드
  depth_expectations: { [level: string]: string };
  code_evidence: CodeEvidence[];
  key_points: string[];
}

interface CodeEvidence {
  file_path: string;
  line_start: number;
  line_end: number;
  code_snippet: string;
  explanation: string;
}

interface TerminologyEntry {
  term: string;                      // "Strangler Fig Pattern"
  definition: string;                // 전문 정의
  plain_language_explanation: string; // 비개발자용 쉬운 설명
  context: string;                   // 이 질문에서 왜 등장하는지
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
      "category": "technical_depth",
      "topic": "Redis 캐싱 설계",
      "difficulty": "Medium",
      "question_text": "GitHub 프로젝트에서 Redis 캐싱을 구현하셨는데, 캐시 무효화 전략은 어떻게 설계하셨나요?",
      "context_bridge": "이력서에서 Redis 기반 캐싱 시스템을 설계하신 경험을 보았습니다. 해당 프로젝트의 코드도 확인했는데요,",
      "alternative_phrasings": [
        "캐시 데이터의 일관성은 어떻게 보장하셨나요?",
        "Redis 캐시 갱신 정책을 설명해 주세요."
      ],
      "why_matters": "캐시 무효화는 분산 시스템에서 가장 어려운 문제 중 하나입니다. 이 질문으로 후보자가 단순히 캐시를 사용한 것인지, 아니면 일관성 문제까지 고민한 것인지 확인합니다.",
      "listen_for": "TTL 전략, 이벤트 기반 무효화, 캐시 스탬피드 방지 중 하나라도 언급하는지 확인",
      "code_reference": {
        "repo_name": "user/user-service",
        "file_path": "src/cache.py",
        "line_range": "L45-L78",
        "permalink": "https://github.com/user/user-service/blob/abc123/src/cache.py#L45-L78",
        "snippet": "class CacheManager:\n    async def invalidate(self, key: str)...",
        "explanation": "Redis 캐시 관리 클래스에서 무효화 로직 구현",
        "plain_language_summary": "이 코드는 저장된 임시 데이터를 지우는 기능입니다. 데이터가 바뀌었을 때 옛날 데이터가 보이지 않도록 관리합니다."
      },
      "evaluation_scenarios": {
        "expert": {
          "description": "TTL + 이벤트 기반 무효화 + 캐시 스탬피드 방지까지 설명",
          "indicators": ["TTL 전략 설명", "이벤트 기반 무효화 패턴", "분산 락 활용", "Cache-Aside 패턴 이해"],
          "score": 20
        },
        "mid": {
          "description": "TTL과 명시적 삭제를 모두 설명",
          "indicators": ["TTL 설정 경험", "명시적 캐시 삭제 구현"],
          "score": 10
        },
        "low": {
          "description": "캐시 무효화 개념 자체를 이해하지 못함",
          "indicators": ["캐시 무효화 개념 부재", "일관성 문제 인식 없음"],
          "score": 0
        }
      },
      "follow_ups": [
        {
          "id": "q1-f1",
          "trigger_level": "expert",
          "question_text": "캐시 스탬피드가 발생하면 어떻게 대응하시겠습니까?",
          "why_matters": "실제 대규모 트래픽에서의 경험을 확인",
          "listen_for": "분산 락, 확률적 조기 갱신 등 구체적 패턴",
          "scoring": {
            "good": "구체적 패턴과 실제 경험 사례 제시",
            "good_score": 8,
            "poor": "개념만 알고 실무 적용 경험 없음",
            "poor_score": 0
          },
          "terminology": []
        },
        {
          "id": "q1-f2",
          "trigger_level": "mid",
          "question_text": "분산 환경에서 캐시 일관성은 어떻게 유지하나요?",
          "why_matters": "기본적인 분산 시스템 이해도 확인",
          "listen_for": "Pub/Sub, 이벤트 버스, 또는 최소한 TTL 기반 접근",
          "scoring": {
            "good": "분산 환경 캐시 전략 설명",
            "good_score": 5,
            "poor": "분산 환경 고려 없음",
            "poor_score": -2
          },
          "terminology": []
        }
      ],
      "expected_answer": {
        "core_answer": "- TTL 기반 자동 만료\n- 데이터 변경 시 명시적 캐시 삭제\n- 캐시 스탬피드 방지 (분산 락)",
        "example_script": "TTL을 설정하여 자동 만료시키고, 사용자 정보 업데이트 시 해당 키를 삭제합니다. 캐시 스탬피드 방지를 위해 분산 락을 사용합니다.",
        "answer_keywords": [
          {"keyword": "TTL", "importance": "must", "explanation": "캐시 기본 전략으로 반드시 언급해야 함"},
          {"keyword": "Cache Stampede", "importance": "good_to_have", "explanation": "고급 캐시 문제 인식을 보여줌"}
        ],
        "depth_expectations": {
          "주니어": "TTL 개념과 기본 캐시 삭제 이해",
          "시니어": "분산 환경에서의 일관성 전략과 스탬피드 방지까지 설명"
        },
        "code_evidence": [
          {
            "file_path": "src/cache.py",
            "line_start": 52,
            "line_end": 58,
            "code_snippet": "await redis.delete(f'user:{user_id}')",
            "explanation": "명시적 캐시 무효화 구현"
          }
        ],
        "key_points": ["TTL", "명시적 삭제", "캐시 스탬피드 방지"]
      },
      "language": "ko",
      "terminology": [
        {
          "term": "TTL (Time To Live)",
          "definition": "캐시 데이터의 유효 기간을 설정하는 값으로, 설정된 시간이 지나면 자동으로 삭제됩니다.",
          "plain_language_explanation": "음식에 유통기한을 붙이는 것처럼, 저장된 데이터에도 '이 날짜까지만 사용' 기한을 정해두는 것입니다. 기한이 지나면 자동으로 버려집니다.",
          "context": "Redis 캐싱 전략에서 가장 기본이 되는 메커니즘이므로 이 질문에서 핵심 개념입니다."
        }
      ],
      "estimated_time_minutes": 5,
      "skills_assessed": ["Redis", "캐싱 전략", "분산 시스템"],
      "generation_rationale": "후보자의 GitHub에서 Redis CacheManager 구현을 확인. JD에서 요구하는 '대규모 트래픽 처리 경험'과 직접 연결되는 실무 역량 검증.",
      "jd_competency_link": "JD 요구사항: '대규모 트래픽 환경에서의 캐싱 전략 설계 경험' → 실제 구현 코드 기반으로 깊이 검증"
    }
  ],
  "interviewer_guide": {
    "total_duration_minutes": 125,
    "question_order_rationale": "카테고리별 그룹화: 역할 적합성으로 시작하여 기술 역량, 실행력, 소통, 위험 신호 순으로 배치",
    "tips": ["코드 기반 질문에서는 실제 구현 의도를 물어볼 것", "꼬리질문으로 깊이를 확인할 것"],
    "warning_signs": ["구체적 사례 없이 일반론만 답변", "본인 코드에 대한 설명이 불명확"]
  },
  "decision_guide": {
    "recommendation": "HIRE",
    "confidence": 0.82,
    "category_scores": {
      "role_fit": {"score": 32, "max": 40, "weight": 0.15},
      "technical_depth": {"score": 37, "max": 50, "weight": 0.35}
    }
  },
  "full_glossary": [
    {
      "term": "TTL (Time To Live)",
      "definition": "캐시 데이터의 유효 기간을 설정하는 값으로, 설정된 시간이 지나면 자동으로 삭제됩니다.",
      "plain_language_explanation": "음식에 유통기한을 붙이는 것처럼, 저장된 데이터에도 '이 날짜까지만 사용' 기한을 정해두는 것입니다.",
      "context": "캐싱 전략의 기본 메커니즘"
    }
  ],
  "metadata": {
    "quality_score": 0.87,
    "sources_used": ["resume.pdf", "portfolio.docx", "cover_letter.pdf", "https://github.com/user/repo"],
    "total_questions": 25,
    "token_usage": {"prompt": 45000, "completion": 28000}
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
`enrich_input`, `plan`, `document_analysis`, `code_analysis`, `jd_analysis`, `aggregate_analysis`, `select_topics`, `craft_questions`, `review_quality`, `finalize`

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
    {"name": "enrich_input", "status": "completed"},
    {"name": "plan", "status": "completed"},
    {"name": "document_analysis", "status": "completed"},
    {"name": "code_analysis", "status": "completed"},
    {"name": "jd_analysis", "status": "completed"},
    {"name": "aggregate_analysis", "status": "completed"},
    {"name": "select_topics", "status": "completed"},
    {"name": "craft_questions", "status": "pending"},
    {"name": "review_quality", "status": "pending"},
    {"name": "finalize", "status": "pending"}
  ],
  "resume_point": "craft_questions",
  "total_steps": 10,
  "completed_count": 7
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
ALLOWED_COVER_LETTER_TYPES = {".pdf", ".docx"}
MAX_RESUME_SIZE = 10 * 1024 * 1024       # 10MB
MAX_PORTFOLIO_SIZE = 20 * 1024 * 1024    # 20MB
MAX_COVER_LETTER_SIZE = 5 * 1024 * 1024  # 5MB


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
    cover_letter: UploadFile | None = File(None),
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
    if cover_letter:
        _validate_upload(cover_letter, ALLOWED_COVER_LETTER_TYPES, MAX_COVER_LETTER_SIZE)

    # 작업 ID 생성
    job_id = str(uuid.uuid4())
    user_id = auth["user_id"]

    # 파일 업로드 (Storage 추상화 — local/R2/S3)
    file_urls = {}
    if resume:
        file_urls["resume"] = await upload_file(job_id, resume)
    if portfolio:
        file_urls["portfolio"] = await upload_file(job_id, portfolio)
    if cover_letter:
        file_urls["cover_letter"] = await upload_file(job_id, cover_letter)

    # raw_input 구성 (InputData 모델과 일치, Phase 0 enrich_input이 이 dict를 받아 enriched_input 생성)
    raw_input = {
        "resume_path": file_urls.get("resume"),       # S3 key (파일 업로드 경로)
        "portfolio_path": file_urls.get("portfolio"),  # S3 key
        "cover_letter_path": file_urls.get("cover_letter"),  # S3 key
        "linkedin_url": input_data.get("linkedin_url"),
        "github_urls": input_data.get("github_urls", []),
        "jd_text": input_data["jd_text"],
        "experience_level": input_data["experience_level"],
        "language_config": {
            "output_language": input_data.get("language_config", {}).get("output_language", "ko"),
            "terminology_languages": input_data.get("language_config", {}).get("terminology_languages", ["ko", "en"]),
        },
        "max_questions": input_data.get("max_questions", 25),
        "include_expected_answers": input_data.get("include_expected_answers", True),
        "focus_areas": input_data.get("focus_areas"),
    }

    # Temporal 워크플로우 시작
    await temporal.start_workflow(
        InterviewGenerationWorkflow.run,
        args=[job_id, raw_input],
        id=f"interview-{job_id}",
        task_queue="interview-generation",
    )

    # DB에 작업 저장 (Temporal workflow ID 연결)
    await save_job(
        job_id=job_id,
        user_id=user_id,
        temporal_workflow_id=f"interview-{job_id}",
        input_data=raw_input,
        callback_url=input_data.get("callback_url"),
    )

    return {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now(UTC).isoformat(),
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
    db: AsyncSession = Depends(get_db),
    temporal: Client = Depends(get_temporal_client),
):
    """작업 상태 조회 (Temporal Query — SOT)"""
    # 소유자 검증
    job = await db.get(Job, job_id)
    if not job or str(job.user_id) != auth["user_id"]:
        raise HTTPException(404, "Job not found")

    # Temporal Query로 실시간 진행 상황 조회
    try:
        handle = temporal.get_workflow_handle(f"interview-{job_id}")
        progress = await handle.query(
            InterviewGenerationWorkflow.get_progress
        )
        return {
            "job_id": job_id,
            "status": progress["phase"],
            "progress_percent": progress["progress"],
            "current_phase": progress["phase"],
        }
    except Exception:
        # 워크플로우 종료/미존재 시 DB fallback
        return {
            "job_id": job_id,
            "status": job.status,
            "progress_percent": 100 if job.status == "completed" else 0,
            "current_phase": None,
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
