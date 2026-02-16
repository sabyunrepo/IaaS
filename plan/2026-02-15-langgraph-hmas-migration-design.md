# Vantict Sniper v5.0 — LangGraph HMAS 전면 마이그레이션 설계서

> 작성일: 2026-02-15 | 상태: 설계 승인 대기

## 1. Executive Summary

현재 Temporal.io 기반 고정 4-Phase 파이프라인을 **LangGraph 기반 계층적 멀티 에이전트 시스템(HMAS)**으로 전면 교체한다. Big Bang 전략으로 일괄 전환하며, Instructor + Pydantic 구조화 출력과 Full Stack 정적 분석 도구(Tree-sitter, Radon/Lizard, SonarQube, Datasketch)를 통합한다.

### 핵심 변경점

| 영역 | AS-IS (v4.0) | TO-BE (v5.0) |
|------|-------------|-------------|
| 오케스트레이션 | Temporal.io (고정 파이프라인) | LangGraph StateGraph (동적 HMAS) |
| 에이전트 패턴 | 단일 LLM Activity | 3계층 Multi-Agent (Meta-Supervisor-Worker) |
| 데이터 전달 | plain dict (암묵적 키) | TypedDict State (타입 안전) |
| LLM 출력 | JSON 직접 파싱 | Instructor + Pydantic (자동 검증/재시도) |
| 정적 분석 | PyGithub + PyDriller만 | + Tree-sitter + Radon/Lizard + SonarQube + Datasketch |
| 벡터 검색 | pgvector 부분 사용 | 전면 RAG (코드 청크 벡터 검색) |
| 프롬프트 | Langfuse-first YAML | Langfuse-first + Few-shot + 카테고리별 특화 |
| 프론트엔드 | 순수 SVG 5축 레이더 | D3.js 레이더 + 드릴다운 트리맵 + 실시간 스트리밍 |

---

## 2. 전체 아키텍처

### 2.1 시스템 아키텍처 개요

```
                    ┌──────────────────────────────────┐
                    │         Frontend (React 19)       │
                    │  D3.js + WebSocket Streaming      │
                    └──────────────┬───────────────────┘
                                   │ REST + WebSocket
                    ┌──────────────▼───────────────────┐
                    │      FastAPI Backend (API)         │
                    │  Job CRUD + Auth + Streaming       │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │     LangGraph Runtime Engine       │
                    │  PostgreSQL Checkpointer           │
                    │  + Langfuse Tracing                │
                    └──────────────┬───────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                     │
   ┌──────────▼──────┐  ┌────────▼────────┐  ┌────────▼────────┐
   │ ForensicSuper   │  │ LogicSuper      │  │ StackSuper      │
   │ (수집/정제/진정성)│  │ (복잡도/품질)    │  │ (전문성/스택)    │
   └──────┬──────────┘  └──────┬──────────┘  └──────┬──────────┘
          │                    │                     │
    ┌─────┼─────┐        ┌────┼────┐          ┌────┼────┐
    │     │     │        │    │    │          │    │    │
   W1    W2   W3-5      W6   W7   W8        W9   W10  W11
```

### 2.2 3계층 HMAS 구조

```
Level 1: MetaAgent (총괄 오케스트레이터)
│
├── Phase 0: InputRouter
│   └── 입력 파싱 + 소스 라우팅
│
├── Phase 1: PlanGenerator
│   └── LLM 기반 실행 계획 동적 생성
│
├── Phase 2: AnalysisDispatcher (Fan-out)
│   ├── Level 2: ForensicSupervisor
│   │   ├── Level 3: CollectorWorker (GitHub/LinkedIn 수집)
│   │   ├── Level 3: CleanerWorker (노이즈 제거)
│   │   ├── Level 3: VibectorWorker (AI코드 탐지)
│   │   ├── Level 3: CLAVEWorker (스타일로메트리)
│   │   └── Level 3: DatasketchWorker (표절 탐지)
│   │
│   ├── Level 2: LogicSupervisor
│   │   ├── Level 3: ASTAnalyzerWorker (Tree-sitter)
│   │   ├── Level 3: ComplexityMeterWorker (Radon/Lizard)
│   │   └── Level 3: QualityScannerWorker (SonarQube)
│   │
│   └── Level 2: StackSupervisor
│       ├── Level 3: SkillExtractorWorker (기술스택 추출)
│       ├── Level 3: APIDepthAnalyzerWorker (API 활용 깊이)
│       └── Level 3: ArchitectureEvaluatorWorker (패턴/SOLID)
│
├── Phase 2.5: ProfileSynthesizer (Fan-in)
│   └── 모든 분석 결과 → UnifiedCandidateProfile
│
├── Phase 3: QuestionOrchestrator
│   ├── TopicSelector (벡터 검색 기반)
│   ├── QuestionCrafter x N (병렬)
│   └── EnhancementAgents x 5 (병렬)
│
├── Phase 4: QualityGate
│   ├── Reviewer (품질 검증)
│   └── Reviser (조건부 재생성, 최대 2회)
│
└── Phase 5: OutputAssembler
    ├── IntelBriefGenerator
    ├── DeepAnalysisGenerator
    ├── DecisionSupportGenerator
    └── FinalScriptAssembler
```

---

## 3. LangGraph 그래프 설계

### 3.1 MetaAgent Graph (Level 1)

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

class MetaState(TypedDict):
    # Phase 0
    raw_input: dict
    enriched_input: dict
    available_sources: list[str]  # ["github", "linkedin", "resume", "jd"]

    # Phase 1
    execution_plan: dict

    # Phase 2 (Fan-out 결과)
    forensic_result: dict
    logic_result: dict
    stack_result: dict

    # Phase 2.5
    unified_profile: dict

    # Phase 3
    selected_topics: list[dict]
    questions: list[dict]
    enhanced_questions: list[dict]

    # Phase 4
    review_result: dict
    revision_count: int  # 최대 2회

    # Phase 5
    intel_brief: dict
    deep_analysis: dict
    decision_support: dict
    final_script: dict

    # Meta
    job_id: str
    status: str
    progress: float
    errors: list[str]

# 그래프 빌드
meta_builder = StateGraph(MetaState)

# 노드 등록
meta_builder.add_node("input_router", input_router_node)
meta_builder.add_node("plan_generator", plan_generator_node)
meta_builder.add_node("forensic_supervisor", forensic_subgraph)  # Level 2 서브그래프
meta_builder.add_node("logic_supervisor", logic_subgraph)        # Level 2 서브그래프
meta_builder.add_node("stack_supervisor", stack_subgraph)        # Level 2 서브그래프
meta_builder.add_node("profile_synthesizer", profile_synthesizer_node)
meta_builder.add_node("question_orchestrator", question_subgraph) # Level 2 서브그래프
meta_builder.add_node("quality_gate", quality_gate_node)
meta_builder.add_node("output_assembler", output_assembler_node)

