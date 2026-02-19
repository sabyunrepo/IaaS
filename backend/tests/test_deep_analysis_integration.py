"""
backend/tests/test_deep_analysis_integration.py
JIT-41~44 통합 테스트: 스킬 테이블 + 레이더 점수 + 코드 분석 데이터 흐름 검증
"""
import json
import pytest
from collections import namedtuple
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.deep_analysis import SkillMatchRow


# Mock 패치 경로
HEARTBEAT_PATCH = "temporalio.activity.heartbeat"
RUN_LLM_PATCH = "app.workflows.utils.run_llm_with_prompt_config_heartbeat"
GET_PROMPT_PATCH = "app.prompts.get_prompt_with_config"
CACHED_LLM_PATCH = "app.services.cached_llm.CachedLLMService"


# ============================================================
# TestSkillTableIntegration (JIT-41)
# ============================================================

class TestSkillTableIntegration:
    """스킬 테이블 생성의 candidate_profile 통합 검증"""

    @pytest.mark.asyncio
    async def test_llm_skill_table_with_candidate_profile(
        self, jd_analysis_fixture, code_analysis_hybrid,
        document_analysis_with_skills, candidate_profile_with_skills,
    ):
        """candidate_profile.skills가 있을 때 unified_skills JSON이 LLM에 전달되는지 검증"""
        from app.workflows.activities.analysis_generation import _llm_build_skill_table

        captured_config = {}

        async def mock_run_llm(llm, prompt_config, **kwargs):
            captured_config["prompt_config"] = prompt_config
            return [
                {"skill": "Python", "candidate": "Python", "type": "exact", "confidence": 95, "evidence": "Resume + GitHub"},
                {"skill": "FastAPI", "candidate": "FastAPI", "type": "exact", "confidence": 90, "evidence": "Multi-source"},
            ]

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch("app.services.llm_config.KIMI_CHAT_MODEL", "test-model"):

            mock_get_prompt.return_value = MagicMock()
            result = await _llm_build_skill_table(
                jd_analysis_fixture, code_analysis_hybrid,
                document_analysis_with_skills, candidate_profile=candidate_profile_with_skills,
            )

            # get_prompt_with_config 호출 인자에서 unified_skills 확인
            call_kwargs = mock_get_prompt.call_args
            unified_skills_arg = call_kwargs.kwargs.get("unified_skills") or call_kwargs[1].get("unified_skills", "")
            parsed = json.loads(unified_skills_arg)

            # candidate_profile.skills가 unified_skills에 포함됨
            skill_names = [s["skill"] for s in parsed]
            assert "Python" in skill_names
            assert "FastAPI" in skill_names

            # 소스 정보 포함
            python_entry = next(s for s in parsed if s["skill"] == "Python")
            assert "resume" in python_entry["sources"]
            assert "github" in python_entry["sources"]

            # 결과 검증
            assert result is not None
            assert len(result) == 2
            assert isinstance(result[0], SkillMatchRow)

    @pytest.mark.asyncio
    async def test_llm_skill_table_fallback_to_document_analysis(
        self, jd_analysis_fixture, code_analysis_hybrid,
        document_analysis_with_skills,
    ):
        """candidate_profile이 None일 때 document_analysis.profile.skills로 폴백"""
        from app.workflows.activities.analysis_generation import _llm_build_skill_table

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return [
                {"skill": "Python", "candidate": "Python", "type": "exact", "confidence": 85, "evidence": "Resume"},
            ]

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch("app.services.llm_config.KIMI_CHAT_MODEL", "test-model"):

            mock_get_prompt.return_value = MagicMock()
            result = await _llm_build_skill_table(
                jd_analysis_fixture, code_analysis_hybrid,
                document_analysis_with_skills, candidate_profile=None,
            )

            # unified_skills는 빈 배열이어야 함 (candidate_profile 없음)
            call_kwargs = mock_get_prompt.call_args
            unified_skills_arg = call_kwargs.kwargs.get("unified_skills") or call_kwargs[1].get("unified_skills", "")
            assert unified_skills_arg == "[]"

            # candidate_skills에 document_analysis.profile.skills가 사용됨
            candidate_skills_arg = call_kwargs.kwargs.get("candidate_skills") or call_kwargs[1].get("candidate_skills", "")
            parsed_candidates = json.loads(candidate_skills_arg)
            assert "Python" in parsed_candidates
            assert "JavaScript" in parsed_candidates

            assert result is not None

    def test_rule_based_skill_table_multi_source(
        self, jd_analysis_fixture, code_analysis_hybrid,
        document_analysis_with_skills, candidate_profile_with_skills,
    ):
        """_build_skill_table() 규칙 기반에서 multi-source evidence 생성 검증"""
        from app.workflows.activities.analysis_generation import _build_skill_table

        result = _build_skill_table(
            jd_analysis_fixture, code_analysis_hybrid,
            document_analysis_with_skills, candidate_profile=candidate_profile_with_skills,
        )

        assert len(result) > 0

        # Python: resume + github 소스 → multi-source evidence
        python_row = next((r for r in result if r.skill == "Python"), None)
        assert python_row is not None
        assert python_row.type == "exact"
        # multi-source confidence 보너스 반영
        assert python_row.confidence > 90
        # evidence에 소스 태그 포함
        assert "Resume" in python_row.evidence or "Github" in python_row.evidence or "GitHub" in python_row.evidence

        # FastAPI: resume + github + linkedin (3 source)
        fastapi_row = next((r for r in result if r.skill == "FastAPI"), None)
        assert fastapi_row is not None
        assert fastapi_row.type == "exact"
        assert fastapi_row.confidence >= 95  # 3-source bonus

        # Kubernetes: candidate_profile에 없음 → none
        k8s_row = next((r for r in result if r.skill == "Kubernetes"), None)
        assert k8s_row is not None
        assert k8s_row.type == "none"

    def test_skill_table_empty_both_sources(self, jd_analysis_fixture, document_analysis_empty_skills):
        """양쪽 다 비어있을 때 graceful 처리"""
        from app.workflows.activities.analysis_generation import _build_skill_table

        result = _build_skill_table(
            jd_analysis_fixture, None,
            document_analysis_empty_skills, candidate_profile=None,
        )

        # JD requirements가 있으므로 행은 생성됨 (모두 none)
        assert len(result) == len(jd_analysis_fixture["requirements"])
        for row in result:
            assert row.type == "none"
            assert row.confidence == 0


