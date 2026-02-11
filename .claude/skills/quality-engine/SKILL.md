# Agent Output Quality Verification Engine (품질 검증 엔진)

> 전체 파이프라인(Phase 0-4, 16+ Activity)의 LLM 아웃풋을 자동 검증하는 통합 품질 시스템.

## 핵심 게이트: Evidence Score

| 점수 | 판정 | 조치 |
|------|------|------|
| 70-100 | PASS | 통과 |
| 40-69 | REVISE | 근거 보강 후 재생성 |
| 0-39 | REJECT | 삭제 및 재생성 |

## 품질 차원 요약

| Phase | 핵심 검증 | 합격 기준 |
|-------|----------|----------|
| P2 분석 | 프로필 완전성, 스킬 정확도, JD 구조화, HYBRID 완수 | ≥90% 필드, 환각 0, 누락 ≤2 |
| P3 질문 | 10차원 (Relevance/Clarity/Depth/Bias/Evidence/Hallucination/Duplicate/Specificity/EvalScenario/Terminology) | Evidence ≥70, 범용 <20%, 중복 0 |
| P4 결과물 | Intel 정확성, 레이더 근거, 추천 일관성, 4탭 교차 일관성 | 사실오류 0, 모순 0 |

## 구현 상태

| 완료 | 미연결 (HIGH) |
|------|-------------|
| `quality_review.py` 구조적+LLM 8차원 검증 | Langfuse 스코어 미호출 |
| Evidence Score 게이트 (0-100) | 품질 결과 DB 미저장 |
| 중복 탐지 + `revise_questions` 자동 수정 | Phase 2/4 품질 게이트 없음 |
| `validate_code_analysis()` HYBRID 검증 | 교차 일관성 검증 없음 |
| Langfuse 트레이싱 (Job 단위) | 프론트엔드 품질 지표 미표시 |

## 상세 참조

Phase별 상세 품질 차원, 파이프라인 아키텍처, 체크리스트 → `docs/claude-references/quality-verification-engine.md`
