# Project Lifecycle Management 가이드

> Medium/Large 프로젝트(2+ phases)의 기획→실행→완료 오케스트레이션 프로토콜.
> Small(1 phase)은 `/linear-ops` 직접 사용.

## 제약사항
- Linear MCP: `create_project` API 없음 → 이슈 라벨/네이밍으로 프로젝트 그룹핑
- Linear 팀: `Jittda (JIT)`, ID: `588a6c89-bc94-45c3-b9a0-7405913e86d8`

---

## 워크플로우 전체 흐름

```
사용자 요청 → Stage 0 (분석) → Stage 1 (기획/이슈 생성) → Stage 2 (실행) → Stage 3 (체크포인트) → Stage 4 (완료)
```

---

## Stage 0: 프로젝트 접수 및 분석

**트리거**: 사용자가 프로젝트/문제 설명
**도구**: sequential MCP (깊은 분석)

1. 요구사항 파악 → 핵심 vs. 부가 분류
2. 프로젝트 타입 결정: `Feature` | `Refactor` | `Bug` | `Infra`
3. 규모 추정: Small (1 phase) | Medium (2-3) | Large (4+)
4. 영향 컴포넌트 식별: frontend / backend / infra / docs
5. 기술 리스크 및 의존성 분석
6. **Scope Analysis Report** 출력 → 사용자 승인 대기

### Scope Analysis Report 포맷

```
## Scope Analysis Report
- 프로젝트: {제목}
- 타입: {Feature/Refactor/Bug/Infra}
- 규모: {Small/Medium/Large} ({N} phases)
- 영향 범위: {컴포넌트 목록}
- 리스크: {주요 리스크}
- 예상 페이즈: Phase 1: {제목}, Phase 2: {제목}, ...
```

> Small로 판정되면 lifecycle 없이 `/linear-ops` 직접 실행 안내.

---

## Stage 1: 페이즈 기획 및 이슈 생성

**트리거**: 사용자가 Stage 0 승인
**도구**: linear MCP, gh CLI

### 1-1. 페이즈 분할
- 각 페이즈 = 독립 실행 가능한 작업 단위
- 의존성 순서 정의 (Phase 1 → 2 → 3)
- 페이즈별 담당 영역 (Backend/Frontend/Infra/QA)

### 1-2. Linear 이슈 생성 (페이즈당 1개)

**이슈 제목**: `[{project-slug}] Phase {N}: {제목}`

**이슈 본문 템플릿**:

```markdown
## 목표 (Goal)
{1-2문장 명확한 목표}

## 수락 기준 (Acceptance Criteria)
- [ ] AC1: {구체적, 테스트 가능한 기준}
- [ ] AC2: ...

## 컨텍스트 (Context)
- 프로젝트 참조: `docs/projects/{slug}/CONTEXT.md`
- 이전 단계: {JIT-XXX 또는 "없음"}
- 다음 단계: {JIT-YYY 또는 "최종"}

## 기술 사양 (Technical Spec)
**수정 파일**:
- `{path/to/file.py}` — {예상 변경 내용}

**참고 패턴**:
- 유사 구현: `{path/to/reference.py}` (L{start}-{end})
- 테스트 예시: `{path/to/test.py}`

## 테스트 시나리오
- [ ] TS1: [Given: {조건}] [When: {행위}] [Then: {결과}]
- [ ] TS2: [Edge: {엣지케이스}] [Expected: {기대}]

## 예상 문제
- {리스크} → {완화 전략}

## Definition of Done
- [ ] 모든 수락 기준 충족
- [ ] 테스트 통과
- [ ] dev-rules.md 규칙 준수
```

> **핵심**: 이 이슈만 읽고 구현 가능할 정도의 정보량

### 1-3. GitHub 이슈 생성 (듀얼 트래킹)

```bash
gh issue create \
  --title "{type}: [{project-slug}] Phase {N} — {제목}" \
  --body "Linear: JIT-{XXX}\n\n{요약}"
```

