# Jittda Sniper v5.0 — Clean Slate Reconstruction 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Vantict Sniper v4.0을 완전히 새로운 `jittda/` 디렉토리에서 LangGraph HMAS + DDD 아키텍처로 재건축한다.

**Architecture:** DDD 4계층 (Interface → Application → Domain ← Infrastructure) + LangGraph StateGraph 3계층 HMAS (MetaAgent → Supervisor → Worker). Reference Passing 패턴으로 State Bloat 방지. Instructor + Pydantic v2 구조화 출력.

**Tech Stack:** Python 3.11 + FastAPI + LangGraph 1.0.8+ | React 19 + Vite + D3.js v7 | PostgreSQL 16 + pgvector + Redis 7 | Tree-sitter 0.24+ | Instructor 1.7+ | Langfuse

---

## Linear 프로젝트 정보

| 항목 | 값 |
|------|-----|
| **프로젝트** | Jittda Sniper v5.0 — Clean Slate Reconstruction |
| **팀** | Jittda (JIT) |
| **총 이슈** | 44개 (JIT-82 ~ JIT-125) |
| **총 기간** | 42일 (7 Phase) |

## Phase별 마일스톤 & 티켓 총괄

| Phase | 마일스톤 | 기간 | 티켓 범위 | 핵심 산출물 |
|-------|---------|------|----------|-----------|
| **0** | Scaffolding | 3일 | JIT-82~85 (4개) | 프로젝트 구조, Docker, DB, Makefile |
| **1** | Domain Layer | 5일 | JIT-86~91, JIT-124 (7개) | 순수 비즈니스 로직 (Identity, LinkedIn, Funnel, Scoring) |
| **2** | Infrastructure Layer | 7일 | JIT-92~99, JIT-125 (9개) | 외부 서비스 어댑터 (Git, GitHub, LinkedIn, AST, LLM) |
| **3** | Application Layer | 7일 | JIT-100~105 (6개) | LangGraph 그래프 (HMAS 파이프라인) |
| **4** | Questions + Enhancement | 5일 | JIT-106~110 (5개) | 질문 생성 엔진 |
| **5** | Output + Frontend | 10일 | JIT-111~119 (9개) | 출력물 조립 + D3.js UI |
| **6** | Test + Polish | 5일 | JIT-120~123 (4개) | 테스트 + 벤치마크 |

## 설계 참조 문서

각 Phase의 상세 설계는 아래 문서에서 참조:

| Phase | 참조 문서 |
|-------|----------|
| Phase 0 | `plan/v5-design/phase0-scaffolding.md` |
| Phase 1 | `plan/v5-design/phase1-domain.md` |
| Phase 2 | `plan/v5-design/phase2-infrastructure.md` |
| Phase 3 | `plan/v5-design/phase3-application.md` |
| Phase 4 | `plan/v5-design/phase4-questions.md` |
| Phase 5 | `plan/v5-design/phase5-output-frontend.md` |
| Phase 6 | `plan/v5-design/phase6-testing.md` |
| 원본 전체 | `plan/2026-02-15-v5-final-design.md` |

---

# Phase 0: Scaffolding (3일)

## Task 1: JIT-82 — 프로젝트 초기화

**Files:**
- Create: `jittda/backend/src/interface/__init__.py`
- Create: `jittda/backend/src/application/__init__.py`
- Create: `jittda/backend/src/domain/__init__.py`
- Create: `jittda/backend/src/infrastructure/__init__.py`
- Create: `jittda/backend/pyproject.toml`
- Create: `jittda/frontend/package.json`
- Create: `jittda/.gitignore`

**Step 1: 프로젝트 루트 디렉토리 구조 생성**

```bash
mkdir -p jittda/{backend/src/{interface/api/{routes,middleware,schemas},application/{graphs,nodes,states,use_cases},domain/{identity,scoring,matching,question,analysis},infrastructure/{git,github,analysis,llm,linkedin,embedding,persistence}},frontend/src/{components/charts,hooks,pages/ResultPage,services},infra/{postgres,sonarqube,nginx}}
```

**Step 2: pyproject.toml 작성**

설계서 §5.4의 의존성을 그대로 사용:
```toml
[project]
name = "jittda-backend"
version = "5.0.0"
requires-python = ">=3.11"
dependencies = [
    "langgraph>=1.0.8",
    "langgraph-checkpoint-postgres>=3.0.4",
    "instructor>=1.7.0",
    "langfuse>=2.57.0",
    "fastapi>=0.119.0",
    "uvicorn>=0.30.0",
    "websockets>=14.0",
    "tree-sitter>=0.24.7",
    "tree-sitter-python>=0.24.1",
    "tree-sitter-javascript>=0.24.1",
    "tree-sitter-typescript>=0.24.1",
    "tree-sitter-java>=0.24.1",
    "tree-sitter-go>=0.24.1",
    "radon>=6.0.1",
    "lizard>=1.17.10",
    "bandit>=1.8.0",
    "PyGithub>=2.5.0",
    "gql[aiohttp]>=3.5.0",
    "PyDriller>=2.9",
    "psycopg[binary]>=3.2.0",
    "pgvector>=0.3.6",
    "redis>=5.2.0",
    "datasketch>=1.6.5",
    "pydantic>=2.12.5",
    "python-Levenshtein>=0.26.0",
    "httpx>=0.28.0",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "pytest-cov", "ruff", "pytest-benchmark"]
```

