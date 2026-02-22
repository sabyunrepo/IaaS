# Claude Code 4대 시스템 업그레이드 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 영상 4대 시스템(자동 매뉴얼, 작업 기억, 품질 검사, 에이전트 보고서)을 기존 Claude Code 세팅에 글로벌 통합

**Architecture:** Hook 기반 강제 시스템(시스템 1,3) + CLAUDE.md/스킬 기반 가이드(시스템 2,4). 기존 superpowers v4.3.0과 공존.

**Tech Stack:** Bash scripts, jq, JSON config, Markdown templates

**Design Doc:** `docs/plans/2026-02-23-claude-code-upgrade-design.md`

---

## Task 1: 매칭 규칙 설정 파일 생성

**Files:**
- Create: `~/.claude/scripts/skill-rules.json`
- Create: `~/.claude/scripts/quality-rules.json`

**Step 1: skill-rules.json 작성**

```json
{
  "rules": [
    {
      "id": "backend",
      "skills": ["/arch-api", "/arch-data"],
      "keywords": ["API", "엔드포인트", "FastAPI", "라우트", "백엔드", "서버", "REST", "endpoint"],
      "intents": ["만들어", "추가해", "수정해", "구현해", "create", "add", "implement", "fix"],
      "file_patterns": ["**/routes/**", "**/api/**", "**/models/**", "**/services/**"]
    },
    {
      "id": "frontend",
      "skills": ["/jittda-design-system", "/arch-frontend"],
      "keywords": ["프론트", "컴포넌트", "React", "UI", "페이지", "화면", "Tailwind", "CSS", "frontend"],
      "file_patterns": ["**/components/**", "**/*.tsx", "**/pages/**", "**/hooks/**"],
      "inject_message": "🎨 프론트엔드 필수 규칙: Seed Design 컴포넌트 우선 | lucide-react 아이콘 전용 | BaseAPI 상속 | 표준 폴더 구조"
    },
    {
      "id": "temporal",
      "skills": ["/temporal-dev", "/arch-workflow"],
      "keywords": ["워크플로우", "activity", "temporal", "파이프라인", "worker", "heartbeat"],
      "file_patterns": ["**/workflows/**", "**/activities/**"]
    },
    {
      "id": "testing",
      "skills": ["/test", "/troubleshoot"],
      "keywords": ["테스트", "버그", "디버그", "에러", "pytest", "test", "bug", "debug", "fix"],
      "file_patterns": ["**/tests/**", "**/test_**", "**/*.spec.*"]
    },
    {
      "id": "infra",
      "skills": ["/arch-infra"],
      "keywords": ["docker", "compose", "배포", "환경변수", "인프라", "deploy", "env"],
      "file_patterns": ["**/docker-compose*", "**/Dockerfile*", "**/.env*"]
    },
    {
      "id": "prompt",
      "skills": ["/arch-prompt"],
      "keywords": ["프롬프트", "LLM", "Langfuse", "prompt", "YAML 프롬프트"],
      "file_patterns": ["**/prompts/**", "**/*.yaml"]
    },
    {
      "id": "auth",
      "skills": ["/arch-auth"],
      "keywords": ["OAuth", "JWT", "인증", "로그인", "auth", "token", "세션"],
      "file_patterns": ["**/auth/**", "**/middleware/**"]
    },
    {
      "id": "git",
      "skills": ["/git-ops"],
      "keywords": ["커밋", "브랜치", "PR", "머지", "commit", "branch", "pull request"],
      "file_patterns": []
    }
  ]
}
```

**Step 2: quality-rules.json 작성**

```json
{
  "rules": {
    ".py": [
      "타입 힌트가 적절한가요?",
      "에러 처리가 추가되었나요?",
      "관련 테스트를 실행했나요?"
    ],
    ".tsx": [
      "Seed Design 컴포넌트를 사용했나요?",
      "lucide-react 아이콘만 사용했나요?",
      "BaseAPI 상속 클래스를 통해 API를 호출했나요?",
      "접근성(a11y)을 확인했나요?"
    ],
    ".ts": [
      "타입 정의가 적절한가요?",
      "에러 처리가 추가되었나요?"
    ],
    ".yaml": [
      "구문 오류가 없나요?",
      "Langfuse 업로드가 필요한가요? (upload_prompts_to_langfuse.py --production)"
    ],
    ".json": [
      "JSON 구문이 유효한가요?",
      "민감 정보가 포함되어 있지 않나요?"
    ],
    "docker-compose": [
      "환경변수가 동기화되었나요?",
      "볼륨 마운트가 정확한가요?"
    ],
    "Dockerfile": [
      "보안 취약점은 없나요?",
      "불필요한 레이어가 없나요?"
    ],
    "_default": [
      "보안 취약점은 없나요?",
      "관련 문서 업데이트가 필요한가요?"
    ]
  }
}
```

