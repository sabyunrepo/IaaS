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
