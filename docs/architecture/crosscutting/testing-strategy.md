---
title: "Testing Strategy"
type: component
layer: crosscutting
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[crosscutting/MOC]]"
depends-on:
  - "[[application/hmas-graph/MOC]]"
  - "[[domain/MOC]]"
affects: []
linear: JIT-120
tags: [testing, pytest, playwright, e2e, unit, integration]
---

# Testing Strategy

> 6단계 테스트 계층. Domain 순수 단위 테스트부터 E2E Playwright까지.
> 소스: `plan/v5-design/phase6-testing.md`

## 테스트 계층

| 레벨 | 대상 | 도구 | 커버리지 목표 |
|------|------|------|:---:|
| **Unit** | Domain 로직 (순수 함수) | pytest | 90% |
| **Unit** | Worker 개별 로직 | pytest + pytest-asyncio | 80% |
| **Integration** | Subgraph 내 Worker 연동 | pytest + testcontainer (PostgreSQL) | 70% |
| **E2E** | MetaGraph 전체 파이프라인 | pytest + Mock LLM | 60% |
| **Visual** | 프론트엔드 차트/UI | Playwright | 주요 페이지 |
| **Performance** | Worker 병렬 실행 시간 | pytest-benchmark | 기준선 대비 |

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

## Domain 테스트 원칙

Domain 레이어는 **외부 의존성이 0**이므로 순수 단위 테스트:

```python
# tests/domain/test_mailmap_builder.py
def test_noreply_email_detected():
    authors = [GitAuthor(name="Kim", email="123+kim@users.noreply.github.com")]
    profile = GitHubProfile(name="Kim Doe", email="kim@example.com")
    result = build_dynamic_mailmap(authors, profile, "12345")
    assert len(result) == 1
    assert result[0].confidence == "high"

def test_funnel_stage1_excludes_forks():
    repos = [RepoMetadata(is_fork=True), RepoMetadata(is_fork=False)]
    result = stage1_hard_filter(repos, ["python"], FunnelConfig())
    assert len(result) == 1
    assert result[0].is_fork is False
```

**규칙:**
- Mock/Patch **사용 금지** (순수 함수이므로 불필요)
- 입력값 -> 출력값 검증만 수행
- Edge case 반드시 포함 (빈 리스트, None, 경계값)
- 각 Domain 모듈별 최소 5개 이상 테스트 케이스

## E2E 테스트 시나리오

### Scenario 1: Happy Path (모든 데이터 소스 사용 가능)

```
입력: GitHub 3 repos + LinkedIn + Resume + JD
예상:
  - 4대 지표 산출 + 20개 질문 생성 + 신뢰도 "높음"
  - candidate_scores 테이블에 레코드 생성
  - 모든 Worker의 analysis_results 저장 (11개)
  - WebSocket으로 진행률 100% 전송
```

### Scenario 2: Partial Data (GitHub만 사용 가능)

```
입력: GitHub 1 repo + JD (LinkedIn/Resume 없음)
예상:
  - confidence = "low"
  - 질문 생성 정상 수행 (코드 기반만)
  - 에러 없이 완료
```

### Scenario 3: Quality Gate Rejection

```
입력: 강제 저품질 질문 주입 (Mock)
예상:
  - revision_count == 2
  - 루프 3회 이상 반복되지 않음
  - 최종 출력물 정상 생성
```

### Scenario 4: Worker Failure (SonarQube 다운)

```
입력: SonarQube 연결 불가 상태
예상:
  - 전체 파이프라인 에러 없이 완료
  - MetaState.errors에 W8 관련 에러 기록
  - 다른 Worker 결과에 영향 없음
```

### Scenario 5: Concurrent (3개 Job 동시)

```
입력: 3개 서로 다른 분석 요청 동시 제출
예상:
  - 교차 오염(데이터 혼재) 없음
  - checkpoints 테이블에서 thread_id별 독립 기록
  - deadlock 없음
```

## Makefile 테스트 명령

```makefile
test:
	docker compose exec backend pytest tests/ -v

test-domain:
	docker compose exec backend pytest tests/domain/ -v

test-e2e:
	docker compose exec backend pytest tests/e2e/ -v
```

## 관련 문서

- [[domain/MOC]] -- Domain 순수 함수 (테스트 대상)
- [[application/hmas-graph/MOC]] -- HMAS Graph (통합 테스트 대상)
- [[crosscutting/performance]] -- 성능 벤치마크
