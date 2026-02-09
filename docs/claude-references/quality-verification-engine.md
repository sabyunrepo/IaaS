# Agent Output Quality Verification Engine (상세)

> CLAUDE.md에서 분리된 상세 문서. 핵심 요약은 CLAUDE.md 본문 참조.

## 품질 검증 대상: 전체 파이프라인 아웃풋 매트릭스

```
Phase 0-1: INPUT & PLANNING
  enrich_input()          → URL 추출 정확도, LinkedIn/GitHub 유효성
  create_execution_plan() → 분석 대상 선정 정확도, 시간 추정 현실성

Phase 2: PARALLEL ANALYSIS (품질 영향도 HIGH)
  analyze_documents()     → 프로필 추출 완전성, 스킬 정확도
  analyze_jd()            → JD 요구사항 구조화 정확도, 누락 항목
  analyze_code()          → 코드 분석 깊이, 기술 스택 매칭, HYBRID 품질
  build_knowledge_graph() → KG 엔티티 정확도, 관계 타당성, 충돌 탐지

Phase 3: QUESTION GENERATION (품질 영향도 CRITICAL)
  select_topics()         → 토픽 균형, 후보자 특화도, 카테고리 배분
  craft_question()        → 질문 품질 8차원 (기존 quality_review)
  enhance_terminology()   → 용어 설명 정확성, 비전문가 이해도
  craft_evaluation_scenarios() → 평가 기준 구분도, 현실성
  design_follow_ups()     → 꼬리질문 깊이/연관성, 난이도 분기
  generate_decision_guide() → 채용 가이드 근거 타당성

Phase 4: RESULT GENERATION (품질 영향도 CRITICAL)
  generate_intel_brief()      → 요약 정확성, 역량 매칭 근거
  generate_deep_analysis()    → 레이더 차트 점수 근거, 스킬 매칭 정밀도
  generate_decision_support() → 추천 일관성, 위험 평가 근거
  finalize_output()           → 전체 조합 일관성, 데이터 무결성
```

## Phase별 품질 차원 정의

### Phase 2: 분석 품질 (Analysis Quality)

| Activity | 품질 차원 | 측정 방법 | 합격 기준 |
|----------|----------|----------|----------|
| `analyze_documents` | 프로필 완전성 | 필수 필드 채워짐 비율 | ≥90% 필드 추출 |
| `analyze_documents` | 스킬 정확도 | 추출 스킬 ↔ 실제 이력서 대조 | 환각 스킬 0개 |
| `analyze_jd` | 요구사항 구조화 | 필수/우대 분류 정확도 | ≥85% 정확도 |
| `analyze_jd` | 기술 스택 추출 | 명시 기술 vs 추출 기술 | 누락 ≤2개 |
| `analyze_code` | 레포 선별 정확도 | JD 관련 레포 선택 비율 | ≥80% 관련성 |
| `analyze_code` | 코드 분석 깊이 | AST 메트릭 + LLM 분석 완전성 | HYBRID 3단계 완수 |
| `build_knowledge_graph` | 엔티티 정확도 | 추출 엔티티 ↔ 원본 데이터 대조 | 환각 엔티티 0개 |
| `build_knowledge_graph` | 관계 타당성 | 관계 추론의 논리적 근거 | 근거 없는 관계 0개 |

### Phase 3: 질문 품질 — 10차원

| 차원 | 범위 | 설명 |
|------|------|------|
| Relevance | 0-10 | JD + 후보자 경험 ↔ 질문 관련성 |
| Clarity | 0-10 | 질문 명확성 |
| Depth | 0-10 | 기술적 깊이 |
| Bias-Free | 0-10 | 편향 없음 |
| Evidence Score | 0-100 | 근거 기반 vs 환각 |
| Hallucination Risk | L/M/H | 환각 위험도 |
| Duplicate Detection | Y/N | 중복 여부 |
| Specificity | specific/generic | 후보자 특화 vs 범용 |
| Eval Scenario Discriminability | 0-10 | 우수/보통/미흡 구분 명확도 |
| Terminology Accuracy | 0-10 | 용어 설명 정확성 |