**Step 3: 각 계층에 __init__.py 생성**

```bash
find jittda/backend/src -type d -exec touch {}/__init__.py \;
```

**Step 4: .gitignore 작성**

**Step 5: frontend/package.json 작성**

설계서 §16.5 참조.

**Step 6: 커밋**

```bash
git add jittda/
git commit -m "feat: [P0-1] jittda/ 프로젝트 초기화 — DDD 4계층 구조 + pyproject.toml [JIT-82]"
```

---

## Task 2: JIT-83 — Docker Compose + Cloudflare Tunnel

**Files:**
- Create: `infra-tunnel/docker-compose.yml`
- Create: `infra-tunnel/.env.example`
- Create: `jittda/docker-compose.yml`
- Create: `jittda/backend/Dockerfile`
- Create: `jittda/frontend/Dockerfile`
- Create: `jittda/.env.example`

**Step 1: infra-tunnel 독립 프로젝트 작성**

설계서 §15.1의 docker-compose.yml 그대로 사용. jittda-public 네트워크 생성.

**Step 2: jittda/docker-compose.yml 작성**

설계서 §15.2: PostgreSQL 16, Redis 7, Backend, Frontend, SonarQube(profile).

**Step 3: Backend Dockerfile 작성**

설계서 §15.3: python:3.11-slim + git.

**Step 4: Frontend Dockerfile 작성 (Multi-stage)**

설계서 §15.4: base → development → builder → production(Nginx).

**Step 5: .env.example 작성**

**Step 6: docker compose up 실행 테스트**

```bash
cd jittda && docker compose up -d
# PostgreSQL, Redis healthcheck 확인
docker compose ps
docker compose down
```

**Step 7: 커밋**

```bash
git add infra-tunnel/ jittda/docker-compose.yml jittda/backend/Dockerfile jittda/frontend/Dockerfile
git commit -m "feat: [P0-2] Docker Compose + Cloudflare Tunnel 독립 프로젝트 [JIT-83]"
```

---

## Task 3: JIT-84 — Fresh init.sql

**Files:**
- Create: `jittda/infra/postgres/init.sql`

**Step 1: init.sql 작성**

설계서 §15.5의 전체 스키마:
- uuid-ossp, vector 확장
- LangGraph Checkpoint 테이블 (3.0.x 호환)
- users, jobs, analysis_results, candidate_scores, identity_resolutions, sonarqube_projects, embeddings
- pgvector ivfflat 인덱스

**Step 2: Docker로 DB 초기화 테스트**

```bash
cd jittda && docker compose up -d postgres
docker compose exec postgres psql -U postgres -d jittda -c "\dt"
# 모든 테이블이 생성되었는지 확인
docker compose down
```

**Step 3: 커밋**

```bash
git add jittda/infra/postgres/init.sql
git commit -m "feat: [P0-3] Fresh init.sql — DB 스키마 + LangGraph Checkpoint [JIT-84]"
```

---

## Task 4: JIT-85 — Makefile 표준화

**Files:**
- Create: `jittda/Makefile`

**Step 1: Makefile 작성**

설계서 §15.6의 전체 타겟.

**Step 2: make up → make test → make down 동작 확인**

```bash
cd jittda
make up
make test   # (아직 테스트 없으므로 실패 예상 — 정상)
make down
```

**Step 3: 커밋**

```bash
git add jittda/Makefile
git commit -m "feat: [P0-4] Makefile 표준화 [JIT-85]"
```

---

# Phase 1: Domain Layer (5일)

> **원칙:** Domain 레이어는 외부 의존성 0. 순수 Python + Pydantic만 사용.
> **참조:** `plan/v5-design/phase1-domain.md`

## Task 5: JIT-86 — Identity Resolution 도메인 모델

**Files:**
- Create: `jittda/backend/src/domain/identity/models.py`
- Test: `jittda/backend/tests/domain/test_identity_models.py`

**Step 1: 테스트 작성 (Red)**

