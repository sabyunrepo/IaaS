# Dev Pipeline Automation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Obsidian 설계 → Linear 이슈 → 구현 → Obsidian 동기화를 자동화하는 3개 스킬(`/phase-plan`, `/phase-sync`, `/phase-pipeline`) 구현

**Architecture:** 기존 `obsidian-api.sh` + `linear-api.sh` 래퍼 위에 3개 독립 스킬을 SKILL.md 마크다운으로 정의. Linear API에 마일스톤(프로젝트) 생성 함수를 추가하고, 파이프라인 상태를 `.claude/pipeline-state.json`으로 관리.

**Tech Stack:** Claude Code Skills (Markdown), Bash shell functions, Linear GraphQL API, Obsidian REST API

**설계 문서:** `docs/plans/2026-02-19-dev-pipeline-design.md`

---

### Task 1: 디렉토리 정리 및 Linear API 확장

이전 브레인스토밍에서 생성된 빈 디렉토리(phase-designer, phase-planner, phase-syncer)를 제거하고, 설계에 맞는 새 디렉토리를 생성한다. Linear API에 마일스톤(프로젝트) 관련 함수를 추가한다.

**Files:**
- Delete: `.claude/skills/phase-designer/` (빈 디렉토리)
- Delete: `.claude/skills/phase-planner/` (빈 디렉토리)
- Delete: `.claude/skills/phase-syncer/` (빈 디렉토리)
- Create: `.claude/skills/phase-plan/` (디렉토리)
- Create: `.claude/skills/phase-sync/` (디렉토리)
- Create: `.claude/skills/phase-pipeline/` (디렉토리)
- Modify: `.claude/skills/linear-ops/linear-api.sh`

**Step 1: 빈 디렉토리 제거**

```bash
rm -rf .claude/skills/phase-designer .claude/skills/phase-planner .claude/skills/phase-syncer
```

**Step 2: 새 디렉토리 생성**

```bash
mkdir -p .claude/skills/phase-plan .claude/skills/phase-sync .claude/skills/phase-pipeline
```

**Step 3: Linear API에 마일스톤 함수 추가**

`linear-api.sh` 끝에 다음 함수들을 추가:

```bash
# ── Milestone (Project) 함수 ──

linear_create_project() {
  # 프로젝트(마일스톤) 생성
  # Usage: linear_create_project "이름" "team-uuid" ["설명"]
  local name="$1"
  local team_id="$2"
  local description="${3:-}"
  _linear_gql '
    mutation($name: String!, $teamIds: [String!]!, $desc: String) {
      projectCreate(input: { name: $name, teamIds: $teamIds, description: $desc }) {
        success
        project { id name state slugId url }
      }
    }
  ' "$(jq -n --arg n "$name" --arg tid "$team_id" --arg d "$description" '{name: $n, teamIds: [$tid], desc: $d}')"
}

linear_assign_issue_to_project() {
  # 이슈를 프로젝트(마일스톤)에 할당
  # Usage: linear_assign_issue_to_project "issue-id" "project-id"
  local input="$1"
  local project_id="$2"
  local issue_id
  issue_id=$(_linear_resolve_id "$input") || return 1
  _linear_gql '
    mutation($id: String!, $projectId: String!) {
      issueUpdate(id: $id, input: { projectId: $projectId }) {
        success
        issue { id identifier title project { name } }
      }
    }
  ' "$(jq -n --arg id "$issue_id" --arg pid "$project_id" '{id: $id, projectId: $pid}')"
}

linear_list_project_issues() {
  # 프로젝트(마일스톤)의 이슈 목록 조회
  # Usage: linear_list_project_issues "project-id" [limit]
  local project_id="$1"
  local first="${2:-50}"
  _linear_gql '
    query($pid: String!, $first: Int) {
      project(id: $pid) {
        name state
        issues(first: $first) {
          nodes {
            id identifier title
            state { name }
            priority priorityLabel
          }
        }
      }
    }
  ' "$(jq -n --arg pid "$project_id" --argjson first "$first" '{pid: $pid, first: $first}')"
}
```

**Step 4: Linear API 함수 테스트**

