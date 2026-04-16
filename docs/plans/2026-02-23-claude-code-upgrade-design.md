# Claude Code 세팅 업그레이드 — 4대 시스템 설계

> 날짜: 2026-02-23
> 범위: 글로벌 (~/.claude/) + 프로젝트 오버라이드
> 접근: Hybrid (Hook + CLAUDE.md/스킬)
> 기존 체계: superpowers v4.3.0 보강 (공존)

## 배경

영상 "[8년차 개발자의 AI 시스템 설계]" 에서 소개된 4대 시스템을 기존 Claude Code 세팅에 통합.
현재 세팅은 permissions, SessionStart/PreToolUse/PostToolUse/Stop hooks, 37개 스킬, 6개 에이전트가 있으나,
**자동 매뉴얼 주입, 품질 넛지, 3종 문서 기억, 에이전트 보고서 표준**이 부재.

## 시스템 1: 자동 매뉴얼 주입 (Hook)

### 구현 파일
- `~/.claude/scripts/skill-injector.sh` — UserPromptSubmit hook 스크립트
- `~/.claude/scripts/skill-rules.json` — 글로벌 매칭 규칙
- 프로젝트 오버라이드: `.claude/skill-rules.json`

### 동작
1. UserPromptSubmit hook이 사용자 프롬프트를 stdin으로 수신
2. `skill-rules.json`의 4가지 규칙으로 매칭:
   - **키워드**: "백엔드", "API", "docker" 등
   - **의도**: "만들어", "추가해", "수정해" 등
   - **파일 경로**: 프롬프트에 언급된 경로
   - **프로젝트 타입**: 현재 CLAUDE.md 키워드
3. 매칭된 스킬 목록을 stdout으로 출력 (nudge, block 아님)

### 매칭 규칙 구조
```json
{
  "rules": [
    {
      "id": "backend",
      "skills": ["/arch-api", "/arch-data"],
      "keywords": ["API", "엔드포인트", "FastAPI", "라우트", "백엔드"],
      "intents": ["만들어", "추가해", "수정해", "구현해"],
      "file_patterns": ["**/routes/**", "**/api/**", "**/models/**"]
    },
    {
      "id": "frontend",
      "skills": ["/jittda-design-system", "/arch-frontend"],
      "keywords": ["프론트", "컴포넌트", "React", "UI", "페이지", "화면"],
      "file_patterns": ["**/components/**", "**/*.tsx", "**/pages/**"],
      "inject_rules": "frontend-rules"
    },
    {
      "id": "temporal",
      "skills": ["/temporal-dev", "/arch-workflow"],
      "keywords": ["워크플로우", "activity", "temporal", "파이프라인"],
      "file_patterns": ["**/workflows/**", "**/activities/**"]
    },
    {
      "id": "testing",
      "skills": ["/test", "/troubleshoot"],
      "keywords": ["테스트", "버그", "디버그", "에러", "pytest"],
      "file_patterns": ["**/tests/**", "**/test_**"]
    },
    {
      "id": "infra",
      "skills": ["/arch-infra"],
      "keywords": ["docker", "compose", "배포", "환경변수", "인프라"],
      "file_patterns": ["**/docker-compose*", "**/Dockerfile*", "**/.env*"]
    }
  ]
}
```

## 시스템 2: 작업 기억 시스템 (CLAUDE.md + 템플릿)

### 3종 문서

| 문서 | 위치 | 역할 |
|------|------|------|
| 계획서 (Plan) | `docs/plans/YYYY-MM-DD-<topic>-design.md` | 무엇을 만들 것인지 (설계도) |
| 맥락노트 (Context) | `docs/plans/YYYY-MM-DD-<topic>-context.md` | 왜 이렇게 결정했는지 (시방서) |
| 체크리스트 (Checklist) | `docs/plans/YYYY-MM-DD-<topic>-checklist.md` | 무엇이 남았는지 (공정표) |

### 계획서 템플릿 (기존 brainstorming 스킬과 동일)
```markdown
# [제목]
## 목표
## 배경/맥락
## 기술 설계
## 단계별 구현 계획
## 성공 기준
```

### 맥락노트 템플릿 (신규)
```markdown
# [제목] — 맥락노트
## 왜 이 방식을 선택했는가
- 결정 1: [근거]
- 결정 2: [근거]
## 관련 자료
- 파일: [경로 목록]
- 이전 논의: [세션 ID 또는 커밋]
## 주의사항
- [알려진 제약/리스크]
```

### 체크리스트 템플릿 (신규)
```markdown
# [제목] — 체크리스트
- [ ] Step 1: [설명]
- [ ] Step 2: [설명]
- [x] Step 3: [완료]
## 발견사항
- [작업 중 발견된 이슈]
```

### CLAUDE.md 규칙
1. 3단계 이상의 구현 작업 시작 전 → 3종 문서 생성 필수
2. 새 세션에서 이어받기 시 → `docs/plans/`에서 최신 체크리스트 읽고 이어서
3. 작업 완료마다 체크리스트 업데이트
4. 세션 종료 전 → 맥락노트에 "미완료 사항" 기록

### 기존 시스템과의 레이어링
```
pipeline-state.json  ← 프로젝트 전체 진행도
docs/plans/*-design  ← 작업 설계 (brainstorming 산출물)
docs/plans/*-context ← 작업 맥락/결정 근거 (신규)
docs/plans/*-checklist ← 작업 진행 추적 (신규)
MEMORY.md           ← 누적 교훈
```