```python
# tests/domain/test_identity_models.py
from domain.identity.models import MailmapEntry, IdentityCluster, BlameLineAttribution, PureContribution

def test_mailmap_entry_creation():
    entry = MailmapEntry(
        canonical="Kim Doe",
        canonical_email="kim@example.com",
        alias_name="kim",
        alias_email="kim@noreply.github.com",
        confidence="high",
    )
    assert entry.confidence == "high"

def test_mailmap_entry_invalid_confidence():
    """confidence는 high/medium/low만 허용"""
    # Pydantic validation test

def test_identity_cluster_creation():
    cluster = IdentityCluster(
        github_node_id="12345",
        canonical_name="Kim Doe",
        canonical_email="kim@example.com",
        aliases=[],
        total_commits=100,
        verified_commits=85,
    )
    assert cluster.verified_commits == 85

def test_blame_line_attribution():
    line = BlameLineAttribution(
        file_path="src/main.py",
        line_number=42,
        content="return result",
        author_name="Kim",
        author_email="kim@example.com",
        commit_sha="abc123",
        is_move=False,
        is_copy=False,
        is_whitespace_only=False,
    )
    assert not line.is_move

def test_pure_contribution():
    contrib = PureContribution(
        file_path="src/main.py",
        language="python",
        total_lines=100,
        pure_logic_lines=60,
        removed_imports=15,
        removed_comments=10,
        removed_config=5,
        removed_generated=10,
        function_bodies=["def process(data): ..."],
    )
    assert contrib.pure_logic_lines == 60
```

**Step 2: 테스트 실행 (실패 확인)**

```bash
cd jittda && docker compose exec backend pytest tests/domain/test_identity_models.py -v
# Expected: FAIL (모듈 없음)
```

**Step 3: 모델 구현**

설계서 §7.3의 코드를 Pydantic v2 ConfigDict(strict=True)로 구현.

**Step 4: 테스트 실행 (통과 확인)**

```bash
cd jittda && docker compose exec backend pytest tests/domain/test_identity_models.py -v
# Expected: ALL PASS
```

**Step 5: 커밋**

```bash
git add jittda/backend/src/domain/identity/models.py jittda/backend/tests/domain/test_identity_models.py
git commit -m "feat: [P1-5] Identity Resolution 도메인 모델 [JIT-86]"
```

---

## Task 6: JIT-87 — Mailmap Builder

**Files:**
- Create: `jittda/backend/src/domain/identity/mailmap_builder.py`
- Test: `jittda/backend/tests/domain/test_mailmap_builder.py`

**Step 1: 테스트 작성 (Red)**

```python
# tests/domain/test_mailmap_builder.py
from domain.identity.mailmap_builder import build_dynamic_mailmap
from domain.identity.models import MailmapEntry

def test_noreply_email_detected():
    """GitHub noreply 이메일은 confidence: high로 매핑"""
    authors = [GitAuthor(name="Kim", email="123+kim@users.noreply.github.com")]
    profile = GitHubProfile(name="Kim Doe", email="kim@example.com")
    result = build_dynamic_mailmap(authors, profile, "12345")
    assert len(result) == 1
    assert result[0].confidence == "high"

def test_exact_email_match():
    """프로필 이메일과 정확히 일치하면 confidence: high"""
    authors = [GitAuthor(name="Kim Doe", email="kim@example.com")]
    profile = GitHubProfile(name="Kim Doe", email="kim@example.com")
    result = build_dynamic_mailmap(authors, profile, "12345")
    assert any(e.confidence == "high" for e in result)

def test_levenshtein_clustering():
    """이름 유사도 threshold 이상이면 confidence: medium"""
    authors = [GitAuthor(name="Kim Doe", email="kimdoe@company.com")]
    profile = GitHubProfile(name="Kim D.", email="kim@personal.com")
    result = build_dynamic_mailmap(authors, profile, "12345", threshold=0.75)
    assert len(result) >= 1

def test_same_domain_email():
    """동일 도메인 이메일은 confidence: low"""
    authors = [GitAuthor(name="Unknown", email="unknown@company.com")]
    profile = GitHubProfile(name="Kim", email="kim@company.com")
    result = build_dynamic_mailmap(authors, profile, "12345")
    assert any(e.confidence == "low" for e in result)

def test_deduplication():
    """중복 매핑 제거"""
    authors = [
        GitAuthor(name="Kim", email="kim@example.com"),
        GitAuthor(name="Kim", email="kim@example.com"),
    ]
    profile = GitHubProfile(name="Kim", email="kim@example.com")
    result = build_dynamic_mailmap(authors, profile, "12345")
    # 중복 없이 1개만
    unique_aliases = set((e.alias_name, e.alias_email) for e in result)
    assert len(unique_aliases) == len(result)
```

**Step 2: 테스트 실행 (실패 확인)**

**Step 3: 구현** — 설계서 §7.2 Step 2 알고리즘.

**Step 4: 테스트 통과 확인**

**Step 5: 커밋**

```bash
git commit -m "feat: [P1-6] Mailmap Builder — 동적 .mailmap 생성 [JIT-87]"
```

---

## Task 7: JIT-88 — Blame Filter

**Files:**
- Create: `jittda/backend/src/domain/identity/blame_filter.py`
- Test: `jittda/backend/tests/domain/test_blame_filter.py`

**Step 1~5:** TDD 사이클 (테스트 → 실패 → 구현 → 통과 → 커밋)

테스트 케이스:
- `test_filter_by_identity_cluster` — 클러스터에 속한 author만 통과
- `test_exclude_whitespace_only` — 공백 변경만 있는 라인 제외
- `test_exclude_move_and_copy` — 파일 이동/복사 라인 제외
- `test_pure_contribution_calculation` — 순수 기여 라인 수 계산

