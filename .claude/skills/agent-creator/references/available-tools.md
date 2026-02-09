# Available Tools for Sub-Agents

서브에이전트에서 사용 가능한 도구 목록.

## Core Tools

| 도구 | 용도 | 읽기 전용 |
|------|------|----------|
| Read | 파일 읽기 | O |
| Grep | 내용 검색 | O |
| Glob | 파일 패턴 매칭 | O |
| Bash | 명령어 실행 | X |
| Write | 파일 생성 | X |
| Edit | 파일 수정 | X |
| WebSearch | 웹 검색 | O |
| WebFetch | URL 내용 가져오기 | O |

## MCP Tools

| 도구 | 용도 |
|------|------|
| mcp__context7__* | 라이브러리 문서 조회 |
| mcp__sequential__sequentialthinking | 구조화된 사고 |
| mcp__playwright__* | 브라우저 자동화 |
| mcp__brave-search__* | 웹 검색 |
| mcp__docker__run_command | Docker 컨테이너 명령 |

## 도구 선정 가이드

- **읽기 전용 분석**: Read, Grep, Glob (가장 안전)
- **코드 수정 필요**: + Write, Edit
- **명령 실행 필요**: + Bash
- **브라우저 테스트**: + mcp__playwright__*
- **문서 참조**: + mcp__context7__*

## Permission Mode

- `plan`: 에이전트가 계획만 세우고 실행은 사용자 승인 필요
- (생략 시): 자유롭게 실행
