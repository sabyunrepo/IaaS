# Phase 4: 질문 생성 + Enhancement

> 원본 설계서: `plan/2026-02-15-v5-final-design.md`
> Linear 티켓: JIT-106 ~ JIT-110

## Linear 티켓 매핑

| 티켓 | 제목 | 참조 섹션 |
|------|------|----------|
| JIT-106 | TopicSelector (벡터 검색 기반 토픽 선별) | §14.1, §13 |
| JIT-107 | 3전략 QuestionCrafter (Negative/Complexity/Evolution 프롬프트) | §14.2 |
| JIT-108 | Enhancement Agents 5개 (용어설명, 비개발자 답변가이드, 파생질문 등) | §6.2 Phase 3 |
| JIT-109 | QualityGate 루프 (Reviewer + Reviser, 최대 2회 루프) | §6.2 Phase 4 |
| JIT-110 | Langfuse 프롬프트 업로드 (모든 프롬프트 Langfuse production 등록) | §14.3 |

---

## §14. 프롬프트 엔지니어링

### 14.1 프롬프트 전략

| 전략 | 적용 대상 | 설명 |
|------|----------|------|
| Few-shot | 질문 생성, 디자인 패턴 탐지 | 2-3개 예시로 출력 형식/품질 가이드 |
| Chain-of-Thought | 복잡도 해석, 결정 생성 | 단계별 추론 유도 |
| Fact-Grounded | 모든 판단 프롬프트 | "결정론적 수치를 참조하여" 전제 |
| Negative Prompting | 질문 생성 | "일반적/교과서적 질문은 제외" |

### 14.2 질문 생성 3전략

#### 전략 A: Negative Selection (안 한 이유 묻기)

```
분석 로직: AST 분석 결과, 사용될 법하지만 사용되지 않은 패턴/기술 감지
질문 예시: "async/await를 적용하지 않고 동기식으로 처리하셨습니다.
           동시성 이슈를 우려하여 일부러 그렇게 설계하신 건가요?"
검증 포인트:
  합격: 트레이드오프 이해 ("데이터 순서가 중요해서")
  불합격: "그냥 짜다 보니 그렇게 됐습니다"
```

**핵심 원리:** 사용하지 않은 기술/패턴을 질문함으로써 후보자가 의도적 선택(trade-off)을 했는지, 아니면 단순히 모르는 것인지를 판별한다.

#### 전략 B: Intentional Complexity (높은 난이도 의도 묻기)

```
분석 로직: Halstead 난이도(D)와 순환 복잡도(M)가 국소적으로 매우 높은 구간 식별
질문 예시: "validateToken 메서드는 순환 복잡도가 매우 높습니다(분기문 15개).
           이 부분을 분리하지 않고 유지한 아키텍처적 이유가 있나요?"
검증 포인트:
  합격: 응집도 / 보안 감사 용이성 등 구체적 이유
  불합격: "복잡한 줄 몰랐습니다"
```

**핵심 원리:** 복잡도가 높은 코드는 "나쁜 코드"일 수도 있고, "의도적으로 복잡하게 유지한 합리적 이유가 있는 코드"일 수도 있다. 이를 분별한다.

#### 전략 C: Code Evolution (변화 과정 묻기)

```
분석 로직: Git 히스토리에서 Code Churn이 높았던 구간, 대규모 리팩토링 지점 추적
질문 예시: "PaymentGateway 모듈이 초기 버전에서 3번 구조가 크게 바뀌었습니다.
           초기 설계에서 예상하지 못했던 문제는 구체적으로 무엇이었나요?"
검증 포인트:
  합격: 구체적인 문제와 해결 과정 설명 (해당 코드를 직접 고민해본 사람만 답변 가능)
  불합격: 최종 결과물만 설명 (AI는 수정 역사를 모름)
```

**핵심 원리:** 코드의 변화 과정을 아는 것은 실제로 그 코드를 작성하고 유지보수한 사람만이 가능하다. AI가 대신 작성한 코드라면 수정 이력의 맥락을 설명하지 못한다.

### 14.3 프롬프트 관리 흐름

```
Langfuse UI에서 프롬프트 편집/버전 관리
         |
         v
    get_prompt("question_craft_v5", label="production")
         |
         v (Langfuse 장애 시)
    YAML fallback (infrastructure/llm/prompts/)
         |
         v
    Instructor + Pydantic 검증
         |
         v (검증 실패 시)
    자동 재시도 (최대 3회, 에러 메시지 포함)
```

**중요 규칙:**
- YAML 프롬프트 수정 후 반드시 Langfuse 업로드: `docker compose exec backend python scripts/upload_prompts_to_langfuse.py --production`
- Langfuse-first 아키텍처: Langfuse가 런타임 우선 -> YAML만 수정하면 반영 안 됨

---

## 질문 생성 파이프라인 구조 (§6.2 Phase 3-4 참조)

### Phase 3: QuestionOrchestrator

```
QuestionOrchestrator 내부 구조:

1. TopicSelector
   - 벡터 검색(pgvector)으로 JD 관련성 높은 코드 청크 선별
   - 3전략별 토픽 분배 (Negative/Complexity/Evolution)

2. QuestionCrafter x N (3전략 병렬)
   - 전략 A: Negative Selection 프롬프트 -> InterviewQuestion
   - 전략 B: Intentional Complexity 프롬프트 -> InterviewQuestion
   - 전략 C: Code Evolution 프롬프트 -> InterviewQuestion
   - 각 전략은 Instructor를 통해 구조화된 InterviewQuestion 모델로 출력

3. EnhancementAgents x 5 (병렬)
   - 용어 설명 Agent: 전문 용어를 비개발자 언어로 풀어씀
   - 답변 가이드 Agent: 예상 답변을 비개발자도 이해 가능하게 작성
   - 파생 질문 Agent: follow_up_triggers 기반 후속 질문 생성
   - Red Flag Agent: 주의해야 할 답변 패턴 식별
   - 코드 레퍼런스 Agent: 관련 코드 위치(파일:라인) 매핑
```

### Phase 4: QualityGate 루프

```
질문 세트 -> Reviewer (품질 검증)
                |
                v
         품질 기준 통과?
         |           |
        YES          NO (revision_count < 2)
         |           |
         v           v
  OutputAssembler   Reviser -> QuestionOrchestrator 재실행
                              (최대 2회 루프)
```

**품질 검증 기준:**
- 질문이 JD 관련성을 갖추었는가
- 코드 레퍼런스가 실제 코드와 일치하는가
- 비개발자가 이해할 수 있는 수준인가
- 3전략 균형이 맞는가 (편중 방지)
- 중복 질문이 없는가

---

## InterviewQuestion 모델 (§12.2 참조)

```python
# domain/question/models.py
class InterviewQuestion(BaseModel):
    """Instructor로 LLM이 직접 생성하는 구조화된 면접 질문"""
    model_config = ConfigDict(strict=True)  # Pydantic v2

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

---

## Instructor + Langfuse 통합 (§12.3 참조)

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
