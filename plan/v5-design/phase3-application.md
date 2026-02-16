# Phase 3: Application Layer - Graphs

> 원본 설계서: `plan/2026-02-15-v5-final-design.md`
> Linear 티켓: JIT-100 ~ JIT-105

## Linear 티켓 매핑

| 티켓 | 제목 | 참조 섹션 |
|------|------|----------|
| JIT-100 | State 정의 (MetaState, ForensicState, LogicState, StackState) | §10.1 |
| JIT-101 | ForensicSupervisor Graph (Collector -> IdentityResolver -> Pruner -> [Vibector/CLAVE/Datasketch]) | §10.3, §6.3 |
| JIT-102 | LogicSupervisor Graph ([ASTAnalyzer/ComplexityMeter/QualityScanner] 병렬) | §10.4, §6.3 |
| JIT-103 | StackSupervisor Graph ([SkillExtractor/APIDepth/Architecture] 병렬) | §10.4, §6.3 |
| JIT-104 | MetaAgent Graph 조립 (전체 연결 + Fan-out/Fan-in + QualityGate 루프) | §10.2, §6.2 |
| JIT-105 | FastAPI + WebSocket 통합 (Interface Layer 라우트 + 실시간 스트리밍) | §10.5 |

---

## §6. 3계층 HMAS 아키텍처

### 6.1 시스템 아키텍처 개요

```
                    +----------------------------------+
                    |     Frontend (React 19 + D3.js)   |
                    |  Tailwind + WebSocket Streaming    |
                    +--------------+-------------------+
                                   | REST + WebSocket
                    +--------------v-------------------+
                    |  Interface Layer (FastAPI Routes)  |
                    |  Job CRUD + Auth + WS Streaming    |
                    +--------------+-------------------+
                                   |
                    +--------------v-------------------+
                    |   Application Layer (LangGraph)    |
                    |  MetaAgent + Supervisor Subgraphs  |
                    |  PostgreSQL Checkpointer           |
                    |  + Langfuse Tracing                |
                    +--------------+-------------------+
                                   |
              +--------------------+--------------------+
              |                    |                     |
   +----------v------+  +--------v--------+  +--------v--------+
   | ForensicSuper   |  | LogicSuper      |  | StackSuper      |
   | (수집/정제/진정성)|  | (복잡도/품질)    |  | (전문성/스택)    |
   +------+----------+  +------+----------+  +------+----------+
          |                    |                     |
    +-----+-----+        +----+----+          +----+----+
    |     |     |        |    |    |          |    |    |
   W1    W2   W3-5      W6   W7   W8        W9   W10  W11
```

### 6.2 3계층 HMAS 구조

```
Level 1: MetaAgent (총괄 오케스트레이터)
|
+-- Phase 0: InputRouter
|   +-- 입력 파싱 + 소스 라우팅
|
+-- Phase 1: PlanGenerator
|   +-- LLM 기반 실행 계획 동적 생성
|
+-- Phase 2: AnalysisDispatcher (Fan-out)
|   +-- Level 2: ForensicSupervisor
|   |   +-- Level 3: CollectorWorker (W1) -- GitHub GraphQL + Identity Resolution
|   |   +-- Level 3: CleanerWorker (W2) -- Funnel Selection + 노이즈 제거
|   |   +-- Level 3: VibectorWorker (W3) -- AI 코드 탐지 (WPM)
|   |   +-- Level 3: CLAVEWorker (W4) -- 스타일로메트리
|   |   +-- Level 3: DatasketchWorker (W5) -- 표절 탐지 (MinHash/LSH)
|   |
|   +-- Level 2: LogicSupervisor
|   |   +-- Level 3: ASTAnalyzerWorker (W6) -- Tree-sitter
|   |   +-- Level 3: ComplexityMeterWorker (W7) -- Radon/Lizard
|   |   +-- Level 3: QualityScannerWorker (W8) -- SonarQube
|   |
|   +-- Level 2: StackSupervisor (LogicSupervisor 완료 후 실행)
|       +-- Level 3: SkillExtractorWorker (W9)
|       +-- Level 3: APIDepthAnalyzerWorker (W10)
|       +-- Level 3: ArchitectureEvaluatorWorker (W11)
|
+-- Phase 2.5: ProfileSynthesizer (Fan-in)
|   +-- 모든 분석 결과 -> UnifiedCandidateProfile + 4대 지표 산출
|
+-- Phase 3: QuestionOrchestrator
|   +-- TopicSelector (벡터 검색 기반)
|   +-- QuestionCrafter x N (3전략 병렬)
|   +-- EnhancementAgents x 5 (병렬)
|
+-- Phase 4: QualityGate
|   +-- Reviewer (품질 검증)
|   +-- Reviser (조건부 재생성, 최대 2회)
|
+-- Phase 5: OutputAssembler
    +-- IntelBriefGenerator
    +-- DeepAnalysisGenerator
    +-- DecisionSupportGenerator
    +-- FinalScriptAssembler
```

