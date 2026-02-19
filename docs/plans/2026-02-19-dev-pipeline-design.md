# Dev Pipeline Automation Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:writing-plans to create implementation plan.

**Goal:** Obsidian 설계 → Linear 이슈 → 구현 → Obsidian 동기화를 자동화하는 3개 스킬 파이프라인

**Architecture:** 3개 독립 스킬(`/phase-plan`, `/phase-sync`, `/phase-pipeline`) + 파이프라인 상태 파일

---

## 1. 아키텍처 개요

```
/phase-pipeline [N]
    │
    ├── Step 1: /phase-plan [N]
    │   ├── Obsidian 설계 문서 읽기
    │   ├── Linear 기존 이슈 확인
    │   ├── 태스크 분해
    │   ├── Linear 마일스톤 + 이슈 생성
    │   └── planning_discoveries 캐시 저장
    │
    ├── 🔒 Gate 1: 사용자 구현
    │
    ├── Step 2: /phase-sync [N]
    │   ├── Git diff 수집
    │   ├── Obsidian 설계 ↔ 구현 비교
    │   ├── Obsidian 업데이트 (참조 체이닝)
    │   ├── 회고 기록
    │   ├── Linear 이슈 상태 정리
    │   └── CLAUDE.md 업데이트
    │
    └── 🔒 Gate 2: 다음 Phase 진행 여부
```

### 스킬 구성

| 스킬 | 파일 위치 | 역할 |
|------|----------|------|
| `/phase-plan` | `.claude/skills/phase-plan/SKILL.md` | Obsidian → Linear 계획 생성 |
| `/phase-sync` | `.claude/skills/phase-sync/SKILL.md` | 구현 결과 → Obsidian 동기화 |
| `/phase-pipeline` | `.claude/skills/phase-pipeline/SKILL.md` | 오케스트레이터 |

### 의존 도구

| 도구 | 용도 |
|------|------|
| `obsidian-api.sh` | Obsidian Vault CRUD (REST API) |
| `linear-api.sh` | Linear 마일스톤/이슈 CRUD |
| Git CLI | diff, log 수집 |

---

## 2. `/phase-plan` 상세 설계

### 입력
```
/phase-plan [phase_number]
예: /phase-plan 1
```

### 실행 흐름

```
1. Initialize
   ├── Phase 번호 → 설계 문서 경로 매핑
   │   phase0 → plan/v5-design/phase0-scaffolding.md
   │   phase1 → plan/v5-design/phase1-domain.md
   │   phase2 → plan/v5-design/phase2-infrastructure.md
   │   ...
   └── Obsidian Vault에서 해당 문서 + MOC.md 읽기

2. Analyze
   ├── 설계 문서에서 구현 항목 추출
   ├── 의존관계 파악
   ├── Linear 기존 이슈 조회 (중복 방지)
   │   └── 완료된 이슈 → 스킵, 진행중 → 참조
   └── planning_discoveries 수집 (설계 불일치, 누락 등)

3. Create
   ├── Linear 마일스톤 생성
   ├── Linear 이슈 생성 (의존관계 포함)
   └── 이슈 목록 출력

4. Cache
   └── .claude/pipeline-state.json에 저장
       {
         "current_phase": N,
         "step": "awaiting_implementation",
         "milestone_id": "...",
         "issues": [...],
         "planning_discoveries": [
           {"file": "path", "type": "mismatch|missing|outdated", "detail": "..."}
         ]
       }
```

### 출력 형식
```markdown
## Phase N 계획 생성 완료

### 마일스톤: Phase N: [이름]
| # | 이슈 | 의존 | 상태 |
|---|------|------|------|
| JIT-XXX | 제목 | JIT-YYY | Backlog |

### 발견 사항 (planning_discoveries)
- [mismatch] file.md: 설명...
- [missing] file.md: 설명...

구현을 시작하세요. 완료 후 `/phase-sync N` 또는 `/phase-pipeline N --from sync`
```

---

## 3. `/phase-sync` 상세 설계

### 입력
```
/phase-sync [phase_number]
예: /phase-sync 1
```

### 실행 흐름

```
1. Collect
   ├── Git diff (마일스톤 시작 시점 ~ 현재)
   ├── 변경된 파일 목록
   ├── 새로 생성된 파일 목록
   └── pipeline-state.json에서 planning_discoveries 로딩

2. Compare
   ├── Obsidian 설계 문서 읽기
   ├── 설계 vs 구현 차이 분석
   │   ├── 설계에 있는데 미구현 → 경고
   │   ├── 설계에 없는데 구현됨 → 반영 필요
   │   └── 설계와 구현이 다름 → 수정 필요
   └── 변경 목록 생성

3. Update (참조 체이닝)
   ├── 주 설계 문서 수정 (Obsidian REST API)
   ├── 수정된 문서 내 참조 파싱
   │   ├── [[wiki links]] 추출
   │   ├── MOC.md 역참조 확인
   │   └── RELATION-MAP.md 의존관계 확인
   ├── 관련 문서 영향도 검토
   │   └── 체이닝 깊이: 최대 2단계
   ├── 관련 문서 수정 (필요 시)
   ├── planning_discoveries 반영
   │   └── 이전 /phase-plan에서 발견된 불일치도 수정
   └── 수정 diff 미리보기 → 사용자 확인

4. Retrospective
   ├── Obsidian에 회고 노트 추가
   │   └── Architecture/Retrospectives/phase-N-retro.md
   └── 계획 vs 실제 차이, 교훈 기록

5. Cleanup
   ├── Linear 이슈 상태 업데이트 (Done)
   ├── CLAUDE.md 컨텍스트 매핑 업데이트
   └── pipeline-state.json 업데이트
       { "step": "sync_completed", "sync_completed_at": "..." }
```

