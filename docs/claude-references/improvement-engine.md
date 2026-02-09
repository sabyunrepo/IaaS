# Continuous Improvement Engine (상세)

> CLAUDE.md에서 분리된 상세 문서. 핵심 요약은 CLAUDE.md 본문 참조.

## 개선 영역 상세

### 🔴 P0: 제품 미션 핵심

#### 1. 점수 근거 체계 확립 (Evidence-Based Scoring)

**현재 문제**: 레이더 차트 5축/매치율/스킬별 점수가 LLM 임의 부여, 근거 불명확

**목표**: 코드 메트릭/경력 데이터 기반 정량 공식

**개선 항목:**
- [ ] 레이더 차트 5축 공식: `code_quality = f(complexity, coverage, docstring, lint)` 등
- [ ] 전체 매치율: `Σ(axis_score × weight) / Σ(weights)` — JD 기반 가중치
- [ ] 스킬별 evidence_source 필수 (GitHub 레포명, 파일, 커밋 수)
- [ ] 프론트엔드 점수 근거 팝업/툴팁

**관련 파일:** `analysis_generation.py`, `decision_generation.py`, `intel_generation.py`, `DeepAnalysisTab.tsx`, `DecisionTab.tsx`

#### 2. 코드 기반 구체적 질문 생성

**현재 문제**: 범용 질문 다수, GitHub 코드 기반 질문 비율 낮음

**목표**: 질문 ≥60%가 실제 코드/프로젝트에서 추출

**개선 항목:**
- [ ] 코드 기반 질문 비율 측정 (evidence_source=GitHub 추적)
- [ ] 코드 스니펫 첨부 질문 ("이 코드에서 왜 이 패턴?")
- [ ] 커밋 히스토리 기반 질문 (PyDriller 핫스팟/리팩토링 패턴)
- [ ] evidence_score <40인 범용 질문 20% 이하 강제

**관련 파일:** `question_generation.py`, `question_enhancement.py`, `code_analysis.py`, `question_generation.yaml`

#### 3. 비개발자 친화 답변 가이드

**현재 문제**: 면접관이 좋은/나쁜 답변 구분 기준 없음

**목표**: 모든 질문에 비개발자 이해 가능한 "기대 답변 + 평가 기준"

**개선 항목:**
- [ ] 3단계 답변 가이드 (우수/보통/주의 — 비개발자 언어)
- [ ] 전문 용어 자동 번역 (glossary_term + plain_explanation)
- [ ] 면접관 액션 가이드 (후속 질문 안내)
- [ ] Playwright 비개발자 이해도 검증

**관련 파일:** `craft_evaluation_scenarios()`, `enhance_terminology()`, `design_follow_ups()`, `LiveInterviewTab.tsx`

#### 4. LinkedIn 경력 정보 구조화

**현재 문제**: LinkedIn 데이터 미활용

**목표**: 경력 타임라인 + 추천서 요약 + 학력 + 승진 패턴

**개선 항목:**
- [ ] 경력 타임라인 (회사/직급/기간/성과)
- [ ] 추천서 요약 (키워드 추출: "3명이 '리더십' 언급")
- [ ] 학력/자격증 구조화
- [ ] 승진 패턴 분석 ("3년마다 직급 상승 → 성장 빠름")
- [ ] Intel Brief 탭 강화

**관련 파일:** `linkedin_service.py`, `intel_generation.py`, `finalization.py`, `IntelBriefTab.tsx`

### 🟡 P1: 아웃풋 품질 & UX

#### 5. 에이전트 아웃풋 품질 향상
- AST/tree-sitter 메트릭 정확도
- PyDriller 기여도 분석
- 스킬 매칭 정확도/confidence 현실성
- fallback 데이터 유의미성

#### 6. UI/UX + Playwright 테스트
- 비개발자 UX: glossary 표시, 점수 근거, 답변 가이드 카드
- 기존 UX: 디자인 일관성, 반응형 (375/768/1280px), WCAG 2.1 AA, i18n
- Playwright 자동 검증: 콘솔 에러 0개, 용어/점수 누락 탐지

#### 7. 프론트엔드 에러 탐지
- 파이프라인: Playwright → 콘솔 에러 수집 → 분류 → 이슈 → 수정
- Hook 순서/undefined/타입 불일치/i18n 누락 자동 탐지

### 🟢 P2: 인프라 & 안정성

#### 8. 성능 최적화
- 백엔드: N+1, 캐시 히트율, p50/p95, 토큰 비용
- 프론트: 번들 <300KB, CWV (LCP <2.5s, FID <100ms, CLS <0.1)

#### 9. 보안: OWASP Top 10

#### 10. 아키텍처: 패턴 적용, 하드코딩 제거, SRP, 타입 힌트 100%

#### 11. 선택적 캐시 무효화
```python
async def invalidate_activity_cache(activity_name: str):
    keys = await redis.keys(f"llm_cache:{activity_name}:*")
    await redis.delete(*keys)
```

## 개선 사이클 보고서 형식

```markdown
## 개선 사이클 #N 보고서
### 측정 결과 | 에이전트 품질 지표 | A/B 결과 | Playwright 결과 | 수정 내역 | 다음 목표
```

## Git 워크플로우 (매 개선건)
```
gh issue create → git checkout -b improve/[영역] → commit (Closes #N) → gh pr create → merge → main sync
```