### 6.3 Supervisor 내부 Worker 의존성

```
ForensicSupervisor:
  Collector -> IdentityResolver -> SemanticPruner -> [Vibector, CLAVE, Datasketch] (병렬) -> Aggregator

LogicSupervisor:
  [ASTAnalyzer, ComplexityMeter, QualityScanner] (완전 병렬) -> Aggregator

StackSupervisor (LogicSupervisor의 AST 결과에 의존):
  [SkillExtractor, APIDepthAnalyzer, ArchitectureEvaluator] (완전 병렬) -> Aggregator
```

**의존성 제약:**
- ForensicSupervisor와 LogicSupervisor는 **병렬 실행**
- StackSupervisor는 LogicSupervisor **완료 후 실행** (AST 결과 필요)

---

## §10. LangGraph 그래프 설계 (Reference Passing)

> **extra.md 반영:** State 객체에 Raw Data(AST, Diff 전문)를 직접 넣으면 DB Checkpoint 크기가 폭발하고 성능이 저하된다. **DB Primary Key(UUID)만 전달**하는 Reference Passing 패턴을 적용한다.

### 10.1 MetaState 정의 (Reference Passing 적용)

```python
# application/states/meta_state.py
from typing import TypedDict, Optional

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
    candidate_scores: Optional[dict]             # 4대 지표 점수

    # Flow Control
    status: str
    revision_count: int                          # 최대 2회 루프
    errors: list[str]
```

### 10.1.1 노드 구현 패턴: Load -> Process -> Save -> Return Ref

모든 노드는 아래 4단계를 따른다. State에는 **결과 자체**가 아닌 **결과가 저장된 DB의 ID(참조)**만 리턴한다.

```python
# application/nodes/logic_supervisor.py
async def logic_supervisor_node(state: MetaState) -> dict:
    job_id = state["job_id"]

    # 1. Load: DB에서 필요한 데이터 조회 (ref 기반)
    repo_files = await repo_repository.get_files(job_id)

    # 2. Process: 분석 수행
    ast_result = await ast_analyzer.analyze(repo_files)

    # 3. Save: 대용량 결과를 DB에 저장
    result_id = await analysis_repository.save_result(
        job_id, "logic_supervisor", ast_result
    )

    # 4. Return Ref: ID만 리턴 (State Checkpoint에는 ID만 기록)
    return {"logic_result_ref": result_id}
```

### 10.2 MetaAgent Graph (Level 1)

```python
# application/graphs/meta_graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

def build_meta_graph() -> StateGraph:
    builder = StateGraph(MetaState)

    # 노드 등록
    builder.add_node("input_router", input_router_node)
    builder.add_node("plan_generator", plan_generator_node)
    builder.add_node("forensic_supervisor", forensic_subgraph)
    builder.add_node("logic_supervisor", logic_subgraph)
    builder.add_node("stack_supervisor", stack_subgraph)
    builder.add_node("profile_synthesizer", profile_synthesizer_node)
    builder.add_node("question_orchestrator", question_subgraph)
    builder.add_node("quality_gate", quality_gate_node)
    builder.add_node("output_assembler", output_assembler_node)

    # Phase 0-1: 순차
    builder.add_edge(START, "input_router")
    builder.add_edge("input_router", "plan_generator")

    # Phase 2: Fan-out (ForensicSuper || LogicSuper -> StackSuper)
    builder.add_edge("plan_generator", "forensic_supervisor")
    builder.add_edge("plan_generator", "logic_supervisor")
    builder.add_edge("logic_supervisor", "stack_supervisor")  # AST 의존

    # Phase 2.5: Fan-in
    builder.add_edge("forensic_supervisor", "profile_synthesizer")
    builder.add_edge("stack_supervisor", "profile_synthesizer")

    # Phase 3-4: 순차 + 조건부 루프
    builder.add_edge("profile_synthesizer", "question_orchestrator")
    builder.add_edge("question_orchestrator", "quality_gate")

    builder.add_conditional_edges(
        "quality_gate",
        should_revise,  # revision_count < 2 && has_flagged
        {"revise": "question_orchestrator", "approve": "output_assembler"},
    )

    # Phase 5: 최종 출력
    builder.add_edge("output_assembler", END)

    return builder
```

