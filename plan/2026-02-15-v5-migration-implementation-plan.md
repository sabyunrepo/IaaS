# Jittda Sniper v5.0 — LangGraph HMAS 전면 마이그레이션 구현 계획

> 작성일: 2026-02-15
> 상태: 리뷰 대기
> 기반: plan/souce1-6.md (비전), plan/review1.md (설계 리뷰)

---

## Context

현재 Vantict Sniper v4.0은 Temporal.io 기반 고정 4-Phase 파이프라인으로, 단일 LLM Activity를 "에이전트"로 명명하지만 실제 에이전틱 루프가 없다. plan 문서(souce1-6)의 비전인 **계층적 멀티 에이전트 시스템(HMAS)**과 현 구현 사이에 큰 갭이 존재한다.

리뷰에서 지적된 4가지 핵심 결함:
1. **Identity Resolution 부재** — `git blame -w -M -C` 미사용, 동적 mailmap 없음, AST semantic pruning 없음
2. **JD 적합성 선별 부재** — 모든 레포 분석은 토큰 낭비, LLM tech_stack 미활용
3. **DDD 미적용** — 비즈니스 로직이 Temporal Activity에 혼재
4. **선별적 마이그레이션 필요** — 맹목적 이식은 기술 부채를 이자까지 가져옴

**확정된 설계 결정:**
- LangGraph 전면 교체 (Big Bang)
- Instructor + Pydantic 구조화 출력
- Full Stack 정적 분석 (Tree-sitter + Radon/Lizard + SonarQube + Datasketch)
- DDD 아키텍처 (Domain / Application / Infrastructure)

---

## Phase 0: Scaffolding (3일)

### 0.1 DDD 디렉토리 구조 생성

```
backend/app/
├── domain/           # 순수 비즈니스 로직 (외부 의존성 0)
│   ├── identity/     # Identity Resolution (mailmap, blame, pruning)
│   ├── scoring/      # 점수 산출 (기존 scoring_formulas.py 이전)
│   ├── matching/     # JD-후보자 매칭 (funnel, skill)
│   └── question/     # 질문 생성 규칙 (카테고리 가중치, 품질)
├── application/      # LangGraph 오케스트레이션
│   ├── graphs/       # StateGraph 정의 (meta, forensic, logic, stack, question)
│   ├── nodes/        # LangGraph 노드 함수 (thin wrapper)
│   ├── states/       # TypedDict State 정의
│   └── use_cases/    # 유스케이스 서비스
└── infrastructure/   # 외부 서비스 어댑터
    ├── git/          # blame_runner, clone_manager, mailmap_writer
    ├── github/       # graphql_client, rest_client
    ├── analysis/     # tree_sitter, radon, lizard, sonarqube, datasketch
    ├── llm/          # cached_client, instructor_client, langfuse
    ├── linkedin/     # brightdata_client
    ├── embedding/    # pgvector_store (확장)
    └── persistence/  # job_repository, kg_repository, score_repository
```

### 0.2 인프라 변경

**Docker Compose:**
- 제거: `temporal`, `temporal-ui`, `worker` 서비스
- 추가: `sonarqube` (sonarqube:community, port 9000)
- 수정: `backend` — Temporal 의존성 제거, `LANGGRAPH_CHECKPOINTER_URI`, `SONARQUBE_URL` 추가
- `postgres` init.sql에 `CREATE DATABASE sonarqube` 추가

**Python 의존성:**
```diff
- temporalio==1.5.0
+ langgraph>=0.2.0
+ langgraph-checkpoint-postgres>=2.0.0
+ instructor>=1.5.0
+ tree-sitter>=0.24.0 + tree-sitter-{python,javascript,typescript,java,go}
+ datasketch>=1.6.5
+ python-Levenshtein>=0.25.0
+ radon>=6.0.1
+ lizard>=1.17.10
+ bandit>=1.8.0
```

### 0.3 DB 마이그레이션 (`004_langgraph_migration.py`)

