# Vantict Sniper v4.0 - 단위 테스트 계획서

> 전체 워크플로우를 단위별로 분해하여 체계적인 테스트 진행

---

## 1. 테스트 단위 분해 (Phase별)

### 전체 파이프라인 개요

```
Phase 0: Input Enrichment (enrich_input)
    ↓
Phase 1: Planning (create_execution_plan)
    ↓
Phase 2: Parallel Analysis
    ├── analyze_documents
    ├── analyze_code (4-Channel)
    └── analyze_jd
    ↓
Phase 3: Question Generation (Multi-Agent)
    ├── 3a. select_topics
    ├── 3b. craft_question (×25 병렬)
    ├── 3c. enhance_terminology
    ├── 3d. craft_evaluation_scenarios
    ├── 3e. design_follow_ups
    ├── 3f. generate_interviewer_notes
    ├── 3g. generate_decision_guide
    └── 3h. review_questions (+ revise_questions)
    ↓
Phase 4: Finalization (finalize_output)
```

---

## 2. 테스트 단위 상세

### 2.1 Phase 0: Input Enrichment

| 테스트 ID | 테스트 항목 | 입력 | 예상 출력 | 토큰 비용 |
|-----------|-------------|------|----------|----------|
| P0-01 | PDF 텍스트 추출 | resume.pdf | 텍스트 문자열 | 0 |
| P0-02 | GitHub URL 추출 | PDF 텍스트 | `["https://github.com/..."]` | 0 |
| P0-03 | LinkedIn URL 추출 | PDF 텍스트 | `"https://linkedin.com/in/..."` | 0 |
| P0-04 | LinkedIn 프로필 수집 | linkedin_url | LinkedInProfile dict | ~$0.01 (Bright Data) |
| P0-05 | GitHub User/Org 검증 | github_urls | personal_repos, skipped_org_repos | 0 (GitHub API) |
| P0-06 | available_analyses 결정 | enriched_input | `["jd_analysis", ...]` | 0 |
| P0-07 | 문서 파싱 실패 처리 | 손상된 PDF | document_errors 필드에 기록, 계속 진행 | 0 |

**테스트 스크립트 위치**: `backend/tests/test_input_enrichment.py`

```python
# P0-05 테스트 예시: GitHub User/Org 검증
async def test_github_user_org_validation():
    """조직 URL은 건너뛰고, 개인 레포만 반환"""
    from app.services.github_service import GitHubService

    svc = GitHubService()
    result = await svc.infer_candidate_username(
        github_urls=[
            "https://github.com/42cats/crime-cat",  # Organization
            "https://github.com/sabyunrepo/Sesami",  # User
        ],
        candidate_name="BYUN SANGHOON"
    )

    assert result["username"] == "sabyunrepo"
    assert result["confidence"] == "high"
    assert "https://github.com/42cats/crime-cat" in result["skipped_org_repos"]
    assert "https://github.com/sabyunrepo/Sesami" in result["personal_repos"]
```

---

### 2.2 Phase 1: Planning

| 테스트 ID | 테스트 항목 | 입력 | 예상 출력 | 토큰 비용 |
|-----------|-------------|------|----------|----------|
| P1-01 | JD 기술스택 추출 | jd_text | `["Python", "FastAPI", ...]` | ~500 토큰 |
| P1-02 | GitHub 워크로드 추정 | github_urls | repo별 size, languages | 0 (GitHub API) |
| P1-03 | 실행 계획 생성 | enriched_input | ExecutionPlan dict | ~500 토큰 |
| P1-04 | phases 활성화 결정 | available_analyses | `[{name, enabled}, ...]` | 0 |

**테스트 스크립트 위치**: `backend/tests/test_planning.py`

---

### 2.3 Phase 2: Parallel Analysis

#### 2.3.1 Document Analysis

| 테스트 ID | 테스트 항목 | 입력 | 예상 출력 | 토큰 비용 |
|-----------|-------------|------|----------|----------|
| P2D-01 | Docling PDF 파싱 | resume.pdf | Markdown 텍스트 | 0 |
| P2D-02 | pymupdf4llm 폴백 | Docling 실패 PDF | Markdown 텍스트 | 0 |
| P2D-03 | LLM 프로필 추출 | parsed_text | CandidateProfile | ~2,000 토큰 |
| P2D-04 | LinkedIn 프로필 통합 | linkedin_profile | 통합된 프로필 | ~500 토큰 |

**테스트 스크립트 위치**: `backend/tests/test_document_analysis.py`

#### 2.3.2 Code Analysis (4-Channel)

