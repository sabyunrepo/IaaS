---
title: "Instructor Setup"
type: component
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [instructor, kimi, openai-compat, pydantic, structured-output]
parent: "[[llm-instructor/MOC]]"
depends-on:
  - "[[decisions/0005-instructor-pydantic]]"
linear: [JIT-98]
---

# Instructor Setup

## 개요

> Instructor 1.7.0+을 Kimi K2.5 (OpenAI 호환 API)에 연결하는 클라이언트 설정.
> `from_provider()` 패턴으로 비동기 클라이언트를 초기화하고,
> Pydantic v2 모델을 출력 스키마로 사용하여 자동 타입 검증과 재시도를 보장한다.

## 상세 설계

### 핵심 개념

**Instructor의 역할**:
- OpenAI `chat.completions.create()`에 `response_model=` 파라미터를 추가하여 LLM 출력을 Pydantic 모델로 자동 파싱
- 파싱/검증 실패 시 `max_retries` 횟수만큼 LLM에 자동 재요청 (수동 retry 불필요)
- Tool Calling 방식 사용 — JSON 모드보다 더 신뢰할 수 있는 구조화 출력

**Kimi K2.5 연동**:
- OpenAI 호환 API를 사용하므로 `instructor.from_openai()` 또는 `AsyncOpenAI` 베이스 클라이언트 그대로 적용
- 모델 ID: `"kimi-k2.5"` (Moonshot AI 제공)
- base_url, api_key는 환경변수로 관리

### 의존성

```toml
# pyproject.toml
[tool.poetry.dependencies]
instructor = ">=1.7.0"
openai = ">=1.40.0"
pydantic = ">=2.6.0"
```

### 코드 예시

#### 비동기 클라이언트 초기화

```python
# infrastructure/llm/instructor_client.py
import instructor
from openai import AsyncOpenAI
from functools import lru_cache

@lru_cache(maxsize=1)
def get_instructor_client() -> instructor.AsyncInstructor:
    """싱글톤 Instructor 클라이언트 — 앱 전체에서 재사용"""
    base_client = AsyncOpenAI(
        api_key=settings.KIMI_API_KEY,
        base_url=settings.KIMI_BASE_URL,  # e.g. "https://api.moonshot.cn/v1"
    )
    return instructor.from_openai(base_client, mode=instructor.Mode.TOOLS)
```

#### Pydantic 출력 모델 정의

```python
# infrastructure/llm/models/interview_question.py
from pydantic import BaseModel, ConfigDict, Field

class InterviewQuestion(BaseModel):
    model_config = ConfigDict(strict=True)  # Pydantic v2 — 암묵적 타입 변환 금지

    question: str = Field(..., description="면접 질문 본문")
    intent: str = Field(..., description="이 질문을 하는 목적 (비개발자가 이해 가능하게)")
    depth_level: int = Field(..., ge=1, le=5, description="기술 깊이 레벨 (1=기초, 5=전문가)")
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="질문 근거가 된 코드/이력 레퍼런스 (GitHub permalink 등)"
    )
    follow_up_hints: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="예상 답변에서 추가로 파고들 포인트"
    )
```

#### 구조화 호출 패턴

```python
# infrastructure/llm/instructor_client.py
from pydantic import BaseModel
from typing import TypeVar

T = TypeVar("T", bound=BaseModel)

async def call_structured(
    response_model: type[T],
    messages: list[dict],
    model: str = "kimi-k2.5",
    temperature: float = 0.7,
    max_retries: int = 3,
) -> T:
    """Instructor 구조화 호출 — 범용 헬퍼"""
    client = get_instructor_client()
    return await client.chat.completions.create(
        model=model,
        response_model=response_model,
        messages=messages,
        temperature=temperature,
        max_retries=max_retries,
    )
```

#### Worker에서의 사용 예시 (W9 SkillExtractorWorker)

```python
# application/nodes/skill_extractor_worker.py
from infrastructure.llm.instructor_client import call_structured
from infrastructure.llm.models.skill_extraction import SkillExtraction

async def skill_extractor_worker(state: StackState) -> dict:
    ast_summary = await analysis_repository.get_ast_summary(state["ast_ref"])

    result: SkillExtraction = await call_structured(
        response_model=SkillExtraction,
        messages=[
            {"role": "system", "content": SKILL_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": ast_summary.to_prompt_text()},
        ],
        model="kimi-k2.5",
        temperature=0.3,  # 결정론적 스킬 추출
    )

    ref_id = await analysis_repository.save_skill_extraction(state["job_id"], result)
    return {"skill_extraction_ref": ref_id}
```

### 에러 처리 전략

| 에러 유형 | Instructor 동작 | 결과 |
|----------|----------------|------|
| Pydantic 검증 실패 | 실패 내용 + 원본 응답을 LLM에 재전송하여 수정 요청 | `max_retries`까지 재시도 |
| `max_retries` 초과 | `InstructorRetryException` 발생 | Worker의 `handle_error`에서 Graceful Degradation |
| API 호출 실패 (5xx) | openai 라이브러리 기본 retry 적용 (별도) | 최대 2회 재시도 |
| Rate Limit (429) | openai 라이브러리 기본 backoff 적용 | 지수 백오프 후 재시도 |

```python
# Worker 레벨 에러 처리
from instructor import InstructorRetryException

try:
    result = await call_structured(...)
except InstructorRetryException as e:
    logger.warning(f"Instructor max_retries 초과: {e.last_completion}")
    # Graceful Degradation: 최소한의 기본값 반환
    return self.handle_error(e, input_data)
```

## 관련 문서

- 상위: [[llm-instructor/MOC]]
- 의존: [[decisions/0005-instructor-pydantic]]
- 연관: [[llm-instructor/langfuse-integration]], [[llm-instructor/prompt-management]]