커밋: `feat: [P1-7] Blame Filter [JIT-88]`

---

## Task 8: JIT-89 — Semantic Pruner

**Files:**
- Create: `jittda/backend/src/domain/identity/semantic_pruner.py`
- Test: `jittda/backend/tests/domain/test_semantic_pruner.py`

**Step 1~5:** TDD 사이클

테스트 케이스:
- `test_remove_imports` — import 구문 제거
- `test_remove_comments` — 주석/docstring 제거
- `test_remove_config` — 설정 파일 제거
- `test_remove_generated` — 자동 생성 코드 감지
- `test_preserve_function_bodies` — 함수/클래스 본문 보존
- `test_combined_pruning` — 전체 파이프라인 통합

커밋: `feat: [P1-8] Semantic Pruner — AST 노이즈 제거 규칙 [JIT-89]`

---

## Task 9: JIT-90 — Funnel Selection 규칙

**Files:**
- Create: `jittda/backend/src/domain/matching/funnel_rules.py`
- Test: `jittda/backend/tests/domain/test_funnel_rules.py`

**Step 1~5:** TDD 사이클

테스트 케이스:
- `test_stage1_excludes_forks` — Fork 레포 제외
- `test_stage1_excludes_old_repos` — 오래된 레포 제외
- `test_stage1_org_contribution_threshold` — Org 기여도 미달 제외
- `test_stage1_language_filter` — JD 언어와 교집합 필터
- `test_stage2_tech_stack_scoring` — 기술스택 매칭 점수
- `test_stage2_recent_activity_bonus` — 최근 활동 가산
- `test_stage3_vector_threshold` — 벡터 유사도 임계값

설계서 §8.3의 코드를 기반으로 구현.

커밋: `feat: [P1-9] Funnel Selection 규칙 — 3단계 퍼널 [JIT-90]`

---

## Task 9b: JIT-124 — LinkedIn 프로필 도메인 모델

**Files:**
- Create: `jittda/backend/src/domain/identity/linkedin_models.py`
- Create: `jittda/backend/src/domain/identity/linkedin_normalizer.py`
- Test: `jittda/backend/tests/domain/test_linkedin_models.py`

**Step 1: 테스트 작성 (Red)**

```python
# tests/domain/test_linkedin_models.py
from domain.identity.linkedin_models import LinkedInProfile, LinkedInExperience

def test_linkedin_profile_creation():
    profile = LinkedInProfile(
        name="Kim Doe",
        headline="Senior Backend Engineer",
        profile_url="https://linkedin.com/in/kimdoe",
        experiences=[LinkedInExperience(company="Acme", title="SWE", duration_months=24)],
    )
    assert profile.total_experience_months == 24

def test_current_company():
    profile = LinkedInProfile(
        name="Kim",
        profile_url="https://linkedin.com/in/kim",
        experiences=[
            LinkedInExperience(company="Current Co", title="Lead", duration_months=12, is_current=True),
            LinkedInExperience(company="Old Co", title="SWE", duration_months=36),
        ],
    )
    assert profile.current_company == "Current Co"

def test_empty_profile():
    profile = LinkedInProfile(name="Kim", profile_url="https://linkedin.com/in/kim")
    assert profile.total_experience_months == 0
    assert profile.current_company is None

def test_normalize_raw_data():
    raw = {"name": "Kim", "url": "https://linkedin.com/in/kim", "experiences": [
        {"company": "Acme", "title": "SWE", "start": "2024-01", "end": None, "description": "Backend"}
    ]}
    result = normalize_linkedin_profile(raw)
    assert isinstance(result, LinkedInProfile)
    assert result.experiences[0].is_current is True
```

**Step 2: 테스트 실행 (실패 확인)**

**Step 3: 구현** — `plan/v5-design/phase1-domain.md` §7.4 참조.

**Step 4: 테스트 통과 확인**

**Step 5: 커밋**

```bash
git commit -m "feat: [P1-5b] LinkedIn 프로필 도메인 모델 [JIT-124]"
```

---

## Task 10: JIT-91 — Scoring Calculator

**Files:**
- Create: `jittda/backend/src/domain/scoring/models.py`
- Create: `jittda/backend/src/domain/scoring/calculator.py`
- Create: `jittda/backend/src/domain/scoring/normalizer.py`
- Test: `jittda/backend/tests/domain/test_scoring.py`

**Step 1~5:** TDD 사이클

테스트 케이스:
- `test_weighted_total` — 0.30 논리력 + 0.30 전문성 + 0.20 안정성 + 0.20 진정성
- `test_logic_score_formula` — 순환복잡도/할스테드 기반
- `test_mastery_score_formula` — API 활용 깊이 가중합
- `test_stability_score_formula` — 부채+Churn 기반
- `test_authenticity_index` — 순수 기여 비율
- `test_confidence_high` — 데이터소스 3+, 레포 5+
- `test_confidence_medium` — 데이터소스 2, 레포 2-4
- `test_confidence_low` — 데이터소스 1 이하