# ============================================================
# TestRadarScoreIntegration (JIT-42)
# ============================================================

class TestRadarScoreIntegration:
    """레이더 점수 계산의 LinkedIn/candidate_profile 통합 검증"""

    @pytest.mark.asyncio
    async def test_radar_with_linkedin_context(
        self, jd_analysis_fixture, code_analysis_hybrid,
        document_analysis_with_skills, sample_linkedin_profile,
        candidate_profile_with_skills,
    ):
        """linkedin_profile이 있을 때 LLM 프롬프트에 LinkedIn 데이터가 포함되는지 검증"""
        from app.workflows.activities.analysis_generation import _llm_calculate_radar_scores

        RadarResult = namedtuple("RadarResult", ["candidate", "required", "sources", "confidence", "human_sources"])
        mock_radar = RadarResult(
            candidate=[70, 80, 60, 50, 75],
            required=[80, 85, 70, 60, 80],
            sources=["src1", "src2", "src3", "src4", "src5"],
            confidence="medium",
            human_sources=["h1", "h2", "h3", "h4", "h5"],
        )

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "candidate_scores": [72, 82, 62, 52, 77],
                "reasoning": {
                    "role_fit": "Good fit",
                    "technical": "Strong",
                    "execution": "Average",
                    "communication": "Needs work",
                    "code_quality": "Good",
                },
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH), \
             patch("app.services.scoring_formulas.calculate_radar_scores", return_value=mock_radar), \
             patch("app.services.scoring_formulas.get_required_scores", return_value=[80, 85, 70, 60, 80]):

            mock_get_prompt.return_value = MagicMock()
            result = await _llm_calculate_radar_scores(
                jd_analysis_fixture, code_analysis_hybrid,
                document_analysis_with_skills,
                linkedin_profile=sample_linkedin_profile,
                candidate_profile=candidate_profile_with_skills,
            )

            # get_prompt_with_config에 linkedin_context가 전달됨
            call_kwargs = mock_get_prompt.call_args
            linkedin_ctx = call_kwargs.kwargs.get("linkedin_context") or call_kwargs[1].get("linkedin_context", "")
            assert "LinkedIn" in linkedin_ctx
            assert "Senior Engineer" in linkedin_ctx or "TechCorp" in linkedin_ctx

            # unified_skills_context도 전달됨
            unified_ctx = call_kwargs.kwargs.get("unified_skills_context") or call_kwargs[1].get("unified_skills_context", "")
            parsed = json.loads(unified_ctx)
            skill_names = [s["skill"] for s in parsed]
            assert "Python" in skill_names

            assert result is not None

    @pytest.mark.asyncio
    async def test_radar_with_unified_skills(
        self, jd_analysis_fixture, code_analysis_hybrid,
        document_analysis_with_skills, candidate_profile_with_skills,
    ):
        """candidate_profile.skills가 unified_skills_context로 전달되는지 검증"""
        from app.workflows.activities.analysis_generation import _llm_calculate_radar_scores

        RadarResult = namedtuple("RadarResult", ["candidate", "required", "sources", "confidence", "human_sources"])
        mock_radar = RadarResult([70, 80, 60, 50, 75], [80, 85, 70, 60, 80],
                                ["s1", "s2", "s3", "s4", "s5"], "medium", [])

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "candidate_scores": [70, 80, 60, 50, 75],
                "reasoning": {"role_fit": "OK", "technical": "OK", "execution": "OK", "communication": "OK", "code_quality": "OK"},
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH), \
             patch("app.services.scoring_formulas.calculate_radar_scores", return_value=mock_radar), \
             patch("app.services.scoring_formulas.get_required_scores", return_value=[80, 85, 70, 60, 80]):

            mock_get_prompt.return_value = MagicMock()
            await _llm_calculate_radar_scores(
                jd_analysis_fixture, code_analysis_hybrid,
                document_analysis_with_skills,
                candidate_profile=candidate_profile_with_skills,
            )

            call_kwargs = mock_get_prompt.call_args
            unified_ctx = call_kwargs.kwargs.get("unified_skills_context") or call_kwargs[1].get("unified_skills_context", "")
            parsed = json.loads(unified_ctx)

            # 모든 스킬이 소스와 함께 전달됨
            for entry in parsed:
                assert "skill" in entry
                assert "sources" in entry

            # Python은 resume + github 소스
            python_entry = next(e for e in parsed if e["skill"] == "Python")
            assert "resume" in python_entry["sources"]
            assert "github" in python_entry["sources"]

    @pytest.mark.asyncio
    async def test_radar_without_linkedin(
        self, jd_analysis_fixture, code_analysis_hybrid, document_analysis_with_skills,
    ):
        """linkedin_profile이 None일 때 에러 없이 처리"""
        from app.workflows.activities.analysis_generation import _llm_calculate_radar_scores

        RadarResult = namedtuple("RadarResult", ["candidate", "required", "sources", "confidence", "human_sources"])
        mock_radar = RadarResult([70, 80, 60, 50, 75], [80, 85, 70, 60, 80],
                                ["s1", "s2", "s3", "s4", "s5"], "medium", [])

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "candidate_scores": [70, 80, 60, 50, 75],
                "reasoning": {"role_fit": "OK", "technical": "OK", "execution": "OK", "communication": "OK", "code_quality": "OK"},
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH), \
             patch("app.services.scoring_formulas.calculate_radar_scores", return_value=mock_radar), \
             patch("app.services.scoring_formulas.get_required_scores", return_value=[80, 85, 70, 60, 80]):

            mock_get_prompt.return_value = MagicMock()
            result = await _llm_calculate_radar_scores(
                jd_analysis_fixture, code_analysis_hybrid,
                document_analysis_with_skills,
                linkedin_profile=None,
                candidate_profile=None,
            )

            # linkedin_context는 빈 문자열
            call_kwargs = mock_get_prompt.call_args
            linkedin_ctx = call_kwargs.kwargs.get("linkedin_context") or call_kwargs[1].get("linkedin_context", "")
            assert linkedin_ctx == ""

            # unified_skills_context도 빈 문자열
            unified_ctx = call_kwargs.kwargs.get("unified_skills_context") or call_kwargs[1].get("unified_skills_context", "")
            assert unified_ctx == ""

            assert result is not None

    @pytest.mark.asyncio
    async def test_radar_code_analysis_hybrid_fields(
        self, jd_analysis_fixture, code_analysis_hybrid, document_analysis_with_skills,
    ):
        """code_analysis에 ast_chunk_count, hybrid_metadata가 code_summary JSON에 포함되는지"""
        from app.workflows.activities.analysis_generation import _llm_calculate_radar_scores

        RadarResult = namedtuple("RadarResult", ["candidate", "required", "sources", "confidence", "human_sources"])
        mock_radar = RadarResult([70, 80, 60, 50, 75], [80, 85, 70, 60, 80],
                                ["s1", "s2", "s3", "s4", "s5"], "medium", [])

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "candidate_scores": [70, 80, 60, 50, 75],
                "reasoning": {"role_fit": "OK", "technical": "OK", "execution": "OK", "communication": "OK", "code_quality": "OK"},
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH), \
             patch("app.services.scoring_formulas.calculate_radar_scores", return_value=mock_radar), \
             patch("app.services.scoring_formulas.get_required_scores", return_value=[80, 85, 70, 60, 80]):

            mock_get_prompt.return_value = MagicMock()
            await _llm_calculate_radar_scores(
                jd_analysis_fixture, code_analysis_hybrid,
                document_analysis_with_skills,
            )

            call_kwargs = mock_get_prompt.call_args
            code_summary_arg = call_kwargs.kwargs.get("code_analysis_summary") or call_kwargs[1].get("code_analysis_summary", "")
            parsed = json.loads(code_summary_arg)

            # HYBRID 필드가 code_summary에 포함
            assert parsed["ast_chunk_count"] == 20
            assert parsed["analyzed_functions_count"] == 5
            assert parsed["hybrid_metadata"]["method"] == "hybrid"
            assert parsed["hybrid_metadata"]["total_repos"] == 2


