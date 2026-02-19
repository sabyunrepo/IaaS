---
name: but-ops
description: GitButler CLI(but) 기반 Git 워크플로우. 브랜치 생성, 커밋, 푸시, PR, 머지를 but 명령어로 처리.
argument-hint: [commit | branch | push | pr | status | teardown]
allowed-tools: Bash, Read, Grep, Glob
---

# But-Ops Skill (GitButler CLI)

> `but` CLI를 사용한 Git 워크플로우. 기존 `git` 명령어를 대체한다.
> **커밋 메시지는 Claude가 직접 작성** (`--ai` 플래그 사용하지 않음).

---

## 전제 조건

- GitButler CLI 설치됨: `~/.local/bin/but` (v0.19.2+)
- 프로젝트 셋업 완료: `but setup` 실행됨
- `gitbutler/workspace` 브랜치 활성 상태

---

## 핵심 명령어 매핑 (git → but)

| 기존 git | but 대체 | 비고 |
|----------|---------|------|
| `git status` | `but status` | 병렬 브랜치 + unstaged 통합 표시 |
| `git checkout -b name` | `but branch new name` | 워크스페이스 내 병렬 생성 |
| `git add file` | `but stage <id> <branch>` | CLI ID 사용 (status에서 확인) |
| `git commit -m "msg"` | `but commit -m "msg" <branch>` | `--only`: staged만 커밋 |
| `git push -u origin` | `but push` | 모든 브랜치 자동 푸시 |
| `git diff` | `but diff` | 미커밋 변경사항 |
| `git log` | `but show <branch>` | 브랜치별 커밋 이력 |
| `gh pr create` | `but pr` | GitHub PR 자동 생성 |
| `git merge` | `but merge <branch>` | 타겟 브랜치에 머지 |
| `git stash` | 불필요 | 병렬 브랜치로 대체 |
| (없음) | `but undo` | 마지막 작업 되돌리기 |
| (없음) | `but absorb` | 변경사항을 적절한 커밋에 자동 흡수 |
| (없음) | `but teardown` | 일반 Git 모드로 복귀 |

---

## 워크플로우

### 1. 상태 확인

```bash
but status
```

출력에서 각 파일의 **CLI ID** (2~3글자 코드, 예: `qn`, `mv`)를 확인한다.
이 ID를 `stage`, `commit --changes` 등에서 사용한다.

### 2. 브랜치 생성

```bash
# 새 브랜치 (병렬)
but branch new feat/JIT-26-feature-name

# 스택 브랜치 (기존 브랜치 위에)
but branch new child-branch -a parent-branch
```

### 3. 파일 스테이징

```bash
# 특정 파일을 특정 브랜치에 스테이징
but stage <file-cli-id> <branch-name>

# 여러 파일
but stage mv feat/JIT-26-slug
but stage qn feat/JIT-26-slug
```

### 4. 커밋

```bash
# staged 파일만 커밋 (--only)
but commit --only -m "feat: 기능 설명 [JIT-26]" <branch-name>

# 모든 미커밋 변경사항 포함 커밋
but commit -m "feat: 기능 설명" <branch-name>

# 특정 파일만 포함 (스테이징 없이)
but commit -m "msg" --changes mv,qn <branch-name>
```

### 5. 푸시

```bash
# 모든 브랜치 푸시
but push

# 특정 브랜치만
but push <branch-name>
```

### 6. PR 생성

```bash
but pr <branch-name>
```

### 7. 머지

```bash
but merge <branch-name>
```

### 8. 되돌리기

```bash
# 마지막 작업 취소
but undo

# 작업 이력 확인
but oplog
```

---

## 커밋 메시지 규칙

Claude가 직접 작성하며 다음 규칙을 따른다:

### 형식
```
<type>: <한글 설명> [JIT-N]
```

### Type 종류
| type | 용도 |
|------|------|
| `feat` | 새로운 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 추가/수정 |
| `refactor` | 코드 리팩토링 |
| `test` | 테스트 추가/수정 |
| `chore` | 설정, 빌드, 기타 |
| `style` | 코드 스타일 변경 |
| `perf` | 성능 개선 |

### 규칙
1. 한글로 간결하게 (50자 이내)
2. Linear 티켓 있으면 `[JIT-N]` 접미사
3. 본문 필요시 `--message-file` 사용
4. Co-Author 불필요 (Claude가 작성한다는 것은 but oplog에 기록됨)

---

## 다른 스킬에서 사용 시

### linear-ops 연동
```
Phase 1: but branch new feat/JIT-{N}-{slug}
Phase 2: (코드 수정 + 테스트)
Phase 3: but commit → but push → but pr
```

### 일반 커밋 플로우
```
but status → but stage → but commit -m "msg" branch → but push
```

---

## 예외 처리

| 상황 | 대응 |
|------|------|
| workspace 미설정 | `but setup` 실행 |
| 충돌 발생 | `but resolve` 사용 |
| 실수한 커밋 | `but undo` → 재작업 |
| 일반 Git 복귀 필요 | `but teardown` |
| 특정 브랜치 checkout 필요 | `git checkout <branch>` (자동 teardown) |

---

## 주의사항

- `but commit --ai` 사용 금지 (OpenAI API 키 미설정, Claude가 메시지 작성)
- `but setup` 후 `gitbutler/workspace` 브랜치로 전환됨
- 일반 `git` 명령어(log, blame 등 읽기 전용)는 그대로 사용 가능
- `but teardown`으로 언제든 일반 Git 모드 복귀 가능
