# Development Rules (Project-Specific)

## File Placement
```
backend/app/workflows/activities/  → 새 Activity 파일
backend/app/workflows/             → 새 Workflow 파일
backend/app/services/              → 비즈니스 로직 서비스
backend/app/api/routes/            → API 엔드포인트
backend/app/models/                → 데이터 모델
backend/app/prompts/               → LLM 프롬프트 YAML
frontend/src/components/           → React 컴포넌트
frontend/src/components/tabs/      → 탭 컴포넌트 (IntelBrief, DeepAnalysis 등)
frontend/src/components/charts/    → 차트 컴포넌트 (RadarChart 등)
frontend/src/pages/                → React 페이지
frontend/src/hooks/                → Custom React Hooks
frontend/src/lib/                  → API 클라이언트, 유틸리티
frontend/src/types/                → TypeScript 타입 정의
frontend/public/locales/           → i18n 번역 파일
frontend/e2e/                      → Playwright E2E 테스트
```

## Naming Conventions
- Activity 함수: `snake_case` (예: `analyze_documents`)
- Workflow 클래스: `PascalCase` + `Workflow` (예: `InterviewGenerationWorkflow`)
- API 라우터: `snake_case` (예: `create_job`)
- 프론트엔드 컴포넌트: `PascalCase` (예: `InterviewForm`)
- E2E 테스트: `kebab-case.spec.ts`
- Hooks: `use` + `PascalCase` (예: `useJob`)

## File Size & Separation
- 단일 파일 300줄 초과 → 분리 검토
- 한 파일에 한 컴포넌트 (SRP)
- 새 파일 생성 시 기존 파일과 책임 중복 금지

## Langfuse-First 프롬프트 규칙

🔴 **YAML 프롬프트 수정 시 Langfuse 업로드 필수**:
1. `backend/app/prompts/*.yaml` 수정 후 반드시 Langfuse에 업로드
2. `docker compose exec backend python scripts/upload_prompts_to_langfuse.py --production`
3. Langfuse가 runtime에서 우선 적용되므로, YAML만 수정하고 업로드하지 않으면 변경이 반영되지 않음

## Utility Scripts

| 스크립트 | 사용법 |
|----------|--------|
| `create_test_job.py` | `docker compose exec backend python scripts/create_test_job.py` |
| `upload_prompts_to_langfuse.py` | `docker compose exec backend python scripts/upload_prompts_to_langfuse.py --production` |

**주의**: Langfuse 업로드 시 반드시 `--production` 플래그. 모델 설정은 `llm_config.py` 단일 소스.

## GitHub Issue/PR/Merge 워크플로우

1. `gh issue create --title "타입: 한글 설명" --body "한글 본문"`
2. `git checkout -b fix/이슈-설명-N` 또는 `feature/이슈-설명-N`
3. 커밋: 한글 메시지 + `Closes #N`
4. `git push -u origin 브랜치명`
5. `gh pr create --title "타입: 한글 설명" --body "한글 본문"`
6. `gh pr merge --merge`
7. `git checkout main && git pull`

**필수**: 모든 GitHub 커뮤니케이션 한글. 자율 진행. 이슈→PR→머지 완주. 머지 후 main 동기화.

## Temporal Patterns
1. `@activity.defn` 데코레이터 필수
2. >30s Activity → `activity.heartbeat()`
3. LLM 호출 → `CachedLLMService` (Redis)
4. Phase 완료 시 checkpoint 저장
5. `worker.py`에 새 Activity 등록

## 고아 서브에이전트 관리
- 확인: `ps aux | grep '[c]laude' | grep -v grep | wc -l`
- 정리: `ps aux | grep '[/]Users/sabyun/.local/bin/claude' | awk '{print $2}' | xargs kill 2>/dev/null`
- 5개 초과 시 정리 필요
