---
name: arch-frontend
description: 프론트엔드 React 구현. Vite, React, Tailwind, 컴포넌트, 페이지, i18n, OAuth UI 관련 구현 시 사용.
argument-hint: [component] (예: login-page, job-form, result-viewer, interview-script)
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Frontend Architecture Skill

Vite + React + Tailwind CSS 프론트엔드 구현 가이드.

## 반드시 먼저 읽을 문서
1. `docs/architecture/01-overview.md` — 시스템 개요 및 입출력 구조
2. `docs/architecture/05-api-spec.md` — API 엔드포인트 (프론트엔드 호출 대상)
3. `docs/architecture/06-output-spec.md` — 면접 스크립트 뷰 설계

## 기술 스택
- **빌드**: Vite
- **UI**: React (함수형 컴포넌트 + Hooks)
- **스타일**: Tailwind CSS
- **인증**: OAuth → JWT (메모리 저장)
- **다국어**: react-i18next
- **HTTP**: fetch 또는 axios + Authorization Bearer header

## 주요 페이지

### 1. 로그인 페이지
- Google/GitHub OAuth 버튼
- `{API_URL}/auth/{provider}/login` 으로 리다이렉트
- 콜백 후 `#token=` 에서 JWT 추출

### 2. Job 생성 폼
- 파일 업로드: 이력서(PDF), 포트폴리오(DOCX)
- 텍스트 입력: JD, GitHub URLs, LinkedIn URL
- 선택: 경험 레벨, 출력 언어
- `POST /api/v1/jobs` 호출

### 3. Job 상태 추적
- `GET /api/v1/jobs/{id}` 폴링
- Phase별 진행률 표시 (0~4)
- 실시간 상태 업데이트

### 4. 결과 뷰어 (면접 스크립트)
- 25개 질문 표시 (카테고리별 탭/섹션)
- 접기/펼치기 (Progressive Disclosure)
- 후속질문 분기 (Expert/Mid/Low)
- 키워드 체크리스트
- 용어 설명 툴팁
- 평가 시나리오 (색상 구분)
- on-demand 번역 버튼

## 파일 배치
```
frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── CreateJobPage.tsx
│   │   ├── JobStatusPage.tsx
│   │   └── ResultPage.tsx
│   ├── components/
│   │   ├── auth/          — OAuth 버튼, AuthProvider
│   │   ├── job/           — JobForm, FileUpload
│   │   ├── interview/     — QuestionCard, FollowUp, Evaluation
│   │   └── common/        — Layout, Navbar, Loading
│   ├── hooks/
│   │   ├── useAuth.ts     — JWT 관리
│   │   └── useJob.ts      — Job API 호출
│   ├── utils/
│   │   └── auth.ts        — extractTokenFromCallback
│   ├── i18n/
│   │   └── config.ts      — react-i18next 설정
│   └── types/
│       └── index.ts       — 공통 타입
├── public/
│   └── locales/
│       ├── ko/translation.json
│       └── en/translation.json
├── tailwind.config.js
├── vite.config.ts
└── package.json
```

## 규칙
- JWT는 메모리만 (localStorage/sessionStorage 금지)
- 컴포넌트명: PascalCase
- Tailwind 유틸리티 클래스 우선 (커스텀 CSS 최소화)
- i18n: 모든 사용자 표시 텍스트는 번역 키 사용
- 반응형: mobile-first
