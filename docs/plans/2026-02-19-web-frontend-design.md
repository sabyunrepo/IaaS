# Web Frontend 아키텍처 설계

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 멀티테넌트 SaaS 웹 프론트엔드 — 지원자 셀프서비스 + 관리자 대시보드

**Architecture:** pnpm 모노레포 + 3 패키지 (@jittda/ui, @jittda/public, @jittda/admin)

**Tech Stack:** React 19, Vite, Tailwind 4, D3.js 7.9+, pnpm workspace, react-router-dom, react-i18next

---

## 1. 배경

기존 v5.0 아키텍처 문서(docs/architecture/)에 웹 프론트엔드 설계가 누락되어 있었다.
Interface 계층에 REST API, WebSocket, Electron App, D3 Charts만 정의되어 있고,
사용자가 실제로 데이터를 입력하는 웹 화면이 없었다.

### 핵심 요구사항

| 항목 | 결정 |
|------|------|
| 사용자 유형 | 지원자 (비회원) + 회사 관리자 (OAuth) |
| 회사 모델 | 멀티테넌트 SaaS |
| 커리어 페이지 | jittda.com/careers/:companySlug (통일 템플릿, 테마 확장 가능) |
| 분석 트리거 | 수동 기본 + 자동 옵션 |
| 요금제 | 미정 (확장 가능 설계) |
| 정보 제공 안내 | 지원 시 제3자 동의 필수 |

---

## 2. 모노레포 구조

```
jittda/frontend/
├── pnpm-workspace.yaml
├── package.json                # 루트 scripts: dev, build, lint
├── tsconfig.base.json          # 공통 TS 설정
├── packages/
│   ├── ui/                     # @jittda/ui — 공유 디자인 시스템
│   │   ├── src/
│   │   │   ├── components/     # Button, Input, Card, FileUpload, Modal, Badge...
│   │   │   ├── hooks/          # useForm, useFileUpload, useToast
│   │   │   └── styles/         # Tailwind 프리셋, 테마 토큰
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── public-app/             # @jittda/public — 지원자용 (비인증)
│   │   ├── src/
│   │   │   ├── pages/          # 4 페이지
│   │   │   ├── components/     # CompanyHeader, JobCard, ApplicationForm
│   │   │   ├── lib/            # api.ts (public API 클라이언트)
│   │   │   ├── App.tsx
│   │   │   └── main.tsx
│   │   ├── index.html
│   │   └── vite.config.ts
│   │
│   └── admin-app/              # @jittda/admin — 관리자용 (인증)
│       ├── src/
│       │   ├── pages/          # 11+ 페이지
│       │   ├── components/
│       │   │   ├── charts/     # D3 RadarChart, Treemap, Heatmap
│       │   │   └── tabs/       # OverviewTab, IntelBriefTab, DeepDiveTab...
│       │   ├── hooks/          # useAuth, useJob, useApplicant, useWebSocket
│       │   ├── lib/            # api.ts (authenticated API 클라이언트)
│       │   ├── App.tsx
│       │   └── main.tsx
│       ├── index.html
│       └── vite.config.ts
```

---

## 3. 페이지 구성

### 3.1 Public App (지원자용, 4 페이지)

| 라우트 | 페이지 | 설명 |
|--------|--------|------|
| `/careers/:slug` | CareersPage | 회사 소개 + 공고 리스트 |
| `/careers/:slug/:jobId` | JobDetailPage | 공고 상세 (JD, 요구사항, 지원 버튼) |
| `/careers/:slug/:jobId/apply` | ApplicationPage | 지원 폼 (파일 업로드, 동의) |
| `/apply/confirm` | ConfirmPage | 이메일 확인 완료 |

### 3.2 Admin App (관리자용, 11 페이지)

| 라우트 | 페이지 | 설명 |
|--------|--------|------|
| `/login` | LoginPage | OAuth (Google, GitHub) |
| `/onboarding` | OnboardingPage | 최초 회사 프로필 설정 |
| `/` | DashboardPage | 대시보드 (지원자 현황, 분석 현황) |
| `/jobs` | JobListPage | 공고 목록 + CRUD |
| `/jobs/new` | JobCreatePage | 새 공고 작성 |
| `/jobs/:id/edit` | JobEditPage | 공고 수정 |
| `/jobs/:id/applicants` | ApplicantListPage | 공고별 지원자 목록 |
| `/applicants/:id` | ApplicantDetailPage | 지원자 상세 + 분석 시작 |
| `/applicants/:id/analysis` | AnalysisPage | 분석 결과 (5탭: Phase 5) |
| `/applicants/register` | ApplicantRegisterPage | 관리자 직접 등록 |
| `/settings` | SettingsPage | 회사 설정 + 멤버 + 분석 설정 |