설계서 §11의 수학적 모델 구현.

커밋: `feat: [P1-10] Scoring Calculator — 4대 지표 가중 합산 [JIT-91]`

---

# Phase 2: Infrastructure Layer (7일)

> **참조:** `plan/v5-design/phase2-infrastructure.md`

## Task 11: JIT-92 — Git 어댑터

**Files:**
- Create: `jittda/backend/src/infrastructure/git/blame_runner.py`
- Create: `jittda/backend/src/infrastructure/git/clone_manager.py`
- Create: `jittda/backend/src/infrastructure/git/mailmap_writer.py`
- Test: `jittda/backend/tests/infrastructure/test_git_adapter.py`

**Step 1: 테스트 작성** — asyncio 기반, subprocess 호출 Mock

**Step 2: 구현**
- `blame_runner.py`: `git blame -w -M -C -C --line-porcelain` 비동기 실행
- `clone_manager.py`: `git clone --depth N` + 임시 디렉토리 관리
- `mailmap_writer.py`: MailmapEntry → .mailmap 파일 변환

**Step 3: 커밋** — `feat: [P2-11] Git 어댑터 [JIT-92]`

---

## Task 12: JIT-93 — GitHub GraphQL 클라이언트

**Files:**
- Create: `jittda/backend/src/infrastructure/github/graphql_client.py`
- Create: `jittda/backend/src/infrastructure/github/rest_client.py`
- Test: `jittda/backend/tests/infrastructure/test_github_client.py`

**Step 1~5:** TDD 사이클

설계서 §7.2 Step 1의 GraphQL 쿼리 구현. gql[aiohttp] 사용.

커밋: `feat: [P2-12] GitHub GraphQL 클라이언트 [JIT-93]`

---

## Task 13: JIT-94 — Tree-sitter 어댑터

**Files:**
- Create: `jittda/backend/src/infrastructure/analysis/tree_sitter_adapter.py`
- Test: `jittda/backend/tests/infrastructure/test_tree_sitter.py`

**Step 1: 테스트 작성**

```python
def test_python_function_extraction():
    code = '''
def hello():
    return "world"

class MyClass:
    def method(self):
        pass
'''
    adapter = TreeSitterAdapter()
    tree = adapter.parse_code(code, "python")
    functions = adapter.extract_functions(tree.root_node, "python")
    assert len(functions) >= 2  # hello, method

def test_unsupported_language():
    adapter = TreeSitterAdapter()
    with pytest.raises(ValueError):
        adapter.get_parser("rust")
```

**Step 2: 구현** — 설계서 §9.0의 0.24.x 네이티브 바인딩 코드.

**Step 3: 커밋** — `feat: [P2-13] Tree-sitter 어댑터 [JIT-94]`

---

## Task 14: JIT-95 — Radon/Lizard 어댑터

**Files:**
- Create: `jittda/backend/src/infrastructure/analysis/complexity_adapter.py`
- Create: `jittda/backend/src/infrastructure/analysis/strategy.py`
- Test: `jittda/backend/tests/infrastructure/test_complexity.py`

설계서 §9.2의 Strategy + Factory Pattern.

커밋: `feat: [P2-14] Radon/Lizard 어댑터 [JIT-95]`

---

## Task 15: JIT-96 — SonarQube 어댑터

**Files:**
- Create: `jittda/backend/src/infrastructure/analysis/sonarqube_adapter.py`
- Test: `jittda/backend/tests/infrastructure/test_sonarqube.py`

Graceful Degradation 포함 (SonarQube 미가동 시 빈 결과 반환).

커밋: `feat: [P2-15] SonarQube 어댑터 [JIT-96]`

---

## Task 16: JIT-97 — Datasketch 어댑터

**Files:**
- Create: `jittda/backend/src/infrastructure/analysis/datasketch_adapter.py`
- Test: `jittda/backend/tests/infrastructure/test_datasketch.py`

MinHash n-gram + LSH 인덱스.

커밋: `feat: [P2-16] Datasketch 어댑터 [JIT-97]`

---

## Task 17: JIT-98 — Instructor 클라이언트

**Files:**
- Create: `jittda/backend/src/infrastructure/llm/instructor_client.py`
- Create: `jittda/backend/src/infrastructure/llm/cached_client.py`
- Create: `jittda/backend/src/infrastructure/llm/langfuse_client.py`
- Test: `jittda/backend/tests/infrastructure/test_llm_client.py`

**Step 1: 테스트 작성**

```python
@pytest.mark.asyncio
async def test_instructor_structured_output(mock_openai):
    """Instructor가 Pydantic 모델로 파싱하는지 확인"""
    result = await generate_question(topic={}, context={})
    assert isinstance(result, InterviewQuestion)

async def test_langfuse_fallback_to_yaml(mock_langfuse_down):
    """Langfuse 장애 시 YAML fallback"""
    prompt = get_prompt_with_fallback("question_craft_v5")
    assert prompt is not None

async def test_redis_cache_hit(mock_redis):
    """동일 입력 캐시 히트"""
    result1 = await cached_llm_call("test_input")
    result2 = await cached_llm_call("test_input")
    assert mock_openai.call_count == 1  # 캐시 히트로 1번만 호출
```

