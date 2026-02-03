"""
backend/tests/test_quality_review.py
Phase 3: Quality Review Activity 단위 테스트

테스트 항목:
- P3-QR-01: 카테고리 분포 검사
- P3-QR-02: 난이도 분포 검사
- P3-QR-03: LLM 중복 검토
- P3-QR-04: 승인/수정 판정
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ============================================================
# P3-QR-01: 카테고리 분포 검사 테스트
# ============================================================

class TestCategoryDistribution:
    """P3-QR-01: 카테고리 분포 검사 테스트"""

    @pytest.mark.asyncio
    async def test_category_underrepresented(self):
        """특정 카테고리가 부족할 때"""
        from app.workflows.activities.quality_review import review_questions
        from unittest.mock import patch

        # role_fit 카테고리만 있는 질문들
        questions = [
            {"question_text": "Q1", "category": "role_fit", "difficulty": "Easy"},
            {"question_text": "Q2", "category": "role_fit", "difficulty": "Medium"},
            {"question_text": "Q3", "category": "role_fit", "difficulty": "Hard"},
        ]

        async def mock_llm_run(prompt):
            return {"duplicates": []}

        with patch("app.workflows.activities.quality_review.activity") as mock_activity, \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await review_questions(questions)

            # 다른 카테고리들이 부족하다는 이슈 발생
            category_issues = [i for i in result["issues"] if i["type"] == "category_underrepresented"]
            assert len(category_issues) >= 3  # technical_depth, execution_ownership, communication, risk_flags

    @pytest.mark.asyncio
    async def test_balanced_categories(self):
        """균형 잡힌 카테고리 분포"""
        from app.workflows.activities.quality_review import review_questions
        from unittest.mock import patch

        categories = ["role_fit", "technical_depth", "execution_ownership", "communication", "risk_flags"]
        questions = []
        for cat in categories:
            for i in range(5):
                questions.append({
                    "question_text": f"{cat} Q{i}",
                    "category": cat,
                    "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"][i],
                })

        async def mock_llm_run(prompt):
            return {"duplicates": []}

        with patch("app.workflows.activities.quality_review.activity") as mock_activity, \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await review_questions(questions)

            # 카테고리 부족 이슈 없음
            category_issues = [i for i in result["issues"] if i["type"] == "category_underrepresented"]
            assert len(category_issues) == 0


# ============================================================
# P3-QR-02: 난이도 분포 검사 테스트
# ============================================================

class TestDifficultyDistribution:
    """P3-QR-02: 난이도 분포 검사 테스트"""

    @pytest.mark.asyncio
    async def test_too_many_easy(self):
        """Easy 질문이 너무 많을 때"""
        from app.workflows.activities.quality_review import review_questions
        from unittest.mock import patch

        # 80% Easy 질문
        questions = [
            {"question_text": f"Q{i}", "category": "role_fit", "difficulty": "Easy"}
            for i in range(8)
        ] + [
            {"question_text": f"Q{i}", "category": "role_fit", "difficulty": "Hard"}
            for i in range(2)
        ]

        async def mock_llm_run(prompt):
            return {"duplicates": []}

        with patch("app.workflows.activities.quality_review.activity") as mock_activity, \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await review_questions(questions)

            # too_many_easy 이슈 발생
            easy_issues = [i for i in result["issues"] if i["type"] == "too_many_easy"]
            assert len(easy_issues) == 1

    @pytest.mark.asyncio
    async def test_too_many_hard(self):
        """Hard 질문이 너무 많을 때"""
        from app.workflows.activities.quality_review import review_questions
        from unittest.mock import patch

        # 80% Hard 질문
        questions = [
            {"question_text": f"Q{i}", "category": "technical_depth", "difficulty": "Hard"}
            for i in range(8)
        ] + [
            {"question_text": f"Q{i}", "category": "technical_depth", "difficulty": "Easy"}
            for i in range(2)
        ]

        async def mock_llm_run(prompt):
            return {"duplicates": []}

        with patch("app.workflows.activities.quality_review.activity") as mock_activity, \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await review_questions(questions)

            # too_many_hard 이슈 발생
            hard_issues = [i for i in result["issues"] if i["type"] == "too_many_hard"]
            assert len(hard_issues) == 1


# ============================================================
# P3-QR-03: LLM 중복 검토 테스트
# ============================================================

class TestDuplicateDetection:
    """P3-QR-03: LLM 중복 검토 테스트"""

    @pytest.mark.asyncio
    async def test_duplicates_detected(self):
        """중복 질문 감지"""
        from app.workflows.activities.quality_review import review_questions
        from unittest.mock import patch

        questions = [
            {"question_text": "Python 경험을 설명해주세요.", "category": "technical_depth", "difficulty": "Medium"},
            {"question_text": "Python 사용 경험에 대해 말씀해주세요.", "category": "technical_depth", "difficulty": "Medium"},
        ]

        async def mock_llm_run(prompt):
            return {"duplicates": [(0, 1, "Similar questions about Python experience")]}

        with patch("app.workflows.activities.quality_review.activity") as mock_activity, \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await review_questions(questions)

            # 중복 이슈 발생
            duplicate_issues = [i for i in result["issues"] if i["type"] == "duplicates"]
            assert len(duplicate_issues) == 1


# ============================================================
# P3-QR-04: 승인/수정 판정 테스트
# ============================================================

class TestVerdict:
    """P3-QR-04: 승인/수정 판정 테스트"""

    @pytest.mark.asyncio
    async def test_approved_verdict(self):
        """이슈가 적을 때 APPROVED"""
        from app.workflows.activities.quality_review import review_questions
        from unittest.mock import patch

        categories = ["role_fit", "technical_depth", "execution_ownership", "communication", "risk_flags"]
        questions = []
        for cat in categories:
            for i in range(5):
                questions.append({
                    "question_text": f"{cat} Q{i}",
                    "category": cat,
                    "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"][i],
                })

        async def mock_llm_run(prompt):
            return {"duplicates": []}

        with patch("app.workflows.activities.quality_review.activity") as mock_activity, \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await review_questions(questions)

            assert result["verdict"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_needs_revision_verdict(self):
        """이슈가 많을 때 NEEDS_REVISION"""
        from app.workflows.activities.quality_review import review_questions
        from unittest.mock import patch

        # 문제가 많은 질문 세트
        questions = [
            {"question_text": "Q1", "category": "role_fit", "difficulty": "Easy"},
        ]

        async def mock_llm_run(prompt):
            return {"duplicates": [(0, 0, "Self duplicate")]}

        with patch("app.workflows.activities.quality_review.activity") as mock_activity, \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await review_questions(questions)

            # 카테고리 부족 이슈 + 중복 이슈 = 3개 이상
            assert result["verdict"] == "NEEDS_REVISION"


# ============================================================
# Activity 통합 테스트
# ============================================================

class TestQualityReviewIntegration:
    """Quality Review Activity 통합 테스트"""

    def test_activity_is_defn(self):
        """Activity 데코레이터 확인"""
        from app.workflows.activities.quality_review import review_questions
        assert hasattr(review_questions, "__temporal_activity_definition")

    @pytest.mark.asyncio
    async def test_output_structure(self):
        """출력 구조 검증"""
        from app.workflows.activities.quality_review import review_questions
        from unittest.mock import patch

        questions = []

        async def mock_llm_run(prompt):
            return {}

        with patch("app.workflows.activities.quality_review.activity") as mock_activity, \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await review_questions(questions)

            # 필수 필드 확인
            assert "verdict" in result
            assert "issues" in result
            assert "questions_to_revise" in result
            assert "category_distribution" in result
            assert "difficulty_distribution" in result