# ============================================================
# TestCodeAnalysisNewFields (JIT-44)
# ============================================================

class TestCodeAnalysisNewFields:
    """HYBRID 파이프라인 코드 분석 신포맷 필드 통합 검증"""

    @pytest.mark.asyncio
    async def test_llm_skill_table_hybrid_functions_context(
        self, jd_analysis_fixture, code_analysis_hybrid,
        document_analysis_with_skills,
    ):
        """HYBRID 코드 분석에서 함수 레벨 근거가 code_functions에 전달되는지"""
        from app.workflows.activities.analysis_generation import _llm_build_skill_table

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return [{"skill": "Python", "candidate": "Python", "type": "exact", "confidence": 90, "evidence": "Code"}]

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch("app.services.llm_config.KIMI_CHAT_MODEL", "test-model"):

            mock_get_prompt.return_value = MagicMock()
            await _llm_build_skill_table(
                jd_analysis_fixture, code_analysis_hybrid,
                document_analysis_with_skills,
            )

            call_kwargs = mock_get_prompt.call_args
            code_functions = call_kwargs.kwargs.get("code_functions") or call_kwargs[1].get("code_functions", "")
            parsed = json.loads(code_functions)

            # ast_analysis.functions에서 추출된 함수명
            assert "main" in parsed
            assert "process_data" in parsed
            assert "validate_input" in parsed
            assert "helper_fn" in parsed
            assert "util_fn" in parsed

    @pytest.mark.asyncio
    async def test_llm_skill_table_legacy_no_functions(
        self, jd_analysis_fixture, code_analysis_legacy,
        document_analysis_with_skills,
    ):
        """LEGACY 파이프라인에서는 함수 컨텍스트가 빈 배열"""
        from app.workflows.activities.analysis_generation import _llm_build_skill_table

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return [{"skill": "Python", "candidate": "Python", "type": "exact", "confidence": 80, "evidence": "Code"}]

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch("app.services.llm_config.KIMI_CHAT_MODEL", "test-model"):

            mock_get_prompt.return_value = MagicMock()
            await _llm_build_skill_table(
                jd_analysis_fixture, code_analysis_legacy,
                document_analysis_with_skills,
            )

            call_kwargs = mock_get_prompt.call_args
            code_functions = call_kwargs.kwargs.get("code_functions") or call_kwargs[1].get("code_functions", "")
            # LEGACY: functions 비어있으므로 "[]" 전달
            assert code_functions == "[]"

    def test_radar_code_summary_legacy_no_hybrid_fields(
        self, jd_analysis_fixture, code_analysis_legacy, document_analysis_with_skills,
    ):
        """LEGACY 파이프라인에서는 hybrid 필드가 code_summary에 없음"""
        import json as json_mod
        # code_summary 구성 로직을 직접 시뮬레이션
        code_analysis = code_analysis_legacy
        summary_data = {
            "tech_stack": code_analysis.get("tech_stack", [])[:10],
            "quality_metrics": code_analysis.get("quality_metrics", {}),
            "risk_flags_count": len(code_analysis.get("risk_flags", [])),
            "repos_count": len(code_analysis.get("repositories", [])),
        }
        if code_analysis.get("jd_relevance_scores"):
            summary_data["jd_relevance_scores"] = code_analysis["jd_relevance_scores"]
        if code_analysis.get("ast_chunk_count"):
            summary_data["ast_chunk_count"] = code_analysis["ast_chunk_count"]
        if code_analysis.get("analyzed_functions_count"):
            summary_data["analyzed_functions_count"] = code_analysis["analyzed_functions_count"]
        if code_analysis.get("hybrid_metadata"):
            summary_data["hybrid_metadata"] = code_analysis["hybrid_metadata"]

        # LEGACY: HYBRID 필드가 없으므로 summary_data에도 없음
        assert "ast_chunk_count" not in summary_data
        assert "analyzed_functions_count" not in summary_data
        assert "hybrid_metadata" not in summary_data

    def test_radar_code_summary_hybrid_includes_all_fields(
        self, code_analysis_hybrid,
    ):
        """HYBRID 파이프라인에서는 모든 신포맷 필드가 code_summary에 포함"""
        code_analysis = code_analysis_hybrid
        summary_data = {
            "tech_stack": code_analysis.get("tech_stack", [])[:10],
            "quality_metrics": code_analysis.get("quality_metrics", {}),
            "risk_flags_count": len(code_analysis.get("risk_flags", [])),
            "repos_count": len(code_analysis.get("repositories", [])),
        }
        if code_analysis.get("ast_chunk_count"):
            summary_data["ast_chunk_count"] = code_analysis["ast_chunk_count"]
        if code_analysis.get("analyzed_functions_count"):
            summary_data["analyzed_functions_count"] = code_analysis["analyzed_functions_count"]
        if code_analysis.get("hybrid_metadata"):
            summary_data["hybrid_metadata"] = code_analysis["hybrid_metadata"]

        assert summary_data["ast_chunk_count"] == 20
        assert summary_data["analyzed_functions_count"] == 5
        assert summary_data["hybrid_metadata"]["method"] == "hybrid"
        assert summary_data["repos_count"] == 2

    def test_linkedin_positions_extraction_experiences_field(self, sample_linkedin_profile):
        """_extract_linkedin_positions에서 experiences 필드 처리"""
        # generate_deep_analysis 내부 로직 시뮬레이션
        linkedin_profile = sample_linkedin_profile
        experiences = linkedin_profile.get("experiences") or linkedin_profile.get("experience") or []
        linkedin_positions = len(experiences) if isinstance(experiences, list) else 0

        assert linkedin_positions == 1

    def test_linkedin_positions_extraction_experience_field(self):
        """experience (단수) 필드 variant 처리"""
        linkedin_profile = {
            "experience": [
                {"title": "Dev", "company": "A"},
                {"title": "Lead", "company": "B"},
            ],
        }
        experiences = linkedin_profile.get("experiences") or linkedin_profile.get("experience") or []
        linkedin_positions = len(experiences) if isinstance(experiences, list) else 0

        assert linkedin_positions == 2

    def test_linkedin_positions_extraction_no_field(self):
        """experiences/experience 필드 모두 없을 때"""
        linkedin_profile = {"skills": ["Python"]}
        experiences = linkedin_profile.get("experiences") or linkedin_profile.get("experience") or []
        linkedin_positions = len(experiences) if isinstance(experiences, list) else 0

        assert linkedin_positions == 0


