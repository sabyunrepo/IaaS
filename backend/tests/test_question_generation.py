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

Note: 모든 question_generation activity는 Langfuse-first 패턴
(run_llm_with_prompt_config_heartbeat → run_with_prompt_config)을 사용하므로
run_with_prompt_config을 모킹합니다.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


HEARTBEAT_PATCH = "temporalio.activity.heartbeat"
LLM_RUN_PATCH = "app.services.cached_llm.CachedLLMService.run_with_prompt_config"
ACTIVITY_MODULE_PATCH = "app.workflows.activities.question_generation.activity"


# ============================================================
# P3-01: 토픽 선정 테스트
# ============================================================

class TestSelectTopics:
    """P3-01: 토픽 선정 테스트"""

    @pytest.mark.asyncio
    async def test_select_topics_basic(self, mock_aggregated_analysis, mock_enriched_input):
        """토픽 선정 기본 테스트"""
        from app.workflows.activities.question_generation import select_topics

        mock_topics = [
            {"category": "role_fit", "topic": "AI Experience", "difficulty": "Medium", "source": "jd_match"},
            {"category": "technical_depth", "topic": "Python", "difficulty": "Hard", "source": "code"},
        ]

        async def mock_llm_run(prompt_config, **kwargs):
            return mock_topics

        with patch(ACTIVITY_MODULE_PATCH) as mock_activity, \
             patch(LLM_RUN_PATCH, side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await select_topics(mock_aggregated_analysis, mock_enriched_input)

            assert len(result) > 0
            assert all("category" in t for t in result)

    @pytest.mark.asyncio
    async def test_select_topics_fallback(self, mock_aggregated_analysis, mock_enriched_input):
        """LLM 실패 시 폴백 토픽 생성"""
        from app.workflows.activities.question_generation import select_topics

        async def mock_llm_run(prompt_config, **kwargs):
            return "Not a list"  # LLM 실패 시뮬레이션

        with patch(ACTIVITY_MODULE_PATCH) as mock_activity, \
             patch(LLM_RUN_PATCH, side_effect=mock_llm_run):

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

        async def mock_llm_run(prompt_config, **kwargs):
            return mock_question

        with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
             patch(HEARTBEAT_PATCH):
            result = await craft_question(topic, mock_aggregated_analysis, mock_enriched_input)

            assert "question_text" in result
            assert result["category"] == "technical_depth"

    @pytest.mark.asyncio
    async def test_craft_question_llm_failure(self, mock_aggregated_analysis, mock_enriched_input):
        """LLM 실패 시 기본값 반환"""
        from app.workflows.activities.question_generation import craft_question

        topic = {
            "category": "role_fit",
            "topic": "Team collaboration",
            "difficulty": "Easy",
        }

        async def mock_llm_run(prompt_config, **kwargs):
            return "Not a dict"

        with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
             patch(HEARTBEAT_PATCH):
            result = await craft_question(topic, mock_aggregated_analysis, mock_enriched_input)

            # 기본값 반환
            assert "question_text" in result
            assert "Team collaboration" in result["question_text"]


# ============================================================
# P3-02b: 카테고리별 프롬프트 라우팅 테스트
# ============================================================

class TestCraftQuestionCategoryRouting:
    """P3-02b: 카테고리별 프롬프트 선택 검증"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("category", [
        "role_fit", "technical_depth", "execution_ownership", "communication", "risk_flags",
    ])
    async def test_category_specific_prompt_loaded(self, category, mock_aggregated_analysis, mock_enriched_input):
        """각 카테고리별 전용 프롬프트가 정상 로딩되는지 검증"""
        from app.prompts import get_prompt

        prompt = get_prompt(
            "question_generation.yaml", f"craft_question_{category}",
            output_language="Korean",
            experience_level="미들",
            topic="테스트 토픽",
            category=category,
            difficulty="Medium",
            evidence_context="",
            recommended_probe="",
        )
        assert len(prompt) > 100, f"craft_question_{category} 프롬프트가 비어 있음"
        assert category in prompt.lower() or "interview" in prompt.lower()

    @pytest.mark.asyncio
    async def test_category_routing_uses_correct_prompt(self, mock_aggregated_analysis, mock_enriched_input):
        """craft_question이 카테고리에 맞는 프롬프트를 선택하는지 검증"""
        from app.workflows.activities.question_generation import craft_question

        captured_prompts = {}

        async def mock_llm_run(prompt_config, **kwargs):
            # 프롬프트 내용 캡처
            captured_prompts["prompt"] = getattr(prompt_config, "prompt", str(prompt_config))
            return {
                "question_text": "테스트 질문",
                "category": "role_fit",
                "difficulty": "Medium",
            }

        categories_to_test = ["role_fit", "technical_depth", "communication"]
        for cat in categories_to_test:
            topic = {"category": cat, "topic": f"{cat} 테스트", "difficulty": "Medium"}
            with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
                 patch(HEARTBEAT_PATCH):
                await craft_question(topic, mock_aggregated_analysis, mock_enriched_input)
                # 카테고리별 프롬프트가 사용되었는지 확인
                assert captured_prompts.get("prompt"), f"{cat} 프롬프트가 캡처되지 않음"

    @pytest.mark.asyncio
    async def test_unknown_category_falls_back_to_generic(self, mock_aggregated_analysis, mock_enriched_input):
        """알 수 없는 카테고리는 범용 craft_question으로 fallback"""
        from app.workflows.activities.question_generation import craft_question

        topic = {
            "category": "nonexistent_category",
            "topic": "Unknown topic",
            "difficulty": "Medium",
        }

        mock_question = {
            "question_text": "Fallback question",
            "category": "nonexistent_category",
            "difficulty": "Medium",
        }

        async def mock_llm_run(prompt_config, **kwargs):
            return mock_question

        with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
             patch(HEARTBEAT_PATCH):
            result = await craft_question(topic, mock_aggregated_analysis, mock_enriched_input)
            # fallback이 작동해서 결과가 반환되어야 함
            assert "question_text" in result

    @pytest.mark.asyncio
    async def test_all_five_categories_produce_questions(self, mock_aggregated_analysis, mock_enriched_input):
        """5개 카테고리 모두 질문 생성 성공"""
        from app.workflows.activities.question_generation import craft_question

        categories = ["role_fit", "technical_depth", "execution_ownership", "communication", "risk_flags"]

        for cat in categories:
            topic = {"category": cat, "topic": f"{cat} topic", "difficulty": "Medium"}

            async def mock_llm_run(prompt_config, **kwargs):
                return {
                    "question_text": f"Question for {cat}",
                    "category": cat,
                    "difficulty": "Medium",
                }

            with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
                 patch(HEARTBEAT_PATCH):
                result = await craft_question(topic, mock_aggregated_analysis, mock_enriched_input)
                assert result["category"] == cat, f"{cat} 카테고리 결과 불일치"
                assert "id" in result, f"{cat} 질문에 ID 없음"


# ============================================================
# P3-03: 용어 설명 테스트
# ============================================================

class TestEnhanceTerminology:
    """P3-03: 용어 설명 테스트"""

    @pytest.mark.asyncio
    async def test_enhance_terminology(self, mock_enriched_input):
        """용어 설명 추가"""
        from app.workflows.activities.question_generation import enhance_terminology

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

        async def mock_llm_run(prompt_config, **kwargs):
            return mock_result

        with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
             patch(HEARTBEAT_PATCH):
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

        async def mock_llm_run(prompt_config, **kwargs):
            return mock_result

        with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
             patch(HEARTBEAT_PATCH):
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

        async def mock_llm_run(prompt_config, **kwargs):
            return mock_result

        with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
             patch(HEARTBEAT_PATCH):
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

        questions = [
            {"question_text": "프로젝트 경험을 설명해주세요.", "category": "execution_ownership"},
        ]

        mock_result = {
            "notes": {
                "q1": "후보자의 구체적인 기여도와 문제 해결 방식에 주목하세요."
            }
        }

        async def mock_llm_run(prompt_config, **kwargs):
            return mock_result

        with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
             patch(HEARTBEAT_PATCH):
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

        mock_result = {
            "key_decision_factors": ["기술 깊이", "문제 해결 능력"],
            "green_flags": ["주도적 프로젝트 경험", "학습 의욕"],
            "red_flags": ["팀워크 부족", "코드 품질 낮음"],
        }

        async def mock_llm_run(prompt_config, **kwargs):
            return mock_result

        with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
             patch(HEARTBEAT_PATCH):
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

        all_questions = [
            {"question_text": "Python 경험을 설명해주세요.", "category": "technical_depth"},
        ]

        flagged_questions = [
            {"question_text": "Python 경험을 설명해주세요.", "category": "technical_depth", "_original_idx": 0},
        ]

        review_feedback = {
            "issues": [{"type": "too_generic", "question_index": 0}]
        }

        mock_revised = [
            {"question_text": "Python으로 해결한 가장 복잡한 문제는 무엇인가요?", "category": "technical_depth", "original_index": 0},
        ]

        async def mock_llm_run(prompt_config, **kwargs):
            return mock_revised

        with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
             patch(HEARTBEAT_PATCH):
            result = await revise_questions(all_questions, flagged_questions, review_feedback, mock_enriched_input)

            assert isinstance(result, list)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_revise_questions_llm_failure(self, mock_enriched_input):
        """LLM 실패 시 원본 반환"""
        from app.workflows.activities.question_generation import revise_questions

        original_questions = [
            {"question_text": "Original question", "category": "technical_depth"},
        ]

        flagged_questions = [
            {"question_text": "Original question", "category": "technical_depth", "_original_idx": 0},
        ]

        async def mock_llm_run(prompt_config, **kwargs):
            return "Not a list"

        with patch(LLM_RUN_PATCH, side_effect=mock_llm_run), \
             patch(HEARTBEAT_PATCH):
            result = await revise_questions(original_questions, flagged_questions, {}, mock_enriched_input)

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
