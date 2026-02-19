"""
Question 도메인 모델 테스트

TDD: 테스트 먼저 작성 후 모델 구현
"""
import pytest
from pydantic import ValidationError

from domain.question.models import (
    InterviewQuestion,
    QuestionCategory,
    QuestionStrategy,
)


# ---------------------------------------------------------------------------
# QuestionCategory
# ---------------------------------------------------------------------------


class TestQuestionCategory:
    def test_values(self):
        assert QuestionCategory.TECHNICAL_DEPTH == "technical_depth"
        assert QuestionCategory.EXECUTION_OWNERSHIP == "execution_ownership"
        assert QuestionCategory.COMMUNICATION == "communication"
        assert QuestionCategory.ROLE_FIT == "role_fit"
        assert QuestionCategory.RISK_FLAGS == "risk_flags"

    def test_is_str(self):
        assert isinstance(QuestionCategory.TECHNICAL_DEPTH, str)

    def test_all_members(self):
        members = set(QuestionCategory)
        assert members == {
            QuestionCategory.TECHNICAL_DEPTH,
            QuestionCategory.EXECUTION_OWNERSHIP,
            QuestionCategory.COMMUNICATION,
            QuestionCategory.ROLE_FIT,
            QuestionCategory.RISK_FLAGS,
        }


# ---------------------------------------------------------------------------
# QuestionStrategy
# ---------------------------------------------------------------------------


class TestQuestionStrategy:
    def test_values(self):
        assert QuestionStrategy.NEGATIVE_SELECTION == "negative_selection"
        assert QuestionStrategy.INTENTIONAL_COMPLEXITY == "intentional_complexity"
        assert QuestionStrategy.CODE_EVOLUTION == "code_evolution"

    def test_is_str(self):
        assert isinstance(QuestionStrategy.NEGATIVE_SELECTION, str)

    def test_all_members(self):
        members = set(QuestionStrategy)
        assert members == {
            QuestionStrategy.NEGATIVE_SELECTION,
            QuestionStrategy.INTENTIONAL_COMPLEXITY,
            QuestionStrategy.CODE_EVOLUTION,
        }


# ---------------------------------------------------------------------------
# InterviewQuestion
# ---------------------------------------------------------------------------


def _make_question(**overrides) -> InterviewQuestion:
    defaults = dict(
        question_id="Q-001",
        category=QuestionCategory.TECHNICAL_DEPTH,
        strategy=QuestionStrategy.NEGATIVE_SELECTION,
        difficulty="medium",
        question_text="이 함수에서 예외 처리가 왜 이렇게 구현되었나요?",
        intent="예외 처리 설계 이해도 확인",
        code_reference=None,
        expected_answer_guide="구체적인 에러 케이스와 복구 전략을 설명할 수 있어야 함",
        red_flags=["모른다고 답변", "전체 설계 설명 불가"],
        follow_up_triggers=["retry 로직은?", "timeout 처리는?"],
        terminology=[{"term": "idempotency", "definition": "같은 요청을 여러 번 해도 결과가 동일한 속성"}],
    )
    defaults.update(overrides)
    return InterviewQuestion(**defaults)


class TestInterviewQuestion:
    def test_creation(self):
        q = _make_question()
        assert q.question_id == "Q-001"
        assert q.category == QuestionCategory.TECHNICAL_DEPTH
        assert q.strategy == QuestionStrategy.NEGATIVE_SELECTION
        assert q.difficulty == "medium"
        assert q.code_reference is None

    def test_creation_with_code_reference(self):
        q = _make_question(code_reference="src/service.py:42")
        assert q.code_reference == "src/service.py:42"

    def test_category_technical_depth(self):
        q = _make_question(category=QuestionCategory.TECHNICAL_DEPTH)
        assert q.category == QuestionCategory.TECHNICAL_DEPTH

    def test_category_execution_ownership(self):
        q = _make_question(category=QuestionCategory.EXECUTION_OWNERSHIP)
        assert q.category == QuestionCategory.EXECUTION_OWNERSHIP

    def test_category_communication(self):
        q = _make_question(category=QuestionCategory.COMMUNICATION)
        assert q.category == QuestionCategory.COMMUNICATION

    def test_category_role_fit(self):
        q = _make_question(category=QuestionCategory.ROLE_FIT)
        assert q.category == QuestionCategory.ROLE_FIT

    def test_category_risk_flags(self):
        q = _make_question(category=QuestionCategory.RISK_FLAGS)
        assert q.category == QuestionCategory.RISK_FLAGS

    def test_strategy_negative_selection(self):
        q = _make_question(strategy=QuestionStrategy.NEGATIVE_SELECTION)
        assert q.strategy == QuestionStrategy.NEGATIVE_SELECTION

    def test_strategy_intentional_complexity(self):
        q = _make_question(strategy=QuestionStrategy.INTENTIONAL_COMPLEXITY)
        assert q.strategy == QuestionStrategy.INTENTIONAL_COMPLEXITY

    def test_strategy_code_evolution(self):
        q = _make_question(strategy=QuestionStrategy.CODE_EVOLUTION)
        assert q.strategy == QuestionStrategy.CODE_EVOLUTION

    def test_question_text_min_length(self):
        with pytest.raises(ValidationError):
            _make_question(question_text="Too short")  # 9 chars, < 10

    def test_question_text_max_length(self):
        with pytest.raises(ValidationError):
            _make_question(question_text="x" * 501)  # 501 chars, > 500

    def test_question_text_boundary_min(self):
        q = _make_question(question_text="x" * 10)  # exactly 10
        assert len(q.question_text) == 10

    def test_question_text_boundary_max(self):
        q = _make_question(question_text="x" * 500)  # exactly 500
        assert len(q.question_text) == 500

    def test_red_flags_list(self):
        q = _make_question(red_flags=["flag1", "flag2"])
        assert q.red_flags == ["flag1", "flag2"]

    def test_red_flags_empty(self):
        q = _make_question(red_flags=[])
        assert q.red_flags == []

    def test_follow_up_triggers_list(self):
        q = _make_question(follow_up_triggers=["trigger1"])
        assert q.follow_up_triggers == ["trigger1"]

    def test_follow_up_triggers_empty(self):
        q = _make_question(follow_up_triggers=[])
        assert q.follow_up_triggers == []

    def test_terminology_list(self):
        terms = [{"term": "foo", "definition": "bar"}]
        q = _make_question(terminology=terms)
        assert q.terminology == terms

    def test_terminology_empty(self):
        q = _make_question(terminology=[])
        assert q.terminology == []

    def test_invalid_category(self):
        with pytest.raises(ValidationError):
            _make_question(category="invalid_category")  # type: ignore[arg-type]

    def test_invalid_strategy(self):
        with pytest.raises(ValidationError):
            _make_question(strategy="invalid_strategy")  # type: ignore[arg-type]

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            InterviewQuestion(  # type: ignore[call-arg]
                question_id="Q-001",
                # missing category, strategy, difficulty, etc.
            )

    def test_difficulty_easy(self):
        q = _make_question(difficulty="easy")
        assert q.difficulty == "easy"

    def test_difficulty_hard(self):
        q = _make_question(difficulty="hard")
        assert q.difficulty == "hard"