### 참조 체이닝 상세

```
수정 대상 문서: phase1-domain.md
    │
    ├── [[Identity Resolution]] → identity-resolution.md 확인/수정
    ├── [[Scoring Calculator]] → scoring-calculator.md 확인/수정
    ├── MOC.md에서 Phase 1 섹션 → 상태 업데이트
    ├── RELATION-MAP.md → 의존관계 업데이트
    └── planning_discoveries 캐시
        └── "phase0에서 발견: init.sql 테이블명 불일치" → 반영
```

**탐색 범위:**
- `[[internal links]]` — 문서 내 Obsidian 위키링크
- `MOC.md` 역참조 — 해당 문서를 참조하는 MOC 항목
- `RELATION-MAP.md` — 모듈 간 의존관계 맵
- `planning_discoveries` — /phase-plan 실행 시 수집된 캐시

**안전장치:**
- 체이닝 깊이 최대 2단계
- 수정 전 diff 미리보기 표시
- 사용자 확인 후 적용

### 출력 형식
```markdown
## Phase N 동기화 완료

### Obsidian 업데이트
| 문서 | 변경 유형 | 상세 |
|------|----------|------|
| phase1-domain.md | 수정 | 구현 반영 |
| identity-resolution.md | 체이닝 수정 | 참조 업데이트 |
| MOC.md | 체이닝 수정 | 상태 업데이트 |

### Linear 정리
- JIT-XXX: Done
- JIT-YYY: Done

### 회고
- 계획 대비 변경: ...
- 교훈: ...
```

---

## 4. `/phase-pipeline` 오케스트레이터

### 입력
```
/phase-pipeline [phase_number] [--from step] [--plan-only]

예:
  /phase-pipeline 1           # 전체 파이프라인
  /phase-pipeline 1 --from sync  # sync부터 재개
  /phase-pipeline 1 --plan-only  # 계획만 생성
```

### 실행 흐름

```
Step 1: /phase-plan 호출
  → Obsidian 읽기 → Linear 확인 → 마일스톤/이슈 생성
  → planning_discoveries 캐시

🔒 Gate 1: "Phase N 계획 생성 완료. 구현을 시작하세요."
  → 사용자가 구현 완료 후 재호출

Step 2: /phase-sync 호출
  → Git diff → Obsidian 비교 → 업데이트(체이닝) → 회고 → Linear 정리

🔒 Gate 2: "Phase N 동기화 완료. 다음 Phase 진행?"
  → yes: /phase-pipeline [N+1]
  → no: 종료
```

### 상태 파일
```json
// .claude/pipeline-state.json
{
  "current_phase": 1,
  "step": "awaiting_implementation",
  "plan_completed_at": "2026-02-19T14:00:00",
  "sync_completed_at": null,
  "milestone_id": "uuid",
  "issues": ["JIT-236", "JIT-237"],
  "planning_discoveries": [
    {
      "file": "plan/v5-design/phase1-domain.md",
      "type": "mismatch",
      "detail": "Identity Resolution 모듈 경로가 설계와 다름"
    }
  ]
}
```

---

## 5. 파일 구조

```
.claude/skills/
├── phase-plan/
│   └── SKILL.md          # /phase-plan 스킬 정의
├── phase-sync/
│   └── SKILL.md          # /phase-sync 스킬 정의
├── phase-pipeline/
│   └── SKILL.md          # /phase-pipeline 오케스트레이터
├── obsidian-api/
│   ├── SKILL.md          # (기존) Obsidian REST API 래퍼
│   └── obsidian-api.sh
└── linear-ops/
    ├── SKILL.md          # (기존) Linear API 래퍼
    └── linear-api.sh

.claude/
└── pipeline-state.json   # 파이프라인 상태 (런타임 생성)
```

---

## 6. Phase 매핑 테이블

| Phase | 설계 문서 | 설명 |
|-------|----------|------|
| 0 | `plan/v5-design/phase0-scaffolding.md` | 프로젝트 스캐폴딩 |
| 1 | `plan/v5-design/phase1-domain.md` | 도메인 레이어 |
| 2 | `plan/v5-design/phase2-infrastructure.md` | 인프라 레이어 |
| 3 | `plan/v5-design/phase3-application.md` | 애플리케이션 레이어 |
| 4 | `plan/v5-design/phase4-questions.md` | 질문 생성 |
| 5 | `plan/v5-design/phase5-output-frontend.md` | 출력 + 프론트엔드 |
| 6 | `plan/v5-design/phase6-testing.md` | 테스트 + 벤치마크 |
