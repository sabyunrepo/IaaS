# Phase 2: Infrastructure Layer

> 원본 설계서: `plan/2026-02-15-v5-final-design.md`
> Linear 티켓: JIT-92 ~ JIT-99, JIT-125

## Linear 티켓 매핑

| 티켓 | 제목 | 참조 섹션 |
|------|------|----------|
| JIT-92 | Git 어댑터 (blame_runner -w -M -C, clone_manager, mailmap_writer) | §9.1 W1-W2, §7.2 Step 1/3 |
| JIT-93 | GitHub GraphQL 클라이언트 (get_user_node_id, get_user_repos_graphql) | §7.2 Step 1 |
| JIT-94 | Tree-sitter 어댑터 (AST 파싱: Python, JS, TS, Java, Go) | §9.0, §9.1 W6 |
| JIT-95 | Radon/Lizard 어댑터 (CC, Halstead, MI 산출) | §9.1 W7 |
| JIT-96 | SonarQube 어댑터 (REST API 연동: 기술부채, 코드스멜, 보안) | §9.1 W8 |
| JIT-97 | Datasketch 어댑터 (MinHash/LSH 표절 탐지) | §9.1 W5 |
| JIT-98 | Instructor 클라이언트 (Instructor + Pydantic + Langfuse 통합) | §12.3 |
| JIT-99 | pgvector 확장 (JD-Repo 벡터 유사도 + 코드 청크 임베딩) | §13 |
| **JIT-125** | **LinkedIn 어댑터 (BrightData 클라이언트 + 프로필 스크레이핑)** | **§9.1 W1 (LinkedIn 수집)** |

---

## §9. Worker Agent 상세 설계 (Tree-sitter 0.24 반영)

### 9.0 Tree-sitter 0.24 Breaking Change 대응

> **extra.md 반영:** Tree-sitter 0.24부터 `.so` 파일 빌드 방식(`Language.build_library`)이 **폐기**되었다. Python 패키지 바인딩을 직접 사용하는 방식으로 구현해야 한다.

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
            "typescript": Language(tsjs.language()),
            "go": Language(tsgo.language()),
            "java": Language(tsjava.language()),
        }

    def get_parser(self, lang_name: str) -> Parser:
        """Parser는 Thread-safe하지 않으므로 매 요청마다 생성"""
        if lang_name not in self.languages:
            raise ValueError(f"Unsupported language: {lang_name}")
        return Parser(self.languages[lang_name])

    def parse_code(self, code: str, lang_name: str):
        parser = self.get_parser(lang_name)
        return parser.parse(bytes(code, "utf8"))

    def extract_functions(self, root_node, lang_name: str) -> list[dict]:
        """Query API로 함수/클래스 추출"""
        query_scm = """
        (function_definition
          name: (identifier) @func.name)
        """
        query = self.languages[lang_name].query(query_scm)
        captures = query.captures(root_node)
        return [{"name": c[0].text.decode(), "node": c[0]} for c in captures]
```

### 9.1 Worker 총괄표

| # | Worker | Supervisor | 도구 | 입력 | 출력 | LLM |
|---|--------|------------|------|------|------|-----|
| W1 | CollectorWorker | Forensic | GraphQL, PyDriller, BrightData | github_urls, linkedin_url | collected_repos, identity_cluster | X |
| W2 | CleanerWorker | Forensic | git blame -w -M -C, Tree-sitter | raw_diffs, identity_cluster | cleaned_diffs, pure_contributions | X |
| W3 | VibectorWorker | Forensic | Git log, WPM calculator | cleaned_diffs, commit_timestamps | vibector_scores (AI 의심 구간) | X |
| W4 | CLAVEWorker | Forensic | Stylometry analyzer | cleaned_diffs | clave_fingerprint (저자 지문) | O |
| W5 | DatasketchWorker | Forensic | Datasketch (MinHash/LSH) | cleaned_diffs | plagiarism_report (유사도 맵) | X |
| W6 | ASTAnalyzerWorker | Logic | Tree-sitter (5개 언어) | cleaned_diffs, repo_files | ast_trees, semantic_diffs, code_chunks | X |
| W7 | ComplexityMeterWorker | Logic | Radon, Lizard, cloc | repo_files | complexity_metrics (CC, Halstead, MI) | X |
| W8 | QualityScannerWorker | Logic | SonarQube API, Bandit | repo_url | quality_report (부채, 스멜, 취약점) | X |
| W9 | SkillExtractorWorker | Stack | Tree-sitter, import parser | ast_analysis, jd_tech_stack | skill_extraction (기술 매핑) | O |
| W10 | APIDepthAnalyzerWorker | Stack | AST call graph | ast_analysis | api_depth_scores (API 활용 깊이) | O |
| W11 | ArchitectureEvaluatorWorker | Stack | AST pattern detector | ast_analysis | architecture_eval (패턴/SOLID) | O |

### 9.2 Worker 구현 패턴

#### BaseWorker (Template Method Pattern)

```python
# application/nodes/base_worker.py
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Generic, TypeVar

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)

