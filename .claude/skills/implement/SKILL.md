---
name: implement
description: 코드 구현. API 엔드포인트, React 컴포넌트, 서비스, 기능 구현 시 사용.
argument-hint: [--type api|component|service] [description]
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Implementation Skill

## API 엔드포인트 (--type api)
- 배치: `backend/app/api/routes/`
- 프레임워크: FastAPI
- 네이밍: `snake_case` (예: `create_job`, `get_job_status`)
- 필수: 타입 힌트, 요청 검증, 에러 핸들링
- 참고: `docs/architecture/05-api-spec.md`

## React 컴포넌트 (--type component)
- 배치: `frontend/src/components/`
- 프레임워크: Vite + React + Tailwind CSS, react-i18next
- 네이밍: `PascalCase` (예: `InterviewForm`, `QuestionCard`)
- 필수: prop 타입, i18n 지원
- 참고: `docs/architecture/01-overview.md`

## 서비스 (--type service)
- 배치: `backend/app/services/`
- 패턴: 의존성 주입, pydantic-settings 환경 설정
- 필수: 에러 분류, 로깅

## 규칙
- 파일 300줄 초과 시 분리 검토
- HTML에 인라인 스크립트/스타일 금지
- 기존 파일과 책임 중복 금지
