---
name: linear-ops
description: Linear 티켓 기반 개발 워크플로우. 티켓 분석 → 코드 수정 → 테스트 검증 → 결과 보고를 하나의 트랜잭션으로 처리.
argument-hint: [ticket-id | "create" title] [--tdd] [--close]
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Linear-Ops Skill

> linear-api.sh 셸 함수를 활용하여 **[티켓 분석 → 코드 수정 → 테스트 검증 → 결과 보고]**를 하나의 트랜잭션으로 처리한다.

---

## 사용법

```
/linear-ops JIT-26              # 기존 티켓 작업 시작 (identifier 자동 resolve)
/linear-ops create "제목"        # 새 티켓 생성 후 작업
/linear-ops list                 # 할당된 이슈 목록 조회
/linear-ops search "키워드"      # 이슈 검색
```

---

## Linear API 셋업

모든 Linear 호출은 linear-api.sh를 source하여 사용한다.
API 키는 자동으로 settings.local.json에서 감지된다.

```bash
source /Users/sabyun/goinfre/IaaS/.claude/skills/linear-ops/linear-api.sh

# 주요 함수 (JIT-26 형식 identifier 또는 UUID 모두 지원)
linear_search_issues "JIT-26" 5       # 이슈 검색
linear_get_issue "JIT-26"             # 이슈 상세 조회
linear_update_status "JIT-26" done    # 상태 변경
linear_add_comment "JIT-26" "본문"    # 코멘트 추가
linear_create_issue "제목" "팀ID"     # 이슈 생성
linear_list_teams                     # 팀 목록
```

---

## Phase 1: Initialize (작업 시작 및 컨텍스트 동기화)

### 기존 티켓 작업 시
1. `linear_get_issue "JIT-N"` → 최신 본문, 라벨, 우선순위 읽기
2. 티켓 본문에서 **수락 기준(Acceptance Criteria)** 추출
3. 수락 기준이 없을 경우 → 사용자에게 "수락 기준을 먼저 정의할까요?" 확인
4. 코드베이스에서 수정 필요 지점 분석 → 사용자에게 영향 범위 출력
5. `linear_update_status "JIT-N" in_progress` → 상태 변경
6. Git 브랜치 생성: `but branch new feat/JIT-{N}-{slug}` 또는 `but branch new fix/JIT-{N}-{slug}`

### 새 티켓 생성 시
1. `linear_list_teams` → 팀 ID 확인
2. `linear_create_issue "제목" "팀ID" "설명" priority` → 이슈 생성
3. description에 반드시 아래 섹션 포함:
   ```markdown
   ## 수락 기준 (Acceptance Criteria)
   - [ ] 기준 1
   - [ ] 기준 2

   ## 테스트 시나리오
   - [ ] 시나리오 1: [입력] → [기대 결과]
   - [ ] 시나리오 2: [엣지 케이스] → [기대 결과]
   ```
4. 생성된 이슈를 In Progress로 변경 후 Phase 2 진입

### 목록/검색
- list: `linear_list_issues` → 상태별 정리하여 출력
- search: `linear_search_issues "키워드"` → 결과 테이블 출력

---

## Phase 2: TDD Implementation (티켓 기반 테스트 주도 개발)

### 2-1. 테스트 먼저 (Test First)

수락 기준에서 테스트 케이스를 도출하고, **코드 수정 전에 테스트를 먼저 작성/업데이트**한다.

**Backend (pytest):**
```
backend/tests/test_{feature}.py  → 신규 기능 테스트
backend/tests/                   → 기존 테스트 업데이트
```
- 실행: `docker compose exec backend pytest tests/test_{feature}.py -v --tb=short`
- 실패 확인 후 구현 진행 (Red → Green → Refactor)

**Frontend (vitest/playwright):**
```
frontend/src/**/*.test.ts        → 단위 테스트
frontend/e2e/*.spec.ts           → E2E 테스트
```
- 단위: `docker compose exec frontend npx vitest run --reporter=verbose`
- E2E: `cd frontend && npx playwright test`

### 2-2. 구현 (Implementation)

1. 수정 파일별 변경 사항 적용
2. 프로젝트 네이밍/배치 규칙 준수 (CLAUDE.md 참조)
3. 파일 300줄 초과 시 분리 검토

### 2-3. 테스트 실행 및 검증