**Step 3: 검증**

Run: `cat ~/.claude/scripts/skill-rules.json | jq . > /dev/null && echo "VALID" || echo "INVALID"`
Expected: `VALID`

Run: `cat ~/.claude/scripts/quality-rules.json | jq . > /dev/null && echo "VALID" || echo "INVALID"`
Expected: `VALID`

**Step 4: 커밋하지 않음** (글로벌 설정이므로 git 트래킹 대상 아님)

---

## Task 2: skill-injector.sh 구현 (UserPromptSubmit Hook)

**Files:**
- Create: `~/.claude/scripts/skill-injector.sh`

**Step 1: 스크립트 작성**

```bash
#!/bin/bash
# UserPromptSubmit hook: 사용자 프롬프트 분석 → 관련 스킬 자동 추천
# stdin: { "prompt": "..." } (Claude Code가 전달)
# stdout: 추천 메시지 (AI에게 system-reminder로 전달됨)

set -euo pipefail

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)

# 프롬프트가 비어있으면 종료
[ -z "$PROMPT" ] && exit 0

# 짧은 프롬프트(슬래시 커맨드 등)는 스킵
[ ${#PROMPT} -lt 10 ] && exit 0

# 규칙 파일 로드 (프로젝트 오버라이드 > 글로벌)
RULES_FILE=""
if [ -f ".claude/skill-rules.json" ]; then
  RULES_FILE=".claude/skill-rules.json"
elif [ -f "$HOME/.claude/scripts/skill-rules.json" ]; then
  RULES_FILE="$HOME/.claude/scripts/skill-rules.json"
fi

[ -z "$RULES_FILE" ] && exit 0

# 키워드 매칭
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')
MATCHED_SKILLS=""
MATCHED_MESSAGES=""

while IFS= read -r rule; do
  RULE_ID=$(echo "$rule" | jq -r '.id')
  KEYWORDS=$(echo "$rule" | jq -r '.keywords[]' 2>/dev/null)
  SKILLS=$(echo "$rule" | jq -r '.skills | join(", ")' 2>/dev/null)
  INJECT_MSG=$(echo "$rule" | jq -r '.inject_message // empty' 2>/dev/null)

  for kw in $KEYWORDS; do
    kw_lower=$(echo "$kw" | tr '[:upper:]' '[:lower:]')
    if echo "$PROMPT_LOWER" | grep -qi "$kw_lower" 2>/dev/null; then
      if ! echo "$MATCHED_SKILLS" | grep -q "$RULE_ID" 2>/dev/null; then
        MATCHED_SKILLS="$MATCHED_SKILLS [$RULE_ID] $SKILLS\n"
        [ -n "$INJECT_MSG" ] && MATCHED_MESSAGES="$MATCHED_MESSAGES$INJECT_MSG\n"
      fi
      break
    fi
  done
done < <(jq -c '.rules[]' "$RULES_FILE")

# 매칭된 스킬이 있으면 출력
if [ -n "$MATCHED_SKILLS" ]; then
  echo "📋 관련 스킬 감지:"
  printf "$MATCHED_SKILLS"
  echo "위 스킬을 확인하고 작업하세요."
  [ -n "$MATCHED_MESSAGES" ] && printf "\n$MATCHED_MESSAGES"
fi

exit 0
```

**Step 2: 실행 권한 부여**

Run: `chmod +x ~/.claude/scripts/skill-injector.sh`

**Step 3: 테스트**

Run: `echo '{"prompt": "백엔드 API 엔드포인트를 추가해줘"}' | bash ~/.claude/scripts/skill-injector.sh`
Expected: `📋 관련 스킬 감지:` + backend 스킬 출력

Run: `echo '{"prompt": "React 컴포넌트를 만들어줘"}' | bash ~/.claude/scripts/skill-injector.sh`
Expected: `📋 관련 스킬 감지:` + frontend 스킬 + Seed Design 넛지 출력

