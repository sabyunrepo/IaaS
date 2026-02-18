---
title: "ADR-0005: Instructor + Pydantic for Structured LLM Output"
type: adr
status: accepted
date: 2026-02-15
decision-makers: ["@sabyun"]
related-adrs: ["[[decisions/0001-langgraph-over-temporal]]", "[[decisions/0003-ddd-four-layers]]"]
impacts: ["[[infrastructure/llm-instructor/MOC]]"]
tags: [instructor, pydantic, llm, structured-output, tool-calling]
---

# ADR-0005: Instructor + Pydantic for Structured LLM Output

## 컨텍스트

v5.0에서 LLM 호출은 면접 질문 생성, JD 관련도 스코어링, 스킬 추출(W9), API 깊이 분석(W10), 아키텍처 평가(W11), CLAVE 스타일로메트리(W4) 등 다수의 노드에서 발생한다. 모든 LLM 호출의 출력은 다음 노드로 전달되거나 DB에 저장되므로 구조화된 형태여야 한다.

v4.0에서는 LLM 출력을 raw JSON 문자열로 받아 수동으로 파싱하는 방식을 사용했다. 이 방식은 LLM이 잘못된 형식의 JSON을 반환할 때 예외 처리가 복잡하고, 재시도 로직을 수동으로 구현해야 했다.

v5.0 설계에서 구조화 출력 라이브러리 선택이 필요했다. sabyun이 직접 요구: "구조화 출력 — Instructor/Pydantic 기반 Tool Calling".

소스: `plan/v5-design/phase2-infrastructure.md` §12.3, `jittda_doc/jittda-v5-brainstorming-log.md` §3 Q2, §17

---

## 결정 옵션

### 옵션 A: Raw JSON 파싱

LLM에 JSON 출력을 요청하고 `json.loads()`로 파싱. 검증은 수동으로 수행.

**장점:**
- 추가 라이브러리 불필요

**단점:**
- LLM의 비정형 JSON 출력 시 파싱 실패
- 검증 로직을 수동으로 작성해야 함
- 재시도 로직 직접 구현 필요
- 출력 스키마가 코드에서 명시적으로 드러나지 않아 가독성 저하

### 옵션 B: Instructor + Pydantic (선택)

Instructor 라이브러리가 Pydantic 모델 기반으로 LLM Tool Calling을 자동 처리. 검증 실패 시 자동 재시도.

**장점:**
- 상용 API(Kimi K2.5) 완전 호환 — OpenAI 호환 API를 사용하는 모든 모델에 적용 가능
- Pydantic v2 자동 타입 검증 — 모델 정의가 곧 출력 스키마 문서
- `max_retries=3` 내장 — 검증 실패 시 LLM에 자동으로 재요청
- Tool Calling 네이티브 지원 — JSON 모드보다 더 신뢰할 수 있는 구조화 출력
- Langfuse 통합 시 `@observe` 데코레이터와 자연스럽게 결합

**단점:**
- 추가 패키지 의존성 (`instructor>=1.7.0`)

### 옵션 C: Outlines

FSM(유한 상태 머신) 기반 제어로 토큰 수준에서 출력 형식 강제.

**장점:**
- 로컬 모델에서 완전한 형식 보장

**단점:**
- 상용 API(Kimi K2.5) 미지원 — 로컬 모델 전용
- v5.0 기술 스택과 미정합

### 옵션 D: Marvin

객체 지향적 추상화 기반 데이터 추출.

**장점:**
- 간단한 데이터 추출에 직관적

**단점:**
- 상용 API 호환성은 있으나 Tool Calling 지원 제한적
- 재시도 로직 내장 없음
- Pydantic v2 네이티브 지원 부족

### 옵션 E: LangChain Output Parser

LangChain의 `PydanticOutputParser` 사용.

**장점:**
- LangChain 생태계와 통합

**단점:**
- v5.0은 LangGraph를 사용하지만 LangChain의 Output Parser는 별도 패키지
- Instructor 대비 Tool Calling 지원이 제한적
- 재시도 로직이 명시적이지 않음

---

## 결정

**옵션 B: Instructor + Pydantic**

