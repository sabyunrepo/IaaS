> [페르소나 정의] 역할: 시니어 풀스택 아키텍트, 태도: 현실적, 냉철, 분석적, 비판적
> **검토 의견:**
> 1. **의존성 최신화 필수:** 2026년 2월 기준, 제공된 라이브러리 버전(LangGraph 1.0 미만, Tree-sitter 0.23 등)은 이미 레거시입니다. 특히 Tree-sitter 0.24의 Breaking Change(바인딩 방식 변경)를 반영하지 않으면 빌드 자체가 불가능합니다.
> 2. **상태 객체 비만(State Bloat) 방지:** `MetaState`에 Raw Data(AST, Diff 전문)를 싣는 것은 메모리 힙 폭발의 지름길입니다. Reference ID(DB Key)만 전달하는 방식으로 설계를 수정했습니다.
> 3. **리소스 효율화:** SonarQube는 상시 구동 시 메모리를 과도하게 점유하므로, Docker Profile을 통해 분석 시에만 구동하도록 변경합니다.
> 
> 
> 위 사항을 모두 반영하여 **Jittda Sniper v5.0 최종 설계서**를 재작성합니다.

---

# Jittda Sniper v5.0 — Clean Slate 재건축 최종 설계서

> **작성일:** 2026-02-15
> **버전:** 5.1 (Dependency & Architecture Optimized)
> **상태:** 최종 설계 완료 (구현 단계 진입)
> **원칙:** **"마이그레이션이 아닌 재건축(Reconstruction)"** — `jittda/` 신규 디렉토리, Fresh init.sql, Modern Tech Stack

---

## 목차