### Phase 4: 결과물 품질 (Output Quality)

| Activity | 품질 차원 | 합격 기준 |
|----------|----------|----------|
| `generate_intel_brief` | 요약 정확성 + 매칭 근거 | 사실 오류 0개, 근거 없는 매칭 0개 |
| `generate_deep_analysis` | 레이더 점수 근거 + 스킬 매칭 | 각 축 근거 ≥1개, F1 ≥0.8 |
| `generate_decision_support` | 추천 일관성 + 위험 근거 | 모순 0개, 근거 없는 위험 0개 |
| `finalize_output` | 데이터 무결성 + 교차 일관성 | 누락 0개, 4탭 모순 0개 |

## Evidence Score 기준

| 점수 | 판정 | 조치 |
|------|------|------|
| 70-100 | PASS | 통과 |
| 40-69 | REVISE | 근거 보강 후 재생성 |
| 0-39 | REJECT | 삭제 및 재생성 |

## 현재 시스템 상태

### 구현 완료 (✅)
- 구조적 검증: `quality_review.py` — 카테고리 분포, 난이도 균형
- LLM 리뷰: `quality_review.yaml` — 8차원 평가
- Evidence Score: 근거 점수 0-100 게이트
- 중복 탐지: 의미적/완전 중복 질문 탐지
- 질문 수정: `revise_questions` Activity
- Langfuse 스코어 설정: `evaluation.py` SCORE_CONFIGS
- 코드 분석 검증: `validate_code_analysis()`
- Langfuse 트레이싱: Job 단위 트레이스

### 미연결/미사용 (⚠️)

| 갭 | 영향도 |
|----|--------|
| Langfuse 스코어 미연결 | 🔴 HIGH — `create_score()` 존재하나 미호출 |
| 품질 결과 미저장 | 🔴 HIGH — evidence_score DB 미저장 |
| 프론트엔드 미표시 | 🔴 HIGH — 품질 지표 Result 페이지 미노출 |
| 수정 후 재평가 없음 | 🟡 MED |
| Phoenix eval 미사용 | 🟡 MED |
| Phase 2 분석 품질 미검증 | 🔴 HIGH |
| Phase 4 결과물 품질 미검증 | 🔴 HIGH |
| 교차 일관성 검증 없음 | 🟡 MED |

## 전체 파이프라인 품질 검증 아키텍처

```
Phase 0-1 → 구조적 검증 (URL, 파일 포맷)
    ↓
Phase 2 → 프로필 완전성 + JD 구조화 + validate_code_analysis() ✅ + KG 검증 [TO-DO]
    ↓
Phase 3 → 카테고리 균형 + 8+2차원 품질 평가 + quality_review ✅ + revise_questions ✅ [재평가 미연결]
    ↓
Phase 4 → Intel/Deep/Decision 검증 [ALL TO-DO]
    ↓
Phase 5 → Langfuse 스코어 + DB 저장 + 추세 대시보드
```

## 품질 검증 체크리스트

### Phase 2: 분석 품질
- [ ] 프로필 추출 완전성 (필수 필드 ≥90%)
- [ ] 스킬 정확도 (환각 스킬 0)
- [ ] JD 구조화 정확도 (기술 누락 ≤2개)
- [ ] 코드 분석 깊이 (HYBRID 3단계 완수)
- [ ] KG 엔티티 정확도

### Phase 3: 질문 품질
- [ ] 지원자 데이터 기반 여부
- [ ] 중복 질문 제거 (유사도 >0.85)
- [ ] 수준 적절성 (경력 수준 매칭)
- [ ] 범용 질문 비율 <20%
- [ ] 카테고리 균형 (≥3개/카테고리)
- [ ] 꼬리질문 품질 (분기 논리성)
- [ ] 평가 시나리오 구분도

### Phase 4: 결과물 품질
- [ ] Intel Brief 정확성 (사실 오류 0)
- [ ] 역량 매칭 근거 (evidence_source 필수)
- [ ] 레이더 점수 근거 (5축 정량 근거)
- [ ] 추천 일관성 (점수/분석/추천 모순 0)
- [ ] 교차 일관성 (4탭 모순 0)