### 10.3 ForensicSupervisor Subgraph (Level 2)

```python
# application/graphs/forensic_graph.py
class ForensicState(TypedDict):
    github_urls: list[str]
    candidate_username: str | None
    linkedin_url: str | None
    jd_languages: list[str]
    jd_tech_stack: list[str]

    # Worker 결과
    collected_repos: list[dict]
    identity_cluster: dict
    blame_attributions: list[dict]
    pure_contributions: list[dict]
    cleaned_diffs: list[dict]
    vibector_scores: list[dict]
    clave_fingerprint: dict
    plagiarism_report: dict

    # 통합
    forensic_summary: dict
    authenticity_score: float

def build_forensic_graph() -> StateGraph:
    builder = StateGraph(ForensicState)

    builder.add_node("collector", collector_worker)          # GraphQL + Funnel Stage 1-3
    builder.add_node("identity_resolver", identity_resolver) # Mailmap + Blame
    builder.add_node("semantic_pruner", semantic_pruner)      # Tree-sitter AST pruning
    builder.add_node("vibector", vibector_worker)             # WPM 분석
    builder.add_node("clave", clave_worker)                   # 스타일로메트리
    builder.add_node("datasketch", datasketch_worker)         # 표절 탐지
    builder.add_node("forensic_aggregator", forensic_aggregator)

    # 순차: collector -> identity_resolver -> semantic_pruner
    builder.add_edge(START, "collector")
    builder.add_edge("collector", "identity_resolver")
    builder.add_edge("identity_resolver", "semantic_pruner")

    # 병렬: pruner 후 진정성 검증 3개 동시
    builder.add_edge("semantic_pruner", "vibector")
    builder.add_edge("semantic_pruner", "clave")
    builder.add_edge("semantic_pruner", "datasketch")

    # Fan-in
    builder.add_edge("vibector", "forensic_aggregator")
    builder.add_edge("clave", "forensic_aggregator")
    builder.add_edge("datasketch", "forensic_aggregator")

    return builder
```

### 10.4 LogicSupervisor / StackSupervisor Subgraphs

```python
# application/graphs/logic_graph.py
class LogicState(TypedDict):
    cleaned_diffs: list[dict]
    repo_paths: list[str]
    ast_analysis: list[dict]
    complexity_metrics: list[dict]
    quality_report: dict
    logic_summary: dict
    logic_score: float

def build_logic_graph() -> StateGraph:
    builder = StateGraph(LogicState)
    builder.add_node("ast_analyzer", ast_analyzer_worker)
    builder.add_node("complexity_meter", complexity_meter_worker)
    builder.add_node("quality_scanner", quality_scanner_worker)
    builder.add_node("logic_aggregator", logic_aggregator)

    # 3개 Worker 완전 병렬
    builder.add_edge(START, "ast_analyzer")
    builder.add_edge(START, "complexity_meter")
    builder.add_edge(START, "quality_scanner")
    builder.add_edge("ast_analyzer", "logic_aggregator")
    builder.add_edge("complexity_meter", "logic_aggregator")
    builder.add_edge("quality_scanner", "logic_aggregator")
    return builder

# application/graphs/stack_graph.py
class StackState(TypedDict):
    ast_analysis: list[dict]    # LogicSupervisor에서 전달
    cleaned_diffs: list[dict]
    jd_tech_stack: list[str]
    skill_extraction: dict
    api_depth_scores: list[dict]
    architecture_eval: dict
    stack_summary: dict
    mastery_score: float

def build_stack_graph() -> StateGraph:
    builder = StateGraph(StackState)
    builder.add_node("skill_extractor", skill_extractor_worker)
    builder.add_node("api_depth_analyzer", api_depth_analyzer_worker)
    builder.add_node("architecture_evaluator", architecture_evaluator_worker)
    builder.add_node("stack_aggregator", stack_aggregator)

    # 3개 Worker 완전 병렬
    builder.add_edge(START, "skill_extractor")
    builder.add_edge(START, "api_depth_analyzer")
    builder.add_edge(START, "architecture_evaluator")
    builder.add_edge("skill_extractor", "stack_aggregator")
    builder.add_edge("api_depth_analyzer", "stack_aggregator")
    builder.add_edge("architecture_evaluator", "stack_aggregator")
    return builder
```

### 10.5 FastAPI 통합

```python
# interface/api/routes/jobs.py
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def run_analysis(job_id: str, input_data: dict):
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        graph = build_meta_graph().compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": job_id}}

        async for event in graph.astream(input_data, config, stream_mode="updates"):
            # WebSocket으로 실시간 전송
            await ws_manager.broadcast(job_id, event)
```