```bash
cd /Users/sabyun/goinfre/IaaS
source .claude/skills/linear-ops/linear-api.sh
linear_list_projects 5
```

Expected: 기존 프로젝트 목록 JSON 반환

**Step 5: 커밋**

```bash
git add .claude/skills/linear-ops/linear-api.sh
git commit -m "feat: Linear API에 마일스톤(프로젝트) 관리 함수 추가"
```

---

### Task 2: `/phase-plan` 스킬 작성

Obsidian 설계 문서를 읽고 → Linear 마일스톤/이슈를 생성하는 스킬.

**Files:**
- Create: `.claude/skills/phase-plan/SKILL.md`

**Step 1: SKILL.md 작성**

```markdown
---
name: phase-plan
description: Obsidian 설계 문서 → Linear 마일스톤/이슈 자동 생성. Phase별 구현 계획을 Linear에 반영.
argument-hint: [phase_number]
allowed-tools: Bash, Read, Grep, Glob, Write
---

# Phase Plan Skill

> Phase 설계 문서를 분석하여 **Linear 마일스톤(프로젝트) + 이슈**를 자동 생성한다.

---

## 사용법

```
/phase-plan 1          # Phase 1 계획 생성
/phase-plan 2          # Phase 2 계획 생성
```

---

## 셋업

```bash
source /Users/sabyun/goinfre/IaaS/.claude/skills/linear-ops/linear-api.sh
source /Users/sabyun/goinfre/IaaS/.claude/skills/obsidian-api/obsidian-api.sh
```

---

## Phase 매핑

| Phase | 설계 문서 경로 | 설명 |
|-------|--------------|------|
| 0 | `plan/v5-design/phase0-scaffolding.md` | 프로젝트 스캐폴딩 |
| 1 | `plan/v5-design/phase1-domain.md` | 도메인 레이어 |
| 2 | `plan/v5-design/phase2-infrastructure.md` | 인프라 레이어 |
| 3 | `plan/v5-design/phase3-application.md` | 애플리케이션 레이어 |
| 4 | `plan/v5-design/phase4-questions.md` | 질문 생성 |
| 5 | `plan/v5-design/phase5-output-frontend.md` | 출력 + 프론트엔드 |
| 6 | `plan/v5-design/phase6-testing.md` | 테스트 + 벤치마크 |

Obsidian Vault의 해당 아키텍처 문서도 참조:
- `docs/architecture/MOC.md` — 전체 구조 맵
- `docs/architecture/domain/MOC.md` — 도메인별 세부

---

## 실행 흐름

### Phase 1: Initialize

1. Phase 번호에서 설계 문서 경로 결정
2. 로컬 파일 읽기: `plan/v5-design/phase{N}-*.md`
3. Obsidian Vault에서 관련 아키텍처 문서 읽기:
   ```bash
   obsidian_status
   obsidian_vault_get "domain/MOC.md"
   obsidian_vault_get "RELATION-MAP.md"
   ```
4. Jittda 팀 ID 확인: `588a6c89-bc94-45c3-b9a0-7405913e86d8`

### Phase 2: Analyze

1. 설계 문서에서 **구현 항목** 추출:
   - `## §N.` 섹션 헤더 → 이슈 제목 후보
   - `### Step N:` → 하위 태스크
   - 코드 블록 → 구현 파일 경로
   - `Linear 티켓 매핑` 테이블 → 기존 매핑 참조

2. Linear 기존 이슈 조회 (중복 방지):
   ```bash
   linear_search_issues "Phase {N}" 30
   ```
   - 이미 Done인 이슈 → 스킵
   - In Progress인 이슈 → 참조 노트 추가
   - 없으면 → 새로 생성

3. **planning_discoveries** 수집:
   - 설계 문서에 있지만 아키텍처 문서에 없는 항목
   - 설계 문서와 아키텍처 문서의 불일치
   - 설계 문서에서 참조하는 미존재 모듈

### Phase 3: Create

1. Linear 마일스톤(프로젝트) 생성:
   ```bash
   linear_create_project "Phase {N}: {이름}" "588a6c89-bc94-45c3-b9a0-7405913e86d8" "설명"
   ```

