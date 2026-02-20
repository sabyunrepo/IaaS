---
title: "Admin App (관리자용)"
type: component
layer: interface
parent: "[[interface/web-frontend/MOC]]"
status: active
created: 2026-02-19
tags: [interface, frontend, admin, dashboard]
---

# Admin App (관리자용)

> OAuth 인증 관리자가 공고 관리, 지원자 관리, 분석 결과 확인을 수행하는 대시보드.

## 페이지 구성

| 라우트 | 컴포넌트 | 설명 |
|--------|---------|------|
| /login | LoginPage | OAuth (Google, GitHub) |
| /onboarding | OnboardingPage | 최초 회사 프로필 설정 |
| / | DashboardPage | 대시보드 |
| /jobs | JobListPage | 공고 목록 |
| /jobs/new | JobCreatePage | 새 공고 작성 |
| /jobs/:id/edit | JobEditPage | 공고 수정 |
| /jobs/:id/applicants | ApplicantListPage | 지원자 목록 |
| /applicants/:id | ApplicantDetailPage | 지원자 상세 |
| /applicants/:id/analysis | AnalysisPage | 분석 결과 (5탭) |
| /applicants/register | ApplicantRegisterPage | 관리자 직접 등록 |
| /settings | SettingsPage | 회사 설정 |

## 분석 결과 탭 (Phase 5 연동)

| 탭 | 컴포넌트 | D3 차트 |
|----|---------|---------|
| Overview | OverviewTab | FourAxisRadar |
| Intel Brief | IntelBriefTab | — |
| Code Deep Dive | DeepDiveTab | ComplexityTreemap, AICodeHeatmap, SkillHeatmap |
| Interview | InterviewTab | — |
| Decision | DecisionTab | — |

## 관리자 플로우

```
OAuth 로그인 → /onboarding (최초)
    │
    ▼
/ (대시보드)
    ├── 신규 지원자, 분석 진행 중, 완료 카운트
    ├── 최근 지원자 카드
    │
    ├── /jobs: 공고 CRUD
    │   └── /jobs/:id/applicants: 지원자 목록
    │       ├─ 상태 필터 (신규/분석중/완료)
    │       └─ '분석 시작' (수동) or 자동
    │
    ├── /applicants/:id: 상세 + 분석 시작
    │   └── /applicants/:id/analysis: 결과 (5탭)
    │
    └── /settings: 회사 프로필, 멤버, 분석 설정
```

## API 연동

### 인증 필요 (Authorization: Bearer JWT)

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | /api/v1/companies | 회사 생성 |
| PATCH | /api/v1/companies/:id | 회사 수정 |
| GET | /api/v1/companies/:id/members | 멤버 목록 |
| POST | /api/v1/companies/:id/invite | 멤버 초대 |
| POST | /api/v1/jobs | 공고 생성 |
| GET | /api/v1/jobs | 공고 목록 |
| PATCH | /api/v1/jobs/:id | 공고 수정 |
| DELETE | /api/v1/jobs/:id | 공고 닫기 |
| GET | /api/v1/applications | 지원자 목록 |
| GET | /api/v1/applications/:id | 지원자 상세 |
| POST | /api/v1/applications | 관리자 직접 등록 |
| POST | /api/v1/applications/:id/analyze | 분석 시작 |
| GET | /api/v1/applications/:id/analysis | 분석 결과 |

### WebSocket 연동

```
ws://host/api/v1/jobs/{analysis_job_id}/stream
→ 분석 진행률 실시간 수신
→ node_started, node_completed, progress, completed 이벤트
```

## 주요 컴포넌트

### 대시보드
- **StatCard** — 숫자 카운트 카드 (신규 지원자, 분석 중, 완료)
- **RecentApplicantList** — 최근 지원자 목록

### 공고 관리
- **JobForm** — 공고 생성/수정 폼 (제목, JD, 스킬, 자동분석 토글)
- **JobTable** — 공고 테이블 (상태 배지, 지원자 수)

### 지원자 관리
- **ApplicantTable** — 지원자 테이블 (이름, 상태, 분석 점수)
- **ApplicantProfile** — 지원자 프로필 카드
- **DocumentViewer** — 제출 문서 미리보기

### 분석 결과
- **AnalysisTabs** — 5탭 네비게이션 (Phase 5 설계 준수)
- D3 차트: FourAxisRadar, ComplexityTreemap, AICodeHeatmap, SkillHeatmap