Run: `echo '{"prompt": "hi"}' | bash ~/.claude/scripts/skill-injector.sh`
Expected: 출력 없음 (짧은 프롬프트 스킵)

---

## Task 3: change-logger.sh 구현 (PostToolUse Hook)

**Files:**
- Create: `~/.claude/scripts/change-logger.sh`

**Step 1: 스크립트 작성**

```bash
#!/bin/bash
# PostToolUse hook (Edit|Write): 파일 변경 사항을 세션별 로그에 기록
# stdin: { "tool_name": "Edit", "tool_input": { "file_path": "..." } }
# 조용히 기록만 하고 exit 0

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

# Edit 또는 Write만 처리
case "$TOOL" in
  Edit|Write) ;;
  *) exit 0 ;;
esac

[ -z "$FILE_PATH" ] && exit 0

# 세션별 로그 파일 (PPID = Claude Code 메인 프로세스 PID)
LOG_FILE="/tmp/claude-changes-${PPID}.log"

# 타임스탬프 + 액션 + 파일 경로 기록
echo "$(date '+%Y-%m-%dT%H:%M:%S') $TOOL $FILE_PATH" >> "$LOG_FILE"

exit 0
```

**Step 2: 실행 권한 부여**

Run: `chmod +x ~/.claude/scripts/change-logger.sh`

**Step 3: 테스트**

Run: `echo '{"tool_name":"Edit","tool_input":{"file_path":"backend/app/routes/auth.py"}}' | bash ~/.claude/scripts/change-logger.sh && cat /tmp/claude-changes-$$.log`
Expected: 타임스탬프 + `Edit backend/app/routes/auth.py` 한 줄 기록

---

## Task 4: quality-nudge.sh 구현 (Stop Hook)

**Files:**
- Create: `~/.claude/scripts/quality-nudge.sh`

**Step 1: 스크립트 작성**

```bash
#!/bin/bash
# Stop hook: 세션 종료 시 변경된 파일 목록 + 파일타입별 셀프체크 리마인더
# 기존 프로세스 경고와 함께 실행됨

# 세션별 로그 파일 찾기
LOG_FILE="/tmp/claude-changes-${PPID}.log"

# 로그 파일이 없으면 종료
[ ! -f "$LOG_FILE" ] && exit 0

# 변경 파일 추출 (중복 제거)
CHANGED_FILES=$(awk '{print $3}' "$LOG_FILE" | sort -u)
FILE_COUNT=$(echo "$CHANGED_FILES" | grep -c '.' 2>/dev/null || echo 0)

[ "$FILE_COUNT" -eq 0 ] && exit 0

# 품질 규칙 파일 로드
QUALITY_RULES=""
if [ -f ".claude/quality-rules.json" ]; then
  QUALITY_RULES=".claude/quality-rules.json"
elif [ -f "$HOME/.claude/scripts/quality-rules.json" ]; then
  QUALITY_RULES="$HOME/.claude/scripts/quality-rules.json"
fi

echo ""
echo "📝 이번 세션에서 수정된 파일 ${FILE_COUNT}개:"
echo "$CHANGED_FILES" | while read -r f; do echo "  - $f"; done

if [ -n "$QUALITY_RULES" ]; then
  echo ""
  echo "✅ 확인사항:"

  # 파일 확장자별 체크 규칙 출력
  SEEN_EXTS=""
  echo "$CHANGED_FILES" | while read -r f; do
    # 확장자 추출
    EXT=".${f##*.}"
    BASENAME=$(basename "$f")

    # docker-compose 특별 처리
    if echo "$BASENAME" | grep -q "docker-compose"; then
      EXT="docker-compose"
    elif echo "$BASENAME" | grep -q "Dockerfile"; then
      EXT="Dockerfile"
    fi

    # 이미 출력한 확장자는 스킵
    if echo "$SEEN_EXTS" | grep -q "$EXT"; then
      continue
    fi
    SEEN_EXTS="$SEEN_EXTS $EXT"

    # 규칙 조회
    CHECKS=$(jq -r ".rules[\"$EXT\"] // .rules[\"_default\"] // [] | .[]" "$QUALITY_RULES" 2>/dev/null)
    if [ -n "$CHECKS" ]; then
      echo "  [$EXT 파일]"
      echo "$CHECKS" | while read -r check; do
        echo "    - $check"
      done
    fi
  done
fi

# 로그 파일 정리
rm -f "$LOG_FILE"

exit 0
```

