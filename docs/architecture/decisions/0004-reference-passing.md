---
title: "ADR-0004: Reference Passing in LangGraph State"
type: adr
status: accepted
date: 2026-02-15
decision-makers: ["@sabyun"]
related-adrs: ["[[decisions/0001-langgraph-over-temporal]]", "[[decisions/0003-ddd-four-layers]]"]
impacts: ["[[application/state-management/MOC]]"]
tags: [langgraph, state, reference-passing, performance, checkpoint]
---

# ADR-0004: Reference Passing in LangGraph State

## 컨텍스트

LangGraph StateGraph는 각 노드 실행 후 State 전체를 PostgreSQL Checkpointer에 직렬화하여 저장한다. v5.0의 분석 파이프라인에서 처리하는 데이터는 대용량이다:

- Tree-sitter AST 파싱 결과: 대형 레포지토리의 경우 수십 MB
- git blame --line-porcelain 출력: 파일당 수 MB
- 전체 코드 diff: 커밋 수에 비례하여 급증

초기 설계에서는 이러한 Raw Data를 State에 직접 포함하는 방식을 사용했다. `extra.md` 아키텍처 최적화 리뷰에서 이 방식의 문제가 지적되었다: "State 객체에 Raw Data(AST, Diff 전문)를 직접 넣으면 DB Checkpoint 크기가 폭발하고 성능이 저하된다."

소스: `plan/v5-design/phase3-application.md` §10, `jittda_doc/jittda-v5-brainstorming-log.md` §19

---

## 문제: Raw Data State의 한계

```python
# AS-IS: State에 Raw Data 직접 포함 (문제 있는 방식)
class MetaState(TypedDict):
    raw_ast_data: dict          # 수십 MB 가능
    full_blame_output: str      # 수 MB
    full_diff_content: list     # 수 MB
    # ...
```

이 방식의 구체적 문제:

1. **PostgreSQL Checkpoint 크기 폭발**: 각 노드 실행마다 수십 MB가 DB에 직렬화됨
2. **메모리 힙 증가**: Python 프로세스 메모리가 분석 대상 레포지토리 크기에 비례하여 증가
3. **직렬화 오버헤드**: 대용량 dict/str의 BYTEA 직렬화/역직렬화 비용
4. **체크포인트 복구 지연**: 장애 후 재시작 시 대용량 State 로딩 시간 증가

---

## 결정 옵션

### 옵션 A: Raw Data 직접 저장

State TypedDict에 분석 결과 데이터를 직접 포함.

**장점:**
- 노드 구현이 단순 — State에서 직접 데이터 접근
- DB 조회 없이 다음 노드가 이전 결과 사용 가능

**단점:**
- State 크기가 분석 대상 데이터 크기에 비례하여 무제한 증가
- Checkpoint 저장/복구 성능 저하
- 메모리 힙 과다 사용

### 옵션 B: Reference Passing — DB ID만 전달 (선택)

State에는 결과 데이터의 DB Primary Key(UUID)만 저장. 실제 데이터는 `analysis_results` 테이블에 저장.

**장점:**
- State 크기를 상수 수준으로 유지 (job_id, result UUID 등 문자열만 포함)
- Checkpoint 직렬화 비용 최소화
- 장애 후 재시작 시 빠른 State 복구
- 각 노드의 결과가 DB에 영구 저장되어 독립적으로 조회/재사용 가능

**단점:**
- 각 노드에서 Load → Process → Save → Return Ref 4단계 패턴을 일관되게 따라야 함
- 다음 노드가 이전 결과를 사용할 때 DB 조회 한 번 필요

---

## 결정

**옵션 B: Reference Passing**

---

## 구현 패턴

### MetaState 정의

```python
# application/states/meta_state.py
class MetaState(TypedDict):
    # Core Context
    job_id: str

    # References (Not Raw Data -- DB ID만 전달)
    input_data_ref: str                          # jobs 테이블 ID
    identity_cluster_ref: Optional[str]          # identity_resolutions 테이블 ID

    # Analysis Result References (analysis_results 테이블 ID)
    forensic_result_ref: Optional[str]
    logic_result_ref: Optional[str]
    stack_result_ref: Optional[str]

    # Metrics (가벼우므로 State에 포함 가능)
    candidate_scores: Optional[dict]             # 4대 지표 점수 (수 KB 이하)

    # Flow Control
    status: str
    revision_count: int
    errors: list[str]
```

### 노드 구현 표준 패턴: Load -> Process -> Save -> Return Ref

모든 노드는 다음 4단계를 따른다:

```python
# application/nodes/logic_supervisor.py
async def logic_supervisor_node(state: MetaState) -> dict:
    job_id = state["job_id"]

    # 1. Load: DB에서 필요한 데이터 조회 (ref 기반)
    repo_files = await repo_repository.get_files(job_id)

    # 2. Process: 분석 수행 (domain + infrastructure 호출)
    ast_result = await ast_analyzer.analyze(repo_files)

    # 3. Save: 대용량 결과를 DB에 저장
    result_id = await analysis_repository.save_result(
        job_id, "logic_supervisor", ast_result
    )

    # 4. Return Ref: ID만 리턴 (State Checkpoint에는 ID만 기록)
    return {"logic_result_ref": result_id}
```

### DB 저장소: analysis_results 테이블

```sql
-- init.sql 발췌
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    worker_name VARCHAR(50) NOT NULL,
    supervisor_name VARCHAR(30) NOT NULL,
    result_data JSONB NOT NULL,   -- 실제 분석 데이터 저장 위치
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 근거

1. **State 크기 상수화**: MetaState는 최대 10여 개의 UUID 문자열만 포함 — 분석 대상 레포지토리 크기와 무관하게 일정
2. **Checkpoint 효율**: PostgreSQL Checkpointer가 직렬화하는 데이터가 수 KB 수준으로 고정
3. **결과 영속성**: 각 Worker의 결과가 `analysis_results` 테이블에 독립적으로 저장되어 재분석, 감사, 디버깅에 활용 가능
4. **장애 복구**: Checkpoint에는 ID만 있으므로 복구 시 DB에서 결과를 다시 로딩 가능
5. **DDD 정합**: Load/Save 로직이 `infrastructure/persistence/` 레이어에 위치 — Application Layer의 Thin Wrapper 원칙(ADR-0003)과 일치

---

## 결과

- `application/states/meta_state.py`에 Reference Passing 기반 MetaState 정의 (JIT-100)
- `infrastructure/persistence/analysis_repository.py`에 결과 저장/조회 로직 구현
- 모든 LangGraph 노드는 Load → Process → Save → Return Ref 패턴 준수
- `analysis_results` 테이블에 Worker별 결과 저장 (JIT-84 init.sql 포함)

---

## 관련 ADR

- ADR-0001: LangGraph (Reference Passing이 필요한 LangGraph State 구조의 원인)
- ADR-0003: DDD 4-Layer (Load/Save 로직의 계층 위치 정의)