신규 테이블:
- `analysis_results` (job_id, worker_name, supervisor_name, result_data JSONB, metrics JSONB)
- `candidate_scores` (job_id, logic/mastery/stability/authenticity scores, weighted_total, UNIQUE(job_id))
- `identity_resolutions` (job_id, github_node_id, canonical_name/email, mailmap_entries JSONB, pure/logic lines, UNIQUE(job_id))
- `sonarqube_projects` (job_id, project_key, scan_status, result_data JSONB)

수정: `jobs` — `temporal_workflow_id` DROP, `langgraph_thread_id` ADD

**검증:** `docker compose up -d && alembic upgrade head` 성공

---

## Phase 1: Domain Layer (5일)

### 1.1 Identity Resolution 도메인

**`domain/identity/models.py`** — MailmapEntry, IdentityCluster, BlameLineAttribution, PureContribution (Pydantic 모델)

**`domain/identity/mailmap_builder.py`** — `build_dynamic_mailmap(git_authors, github_profile, github_node_id, threshold=0.75) -> list[MailmapEntry]`
- noreply email 패턴 매칭 (확정적)
- GitHub profile name/email 교차 매칭 (확정적)
- 이름 Levenshtein distance < threshold → 클러스터링 (휴리스틱)
- 동일 커스텀 도메인 이메일 → 후보 추가 (약한 신호)

**`domain/identity/blame_filter.py`** — `filter_blame_lines(blame_lines, identity_cluster, exclude_moves=True, exclude_copies=True) -> list[BlameLineAttribution]`
- identity_cluster에 속하지 않는 author 제외
- is_move/is_copy 라인 제외
- 빈 줄/공백만 변경 제외

**`domain/identity/semantic_pruner.py`** — `prune_ast_noise(file_path, source_code, language, blame_lines) -> PureContribution`
- 제거: import, 주석, config, 자동 생성 코드, boilerplate
- 보존: 함수/클래스 본문, 제어 흐름

### 1.2 Scoring 도메인 이전

**`domain/scoring/formulas.py`** — 기존 `scoring_formulas.py` (899줄) 그대로 이전 (순수 비즈니스 로직, 변경 불필요)

### 1.3 Funnel Selection 도메인

**`domain/matching/funnel_rules.py`**:
- `stage1_hard_filter(repos, jd_languages, config)` — Fork/크기/push날짜 필터
- `stage2_relevance_score(repos, jd_requirements, jd_tech_stack)` — LLM 분석 tech_stack 기반 스코어링 (기존 `_score_repo_relevance` 공식 재활용, jd_keywords를 LLM requirements로 교체)
- `stage3_should_filter(similarity, config)` — 벡터 유사도 임계값 판정

**검증:** `pytest tests/domain/` — 외부 의존성 없는 순수 단위 테스트

---

## Phase 2: Infrastructure Layer (7일)

### 2.1 Git 어댑터

**`infrastructure/git/blame_runner.py`** — `run_git_blame(clone_dir, file_paths, mailmap_path) -> list[BlameLineAttribution]`
- `git blame -w -M -C -C --line-porcelain` 실행 + 파싱

**`infrastructure/git/clone_manager.py`** — shallow clone + `git fetch --deepen=49` (기존 패턴 유지)

**`infrastructure/git/mailmap_writer.py`** — .mailmap 파일 I/O

### 2.2 GitHub 어댑터

**`infrastructure/github/graphql_client.py`**:
- `get_user_node_id(username) -> str` — databaseId 조회 (이메일 변경에도 불변)
- `get_user_repos_graphql(username, max=20) -> list[dict]` — 레포+언어+기여도 일괄 조회 (REST 대비 80% 호출 감소)

**`infrastructure/github/rest_client.py`** — 기존 `github_service.py`에서 API 호출 부분 분리

### 2.3 정적 분석 어댑터

| 어댑터 | 파일 | 도구 | 산출 지표 |
|--------|------|------|----------|
| `tree_sitter_adapter.py` | AST 파싱 | Tree-sitter (5개 언어) | AST 구조, 시맨틱 diff, 코드 청크 |
| `radon_adapter.py` | Python 복잡도 | Radon | CC, Halstead (D/V/E), MI |
| `lizard_adapter.py` | 다중 언어 복잡도 | Lizard | CC, NLOC, Parameter Count |
| `sonarqube_adapter.py` | 종합 품질 | SonarQube API | 기술부채, 코드스멜, 중복률, 보안취약점 |
| `datasketch_adapter.py` | 표절 탐지 | Datasketch (MinHash/LSH) | 유사도 맵 |

