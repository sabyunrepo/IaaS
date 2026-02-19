"""
Question 도메인 모델

순수 Pydantic v2 모델 — 외부 의존성 없음 (pydantic만 허용).
면접 질문 생성에 필요한 핵심 데이터 구조 정의.
"""
from enum import StrEnum

from pydantic import BaseModel, Field


class QuestionCategory(StrEnum):
    """면접 질문 카테고리."""

    TECHNICAL_DEPTH = "technical_depth"
    EXECUTION_OWNERSHIP = "execution_ownership"
    COMMUNICATION = "communication"
    ROLE_FIT = "role_fit"
    RISK_FLAGS = "risk_flags"


class QuestionStrategy(StrEnum):
    """면접 질문 생성 전략."""

    NEGATIVE_SELECTION = "negative_selection"
    INTENTIONAL_COMPLEXITY = "intentional_complexity"
    CODE_EVOLUTION = "code_evolution"


class InterviewQuestion(BaseModel, strict=True):
    """
    AI가 생성한 면접 질문 단일 항목.

    후보자의 실제 GitHub 코드에서 추출한 근거를 기반으로
    카테고리, 전략, 난이도, 질문 본문, 예상 답변 가이드를 담는다.
    """

    question_id: str
    category: QuestionCategory
    strategy: QuestionStrategy
    difficulty: str  # easy | medium | hard
    question_text: str = Field(min_length=10, max_length=500)
    intent: str
    code_reference: str | None = None
    expected_answer_guide: str
    red_flags: list[str]
    follow_up_triggers: list[str]
    terminology: list[dict]


class InterviewScript(BaseModel, strict=True):
    """
    면접 질문 세트 전체를 담는 Aggregate.

    3전략별 질문 목록 + 메타데이터를 포함한다.
    OutputAssembler에서 최종 조립 시 사용.
    """

    job_id: str
    questions: list[InterviewQuestion]
    total_count: int = 0
    strategy_distribution: dict[str, int] = Field(default_factory=dict)
    category_distribution: dict[str, int] = Field(default_factory=dict)

    def model_post_init(self, __context: object) -> None:
        self.total_count = len(self.questions)
        self.strategy_distribution = {}
        for q in self.questions:
            key = q.strategy.value if hasattr(q.strategy, "value") else str(q.strategy)
            self.strategy_distribution[key] = self.strategy_distribution.get(key, 0) + 1
        self.category_distribution = {}
        for q in self.questions:
            key = q.category.value if hasattr(q.category, "value") else str(q.category)
            self.category_distribution[key] = self.category_distribution.get(key, 0) + 1
