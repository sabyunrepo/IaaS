---
title: "Three Strategies"
type: component
layer: domain
parent: "[[domain/question-generation/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-107"]
depends-on: ["[[infrastructure/llm-instructor/MOC]]"]
---

# 3전략 질문 생성

## 개요

Jittda v5.0은 후보자 코드에서 면접 질문을 도출하는 3가지 고유 전략을 사용한다. 각 전략은 서로 다른 분석 로직을 가지며, 코드를 실제로 작성하고 이해한 사람만이 답변할 수 있는 질문을 생성하는 것이 목표다.

## 3전략 비교 테이블

| 항목 | 전략 A: Negative Selection | 전략 B: Intentional Complexity | 전략 C: Code Evolution |
|------|--------------------------|-------------------------------|------------------------|
| **핵심 원리** | 사용하지 않은 기술/패턴을 질문 | 높은 복잡도 구간의 의도를 질문 | 코드 변화 과정을 질문 |
| **분석 로직** | AST로 미사용 패턴/기술 감지 | Halstead D + 순환 복잡도 높은 구간 | Git Churn 높은 구간, 대규모 리팩토링 |
| **검증 목적** | 의도적 선택 vs 단순 무지 판별 | 아키텍처 결정의 근거 검증 | 직접 작성/유지보수 진정성 검증 |
| **합격 답변** | 트레이드오프 설명 가능 | 구체적 아키텍처 이유 제시 | 구체적 문제와 해결 과정 설명 |
| **불합격 답변** | "그냥 짜다 보니 그렇게 됐습니다" | "복잡한 줄 몰랐습니다" | 최종 결과물만 설명 |
| **AI 우회 불가 이유** | AI도 대안을 나열만 할 수 있음; 선택 이유는 맥락 없이 답 불가 | AI는 코드를 쓰지만 복잡도 유지 의도는 모름 | AI는 수정 역사의 맥락을 모름 |
| **`strategy` 값** | `"negative_selection"` | `"intentional_complexity"` | `"evolution"` |

## 각 전략의 출력 모델

세 전략 모두 동일한 `InterviewQuestion` Pydantic 모델로 출력한다:

```python
# domain/question/models.py
class InterviewQuestion(BaseModel):
    model_config = ConfigDict(strict=True)

    question_id: str
    category: str      # technical_depth | execution_ownership | communication | role_fit | risk_flags
    strategy: str      # negative_selection | intentional_complexity | evolution
    difficulty: str    # easy | medium | hard
    question_text: str = Field(min_length=20, max_length=500)
    intent: str = Field(description="이 질문의 의도 (비개발자용)")
    code_reference: str | None = Field(description="관련 코드 파일:라인")
    expected_answer_guide: str = Field(description="비개발자도 이해 가능한 예상 답변 가이드")
    red_flags: list[str] = Field(description="주의해야 할 답변 패턴")
    follow_up_triggers: list[str] = Field(description="파생 질문 트리거 조건")
    terminology: list[dict] = Field(description="질문에 포함된 전문 용어 설명")
```

## 프롬프트 전략

각 전략은 다음 프롬프트 기법을 조합하여 사용한다:

| 기법 | 적용 전략 | 효과 |
|------|-----------|------|
| Few-shot | 전 전략 | 2-3개 예시로 출력 형식/품질 가이드 |
| Negative Prompting | Negative Selection | "일반적/교과서적 질문은 제외" |
| Chain-of-Thought | Intentional Complexity | 복잡도 해석 단계별 추론 유도 |
| Fact-Grounded | 전 전략 | "결정론적 수치를 참조하여" 전제 |

## LLM 연동 (Instructor + Langfuse)

각 전략의 QuestionCrafter는 Instructor를 통해 구조화된 출력을 생성한다. 프롬프트는 Langfuse에서 런타임 관리되며, 장애 시 YAML fallback을 사용한다.

```python
# infrastructure/llm/instructor_client.py
@observe(name="generate_interview_question")
async def generate_question(topic: dict, context: dict) -> InterviewQuestion:
    prompt = langfuse.get_prompt("question_craft_v5", label="production")
    result = await client.chat.completions.create(
        model=prompt.config.get("model", "kimi-k2.5"),
        response_model=InterviewQuestion,
        messages=prompt.compile(topic=topic, context=context),
        max_retries=3,  # Pydantic 검증 실패 시 자동 재시도
    )
    return result
```

## 세부 문서

- [[domain/question-generation/negative-selection]] — 전략 A 상세
- [[domain/question-generation/intentional-complexity]] — 전략 B 상세
- [[domain/question-generation/code-evolution]] — 전략 C 상세