# 엣지
meta_builder.add_edge(START, "input_router")
meta_builder.add_edge("input_router", "plan_generator")

# Phase 2: Fan-out (3개 Supervisor 병렬)
meta_builder.add_edge("plan_generator", "forensic_supervisor")
meta_builder.add_edge("plan_generator", "logic_supervisor")
meta_builder.add_edge("plan_generator", "stack_supervisor")

# Phase 2.5: Fan-in
meta_builder.add_edge("forensic_supervisor", "profile_synthesizer")
meta_builder.add_edge("logic_supervisor", "profile_synthesizer")
meta_builder.add_edge("stack_supervisor", "profile_synthesizer")

# Phase 3-5
meta_builder.add_edge("profile_synthesizer", "question_orchestrator")
meta_builder.add_edge("question_orchestrator", "quality_gate")

# 조건부: Quality Gate → 재수정 or 완료
meta_builder.add_conditional_edges(
    "quality_gate",
    should_revise,  # revision_count < 2 && has_flagged
    {"revise": "question_orchestrator", "approve": "output_assembler"}
)
meta_builder.add_edge("output_assembler", END)

# 컴파일
DB_URI = "postgresql://postgres:postgres@postgres:5432/iaas"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    meta_graph = meta_builder.compile(checkpointer=checkpointer)
```

### 3.2 ForensicSupervisor Subgraph (Level 2)

```python
class ForensicState(TypedDict):
    github_urls: list[str]
    candidate_username: str | None
    linkedin_url: str | None

    # Worker 결과
    collected_repos: list[dict]
    cleaned_diffs: list[dict]
    vibector_scores: list[dict]   # AI 생성 의심 구간
    clave_fingerprint: dict       # 스타일로메트리
    plagiarism_report: dict       # 표절 탐지

    # 통합
    forensic_summary: dict
    authenticity_score: float     # 0.0 ~ 1.0

forensic_builder = StateGraph(ForensicState)

# Worker 노드
forensic_builder.add_node("collector", collector_worker)       # GitHub API + PyDriller
forensic_builder.add_node("cleaner", cleaner_worker)           # git-filter-repo + 노이즈 제거
forensic_builder.add_node("vibector", vibector_worker)         # WPM 타이핑 속도 분석
forensic_builder.add_node("clave", clave_worker)               # 스타일로메트리 분석
forensic_builder.add_node("datasketch", datasketch_worker)     # MinHash/LSH 표절 탐지
forensic_builder.add_node("forensic_aggregator", forensic_aggregator) # 결과 종합

# 엣지: collector → cleaner 순차, 나머지 병렬
forensic_builder.add_edge(START, "collector")
forensic_builder.add_edge("collector", "cleaner")
forensic_builder.add_edge("cleaner", "vibector")
forensic_builder.add_edge("cleaner", "clave")
forensic_builder.add_edge("cleaner", "datasketch")
forensic_builder.add_edge("vibector", "forensic_aggregator")
forensic_builder.add_edge("clave", "forensic_aggregator")
forensic_builder.add_edge("datasketch", "forensic_aggregator")

forensic_subgraph = forensic_builder.compile()
```

### 3.3 LogicSupervisor Subgraph (Level 2)

```python
class LogicState(TypedDict):
    cleaned_diffs: list[dict]      # ForensicSupervisor에서 전달
    repo_paths: list[str]

    # Worker 결과
    ast_analysis: list[dict]       # Tree-sitter AST 분석
    complexity_metrics: list[dict] # Radon/Lizard 복잡도 지표
    quality_report: dict           # SonarQube 정적 분석

    # 통합
    logic_summary: dict
    logic_score: float             # 논리력 점수

logic_builder = StateGraph(LogicState)

# Worker 노드
logic_builder.add_node("ast_analyzer", ast_analyzer_worker)       # Tree-sitter
logic_builder.add_node("complexity_meter", complexity_meter_worker) # Radon + Lizard
logic_builder.add_node("quality_scanner", quality_scanner_worker) # SonarQube API
logic_builder.add_node("logic_aggregator", logic_aggregator)

# 3개 Worker 병렬 실행
logic_builder.add_edge(START, "ast_analyzer")
logic_builder.add_edge(START, "complexity_meter")
logic_builder.add_edge(START, "quality_scanner")
logic_builder.add_edge("ast_analyzer", "logic_aggregator")
logic_builder.add_edge("complexity_meter", "logic_aggregator")
logic_builder.add_edge("quality_scanner", "logic_aggregator")

logic_subgraph = logic_builder.compile()
```

### 3.4 StackSupervisor Subgraph (Level 2)

```python
class StackState(TypedDict):
    ast_analysis: list[dict]       # LogicSupervisor에서 공유
    cleaned_diffs: list[dict]
    jd_tech_stack: list[str]

    # Worker 결과
    skill_extraction: dict         # 기술스택 + SDK/라이브러리 매핑
    api_depth_scores: list[dict]   # API 활용 깊이 점수
    architecture_eval: dict        # 디자인 패턴 + SOLID 분석

    # 통합
    stack_summary: dict
    mastery_score: float           # 전문성 점수

stack_builder = StateGraph(StackState)

stack_builder.add_node("skill_extractor", skill_extractor_worker)
stack_builder.add_node("api_depth_analyzer", api_depth_analyzer_worker)
stack_builder.add_node("architecture_evaluator", architecture_evaluator_worker)
stack_builder.add_node("stack_aggregator", stack_aggregator)

# 병렬 실행
stack_builder.add_edge(START, "skill_extractor")
stack_builder.add_edge(START, "api_depth_analyzer")
stack_builder.add_edge(START, "architecture_evaluator")
stack_builder.add_edge("skill_extractor", "stack_aggregator")
stack_builder.add_edge("api_depth_analyzer", "stack_aggregator")
stack_builder.add_edge("architecture_evaluator", "stack_aggregator")