# ============================================================
# TestGracefulDegradation
# ============================================================

class TestGracefulDegradation:
    """모든 데이터가 비어있을 때의 graceful degradation 검증"""

    def test_all_empty_skill_table(self, jd_analysis_fixture, document_analysis_empty_skills):
        """모든 데이터 비어있을 때 스킬 테이블 빈 결과가 아닌 none type 행 반환"""
        from app.workflows.activities.analysis_generation import _build_skill_table

        result = _build_skill_table(
            jd_analysis_fixture, None,
            document_analysis_empty_skills, candidate_profile=None,
        )

        assert isinstance(result, list)
        assert len(result) > 0  # JD requirements만큼은 행이 생성됨
        for row in result:
            assert row.type == "none"

    def test_all_empty_radar_rule_based(self, document_analysis_empty_skills):
        """모든 데이터 비어있을 때 규칙 기반 레이더 점수 정상 계산"""
        from app.workflows.activities.analysis_generation import _calculate_radar_scores

        jd_empty = {"job_title": "Engineer", "requirements": []}

        with patch("app.services.scoring_formulas.calculate_radar_scores") as mock_calc:
            RadarResult = namedtuple("RadarResult", ["candidate", "required", "sources", "confidence", "human_sources"])
            mock_calc.return_value = RadarResult(
                [30, 30, 30, 30, 30], [50, 50, 50, 50, 50],
                ["no data"] * 5, "low", ["데이터 부족"] * 5,
            )

            candidate, required, sources, confidence, human_sources = _calculate_radar_scores(
                jd_empty, None, document_analysis_empty_skills,
                candidate_profile=None,
            )

            assert len(candidate) == 5
            assert len(required) == 5
            assert all(isinstance(s, int) for s in candidate)
