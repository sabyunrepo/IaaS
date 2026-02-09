---
name: hook-creator
description: Claude Code 훅 생성 스킬. 자동화 훅을 만들 때 사용.
argument-hint: [hook-event] [purpose]
allowed-tools: Read, Write, Edit
---

# Hook Creator Skill

Claude Code 라이프사이클 훅을 생성합니다.

## 훅이란?

Claude Code 도구 호출 전/후에 자동 실행되는 셸 커맨드. `.claude/settings.local.json`의 `hooks` 섹션에 정의.

## 생성 절차

1. 자동화할 작업 식별 (포맷팅, 검증, 알림 등)
2. 적절한 이벤트 선택 → See `references/hook-events.md`
3. 셸 커맨드 작성
4. `.claude/settings.local.json`의 `hooks` 섹션에 추가
5. 테스트 (세션 재시작 후 확인)

## 훅 설계 원칙

- **빠른 실행**: 훅은 매 도구 호출마다 실행되므로 2초 이내
- **안전한 실패**: `exit 0`으로 끝내서 Claude Code 작업 방해 안 함
- **exit 2 = 차단**: `exit 2` 반환 시 도구 실행이 차단됨 (PreToolUse에서만)
- **stdin으로 컨텍스트**: 도구 호출 정보가 JSON으로 stdin에 전달됨
- **matcher**: `*` (전체) 또는 `Edit|Write` (특정 도구) 패턴

## 기존 훅 목록

| 이벤트 | Matcher | 목적 |
|--------|---------|------|
| SessionStart | * | Docker/Git 상태 자동 표시 |
| PreToolUse | Edit\|Write | 프로덕션 설정 파일 보호 |
| PreToolUse | Bash | main 브랜치 직접 커밋 방지 |
| PostToolUse | Bash | 커밋 후 PR 생성 제안 + PR 머지 후 main 동기화 |
| Stop | * | 고아 서브에이전트 경고 |

## 참고
- `references/hook-events.md` — 이벤트 레퍼런스
- `references/examples.md` — IaaS 맞춤 예제
