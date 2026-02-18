---
title: "Negative Selection Strategy"
type: component
layer: domain
parent: "[[domain/question-generation/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-107"]
---

# Negative Selection (전략 A)

## 핵심 원리

코드에서 **사용될 법하지만 사용되지 않은 패턴/기술**을 AST 분석으로 감지하여, 후보자가 해당 기술을 의도적으로 선택하지 않은 이유를 질문한다.

이 전략은 두 가지를 판별한다:
- **합격 신호**: 후보자가 트레이드오프를 이해하고 의식적 선택을 했음
- **불합격 신호**: 해당 기술을 몰라서 사용하지 못했음 (단순 무지)

AI가 대신 작성한 코드라면, AI는 대안 기술을 나열할 수 있지만 "왜 그 코드에서 그 선택을 했는지"의 맥락적 이유는 답변하지 못한다.

## 분석 로직

```
AST 분석 결과에서:
  1. 동기(sync) I/O 코드 감지 → async/await 미사용 질문
  2. 단일 스레드 처리 → 병렬 처리 미사용 질문
  3. 직접 DB 쿼리 → ORM/Repository 패턴 미사용 질문
  4. 예외 처리 없는 외부 API 호출 → Circuit Breaker 미사용 질문
  5. 전역 상태 변수 → 불변 데이터 구조 미사용 질문
```

## 질문 예시

```
질문: "async/await를 적용하지 않고 동기식으로 처리하셨습니다.
      동시성 이슈를 우려하여 일부러 그렇게 설계하신 건가요?"

검증 포인트:
  합격: "데이터 순서가 중요해서 순차 처리가 필요했습니다",
        "해당 작업의 I/O 대기 시간이 짧아 비동기 오버헤드가 더 컸습니다"
  불합격: "그냥 짜다 보니 그렇게 됐습니다",
           "async를 어떻게 쓰는지 잘 몰랐습니다"
```

## 프롬프트 구성

```python
# infrastructure/llm/prompts/negative_selection.yaml
system: |
  당신은 시니어 기술 면접관입니다.
  후보자의 코드에서 "사용될 법하지만 사용되지 않은" 패턴을 발견하여
  의도적 선택인지 단순 무지인지를 판별하는 질문을 작성하세요.

  규칙:
  - 일반적/교과서적 질문은 제외
  - 해당 코드의 구체적 맥락(파일명, 함수명)을 질문에 포함
  - 비개발자 면접관도 판단 기준을 이해할 수 있는 answer_guide 작성

few_shot_examples:
  - input:
      missing_pattern: "async/await"
      code_context: "user_service.py:45, get_all_users() 함수가 동기 DB 쿼리 수행"
    output:
      question_text: "get_all_users 함수에서 async/await 없이 동기 방식으로 DB를 조회하셨습니다. 이 결정의 이유가 있으신가요?"
      intent: "동시성 개념 이해 및 의도적 설계 판단"
      expected_answer_guide: "합격: 순서 보장 필요성 또는 I/O 특성 설명 / 불합격: 모른다고 답변"
```

## 코드 예시 (QuestionCrafter)

```python
# application/question/question_crafter.py
async def craft_negative_selection_question(
    missing_pattern: str,
    code_context: str,
    jd_context: dict,
) -> InterviewQuestion:
    """전략 A: 미사용 패턴 기반 질문 생성"""
    topic = {
        "strategy": "negative_selection",
        "missing_pattern": missing_pattern,
        "code_context": code_context,
    }
    return await generate_question(topic=topic, context=jd_context)
```

## 출력 필드에서 전략별 특성

| 필드 | Negative Selection 특성 |
|------|------------------------|
| `strategy` | `"negative_selection"` |
| `intent` | "의도적 미사용인지 단순 무지인지 판별" |
| `code_reference` | 미사용 패턴이 감지된 파일:라인 |
| `red_flags` | `["모른다고 답변", "사용 방법 설명만 함"]` |
| `follow_up_triggers` | `["트레이드오프 설명 부재 시 → 왜 그 방식을 선택했는지 재질문"]` |