브레인스토밍 Q2 확정: "Instructor — Pydantic 기반 Tool Calling, 상용 API 사용 시 최적"

---

## 비교 요약

| 기준 | Instructor + Pydantic | Outlines | Marvin | LangChain Parser |
|------|----------------------|----------|--------|-----------------|
| 상용 API 호환 (Kimi K2.5) | 최적 | 로컬 전용 | 가능 | 가능 |
| Pydantic v2 자동 검증 | 네이티브 | 수동 | 부분 | 부분 |
| 자동 재시도 | `max_retries=3` 내장 | 없음 | 없음 | 없음 |
| Tool Calling | 네이티브 | 없음 | 부분 | 제한적 |

---

## 구현 패턴

### Langfuse 통합 구조화 출력

```python
# infrastructure/llm/instructor_client.py
import instructor
from langfuse.decorators import observe

@observe(name="generate_interview_question")
async def generate_question(topic: dict, context: dict) -> InterviewQuestion:
    """Langfuse 추적 + Instructor 구조화 출력"""
    # 1. Langfuse에서 프롬프트 가져오기 (Langfuse-first 아키텍처)
    prompt = langfuse.get_prompt("question_craft_v5", label="production")

    # 2. Instructor로 구조화 출력 생성
    result = await client.chat.completions.create(
        model=prompt.config.get("model", "kimi-k2.5"),
        response_model=InterviewQuestion,
        messages=prompt.compile(topic=topic, context=context),
        temperature=prompt.config.get("temperature", 0.7),
        max_retries=3,  # Pydantic 검증 실패 시 LLM에 자동 재요청
    )
    return result
```

### Pydantic 출력 모델 예시

```python
from pydantic import BaseModel, ConfigDict

class AnalysisResult(BaseModel):
    model_config = ConfigDict(strict=True)  # Pydantic v2

    score: float
    evidence: list[str]
    confidence: float
```

### 적용 노드 목록

| Worker | LLM 사용 | Instructor 역할 |
|--------|----------|----------------|
| W4 CLAVEWorker | O | 스타일로메트리 패턴 추출 |
| W9 SkillExtractorWorker | O | 기술 스택 매핑 구조화 |
| W10 APIDepthAnalyzerWorker | O | API 활용 깊이 평가 |
| W11 ArchitectureEvaluatorWorker | O | 디자인 패턴/SOLID 평가 |
| 질문 생성 (QuestionCrafter) | O | 면접 질문 생성 |
| Enhancement Agents | O | 질문 개선 |

---

## 근거

1. **상용 API 호환**: Kimi K2.5는 OpenAI 호환 API를 사용 — Instructor의 `from_openai()` 패턴이 직접 적용됨
2. **자동 재시도**: `max_retries=3`으로 LLM 출력 검증 실패 시 자동으로 재요청 — 수동 retry 로직 불필요
3. **Pydantic v2 정합**: 도메인 모델과 동일한 Pydantic v2 스타일로 출력 스키마 정의 — 코드 일관성 유지
4. **Langfuse 통합**: `@observe` 데코레이터로 모든 LLM 호출이 자동 추적 — 프롬프트 관리와 출력 검증이 단일 위치에서 관리됨
5. **DDD 정합**: Instructor 클라이언트는 `infrastructure/llm/` 레이어에 위치 — Domain Layer는 LLM 호출 방식에 무관

---

## 결과

- `instructor>=1.7.0` 의존성을 `pyproject.toml`에 추가 (JIT-98)
- `infrastructure/llm/instructor_client.py`에 Langfuse 통합 클라이언트 구현 (JIT-98)
- LLM을 사용하는 모든 Worker(W4, W9, W10, W11)와 질문 생성 노드에서 Instructor 사용 통일
- LLM 출력 스키마는 Pydantic v2 `BaseModel`로 정의 (`ConfigDict(strict=True)` 기본)

---

## 관련 ADR

- ADR-0001: LangGraph (Instructor로 구조화된 출력이 LangGraph State에 안전하게 저장됨)
- ADR-0003: DDD 4-Layer (Instructor 클라이언트 위치: `infrastructure/llm/`)
- ADR-0004: Reference Passing (Instructor 출력 결과도 DB 저장 후 ID만 State에 전달)