2. 이슈 생성 (의존관계 반영):
   ```bash
   linear_create_issue "이슈 제목" "588a6c89-bc94-45c3-b9a0-7405913e86d8" "설명" priority
   linear_assign_issue_to_project "JIT-XXX" "project-id"
   ```

3. 이슈 간 의존관계는 description에 `Depends on: JIT-XXX` 형태로 명시

### Phase 4: Cache

파이프라인 상태 저장:

```bash
cat > .claude/pipeline-state.json << 'PIPEOF'
{
  "current_phase": N,
  "step": "awaiting_implementation",
  "plan_completed_at": "ISO_TIMESTAMP",
  "sync_completed_at": null,
  "milestone_id": "project-uuid",
  "issues": ["JIT-XXX", "JIT-YYY"],
  "planning_discoveries": []
}
PIPEOF
```

---

## 출력 형식

```
[Phase-Plan] Phase {N} 계획 생성 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

마일스톤: Phase {N}: {이름}

| # | 이슈 | 의존 | 상태 |
|---|------|------|------|
| JIT-XXX | 제목 | - | Backlog |
| JIT-YYY | 제목 | JIT-XXX | Backlog |

발견 사항 (planning_discoveries):
- [mismatch] file.md: 설명
- [missing] file.md: 설명

구현을 시작하세요.
완료 후 `/phase-sync {N}` 또는 `/phase-pipeline {N} --from sync`
```

---

## 예외 처리

| 상황 | 대응 |
|------|------|
| 설계 문서 미존재 | 에러 메시지 + 사용 가능한 Phase 목록 출력 |
| Linear API 오류 | API 키 확인 요청 |
| 중복 마일스톤 | 기존 마일스톤 재사용 (새로 생성 안 함) |
| Obsidian 미연결 | 경고 출력 후 로컬 파일만으로 진행 |
```

**Step 2: 스킬 파일 저장 확인**

```bash
ls -la .claude/skills/phase-plan/SKILL.md
```

Expected: 파일 존재 확인

**Step 3: 커밋**

```bash
git add .claude/skills/phase-plan/SKILL.md
git commit -m "feat: /phase-plan 스킬 추가 — Obsidian 설계 → Linear 이슈 자동 생성"
```

---

### Task 3: `/phase-sync` 스킬 작성

구현 완료 후 Git diff를 분석하여 Obsidian 설계 문서를 업데이트하는 스킬. 참조 체이닝 포함.

**Files:**
- Create: `.claude/skills/phase-sync/SKILL.md`

**Step 1: SKILL.md 작성**

```markdown
---
name: phase-sync
description: 구현 결과 → Obsidian 설계 동기화. Git diff 분석, 참조 체이닝 업데이트, 회고 기록, Linear 정리.
argument-hint: [phase_number]
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# Phase Sync Skill

> 구현 완료 후 **Git 변경사항을 분석**하여 Obsidian 설계 문서를 업데이트하고, 참조된 관련 문서도 체이닝으로 수정한다.

---

## 사용법

```
/phase-sync 1          # Phase 1 동기화
```

---

## 셋업

```bash
source /Users/sabyun/goinfre/IaaS/.claude/skills/linear-ops/linear-api.sh
source /Users/sabyun/goinfre/IaaS/.claude/skills/obsidian-api/obsidian-api.sh
```

---

## 실행 흐름

### Step 1: Collect (변경사항 수집)

1. `pipeline-state.json` 로딩:
   ```bash
   cat .claude/pipeline-state.json
   ```
   → `plan_completed_at` 타임스탬프 확인

2. Git diff 수집 (마일스톤 시작 ~ 현재):
   ```bash
   git log --oneline --since="PLAN_COMPLETED_AT" -- jittda/
   git diff --stat HEAD~N -- jittda/
   ```

3. 변경된 파일 분류:
   - 새로 생성된 파일 (domain, infrastructure 등)
   - 수정된 파일
   - 삭제된 파일

4. `planning_discoveries` 로딩 (이전 /phase-plan에서 수집)

### Step 2: Compare (설계 vs 구현 비교)