**Step 2: 실행 권한 부여**

Run: `chmod +x ~/.claude/scripts/quality-nudge.sh`

**Step 3: 테스트**

```bash
# 테스트용 로그 생성
echo "2026-02-23T04:00:00 Edit backend/app/routes/auth.py" > /tmp/claude-changes-$$.log
echo "2026-02-23T04:01:00 Write frontend/src/components/Button.tsx" >> /tmp/claude-changes-$$.log
echo "2026-02-23T04:02:00 Edit docker-compose.yml" >> /tmp/claude-changes-$$.log

# 실행
PPID=$$ bash ~/.claude/scripts/quality-nudge.sh
```

Expected: 파일 목록 + `.py`, `.tsx`, `docker-compose` 각각의 체크 규칙 출력

---

## Task 5: 글로벌 settings.json에 hooks 등록

**Files:**
- Modify: `~/.claude/settings.json` — hooks 키 추가

**Step 1: 현재 settings.json 백업**

Run: `cp ~/.claude/settings.json ~/.claude/settings.json.backup`

**Step 2: hooks 키 추가**

`~/.claude/settings.json`의 최상위에 `"hooks"` 키를 추가한다. 기존 `permissions`, `enabledPlugins`, `language` 키는 유지.

추가할 hooks:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/scripts/skill-injector.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/scripts/change-logger.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash $HOME/.claude/scripts/quality-nudge.sh"
          }
        ]
      }
    ]
  }
}
```

**Step 3: IaaS 프로젝트 hooks와 충돌 확인**

IaaS `.claude/settings.local.json`에 이미 다음 hooks가 있음:
- SessionStart: docker/git 상태, context-health, QMD
- PreToolUse: 프로덕션 파일 보호, git commit 검증
- PostToolUse: context-guard, git PR 안내
- Stop: 프로세스 경고

**병합 전략**: 글로벌 hooks가 먼저 실행되고, 프로젝트 hooks가 추가 실행됨.
- PostToolUse `Edit|Write`: 글로벌(change-logger) → 프로젝트(context-guard) 순서. 충돌 없음.
- Stop: 글로벌(quality-nudge) → 프로젝트(프로세스 경고) 순서. 충돌 없음.

**Step 4: JSON 유효성 검증**

Run: `cat ~/.claude/settings.json | jq . > /dev/null && echo "VALID" || echo "INVALID"`
Expected: `VALID`

**Step 5: 새 세션에서 동작 확인**

새 Claude Code 세션을 열고 "백엔드 API를 만들어줘"를 입력했을 때 `📋 관련 스킬 감지:` 메시지가 보이는지 확인.

---

## Task 6: 3종 문서 템플릿 생성

**Files:**
- Create: `~/.claude/templates/context-note.md`
- Create: `~/.claude/templates/checklist.md`

**Step 1: 맥락노트 템플릿**

```markdown
# [TITLE] — 맥락노트

> 생성일: [DATE]
> 관련 계획: docs/plans/[PLAN_FILE]

## 왜 이 방식을 선택했는가

- 결정 1: [무엇을 결정했는가] — [근거]
- 결정 2: [무엇을 결정했는가] — [근거]

## 대안과 트레이드오프

| 대안 | 장점 | 단점 | 선택 여부 |
|------|------|------|----------|
| [대안 A] | | | 선택됨 / 기각 |
| [대안 B] | | | 선택됨 / 기각 |

## 관련 자료

- 파일: [변경된/참조된 파일 경로 목록]
- 이전 논의: [세션 ID, 커밋 해시, 또는 이슈 번호]
- 외부 참조: [문서 URL, 라이브러리 문서 등]

## 주의사항

- [알려진 제약 조건]
- [향후 리스크]
- [의존성 변경 시 영향받는 부분]
```

**Step 2: 체크리스트 템플릿**

```markdown
# [TITLE] — 체크리스트

> 생성일: [DATE]
> 관련 계획: docs/plans/[PLAN_FILE]
> 마지막 업데이트: [DATE]

## 진행 상황

- [ ] Step 1: [설명]
- [ ] Step 2: [설명]
- [x] Step 3: [완료된 항목]

## 현재 세션 메모

- [이번 세션에서 작업한 내용 요약]
- [다음 세션에서 이어서 할 작업]

## 발견사항

- [작업 중 발견된 이슈]
- [예상과 달랐던 점]

## 블로커