stack_subgraph = stack_builder.compile()
```

---

## 4. Worker Agent 상세 설계

### 4.1 Worker 에이전트 총괄표

| # | Worker | Supervisor | 도구 | 입력 | 출력 | LLM |
|---|--------|------------|------|------|------|-----|
| W1 | CollectorWorker | Forensic | PyGithub, GraphQL, PyDriller, BrightData | github_urls, linkedin_url | collected_repos, raw_diffs | X |
| W2 | CleanerWorker | Forensic | git-filter-repo, Regex, AST filter | raw_diffs | cleaned_diffs (보일러플레이트/바이너리 제거) | X |
| W3 | VibectorWorker | Forensic | Git log analysis, WPM calculator | cleaned_diffs, commit_timestamps | vibector_scores (AI 의심 구간) | X |
| W4 | CLAVEWorker | Forensic | Stylometry analyzer | cleaned_diffs | clave_fingerprint (저자 지문) | O |
| W5 | DatasketchWorker | Forensic | Datasketch (MinHash/LSH) | cleaned_diffs, FOSS corpus | plagiarism_report (유사도 맵) | X |
| W6 | ASTAnalyzerWorker | Logic | Tree-sitter, language grammars | cleaned_diffs, repo_files | ast_analysis (AST 구조, 시맨틱 diff) | X |
| W7 | ComplexityMeterWorker | Logic | Radon, Lizard, cloc | repo_files | complexity_metrics (CC, Halstead, MI) | X |
| W8 | QualityScannerWorker | Logic | SonarQube API, Bandit | repo_url (SonarQube project) | quality_report (부채, 스멜, 취약점) | X |
| W9 | SkillExtractorWorker | Stack | Tree-sitter, import parser | ast_analysis, jd_tech_stack | skill_extraction (기술 매핑) | O |
| W10 | APIDepthAnalyzerWorker | Stack | AST call graph, API usage scorer | ast_analysis | api_depth_scores (API 활용 깊이) | O |
| W11 | ArchitectureEvaluatorWorker | Stack | AST pattern detector | ast_analysis | architecture_eval (패턴/SOLID) | O |

### 4.2 Worker 구현 패턴 (Strategy Pattern)

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Generic, TypeVar

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)

class BaseWorker(ABC, Generic[TInput, TOutput]):
    """모든 Worker의 기본 클래스 (Template Method Pattern)"""

    @abstractmethod
    def validate_input(self, input_data: TInput) -> bool:
        """입력 데이터 검증"""
        ...

    @abstractmethod
    def execute(self, input_data: TInput) -> TOutput:
        """핵심 분석 로직"""
        ...

    @abstractmethod
    def handle_error(self, error: Exception, input_data: TInput) -> TOutput:
        """에러 시 Graceful Degradation"""
        ...

    async def run(self, state: dict) -> dict:
        """LangGraph 노드로 실행 (Template Method)"""
        input_data = self.parse_input(state)

        if not self.validate_input(input_data):
            return self.empty_result()

        try:
            result = await self.execute(input_data)
            return self.format_output(result)
        except Exception as e:
            return self.format_output(self.handle_error(e, input_data))


# Strategy Pattern: 언어별 분석 도구 선택
class AnalysisStrategy(ABC):
    @abstractmethod
    def analyze_complexity(self, file_path: str) -> dict: ...

    @abstractmethod
    def parse_ast(self, code: str) -> dict: ...

class PythonAnalysis(AnalysisStrategy):
    def analyze_complexity(self, file_path):
        # Radon CC + Halstead
        ...
    def parse_ast(self, code):
        # Tree-sitter python grammar
        ...

class JavaScriptAnalysis(AnalysisStrategy):
    def analyze_complexity(self, file_path):
        # Lizard + Esprima
        ...
    def parse_ast(self, code):
        # Tree-sitter javascript grammar
        ...

# Factory Pattern: 언어별 Strategy 생성
class AnalysisStrategyFactory:
    _strategies = {
        "python": PythonAnalysis,
        "javascript": JavaScriptAnalysis,
        "typescript": JavaScriptAnalysis,
        "java": JavaAnalysis,
        "go": GoAnalysis,
    }

    @classmethod
    def create(cls, language: str) -> AnalysisStrategy:
        strategy_cls = cls._strategies.get(language)
        if not strategy_cls:
            return GenericAnalysis()
        return strategy_cls()
```

### 4.3 각 Worker 상세

#### W1: CollectorWorker (데이터 수집)

```
입력: github_urls, linkedin_url, candidate_username
도구: PyGithub, GitHub GraphQL API, PyDriller, BrightData API
처리:
  1. GraphQL로 사용자 정보 + Org + 레포 한 번에 조회 (REST 대비 호출 80% 감소)
  2. Fork/Mirror 레포 필터링
  3. PyDriller로 커밋 히스토리 + diff 추출
  4. BrightData로 LinkedIn 프로필 스크레이핑
  5. 이력서/포트폴리오 PDF 텍스트 추출
출력: collected_repos[], raw_diffs[], linkedin_profile, documents[]
```

#### W6: ASTAnalyzerWorker (AST 구조 분석)

```
입력: cleaned_diffs[], repo_files
도구: Tree-sitter (multi-language), diffsitter
처리:
  1. Tree-sitter로 코드를 AST로 변환
  2. 시맨틱 diff 추출 (포맷팅 변경 무시)
  3. 함수/클래스 경계 기준 코드 청크 분할
  4. 각 청크를 pgvector에 임베딩 저장 (RAG용)
  5. import/export 그래프 구축
출력: ast_trees[], semantic_diffs[], code_chunks[], import_graph
```

#### W7: ComplexityMeterWorker (복잡도 측정)

```
입력: repo_files (소스 파일 경로들)
도구: Radon (Python), Lizard (multi-lang), cloc
처리:
  1. cloc로 언어별 LOC 통계
  2. Radon CC: 함수별 순환 복잡도 (M = E - N + 2P)
  3. Radon Halstead: 난이도(D), 볼륨(V), 노력(E)
  4. Lizard: 다중 언어 CC + NLOC + Parameter Count
  5. 유지보수 지수(MI) 계산
출력: {
  per_function: [{name, cc, halstead_d, halstead_v, nloc, params}],
  per_file: [{path, avg_cc, max_cc, mi_score, loc}],
  summary: {total_loc, avg_cc, median_cc, p90_cc, mi_avg}
}
```

#### W8: QualityScannerWorker (SonarQube 정적 분석)

```
입력: repo_url 또는 로컬 소스 경로
도구: SonarQube API, Bandit (Python 보안)
처리:
  1. sonar-scanner로 프로젝트 분석 실행
  2. SonarQube API로 결과 조회:
     - 기술 부채 (SQALE debt)
     - 코드 스멜 수/심각도
     - 중복 코드 비율 (CPD)
     - 보안 취약점 (Security Hotspots)
     - 인지적 복잡도 (Cognitive Complexity)
  3. Bandit (Python 전용): 보안 안티패턴 탐지
출력: {
  tech_debt_hours: float,
  code_smells: [{rule, severity, file, line}],
  duplication_pct: float,
  vulnerabilities: [{type, severity, file}],
  reliability_rating: str,  # A-E
  security_rating: str,     # A-E
  maintainability_rating: str
}
```

---

## 5. Pydantic 모델 + Instructor 통합

### 5.1 구조화 출력 모델