class BaseWorker(ABC, Generic[TInput, TOutput]):
    """모든 Worker의 기본 클래스"""

    @abstractmethod
    def validate_input(self, input_data: TInput) -> bool:
        """입력 데이터 검증"""
        ...

    @abstractmethod
    async def execute(self, input_data: TInput) -> TOutput:
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
```

#### Strategy + Factory Pattern (언어별 분석)

```python
# infrastructure/analysis/strategy.py
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
    """TypeScript도 동일 Strategy 사용"""
    ...

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

### 9.3 노드 함수 원칙: Thin Wrapper

노드 함수는 **domain 호출 + infrastructure 호출의 조합**이다. 비즈니스 로직을 직접 작성하지 않는다.

```python
# application/nodes/identity_resolver.py
async def identity_resolver_node(state: ForensicState) -> dict:
    """DDD 원칙: 노드 = domain + infrastructure 조합"""
    # 1. infrastructure: git authors 추출
    authors = await git_adapter.extract_authors(state["clone_dir"])

    # 2. infrastructure: GitHub Node ID 조회
    node_id = await github_client.get_user_node_id(state["candidate_username"])

    # 3. domain: mailmap 생성 (순수 비즈니스 로직)
    mailmap = mailmap_builder.build_dynamic_mailmap(
        authors, state["github_profile"], node_id
    )

    # 4. infrastructure: .mailmap 파일 쓰기
    await mailmap_writer.write(state["clone_dir"], mailmap)

    # 5. infrastructure: git blame -w -M -C 실행
    blame_lines = await blame_runner.run_git_blame(
        state["clone_dir"], state["target_files"], mailmap
    )

    # 6. domain: blame 필터링 (순수 비즈니스 로직)
    identity_cluster = IdentityCluster.from_mailmap(mailmap, node_id)
    filtered = blame_filter.filter_blame_lines(blame_lines, identity_cluster)

    return {"blame_attributions": filtered, "identity_cluster": identity_cluster}
```

---

## §12.3 Instructor + Langfuse 통합

```python
# infrastructure/llm/instructor_client.py
import instructor
from langfuse.decorators import observe

@observe(name="generate_interview_question")
async def generate_question(topic: dict, context: dict) -> InterviewQuestion:
    """Langfuse 추적 + Instructor 구조화 출력"""
    # 1. Langfuse에서 프롬프트 가져오기
    prompt = langfuse.get_prompt("question_craft_v5", label="production")

    # 2. Instructor로 구조화 출력 생성
    result = await client.chat.completions.create(
        model=prompt.config.get("model", "kimi-k2.5"),
        response_model=InterviewQuestion,
        messages=prompt.compile(topic=topic, context=context),
        temperature=prompt.config.get("temperature", 0.7),
        max_retries=3,  # Pydantic 검증 실패 시 자동 재시도
    )
    return result
```

---

## §13. 벡터 검색 (RAG) 전략

### 13.1 임베딩 파이프라인

```
코드 파일 -> Tree-sitter AST -> 함수/클래스 단위 청크 분할
                                       |
                                       v
                              임베딩 모델 (text-embedding-3-small)
                                       |
                                       v
                              pgvector 저장 (Vector(1536))
                                       |
                              +--------+--------+
                              |        |        |
                          kind: code  kind: jd  kind: resume
```

### 13.2 청크 전략

| 소스 | 청크 단위 | 메타데이터 |
|------|----------|-----------|
| 코드 | 함수/클래스 (AST 기반) | file_path, language, complexity, author |
| JD | 섹션별 (자격요건, 우대사항) | section_type, keywords |
| 이력서 | 경력/프로젝트별 | company, role, duration |
| LinkedIn | 프로필 섹션별 | section_type |

### 13.3 JD-Repo 유사도 비교 (Funnel Stage 3 용)

