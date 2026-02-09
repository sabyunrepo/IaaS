# Hook Events Reference

Claude Code 훅 이벤트 종류와 스키마.

## 이벤트 종류

| 이벤트 | 실행 시점 | 차단 가능 | stdin 데이터 |
|--------|----------|----------|-------------|
| `SessionStart` | 세션 시작 시 | X | `{}` |
| `PreToolUse` | 도구 호출 직전 | O (exit 2) | `{tool_name, tool_input}` |
| `PostToolUse` | 도구 호출 직후 | X | `{tool_name, tool_input, tool_output}` |
| `Stop` | 세션 종료 시 | X | `{}` |
| `Notification` | 알림 발생 시 | X | `{message}` |

## stdin JSON 스키마

### PreToolUse / PostToolUse

```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.py",
    "old_string": "...",
    "new_string": "..."
  }
}
```

### Bash 도구의 경우

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "git commit -m 'message'"
  }
}
```

## Matcher 패턴

- `*` — 모든 도구에 매칭
- `Edit` — Edit 도구에만 매칭
- `Edit|Write` — Edit 또는 Write에 매칭
- `Bash` — Bash 도구에만 매칭

## 훅 구조 (settings.local.json)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "your-shell-command-here"
          }
        ]
      }
    ]
  }
}
```

## 차단 동작 (PreToolUse 전용)

- `exit 0` → 도구 실행 허용
- `exit 2` → 도구 실행 차단 (stdout 메시지가 Claude에게 전달됨)
- 기타 exit code → 도구 실행 허용 (경고만)