```python
import instructor
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

# Instructor 클라이언트 초기화
client = instructor.from_openai(AsyncOpenAI())

# --- 분석 결과 모델 ---

class ComplexityMetrics(BaseModel):
    cyclomatic_complexity: float = Field(ge=0, description="McCabe 순환 복잡도 평균")
    halstead_difficulty: float = Field(ge=0, description="Halstead 난이도")
    halstead_volume: float = Field(ge=0, description="Halstead 볼륨")
    maintainability_index: float = Field(ge=0, le=100, description="유지보수 지수")
    cognitive_complexity: float = Field(ge=0, description="인지적 복잡도")

class AuthenticityScore(BaseModel):
    human_typing_ratio: float = Field(ge=0, le=1, description="인간 타이핑 속도 준수 비율")
    originality_ratio: float = Field(ge=0, le=1, description="순수 기여도 비율")
    ai_code_suspicion: float = Field(ge=0, le=1, description="AI 생성 코드 의심도")
    plagiarism_ratio: float = Field(ge=0, le=1, description="표절/복사 비율")
    style_consistency: float = Field(ge=0, le=1, description="코딩 스타일 일관성")

class SkillAssessment(BaseModel):
    skill_name: str
    proficiency: str = Field(description="beginner|intermediate|advanced|expert")
    evidence_count: int = Field(ge=0)
    evidence_sources: list[str]  # ["github:repo1", "linkedin", "resume"]
    confidence: str  # "high" | "medium" | "low"

# --- 질문 생성 모델 ---

class InterviewQuestion(BaseModel):
    """Instructor로 LLM이 직접 생성하는 구조화된 면접 질문"""
    question_id: str
    category: str  # technical_depth | execution_ownership | communication | role_fit | risk_flags
    difficulty: str  # easy | medium | hard
    question_text: str = Field(min_length=20, max_length=500)
    intent: str = Field(description="이 질문의 의도 (비개발자용)")
    code_reference: str | None = Field(description="관련 코드 파일:라인")
    expected_answer_guide: str = Field(description="비개발자도 이해 가능한 예상 답변 가이드")
    red_flags: list[str] = Field(description="주의해야 할 답변 패턴")
    follow_up_triggers: list[str] = Field(description="파생 질문 트리거 조건")
    terminology: list[dict] = Field(description="질문에 포함된 전문 용어 설명")

# --- Instructor 호출 예시 ---

async def generate_question(topic: dict, context: dict) -> InterviewQuestion:
    return await client.chat.completions.create(
        model="kimi-k2.5",
        response_model=InterviewQuestion,
        messages=[
            {"role": "system", "content": QUESTION_CRAFT_SYSTEM_PROMPT},
            {"role": "user", "content": format_question_prompt(topic, context)}
        ],
        max_retries=3,  # Pydantic 검증 실패 시 자동 재시도
    )
```

### 5.2 Langfuse-First + Instructor 통합

```python
from langfuse import Langfuse
from langfuse.decorators import observe

langfuse = Langfuse()

@observe(name="generate_interview_question")
async def generate_question_with_tracing(topic, context):
    """Langfuse 추적 + Instructor 구조화 출력"""
    # 1. Langfuse에서 프롬프트 가져오기
    prompt = langfuse.get_prompt("question_craft_v5", label="production")

    # 2. Instructor로 구조화 출력 생성
    result = await client.chat.completions.create(
        model=prompt.config.get("model", "kimi-k2.5"),
        response_model=InterviewQuestion,
        messages=prompt.compile(topic=topic, context=context),
        temperature=prompt.config.get("temperature", 0.7),
        max_retries=3,
    )

    return result
```

---

## 6. 벡터 검색 (RAG) 전략

### 6.1 임베딩 파이프라인

```
코드 파일 → Tree-sitter AST → 함수/클래스 단위 청크 분할
                                       │
                                       ▼
                              임베딩 모델 (text-embedding-3-small)
                                       │
                                       ▼
                              pgvector 저장 (Vector(1536))
                                       │
                              ┌────────┼────────┐
                              │        │        │
                          kind: code  kind: jd  kind: resume
```

### 6.2 청크 전략

| 소스 | 청크 단위 | 메타데이터 |
|------|----------|-----------|
| 코드 | 함수/클래스 (AST 기반) | file_path, language, complexity, author |
| JD | 섹션별 (자격요건, 우대사항 등) | section_type, keywords |
| 이력서 | 경력/프로젝트별 | company, role, duration |
| LinkedIn | 프로필 섹션별 | section_type |

### 6.3 질문 생성 시 벡터 검색 활용

```python
async def select_relevant_context(topic: dict, job_id: str) -> list[dict]:
    """토픽과 관련된 코드 청크만 벡터 검색으로 선별"""
    query = f"{topic['skill']} {topic['context']} {topic['question_angle']}"

    # pgvector 유사도 검색
    chunks = await embedding_store.similarity_search(
        query=query,
        job_id=job_id,
        kind="code",
        top_k=5,
        min_similarity=0.7,
    )

    return chunks  # 전체 코드 대신 관련 청크 5개만 → LLM 입력 90% 축소
```

### 6.4 컨텍스트 예산 관리

```python
class ContextBudget:
    """LLM 입력 컨텍스트 예산 관리자"""
    MAX_TOKENS = 8000  # 질문 생성 시 최대 입력 토큰

    ALLOCATION = {
        "system_prompt": 1500,     # 시스템 프롬프트 + Few-shot
        "jd_context": 1500,        # JD 핵심 요구사항
        "code_chunks": 3000,       # 벡터 검색된 코드 청크
        "candidate_profile": 1000, # 통합 프로필 요약
        "topic_context": 1000,     # 토픽 관련 컨텍스트
    }

    def allocate(self, section: str, content: str) -> str:
        """토큰 예산 내에서 컨텐츠 트림"""
        max_tokens = self.ALLOCATION[section]
        return truncate_to_tokens(content, max_tokens)
```

---

## 7. 프롬프트 엔지니어링

### 7.1 프롬프트 전략

| 전략 | 적용 대상 | 설명 |
|------|----------|------|
| Few-shot | 질문 생성, 디자인 패턴 탐지 | 2-3개 예시로 출력 형식/품질 가이드 |
| Chain-of-Thought | 복잡도 해석, 결정 생성 | 단계별 추론 유도 |
| Fact-Grounded | 모든 판단 프롬프트 | "결정론적 수치를 참조하여" 전제 |
| Negative Prompting | 질문 생성 | "일반적/교과서적 질문은 제외" |

### 7.2 질문 생성 3전략 프롬프트

