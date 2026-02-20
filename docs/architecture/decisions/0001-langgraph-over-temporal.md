---
title: "ADR-0001: LangGraph over Temporal"
type: adr
status: accepted
date: 2026-02-15
decision-makers: ["@sabyun"]
related-adrs: ["[[decisions/0003-ddd-four-layers]]", "[[decisions/0004-reference-passing]]"]
impacts: ["[[application/hmas-graph/MOC]]", "[[application/state-management/MOC]]", "[[application/live-session/MOC]]"]
tags: [langgraph, temporal, orchestration]
---

# ADR-0001: LangGraph over Temporal

## 컨텍스트

Jittda Sniper v4.0은 Temporal.io 기반의 고정 4-Phase 파이프라인으로 운영되었다. 이름은 "Agent"이지만 실제로는 단일 LLM 호출의 순차 나열 구조였으며, 에이전트 간 데이터는 `plain dict`로 암묵적 키 합의를 통해 전달되었다. 타입 안전성이 없었고, 동적 라우팅 및 에이전트 간 피드백 루프가 불가능했다.

v5.0에서는 HMAS(Hierarchical Multi-Agent System) 3계층 구조 (MetaAgent → 3 Supervisor → 11 Worker)를 구현해야 했다. 이 구조는 Fan-out/Fan-in 병렬 실행, 조건부 루프(QualityGate), WebSocket 실시간 스트리밍이 필요하며, Temporal의 고정 워크플로우 모델로는 자연스럽게 표현할 수 없었다.

sabyun이 명시한 요구사항: "에이전트 로직이 유기적으로 동적으로 피드백을 주고 받으면서 작동할 수 있도록", "현재는 플랜만 세우지 실제로는 랭체인 형식으로 진행되는 것 같다".

소스: `jittda_doc/jittda-v5-brainstorming-log.md` §3 Q1, §4

---

## 결정 옵션

### 옵션 A: Temporal 유지 + LangGraph 레이어 추가 (공존)

기존 Temporal 인프라 위에 LangGraph 레이어를 추가하는 방식.

**장점:**
- 기존 Temporal durability, retry, observability 유지
- 점진적 전환 가능, 리스크 분산

**단점:**
- 두 시스템을 동시에 관리해야 하는 운영 복잡도
- LangGraph의 동적 라우팅 장점이 Temporal 경계에서 차단됨
- Temporal Worker 프로세스 + LangGraph 상태 관리 이중화
- 코드베이스에 두 가지 오케스트레이션 패러다임 혼재

### 옵션 B: LangGraph 전면 교체 (선택)

Temporal을 완전히 제거하고 LangGraph만으로 전체 파이프라인을 구현.

**장점:**
- plan 문서(souce1-6)의 HMAS 비전을 서브그래프 중첩으로 자연스럽게 구현
- 단일 프레임워크로 전체 파이프라인 통제 — 디버깅 포인트 최소화
- `PostgreSQL AsyncPostgresSaver` Checkpointer로 Temporal 수준의 durability 확보
- `graph.astream()` + WebSocket으로 Temporal heartbeat 대체
- 별도 Worker 프로세스 불필요 — LangGraph가 FastAPI 내 백그라운드 태스크로 실행
- Instructor + Pydantic State로 타입 안전한 에이전트 간 통신 가능
- Tool-calling 패턴으로 정적 분석 도구들을 동적으로 선택/실행

**단점:**
- Temporal durability를 Checkpointer로 재구현해야 함
- LangGraph 서브그래프 디버깅이 상대적으로 복잡
- 분산 실행 시 LangGraph Cloud 필요 가능성
- 새 기술 학습 곡선

### 옵션 C: LangGraph 점진적 대체

단계별 이관 전략.

**단점:**
- 과도기적 상태가 장기화되어 기술 부채로 전환됨
- 두 시스템의 동작 차이로 인한 테스트 복잡도 증가

---

## 결정

**옵션 B: LangGraph 전면 교체 (Pure LangGraph HMAS)**

sabyun의 결정: "LangGraph 전면 교체 — Temporal의 durability, retry, observability를 LangGraph에서 재구현하는 가장 도전적인 경로."

---

## 근거

1. **단일 프레임워크 통제**: 의존성 최소화, 디버깅 포인트 단일화
2. **HMAS 비전 직접 구현**: MetaGraph > ForensicSupervisor/LogicSupervisor/StackSupervisor 서브그래프 중첩이 plan 문서 비전과 1:1 매핑
3. **durability 대체 가능**: `AsyncPostgresSaver.from_conn_string()` Checkpointer로 PostgreSQL 재활용
4. **heartbeat 대체 가능**: `graph.astream()` 이벤트 스트림을 WebSocket으로 브로드캐스팅
5. **Worker 프로세스 불필요**: LangGraph 노드가 FastAPI 내에서 실행 — 인프라 단순화
6. **Clean Slate와 정합**: ADR-0002에서 결정된 `jittda/` 신규 디렉토리 전략과 일치 — `temporalio` 패키지를 `pyproject.toml`에 처음부터 포함하지 않음

---

## 결과

- `jittda/backend/src/application/graphs/` 하위에 `meta_graph.py`, `forensic_graph.py`, `logic_graph.py`, `stack_graph.py`, `question_graph.py` 구성
- `langgraph>=1.0.8`, `langgraph-checkpoint-postgres>=3.0.4` 의존성 추가
- `temporalio` 패키지는 `pyproject.toml`에 포함하지 않음 (Clean Slate 원칙)
- 기존 `workflows/`, `activities/`, `worker.py` 파일은 폐기 대상 ([Liability] 분류)

---

## 관련 ADR

- ADR-0002: Clean Slate 재건축 전략 결정 (Temporal 코드가 애초에 존재하지 않는 구조)
- ADR-0003: DDD 4-Layer (LangGraph 노드는 Application Layer의 Thin Wrapper)
- ADR-0004: Reference Passing (LangGraph State에 Raw Data 대신 DB ID 전달)
