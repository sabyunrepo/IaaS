"""
backend/tests/test_question_generation.py
Phase 3-4: Question Generation Activities 단위 테스트

테스트 항목:
- P3-01: 토픽 선정 (select_topics)
- P3-02: 질문 생성 (craft_question)
- P3-03: 용어 설명 (enhance_terminology)
- P3-04: 평가 시나리오 (craft_evaluation_scenarios)
- P3-05: 후속질문 (design_follow_ups)
- P3-06: 면접관 노트 (generate_interviewer_notes)
- P3-07: 의사결정 가이드 (generate_decision_guide)
- P3-08: 질문 수정 (revise_questions)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ============================================================
# P3-01: 토픽 선정 테스트
# ============================================================

class TestSelectTopics:
    """P3-01: 토픽 선정 테스트"""

    @pytest.mark.asyncio
    async def test_select_topics_basic(self, mock_aggregated_analysis, mock_enriched_input):
        """토픽 선정 기본 테스트"""
        from app.workflows.activities.question_generation import select_topics
        from unittest.mock import patch

        mock_topics = [
            {"category": "role_fit", "topic": "AI Experience", "difficulty": "Medium", "source": "jd_match"},
            {"category": "technical_depth", "topic": "Python", "difficulty": "Hard", "source": "code"},
        ]

        async def mock_llm_run(prompt):
            return mock_topics

        with patch("app.workflows.activities.question_generation.activity") as mock_activity, \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await select_topics(mock_aggregated_analysis, mock_enriched_input)

            assert len(result) > 0
            assert all("category" in t for t in result)

    @pytest.mark.asyncio
    async def test_select_topics_fallback(self, mock_aggregated_analysis, mock_enriched_input):
        """LLM 실패 시 폴백 토픽 생성"""
        from app.workflows.activities.question_generation import select_topics
        from unittest.mock import patch

        async def mock_llm_run(prompt):
            return "Not a list"  # LLM 실패 시뮬레이션

        with patch("app.workflows.activities.question_generation.activity") as mock_activity, \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await select_topics(mock_aggregated_analysis, mock_enriched_input)

            # 폴백으로 최대 25개 토픽 생성
            assert len(result) <= 25
            assert all("category" in t for t in result)


# ============================================================
# P3-02: 질문 생성 테스트
# ============================================================

class TestCraftQuestion:
    """P3-02: 질문 생성 테스트"""

    @pytest.mark.asyncio
    async def test_craft_question_basic(self, mock_aggregated_analysis, mock_enriched_input):
        """단일 질문 생성"""
        from app.workflows.activities.question_generation import craft_question
        from unittest.mock import patch

        topic = {
            "category": "technical_depth",
            "topic": "Python async programming",
            "difficulty": "Hard",
        }

        mock_question = {
            "question_text": "Python의 async/await에 대해 설명해주세요.",
            "category": "technical_depth",
            "difficulty": "Hard",
            "expected_answer": {"level_1": "기본 개념", "level_2": "구현 경험", "level_3": "최적화"},
        }

        async def mock_llm_run(prompt):
            return mock_question

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await craft_question(topic, mock_aggregated_analysis, mock_enriched_input)

            assert "question_text" in result
            assert result["category"] == "technical_depth"

    @pytest.mark.asyncio
    async def test_craft_question_llm_failure(self, mock_aggregated_analysis, mock_enriched_input):
        """LLM 실패 시 기본값 반환"""
        from app.workflows.activities.question_generation import craft_question
        from unittest.mock import patch

        topic = {
            "category": "role_fit",
            "topic": "Team collaboration",
            "difficulty": "Easy",
        }

        async def mock_llm_run(prompt):
            return "Not a dict"

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await craft_question(topic, mock_aggregated_analysis, mock_enriched_input)

            # 기본값 반환
            assert "question_text" in result
            assert "Team collaboration" in result["question_text"]


# ============================================================
# P3-03: 용어 설명 테스트
# ============================================================

class TestEnhanceTerminology:
    """P3-03: 용어 설명 테스트"""

    @pytest.mark.asyncio
    async def test_enhance_terminology(self, mock_enriched_input):
        """용어 설명 추가"""
        from app.workflows.activities.question_generation import enhance_terminology
        from unittest.mock import patch

        questions = [
            {"question_text": "FastAPI의 dependency injection을 설명해주세요."},
            {"question_text": "Temporal workflow의 retry policy에 대해 설명해주세요."},
        ]

        mock_result = {
            "terminology": {
                "dependency injection": "코드에서 필요한 객체를 외부에서 주입하는 패턴",
                "retry policy": "실패 시 재시도하는 정책",
            }
        }

        async def mock_llm_run(prompt):
            return mock_result

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await enhance_terminology(questions, mock_enriched_input)

            assert isinstance(result, dict)


# ============================================================
# P3-04: 평가 시나리오 테스트
# ============================================================

class TestCraftEvaluationScenarios:
    """P3-04: 평가 시나리오 테스트"""

    @pytest.mark.asyncio
    async def test_craft_evaluation_scenarios(self, mock_enriched_input):
        """평가 시나리오 생성"""
        from app.workflows.activities.question_generation import craft_evaluation_scenarios
        from unittest.mock import patch

        questions = [
            {"question_text": "Python 경험을 설명해주세요.", "category": "technical_depth"},
        ]

        mock_result = {
            "scenarios": {
                "q1": {
                    "fail": "Python 기본 문법도 모름",
                    "pass": "프로젝트에서 Python 사용 경험 있음",
                    "excel": "복잡한 Python 시스템 설계 및 최적화 경험",
                }
            }
        }

        async def mock_llm_run(prompt):
            return mock_result

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await craft_evaluation_scenarios(questions, mock_enriched_input)

            assert isinstance(result, dict)


# ============================================================
# P3-05: 후속질문 테스트
# ============================================================

class TestDesignFollowUps:
    """P3-05: 후속질문 테스트"""

    @pytest.mark.asyncio
    async def test_design_follow_ups(self, mock_enriched_input):
        """후속질문 설계"""
        from app.workflows.activities.question_generation import design_follow_ups
        from unittest.mock import patch

        questions = [
            {"question_text": "팀 협업 경험을 설명해주세요.", "category": "communication"},
        ]

        mock_result = {
            "follow_ups": {
                "q1": [
                    "구체적으로 어떤 역할을 맡으셨나요?",
                    "갈등 상황은 어떻게 해결하셨나요?",
                ]
            }
        }

        async def mock_llm_run(prompt):
            return mock_result

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await design_follow_ups(questions, mock_enriched_input)

            assert isinstance(result, dict)


# ============================================================
# P3-06: 면접관 노트 테스트
# ============================================================

class TestGenerateInterviewerNotes:
    """P3-06: 면접관 노트 테스트"""

    @pytest.mark.asyncio
    async def test_generate_interviewer_notes(self, mock_enriched_input):
        """면접관 노트 생성"""
        from app.workflows.activities.question_generation import generate_interviewer_notes
        from unittest.mock import patch

        questions = [
            {"question_text": "프로젝트 경험을 설명해주세요.", "category": "execution_ownership"},
        ]

        mock_result = {
            "notes": {
                "q1": "후보자의 구체적인 기여도와 문제 해결 방식에 주목하세요."
            }
        }

        async def mock_llm_run(prompt):
            return mock_result

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await generate_interviewer_notes(questions, mock_enriched_input)

            assert isinstance(result, dict)


# ============================================================
# P3-07: 의사결정 가이드 테스트
# ============================================================

class TestGenerateDecisionGuide:
    """P3-07: 의사결정 가이드 테스트"""

    @pytest.mark.asyncio
    async def test_generate_decision_guide(self, mock_aggregated_analysis, mock_enriched_input):
        """의사결정 가이드 생성"""
        from app.workflows.activities.question_generation import generate_decision_guide
        from unittest.mock import patch

        mock_result = {
            "key_decision_factors": ["기술 깊이", "문제 해결 능력"],
            "green_flags": ["주도적 프로젝트 경험", "학습 의욕"],
            "red_flags": ["팀워크 부족", "코드 품질 낮음"],
        }

        async def mock_llm_run(prompt):
            return mock_result

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await generate_decision_guide(mock_aggregated_analysis, mock_enriched_input)

            assert isinstance(result, dict)


# ============================================================
# P3-08: 질문 수정 테스트
# ============================================================

class TestReviseQuestions:
    """P3-08: 질문 수정 테스트"""

    @pytest.mark.asyncio
    async def test_revise_questions(self, mock_enriched_input):
        """피드백 기반 질문 수정"""
        from app.workflows.activities.question_generation import revise_questions
        from unittest.mock import patch

        questions = [
            {"question_text": "Python 경험을 설명해주세요.", "category": "technical_depth"},
        ]

        review_feedback = {
            "issues": [{"type": "too_generic", "question_index": 0}]
        }

        mock_revised = [
            {"question_text": "Python으로 해결한 가장 복잡한 문제는 무엇인가요?", "category": "technical_depth"},
        ]

        async def mock_llm_run(prompt):
            return mock_revised

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await revise_questions(questions, review_feedback, mock_enriched_input)

            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_revise_questions_llm_failure(self, mock_enriched_input):
        """LLM 실패 시 원본 반환"""
        from app.workflows.activities.question_generation import revise_questions
        from unittest.mock import patch

        original_questions = [
            {"question_text": "Original question", "category": "technical_depth"},
        ]

        async def mock_llm_run(prompt):
            return "Not a list"

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await revise_questions(original_questions, {}, mock_enriched_input)

            # 원본 반환
            assert result == original_questions


# ============================================================
# Activity 데코레이터 확인
# ============================================================

class TestQuestionGenerationActivities:
    """Question Generation Activity 데코레이터 확인"""

    def test_all_activities_have_defn(self):
        """모든 Activity에 데코레이터 확인"""
        from app.workflows.activities import question_generation

        activities = [
            question_generation.select_topics,
            question_generation.craft_question,
            question_generation.enhance_terminology,
            question_generation.craft_evaluation_scenarios,
            question_generation.design_follow_ups,
            question_generation.generate_interviewer_notes,
            question_generation.generate_decision_guide,
            question_generation.revise_questions,
        ]

        for activity_fn in activities:
            assert hasattr(activity_fn, "__temporal_activity_definition"), \
                f"{activity_fn.__name__} missing @activity.defn decorator"


# ============================================================
# 헬퍼 함수 테스트
# ============================================================

class TestHelperFunctions:
    """헬퍼 함수 테스트"""

    def test_format_candidates(self):
        """_format_candidates 함수 테스트"""
        from app.workflows.activities.question_generation import _format_candidates

        candidates = [
            {"source": "code", "topic": "Python async", "score": 0.9},
            {"source": "jd_match", "topic": "FastAPI", "score": 0.7},
        ]

        result = _format_candidates(candidates)

        assert "Python async" in result
        assert "FastAPI" in result
        assert "code" in result
        assert "jd_match" in result