### 2.4 LLM 어댑터

**`infrastructure/llm/instructor_client.py`** — Instructor + Pydantic 구조화 출력 (자동 검증/재시도 max 3회)

**`infrastructure/llm/cached_client.py`** — 기존 `cached_llm.py` 이전 (Redis 캐시 유지)

**`infrastructure/llm/langfuse_integration.py`** — Langfuse-first 프롬프트 로딩 유지

### 2.5 벡터 검색 확장

**`infrastructure/embedding/pgvector_store.py`** — 기존 `vector_store.py` + `compute_jd_repo_similarity()` 추가 (Funnel Stage 3용 JD-레포 README 벡터 비교)

**검증:** 각 어댑터 mock 기반 단위 테스트

---

## Phase 3: LangGraph 그래프 구축 (7일)

### 3.1 State 정의

**`application/states/meta_state.py`** — MetaState(TypedDict):
- raw_input, enriched_input, execution_plan
- forensic/logic/stack_result (Annotated[dict, merge_dicts] 병렬 merge)
- unified_profile, topics, questions, review_result
- revision_count, final_script, status, progress, errors

**`application/states/forensic_state.py`** — ForensicState:
- github_urls, candidate_username, jd_languages
- collected_repos, identity_cluster, blame_attributions
- pure_contributions, cleaned_diffs, authenticity_signals, forensic_summary

### 3.2 3계층 HMAS 그래프

**Level 1: MetaAgent** (`application/graphs/meta_graph.py`)
```
START → input_router → plan_generator → [forensic_supervisor ∥ logic_supervisor] → stack_supervisor → profile_synthesizer → question_orchestrator → quality_gate →(revise|approve)→ output_assembler → END
```
- forensic + logic 병렬, stack은 logic의 AST 결과 의존
- quality_gate: 조건부 재생성 (최대 2회 루프)

**Level 2: ForensicSupervisor** (`application/graphs/forensic_graph.py`)
```
START → collector → identity_resolver → semantic_pruner → forensic_aggregator
```
- collector: GraphQL 레포 수집 + Funnel Stage 1-3
- identity_resolver: mailmap 생성 + git blame -w -M -C
- semantic_pruner: Tree-sitter AST pruning

**Level 2: LogicSupervisor** (`application/graphs/logic_graph.py`)
```
START → [ast_analyzer ∥ complexity_meter ∥ quality_scanner] → logic_aggregator
```
- 3개 Worker 완전 병렬

**Level 2: StackSupervisor** (`application/graphs/stack_graph.py`)
```
START → [skill_extractor ∥ api_depth_analyzer ∥ architecture_evaluator] → stack_aggregator
```

### 3.3 노드 함수 원칙: thin wrapper

```python
# 노드 = domain 호출 + infrastructure 호출. 비즈니스 로직 직접 작성 금지.
async def identity_resolver_node(state: ForensicState) -> dict:
    # 1. infrastructure: git authors 추출
    authors = await git.log_parser.extract_authors(state["clone_dir"])
    # 2. domain: mailmap 생성
    mailmap = mailmap_builder.build_dynamic_mailmap(authors, state["github_profile"])
    # 3. infrastructure: git blame 실행
    blame_lines = await git.blame_runner.run_git_blame(
        state["clone_dir"], state["files"], mailmap
    )
    # 4. domain: blame 필터링
    filtered = blame_filter.filter_blame_lines(
        blame_lines, state["identity_cluster"]
    )
    return {"blame_attributions": filtered, "identity_cluster": mailmap}
```

### 3.4 FastAPI 통합

```python
# api/routes/jobs.py — Temporal client 교체
async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
    graph = build_meta_graph().compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": job_id}}
    async for event in graph.astream(input_data, config, stream_mode="updates"):
        await ws_manager.broadcast(job_id, event)  # WebSocket 실시간 전송
```

**검증:** E2E 파이프라인 테스트 (Happy Path + Partial Data + Worker Failure)

---

## Phase 4: Temporal 제거 + 정리 (3일)