| 테스트 ID | 테스트 항목 | 입력 | 예상 출력 | 토큰 비용 |
|-----------|-------------|------|----------|----------|
| P2C-01 | JD 매칭 레포 필터링 | github_urls, jd_tech_stack | matched_repos | 0 (GitHub API) |
| P2C-02 | PyDriller diff 추출 | repo_url, author | commits, files | 0 |
| P2C-03 | AST 분석 (Python) | .py 파일들 | functions, classes, patterns | 0 |
| P2C-04 | AST 분석 (JS/TS) | .ts 파일들 | functions, classes | 0 |
| P2C-05 | LLM 코드 의미 분석 | ranked_files | notable_implementations | ~5,000 토큰/레포 |
| P2C-06 | Channel B: OSS PR | username | merged_prs | 0 (GitHub API) |
| P2C-07 | Channel C: Issues | username | issues | 0 (GitHub API) |
| P2C-08 | Channel D: Reviews | username | code_reviews | 0 (GitHub API) |
| P2C-09 | 4-Channel 통합 | all_channels | aggregated_result | 0 |

**테스트 스크립트 위치**: `backend/tests/test_code_analysis.py`

#### 2.3.3 JD Analysis

| 테스트 ID | 테스트 항목 | 입력 | 예상 출력 | 토큰 비용 |
|-----------|-------------|------|----------|----------|
| P2J-01 | JD 파싱 | jd_text | JDAnalysis | ~1,500 토큰 |
| P2J-02 | requirements 추출 | jd_text | `[{skill, category}, ...]` | 포함 |
| P2J-03 | company_culture 추출 | jd_text | `["...", ...]` | 포함 |

**테스트 스크립트 위치**: `backend/tests/test_jd_analysis.py`

---

### 2.4 Phase 3: Question Generation

| 테스트 ID | 테스트 항목 | 입력 | 예상 출력 | 토큰 비용 |
|-----------|-------------|------|----------|----------|
| P3a-01 | 토픽 선정 | aggregated_analysis | 25개 토픽 | ~3,000 토큰 |
| P3b-01 | 단일 질문 생성 | topic, analysis | InterviewQuestion | ~1,500 토큰 |
| P3b-02 | 25개 질문 병렬 생성 | 25 topics | 25 questions | ~37,500 토큰 |
| P3c-01 | 용어 설명 생성 | questions | terminology_map | ~2,000 토큰 |
| P3d-01 | 평가 시나리오 생성 | questions | evaluation_scenarios | ~3,000 토큰 |
| P3e-01 | 꼬리질문 설계 | questions | follow_ups | ~2,500 토큰 |
| P3f-01 | 면접관 노트 생성 | questions | interviewer_notes | ~2,000 토큰 |
| P3g-01 | 결정 가이드 생성 | aggregated | decision_guide | ~2,000 토큰 |
| P3h-01 | 품질 검토 | questions | review_result | ~3,000 토큰 |
| P3h-02 | 질문 수정 | questions, feedback | revised_questions | ~2,000 토큰 |

**테스트 스크립트 위치**: `backend/tests/test_question_generation.py`

---

### 2.5 Phase 4: Finalization

| 테스트 ID | 테스트 항목 | 입력 | 예상 출력 | 토큰 비용 |
|-----------|-------------|------|----------|----------|
| P4-01 | Hallucination 검증 | questions | validated_questions | ~1,000 토큰 |
| P4-02 | 용어집 통합 | questions | full_glossary | 0 |
| P4-03 | 후보자 요약 생성 | analysis | candidate_summary | ~1,500 토큰 |
| P4-04 | 면접관 가이드 생성 | questions | interviewer_guide | ~1,500 토큰 |
| P4-05 | S3 저장 | final_script | s3_path | 0 |

**테스트 스크립트 위치**: `backend/tests/test_finalization.py`

---

## 3. 토큰 최적화 전략

### 3.1 단계별 테스트 분리

**원칙**: 각 Phase를 독립적으로 테스트하여 불필요한 LLM 호출 방지

```
# ❌ 비효율적 (전체 파이프라인)
pytest tests/test_workflow.py  # ~70,000 토큰

# ✅ 효율적 (Phase별 분리)
pytest tests/test_input_enrichment.py  # ~0 토큰
pytest tests/test_planning.py          # ~1,000 토큰
pytest tests/test_code_analysis.py     # ~5,000 토큰
pytest tests/test_question_generation.py --topic-only  # ~3,000 토큰
```

### 3.2 Mock/Fixture 활용

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_enriched_input():
    """Phase 0 결과를 미리 준비 (Phase 1+ 테스트용)"""
    return {
        "raw_input": {...},
        "github_urls": ["https://github.com/user/repo"],
        "linkedin_profile": {"full_name": "Test User"},
        "available_analyses": ["jd_analysis", "document_analysis", "code_analysis"],
    }

