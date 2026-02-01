---
name: test
description: 테스트 작성 및 실행. unit test, integration test, E2E test, coverage 분석 시 사용.
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Testing Skill

## Python (Backend)
- 프레임워크: pytest
- 실행: `pytest tests/` 또는 `pytest tests/test_specific.py -v`
- 커버리지: `pytest --cov=app tests/`
- Activity 테스트 시 Temporal test environment 사용

## JavaScript/TypeScript (Frontend)
- 프레임워크: Vitest 또는 Jest
- 실행: `npm test` 또는 `npx vitest`

## E2E
- 프레임워크: Playwright
- 실행: `npx playwright test`
- MCP `playwright` 서버 활용 가능

## 테스트 원칙
- 새 기능에는 반드시 테스트 추가
- 버그 수정 시 회귀 테스트 추가
- Activity는 멱등성 테스트 포함
- LLM 호출은 mock 처리