```
# Backend 전체 테스트
docker compose exec backend pytest --tb=short -q

# Frontend 단위 테스트
docker compose exec frontend npx vitest run

# 실패한 테스트만 재실행
docker compose exec backend pytest --last-failed -v

# 커버리지 확인
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

### 2-4. 테스트 실패 대응

테스트 실패 시 **절대 Linear 티켓을 업데이트하지 않는다.**

1. 에러 로그 분석 → 근본 원인 식별
2. 코드 재수정 → 테스트 재실행
3. 3회 실패 시 → 사용자에게 에러 리포트:
   ```
   [Test Failure Report]
   - 실패 테스트: test_name
   - 에러 메시지: ...
   - 시도한 수정: ...
   - 제안: ...
   ```
4. 전체 테스트 커버리지가 감소하지 않았는지 확인

---

## Phase 3: Finalize (결과 보고 및 클로징)

### 조건: 모든 테스트 통과 시에만 진행

### 3-1. 티켓 업데이트 (코멘트 추가)

코멘트 본문에 마크다운 특수문자가 많으면 파일 기반 입력을 사용한다:

```bash
# 직접 본문 전달
linear_add_comment "JIT-N" "## 구현 완료\n\n### 수정 파일\n- file1.py"

# 파일에서 읽기 (권장 — 특수문자 안전)
linear_add_comment "JIT-N" @/tmp/review_comment.md
```

코멘트 본문 템플릿:
```markdown
## 구현 결과

### [Summary]
{구현된 기능의 기술적 요약}

### [Files Changed]
- path/to/file1.py — 변경 내용 요약

### [Test Result]
- 결과: ALL PASSED (X passed, 0 failed)

### [Commit]
- 브랜치: feat/JIT-{N}-slug
- 커밋: {커밋 해시}
```

### 3-2. 상태 업데이트
- `linear_update_status "JIT-N" in_review`

### 3-3. GitButler 커밋, PR, 머지 및 완료 (but-ops 스킬 참조)
1. 스테이징: `but stage <file-id> {branch}`
2. 커밋 (Claude가 메시지 작성): `but commit --only -m "feat: {설명} [JIT-{N}]" {branch}`
3. 푸시: `but push {branch}`
4. PR 생성: `but pr {branch}`
5. 머지: `but merge {branch}`
6. `but pull` → 타겟 브랜치 동기화
7. `linear_update_status "JIT-N" done` → 티켓 완료 처리

---

## 예외 처리 (Guardrails)

| 상황 | 대응 |
|------|------|
| Linear API 권한 오류 | 즉시 사용자에게 알림 → API Key 확인 요청 |
| 수락 기준 없는 티켓 | 작업 시작 전 "수락 기준을 먼저 정의할까요?" 확인 |
| 테스트 실패 | Linear 업데이트 금지, 에러 분석 후 재시도 또는 사용자 리포트 |
| 티켓 ID 미발견 | linear_search_issues로 유사 이슈 검색 후 제안 |
| 모호한 요구사항 | 사용자에게 구체화 질문 후 진행 |
| 커버리지 감소 | 추가 테스트 작성 후 재검증 |

---

## 워크플로우 다이어그램

```
/linear-ops JIT-26
    |
    +- Phase 1: Initialize
    |   +- linear_get_issue → 티켓 읽기
    |   +- 수락 기준 확인 (없으면 → 사용자 확인)
    |   +- 코드베이스 영향 분석
    |   +- linear_update_status → in_progress
    |   +- but branch new feat/JIT-26-slug
    |
    +- Phase 2: TDD Implementation
    |   +- 수락 기준 → 테스트 케이스 도출
    |   +- 테스트 작성 (Red)
    |   +- 코드 구현 (Green)
    |   +- 리팩토링 (Refactor)
    |   +- 전체 테스트 실행
    |   +- [실패 시] 재수정 루프 (최대 3회)
    |
    +- Phase 3: Finalize (테스트 통과 시만)
        +- linear_add_comment → 결과 기록
        +- linear_update_status → in_review
        +- but commit -m "msg" branch (Claude 메시지 작성)
        +- but push branch
        +- but pr branch
        +- but merge branch
        +- but pull
        +- linear_update_status → done
```

---

## 활용 MCP 서버

| 서버 | 용도 |
|------|------|
| sequential | 복잡한 티켓 분석, 수정 영향 범위 추론 |
| context7 | 프레임워크/라이브러리 공식 문서 참조 |
| docker | 컨테이너 내 테스트 실행 |

---

## 출력 포맷

### 작업 시작 시
```
[Linear-Ops] JIT-26 작업 시작
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
제목: {title}
우선순위: {priority}
상태: → In Progress

수락 기준:
  - 기준 1
  - 기준 2

영향 파일:
  backend/app/services/foo.py (L45-78)
  frontend/src/components/Bar.tsx (L12-30)

브랜치: feat/JIT-26-slug
```

### 작업 완료 시
```
[Linear-Ops] JIT-26 작업 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
수정 파일: 3개
테스트: 12 passed, 0 failed
커버리지: 85% (변동 없음)
상태: → In Review
PR: #270 (feat: 설명 [JIT-26])
```