- [현재 막혀 있는 부분이 있다면]
```

**Step 3: 템플릿 디렉토리 생성 확인**

Run: `ls ~/.claude/templates/`
Expected: `context-note.md`, `checklist.md` 파일 존재

---

## Task 7: 글로벌 CLAUDE.md 업데이트

**Files:**
- Modify: `~/.claude/CLAUDE.md` — 3개 섹션 추가

**Step 1: "작업 기억 규칙" 섹션 추가**

`## 컨텍스트 효율 규칙` 섹션 바로 아래에 추가:

```markdown
## 작업 기억 규칙 (3종 문서)
- 3+ 단계 구현 작업 시작 전 → 3종 문서 생성 필수:
  - 계획서: `docs/plans/YYYY-MM-DD-<topic>-design.md` (brainstorming 산출물)
  - 맥락노트: `docs/plans/YYYY-MM-DD-<topic>-context.md` (결정 근거)
  - 체크리스트: `docs/plans/YYYY-MM-DD-<topic>-checklist.md` (진행 추적)
- 템플릿: `~/.claude/templates/` 참조
- 새 세션 이어받기: "docs/plans/ 최신 체크리스트 읽고 이어서 작업"
- 작업 완료마다 체크리스트 업데이트
- 세션 종료 전: 맥락노트에 미완료 사항 기록
```

**Step 2: "에이전트 보고서 규칙" 섹션 추가**

```markdown
## 에이전트 보고서 규칙
- Task tool 서브에이전트 결과물은 4섹션 구조 필수:
  - 발견사항 (What I Found)
  - 수행한 작업 (What I Did)
  - 판단 근거 (Why)
  - 미해결 사항 (Open Items)
- "다 했습니다"만 반환하면 → 상세 보고서 재요청
- PR 생성 직전 → superpowers:requesting-code-review 실행 필수
```

**Step 3: "프론트엔드 아키텍처 규칙" 섹션 추가**

```markdown
## 프론트엔드 아키텍처 규칙
- **Seed Design First**: 모든 UI는 Seed Design 컴포넌트 우선. 없으면 커스텀 (근거 필수)
- **아이콘**: `lucide-react` 전용. heroicons/react-icons/font-awesome 금지
- **API 패턴**: 추상 BaseAPI 상속 → 도메인별 API (JobAPI, AuthAPI 등). 직접 fetch 금지
- **폴더 구조**: components/ | pages/ | hooks/ | api/ | types/ | utils/ | constants/
- **토큰/스타일**: Seed Design 토큰만 사용. 반응형은 Tailwind breakpoint (sm/md/lg/xl)
```

**Step 4: 검증 — CLAUDE.md 토큰 크기 확인**

Run: `wc -c ~/.claude/CLAUDE.md`
Expected: 5000B 미만 유지 (context-health.sh 경고 기준)

---

## Task 8: frontend-verifier 에이전트 업데이트

**Files:**
- Modify: `/Users/sabyun/goinfre/IaaS/.claude/agents/frontend-verifier.md`

**Step 1: 아키텍처 규칙 검증 섹션 추가**

기존 `## Verification Sequences` 앞에 새 섹션 추가:

