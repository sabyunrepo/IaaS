---
title: "Public App (지원자용)"
type: component
layer: interface
parent: "[[interface/web-frontend/MOC]]"
status: active
created: 2026-02-19
tags: [interface, frontend, public, candidate]
---

# Public App (지원자용)

> 비인증 지원자가 회사 커리어 페이지에서 공고를 확인하고 직접 지원하는 경량 웹 앱.

## 페이지 구성

| 라우트 | 컴포넌트 | 설명 |
|--------|---------|------|
| /careers/:slug | CareersPage | 회사 소개 + 공고 리스트 |
| /careers/:slug/:jobId | JobDetailPage | 공고 상세 (JD, 요구사항) |
| /careers/:slug/:jobId/apply | ApplicationPage | 지원 폼 |
| /apply/confirm | ConfirmPage | 이메일 확인 완료 |

## 지원 플로우

```
방문자 → /careers/:slug
    │ 공고 리스트 확인
    ▼
/careers/:slug/:jobId
    │ 공고 상세 확인 → '지원하기'
    ▼
/careers/:slug/:jobId/apply
    ├─ 이름 (필수)
    ├─ 이메일 (필수)
    ├─ GitHub URL (선택)
    ├─ LinkedIn URL (선택)
    ├─ 이력서 PDF (필수)
    ├─ 포트폴리오 PDF (선택)
    ├─ 커버레터 PDF (선택)
    └─ ☑ 제3자 정보 제공 동의 (필수)
    │ 제출 → 이메일 확인 링크 발송
    ▼
/apply/confirm?token=...
    └─ 확인 완료 → status: confirmed
```

## API 연동

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | /api/v1/public/careers/:slug | 회사 정보 |
| GET | /api/v1/public/careers/:slug/jobs | 공고 리스트 |
| GET | /api/v1/public/careers/:slug/jobs/:id | 공고 상세 |
| POST | /api/v1/public/applications | 지원 제출 |
| POST | /api/v1/public/applications/confirm | 이메일 확인 |
| POST | /api/v1/public/files/upload | 파일 업로드 (rate limit) |

## 주요 컴포넌트

- **CompanyHeader** — 회사 로고 + 이름 + 소개
- **JobCard** — 공고 카드 (제목, 스킬, 경험 레벨)
- **ApplicationForm** — 지원 폼 (파일 업로드, 동의 체크박스)
- **ConsentBanner** — 제3자 정보 제공 안내 배너

## 설계 원칙

1. **비인증**: 회원가입 없이 이메일+이름으로 지원
2. **경량**: 4 페이지, D3/차트 미포함, 번들 최소화
3. **SEO**: SSR 또는 Pre-rendering 고려 (추후)
4. **모바일 퍼스트**: 지원자는 모바일로 접근할 가능성 높음
