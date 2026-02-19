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