1. Phase 설계 문서 읽기:
   ```bash
   # 로컬
   cat plan/v5-design/phase{N}-*.md
   # Obsidian
   obsidian_vault_get "domain/MOC.md"
   ```

2. 차이 분석:
   | 유형 | 의미 | 대응 |
   |------|------|------|
   | 설계 O, 구현 X | 미구현 | 경고 출력 |
   | 설계 X, 구현 O | 설계 미반영 | Obsidian에 추가 |
   | 설계 ≠ 구현 | 차이 발생 | Obsidian 수정 |

3. 변경 목록 생성 → 사용자에게 미리보기 출력

### Step 3: Update (Obsidian 업데이트 + 참조 체이닝)

#### 3-1. 주 설계 문서 수정

```bash
# 수정된 내용을 임시 파일에 작성
cat > /tmp/obsidian_update.md << 'EOF'
# 수정된 내용
EOF

# Obsidian에 반영
obsidian_vault_put "domain/identity-resolution/models.md" @/tmp/obsidian_update.md
```

#### 3-2. 참조 체이닝 (최대 2단계)

수정된 문서에서 참조를 추출하고 관련 문서도 업데이트:

```
수정 대상: phase1-domain.md
  │
  ├─ Step 1: 위키링크 추출
  │   grep -oP '\[\[([^\]]+)\]\]' → 참조 문서 목록
  │
  ├─ Step 2: 각 참조 문서 확인
  │   obsidian_vault_get "domain/identity-resolution/MOC.md"
  │   → 영향 받는 내용 있으면 수정
  │
  ├─ Step 3: MOC.md 역참조
  │   obsidian_vault_get "MOC.md"
  │   → Phase N 관련 상태/진행률 업데이트
  │
  ├─ Step 4: RELATION-MAP.md
  │   obsidian_vault_get "RELATION-MAP.md"
  │   → 모듈 간 의존관계 업데이트
  │
  └─ Step 5: planning_discoveries 반영
      → 이전 /phase-plan에서 발견된 불일치도 이 시점에서 수정
```

**체이닝 규칙:**
- 깊이 최대 2단계 (직접 참조 → 1차 연결까지)
- 수정 전 diff 미리보기 → 사용자 확인
- 대량 수정 시 파일별로 확인 요청

### Step 4: Retrospective (회고 기록)

Obsidian에 회고 노트 생성:

```bash
obsidian_vault_put "Retrospectives/phase-{N}-retro.md" @/tmp/retro.md
```

회고 내용:
- 계획 대비 실제 차이점
- 예상 밖 변경사항
- 교훈 및 다음 Phase 주의사항
- 소요 시간/이슈 수 통계

### Step 5: Cleanup (정리)

1. Linear 이슈 상태 업데이트:
   ```bash
   linear_update_status "JIT-XXX" done
   ```

2. CLAUDE.md 컨텍스트 매핑 업데이트:
   - 완료된 Phase 마킹
   - 새로 발견된 참조 문서 추가

3. pipeline-state.json 업데이트:
   ```json
   {
     "step": "sync_completed",
     "sync_completed_at": "ISO_TIMESTAMP"
   }
   ```

---

## 출력 형식

```
[Phase-Sync] Phase {N} 동기화 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Obsidian 업데이트:
| 문서 | 유형 | 상세 |
|------|------|------|
| identity-resolution/models.md | 수정 | 모델 필드 추가 반영 |
| domain/MOC.md | 체이닝 | 상태 업데이트 |
| RELATION-MAP.md | 체이닝 | 의존관계 추가 |

Linear 정리:
- JIT-236: Done ✓
- JIT-237: Done ✓

회고:
- 계획: 7개 이슈 / 실제: 7개 완료, 1개 추가 발생
- 교훈: tree-sitter 버전 호환성 주의
```

---

## 예외 처리

