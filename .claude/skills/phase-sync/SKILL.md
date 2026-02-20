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