## 시스템 3: 자동 품질 검사 + 셀프체크 (Hook)

### 구현 파일
- `~/.claude/scripts/change-logger.sh` — PostToolUse 변경 로그
- `~/.claude/scripts/quality-nudge.sh` — Stop hook 셀프체크
- `~/.claude/scripts/quality-rules.json` — 파일타입별 체크 규칙

### 변경 로그 (PostToolUse)
- Edit/Write 감지 시 `/tmp/claude-changes-{PID}.log`에 기록
- 형식: `{timestamp} {action} {file_path}`
- 조용히 기록만 (exit 0)

### 셀프체크 리마인더 (Stop hook)
- 세션 종료 시 change-log 읽어 변경 파일 목록 출력
- 파일 확장자별 체크 규칙:
  - `.py` → "타입 힌트, 에러 처리, 테스트 확인?"
  - `.tsx` → "Seed Design 컴포넌트, lucide-react, 접근성 확인?"
  - `.yaml` → "구문 오류, 들여쓰기 확인?"
  - `docker-compose*` → "환경변수, 볼륨 확인?"
- Nudge만 (block 아님)

### quality-rules.json 구조
```json
{
  "rules": {
    ".py": ["타입 힌트가 적절한가요?", "에러 처리가 추가되었나요?", "관련 테스트를 실행했나요?"],
    ".tsx": ["Seed Design 컴포넌트를 사용했나요?", "lucide-react 아이콘만 사용했나요?", "접근성(a11y)을 확인했나요?"],
    ".yaml": ["구문 오류가 없나요?", "Langfuse 업로드가 필요한가요?"],
    "docker-compose": ["환경변수가 동기화되었나요?", "볼륨 마운트가 정확한가요?"],
    "_default": ["보안 취약점은 없나요?", "관련 문서 업데이트가 필요한가요?"]
  }
}
```

## 시스템 4: 에이전트 보고서 + 프론트엔드 아키텍처 규칙

### 에이전트 보고서 표준
모든 서브에이전트(Task tool) 결과물은 4섹션 구조 필수:

```markdown
## [에이전트명] 보고서
### 발견사항 (What I Found)
### 수행한 작업 (What I Did)
### 판단 근거 (Why)
### 미해결 사항 (Open Items)
```

### 프론트엔드 아키텍처 규칙

#### Seed Design First
- 모든 UI 컴포넌트는 Seed Design 컴포넌트 우선 사용
- Seed Design에 없는 경우에만 커스텀 구현 (근거 기록 필수)
- 구현 전: /jittda-design-system 스킬 + seed-docs MCP 확인

#### 아이콘: lucide-react 전용
- `import { IconName } from "lucide-react"` 만 사용
- heroicons, react-icons, font-awesome 등 금지

#### API 추상화 패턴
- 모든 API 호출은 추상 BaseAPI 클래스 상속
- 구조: `BaseAPI` → `JobAPI`, `AuthAPI`, `AnalysisAPI` 등
- 직접 fetch/axios 호출 금지

#### 폴더 구조 표준
```
src/
├── components/    # 재사용 UI 컴포넌트
├── pages/         # 라우트별 페이지
├── hooks/         # 커스텀 훅
├── api/           # BaseAPI + 도메인별 API
├── types/         # TypeScript 타입 정의
├── utils/         # 유틸리티 함수
├── constants/     # 상수/설정값
└── styles/        # 글로벌 스타일
```

#### UI/UX 일관성
- 컬러/스페이싱/타이포그래피 → Seed Design 토큰만 사용
- 반응형: Tailwind breakpoint 표준 (sm/md/lg/xl)
- 다크모드: Seed Design 테마 시스템 활용

### frontend-verifier 에이전트 강화
기존 `frontend-verifier.md` 업데이트:
1. Seed Design 컴포넌트 사용 여부 검증
2. lucide-react 아이콘 전용 검증
3. BaseAPI 상속 패턴 검증
4. 폴더 구조 표준 준수 검증
5. Seed Design 토큰 사용 검증

### 코드 리뷰 워크플로우
- PR 생성 직전 → superpowers:requesting-code-review 스킬 실행 필수
- 리뷰 결과를 PR description에 포함

---

## 구현 순서 (예상)

### Phase 1: Hook 인프라 (시스템 1 + 3)
1. `skill-rules.json` + `quality-rules.json` 작성
2. `skill-injector.sh` 구현 (UserPromptSubmit hook)
3. `change-logger.sh` 구현 (PostToolUse hook)
4. `quality-nudge.sh` 구현 (Stop hook)
5. `~/.claude/settings.json`에 hooks 등록 (글로벌)
6. 기존 IaaS hooks와 병합 검증

### Phase 2: 작업 기억 (시스템 2)
7. 맥락노트 + 체크리스트 템플릿 작성
8. CLAUDE.md에 작업 기억 규칙 추가
9. 기존 brainstorming/write-plan 스킬과 연동 확인

### Phase 3: 에이전트 + 프론트엔드 (시스템 4)
10. CLAUDE.md에 프론트엔드 아키텍처 규칙 추가
11. 에이전트 보고서 포맷 규칙 추가
12. `frontend-verifier.md` 업데이트
13. 기존 6개 에이전트에 보고서 포맷 추가

### Phase 4: 검증
14. 테스트 세션으로 4대 시스템 동작 확인
15. 미세 조정
