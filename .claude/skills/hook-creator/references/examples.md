# Hook Examples (IaaS Project)

IaaS 프로젝트에 적용된 훅 예제.

## 1. SessionStart — 프로젝트 상태 자동 로딩

```json
{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "cd /home/sabyun/IaaS && echo '--- Docker Status ---' && docker compose ps --format 'table {{.Name}}\t{{.Status}}' 2>/dev/null | head -15; echo '--- Git Branch ---' && git branch --show-current; echo '--- Recent Commits ---' && git log --oneline -3"
  }]
}
```
**효과**: 세션 시작 시 Docker 컨테이너 상태, 현재 Git 브랜치, 최근 커밋 3개 표시

## 2. PreToolUse — 프로덕션 파일 보호

```json
{
  "matcher": "Edit|Write",
  "hooks": [{
    "type": "command",
    "command": "python3 -c \"import json,sys; p=json.load(sys.stdin).get('tool_input',{}).get('file_path',''); sys.exit(2 if any(x in p for x in ['.env.production', 'docker-compose.prod']) else 0)\""
  }]
}
```
**효과**: `.env.production`, `docker-compose.prod` 파일 수정 시 자동 차단 (exit 2)

## 3. PreToolUse — main 브랜치 커밋 방지

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "bash -c 'INPUT=$(cat); CMD=$(echo \"$INPUT\" | jq -r \".tool_input.command // empty\" 2>/dev/null); if echo \"$CMD\" | grep -q \"git commit\"; then BRANCH=$(cd /home/sabyun/IaaS && git branch --show-current 2>/dev/null); if [ \"$BRANCH\" = \"main\" ] || [ \"$BRANCH\" = \"master\" ]; then echo \"[Git Hook] BLOCKED: main/master 브랜치에 직접 커밋 금지.\"; exit 2; fi; fi'"
  }]
}
```
**효과**: main/master에서 `git commit` 시도 시 자동 차단

## 4. PostToolUse — 커밋 후 PR 알림 + 머지 후 main 동기화

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "bash -c '...git commit 감지 → PR 미존재 시 알림...gh pr merge 감지 → main 자동 체크아웃+pull...'"
  }]
}
```
**효과**: feature 브랜치 커밋 시 PR 생성 유도, PR 머지 후 자동 main 동기화

## 5. Stop — 고아 프로세스 경고

```json
{
  "matcher": "*",
  "hooks": [{
    "type": "command",
    "command": "count=$(ps aux | grep '[/]Users/sabyun/.local/bin/claude' | wc -l | tr -d ' '); [ \"$count\" -gt 5 ] && echo \"WARNING: $count claude processes detected.\" || exit 0"
  }]
}
```
**효과**: 세션 종료 시 claude 프로세스 5개 초과면 경고

## 추가 훅 아이디어

### Python lint 자동 실행
```json
{
  "matcher": "Edit|Write",
  "hooks": [{
    "type": "command",
    "command": "jq -r '.tool_input.file_path' | { read f; [[ \"$f\" == *.py ]] && docker compose exec -T backend python -m ruff check \"$f\" 2>/dev/null; exit 0; }"
  }]
}
```

### TypeScript 타입 체크
```json
{
  "matcher": "Edit|Write",
  "hooks": [{
    "type": "command",
    "command": "jq -r '.tool_input.file_path' | { read f; [[ \"$f\" == *.tsx || \"$f\" == *.ts ]] && cd frontend && npx tsc --noEmit 2>/dev/null | head -5; exit 0; }"
  }]
}
```