@pytest.fixture
def mock_aggregated_analysis():
    """Phase 2 결과를 미리 준비 (Phase 3 테스트용)"""
    return {
        "document_analysis": {...},
        "code_analysis": {...},
        "jd_analysis": {...},
    }

@pytest.fixture
def mock_llm_service():
    """LLM 호출 모킹 (토큰 0)"""
    mock = AsyncMock()
    mock.run.return_value.data = MockResponse()
    return mock
```

### 3.3 캐시 활용

```python
# LiteLLM Redis 캐시 활용
# 동일 프롬프트 재테스트 시 API 호출 0

# 테스트 환경에서 캐시 강제 활성화
import litellm
litellm.cache = litellm.Cache(type="redis", host="localhost", port=6379)

# 캐시 히트 확인
@pytest.mark.parametrize("run", range(3))
async def test_with_cache(run):
    result = await llm_service.run(SAME_PROMPT)
    # run 1: API 호출 (캐시 미스)
    # run 2, 3: 캐시 히트 (토큰 0)
```

### 3.4 토큰 예산 추정

| Phase | 예상 토큰 | 예상 비용 (GPT-4o) |
|-------|----------|-------------------|
| Phase 0 | ~0 | $0.00 |
| Phase 1 | ~1,000 | $0.01 |
| Phase 2 (docs) | ~2,500 | $0.025 |
| Phase 2 (code) | ~15,000 | $0.15 |
| Phase 2 (jd) | ~1,500 | $0.015 |
| Phase 3 | ~55,000 | $0.55 |
| Phase 4 | ~5,000 | $0.05 |
| **총계** | **~80,000** | **~$0.80/job** |

---

## 4. 테스트 실행 순서

### 4.1 권장 테스트 순서

```bash
# 1단계: 외부 의존성 없는 유틸리티 테스트
pytest tests/test_utils.py -v

# 2단계: Phase 0 (API 호출 최소)
pytest tests/test_input_enrichment.py -v

# 3단계: Phase 1 (LLM 1회)
pytest tests/test_planning.py -v --mock-llm  # 모킹 모드
pytest tests/test_planning.py -v             # 실제 LLM

# 4단계: Phase 2 개별 (병렬 가능)
pytest tests/test_document_analysis.py -v
pytest tests/test_code_analysis.py -v
pytest tests/test_jd_analysis.py -v

# 5단계: Phase 3 (가장 비용 큼 - 신중히)
pytest tests/test_question_generation.py -v --topic-only  # 토픽만
pytest tests/test_question_generation.py -v -k "craft_question"  # 질문 1개만

# 6단계: Phase 4
pytest tests/test_finalization.py -v

# 7단계: E2E 통합 (최종 확인용)
pytest tests/test_e2e_workflow.py -v
```

### 4.2 CI/CD 환경 설정

```yaml
# .github/workflows/test.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Unit Tests (Mock LLM)
        run: pytest tests/ -v --mock-llm -x

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - name: Integration Tests (Real LLM)
        run: pytest tests/test_e2e_workflow.py -v
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

---

## 5. 디버깅 및 프롬프트 개발 워크플로우

### 5.1 프롬프트 디버깅 프로세스

```
1. 문제 발견
   └─ 로그 확인: docker logs vantict-worker
   └─ Langfuse 트레이스 확인

2. 프롬프트 격리
   └─ 해당 Activity만 단독 테스트
   └─ 입력 데이터 덤프 (JSON)

3. 프롬프트 수정
   └─ backend/app/prompts/*.yaml 편집
   └─ Langfuse에서 버전 관리

4. 단위 테스트
   └─ pytest tests/test_<activity>.py -v -k "specific_test"

5. 통합 확인
   └─ Docker에서 해당 Phase만 재실행
```

### 5.2 Activity 단독 테스트 템플릿

```python
# scratchpad/test_activity_isolated.py
"""단일 Activity 격리 테스트"""
import asyncio
import json
from temporalio import activity as temporal_activity

# Heartbeat 모킹
temporal_activity.heartbeat = lambda msg: print(f"♥ {msg}")

async def test_isolated():
    # 1. 입력 데이터 로드 (이전 Phase 결과)
    with open("/tmp/enriched_input.json") as f:
        enriched_input = json.load(f)

    # 2. 테스트 대상 Activity import
    from app.workflows.activities.planning import create_execution_plan

    # 3. 실행
    result = await create_execution_plan("test-job-001", enriched_input)

    # 4. 결과 저장
    with open("/tmp/execution_plan.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(test_isolated())
```

### 5.3 Langfuse 트레이스 활용