```markdown
## Architecture Rule Verification

### Rule 1: Seed Design First
- Grep: 커스텀 HTML 태그 (`<button`, `<input`, `<select` 등)가 Seed Design 컴포넌트 대신 사용되었는지
- 검증: `@seed-design/` import 존재 여부

### Rule 2: lucide-react Only
- Grep: `from "heroicons"`, `from "react-icons"`, `from "@fortawesome"` — 금지 패턴
- 검증: 아이콘은 `from "lucide-react"` import만 허용

### Rule 3: BaseAPI Inheritance
- Grep: 직접 `fetch(`, `axios.` 호출 — 금지 패턴
- 검증: API 호출은 `api/` 디렉토리의 클래스 메서드만 사용

### Rule 4: Folder Structure
- 검증: 새 파일이 표준 폴더(components/pages/hooks/api/types/utils/constants)에 위치하는지

### Rule 5: Design Tokens
- Grep: 하드코딩 색상 (`#`, `rgb(`, `hsl(`) — 금지 패턴
- 검증: Seed Design 토큰 또는 Tailwind 클래스만 사용
```

**Step 2: Output Format에 아키텍처 검증 추가**

기존 Output Format의 `### E2E Results` 앞에 추가:

```markdown
### Architecture Rules
| Rule | Status | Violations |
|------|--------|-----------|
| Seed Design First | pass/fail | {details} |
| lucide-react Only | pass/fail | {details} |
| BaseAPI Inheritance | pass/fail | {details} |
| Folder Structure | pass/fail | {details} |
| Design Tokens | pass/fail | {details} |
```

---

## Task 9: 나머지 에이전트에 보고서 포맷 추가

**Files:**
- Modify: `/Users/sabyun/goinfre/IaaS/.claude/agents/design-specialist.md`
- Modify: `/Users/sabyun/goinfre/IaaS/.claude/agents/output-quality-reviewer.md`
- Modify: `/Users/sabyun/goinfre/IaaS/.claude/agents/pipeline-debugger.md`
- Modify: `/Users/sabyun/goinfre/IaaS/.claude/agents/prompt-optimizer.md`
- Modify: `/Users/sabyun/goinfre/IaaS/.claude/agents/i18n-checker.md`

**Step 1: 각 에이전트 상단에 표준 보고서 규칙 추가**

각 에이전트 파일의 `## Role` 섹션 바로 아래에 다음을 추가:

```markdown
## Report Standard

모든 보고서는 4섹션 구조를 따른다:
1. **발견사항 (What I Found)** — 분석/검증 결과
2. **수행한 작업 (What I Did)** — 실제 변경/수정 내역
3. **판단 근거 (Why)** — 왜 그렇게 판단/수정했는지
4. **미해결 사항 (Open Items)** — 남은 이슈, 후속 작업
```

**Step 2: 각 에이전트의 기존 Output Format이 4섹션과 대응되는지 확인**

이미 구조화된 Output Format이 있는 에이전트들은 매핑만 명시:
- `output-quality-reviewer.md`: Cross-Tab=발견, Action Items=미해결
- `pipeline-debugger.md`: Root Cause=발견, Recommendation=미해결
- `prompt-optimizer.md`: Changes Summary=수행, Expected Impact=판단근거
- `i18n-checker.md`: 각 테이블=발견, Summary=미해결
- `design-specialist.md`: Design Direction=판단근거, Implementation=수행

**Step 3: 검증**

Run: `grep -l "Report Standard" /Users/sabyun/goinfre/IaaS/.claude/agents/*.md | wc -l`
Expected: `6` (모든 에이전트)

---

## Task 10: 통합 검증

**Step 1: 새 Claude Code 세션 시작**

Run: `claude` (새 세션)

**Step 2: 시스템 1 검증 — 자동 매뉴얼 주입**

입력: "백엔드 API 엔드포인트를 만들어줘"
Expected: `📋 관련 스킬 감지: [backend] /arch-api, /arch-data` 메시지가 system-reminder로 표시

입력: "React 컴포넌트를 추가해줘"
Expected: `📋 관련 스킬 감지: [frontend]` + Seed Design 넛지 메시지

**Step 3: 시스템 3 검증 — 변경 로그 + 셀프체크**

세션에서 파일을 수정한 후 `/clear`로 종료하면 품질 넛지 출력 확인.

**Step 4: 시스템 2 검증 — CLAUDE.md 규칙 확인**

입력: "5단계 작업을 시작하려고 해"
Expected: AI가 3종 문서 생성을 제안하는지 확인

**Step 5: 시스템 4 검증 — 에이전트 보고서**

Task tool로 서브에이전트 실행 시 4섹션 보고서 형태로 반환되는지 확인.

---

## 파일 요약

| # | 파일 | 액션 | 시스템 |
|---|------|------|--------|
| 1 | `~/.claude/scripts/skill-rules.json` | Create | 1 |
| 2 | `~/.claude/scripts/quality-rules.json` | Create | 3 |
| 3 | `~/.claude/scripts/skill-injector.sh` | Create | 1 |
| 4 | `~/.claude/scripts/change-logger.sh` | Create | 3 |
| 5 | `~/.claude/scripts/quality-nudge.sh` | Create | 3 |
| 6 | `~/.claude/settings.json` | Modify | 1+3 |
| 7 | `~/.claude/templates/context-note.md` | Create | 2 |
| 8 | `~/.claude/templates/checklist.md` | Create | 2 |
| 9 | `~/.claude/CLAUDE.md` | Modify | 2+4 |
| 10 | `.claude/agents/frontend-verifier.md` | Modify | 4 |
| 11-15 | `.claude/agents/*.md` (5개) | Modify | 4 |