**Step 2: 구현** — 설계서 §12.3 + §14.3.

**Step 3: 커밋** — `feat: [P2-17] Instructor 클라이언트 [JIT-98]`

---

## Task 18: JIT-99 — pgvector 확장

**Files:**
- Create: `jittda/backend/src/infrastructure/embedding/pgvector_store.py`
- Test: `jittda/backend/tests/infrastructure/test_pgvector.py`

설계서 §13의 임베딩 파이프라인 + JD-Repo 유사도.

커밋: `feat: [P2-18] pgvector 확장 [JIT-99]`

---

## Task 18b: JIT-125 — LinkedIn 어댑터

**Files:**
- Create: `jittda/backend/src/infrastructure/linkedin/brightdata_client.py`
- Test: `jittda/backend/tests/infrastructure/test_linkedin.py`

**Step 1: 테스트 작성 (Red)**

```python
# tests/infrastructure/test_linkedin.py
import pytest
from infrastructure.linkedin.brightdata_client import BrightDataClient
from domain.identity.linkedin_models import LinkedInProfile

@pytest.mark.asyncio
async def test_scrape_profile_success(mock_brightdata_api):
    client = BrightDataClient(api_key="test", scraping_browser_url="http://mock")
    result = await client.scrape_profile("https://linkedin.com/in/kimdoe")
    assert isinstance(result, LinkedInProfile)
    assert result.name == "Kim Doe"

@pytest.mark.asyncio
async def test_scrape_profile_no_url():
    client = BrightDataClient(api_key="test", scraping_browser_url="http://mock")
    result = await client.scrape_profile(None)
    assert result is None

@pytest.mark.asyncio
async def test_scrape_profile_no_url_empty_string():
    client = BrightDataClient(api_key="test", scraping_browser_url="http://mock")
    result = await client.scrape_profile("")
    assert result is None

@pytest.mark.asyncio
async def test_scrape_profile_rate_limit(mock_brightdata_429_then_ok):
    """429 → backoff → 재시도 → 성공"""
    client = BrightDataClient(api_key="test", scraping_browser_url="http://mock")
    result = await client.scrape_profile("https://linkedin.com/in/kimdoe")
    assert result is not None

@pytest.mark.asyncio
async def test_scrape_profile_all_retries_failed(mock_brightdata_always_fail):
    """3회 실패 → None (graceful)"""
    client = BrightDataClient(api_key="test", scraping_browser_url="http://mock")
    result = await client.scrape_profile("https://linkedin.com/in/kimdoe")
    assert result is None
```

**Step 2: 구현** — `plan/v5-design/phase2-infrastructure.md` LinkedIn 어댑터 섹션 참조.

**Step 3: 커밋**

```bash
git commit -m "feat: [P2-12b] LinkedIn 어댑터 — BrightData 클라이언트 [JIT-125]"
```

---

# Phase 3: Application Layer — Graphs (7일)

> **참조:** `plan/v5-design/phase3-application.md`

## Task 19: JIT-100 — State 정의

**Files:**
- Create: `jittda/backend/src/application/states/meta_state.py`
- Create: `jittda/backend/src/application/states/forensic_state.py`
- Create: `jittda/backend/src/application/states/logic_state.py`
- Create: `jittda/backend/src/application/states/stack_state.py`
- Test: `jittda/backend/tests/application/test_states.py`

설계서 §10.1의 TypedDict State. Reference Passing 적용.

커밋: `feat: [P3-19] State 정의 — Reference Passing [JIT-100]`

---

## Task 20: JIT-101 — ForensicSupervisor Graph

**Files:**
- Create: `jittda/backend/src/application/graphs/forensic_graph.py`
- Create: `jittda/backend/src/application/nodes/collector_worker.py`
- Create: `jittda/backend/src/application/nodes/identity_resolver.py`
- Create: `jittda/backend/src/application/nodes/semantic_pruner_node.py`
- Create: `jittda/backend/src/application/nodes/vibector_worker.py`
- Create: `jittda/backend/src/application/nodes/clave_worker.py`
- Create: `jittda/backend/src/application/nodes/datasketch_worker.py`
- Create: `jittda/backend/src/application/nodes/forensic_aggregator.py`
- Test: `jittda/backend/tests/application/test_forensic_graph.py`

설계서 §10.3. 각 노드는 Thin Wrapper (설계서 §9.3).

커밋: `feat: [P3-20] ForensicSupervisor Graph [JIT-101]`

---

## Task 21: JIT-102 — LogicSupervisor Graph

**Files:**
- Create: `jittda/backend/src/application/graphs/logic_graph.py`
- Create: `jittda/backend/src/application/nodes/ast_analyzer_worker.py`
- Create: `jittda/backend/src/application/nodes/complexity_meter_worker.py`
- Create: `jittda/backend/src/application/nodes/quality_scanner_worker.py`
- Create: `jittda/backend/src/application/nodes/logic_aggregator.py`
- Test: `jittda/backend/tests/application/test_logic_graph.py`