```yaml
# question_craft_negative_selection.yaml (전략 A)
system: |
  당신은 코드 기반 기술 면접 질문 전문가입니다.

  ## 전략: Negative Selection (안 한 이유 묻기)
  후보자의 코드에서 사용될 법하지만 사용되지 않은 패턴/기술을 발견하고,
  "왜 A 대신 B를 선택했는지" 의도를 탐색하는 질문을 생성합니다.

  ## 규칙
  1. 반드시 정량적 분석 데이터를 근거로 질문 생성
  2. 비개발자가 이해 가능한 용어 설명 포함
  3. 회피형 답변 대응 파생 질문 1-2개 포함

  ## Few-shot 예시

  ### 예시 1:
  분석 데이터: "candidate는 React 프로젝트에서 Context API만 사용,
  Redux/Zustand 미사용. 컴포넌트 트리 깊이 4단계."

  질문: "프로젝트에서 상태 관리를 Context API로 구현하셨는데,
  컴포넌트 트리가 4단계까지 있습니다. Redux나 Zustand 같은
  전역 상태 관리 도구를 고려하지 않은 특별한 이유가 있으셨나요?"

  의도: "Context API를 선택한 판단의 근거를 확인하여,
  도구 선택에 대한 기술적 사고 깊이를 평가"

  ### 예시 2:
  분석 데이터: "Python 프로젝트에서 asyncio 미사용,
  동기 requests 라이브러리로 외부 API 5곳 호출. 응답 대기 시간 평균 2초."

  질문: "외부 API를 동기 방식으로 호출하고 계시는데,
  비동기 처리를 적용하지 않은 이유가 궁금합니다.
  성능 관련 고민은 있으셨나요?"

user: |
  ## 분석 데이터
  {{analysis_data}}

  ## 후보자 프로필 요약
  {{candidate_profile_summary}}

  ## JD 요구사항
  {{jd_requirements}}

  ## 관련 코드 청크 (벡터 검색 결과)
  {{relevant_code_chunks}}

  위 데이터를 기반으로 Negative Selection 전략의 면접 질문을 생성하세요.
```

### 7.3 프롬프트 관리 흐름

```
Langfuse UI에서 프롬프트 편집/버전 관리
         │
         ▼
    get_prompt("question_craft_v5")
         │
         ▼ (Langfuse 장애 시)
    YAML fallback (로컬 파일)
         │
         ▼
    Instructor + Pydantic 검증
         │
         ▼ (검증 실패 시)
    자동 재시도 (최대 3회, 에러 메시지 포함)
```

---

## 8. 디자인 패턴 적용

### 8.1 적용 패턴 총괄

| 패턴 | 적용 위치 | 목적 |
|------|----------|------|
| **Strategy** | Worker 내 언어별 분석 도구 선택 | 하드코딩 없이 언어별 분석 로직 분리 |
| **Factory** | WorkerFactory, AnalysisStrategyFactory | Worker/Strategy 객체 생성 추상화 |
| **Template Method** | BaseWorker.run() | Worker 공통 실행 흐름 통일 |
| **Observer** | 에이전트 간 이벤트/진행률 알림 | 느슨한 결합 유지 |
| **Chain of Responsibility** | Quality Gate (Review → Revise → Re-review) | 품질 검증 체인 |
| **Composite** | HMAS 3계층 (MetaGraph → SubGraph → Node) | 계층 구조 일관된 인터페이스 |
| **Adapter** | SonarQube API, Langfuse API 래퍼 | 외부 서비스 통합 추상화 |
| **Builder** | ContextBudget, PromptBuilder | 복잡한 객체 단계적 조립 |

### 8.2 Observer Pattern: 에이전트 간 이벤트

```python
from typing import Protocol, Callable

class AgentEvent(BaseModel):
    agent_name: str
    event_type: str  # "started" | "progress" | "completed" | "failed"
    data: dict
    timestamp: datetime

class EventBus:
    """에이전트 간 이벤트 버스 (Observer Pattern)"""
    _subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        self._subscribers.setdefault(event_type, []).append(handler)

    async def publish(self, event: AgentEvent):
        for handler in self._subscribers.get(event.event_type, []):
            await handler(event)

# 사용 예
event_bus = EventBus()

# Supervisor가 Worker 진행률 구독
event_bus.subscribe("progress", forensic_supervisor.on_worker_progress)

# Worker가 완료 이벤트 발행
await event_bus.publish(AgentEvent(
    agent_name="collector_worker",
    event_type="completed",
    data={"repos_collected": 5, "diffs_extracted": 150}
))
```

---

## 9. 인프라 변경 계획

### 9.1 Docker Compose 변경

```yaml
# 제거되는 서비스
# - temporal (LangGraph Checkpointer로 대체)
# - temporal-ui (LangGraph Studio 또는 Langfuse로 대체)
# - worker (LangGraph 런타임이 FastAPI 내에서 실행)

# 추가되는 서비스
services:
  sonarqube:
    image: sonarqube:community
    ports:
      - "9000:9000"
    environment:
      - SONAR_JDBC_URL=jdbc:postgresql://postgres:5432/sonarqube
      - SONAR_JDBC_USERNAME=postgres
      - SONAR_JDBC_PASSWORD=postgres
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/api/system/status"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - iaas_internal

  sonar-scanner:
    image: sonarsource/sonar-scanner-cli:latest
    profiles: ["analysis"]  # 분석 시에만 실행
    depends_on:
      sonarqube:
        condition: service_healthy
    networks:
      - iaas_internal

# 수정되는 서비스
  backend:
    # Temporal 의존성 제거
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      phoenix:
        condition: service_started
      sonarqube:
        condition: service_healthy
    environment:
      # Temporal 환경변수 제거
      # - TEMPORAL_HOST=temporal:7233  # 삭제
      # LangGraph 관련 추가
      - LANGGRAPH_CHECKPOINTER_URI=postgresql://postgres:postgres@postgres:5432/iaas
      - SONARQUBE_URL=http://sonarqube:9000
      - SONARQUBE_TOKEN=${SONARQUBE_TOKEN}

# 제거되는 볼륨
# - temporal_data (불필요)

# 추가되는 볼륨
volumes:
  sonarqube_data:
  sonarqube_extensions:
```

### 9.2 새 DB 마이그레이션

