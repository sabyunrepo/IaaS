# Question Schema Reference

InterviewQuestion 및 관련 모델의 상세 구조.

## InterviewQuestion (Full Schema)

```python
class InterviewQuestion(BaseModel):
    id: str                                    # UUID
    category: QuestionCategory                 # role_fit|technical|execution|communication|risk_flags
    difficulty: Difficulty                      # easy|medium|hard
    main_question: str                         # 메인 질문 텍스트
    alternative_phrasings: list[str]           # 2-3개 대안 표현
    follow_up_questions: list[FollowUpQuestion] # 3개 (expert/mid/low trigger)
    evaluation_scenarios: list[EvaluationScenario]  # 3개 (expert/mid/low)
    keywords: list[Keyword]                    # must / good_to_have
    terminology: list[Terminology]             # plain_language_explanation
    code_reference: CodeReference | None       # GitHub permalink + 설명
    interviewer_note: InterviewerNote          # 비즈니스 해석 + 일상 비유
```

## Sub-Models

### FollowUpQuestion
```python
class FollowUpQuestion(BaseModel):
    id: str
    trigger: Literal["expert", "mid", "low"]  # 어떤 수준 답변 후 사용
    question: str
    purpose: str  # 왜 이 질문을 하는지 (면접관용 설명)
```

### EvaluationScenario
```python
class EvaluationScenario(BaseModel):
    level: Literal["expert", "mid", "low"]
    description: str       # 이 레벨 답변의 특징
    indicators: list[str]  # 구체적 판단 기준 (비개발자 이해 가능)
```

### CodeReference
```python
class CodeReference(BaseModel):
    permalink: str              # GitHub permalink (필수, null 금지)
    file_path: str              # 파일 경로
    line_range: str             # 줄 범위 (예: "L15-L42")
    plain_language_summary: str # 비개발자용 코드 설명
```

### InterviewerNote
```python
class InterviewerNote(BaseModel):
    business_interpretation: str  # 비즈니스 관점 해석
    daily_analogy: str            # 일상 비유
    red_flags: list[str]          # 경계 신호
```

### Keyword
```python
class Keyword(BaseModel):
    term: str
    priority: Literal["must", "good_to_have"]
```

### Terminology
```python
class Terminology(BaseModel):
    term: str                     # 기술 용어
    plain_explanation: str        # 비개발자 쉬운 설명
    daily_analogy: str | None     # 일상 비유 (선택)
```

## 8-Agent 생성 파이프라인 상세

| Step | Agent | Input | Output | 병렬 |
|------|-------|-------|--------|------|
| 1 | Topic Selector | 분석 결과 3종 | 25개 토픽 | - |
| 2 | Question Crafter | 토픽 + 컨텍스트 | 기본 질문 25개 | ×10 Worker |
| 3 | Terminology Definer | 질문 텍스트 | terminology[] | ×25 |
| 4 | Follow-up Designer | 질문 + 답변 분기 | follow_up_questions[3] | ×25 |
| 5 | Evaluation Writer | 질문 + 기대 수준 | evaluation_scenarios[3] | ×25 |
| 6 | Code Linker | 질문 + 코드 분석 | code_reference | ×25 |
| 7 | Interviewer Note Writer | 질문 + 비즈니스 맥락 | interviewer_note | ×25 |
| 8 | Quality Reviewer | 전체 25개 | PASS/REVISE/REJECT | 최대 3회 |
