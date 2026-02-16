# Phase 6: 통합 테스트 + 정리

> 원본 설계서: `plan/2026-02-15-v5-final-design.md`
> Linear 티켓: JIT-120 ~ JIT-123

## Linear 티켓 매핑

| 티켓 | 제목 | 참조 섹션 |
|------|------|----------|
| JIT-120 | Domain 단위 테스트 (Identity, Scoring, Funnel 테스트, 커버리지 90%) | §17.1, §17.2 |
| JIT-121 | E2E 통합 테스트 (Happy Path + Partial Data + Worker Failure + Concurrent) | §17.1, §17.3 |
| JIT-122 | Playwright E2E (Overview + Code Deep Dive 탭 렌더링 검증) | §17.1 |
| JIT-123 | 성능 벤치마크 + 문서화 (기존 Temporal 대비 실행 시간 비교, 아키텍처 다이어그램) | §17.1 |

---

## §17. 테스트 전략

### 17.1 테스트 계층

| 레벨 | 대상 | 도구 | 커버리지 목표 |
|------|------|------|-------------|
| **Unit** | Domain 로직 (순수 함수) | pytest | 90% |
| **Unit** | Worker 개별 로직 | pytest + pytest-asyncio | 80% |
| **Integration** | Subgraph 내 Worker 연동 | pytest + testcontainer (PostgreSQL) | 70% |
| **E2E** | MetaGraph 전체 파이프라인 | pytest + Mock LLM | 60% |
| **Visual** | 프론트엔드 차트/UI | Playwright | 주요 페이지 |
| **Performance** | Worker 병렬 실행 시간 | pytest-benchmark | 기준선 대비 |

### 17.2 Domain 테스트 원칙

Domain 레이어는 **외부 의존성이 0**이므로, 순수 단위 테스트로 작성한다.

```python
# tests/domain/test_mailmap_builder.py
def test_noreply_email_detected():
    authors = [GitAuthor(name="Kim", email="123+kim@users.noreply.github.com")]
    profile = GitHubProfile(name="Kim Doe", email="kim@example.com")
    result = build_dynamic_mailmap(authors, profile, "12345")
    assert len(result) == 1
    assert result[0].confidence == "high"

def test_levenshtein_clustering():
    authors = [GitAuthor(name="Kim Doe", email="kimdoe@company.com")]
    profile = GitHubProfile(name="Kim D.", email="kim@personal.com")
    result = build_dynamic_mailmap(authors, profile, "12345", threshold=0.75)
    assert len(result) >= 1

def test_funnel_stage1_excludes_forks():
    repos = [RepoMetadata(is_fork=True), RepoMetadata(is_fork=False)]
    result = stage1_hard_filter(repos, ["python"], FunnelConfig())
    assert len(result) == 1
    assert result[0].is_fork is False
```

**테스트 작성 규칙:**
- Domain 테스트는 Mock/Patch **사용 금지** (순수 함수이므로 불필요)
- 입력값 -> 출력값 검증만 수행
- Edge case 반드시 포함 (빈 리스트, None, 경계값)
- 각 Domain 모듈별 최소 5개 이상 테스트 케이스

### 17.3 테스트 시나리오

#### Scenario 1: Happy Path (모든 데이터 소스 사용 가능)

```
입력: GitHub 3 repos + LinkedIn + Resume + JD
예상 흐름:
  1. InputRouter: 모든 소스 파싱 성공
  2. PlanGenerator: 전체 Worker 실행 계획 생성
  3. ForensicSupervisor: W1-W5 모두 실행
  4. LogicSupervisor: W6-W8 병렬 실행
  5. StackSupervisor: W9-W11 병렬 실행 (LogicSupervisor 완료 후)
  6. ProfileSynthesizer: 4대 지표 산출
  7. QuestionOrchestrator: 3전략 x N개 질문 생성
  8. QualityGate: 1회 통과 (revision_count=0)
  9. OutputAssembler: 모든 출력물 생성
예상 결과: 4대 지표 산출 + 20개 질문 생성 + 신뢰도 "높음"
검증 포인트:
  - candidate_scores 테이블에 레코드 생성됨
  - 모든 Worker의 analysis_results 저장됨 (11개)
  - WebSocket으로 진행률 100% 전송됨
```

#### Scenario 2: Partial Data (GitHub만 사용 가능)