```sql
-- 004_remove_temporal_add_langgraph.py

-- 1. LangGraph 체크포인트 테이블 (PostgresSaver가 자동 생성하나 명시적 정의)
-- PostgresSaver.setup()이 자동으로 생성하므로 별도 마이그레이션 불필요

-- 2. 분석 결과 테이블 (Worker 결과 저장)
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    worker_name VARCHAR(50) NOT NULL,
    supervisor_name VARCHAR(30) NOT NULL,
    result_data JSONB NOT NULL,
    metrics JSONB,  -- 수치 지표 (빠른 조회용)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analysis_results_job ON analysis_results(job_id);
CREATE INDEX idx_analysis_results_worker ON analysis_results(worker_name);

-- 3. 4대 지표 테이블
CREATE TABLE candidate_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    logic_score FLOAT NOT NULL,       -- 논리력 (30%)
    mastery_score FLOAT NOT NULL,     -- 전문성 (30%)
    stability_score FLOAT NOT NULL,   -- 안정성 (20%)
    authenticity_score FLOAT NOT NULL, -- 진정성 (20%)
    weighted_total FLOAT NOT NULL,    -- 가중 합산
    details JSONB,                    -- 세부 내역
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id)
);

-- 4. jobs 테이블 수정
ALTER TABLE jobs DROP COLUMN IF EXISTS temporal_workflow_id;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS langgraph_thread_id VARCHAR(100);
CREATE INDEX idx_jobs_thread ON jobs(langgraph_thread_id);

-- 5. SonarQube 프로젝트 매핑
CREATE TABLE sonarqube_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    project_key VARCHAR(200) NOT NULL,
    repo_url TEXT,
    scan_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 9.3 Python 의존성 변경

```diff
# requirements.txt 또는 pyproject.toml

# 제거
- temporalio==1.5.0
- temporalio[opentelemetry]

# 추가
+ langgraph==1.0.6
+ langgraph-checkpoint-postgres==2.0.0
+ instructor==1.5.0
+ tree-sitter==0.24.0
+ tree-sitter-python==0.23.0
+ tree-sitter-javascript==0.23.0
+ tree-sitter-typescript==0.23.0
+ tree-sitter-java==0.23.0
+ tree-sitter-go==0.23.0
+ radon==6.0.1
+ lizard==1.17.10
+ datasketch==1.6.5
+ cloc  # system package (apt/brew)
+ bandit==1.8.0
+ pydeps==1.12.0
```

---

## 10. 프론트엔드 변경 계획

### 10.1 새로운 시각화 요소

```
현재: 순수 SVG 5축 레이더 (React.memo)
변경: D3.js 기반 고급 시각화