1. [Executive Summary](https://www.google.com/search?q=%231-executive-summary)
2. [설계 철학 및 핵심 원칙](https://www.google.com/search?q=%232-%EC%84%A4%EA%B3%84-%EC%B2%A0%ED%95%99-%EB%B0%8F-%ED%95%B5%EC%8B%AC-%EC%9B%90%EC%B9%99)
3. [Clean Slate 접근 전략](https://www.google.com/search?q=%233-clean-slate-%EC%A0%91%EA%B7%BC-%EC%A0%84%EB%9E%B5)
4. [DDD 아키텍처 및 디렉토리 구조](https://www.google.com/search?q=%234-ddd-%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98-%EB%B0%8F-%EB%94%94%EB%A0%89%ED%86%A0%EB%A6%AC-%EA%B5%AC%EC%A1%B0)
5. [기술 스택 선정 (최신화)](https://www.google.com/search?q=%235-%EA%B8%B0%EC%88%A0-%EC%8A%A4%ED%83%9D-%EC%84%A0%EC%A0%95-%EC%B5%9C%EC%8B%A0%ED%99%94)
6. [3계층 HMAS 아키텍처](https://www.google.com/search?q=%236-3%EA%B3%84%EC%B8%B5-hmas-%EC%95%84%ED%82%A4%ED%85%8D%EC%B2%98)
7. [Identity Resolution Pipeline](https://www.google.com/search?q=%237-identity-resolution-pipeline)
8. [JD 기반 Funnel Selection](https://www.google.com/search?q=%238-jd-%EA%B8%B0%EB%B0%98-funnel-selection)
9. [Worker Agent 상세 설계 (Tree-sitter 0.24 반영)](https://www.google.com/search?q=%239-worker-agent-%EC%83%81%EC%84%B8-%EC%84%A4%EA%B3%84-tree-sitter-024-%EB%B0%98%EC%98%81)
10. [LangGraph 그래프 설계 (Reference Passing)](https://www.google.com/search?q=%2310-langgraph-%EA%B7%B8%EB%9E%98%ED%94%84-%EC%84%A4%EA%B3%84-reference-passing)
11. [4대 핵심 지표 체계](https://www.google.com/search?q=%2311-4%EB%8C%80-%ED%95%B5%EC%8B%AC-%EC%A7%80%ED%91%9C-%EC%B2%B4%EA%B3%84)
12. [Pydantic 모델 + Instructor 통합](https://www.google.com/search?q=%2312-pydantic-%EB%AA%A8%EB%8D%B8--instructor-%ED%86%B5%ED%95%A9)
13. [벡터 검색 (RAG) 전략](https://www.google.com/search?q=%2313-%EB%B2%A1%ED%84%B0-%EA%B2%80%EC%83%89-rag-%EC%A0%84%EB%9E%B5)
14. [프롬프트 엔지니어링](https://www.google.com/search?q=%2314-%ED%94%84%EB%A1%AC%ED%94%84%ED%8A%B8-%EC%97%94%EC%A7%80%EB%8B%88%EC%96%B4%EB%A7%81)
15. [인프라 구성 (Docker + Cloudflare Tunnel)](https://www.google.com/search?q=%2315-%EC%9D%B8%ED%94%84%EB%9D%BC-%EA%B5%AC%EC%84%B1-docker--cloudflare-tunnel)
16. [프론트엔드 설계](https://www.google.com/search?q=%2316-%ED%94%84%EB%A1%A0%ED%8A%B8%EC%97%94%EB%93%9C-%EC%84%A4%EA%B3%84)
17. [테스트 전략](https://www.google.com/search?q=%2317-%ED%85%8C%EC%8A%A4%ED%8A%B8-%EC%A0%84%EB%9E%B5)
18. [Phase별 구현 로드맵](https://www.google.com/search?q=%2318-phase%EB%B3%84-%EA%B5%AC%ED%98%84-%EB%A1%9C%EB%93%9C%EB%A7%B5)

---

## 1. Executive Summary

현재 Vantict Sniper v4.0(Temporal.io 기반 고정 4-Phase 파이프라인)을 **완전히 새로운 프로젝트 `jittda/`**로 재건축한다. 기존 코드베이스 위에서 작업하는 "마이그레이션"이 아니라, 옆 부지에 새 건물을 짓고 필요한 가구(로직)만 골라 옮기는 **Clean Slate Reconstruction**이다.

### 핵심 변경점 (v5.1 반영)

| 영역 | AS-IS (Vantict v4.0) | TO-BE (Jittda v5.0) |
| --- | --- | --- |
| **프로젝트 구조** | `backend/` (레거시 혼재) | `jittda/` (신규 Clean Slate) |
| **오케스트레이션** | Temporal.io (고정 파이프라인) | **LangGraph 1.0+** (StateGraph, 동적 HMAS) |
| **상태 관리** | 메모리 내 전체 데이터 전달 | **Reference Passing** (DB ID만 전달, Blob 분리) |
| **AST 파싱** | Tree-sitter 0.20 (.so 빌드 필요) | **Tree-sitter 0.24+** (Python Package 네이티브 바인딩) |
| **데이터 전달** | plain dict (암묵적 키) | Pydantic v2 `TypedDict` State (타입 안전) |
| **LLM 출력** | JSON 직접 파싱 | Instructor + Pydantic v2 (자동 검증/재시도) |
| **코드 분석** | PyGithub + 단순 clone | Identity Resolution + Forensic Blame + AST Pruning |
| **인프라** | SonarQube 상시 구동 | **Docker Profile** 기반 On-Demand 실행 |
| **DDD** | 미적용 (로직 혼재) | 엄격한 4계층 (Interface/Application/Domain/Infrastructure) |

---

## 2. 설계 철학 및 핵심 원칙

### 2.1 시스템 설계 철학

**"확률적 AI(LLM)와 결정론적 알고리즘(Static Analysis)의 하이브리드 결합"**

단순히 LLM에게 "이 코드 어때?"라고 묻는 것이 아니라, 수학적으로 계산된 지표(Fact)를 LLM에게 제공하여 해석(Insight)하게 함으로써 할루시네이션을 원천 차단하고 신뢰도를 보장한다.

### 2.2 핵심 원칙

| # | 원칙 | 설명 |
| --- | --- | --- |
| 1 | **Noise-Free** | Fork, 라이브러리, AI 생성/Boilerplate 코드를 완벽히 제거한 순수 기여분만 분석 |
| 2 | **Semantic Analysis** | 텍스트 기반이 아닌 AST(추상 구문 트리) 기반의 논리적 분석 수행 |
| 3 | **Identity-First** | "이 코드를 정말 지원자가 짰는가?" 검증이 분석보다 선행 |
| 4 | **JD-Relevance** | "이 프로젝트가 회사 업무와 관련 있는가?" JD 적합성 선별 후 분석 |
| 5 | **Reference Passing** | **(New)** LangGraph 상태 객체에는 '데이터'가 아닌 '참조(ID)'만 담는다. |
| 6 | **Fact-Grounded** | 모든 LLM 판단에 정량적 분석 데이터 근거 필수 |
| 7 | **Parallel Execution** | Fan-out/Fan-in 패턴으로 분석 속도 극대화 |
| 8 | **Clean Separation** | DDD 4계층 엄격 준수, 계층 간 의존성 규칙 위반 금지 |

---

## 3. Clean Slate 접근 전략

### 3.1 원칙: "마이그레이션이 아닌 재건축"

* `jittda/`는 **완전히 새로운 디렉토리**에서 시작
* Temporal 코드가 **애초에 존재하지 않음** (제거할 것이 없음)
* DB는 **Fresh `init.sql**` 하나로 초기화 (Alembic revision 히스토리 금지)
* 기존 Vantict 코드는 **참조용 라이브러리(Read-only)**로만 취급

### 3.2 레거시 자산 선별 가이드

**"파일 복사-붙여넣기 금지, 로직 이식 허용"**이 원칙이다.

* **[Asset] 핵심 로직:** `scoring_formulas.py` 등은 `domain/scoring/calculator.py`로 Pydantic v2 기반 재작성.
* **[Reference] 참조 대상:** `services/git.py` 등의 아이디어만 참조하여 Identity Resolution 파이프라인으로 재구현.
* **[Liability] 폐기 대상:** Temporal 관련 코드, SVG 차트, 정규식 파서 등은 폐기.

---

## 4. DDD 아키텍처 및 디렉토리 구조

### 4.1 4계층 아키텍처

```
  Interface → Application → Domain ← Infrastructure
                              ↑
                              │ (Domain은 외부를 모른다)
                              │
                     Infrastructure가 Domain 모델을 리턴

```

### 4.2 디렉토리 구조

```
jittda/
├── docker-compose.yml        # PostgreSQL, Redis, SonarQube(Profile), Cloudflare Tunnel
├── Makefile                   # 표준화된 개발 명령어
├── init.sql                   # Fresh DB 스키마
├── pyproject.toml             # Python 의존성 (Updated)
├── .env.example
│
├── interface/                 # 계층 1: 외부 어댑터
│   ├── api/
│   │   └── main.py            # FastAPI 앱 엔트리포인트
│
├── application/               # 계층 2: 오케스트레이션
│   ├── graphs/                # LangGraph StateGraph 정의
│   │   ├── meta_graph.py
│   │   └── ...
│   ├── nodes/                 # LangGraph 노드 함수 (Thin Wrapper)
│   └── states/                # TypedDict State 정의 (Reference Passing 적용)
│
├── domain/                    # 계층 3: 순수 비즈니스 로직
│   ├── identity/              # Identity Resolution 모델
│   ├── scoring/               # 점수 산출 로직
│   └── analysis/              # 분석 도메인 모델
│
├── infrastructure/            # 계층 4: 외부 서비스 어댑터
│   ├── analysis/
│   │   ├── tree_sitter_adapter.py  # (v0.24 대응)
│   │   └── sonarqube_adapter.py
│   └── llm/
│       └── instructor_client.py
│
└── tests/

```

---

## 5. 기술 스택 선정 (최신화)

2026년 2월 기준, 안정성과 성능이 검증된 최신 버전으로 스택을 확정합니다.

### 5.1 Python 의존성 (pyproject.toml)

```toml
[project]
dependencies = [
    # Orchestration: 1.0 GA 안정화 버전 및 3.x 체크포인터
    "langgraph>=1.0.8",
    "langgraph-checkpoint-postgres>=3.0.4",

    # LLM: 최신 Anthropic/OpenAI 모델 지원
    "instructor>=1.7.0",
    "langfuse>=2.57.0",

    # Web Framework: Pydantic v2 최적화
    "fastapi>=0.119.0",
    "uvicorn>=0.30.0",
    "websockets>=14.0",

    # AST & Static Analysis: 0.24.x 버전으로 통일 (Breaking Change 대응)
    "tree-sitter>=0.24.7",
    "tree-sitter-python>=0.24.1",
    "tree-sitter-javascript>=0.24.1",
    "tree-sitter-typescript>=0.24.1",
    "tree-sitter-java>=0.24.1",
    "tree-sitter-go>=0.24.1",
    "radon>=6.0.1",
    "lizard>=1.17.10",
    "bandit>=1.8.0",

    # Git & GitHub
    "PyGithub>=2.5.0",
    "gql[aiohttp]>=3.5.0",
    "PyDriller>=2.9",

    # Data & Vector
    "psycopg[binary]>=3.2.0",
    "pgvector>=0.3.6",
    "redis>=5.2.0",
    "datasketch>=1.6.5",

    # Utilities
    "pydantic>=2.12.5",
    "python-Levenshtein>=0.26.0",
    "httpx>=0.28.0",
]

```

---

## 6. 3계층 HMAS 아키텍처

### 6.1 시스템 아키텍처 개요

LangGraph의 `StateGraph`를 활용하여 3계층 Multi-Agent System을 구현합니다.

```
Level 1: MetaAgent (총괄 오케스트레이터)
│
├── Phase 1: PlanGenerator
│
├── Phase 2: AnalysisDispatcher (Fan-out)
│   ├── Level 2: ForensicSupervisor (병렬)
│   │   ├── W1: Collector (GraphQL)
│   │   ├── W2: Cleaner (Identity Resolution)
│   │   └── W3-5: Vibector, CLAVE, Datasketch
│   │
│   ├── Level 2: LogicSupervisor (병렬)
│   │   ├── W6: ASTAnalyzer (Tree-sitter)
│   │   ├── W7: ComplexityMeter
│   │   └── W8: QualityScanner (SonarQube)
│   │
│   └── Level 2: StackSupervisor (Logic 완료 후 실행 - v5.0 기준)
│       ├── W9: SkillExtractor
│       ├── W10: APIDepthAnalyzer
│       └── W11: ArchitectureEvaluator
│
├── Phase 2.5: ProfileSynthesizer (Fan-in)
│
├── Phase 3: QuestionOrchestrator
│
└── Phase 5: OutputAssembler

```

> **설계 노트 (StackSupervisor 지연):**
> 현재 설계상 StackSupervisor는 LogicSupervisor의 AST 분석 결과(`ast_analysis_ref`)가 필요합니다. v5.0에서는 구현 단순성을 위해 **Logic 완료 후 Stack 실행(순차)** 방식을 채택합니다. v5.1 최적화 시 Pipelining을 도입합니다.

---

## 7. Identity Resolution Pipeline

(기존 설계 유지: GitHub Node ID 추적 + 동적 Mailmap + 3단계 포렌식)

---

## 8. JD 기반 Funnel Selection

(기존 설계 유지: Hard Filter → Relevance Score → Vector Similarity 3단계 퍼널)

---

## 9. Worker Agent 상세 설계 (Tree-sitter 0.24 반영)

### 9.1 Tree-sitter 구현 변경 (Critical)

Tree-sitter 0.24부터 `.so` 파일 빌드 방식(`Language.build_library`)이 폐기되었습니다. Python 패키지 바인딩을 직접 사용하는 방식으로 `infrastructure/analysis/tree_sitter_adapter.py`를 구현해야 합니다.

```python
# infrastructure/analysis/tree_sitter_adapter.py
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava

class TreeSitterAdapter:
    def __init__(self):
        # 0.24.x: 언어별 패키지에서 직접 language 객체 로딩
        self.languages = {
            "python": Language(tspython.language()),
            "javascript": Language(tsjs.language()),
            "typescript": Language(tsjs.language()), # TS도 JS 파서 호환 혹은 별도 패키지
            "go": Language(tsgo.language()),
            "java": Language(tsjava.language()),
        }
    
    def get_parser(self, lang_name: str) -> Parser:
        """Parser는 Thread-safe하지 않으므로 매 요청/컨텍스트마다 생성 권장"""
        if lang_name not in self.languages:
            raise ValueError(f"Unsupported language: {lang_name}")
        
        parser = Parser(self.languages[lang_name])
        return parser

    def parse_code(self, code: str, lang_name: str):
        parser = self.get_parser(lang_name)
        # 0.24.x: encoding 지정 필수
        return parser.parse(bytes(code, "utf8"))

    def extract_functions(self, root_node, lang_name: str):
        # Query API 활용
        query_scm = """
        (function_definition
          name: (identifier) @func.name)
        """
        if lang_name == 'python':
            query = self.languages['python'].query(query_scm)
            captures = query.captures(root_node)
            # ... 처리 로직

```

---

## 10. LangGraph 그래프 설계 (Reference Passing)

### 10.1 MetaState 최적화 (Reference Passing)

LangGraph의 State 객체에 대용량 데이터(코드 전문, AST, Diff 등)를 직접 넣으면 DB Checkpoint 크기가 커지고 성능이 저하됩니다. **DB Primary Key(UUID)만 전달**합니다.

```python
# application/states/meta_state.py
from typing import TypedDict, Optional

class MetaState(TypedDict):
    # Core Context
    job_id: str
    
    # References (Not Raw Data)
    input_data_ref: str        # jobs table ID
    identity_cluster_ref: Optional[str] # identity_resolutions table ID
    
    # Analysis Result References (Pointer to analysis_results table)
    forensic_result_ref: Optional[str]
    logic_result_ref: Optional[str]
    stack_result_ref: Optional[str]
    
    # Metrics
    candidate_scores: Optional[dict] # 4대 지표 점수 (가벼우므로 포함 가능)
    
    # Flow Control
    status: str
    revision_count: int
    errors: list[str]

```

### 10.2 노드 구현 패턴 (Load -> Process -> Save -> Return Ref)

```python
# application/nodes/logic_supervisor.py
async def logic_supervisor_node(state: MetaState):
    job_id = state["job_id"]
    
    # 1. Load Data from DB (using ref)
    repo_files = await repo_repository.get_files(job_id)
    
    # 2. Process (Analysis)
    ast_result = await ast_analyzer.analyze(repo_files)
    
    # 3. Save Large Result to DB
    result_id = await analysis_repository.save_result(
        job_id, "logic_supervisor", ast_result
    )
    
    # 4. Return Reference only
    return {"logic_result_ref": result_id}

```

---

## 11. 4대 핵심 지표 체계

(기존 설계 유지: 논리력, 전문성, 안정성, 진정성)

---

## 12. Pydantic 모델 + Instructor 통합

Pydantic v2 문법을 준수합니다.

```python
from pydantic import BaseModel, Field, ConfigDict

class InterviewQuestion(BaseModel):
    model_config = ConfigDict(strict=True) # v2 Config
    
    question_text: str = Field(min_length=20)
    intent: str
    # ...

```

---

## 13. 벡터 검색 (RAG) 전략

(기존 설계 유지: pgvector 기반)

---

## 14. 프롬프트 엔지니어링

(기존 설계 유지: Negative Selection 등 3전략)

---

## 15. 인프라 구성 (Docker + Cloudflare Tunnel)

### 15.1 On-Demand SonarQube (Profile 적용)

SonarQube는 무겁기 때문에, 상시 구동 대신 분석이 필요할 때만 구동하거나 별도 프로파일로 관리합니다. 운영 환경에서는 별도 인스턴스를 권장하지만, 단일 Docker 환경에서는 Profile을 사용합니다.

```yaml
# docker-compose.yml
services:
  # ... postgres, redis ...

  sonarqube:
    image: sonarqube:community
    profiles: ["analysis"]  # 기본 up 시 실행되지 않음
    # ...
    
  backend:
    # ...
    environment:
      - SONAR_ON_DEMAND=true

```

### 15.2 Fresh init.sql (최적화)

```sql
-- jittda/init.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- LangGraph Checkpoint용 (3.0.x 호환)
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint BYTEA,
    metadata BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- (나머지 비즈니스 테이블: jobs, analysis_results 등 기존과 동일)

```

---

## 16. 프론트엔드 설계

(기존 설계 유지: React 19 + D3.js + WebSocket Streaming)

---

## 17. 테스트 전략

(기존 설계 유지: Domain Unit Test 중심)

---

## 18. Phase별 구현 로드맵 및 Linear 티켓

### Phase 0: Modern Scaffolding (3일)

1. **Project Init:** `jittda/` 생성, pyproject.toml (Updated versions) 작성.
2. **Infra Setup:** Docker Compose (Postgres, Redis, SonarQube Profile), Fresh init.sql.

### Phase 1: Domain & Core Logic (5일)

3. **Identity Domain:** Pydantic v2 모델 정의.
4. **Tree-sitter Adapter:** v0.24 대응 구현 (패키지 로딩 방식).

### Phase 2: Infrastructure & Data (7일)

5. **GitHub/Git Adapter:** GraphQL 및 Blame 로직.
6. **DB Repository:** Reference Passing을 위한 Load/Save 로직 구현.

### Phase 3: Application & LangGraph (7일)

7. **Nodes Implementation:** Load-Process-Save-Ref 패턴 적용.
8. **Graph Assembly:** MetaGraph 및 SubGraph 연결.

### Phase 4: AI & Quality (5일)

9. **Instructor Integration:** Pydantic v2 호환성 검증.
10. **Question Logic:** 3전략 프롬프트 구현.

### Phase 5: Output & Frontend (10일)

11. **API/WS:** 실시간 스트리밍 구현.
12. **Frontend:** D3.js 차트 및 결과 페이지.

---

### 부록: 마이그레이션 체크리스트 (v4 -> v5)

* [ ] `requirements.txt` 폐기 및 `pyproject.toml` (v5.1 스펙) 적용
* [ ] Tree-sitter `.so` 빌드 스크립트 삭제 및 `pip install tree-sitter-python` 등으로 대체
* [ ] Alembic 마이그레이션 폴더 삭제 (Fresh Init)
* [ ] Temporal Activity 코드 폐기 (LangGraph Node로 재작성)
* [ ] SonarQube 호출 로직에 "Container Start/Wait" 로직 추가 (On-Demand)

> [페르소나 정의] 역할: 시니어 풀스택 아키텍트, 태도: 현실적, 냉철, 분석적
> **지적 확인:** 맞습니다. 이전 구조는 모노레포(Monorepo) 환경에서 **Backend와 Frontend, 그리고 인프라 설정이 혼재**되어 있어, CI/CD 파이프라인 구축 시 빌드 컨텍스트가 꼬이고 도커 이미지 최적화가 불가능한 구조였습니다.
> **조치:** **"관심사의 완벽한 분리(Separation of Concerns)"** 원칙에 따라, 루트 레벨에서는 오케스트레이션(Docker Compose)만 담당하고, 실제 애플리케이션 코드는 `backend/`와 `frontend/`로 물리적으로 격리합니다.

---

# Jittda Sniper v5.0 — Monorepo Directory Structure

이 구조는 **실제 상용 배포(Production)**와 **로컬 개발(Local Dev)**이 모두 가능한 표준 모노레포 구조입니다.

## 1. 전체 디렉토리 구조 (Tree View)

```text
jittda/
├── docker-compose.yml          # [Root] 전체 서비스 오케스트레이션 (Backend + Frontend + DB + Redis)
├── Makefile                    # [Root] 통합 빌드/실행 명령어 (e.g., make up, make build)
├── .env.example                # [Root] 공통 환경변수 템플릿
├── .gitignore                  # [Root] Git 무시 설정
│
├── backend/                    # [Backend Service] Python + FastAPI + LangGraph
│   ├── Dockerfile              # Backend 전용 빌드 명세
│   ├── pyproject.toml          # Python 의존성 관리 (Poetry/UV 권장)
│   ├── alembic.ini             # (Optional) DB 마이그레이션 설정 (Fresh Init이라도 설정은 유지 권장)
│   ├── .dockerignore           # Backend 빌드 컨텍스트 최적화
│   │
│   └── src/                    # 소스 코드 루트 (DDD 4계층 적용)
│       ├── main.py             # 앱 진입점
│       ├── interface/          # [Layer 1] API Routes, Websocket
│       ├── application/        # [Layer 2] LangGraph Workflows, UseCases
│       ├── domain/             # [Layer 3] Pure Business Logic (Models)
│       ├── infrastructure/     # [Layer 4] External Adapters (Git, LLM, DB)
│       └── tests/              # Backend 테스트 코드
│
├── frontend/                   # [Frontend Service] React 19 + Vite + D3.js
│   ├── Dockerfile              # Frontend 전용 빌드 명세 (Multi-stage: Build -> Nginx)
│   ├── package.json            # Node.js 의존성
│   ├── vite.config.ts          # Vite 설정
│   ├── tsconfig.json           # TypeScript 설정
│   ├── tailwind.config.js      # Tailwind CSS 설정
│   ├── .dockerignore           # Frontend 빌드 컨텍스트 최적화
│   │
│   ├── public/                 # 정적 에셋 (favicon 등)
│   └── src/                    # React 소스 코드
│       ├── components/         # D3 Charts, UI Components
│       ├── hooks/              # Custom Hooks (WebSocket 등)
│       ├── pages/              # 라우트별 페이지
│       └── services/           # API 호출 클라이언트
│
└── infra/                      # [Infrastructure] 설정 및 초기화 스크립트
    ├── postgres/
    │   └── init.sql            # Fresh DB Schema
    ├── sonarqube/
    │   └── sonar-project.properties # (Optional) 로컬 분석 설정
    └── nginx/                  # (Production Only) 리버스 프록시 설정
        └── default.conf

```

---

## 2. 주요 설정 파일 상세 (Docker)

### 2.1 Root `docker-compose.yml`

루트에서는 각 서비스의 `build context`를 명확히 지정하여 격리합니다.

```yaml
services:
  # --- Data Layer ---
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: jittda
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro # infra 경로 참조
    ports:
      - "5432:5432"
    networks:
      - jittda_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - jittda_net

  sonarqube:
    image: sonarqube:community
    profiles: ["analysis"]  # 필요 시에만 구동
    ports:
      - "9000:9000"
    networks:
      - jittda_net

  # --- Application Layer ---
  backend:
    build:
      context: ./backend      # 중요: backend 디렉토리를 컨텍스트로 사용
      dockerfile: Dockerfile
    volumes:
      - ./backend/src:/app/src # 개발 시 Hot Reload (코드 수정 즉시 반영)
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/jittda
      - REDIS_URL=redis://redis:6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    ports:
      - "8000:8000"
    networks:
      - jittda_net

  frontend:
    build:
      context: ./frontend     # 중요: frontend 디렉토리를 컨텍스트로 사용
      dockerfile: Dockerfile
      target: development     # 개발용 스테이지 타겟팅
    volumes:
      - ./frontend/src:/app/src # 개발 시 Hot Reload
    environment:
      - VITE_API_URL=http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - jittda_net

  # --- Tunneling ---
  cloudflared:
    image: cloudflare/cloudflared:latest
    command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}
    networks:
      - jittda_net

volumes:
  postgres_data:

networks:
  jittda_net:
    driver: bridge

```

### 2.2 Backend `backend/Dockerfile`

Python 환경을 격리하고 최적화합니다.

```dockerfile
# Base Image
FROM python:3.11-slim

# System Dependencies (Git is required for PyDriller/Cloning)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python Dependencies
# (Caching layer: copy requirements first)
COPY pyproject.toml .
# poetry나 uv를 쓴다면 여기서 설치 및 export
# 여기서는 pip 예시
RUN pip install --no-cache-dir . 

# Copy Application Code
COPY . .

# Environment
ENV PYTHONPATH=/app/src

# Run
CMD ["uvicorn", "src.interface.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

```

### 2.3 Frontend `frontend/Dockerfile`

Multi-stage build를 사용하여 개발용과 배포용을 분리합니다.

```dockerfile
# Stage 1: Base & Install Dependencies
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Development
FROM base AS development
COPY . .
CMD ["npm", "run", "dev", "--", "--host"]

# Stage 3: Builder (Production)
FROM base AS builder
COPY . .
RUN npm run build

# Stage 4: Production Serve (Nginx)
FROM nginx:alpine AS production
COPY --from=builder /app/dist /usr/share/nginx/html
# Nginx 설정이 필요하다면 infra에서 복사
# COPY ../infra/nginx/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

```

---

## 3. 리팩토링 포인트 및 주의사항

1. **Context Isolation (컨텍스트 격리):**
* `docker-compose.yml`에서 `build.context`를 반드시 `./backend`, `./frontend`로 각각 지정해야 합니다.
* 루트 디렉토리의 파일이 불필요하게 Docker Daemon으로 전송되는 것을 막기 위해 각 폴더 안에 `.dockerignore`를 반드시 작성하십시오.


2. **Shared Resources (공유 자원):**
* DB 초기화 스크립트(`init.sql`)는 이제 코드 베이스와 분리된 `infra/postgres/`에 위치합니다. 이는 인프라 설정이 애플리케이션 로직과 섞이지 않게 합니다.


3. **Hot Reload (핫 리로드):**
* `volumes` 설정을 통해 로컬 호스트의 소스 코드 변경 사항이 컨테이너 내부에 즉시 반영되도록 구성했습니다.
* Backend: `./backend/src:/app/src`
* Frontend: `./frontend/src:/app/src`


4. **DDD Layer 위치:**
* 이전 설계서의 `interface`, `application`, `domain`, `infrastructure` 폴더는 이제 **`backend/src/` 아래**로 이동합니다. 이것이 Python 패키지 구조상 올바른 위치입니다.



이제 이 구조대로 프로젝트를 초기화(`jittda/` 생성 -> `backend/`, `frontend/`, `infra/` 생성) 하시고 진행하시면 됩니다.
네, 아주 좋은 접근입니다. **Cloudflare Tunnel(인프라 영역)**과 **Jittda 서비스(애플리케이션 영역)**의 생명주기를 분리하는 전략입니다.

이렇게 하면 애플리케이션을 배포/재시작하더라도 터널 연결은 끊어지지 않고 유지되며, 여러 프로젝트가 하나의 터널 네트워크를 공유할 수도 있어 확장성 면에서도 유리합니다.

요청하신 구조에 맞춰 **2개의 독립된 프로젝트**로 디렉토리와 설정을 구성해 드립니다.

---

### 1. 전체 디렉토리 구조 (변경됨)

인프라용 폴더(`infra-tunnel`)와 애플리케이션용 폴더(`jittda`)를 분리합니다.

```text
/ (Root)
├── infra-tunnel/             # [인프라] Cloudflare Tunnel 전용
│   ├── docker-compose.yml
│   └── .env                  # TUNNEL_TOKEN 저장
│
└── jittda/                   # [애플리케이션] Jittda 서비스
    ├── docker-compose.yml    # frontend가 외부 네트워크 참조
    ├── backend/
    ├── frontend/
    └── infra/                # DB, Nginx 설정 등

```

---

### 2. Step 1: 인프라 (Cloudflare Tunnel) 구성

이 `docker-compose.yml`은 **`jittda-public`**이라는 이름의 도커 네트워크를 생성하고, 터널 컨테이너를 실행합니다.

**파일 위치:** `infra-tunnel/docker-compose.yml`

```yaml
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: jittda_tunnel_gateway
    restart: unless-stopped
    command: tunnel run
    environment:
      - TUNNEL_TOKEN=${TUNNEL_TOKEN}
    networks:
      - public_net

# 핵심: 네트워크 이름을 명시적으로 지정하여 생성
networks:
  public_net:
    name: jittda-public  # 이 이름이 중요합니다. (다른 컴포즈에서 참조할 이름)
    driver: bridge

```

**실행 방법:**

1. `infra-tunnel/.env` 파일에 `TUNNEL_TOKEN=eyJh...` 작성.
2. 실행: `docker compose up -d`
3. 결과: `jittda-public`이라는 도커 네트워크가 생성되고 터널이 대기 상태가 됩니다.

---

### 3. Step 2: Jittda 애플리케이션 구성

Jittda 컴포즈 파일에서는 `frontend` 서비스만 **외부 네트워크(`jittda-public`)**에 다리를 걸칩니다. Backend와 DB는 내부 네트워크에 숨깁니다.

**파일 위치:** `jittda/docker-compose.yml`

```yaml
services:
  # --- Data Layer (내부망 전용) ---
  postgres:
    image: postgres:16-alpine
    # ... (환경변수 및 볼륨 설정 생략) ...
    networks:
      - internal_net

  redis:
    image: redis:7-alpine
    networks:
      - internal_net

  # --- Application Layer ---
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    depends_on:
      - postgres
      - redis
    networks:
      - internal_net # 백엔드는 외부에 노출될 필요 없음 (프론트/Nginx 통해서만 접근)

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production # Nginx가 포함된 프로덕션 빌드
    container_name: jittda_frontend # 터널에서 바라볼 호스트네임 고정
    depends_on:
      - backend
    networks:
      - internal_net # 백엔드와 통신용
      - external_tunnel_net # 터널과 통신용 (외부 노출)

# 네트워크 정의
networks:
  internal_net:
    driver: bridge
    
  # 핵심: 이미 생성된 외부 네트워크를 참조
  external_tunnel_net:
    name: jittda-public # infra-tunnel에서 만든 네트워크 이름
    external: true

```

---

### 4. Cloudflare Zero Trust 대시보드 설정 방법

이제 Cloudflare 관리자 페이지(Zero Trust Dashboard)에서 **Public Hostname**을 설정할 때 다음과 같이 입력해야 합니다.

* **Service:** `HTTP`
* **URL:** `jittda_frontend:80`

**설명:**
터널 컨테이너(`cloudflared`)와 프론트엔드 컨테이너(`jittda_frontend`)가 `jittda-public`이라는 **동일한 도커 네트워크**에 있기 때문에, 터널은 `container_name`을 도메인 주소처럼 사용하여 프론트엔드 Nginx 포트(80)로 트래픽을 전달할 수 있습니다.

### 요약: 트래픽 흐름

```mermaid
graph LR
    User((User)) --> CF[Cloudflare Edge]
    CF --> Tunnel[Container: cloudflared]
    
    subgraph "Network: jittda-public"
    Tunnel -- "http://jittda_frontend:80" --> Frontend[Container: Nginx/React]
    end
    
    subgraph "Network: internal_net"
    Frontend -- "API Call" --> Backend[Container: FastAPI]
    Backend --> DB[(Postgres)]
    end

```

이 구조로 진행하시면 됩니다. `infra-tunnel`을 먼저 띄우고 `jittda`를 띄우시면 완벽하게 연결됩니다.