---

## 4. 지원자 플로우

```
방문자 → /careers/:slug (회사 커리어 페이지)
    │
    │  공고 리스트 확인
    ▼
/careers/:slug/:jobId (공고 상세)
    │
    │  '지원하기' 클릭
    ▼
/careers/:slug/:jobId/apply (지원 폼)
    ├─ 이름 (필수)
    ├─ 이메일 (필수)
    ├─ GitHub URL (선택)
    ├─ LinkedIn URL (선택)
    ├─ 이력서 PDF 업로드 (필수)
    ├─ 포트폴리오 PDF 업로드 (선택)
    ├─ 커버레터 PDF 업로드 (선택)
    └─ ☑ "지원 정보가 AI 분석 목적으로 제3자에게 제공됩니다" (필수 동의)
    │
    │  제출
    ▼
이메일 확인 링크 발송 → /apply/confirm?token=...
    │
    │  확인 클릭
    ▼
지원 완료 (status: confirmed)
    │
    │  관리자가 '분석 시작' (수동) or 자동
    ▼
HMAS 파이프라인 실행 → WebSocket 진행률 → 결과
```

---

## 5. 관리자 플로우

```
OAuth 로그인 → /onboarding (최초) → / (대시보드)
    │
    ├── 공고 관리
    │   ├─ /jobs/new: 공고 생성 (제목, JD, 스킬, 자동분석 ON/OFF)
    │   └─ /jobs/:id/applicants: 지원자 목록
    │       ├─ 상태 필터 (신규/분석중/완료)
    │       └─ 일괄 '분석 시작' or 개별 시작
    │
    ├── 지원자 관리
    │   ├─ /applicants/:id: 프로필 + 제출 문서 확인
    │   ├─ /applicants/:id/analysis: 분석 결과 (Phase 5 탭)
    │   │   ├─ Tab 1: Overview (3초 요약 + FourAxisRadar)
    │   │   ├─ Tab 2: Intel Brief (진정성 검증)
    │   │   ├─ Tab 3: Code Deep Dive (Treemap + Heatmap)
    │   │   ├─ Tab 4: Interview (3전략 질문)
    │   │   └─ Tab 5: Decision (종합 판단)
    │   └─ /applicants/register: 관리자 직접 등록
    │
    └── 설정
        ├─ 회사 프로필 (이름, 로고, slug, 소개)
        ├─ 멤버 관리 (초대/역할)
        └─ 분석 설정 (자동분석 기본값)
```

---

## 6. REST API 엔드포인트 추가

### 6.1 Company (멀티테넌트)

```
POST   /api/v1/companies              # 회사 생성 (온보딩)
GET    /api/v1/companies/:slug         # 회사 공개 정보
PATCH  /api/v1/companies/:id           # 회사 수정
GET    /api/v1/companies/:id/members   # 멤버 목록
POST   /api/v1/companies/:id/invite    # 멤버 초대
```

### 6.2 Job Postings (공고)

```
POST   /api/v1/jobs                    # 공고 생성
GET    /api/v1/jobs                    # 공고 목록 (관리자, 회사 필터)
GET    /api/v1/jobs/:id                # 공고 상세
PATCH  /api/v1/jobs/:id                # 공고 수정
DELETE /api/v1/jobs/:id                # 공고 닫기
```

### 6.3 Public API (비인증)

```
GET    /api/v1/public/careers/:slug            # 회사 커리어 페이지
GET    /api/v1/public/careers/:slug/jobs       # 공고 리스트
GET    /api/v1/public/careers/:slug/jobs/:id   # 공고 상세
POST   /api/v1/public/applications             # 지원 제출
POST   /api/v1/public/applications/confirm     # 이메일 확인
```

### 6.4 Applications (지원 관리)

```
GET    /api/v1/applications                    # 지원자 목록 (관리자)
GET    /api/v1/applications/:id                # 지원자 상세
POST   /api/v1/applications                    # 관리자 직접 등록
POST   /api/v1/applications/:id/analyze        # 분석 시작 (수동)
GET    /api/v1/applications/:id/analysis       # 분석 결과
```

### 6.5 기존 유지

```
GET    /api/v1/jobs/:id/stream                 # WebSocket (분석 진행률)
POST   /api/v1/files/upload                    # 파일 업로드
GET    /health                                 # 헬스체크
POST   /api/v1/auth/google                     # Google OAuth
POST   /api/v1/auth/github                     # GitHub OAuth
GET    /api/v1/auth/me                         # 현재 사용자 정보
```

---

## 7. 도메인 모델 추가

### 7.1 Company (새 도메인)