```python
# infrastructure/embedding/pgvector_store.py
async def compute_jd_repo_similarity(
    jd_text: str,
    repo_readme: str,
    repo_description: str,
) -> float:
    """JD 텍스트와 레포 README/Description 간 벡터 유사도 계산"""
    jd_embedding = await embed(jd_text)
    repo_text = f"{repo_description}\n{repo_readme}"
    repo_embedding = await embed(repo_text)
    return cosine_similarity(jd_embedding, repo_embedding)
```

### 13.4 컨텍스트 예산 관리

```python
# application/use_cases/context_budget.py
class ContextBudget:
    MAX_TOKENS = 8000

    ALLOCATION = {
        "system_prompt": 1500,
        "jd_context": 1500,
        "code_chunks": 3000,      # 벡터 검색된 코드 청크
        "candidate_profile": 1000,
        "topic_context": 1000,
    }

    def allocate(self, section: str, content: str) -> str:
        max_tokens = self.ALLOCATION[section]
        return truncate_to_tokens(content, max_tokens)
```

---

## LinkedIn 어댑터 — BrightData 클라이언트 (JIT-125)

CollectorWorker(W1)에서 호출되는 LinkedIn 프로필 수집 어댑터이다. BrightData Scraping Browser API로 프로필 HTML을 가져오고, Domain 모델(`LinkedInProfile`)로 변환한다.

### 아키텍처

```
linkedin_url (입력)
      │
      ▼
BrightDataClient.scrape_profile(url)
      │  ← BrightData Scraping Browser API
      ▼
raw HTML/JSON
      │
      ▼
normalize_linkedin_profile(raw_data)   ← domain/identity/linkedin_normalizer.py
      │
      ▼
LinkedInProfile (도메인 모델)
      │
      ├──→ pgvector_store.save_embedding(kind="linkedin")
      └──→ ForensicState.linkedin_profile
```

### 구현

```python
# infrastructure/linkedin/brightdata_client.py
import httpx
from domain.identity.linkedin_models import LinkedInProfile
from domain.identity.linkedin_normalizer import normalize_linkedin_profile

class BrightDataClient:
    def __init__(self, api_key: str, scraping_browser_url: str):
        self.api_key = api_key
        self.base_url = scraping_browser_url
        self.max_retries = 3

    async def scrape_profile(self, linkedin_url: str) -> LinkedInProfile | None:
        """LinkedIn 프로필 스크레이핑 → 도메인 모델 변환

        Returns None if:
        - linkedin_url이 빈 문자열/None
        - BrightData API 호출 실패 (모든 재시도 소진)
        - 프로필 비공개
        """
        if not linkedin_url:
            return None

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{self.base_url}/scrape",
                        json={"url": linkedin_url, "format": "json"},
                        headers={"Authorization": f"Bearer {self.api_key}"},
                    )

                    if response.status_code == 429:
                        # Rate limit — exponential backoff
                        await asyncio.sleep(2 ** attempt)
                        continue

                    response.raise_for_status()
                    raw_data = response.json()
                    return normalize_linkedin_profile(raw_data)

            except httpx.HTTPError:
                if attempt == self.max_retries - 1:
                    return None
                await asyncio.sleep(2 ** attempt)

        return None
```

### ForensicSupervisor Graph 연동

CollectorWorker(W1) 노드에서 LinkedIn 수집 호출:

```python
# application/nodes/collector_worker.py (발췌)
async def collector_worker(state: ForensicState) -> dict:
    # ... GitHub 수집 로직 ...

    # LinkedIn 수집 (URL 있을 때만)
    linkedin_profile = None
    if state.get("linkedin_url"):
        linkedin_profile = await brightdata_client.scrape_profile(state["linkedin_url"])

        # 프로필 임베딩 저장
        if linkedin_profile:
            await pgvector_store.save_embedding(
                job_id=state["job_id"],
                kind="linkedin",
                content=linkedin_profile.summary,
                metadata={"name": linkedin_profile.name, "headline": linkedin_profile.headline},
            )

    return {
        "collected_repos": repos,
        "linkedin_profile": linkedin_profile.model_dump() if linkedin_profile else None,
    }
```

### 테스트 케이스

- `test_scrape_profile_success` — 정상 응답 → LinkedInProfile 변환
- `test_scrape_profile_no_url` — URL 미제공 → None 반환
- `test_scrape_profile_rate_limit` — 429 → exponential backoff 후 재시도
- `test_scrape_profile_all_retries_failed` — 3회 실패 → None (graceful)
- `test_scrape_profile_private` — 비공개 프로필 → None
