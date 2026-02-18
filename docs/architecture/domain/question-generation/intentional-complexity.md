---
title: "Intentional Complexity Strategy"
type: component
layer: domain
parent: "[[domain/question-generation/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-107"]
---

# Intentional Complexity (전략 B)

## 핵심 원리

**Halstead 난이도(D)와 순환 복잡도(M)가 국소적으로 매우 높은 구간**을 식별하여, 그 복잡도를 유지한 아키텍처적 이유를 묻는다.

복잡도가 높은 코드는 두 가지 가능성이 있다:
- 나쁜 코드 (리팩토링하지 못한 기술 부채)
- **의도적으로 복잡하게 유지한 합리적 이유가 있는 코드** (응집도, 보안, 원자성 등)

이 전략은 후보자가 자신의 코드에서 복잡도 높은 구간을 인식하고 그 이유를 설명할 수 있는지 검증한다.

## 분석 로직

```
Radon/Lizard로 함수별 복잡도 측정:
  1. 순환 복잡도(M) > 10 인 함수 → 높은 분기 복잡도
  2. Halstead 난이도(D) 상위 10% 구간 → 복잡한 연산 로직
  3. SonarQube 인지적 복잡도 경고 발생 구간
  → 위 조건 2개 이상 해당하는 함수를 질문 대상으로 선정
```

## 질문 예시

```
질문: "validateToken 메서드는 순환 복잡도가 매우 높습니다(분기문 15개).
      이 부분을 분리하지 않고 유지한 아키텍처적 이유가 있나요?"

검증 포인트:
  합격: "토큰 검증 로직이 분리되면 보안 감사 추적이 어려워집니다",
        "모든 케이스를 한 곳에서 처리해야 원자성이 보장됩니다",
        "응집도를 높이기 위해 분리하지 않았습니다"
  불합격: "복잡한 줄 몰랐습니다",
           "리팩토링할 시간이 없었습니다" (이유 없는 답변)
```

## 복잡도 측정 도구

| 도구 | 측정 지표 | 임계값 |
|------|-----------|--------|
| Radon | 순환 복잡도(CC), Halstead 난이도(D) | CC > 10 |
| Lizard | 함수 복잡도, 파라미터 수 | CC > 10 |
| SonarQube | 인지적 복잡도 | 경고 발생 |

수학적 기준:
```
Score_logic = 1 / (1 + a * M_avg + b * D_avg) * 100
# 복잡도가 낮을수록 고득점 → 역으로 높은 구간이 질문 대상
```

## 프롬프트 구성

```python
# infrastructure/llm/prompts/intentional_complexity.yaml
system: |
  당신은 시니어 코드 리뷰어입니다.
  복잡도가 높은 코드 구간에서 개발자의 아키텍처적 의도를 검증하는 질문을 작성하세요.

  규칙:
  - Chain-of-Thought: "이 복잡도가 의도적인지 판단하기 위해 먼저..."
  - 수치 근거 포함: "순환 복잡도 {cc}(분기문 {branches}개)"
  - 비개발자도 이해 가능한 answer_guide 작성
```

## 코드 예시 (QuestionCrafter)

```python
# application/question/question_crafter.py
async def craft_complexity_question(
    function_name: str,
    file_path: str,
    cyclomatic_complexity: float,
    halstead_difficulty: float,
    jd_context: dict,
) -> InterviewQuestion:
    """전략 B: 높은 복잡도 구간 기반 질문 생성"""
    topic = {
        "strategy": "intentional_complexity",
        "function_name": function_name,
        "file_path": file_path,
        "metrics": {
            "cyclomatic_complexity": cyclomatic_complexity,
            "halstead_difficulty": halstead_difficulty,
        },
    }
    return await generate_question(topic=topic, context=jd_context)
```

## 출력 필드에서 전략별 특성

| 필드 | Intentional Complexity 특성 |
|------|----------------------------|
| `strategy` | `"intentional_complexity"` |
| `intent` | "복잡도 유지의 아키텍처적 근거 검증" |
| `code_reference` | 높은 복잡도 함수의 파일:라인 |
| `red_flags` | `["모른다고 답변", "기술 부채 인정만 하고 개선 의지 없음"]` |
| `follow_up_triggers` | `["아키텍처 이유 설명 부재 시 → 리팩토링 방향을 제안해보라고 재질문"]` |

## 관련 지표

이 전략이 선정한 코드 구간의 복잡도 수치는 4대 지표 중 **논리력(30%)** 산출에도 직접 사용된다. 순환 복잡도 및 Halstead 난이도는 `Worker W7`이 처리한다.
