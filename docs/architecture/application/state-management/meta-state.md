---
title: "MetaState TypedDict"
type: component
layer: application
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[application/state-management/MOC]]"
depends-on:
  - "[[decisions/0004-reference-passing]]"
  - "[[application/state-management/reference-passing]]"
affects:
  - "[[application/hmas-graph/meta-agent]]"
  - "[[application/hmas-graph/conditional-edges]]"
linear: JIT-100
tags: [meta-state, typed-dict, langgraph, state, reference-passing]
---

# MetaState TypedDict

> MetaAgent Graph(Level 1)의 공유 상태. 5개 Phase를 관통하며 각 노드가 Reference Passing 패턴으로 결과를 전달한다. 모든 필드의 목적, 타입, 생산/소비 노드를 정의한다.

## 전체 필드 정의

```python
# application/states/meta_state.py
from typing import TypedDict, Optional

class MetaState(TypedDict):
    # ─── Core Context ───
    job_id: str

    # ─── References (DB ID만 전달) ───
    input_data_ref: str                          # jobs 테이블 ID
    identity_cluster_ref: Optional[str]          # identity_resolutions 테이블 ID

    # ─── Analysis Result References ───
    forensic_result_ref: Optional[str]           # analysis_results 테이블 ID
    logic_result_ref: Optional[str]              # analysis_results 테이블 ID
    stack_result_ref: Optional[str]              # analysis_results 테이블 ID

    # ─── Inline Metrics (가벼움) ───
    candidate_scores: Optional[dict]             # 4대 지표 점수

    # ─── Flow Control ───
    status: str
    revision_count: int                          # QualityGate 루프 (최대 2)
    errors: list[str]
```

## 필드별 상세

### Core Context

| 필드 | 타입 | 설명 | 생산 노드 | 소비 노드 |
|------|------|------|----------|----------|
| `job_id` | `str` (UUID) | 분석 작업 고유 식별자. 모든 노드에서 DB 조회 키로 사용 | 초기 입력 | 전체 노드 |

### References

| 필드 | 타입 | 참조 테이블 | 생산 노드 | 소비 노드 |
|------|------|-----------|----------|----------|
| `input_data_ref` | `str` (UUID) | `jobs` | InputRouter | PlanGenerator, Supervisors |
| `identity_cluster_ref` | `Optional[str]` | `identity_resolutions` | ForensicSupervisor | ProfileSynthesizer |
| `forensic_result_ref` | `Optional[str]` | `analysis_results` | ForensicSupervisor | ProfileSynthesizer |
| `logic_result_ref` | `Optional[str]` | `analysis_results` | LogicSupervisor | StackSupervisor, ProfileSynthesizer |
| `stack_result_ref` | `Optional[str]` | `analysis_results` | StackSupervisor | ProfileSynthesizer |

### Inline Metrics

| 필드 | 타입 | 크기 | 생산 노드 | 소비 노드 |
|------|------|------|----------|----------|
| `candidate_scores` | `Optional[dict]` | ~수 KB | ProfileSynthesizer | QuestionOrchestrator, OutputAssembler |

`candidate_scores` 내부 구조:

```python
{
    "authenticity_score": 0.82,     # 진정성 (ForensicSupervisor)
    "logic_score": 0.75,            # 코드 품질 (LogicSupervisor)
    "mastery_score": 0.68,          # 기술 숙련도 (StackSupervisor)
    "role_fit_score": 0.71,         # JD 적합성 (ProfileSynthesizer)
}
```

### Flow Control

| 필드 | 타입 | 설명 | 초기값 | 변경 시점 |
|------|------|------|--------|----------|
| `status` | `str` | 현재 진행 상태 | `"created"` | 각 노드 완료 시 갱신 |
| `revision_count` | `int` | QualityGate 재생성 횟수 | `0` | QualityGate revise 시 +1 |
| `errors` | `list[str]` | 비치명적 에러 누적 | `[]` | 에러 발생 시 append |

`status` 값 흐름:
```
created -> routed -> planned -> analyzing ->
  forensic_complete / logic_complete / stack_complete ->
  profile_synthesized -> questions_generated ->
  quality_approved -> complete
```

## Supervisor-Level State

각 Supervisor는 자체 TypedDict를 사용한다. MetaState와는 독립적이며, Subgraph 내부에서만 유효하다.

### ForensicState

```python
class ForensicState(TypedDict):
    github_urls: list[str]
    candidate_username: str | None
    linkedin_url: str | None
    jd_languages: list[str]
    jd_tech_stack: list[str]
    collected_repos: list[dict]
    identity_cluster: dict
    blame_attributions: list[dict]
    pure_contributions: list[dict]
    cleaned_diffs: list[dict]
    vibector_scores: list[dict]
    clave_fingerprint: dict
    plagiarism_report: dict
    forensic_summary: dict
    authenticity_score: float
```

### LogicState

```python
class LogicState(TypedDict):
    cleaned_diffs: list[dict]
    repo_paths: list[str]
    ast_analysis: list[dict]
    complexity_metrics: list[dict]
    quality_report: dict
    logic_summary: dict
    logic_score: float
```

### StackState

```python
class StackState(TypedDict):
    ast_analysis: list[dict]    # LogicSupervisor에서 전달
    cleaned_diffs: list[dict]
    jd_tech_stack: list[str]
    skill_extraction: dict
    api_depth_scores: list[dict]
    architecture_eval: dict
    stack_summary: dict
    mastery_score: float
```

## State 크기 분석

| State | 필드 수 | 예상 크기 | 비고 |
|-------|--------|----------|------|
| MetaState | 10 | ~2 KB | Reference Passing (UUID만) |
| ForensicState | 14 | 가변 (Subgraph 내부) | Checkpoint 대상 아님 (노드별 Save) |
| LogicState | 7 | 가변 (Subgraph 내부) | Checkpoint 대상 아님 |
| StackState | 8 | 가변 (Subgraph 내부) | Checkpoint 대상 아님 |

**핵심**: MetaState만 PostgreSQL Checkpointer로 직렬화된다. Supervisor-Level State는 Subgraph 내부에서만 사용되며, 각 Worker가 결과를 DB에 직접 Save하므로 Checkpoint 부담이 없다.

## 관련 문서

- [[state-management/reference-passing]] -- Reference Passing 패턴 상세
- [[state-management/checkpoint-schema]] -- PostgreSQL Checkpoint 테이블 구조
- [[hmas-graph/meta-agent]] -- MetaState를 사용하는 MetaAgent Graph
- [[hmas-graph/conditional-edges]] -- MetaState flow control 필드 활용