설계서 §10.4. 3개 Worker 완전 병렬.

커밋: `feat: [P3-21] LogicSupervisor Graph [JIT-102]`

---

## Task 22: JIT-103 — StackSupervisor Graph

**Files:**
- Create: `jittda/backend/src/application/graphs/stack_graph.py`
- Create: `jittda/backend/src/application/nodes/skill_extractor_worker.py`
- Create: `jittda/backend/src/application/nodes/api_depth_worker.py`
- Create: `jittda/backend/src/application/nodes/architecture_evaluator_worker.py`
- Create: `jittda/backend/src/application/nodes/stack_aggregator.py`
- Test: `jittda/backend/tests/application/test_stack_graph.py`

설계서 §10.4. LogicSupervisor AST 결과 참조.

커밋: `feat: [P3-22] StackSupervisor Graph [JIT-103]`

---

## Task 23: JIT-104 — MetaAgent Graph 조립

**Files:**
- Create: `jittda/backend/src/application/graphs/meta_graph.py`
- Create: `jittda/backend/src/application/nodes/input_router.py`
- Create: `jittda/backend/src/application/nodes/plan_generator.py`
- Create: `jittda/backend/src/application/nodes/profile_synthesizer.py`
- Create: `jittda/backend/src/application/nodes/output_assembler_node.py`
- Test: `jittda/backend/tests/application/test_meta_graph.py`

설계서 §10.2. Fan-out/Fan-in + QualityGate 루프 + PostgreSQL Checkpointer.

커밋: `feat: [P3-23] MetaAgent Graph 조립 [JIT-104]`

---

## Task 24: JIT-105 — FastAPI + WebSocket 통합

**Files:**
- Create: `jittda/backend/src/interface/api/routes/jobs.py`
- Create: `jittda/backend/src/interface/api/routes/auth.py`
- Create: `jittda/backend/src/interface/api/routes/health.py`
- Create: `jittda/backend/src/interface/api/main.py`
- Create: `jittda/backend/src/interface/websocket/stream_manager.py`
- Test: `jittda/backend/tests/interface/test_api.py`

설계서 §10.5. LangGraph astream + WebSocket.

커밋: `feat: [P3-24] FastAPI + WebSocket 통합 [JIT-105]`

---

# Phase 4: 질문 생성 + Enhancement (5일)

> **참조:** `plan/v5-design/phase4-questions.md`

## Task 25: JIT-106 — TopicSelector

**Files:**
- Create: `jittda/backend/src/application/nodes/topic_selector.py`
- Create: `jittda/backend/src/application/use_cases/context_budget.py`
- Test: `jittda/backend/tests/application/test_topic_selector.py`

설계서 §13.4 ContextBudget + pgvector 벡터 검색.

커밋: `feat: [P4-25] TopicSelector [JIT-106]`

---

## Task 26: JIT-107 — 3전략 QuestionCrafter

**Files:**
- Create: `jittda/backend/src/application/nodes/question_crafter.py`
- Create: `jittda/backend/src/domain/question/models.py`
- Create: `jittda/backend/src/infrastructure/llm/prompts/question_negative.yaml`
- Create: `jittda/backend/src/infrastructure/llm/prompts/question_complexity.yaml`
- Create: `jittda/backend/src/infrastructure/llm/prompts/question_evolution.yaml`
- Test: `jittda/backend/tests/application/test_question_crafter.py`

설계서 §14.2 — 3전략 + InterviewQuestion 모델 (§12.2).

커밋: `feat: [P4-26] 3전략 QuestionCrafter [JIT-107]`

---

## Task 27: JIT-108 — Enhancement Agents (5개)

**Files:**
- Create: `jittda/backend/src/application/nodes/enhancement_agents.py`
- Test: `jittda/backend/tests/application/test_enhancement.py`

5개 에이전트 병렬 실행 (terminology, answer_guide, follow_up, red_flags, code_reference).

커밋: `feat: [P4-27] Enhancement Agents [JIT-108]`

---

## Task 28: JIT-109 — QualityGate 루프

**Files:**
- Create: `jittda/backend/src/application/nodes/quality_gate.py`
- Test: `jittda/backend/tests/application/test_quality_gate.py`

Reviewer + Reviser, revision_count < 2 조건부 루프.

커밋: `feat: [P4-28] QualityGate 루프 [JIT-109]`

---

## Task 29: JIT-110 — Langfuse 프롬프트 업로드

**Files:**
- Create: `jittda/backend/scripts/upload_prompts.py`
- Modify: `jittda/backend/src/infrastructure/llm/prompts/*.yaml`

모든 프롬프트를 Langfuse production label로 등록.

커밋: `feat: [P4-29] Langfuse 프롬프트 업로드 [JIT-110]`

---

# Phase 5: 출력 + 프론트엔드 (10일)