```python
# 프롬프트 버전 관리
from langfuse import Langfuse

langfuse = Langfuse()

# 프롬프트 가져오기 (버전 지정)
prompt = langfuse.get_prompt("select_topics", version=3)

# 트레이스 생성
trace = langfuse.trace(name="test_select_topics", metadata={"test": True})

# LLM 호출
generation = trace.generation(
    name="select_topics",
    model="gpt-4o",
    input=prompt.compile(context=analysis),
)

result = await llm.run(prompt.compile(context=analysis))

generation.end(output=result)
trace.update(output={"topics_count": len(result)})
```

---

## 6. Docker 테스트 환경

### 6.1 테스트용 Docker 명령

```bash
# 서비스 시작
make up

# 백엔드 컨테이너 진입
docker exec -it vantict-backend bash

# Python 경로 확인
which python  # /usr/local/bin/python

# 테스트 실행 (컨테이너 내부)
cd /app
python -m pytest tests/test_input_enrichment.py -v

# 단독 Activity 테스트
python scratchpad/test_activity_isolated.py
```

### 6.2 테스트 파일 복사

```bash
# 호스트 → 컨테이너
docker cp ./test_data/resume.pdf vantict-backend:/tmp/
docker cp ./test_data/portfolio.pdf vantict-backend:/tmp/

# 컨테이너 → 호스트
docker cp vantict-backend:/tmp/result.json ./test_output/
```

### 6.3 로그 확인

```bash
# Worker 로그
docker logs -f vantict-worker

# 특정 Phase 로그 필터링
docker logs vantict-worker 2>&1 | grep "Phase 2"

# Temporal Web UI
open http://localhost:8233
```

---

## 7. 테스트 체크리스트

### Phase 0: Input Enrichment
- [ ] P0-01: PDF 텍스트 추출
- [ ] P0-02: GitHub URL 추출 (정규식)
- [ ] P0-03: LinkedIn URL 추출
- [ ] P0-04: Bright Data LinkedIn 프로필
- [ ] P0-05: GitHub User/Org 검증 ✅ (PR #37)
- [ ] P0-06: available_analyses 결정
- [ ] P0-07: 문서 파싱 실패 graceful 처리 ✅ (PR #37)

### Phase 1: Planning
- [ ] P1-01: JD 기술스택 추출
- [ ] P1-02: GitHub 워크로드 추정
- [ ] P1-03: 실행 계획 생성
- [ ] P1-04: phases 활성화 결정

### Phase 2: Analysis
- [ ] P2D-01~04: Document Analysis
- [ ] P2C-01~09: Code Analysis (4-Channel)
- [ ] P2J-01~03: JD Analysis

### Phase 3: Question Generation
- [ ] P3a-01: 토픽 선정
- [ ] P3b-01~02: 질문 생성
- [ ] P3c-01: 용어 설명
- [ ] P3d-01: 평가 시나리오
- [ ] P3e-01: 꼬리질문
- [ ] P3f-01: 면접관 노트
- [ ] P3g-01: 결정 가이드
- [ ] P3h-01~02: 품질 검토/수정

### Phase 4: Finalization
- [ ] P4-01: Hallucination 검증
- [ ] P4-02: 용어집 통합
- [ ] P4-03: 후보자 요약
- [ ] P4-04: 면접관 가이드
- [ ] P4-05: S3 저장

---

## 8. 빠른 참조

### 테스트 파일 위치
```
backend/tests/
├── conftest.py                    # Fixtures
├── test_input_enrichment.py       # Phase 0
├── test_planning.py               # Phase 1
├── test_document_analysis.py      # Phase 2
├── test_code_analysis.py          # Phase 2
├── test_jd_analysis.py            # Phase 2
├── test_question_generation.py    # Phase 3
├── test_quality_review.py         # Phase 3
├── test_finalization.py           # Phase 4
└── test_e2e_workflow.py           # E2E
```

### 자주 사용하는 명령
```bash
# Phase별 테스트
pytest tests/test_input_enrichment.py -v

# 특정 테스트만
pytest tests/test_code_analysis.py -v -k "test_github_user_org"

# Mock LLM 모드
pytest tests/ --mock-llm -v

# Docker 내 테스트
docker exec -it vantict-backend pytest tests/test_input_enrichment.py -v

# 단독 Activity 테스트
docker exec -it vantict-backend python /tmp/test_activity.py
```

### 환경 변수
```bash
# 테스트 모드 활성화
export VANTICT_TEST_MODE=true

# LLM 캐시 강제 활성화
export LITELLM_CACHE=redis

# GitHub API 토큰 (rate limit 회피)
export GITHUB_TOKEN=ghp_xxxxx
```

---

*작성일: 2026-02-04*
*마지막 업데이트: PR #37 (GitHub User/Org Validation) 반영*