- 삭제: `worker.py`, `core/temporal.py`, `core/temporal_interceptors.py`, `workflows/` 전체, `activity_logger.py`
- pyproject.toml에서 `temporalio` 제거
- Docker Compose에서 temporal/temporal-ui 완전 제거
- `services/` 에서 domain/infrastructure로 이전 완료된 파일 정리

**검증:** `pytest tests/ -x` 전체 통과, `docker compose up -d` 정상 가동

---

## Phase 5: 프론트엔드 + 출력 (별도 트랙)

- D3.js 추가 (`d3`, `@types/d3`)
- `FourAxisRadar.tsx` — 4대 지표 레이더 (논리력/전문성/안정성/진정성)
- `ComplexityTreemap.tsx` — D3.js 파일별 복잡도 드릴다운
- `AuthenticityGauge.tsx` — 진정성 게이지 (WPM + 표절률)
- `AICodeHeatmap.tsx` — 파일별 Human vs AI 생성 비율 히트맵
- `AgentProgressFlow.tsx` — HMAS 에이전트 실행 흐름 실시간 (WebSocket)
- 새 탭: Overview(3초 요약) + Code Deep Dive(신규)

---

## 선별적 마이그레이션 요약

| 판정 | 비율 | 주요 파일 |
|------|------|----------|
| **그대로 이전** | 60% | scoring_formulas.py, models/*, vector_store.py, cached_llm.py, skill_normalizer.py, knowledge_graph.py, api/*, core/*, prompts/* |
| **분리 재설계** | 30% | github_service.py → domain/identity + infrastructure/github, code_analyzer.py → infrastructure/analysis + nodes, interview_workflow.py → meta_graph.py, activities/*.py → nodes/*.py |
| **폐기** | 10% | core/temporal.py, workflows/utils.py, workflow_constants.py(Temporal부분), worker.py, activity_logger.py |

---

## 4대 지표 체계

```
최종 점수 = 0.30 x 논리력 + 0.30 x 전문성 + 0.20 x 안정성 + 0.20 x 진정성
```

| 주지표 | 세부 | 도구 |
|--------|------|------|
| 논리력 30% | CC(Radon/Lizard), Halstead D(Radon), 인지적 복잡도(SonarQube) | W7, W8 |
| 전문성 30% | API 활용 깊이(AST), 디자인 패턴(AST), SOLID(AST), 기술스택 다양성 | W9, W10, W11 |
| 안정성 20% | 기술부채(SonarQube), 코드스멜(SonarQube), Churn(PyDriller), 보안(Bandit) | W7, W8 |
| 진정성 20% | WPM(Vibector), 순수기여도(blame+pruning), 표절(Datasketch), 스타일(CLAVE) | W3, W4, W5 |

---

## Linear 티켓 구조 (25개)

설계 승인 후 생성 예정:

```
Epic: Jittda Sniper v5.0 LangGraph HMAS 마이그레이션

Phase 0 (3 tickets): Scaffolding, Docker/SonarQube, DB Migration
Phase 1 (5 tickets): Identity models, mailmap builder, blame filter, semantic pruner, funnel rules
Phase 2 (7 tickets): git adapters, GitHub GraphQL, Tree-sitter, SonarQube, Datasketch, Instructor, pgvector
Phase 3 (5 tickets): States, MetaGraph, 3 Subgraphs, FastAPI integration
Phase 4 (2 tickets): Temporal removal, cleanup
Phase 5 (3 tickets): D3.js charts, WebSocket streaming, new tabs
```

---

## Verification

1. **Domain 테스트**: `pytest tests/domain/` — 순수 단위 테스트 (외부 의존성 0)
2. **Infrastructure 테스트**: `pytest tests/infrastructure/` — mock 기반 어댑터 테스트
3. **Graph 테스트**: `pytest tests/application/` — LangGraph 통합 테스트 (Mock LLM)
4. **E2E 테스트**: Happy Path (3 repos + LinkedIn + Resume + JD), Partial Data (GitHub only), Worker Failure (SonarQube down), Quality Gate Rejection
5. **성능**: 기존 Temporal 파이프라인 대비 실행 시간 비교
6. **프론트엔드**: Playwright E2E (새 탭 + 차트 렌더링)