```
입력: GitHub 1 repo + JD (LinkedIn/Resume 없음)
예상 흐름:
  1. InputRouter: LinkedIn/Resume 소스 비활성화
  2. ForensicSupervisor: CollectorWorker가 LinkedIn 스킵
  3. SkillExtractorWorker: GitHub 코드만으로 스킬 추출
  4. ProfileSynthesizer: 제한된 데이터로 4대 지표 산출
예상 결과: 4대 지표 산출 (일부 낮은 점수) + 신뢰도 "낮음"
검증 포인트:
  - confidence = "low"
  - 질문 생성은 정상 수행 (코드 기반만)
  - 에러 없이 완료
```

#### Scenario 3: Quality Gate Rejection (질문 품질 미달)

```
입력: 강제 저품질 질문 주입 (테스트용 Mock)
예상 흐름:
  1. QuestionOrchestrator: 의도적 저품질 질문 생성
  2. QualityGate Reviewer: 품질 미달 판정
  3. Reviser: 재생성 요청 (revision_count=1)
  4. QuestionOrchestrator: 재실행
  5. QualityGate Reviewer: 재검증
  6. 최대 2회 루프 후 강제 통과
예상 결과: revision_count=2, 최종 질문 세트 생성
검증 포인트:
  - MetaState.revision_count == 2
  - 루프가 3회 이상 반복되지 않음
  - 최종 출력물 정상 생성
```

#### Scenario 4: Worker Failure (SonarQube 서비스 다운)

```
입력: SonarQube 연결 불가 상태
예상 흐름:
  1. QualityScannerWorker (W8): SonarQube 연결 실패
  2. W8.handle_error(): Graceful Degradation 실행
  3. LogicAggregator: W8 결과 없이 W6+W7 결과만으로 집계
  4. 나머지 Worker 정상 실행
예상 결과:
  - 논리력 지표에서 인지적 복잡도(SonarQube) 항목만 null
  - 나머지 지표 정상 산출
  - 에러 로그에 W8 실패 기록
검증 포인트:
  - 전체 파이프라인이 에러 없이 완료
  - MetaState.errors에 W8 관련 에러 기록
  - 다른 Worker 결과에 영향 없음
```

#### Scenario 5: Concurrent (3개 Job 동시 실행)

```
입력: 3개의 서로 다른 분석 요청 동시 제출
예상 흐름:
  1. 각 Job별 고유 thread_id로 LangGraph 실행
  2. LangGraph Checkpointer가 각 thread별 state 독립 관리
  3. DB 레벨에서 job_id 기반 격리
예상 결과:
  - 3개 Job 모두 정상 완료
  - 교차 오염(데이터 혼재) 없음
검증 포인트:
  - 각 job_id의 analysis_results가 다른 job의 데이터를 포함하지 않음
  - checkpoints 테이블에서 thread_id별 독립 기록 확인
  - 동시 실행 시 deadlock 없음
```

---

## 테스트 디렉토리 구조

```
backend/tests/
├── domain/                     # 순수 단위 테스트 (Mock 없음)
│   ├── test_mailmap_builder.py
│   ├── test_blame_filter.py
│   ├── test_semantic_pruner.py
│   ├── test_funnel_rules.py
│   ├── test_scoring_calculator.py
│   └── test_scoring_normalizer.py
│
├── infrastructure/             # Mock 기반 어댑터 테스트
│   ├── test_tree_sitter_adapter.py
│   ├── test_github_graphql_client.py
│   ├── test_blame_runner.py
│   ├── test_instructor_client.py
│   ├── test_pgvector_store.py
│   └── test_datasketch_adapter.py
│
├── application/                # LangGraph 통합 테스트
│   ├── test_forensic_graph.py
│   ├── test_logic_graph.py
│   ├── test_stack_graph.py
│   ├── test_meta_graph.py
│   └── test_quality_gate.py
│
└── e2e/                        # E2E 파이프라인 테스트
    ├── test_happy_path.py
    ├── test_partial_data.py
    ├── test_worker_failure.py
    └── test_concurrent.py
```

---

## 성능 벤치마크 기준

| 항목 | v4.0 (Temporal) 기준선 | v5.0 (LangGraph) 목표 |
|------|----------------------|---------------------|
| 전체 파이프라인 실행 시간 (3 repos) | ~15분 | ~10분 (33% 단축) |
| Worker 병렬화 효율 | 순차 실행 | Fan-out 3-5x 병렬 |
| State Checkpoint 크기 | N/A | < 10KB (Reference Passing) |
| LLM 토큰 사용량 (분석당) | ~50K tokens | ~30K tokens (Funnel Selection) |
| 동시 Job 처리 | 1개 (Temporal Worker) | 3개+ (LangGraph thread) |
