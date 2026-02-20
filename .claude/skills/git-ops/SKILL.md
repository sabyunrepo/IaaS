---
name: git-ops
description: 표준 Git + GitHub CLI 기반 워크플로우. 브랜치 생성, 커밋, 푸시, PR, 머지를 git/gh 명령어로 처리.
argument-hint: [commit | branch | push | pr | status]
allowed-tools: Bash, Read, Grep, Glob
---

# Git-Ops Skill (표준 Git + GitHub CLI)

> 표준 `git` + `gh` CLI를 사용한 Git 워크플로우.
> **커밋 메시지는 Claude가 직접 작성.**

---

## 전제 조건

- `git` CLI 설치됨
- `gh` CLI 설치 및 인증됨: `gh auth status`
- 원격 저장소 연결됨: `git remote -v`

---

## 워크플로우

### 1. 상태 확인

```bash
git status
git diff --stat
```

### 2. 브랜치 생성

```bash
# 최신 main에서 새 브랜치
git checkout main && git pull origin main
git checkout -b feat/JIT-26-feature-name

# 또는 현재 브랜치에서 분기
git checkout -b feat/JIT-26-feature-name
```

### 3. 파일 스테이징

```bash
# 특정 파일
git add path/to/file1.py path/to/file2.py

# 디렉토리 전체
git add src/components/

# 변경사항 확인 후 스테이징
git diff --name-only
git add <file>
```

### 4. 커밋

```bash
# 간단한 커밋
git commit -m "feat: 기능 설명 [JIT-26]"

# 본문 포함 커밋 (HEREDOC)
git commit -m "$(cat <<'EOF'
feat: 기능 설명 [JIT-26]

상세 설명 본문
EOF
)"
```

### 5. 푸시

```bash
# 첫 푸시 (upstream 설정)
git push -u origin feat/JIT-26-feature-name

# 이후 푸시
git push
```

### 6. PR 생성

```bash
gh pr create --title "feat: 기능 설명 [JIT-26]" --body "$(cat <<'EOF'
## Summary
- 변경 내용 요약

## Test plan
- [ ] 테스트 항목
EOF
)"
```

### 7. 머지

```bash
# PR 머지 (squash)
gh pr merge <PR번호> --squash

# 머지 후 로컬 동기화
git checkout main && git pull origin main

# 완료된 브랜치 삭제
git branch -d feat/JIT-26-feature-name
```

### 8. 되돌리기

```bash
# 마지막 커밋 취소 (변경사항 유지)
git reset --soft HEAD~1

# 특정 커밋 되돌리기
git revert <commit-hash>

# 스테이징 취소
git restore --staged <file>
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
3. 본문 필요시 HEREDOC 사용

---

## 다른 스킬에서 사용 시

### linear-ops 연동
```
Phase 1: git checkout -b feat/JIT-{N}-{slug}
Phase 2: (코드 수정 + 테스트)
Phase 3: git add → git commit → git push → gh pr create
```

### 일반 커밋 플로우
```
git status → git add → git commit -m "msg" → git push
```

---

## 예외 처리

| 상황 | 대응 |
|------|------|
| 충돌 발생 | 충돌 파일 수동 해결 → `git add` → `git commit` |
| 실수한 커밋 | `git reset --soft HEAD~1` → 재작업 |
| 원격 브랜치 뒤처짐 | `git pull --rebase origin main` |
| 잘못된 브랜치에서 작업 | `git stash` → `git checkout correct-branch` → `git stash pop` |

---

## 주의사항

- `git push --force` 사용 금지 (사용자 명시 요청 시에만)
- `git reset --hard` 사용 전 반드시 확인
- 민감 파일(.env, credentials) 커밋 금지
- PR 생성 전 `git diff main...HEAD`로 변경 범위 확인
