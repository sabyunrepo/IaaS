# Workflow Phase Details

상세 Phase 구현 정보. SKILL.md에서 참조됨.

## Phase 0: Smart Input Extraction

### enrich_input() Activity
- **입력**: `InputData` (raw user input)
- **출력**: `EnrichedInput` (교차 추출 완료)
- **핵심 로직**:
  1. PDF/DOCX 텍스트에서 URL 교차 추출 (LinkedIn, GitHub)
  2. LinkedIn URL 발견 시 → Bright Data API로 프로필 수집
  3. GitHub URL 발견 시 → 레포 목록 추출
  4. 이력서/포트폴리오/JD 텍스트 추출
- **외부 의존**: Bright Data API (LinkedIn), PyGithub (GitHub)

## Phase 1: Planning

### create_plan() Activity
- **입력**: `EnrichedInput` → **출력**: `ExecutionPlan`
- **핵심 로직**:
  1. GitHub API로 레포 크기/언어/커밋 수 조회
  2. 분석 대상 레포 선정 (JD 관련도 기반)
  3. 예상 소요 시간 추정
  4. 실행 전략 결정 (FAST/STANDARD/DEEP)

## Phase 2: Parallel Analysis

### 3개 Activity 병렬 실행 (`workflow.wait_all()`)

#### analyze_documents()
- PDF/DOCX → `CandidateProfile`
- 이름, 경력, 스킬, 학력, 프로젝트 추출
- LLM으로 구조화 (Pydantic AI)

#### analyze_code()
- **4-Phase HYBRID 분석**:
  1. Overview: PyGithub API로 레포 메타데이터
  2. Deep: PyDriller로 커밋 히스토리 + AST 분석
  3. LLM Synthesis: 코드 패턴/아키텍처 의미 해석
  4. Validation: `validate_code_analysis()` 완전성 검증
- 출력: `CodeAnalysis` (기술 스택, 코드 품질 메트릭, 기여도)

#### analyze_jd()
- JD 텍스트 → `JDAnalysis`
- 필수/우대 요구사항 분류
- 기술 스택 추출, 연차 요구, 역할 분석

## Phase 3: Question Generation

### 워크플로우 상세
```
select_topics(25개)
  → craft_question × 10 병렬 Worker
    → enhance_terminology (용어 설명)
    → craft_evaluation_scenarios (평가 시나리오)
    → design_follow_ups (꼬리질문)
      → quality_review (최대 3회 루프)
        → revise_questions (REVISE 판정 질문 수정)
```

### 카테고리 균형 (5 × 5)
- role_fit: 5개 (Easy 2, Medium 2, Hard 1)
- technical: 5개
- execution: 5개
- communication: 5개
- risk_flags: 5개

### Quality Gate
- Evidence Score ≥70 → PASS
- Evidence Score 40-69 → REVISE (자동 수정)
- Evidence Score <40 → REJECT (재생성)
- 중복 유사도 >0.85 → 제거 + 대체

## Phase 4: Result Generation + Finalization

### 4탭 생성 (병렬)
1. `generate_intel_brief()` → Intel Brief 탭
2. `generate_deep_analysis()` → Deep Analysis 탭
3. `generate_decision_support()` → Decision 탭
4. `finalize_output()` → 전체 조합 + Live Interview 탭

### Supervisor 검증
- Hallucination 체크: 코드 참조 실제 존재 확인
- 교차 일관성: 4탭 간 데이터 모순 없음
- 비개발자 가독성: 용어 설명 누락 확인