| 상황 | 대응 |
|------|------|
| pipeline-state.json 미존재 | `/phase-plan` 먼저 실행 안내 |
| Obsidian 미연결 | 로컬 docs/architecture/ 직접 수정 + 경고 |
| Git diff 없음 | 구현 완료 여부 사용자 확인 |
| 체이닝 중 순환 참조 | 깊이 제한(2)으로 방지, 경고 출력 |
```

**Step 2: 스킬 파일 저장 확인**

```bash
ls -la .claude/skills/phase-sync/SKILL.md
```

Expected: 파일 존재 확인

**Step 3: 커밋**

```bash
git add .claude/skills/phase-sync/SKILL.md
git commit -m "feat: /phase-sync 스킬 추가 — 구현 결과 → Obsidian 동기화 + 참조 체이닝"
```

---

### Task 4: `/phase-pipeline` 오케스트레이터 스킬 작성

`/phase-plan` → 사용자 구현 → `/phase-sync`를 체이닝하는 오케스트레이터.

**Files:**
- Create: `.claude/skills/phase-pipeline/SKILL.md`

**Step 1: SKILL.md 작성**

```markdown
---
name: phase-pipeline
description: Phase 개발 파이프라인 오케스트레이터. plan → 구현 → sync를 체이닝하고 상태를 관리.
argument-hint: [phase_number] [--from sync] [--plan-only]
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# Phase Pipeline Skill

> `/phase-plan` → 사용자 구현 → `/phase-sync`를 하나의 워크플로우로 체이닝하는 **오케스트레이터**.

---

## 사용법

```
/phase-pipeline 1              # Phase 1 전체 파이프라인
/phase-pipeline 1 --from sync  # 구현 완료 후 sync부터 재개
/phase-pipeline 1 --plan-only  # 계획만 생성 (= /phase-plan 1)
```

---

## 실행 흐름

```
/phase-pipeline N
    │
    ├── Step 1: /phase-plan 호출
    │   ├── Obsidian 설계 문서 읽기
    │   ├── Linear 기존 이슈 확인
    │   ├── 마일스톤 + 이슈 생성
    │   └── pipeline-state.json 저장
    │
    ├── 🔒 Gate 1: 사용자 확인
    │   "Phase N 계획 생성 완료. 구현을 시작하세요."
    │   → 사용자가 구현 완료 후 재호출:
    │     /phase-pipeline N --from sync
    │
    ├── Step 2: /phase-sync 호출
    │   ├── Git diff 수집
    │   ├── Obsidian 설계 ↔ 구현 비교
    │   ├── Obsidian 업데이트 (참조 체이닝)
    │   ├── 회고 기록
    │   ├── Linear 이슈 상태 정리
    │   └── CLAUDE.md 업데이트
    │
    └── 🔒 Gate 2: 사용자 확인
        "Phase N 동기화 완료. 다음 Phase 진행?"
        → yes: /phase-pipeline [N+1]
        → no: 종료
```

---

## 상태 관리

파이프라인 상태 파일: `.claude/pipeline-state.json`

```json
{
  "current_phase": 1,
  "step": "awaiting_implementation | plan_completed | sync_completed",
  "plan_completed_at": "2026-02-19T14:00:00",
  "sync_completed_at": null,
  "milestone_id": "project-uuid",
  "issues": ["JIT-236", "JIT-237"],
  "planning_discoveries": []
}
```

### Step 상태 전이

```
(없음) → plan_completed → awaiting_implementation → sync_completed
                                                        │
                                                        └→ 다음 Phase로
```

---

## 명령어 분기

### `--from sync` (sync부터 재개)

1. `pipeline-state.json` 확인
2. `step == "awaiting_implementation"` 확인
3. `/phase-sync` 스킬 호출
4. Gate 2로 진행

### `--plan-only` (계획만)

1. `/phase-plan` 스킬 호출
2. Gate 1에서 종료 (sync 미실행)

### 기본 (전체 파이프라인)

1. `/phase-plan` 호출
2. Gate 1: 사용자에게 안내
3. 사용자가 `--from sync`로 재호출하면 계속

---

## Gate 출력

### Gate 1 (계획 완료)
```
[Phase-Pipeline] Gate 1: 계획 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase {N} 계획이 Linear에 생성되었습니다.
마일스톤: Phase {N}: {이름}
이슈: {count}개

구현을 시작하세요.
완료 후: /phase-pipeline {N} --from sync
```

