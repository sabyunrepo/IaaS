"""
backend/tests/test_jd_analysis.py
Phase 2: JD Analysis Activity 단위 테스트

테스트 항목:
- P2J-01: JD 요구사항 추출
- P2J-02: 스킬 추출
- P2J-03: LLM 실패 시 기본값 반환
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ============================================================
# P2J-01: JD 요구사항 추출 테스트
# ============================================================

class TestJdRequirementsExtraction:
    """P2J-01: JD 요구사항 추출 테스트"""

    @pytest.mark.asyncio
    async def test_analyze_jd_returns_requirements(self, sample_jd_text):
        """JD 분석 결과에 요구사항 포함"""
        from app.workflows.activities.jd_analysis import analyze_jd
        from unittest.mock import patch

        mock_result = {
            "job_title": "AI Engineer",
            "company_name": "TechCorp",
            "requirements": [
                {"skill": "Python", "level": "필수"},
                {"skill": "LLM API", "level": "필수"},
            ],
            "responsibilities": ["AI 서비스 개발", "백엔드 구축"],
            "company_culture": [],
            "tech_stack": ["Python", "TypeScript", "FastAPI"],
        }

        async def mock_llm_run(prompt, **kwargs):
            return mock_result

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await analyze_jd(sample_jd_text)

            assert result["job_title"] == "AI Engineer"
            assert len(result["requirements"]) > 0
            assert len(result["tech_stack"]) > 0


# ============================================================
# P2J-02: 스킬 추출 테스트
# ============================================================

class TestJdSkillExtraction:
    """P2J-02: 스킬 추출 테스트"""

    @pytest.mark.asyncio
    async def test_analyze_jd_extracts_tech_stack(self, sample_jd_text):
        """JD에서 기술스택 추출"""
        from app.workflows.activities.jd_analysis import analyze_jd
        from unittest.mock import patch

        mock_result = {
            "job_title": "Backend Developer",
            "tech_stack": ["Python", "TypeScript", "FastAPI", "React"],
            "requirements": [],
            "responsibilities": [],
        }

        async def mock_llm_run(prompt, **kwargs):
            return mock_result

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await analyze_jd(sample_jd_text)

            assert "tech_stack" in result
            assert "Python" in result["tech_stack"]


# ============================================================
# P2J-03: LLM 실패 시 기본값 반환 테스트
# ============================================================

class TestJdAnalysisErrorHandling:
    """P2J-03: LLM 실패 시 기본값 반환 테스트"""

    @pytest.mark.asyncio
    async def test_analyze_jd_llm_returns_non_dict(self):
        """LLM이 dict가 아닌 값 반환 시"""
        from app.workflows.activities.jd_analysis import analyze_jd
        from unittest.mock import patch

        async def mock_llm_run(prompt, **kwargs):
            return "Not a dict response"

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await analyze_jd("Test JD")

            # 기본값 반환
            assert result["job_title"] is None
            assert result["requirements"] == []
            assert result["tech_stack"] == []


# ============================================================
# Activity 통합 테스트
# ============================================================

class TestJdAnalysisIntegration:
    """JD Analysis Activity 통합 테스트"""

    def test_activity_is_defn(self):
        """Activity 데코레이터 확인"""
        from app.workflows.activities.jd_analysis import analyze_jd
        assert hasattr(analyze_jd, "__temporal_activity_definition")

    @pytest.mark.asyncio
    async def test_output_structure(self, sample_jd_text):
        """출력 구조 검증"""
        from app.workflows.activities.jd_analysis import analyze_jd
        from unittest.mock import patch

        mock_result = {
            "job_title": "Test",
            "company_name": "Test Co",
            "requirements": [],
            "responsibilities": [],
            "company_culture": [],
            "tech_stack": [],
        }

        async def mock_llm_run(prompt, **kwargs):
            return mock_result

        with patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):
            result = await analyze_jd(sample_jd_text)

            # 필수 필드 확인
            required_fields = [
                "job_title", "company_name", "requirements",
                "responsibilities", "company_culture", "tech_stack",
                "skill_matches", "overall_match_score", "gaps", "strengths",
            ]
            for field in required_fields:
                assert field in result, f"Missing field: {field}"
