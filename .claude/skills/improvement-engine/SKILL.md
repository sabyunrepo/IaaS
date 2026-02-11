# Continuous Improvement Engine (지속적 개선 엔진)

> MEASURE → ANALYZE → IMPROVE → VERIFY → REPORT 사이클 반복

## 개선 영역 요약 (미션 우선순위순)

| 우선순위 | 영역 | 핵심 목표 | 관련 파일 |
|---------|------|----------|----------|
| P0-1 | 점수 근거 체계 | 코드 메트릭 기반 정량 공식 (레이더 5축, 매치율, 스킬별) | `analysis_generation.py`, `decision_generation.py`, `DeepAnalysisTab.tsx` |
| P0-2 | 코드 기반 질문 | ≥60% 질문이 후보자 GitHub 코드에서 추출 | `question_generation.py`, `code_analysis.py` |
| P0-3 | 비개발자 답변 가이드 | 3단계(우수/보통/주의) + glossary + 후속질문 팁 | `craft_evaluation_scenarios()`, `LiveInterviewTab.tsx` |
| P0-4 | LinkedIn 경력 구조화 | 타임라인 + 추천서 요약 + 승진 패턴 | `linkedin_service.py`, `IntelBriefTab.tsx` |
| P1 | 아웃풋 품질 & UX | AST/PyDriller 정확도, 반응형, WCAG 2.1 AA, i18n | `quality_review.py`, 프론트엔드 전체 |
| P2 | 인프라 & 안정성 | N+1, 캐시, CWV, OWASP Top 10, SRP | 백엔드/프론트엔드 전체 |

## Git 워크플로우 (매 개선건)

`gh issue create` → `git checkout -b improve/[영역]` → 수정+테스트 → `git commit -m "improve: [설명] Closes #N"` → `gh pr create` → merge → main sync

## 상세 참조

P0 상세 TODO, P1/P2 세부, 보고서 형식 → `docs/claude-references/improvement-engine.md`