### Gate 2 (동기화 완료)
```
[Phase-Pipeline] Gate 2: 동기화 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase {N} 동기화가 완료되었습니다.
- Obsidian: {count}개 문서 업데이트
- Linear: {count}개 이슈 Done
- 회고: phase-{N}-retro.md 작성

다음 Phase로 진행할까요?
→ /phase-pipeline {N+1}
→ 또는 여기서 종료
```

---

## 예외 처리

| 상황 | 대응 |
|------|------|
| `--from sync` 인데 plan 미완료 | "먼저 `/phase-plan {N}` 실행" 안내 |
| 이미 sync 완료된 Phase | "이미 완료. 다음 Phase 진행?" 안내 |
| pipeline-state.json 미존재 | 새로 시작 (plan부터) |
| Phase 번호 범위 초과 (0~6) | 에러 + 유효 범위 안내 |
```

**Step 2: 스킬 파일 저장 확인**

```bash
ls -la .claude/skills/phase-pipeline/SKILL.md
```

Expected: 파일 존재 확인

**Step 3: 커밋**

```bash
git add .claude/skills/phase-pipeline/SKILL.md
git commit -m "feat: /phase-pipeline 오케스트레이터 스킬 추가 — plan → sync 체이닝"
```

---

### Task 5: CLAUDE.md Auto-Routing 업데이트

루트 CLAUDE.md의 Auto-Routing 테이블에 새 스킬을 추가한다.

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Auto-Routing 테이블에 추가**

`CLAUDE.md`의 `## Auto-Routing` 테이블 끝에 다음 행 추가:

```markdown
| phase-plan, 계획, 마일스톤 | - | /phase-plan |
| phase-sync, 동기화, 회고 | - | /phase-sync |
| phase-pipeline, 파이프라인 | - | /phase-pipeline |
```

**Step 2: 커밋**

```bash
git add CLAUDE.md
git commit -m "docs: Auto-Routing에 phase-plan/sync/pipeline 스킬 추가"
```

---

### Task 6: linear-ops SKILL.md 함수 목록 업데이트

linear-api.sh에 추가한 함수들을 linear-ops SKILL.md 문서에도 반영한다.

**Files:**
- Modify: `.claude/skills/linear-ops/SKILL.md`

**Step 1: 셋업 섹션의 함수 목록에 추가**

`linear-ops/SKILL.md`의 함수 목록에 다음 추가:

```markdown
linear_create_project  "이름" "team-uuid" ["설명"]  # 프로젝트(마일스톤) 생성
linear_assign_issue_to_project "issue-id" "project-id"  # 이슈 → 프로젝트 할당
linear_list_project_issues "project-id" [limit]  # 프로젝트 이슈 목록
```

**Step 2: 커밋**

```bash
git add .claude/skills/linear-ops/SKILL.md
git commit -m "docs: linear-ops에 마일스톤 관련 함수 문서 추가"
```

---

### Task 7: 스킬 동작 검증

3개 스킬이 Claude Code에서 인식되는지 확인한다.

**Step 1: 스킬 파일 존재 확인**

```bash
ls -la .claude/skills/phase-plan/SKILL.md
ls -la .claude/skills/phase-sync/SKILL.md
ls -la .claude/skills/phase-pipeline/SKILL.md
```

Expected: 3개 파일 모두 존재

**Step 2: 스킬 frontmatter 검증**

각 SKILL.md의 frontmatter에 `name`, `description`, `argument-hint`, `allowed-tools`가 있는지 확인.

```bash
head -6 .claude/skills/phase-plan/SKILL.md
head -6 .claude/skills/phase-sync/SKILL.md
head -6 .claude/skills/phase-pipeline/SKILL.md
```

Expected: 각 파일의 frontmatter에 필수 필드 포함

**Step 3: Linear API 함수 동작 확인**

```bash
source .claude/skills/linear-ops/linear-api.sh
linear_list_projects 3
```

Expected: JSON 형식으로 프로젝트 목록 반환

**Step 4: 최종 커밋 (필요 시)**

모든 변경사항이 커밋되었는지 확인:

```bash
git status
```

Expected: clean working tree
