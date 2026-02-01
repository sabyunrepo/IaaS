---
name: analyze
description: 코드 분석. security, 보안, 취약점, 코드 품질, 의존성 분석 시 사용.
argument-hint: [--focus security|quality|dependency]
allowed-tools: Read, Grep, Bash, Glob
---

# Analysis Skill

## 보안 분석 (--focus security)
- OWASP Top 10 취약점 점검
- 인증/인가 로직 검토
- SQL injection, XSS, CSRF 확인
- 환경변수/시크릿 노출 확인
- 의존성 취약점 (`npm audit`, `pip audit`)

## 코드 품질 (--focus quality)
- 순환 복잡도 확인
- 중복 코드 탐지
- 네이밍 규칙 준수 확인
- 테스트 커버리지 확인

## 의존성 분석 (--focus dependency)
- 패키지 버전 확인
- 미사용 의존성 탐지
- 라이선스 호환성

## 활용 MCP
- `sequential`: 복잡한 분석 추론
- `context7`: 라이브러리 문서 확인