추가 컴포넌트:
├── charts/
│   ├── FourAxisRadar.tsx         # 4대 지표 레이더 (논리력/전문성/안정성/진정성)
│   ├── ComplexityTreemap.tsx     # D3.js 드릴다운 트리맵 (파일별 복잡도)
│   ├── AuthenticityGauge.tsx     # 진정성 게이지 (WPM + 표절률)
│   ├── SkillHeatmap.tsx          # 기술스택 히트맵 (JD 매칭)
│   ├── CommitTimeline.tsx        # Git 커밋 타임라인 (PyDriller 데이터)
│   └── AgentProgressFlow.tsx     # HMAS 에이전트 실행 흐름 실시간
```

### 10.2 실시간 스트리밍 (LangGraph → WebSocket)

```typescript
// hooks/useLangGraphStream.ts
export function useLangGraphStream(jobId: string) {
  const [agentStates, setAgentStates] = useState<AgentState[]>([]);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/jobs/${jobId}/stream`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'agent_started':
          setAgentStates(prev => [...prev, { name: data.agent, status: 'running' }]);
          break;
        case 'agent_completed':
          setAgentStates(prev => prev.map(a =>
            a.name === data.agent ? { ...a, status: 'completed', result: data.result } : a
          ));
          break;
        case 'progress':
          setProgress(data.progress);
          break;
        case 'metric_update':
          // 실시간 지표 업데이트 (레이더 차트 점진적 렌더링)
          break;
      }
    };

    return () => ws.close();
  }, [jobId]);

  return { agentStates, progress };
}
```

### 10.3 새 탭 구조

```
ResultPage 탭 (변경 후):
├── Tab 1: Overview (3초 요약)
│   └── 4대 지표 신호등 카드 + 가중 합산 점수
├── Tab 2: Intel Brief (기존 유지 + 강화)
│   └── + 진정성 검증 섹션 추가
├── Tab 3: Code Deep Dive (신규)
│   ├── 복잡도 트리맵 (D3.js)
│   ├── 기술스택 히트맵
│   └── 커밋 타임라인
├── Tab 4: Interview (기존 유지 + 강화)
│   └── + 3전략별 질문 그룹핑 (Negative/Complexity/Evolution)
└── Tab 5: Decision (기존 유지 + 강화)
    └── + 4대 지표 기반 종합 판단 근거
```

### 10.4 프론트엔드 의존성 추가

```diff
# package.json
+ "d3": "^7.9.0",
+ "@types/d3": "^7.4.3",
```

---

## 11. 4대 핵심 지표 체계

### 11.1 점수 산출 공식

```
최종 점수 = W1 * 논리력 + W2 * 전문성 + W3 * 안정성 + W4 * 진정성
         = 0.30 * Logic + 0.30 * Mastery + 0.20 * Stability + 0.20 * Authenticity
```

### 11.2 각 지표 세부 구성

| 주지표 | 세부 지표 | 산출 도구 | 가중치 |
|--------|----------|----------|--------|
| **논리력 (30%)** | 순환 복잡도 (CC) | Radon/Lizard | 40% |
| | 할스테드 난이도 (D) | Radon | 30% |
| | 인지적 복잡도 | SonarQube | 30% |
| **전문성 (30%)** | API 활용 깊이 | AST 분석 | 35% |
| | 디자인 패턴 사용 | AST 패턴 감지 | 25% |
| | SOLID 준수율 | 아키텍처 분석 | 20% |
| | 기술스택 다양성 | 스킬 추출 | 20% |
| **안정성 (20%)** | 기술 부채 비율 | SonarQube | 35% |
| | 코드 스멜 밀도 | SonarQube | 25% |
| | 리워크 비율 (Churn) | PyDriller | 20% |
| | 보안 취약점 밀도 | SonarQube + Bandit | 20% |
| **진정성 (20%)** | 인간 타이핑 속도 | Vibector (WPM) | 30% |
| | 순수 기여도 | PyDriller + git-filter-repo | 30% |
| | 표절/복사 비율 | Datasketch (LSH) | 20% |
| | 스타일 일관성 | CLAVE | 20% |

### 11.3 신뢰도 표시 체계

| 신뢰도 | 조건 | 표시 |
|--------|------|------|
| 높음 | 데이터 소스 3개 이상 + 공개 레포 5개 이상 | 초록색 |
| 중간 | 데이터 소스 2개 + 공개 레포 2-4개 | 노란색 |
| 낮음 | 데이터 소스 1개 또는 공개 레포 1개 이하 | 빨간색 |

---

## 12. 에이전트 간 데이터 흐름 상세

### 12.1 Phase 간 State 전파

```
Phase 0 (InputRouter)
│ 출력: enriched_input, available_sources
│
▼
Phase 1 (PlanGenerator)
│ 입력: enriched_input
│ 출력: execution_plan (어떤 Worker를 활성화할지 동적 결정)
│
▼ (Fan-out: 3개 Supervisor 병렬)
Phase 2a (ForensicSupervisor)        Phase 2b (LogicSupervisor)      Phase 2c (StackSupervisor)
│ 입력: github_urls, linkedin_url    │ 입력: cleaned_diffs           │ 입력: ast_analysis
│ 출력: forensic_result              │ 출력: logic_result            │ 출력: stack_result
│   ├── authenticity_score           │   ├── logic_score             │   ├── mastery_score
│   ├── cleaned_diffs                │   ├── complexity_metrics      │   ├── skill_assessment
│   └── plagiarism_report            │   └── quality_report          │   └── architecture_eval
│
▼ (Fan-in: Profile 통합)
Phase 2.5 (ProfileSynthesizer)
│ 입력: forensic_result + logic_result + stack_result + enriched_input
│ 출력: unified_profile, candidate_scores
│
▼
Phase 3 (QuestionOrchestrator)
│ 입력: unified_profile + candidate_scores + execution_plan
│ 처리:
│   1. 벡터 검색으로 관련 코드 청크 선별
│   2. 3전략 (Negative/Complexity/Evolution) 질문 생성
│   3. 5개 Enhancement Agent 병렬 실행
│ 출력: enhanced_questions[]
│
▼
Phase 4 (QualityGate)
│ 입력: enhanced_questions
│ 처리: 품질 검증 → 조건부 재생성 (최대 2회 루프)
│ 출력: approved_questions[]
│
▼
Phase 5 (OutputAssembler)
│ 입력: approved_questions + unified_profile + candidate_scores
│ 출력: final_script (IntelBrief + DeepAnalysis + DecisionSupport + Questions)
```

### 12.2 Supervisor 내부 Worker 의존성

```
ForensicSupervisor:
  Collector → Cleaner → [Vibector, CLAVE, Datasketch] (병렬) → Aggregator

LogicSupervisor:
  [ASTAnalyzer, ComplexityMeter, QualityScanner] (병렬) → Aggregator

StackSupervisor:
  (AST 결과 필요) → [SkillExtractor, APIDepthAnalyzer, ArchitectureEvaluator] (병렬) → Aggregator
```

**주의**: StackSupervisor는 LogicSupervisor의 AST 분석 결과에 의존. 따라서 MetaGraph에서:
- ForensicSupervisor와 LogicSupervisor는 병렬 실행
- StackSupervisor는 LogicSupervisor 완료 후 실행 (또는 AST 결과만 부분 전달)

수정된 엣지:
```python
meta_builder.add_edge("plan_generator", "forensic_supervisor")
meta_builder.add_edge("plan_generator", "logic_supervisor")
# StackSupervisor는 LogicSupervisor의 AST 결과 필요
meta_builder.add_edge("logic_supervisor", "stack_supervisor")
# ForensicSupervisor와 StackSupervisor가 완료되면 Fan-in
meta_builder.add_edge("forensic_supervisor", "profile_synthesizer")
meta_builder.add_edge("stack_supervisor", "profile_synthesizer")
```

---

## 13. 기존 코드 유지/재활용 목록

### 13.1 유지 (그대로)

| 모듈 | 이유 |
|------|------|
| `CachedLLMService` | Redis 캐시 레이어 그대로 유지 (Instructor와 호환) |
| `get_prompt_with_config()` | Langfuse-first 패턴 유지 |
| Pydantic 모델 (`models/`) | 확장하여 사용 (v5 필드 추가) |
| DB 스키마 (users, jobs, embeddings) | 마이그레이션으로 확장 |
| 프론트엔드 인증 흐름 | 변경 불필요 |
| API 엔드포인트 (`/jobs`, `/auth`) | WebSocket 스트리밍만 추가 |

### 13.2 수정 (리팩토링)

| 모듈 | 변경 내용 |
|------|----------|
| `interview_workflow.py` → `meta_graph.py` | Temporal → LangGraph StateGraph |
| `workflow_code_analysis.py` → `supervisors/forensic.py` | Activity → Subgraph |
| Activity 파일들 → Worker 클래스들 | `@activity.defn` → `BaseWorker` 상속 |
| `utils.py` (heartbeat) | Temporal heartbeat → LangGraph streaming |

### 13.3 제거

| 모듈 | 이유 |
|------|------|
| `workflow_constants.py` (Temporal retry policies) | LangGraph 재시도로 대체 |
| Temporal worker 설정 | 불필요 |
| `docker-compose.yml`의 temporal/temporal-ui 서비스 | 제거 |

---

## 14. 테스트 전략

### 14.1 테스트 계층

| 레벨 | 대상 | 도구 | 커버리지 목표 |
|------|------|------|-------------|
| Unit | Worker 개별 로직 | pytest + pytest-asyncio | 80% |
| Integration | Subgraph 내 Worker 연동 | pytest + PostgreSQL testcontainer | 70% |
| E2E | MetaGraph 전체 파이프라인 | pytest + Mock LLM | 60% |
| Visual | 프론트엔드 차트/UI | Playwright | 주요 페이지 |
| Performance | Worker 병렬 실행 시간 | pytest-benchmark | 기준선 대비 |

### 14.2 테스트 시나리오

```
1. Happy Path: 모든 데이터 소스 사용 가능
   - GitHub 3 repos + LinkedIn + Resume + JD
   - 예상: 모든 Worker 실행 → 4대 지표 산출 → 20개 질문 생성

2. Partial Data: GitHub만 사용 가능
   - GitHub 1 repo + JD (LinkedIn/Resume 없음)
   - 예상: Forensic + Logic + Stack 실행, 신뢰도 "낮음"

3. Quality Gate Rejection: 질문 품질 미달
   - 강제 저품질 질문 주입
   - 예상: Reviewer → Reviser → Re-review (최대 2회)

4. Worker Failure: SonarQube 서비스 다운
   - SonarQube 연결 불가
   - 예상: QualityScanner Graceful Degradation, 나머지 Worker 정상

5. Concurrent: 3개 Job 동시 실행
   - 예상: LangGraph thread_id로 격리, 교차 오염 없음
```

---

## 15. 마이그레이션 단계 (Big Bang)

### Phase 1: 인프라 준비 (1-2주)

```
1.1 Docker Compose 수정 (Temporal 제거, SonarQube 추가)
1.2 Python 의존성 업데이트 (langgraph, instructor, tree-sitter 등)
1.3 DB 마이그레이션 스크립트 작성 (004)
1.4 SonarQube 초기 설정 + Quality Profile
1.5 Tree-sitter 언어 그래머 설치 검증
```

### Phase 2: Worker 구현 (2-3주)

```
2.1 BaseWorker 추상 클래스 + Strategy/Factory 패턴
2.2 ForensicSupervisor Workers (W1-W5)
    - CollectorWorker (기존 input_enrichment + code_analysis 수집 부분 리팩토링)
    - CleanerWorker (기존 code_analysis 전처리 부분)
    - VibectorWorker (신규)
    - CLAVEWorker (신규)
    - DatasketchWorker (신규)
2.3 LogicSupervisor Workers (W6-W8)
    - ASTAnalyzerWorker (신규 - Tree-sitter)
    - ComplexityMeterWorker (신규 - Radon/Lizard)
    - QualityScannerWorker (신규 - SonarQube API)
2.4 StackSupervisor Workers (W9-W11)
    - SkillExtractorWorker (기존 profile_builder 일부)
    - APIDepthAnalyzerWorker (신규)
    - ArchitectureEvaluatorWorker (신규)
```

### Phase 3: Graph 조립 (1-2주)

```
3.1 Level 2: ForensicSupervisor Subgraph
3.2 Level 2: LogicSupervisor Subgraph
3.3 Level 2: StackSupervisor Subgraph
3.4 Level 1: MetaAgent Graph (전체 연결)
3.5 PostgreSQL Checkpointer 통합
3.6 Instructor + Pydantic 구조화 출력 통합
```

### Phase 4: 질문 생성 + Enhancement (1-2주)

```
4.1 벡터 검색 기반 TopicSelector
4.2 3전략 QuestionCrafter (Negative/Complexity/Evolution)
4.3 Enhancement Agents 5개 (기존 리팩토링)
4.4 QualityGate (Reviewer + Reviser 루프)
4.5 Few-shot 프롬프트 작성 + Langfuse 업로드
```

### Phase 5: 출력 + 프론트엔드 (1-2주)

```
5.1 OutputAssembler (IntelBrief + DeepAnalysis + DecisionSupport)
5.2 4대 지표 산출 + candidate_scores 테이블
5.3 WebSocket 스트리밍 (LangGraph → Frontend)
5.4 D3.js 차트 컴포넌트 (FourAxisRadar, ComplexityTreemap)
5.5 새 탭 구조 (Overview, Code Deep Dive)
```

### Phase 6: 통합 테스트 + 정리 (1주)

```
6.1 E2E 테스트 (Happy Path + Edge Cases)
6.2 Temporal 코드 완전 제거
6.3 성능 벤치마크 (기존 대비)
6.4 Langfuse 대시보드 설정
6.5 문서화 (아키텍처 다이어그램 업데이트)
```

---

## 16. 리스크 및 완화 전략

| 리스크 | 영향 | 완화 |
|--------|------|------|
| SonarQube Docker 메모리 요구 (2GB+) | 로컬 개발 환경 부담 | 최소 설정 + 분석 시에만 실행 (profile) |
| Tree-sitter 언어 지원 범위 | 일부 언어 미지원 | GenericAnalysis fallback |
| LangGraph Checkpointer 성능 | 동시 Job 처리 시 DB 병목 | 커넥션 풀 최적화 + Redis 보조 |
| Instructor 모델 호환성 | Kimi K2.5 structured output 미지원 시 | JSON mode fallback + 수동 파싱 |
| Big Bang 전환 리스크 | 서비스 중단 | main 브랜치 보호 + 별도 v5 브랜치 |
| Datasketch FOSS Corpus 크기 | 초기 구축 시간 | 단계적 확장 (주요 프레임워크부터) |

---

## 17. Linear 티켓 구조 (예정)

설계 승인 후 다음 구조로 Linear 티켓을 생성합니다:

```
Epic: JIT-XXX Vantict Sniper v5.0 — LangGraph HMAS 마이그레이션

Phase 1: 인프라 준비
├── JIT-XX1: Docker Compose 수정 (Temporal 제거, SonarQube 추가)
├── JIT-XX2: Python 의존성 업데이트 (langgraph, instructor, tree-sitter)
├── JIT-XX3: DB 마이그레이션 004 작성
├── JIT-XX4: SonarQube 초기 설정
└── JIT-XX5: Tree-sitter 언어 그래머 설치 검증

Phase 2: Worker 구현
├── JIT-XX6: BaseWorker + Strategy/Factory 패턴
├── JIT-XX7: ForensicSupervisor Workers (W1-W5)
├── JIT-XX8: LogicSupervisor Workers (W6-W8)
└── JIT-XX9: StackSupervisor Workers (W9-W11)

Phase 3: Graph 조립
├── JIT-XX10: Level 2 Subgraphs (Forensic/Logic/Stack)
├── JIT-XX11: Level 1 MetaAgent Graph
├── JIT-XX12: PostgreSQL Checkpointer 통합
└── JIT-XX13: Instructor + Pydantic 통합

Phase 4: 질문 생성
├── JIT-XX14: 벡터 검색 기반 TopicSelector
├── JIT-XX15: 3전략 QuestionCrafter
├── JIT-XX16: Enhancement Agents 리팩토링
└── JIT-XX17: QualityGate 루프

Phase 5: 출력 + 프론트엔드
├── JIT-XX18: OutputAssembler + 4대 지표 산출
├── JIT-XX19: WebSocket 스트리밍
├── JIT-XX20: D3.js 차트 컴포넌트
└── JIT-XX21: 새 탭 구조 구현

Phase 6: 통합 테스트
├── JIT-XX22: E2E 테스트
├── JIT-XX23: Temporal 코드 완전 제거
├── JIT-XX24: 성능 벤치마크
└── JIT-XX25: 문서화
```

---

## 부록 A: 기술 선택 근거

| 기술 | 선택 이유 | 대안 | 대안 미선택 이유 |
|------|----------|------|----------------|
| LangGraph | StateGraph로 HMAS 자연스럽게 표현, Checkpointer durability | CrewAI, AutoGen | 추상화 과다, 커스터마이징 제한 |
| Instructor | Pydantic 네이티브, 자동 재시도, 다중 모델 지원 | LangChain structured_output | 모델 호환성 제한, Pydantic v2 미완전 지원 |
| Tree-sitter | 50+ 언어, 증분 파싱, 메모리 효율 | Python ast, Babel | 단일 언어만, 느린 속도 |
| Radon/Lizard | 정확한 CC/Halstead, 경량 | SonarQube 내장 | SonarQube는 세부 지표 API 제한 |
| SonarQube Community | 무료, 종합적 품질 분석, REST API | CodeClimate, Codacy | 유료, 제한적 API |
| Datasketch | MinHash/LSH 표절 탐지, Python 네이티브 | Moss, JPlag | 학술용 제한, API 의존 |
| D3.js | 최대 유연성, 커스텀 시각화 | Recharts, Chart.js | 커스터마이징 한계 |
| PostgreSQL Checkpointer | 기존 PostgreSQL 재활용, 트랜잭션 보장 | Redis, SQLite | 단일 장애점, 트랜잭션 미보장 |
