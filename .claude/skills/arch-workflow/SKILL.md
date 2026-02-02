---
name: arch-workflow
description: Temporal 워크플로우 파이프라인 구현. Phase 0~4 파이프라인, 병렬 분석, 질문 생성, 체크포인트 관련 구현 시 사용.
argument-hint: [phase] (예: phase0-input, phase1-plan, phase2-analysis, phase3-question, phase4-final)
allowed-tools: Read, Grep, Bash, Write, Edit, Glob
---

# Workflow Pipeline Architecture Skill

4-Phase Temporal 워크플로우 파이프라인 구현 가이드.

## 반드시 먼저 읽을 문서
1. `docs/architecture/03-workflow.md` — 워크플로우 전체 설계 (1800줄)
2. `docs/architecture/02-data-models.md` — Phase별 입출력 모델

## 파이프라인 개요

```
Phase 0: Smart Input Extraction (교차 추출)
  → Phase 1: Planning (실행 계획)
    → Phase 2: Parallel Analysis (문서/코드/JD 병렬)
      → Phase 3: Question Generation (25개 질문)
        → Phase 4: Finalization (검증 + 출력)
```

## Phase별 구현

### Phase 0: Smart Input Extraction
- Activity: `enrich_input()`
- 입력: `InputData` → 출력: `EnrichedInput`
- 모든 입력(PDF, DOCX, LinkedIn)에서 URL 교차 추출
- Proxycurl API로 LinkedIn 프로필 수집

### Phase 1: Planning
- Activity: `create_plan()`
- 입력: `EnrichedInput` → 출력: `ExecutionPlan`
- GitHub API로 레포 워크로드 추정
- 실행 전략 결정 (어떤 분석을 얼마나)

### Phase 2: Parallel Analysis (핵심)
- `workflow.execute_activity()` 3개 병렬 실행
- Document: `analyze_documents()` — PDF/DOCX 파싱 → `CandidateProfile`
- Code: `analyze_code()` — PyGithub → PyDriller → AST → LLM 4-Phase
- JD: `analyze_jd()` — 요구사항 추출 → `JDAnalysis`
- **병렬 실행**: `asyncio.gather()` 또는 Temporal `workflow.wait_all()`

### Phase 3: Question Generation
1. **Topic Selection**: 분석 결과에서 25개 토픽 선정 (5카테고리 × 5)
2. **Parallel Crafting**: 10개 Worker로 질문 병렬 생성
3. **Enhancement**: 용어 정의, 후속질문, 평가 시나리오 병렬 보강
4. **Quality Review**: 최대 3회 루프 (중복/연관성/흐름)

### Phase 4: Finalization
- Supervisor 검증: Hallucination 체크, 코드 참조 확인
- 포맷 검증: 비개발자 가독성 점수
- 최종 `InterviewScript` 조합

## 체크포인트 패턴
```python
# 각 Phase 완료 시 저장
await checkpoint_store.save(job_id, phase="phase_2", data=analysis_results)

# 재시작 시 복구
last_checkpoint = await checkpoint_store.load(job_id)
if last_checkpoint.phase == "phase_2":
    # Phase 3부터 재개
```

## 파일 배치
```
backend/app/workflows/interview_workflow.py     — 메인 워크플로우
backend/app/workflows/activities/
  input_enrichment.py   — Phase 0
  planning.py           — Phase 1
  document_analysis.py  — Phase 2a
  code_analysis.py      — Phase 2b
  jd_analysis.py        — Phase 2c
  question_generation.py — Phase 3
  quality_review.py     — Phase 3 (검토 루프)
  finalization.py       — Phase 4
  checkpoint_activities.py — 체크포인트 관리
backend/app/workflows/worker.py                 — Worker 등록
```

## 필수 패턴
- 모든 Activity: `@activity.defn` 데코레이터
- 30초+ Activity: `activity.heartbeat()` 필수
- LLM 호출: `CachedLLMService` 사용 (Redis 캐시)
- 에러: `RetryableError` / `NonRetryableError` 분류
- 멱등성 보장: 같은 입력 → 같은 출력
