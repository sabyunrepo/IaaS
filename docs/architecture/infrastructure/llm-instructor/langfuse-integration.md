---
title: "Langfuse Integration"
type: component
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [langfuse, tracing, observability, prompt-versioning, observe]
parent: "[[llm-instructor/MOC]]"
depends-on:
  - "[[decisions/0005-instructor-pydantic]]"
linear: [JIT-98]
---

# Langfuse Integration

## 개요

> 모든 LLM 호출에 `@observe` 데코레이터를 적용하여 Langfuse에서 추적한다.
> 프롬프트는 Langfuse에서 런타임에 풀링(Langfuse-first 아키텍처)하며,
> 실행 지표(레이턴시, 토큰 수, 검증 재시도 횟수)를 자동 수집한다.

## 상세 설계

### 핵심 개념

**Langfuse-first 아키텍처**:
- 프롬프트 원본은 YAML 파일에 정의하지만, 런타임에는 Langfuse에서 로드
- YAML만 수정하면 실제 호출에 반영되지 않음 — Langfuse 업로드 필수
- `langfuse.get_prompt(name, label="production")`으로 런타임 프롬프트 획득
- `prompt.compile(**kwargs)`로 변수 치환하여 메시지 생성

**`@observe` 데코레이터**:
- 함수 실행 전/후를 자동으로 Langfuse Trace에 기록
- 입력 파라미터, 출력 결과, 레이턴시, 토큰 수 자동 캡처
- Instructor 재시도 시 각 시도도 개별 Span으로 기록

### 의존성

```toml
# pyproject.toml
[tool.poetry.dependencies]
langfuse = ">=2.57.0"
```

### 환경 변수

```bash
# .env
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # 또는 self-hosted URL
```

### 코드 예시

#### Langfuse 클라이언트 초기화

```python
# infrastructure/llm/langfuse_client.py
from langfuse import Langfuse
from functools import lru_cache
from core.config import settings

@lru_cache(maxsize=1)
def get_langfuse() -> Langfuse:
    """싱글톤 Langfuse 클라이언트"""
    return Langfuse(
        secret_key=settings.LANGFUSE_SECRET_KEY,
        public_key=settings.LANGFUSE_PUBLIC_KEY,
        host=settings.LANGFUSE_HOST,
    )
```

#### `@observe` + Instructor 통합

```python
# infrastructure/llm/instructor_client.py
import instructor
from langfuse.decorators import observe, langfuse_context
from infrastructure.llm.langfuse_client import get_langfuse
from infrastructure.llm.instructor_client import get_instructor_client
from infrastructure.llm.models.interview_question import InterviewQuestion

@observe(name="generate_interview_question")
async def generate_interview_question(
    topic: dict,
    context: dict,
    job_id: str,
) -> InterviewQuestion:
    """Langfuse 추적 + Instructor 구조화 출력"""
    langfuse = get_langfuse()
    client = get_instructor_client()

    # 1. Langfuse에서 런타임 프롬프트 풀링
    prompt = langfuse.get_prompt("question_craft_v5", label="production")

    # 2. Langfuse 컨텍스트에 추가 메타데이터 추가
    langfuse_context.update_current_trace(
        tags=["question-generation", topic.get("strategy", "unknown")],
        metadata={"job_id": job_id, "topic_id": topic.get("id")},
    )

    # 3. Instructor로 구조화 출력 생성
    result = await client.chat.completions.create(
        model=prompt.config.get("model", "kimi-k2.5"),
        response_model=InterviewQuestion,
        messages=prompt.compile(topic=topic, context=context),
        temperature=prompt.config.get("temperature", 0.7),
        max_retries=3,
    )
    return result
```

#### Langfuse Trace에 사용자 정의 점수 추가

```python
# 분석 품질 점수 추가 (QualityGate에서 호출)
@observe(name="quality_gate_evaluation")
async def evaluate_question_quality(
    question: InterviewQuestion,
    rubric: dict,
) -> dict:
    langfuse = get_langfuse()

    # 품질 평가 로직 실행 ...
    scores = compute_quality_scores(question, rubric)

    # Langfuse에 점수 기록
    langfuse_context.update_current_observation(
        output=scores,
        metadata={"retry_count": 0},
    )
    return scores
```

### Trace 계층 구조

```
Trace: job_analysis (job_id=JOB-123)
  ├── Span: forensic_supervisor
  │     ├── Span: collector_worker
  │     └── Span: identity_resolver
  ├── Span: logic_supervisor
  │     └── Span: ast_analyzer_worker
  └── Span: question_orchestrator
        ├── Generation: generate_interview_question (topic=negative_selection)
        │     ├── Input: {topic, context}
        │     ├── Output: InterviewQuestion(...)
        │     ├── Tokens: 1243 prompt + 387 completion
        │     └── Latency: 1.2s
        └── Generation: generate_interview_question (topic=code_evolution)
```

### 프롬프트 버전 관리

Langfuse UI에서 프롬프트 버전을 관리한다:

| 라벨 | 용도 |
|------|------|
| `production` | 현재 서비스 중인 버전 (기본 로드 대상) |
| `staging` | 테스트 중인 새 버전 |
| `experiment-v2` | A/B 테스트 중인 실험 버전 |

```python
# 특정 버전 명시적 로드 (A/B 테스트)
prompt_v2 = langfuse.get_prompt("question_craft_v5", label="experiment-v2")
```

### 모니터링 항목

Langfuse 대시보드에서 추적하는 핵심 지표:

| 지표 | 설명 |
|------|------|
| 프롬프트별 평균 레이턴시 | 버전 간 성능 비교 |
| `max_retries` 발생 빈도 | Pydantic 검증 실패율 — 프롬프트 품질 지표 |
| 토큰 비용 | 노드별 LLM 비용 분석 |
| 출력 스키마 필드별 오류율 | 구조화 출력 실패 패턴 분석 |

### 주의 사항

> **YAML 프롬프트 수정 후 반드시 Langfuse 업로드 필수**:
>
> ```bash
> docker compose exec backend python scripts/upload_prompts_to_langfuse.py --production
> ```
>
> YAML만 수정해도 Langfuse에 업로드하지 않으면 런타임에 반영되지 않는다.

## 관련 문서

- 상위: [[llm-instructor/MOC]]
- 연관: [[llm-instructor/instructor-setup]], [[llm-instructor/prompt-management]]