> **참조:** `plan/v5-design/phase5-output-frontend.md`

## Task 30: JIT-111 — OutputAssembler

설계서 §6.2 Phase 5.

커밋: `feat: [P5-30] OutputAssembler [JIT-111]`

## Task 31: JIT-112 — 4대 지표 산출 + DB 저장

설계서 §11. domain Calculator → candidate_scores 테이블.

커밋: `feat: [P5-31] 4대 지표 산출 + DB 저장 [JIT-112]`

## Task 32: JIT-113 — FourAxisRadar.tsx

D3.js 4축 레이더. 설계서 §16.1.

커밋: `feat: [P5-32] FourAxisRadar.tsx [JIT-113]`

## Task 33: JIT-114 — ComplexityTreemap.tsx

D3.js Treemap. 파일 클릭 드릴다운.

커밋: `feat: [P5-33] ComplexityTreemap.tsx [JIT-114]`

## Task 34: JIT-115 — AICodeHeatmap.tsx

D3.js Heatmap. Human vs AI 비율.

커밋: `feat: [P5-34] AICodeHeatmap.tsx [JIT-115]`

## Task 35: JIT-116 — AgentProgressFlow.tsx

WebSocket + useLangGraphStream. 설계서 §16.4.

커밋: `feat: [P5-35] AgentProgressFlow.tsx [JIT-116]`

## Task 36: JIT-117 — Overview Tab

3초 요약 + 신호등 카드 + FourAxisRadar. 설계서 §16.3.

커밋: `feat: [P5-36] Overview Tab [JIT-117]`

## Task 37: JIT-118 — Code Deep Dive Tab

Treemap + Heatmap + Timeline 통합. 설계서 §16.2 Tab 3.

커밋: `feat: [P5-37] Code Deep Dive Tab [JIT-118]`

## Task 38: JIT-119 — Interview Tab 강화

3전략 그룹핑 + 카드형 UI. 설계서 §16.2 Tab 4.

커밋: `feat: [P5-38] Interview Tab 강화 [JIT-119]`

---

# Phase 6: 통합 테스트 + 정리 (5일)

> **참조:** `plan/v5-design/phase6-testing.md`

## Task 39: JIT-120 — Domain 단위 테스트 (커버리지 90%)

Identity, Scoring, Funnel 전체 엣지 케이스. 설계서 §17.2.

커밋: `test: [P6-39] Domain 단위 테스트 90% [JIT-120]`

## Task 40: JIT-121 — E2E 통합 테스트 (5가지 시나리오)

설계서 §17.3의 5가지 시나리오: Happy Path, Partial Data, Quality Gate Rejection, Worker Failure, Concurrent.

커밋: `test: [P6-40] E2E 통합 테스트 [JIT-121]`

## Task 41: JIT-122 — Playwright E2E

Overview Tab + Code Deep Dive Tab 렌더링. 설계서 §17.1.

커밋: `test: [P6-41] Playwright E2E [JIT-122]`

## Task 42: JIT-123 — 성능 벤치마크 + 문서화

pytest-benchmark + Mermaid 아키텍처 다이어그램 + README.

커밋: `docs: [P6-42] 성능 벤치마크 + 문서화 [JIT-123]`

---

# 의존성 그래프 요약

```
Phase 0 (JIT-82~85): 독립 → 나머지 모든 Phase의 기반
   82 → 83 → 84
              └→ 85

Phase 1 (JIT-86~91, JIT-124): Domain — Phase 0 완료 후
   86 → 87, 88, 89 (병렬)
   90, 91 (독립)
   124 (LinkedIn 모델, 독립)

Phase 2 (JIT-92~99, JIT-125): Infrastructure — Phase 0 완료 후, Phase 1과 병렬 가능
   92, 93 → Phase 0-3 의존
   94, 95, 96, 97, 98 → Phase 0-1 의존
   99 → Phase 0-3 의존
   125 (LinkedIn 어댑터) → Phase 0-3 + JIT-124 의존

Phase 3 (JIT-100~105): Application — Phase 1+2 완료 후
   100 → 독립
   101 → 87, 88, 89, 92, 93
   102 → 94, 95, 96
   103 → 94, 98
   104 → 100, 101, 102, 103
   105 → 104

Phase 4 (JIT-106~110): Questions — Phase 3 완료 후
   106 → 99, 104
   107 → 98, 106
   108 → 107
   109 → 108
   110 → 107, 108

Phase 5 (JIT-111~119): Output+FE — Phase 4 완료 후
   111 → 109
   112 → 91, 104
   113 → 112
   114, 115 → 112
   116 → 105
   117 → 113
   118 → 114, 115
   119 → 111

Phase 6 (JIT-120~123): Test — Phase 5 완료 후
   120 → 86~91
   121 → 104
   122 → 117, 118
   123 → 121
```

---

# 실행 옵션

**Plan complete and saved to `docs/plans/2026-02-15-jittda-v5-reconstruction.md`.**

**1. Subagent-Driven (this session)** — I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