```python
@dataclass
class Company:
    id: str
    name: str
    slug: str                # URL-friendly identifier
    logo_url: str | None
    description: str | None
    auto_analyze: bool       # 자동 분석 기본값
    created_at: datetime

@dataclass
class CompanyMember:
    id: str
    company_id: str
    user_id: str
    role: str                # "owner" | "admin" | "member"
    invited_at: datetime
```

### 7.2 JobPosting (새 도메인)

```python
@dataclass
class JobPosting:
    id: str
    company_id: str
    title: str
    description: str         # JD (Markdown)
    required_skills: list[str]
    experience_level: str    # "junior" | "mid" | "senior"
    status: str              # "draft" | "open" | "closed"
    auto_analyze: bool       # 이 공고에 대한 자동 분석 여부
    created_at: datetime
```

### 7.3 Application (새 도메인)

```python
@dataclass
class Application:
    id: str
    company_id: str
    job_posting_id: str
    candidate_name: str
    candidate_email: str
    github_url: str | None
    linkedin_url: str | None
    resume_path: str
    portfolio_path: str | None
    cover_letter_path: str | None
    consent_given: bool      # 제3자 정보 제공 동의
    email_confirmed: bool
    status: str              # "pending" | "confirmed" | "analyzing" | "completed"
    analysis_job_id: str | None  # HMAS Job ID (기존 Job과 연결)
    created_at: datetime
```

---

## 8. 기존 아키텍처 연동

### 8.1 HMAS 파이프라인 연결

```
Application (status: confirmed)
    │
    │  POST /api/v1/applications/:id/analyze
    ▼
Job 생성 (기존 HMAS 파이프라인)
    │  ├─ github_urls: [application.github_url]
    │  ├─ jd_text: job_posting.description
    │  ├─ resume_path: application.resume_path
    │  └─ linkedin_url: application.linkedin_url
    ▼
MetaAgent → Supervisors → Workers (기존 그대로)
    │
    ▼
분석 결과 → Application.analysis_job_id로 연결
```

### 8.2 WebSocket 진행률

기존 `/api/v1/jobs/:id/stream` 그대로 사용.
Admin App에서 `application.analysis_job_id`로 WebSocket 연결.

### 8.3 D3 Charts

기존 Phase 5 차트 컴포넌트를 `@jittda/admin` 패키지의 `components/charts/`에 구현.
- FourAxisRadar, ComplexityTreemap, AICodeHeatmap, SkillHeatmap

### 8.4 파일 업로드

기존 `/api/v1/files/upload` 엔드포인트 재사용.
Public App에서도 비인증으로 업로드 가능하도록 별도 엔드포인트 추가:
`POST /api/v1/public/files/upload` (rate limit 적용)

---

## 9. 배포 구조

```nginx
# nginx.conf
server {
    # Public App (지원자용)
    location /careers {
        proxy_pass http://frontend-public:3000;
    }
    location /apply {
        proxy_pass http://frontend-public:3000;
    }

    # Admin App (관리자용)
    location /admin {
        proxy_pass http://frontend-admin:3001;
    }
    location /login {
        proxy_pass http://frontend-admin:3001;
    }

    # API
    location /api {
        proxy_pass http://backend:8000;
    }
    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
    }
}
```

Docker Compose 추가:
```yaml
frontend-public:
  build: ./frontend/packages/public-app
  ports: ["3000:80"]

frontend-admin:
  build: ./frontend/packages/admin-app
  ports: ["3001:80"]
```

---

## 10. 기존 아키텍처 문서 수정 목록

| 문서 | 수정 내용 |
|------|----------|
| `interface/MOC.md` | Web Frontend (Public + Admin) 컴포넌트 추가 |
| `interface/rest-api/endpoints.md` | Company, Public, Application 엔드포인트 추가 |
| `interface/rest-api/schemas.md` | Company, JobPosting, Application 스키마 추가 |
| `crosscutting/deployment.md` | frontend 2앱 nginx + Docker 설정 |
| `crosscutting/security.md` | 비인증 public API + 이메일 확인 + rate limit |
| `RELATION-MAP.md` | WF(Web Frontend) 노드 + 의존성 추가 |
| `tech-stack/frontend.md` | pnpm workspace + 모노레포 구조 |
| `domain/MOC.md` | Company, Application 하위 도메인 추가 |

### 새로 생성할 문서

| 새 문서 | 내용 |
|---------|------|
| `interface/web-frontend/MOC.md` | 웹 프론트엔드 전체 개요 |
| `interface/web-frontend/public-app.md` | 지원자 앱 상세 |
| `interface/web-frontend/admin-app.md` | 관리자 앱 상세 |
| `interface/web-frontend/shared-ui.md` | 공유 디자인 시스템 |
| `domain/company/MOC.md` | Company 도메인 모델 |
| `domain/application-flow/MOC.md` | Application(지원) 도메인 모델 |