### 1-4. 프로젝트 컨텍스트 파일 생성

**경로**: `docs/projects/{project-slug}/CONTEXT.md`

```markdown
# {프로젝트 제목}

## 개요
{프로젝트 목적 2-3문장}

## 아키텍처 결정
### AD-1: {결정 제목}
- 컨텍스트: {왜 이 결정이 필요했는지}
- 결정: {무엇을 결정했는지}
- 근거: {트레이드오프, 제약}

## 파일 구조
{영향받는 파일 트리}

## 진행 상황
- [ ] Phase 1: {제목} — JIT-{XXX} / GitHub #{N}
- [ ] Phase 2: {제목} — JIT-{YYY} / GitHub #{M}
```

---

## Stage 2: 페이즈 실행 (기존 /linear-ops 활용)

**트리거**: 사용자가 "JIT-{XXX} 진행해" 또는 `/linear-ops JIT-{XXX}`
**소유**: `/linear-ops` 스킬 (기존 3-Phase 그대로)

1. **Initialize**: Linear 이슈 읽기 → AC 추출 → feature branch 생성
2. **TDD Implementation**: 테스트 먼저 → 구현 → 검증
3. **Finalize**:
   - Linear 이슈 결과 기록 + 상태 "Done"
   - PR 생성 (한글): `feat: [{project-slug}] {설명} [JIT-{XXX}] Closes #{GitHub-N}`
   - PR 머지
   - GitHub 이슈 자동 클로즈 (`Closes #{N}`)
   - main 동기화

---

## Stage 3: 페이즈 간 체크포인트

**트리거**: 각 페이즈 완료 직후 (자동)

1. `CONTEXT.md` 진행 상황 업데이트 (`- [x] Phase N: 완료`)
2. 다음 페이즈 의존성 확인
3. 리스크 재평가 (새 기술 부채 발생 여부)
4. 사용자에게 체크포인트 리포트 출력

### 체크포인트 리포트 포맷

```
## Checkpoint: Phase {N} 완료
- 완료: {변경 파일 수}개 파일, {테스트 수}개 테스트
- 다음: Phase {N+1} — {제목} (JIT-{YYY})
- 의존성: {충족/미충족}
- 새 리스크: {있음/없음}
```

---

## Stage 4: 프로젝트 완료

**트리거**: 모든 페이즈 이슈 "Done"

1. 전체 프로젝트 요약 생성
   - 변경 파일 목록 및 통계
   - 테스트 커버리지 변화
   - 주요 아키텍처 결정 사항
   - 교훈 (Lessons Learned)
2. 모든 GitHub 이슈 클로즈 확인
3. `CONTEXT.md` 최종 업데이트 (status: Completed)

---

## Linear ↔ GitHub 듀얼 트래킹 규칙

| 이벤트 | Linear | GitHub |
|--------|--------|--------|
| 프로젝트 시작 | 이슈 N개 생성 (라벨로 그룹핑) | 이슈 N개 생성 |
| 페이즈 착수 | status: "In Progress" | branch: `feat/JIT-{N}-{slug}` |
| 페이즈 완료 | status: "Done" + 결과 기록 | PR 머지 + `Closes #{N}` |
| 프로젝트 완료 | 모든 이슈 Done | 모든 이슈 Closed |

**상호 참조**: Linear 이슈에 `GitHub: #{N}`, GitHub 이슈에 `Linear: JIT-{XXX}`

---

## 예외 처리

| 상황 | 대응 |
|------|------|
| 페이즈 실행 중 스코프 변경 | Stage 0으로 회귀, 사용자 재승인 |
| 페이즈 간 의존성 충돌 | 체크포인트에서 차단, 사용자 판단 요청 |
| Linear API 오류 | GitHub 이슈만으로 폴백, Linear는 수동 업데이트 |
| Small로 재분류 | lifecycle 중단, `/linear-ops` 직접 전환 |
| 사용자 중단 요청 | 현재 페이즈까지 완료 후 CONTEXT.md에 "Paused" 기록 |
