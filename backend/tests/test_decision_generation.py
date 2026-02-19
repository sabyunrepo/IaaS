"""
backend/tests/test_decision_generation.py
JIT-43 통합 테스트: Decision Summary + Interviewer Tips 데이터 흐름 검증
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.decision import DecisionSummary, InterviewerGuideTips, ResumeTip, CoverLetterInsight


# Mock 패치 경로
HEARTBEAT_PATCH = "temporalio.activity.heartbeat"
RUN_LLM_PATCH = "app.workflows.utils.run_llm_with_prompt_config_heartbeat"
GET_PROMPT_PATCH = "app.prompts.get_prompt_with_config"
CACHED_LLM_PATCH = "app.services.cached_llm.CachedLLMService"


# ============================================================
# TestDecisionSummaryIntegration (JIT-43)
# ============================================================

class TestDecisionSummaryIntegration:
    """Decision Summary 생성의 candidate_profile 통합 검증"""

    @pytest.mark.asyncio
    async def test_decision_with_candidate_profile_skills(
        self, jd_analysis_fixture, document_analysis_with_skills,
        candidate_profile_with_skills,
    ):
        """candidate_profile.skills primary, skill_sources에 소스 태그"""
        from app.workflows.activities.decision_generation import _llm_generate_decision_summary

        captured_config = {}

        async def mock_run_llm(llm, prompt_config, **kwargs):
            captured_config["prompt_config"] = prompt_config
            return {
                "experience": "5년 경력",
                "jd_match": "높음",
                "level": "시니어",
                "level_evidence": "SFIA v9: 5년 경력",
                "strengths": ["Python 활용 이력서 경력 (Resume)", "FastAPI 경험 다수"],
                "concerns": ["분산 시스템 경험 부족"],
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH):

            mock_get_prompt.return_value = MagicMock()

            candidate_summary = {"key_strengths": ["Good coding"]}
            result = await _llm_generate_decision_summary(
                candidate_summary, jd_analysis_fixture,
                document_analysis_with_skills,
                candidate_profile=candidate_profile_with_skills,
            )

            # get_prompt_with_config에 candidate_profile 데이터 전달 확인
            call_kwargs = mock_get_prompt.call_args
            cp_arg = call_kwargs.kwargs.get("candidate_profile") or call_kwargs[1].get("candidate_profile", "")
            parsed = json.loads(cp_arg)

            # candidate_profile.skills가 primary 소스
            assert "Python" in parsed["skills"]
            assert "FastAPI" in parsed["skills"]

            # skill_sources에 소스 태그 포함
            assert "Python" in parsed["skill_sources"]
            assert "resume" in parsed["skill_sources"]["Python"]
            assert "github" in parsed["skill_sources"]["Python"]

            # linkedin_experiences가 포함
            assert "linkedin_experiences" in parsed
            assert len(parsed["linkedin_experiences"]) > 0

            assert result is not None
            assert isinstance(result, DecisionSummary)

    @pytest.mark.asyncio
    async def test_decision_fallback_to_document_analysis(
        self, jd_analysis_fixture, document_analysis_with_skills,
    ):
        """candidate_profile 없을 때 document_analysis.profile.skills 사용"""
        from app.workflows.activities.decision_generation import _llm_generate_decision_summary

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "experience": "5년",
                "jd_match": "중간",
                "level": "미들",
                "level_evidence": "경력 기반",
                "strengths": ["Python 경험 (Resume)"],
                "concerns": [],
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH):

            mock_get_prompt.return_value = MagicMock()

            result = await _llm_generate_decision_summary(
                {"key_strengths": []}, jd_analysis_fixture,
                document_analysis_with_skills,
                candidate_profile=None,
            )

            call_kwargs = mock_get_prompt.call_args
            cp_arg = call_kwargs.kwargs.get("candidate_profile") or call_kwargs[1].get("candidate_profile", "")
            parsed = json.loads(cp_arg)

            # document_analysis.profile.skills로 폴백
            assert "Python" in parsed["skills"]
            assert "JavaScript" in parsed["skills"]
            assert "Docker" in parsed["skills"]

            # skill_sources는 빈 dict
            assert parsed["skill_sources"] == {}

            assert result is not None

    @pytest.mark.asyncio
    async def test_strengths_multi_source_tagging(
        self, jd_analysis_fixture, document_analysis_with_skills,
        candidate_profile_with_skills,
    ):
        """multi-source 스킬이 "(Multi-source)" 태그 자동 보강"""
        from app.workflows.activities.decision_generation import _llm_generate_decision_summary

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "experience": "5년",
                "jd_match": "높음",
                "level": "시니어",
                "level_evidence": "SFIA v9",
                # Python은 resume+github (multi-source) → 태그 보강 대상
                "strengths": ["Python 이력서 활용 경험이 풍부함"],
                "concerns": [],
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH, return_value=MagicMock()), \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH):

            result = await _llm_generate_decision_summary(
                {"key_strengths": []}, jd_analysis_fixture,
                document_analysis_with_skills,
                candidate_profile=candidate_profile_with_skills,
            )

            # "이력서" 키워드 + Python이 multi-source → "(Multi-source)" 태그
            assert result is not None
            tagged = [s for s in result.strengths if "(Multi-source)" in s]
            assert len(tagged) >= 1

    @pytest.mark.asyncio
    async def test_strengths_github_source_tagging(
        self, jd_analysis_fixture, document_analysis_with_skills,
        candidate_profile_with_skills,
    ):
        """GitHub 키워드 감지 시 "(GitHub)" 태그"""
        from app.workflows.activities.decision_generation import _llm_generate_decision_summary

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "experience": "5년",
                "jd_match": "높음",
                "level": "시니어",
                "level_evidence": "SFIA v9",
                "strengths": [
                    "GitHub 레포에서 활발한 커밋 활동",
                    "코드 품질이 우수",
                ],
                "concerns": [],
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH, return_value=MagicMock()), \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH):

            result = await _llm_generate_decision_summary(
                {"key_strengths": []}, jd_analysis_fixture,
                document_analysis_with_skills,
                candidate_profile=candidate_profile_with_skills,
            )

            assert result is not None
            # "GitHub" 키워드 → "(GitHub)" 태그
            github_tagged = [s for s in result.strengths if "(GitHub)" in s]
            assert len(github_tagged) >= 1

    @pytest.mark.asyncio
    async def test_code_depth_context_hybrid(
        self, jd_analysis_fixture, document_analysis_with_skills,
        candidate_profile_with_skills, code_analysis_hybrid,
    ):
        """code_analysis에 HYBRID 메타데이터 있을 때 code_depth_context 생성"""
        from app.workflows.activities.decision_generation import _llm_generate_decision_summary

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "experience": "5년",
                "jd_match": "높음",
                "level": "시니어",
                "level_evidence": "SFIA",
                "strengths": ["Good"],
                "concerns": [],
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH):

            mock_get_prompt.return_value = MagicMock()

            await _llm_generate_decision_summary(
                {"key_strengths": []}, jd_analysis_fixture,
                document_analysis_with_skills,
                candidate_profile=candidate_profile_with_skills,
                code_analysis=code_analysis_hybrid,
            )

            call_kwargs = mock_get_prompt.call_args

            # code_depth_context가 프롬프트에 전달됨
            code_depth = call_kwargs.kwargs.get("code_depth_context") or call_kwargs[1].get("code_depth_context", "")
            assert "5 functions" in code_depth
            assert "20 AST chunks" in code_depth

            # candidate_profile_data에도 포함
            cp_arg = call_kwargs.kwargs.get("candidate_profile") or call_kwargs[1].get("candidate_profile", "")
            parsed = json.loads(cp_arg)
            assert "code_depth_context" in parsed


# ============================================================
# TestInterviewerTipsIntegration (JIT-43)
# ============================================================

class TestInterviewerTipsIntegration:
    """면접관 팁 생성의 candidate_profile 통합 검증"""

    @pytest.mark.asyncio
    async def test_tips_with_candidate_profile(
        self, jd_analysis_fixture, document_analysis_with_skills,
        candidate_profile_with_skills,
    ):
        """candidate_profile.experiences/areas_to_probe가 primary"""
        from app.workflows.activities.decision_generation import _llm_generate_interviewer_tips

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "resume_based_tips": [
                    {"section": "경력", "insight": "확인 필요", "question_link": None},
                ],
                "cover_letter_insights": [],
                "red_flags_to_watch": ["분산 시스템 경험 부족"],
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH):

            mock_get_prompt.return_value = MagicMock()

            questions = [{"question_text": "Python 경험은?", "category": "technical"}]
            result = await _llm_generate_interviewer_tips(
                questions, document_analysis_with_skills,
                jd_analysis_fixture,
                candidate_profile=candidate_profile_with_skills,
            )

            call_kwargs = mock_get_prompt.call_args
            cp_arg = call_kwargs.kwargs.get("candidate_profile") or call_kwargs[1].get("candidate_profile", "")
            parsed = json.loads(cp_arg)

            # candidate_profile.experiences가 primary
            assert len(parsed["experiences"]) > 0
            assert parsed["experiences"][0]["company"] == "TechCorp"

            # areas_to_probe가 전달
            assert len(parsed["areas_to_probe"]) > 0
            assert "Distributed system experience gap" in parsed["areas_to_probe"]

            # unified_skills가 포함
            assert "unified_skills" in parsed
            skill_names = [s["name"] for s in parsed["unified_skills"]]
            assert "Python" in skill_names

            # linkedin_experiences 포함
            assert "linkedin_experiences" in parsed
            assert len(parsed["linkedin_experiences"]) > 0

            # linkedin_honors 포함
            assert "linkedin_honors" in parsed

            assert result is not None
            assert isinstance(result, InterviewerGuideTips)

    @pytest.mark.asyncio
    async def test_tips_fallback_to_document_analysis(
        self, jd_analysis_fixture, document_analysis_with_skills,
    ):
        """candidate_profile 없을 때 document_analysis fallback"""
        from app.workflows.activities.decision_generation import _llm_generate_interviewer_tips

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "resume_based_tips": [
                    {"section": "경력", "insight": "확인", "question_link": None},
                ],
                "cover_letter_insights": [],
                "red_flags_to_watch": [],
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH):

            mock_get_prompt.return_value = MagicMock()

            questions = [{"question_text": "경험?", "category": "behavioral"}]
            result = await _llm_generate_interviewer_tips(
                questions, document_analysis_with_skills,
                jd_analysis_fixture,
                candidate_profile=None,
            )

            call_kwargs = mock_get_prompt.call_args
            cp_arg = call_kwargs.kwargs.get("candidate_profile") or call_kwargs[1].get("candidate_profile", "")
            parsed = json.loads(cp_arg)

            # document_analysis.profile.experiences로 폴백
            assert len(parsed["experiences"]) > 0
            assert parsed["experiences"][0]["company"] == "OldCorp"

            # unified_skills, linkedin 관련 필드 없음
            assert "unified_skills" not in parsed
            assert "linkedin_experiences" not in parsed

            assert result is not None

    @pytest.mark.asyncio
    async def test_tips_linkedin_enrichment(
        self, jd_analysis_fixture, document_analysis_with_skills,
        candidate_profile_with_skills,
    ):
        """linkedin_experiences, linkedin_honors가 프롬프트에 포함"""
        from app.workflows.activities.decision_generation import _llm_generate_interviewer_tips

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "resume_based_tips": [],
                "cover_letter_insights": [],
                "red_flags_to_watch": [],
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH) as mock_get_prompt, \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH):

            mock_get_prompt.return_value = MagicMock()

            result = await _llm_generate_interviewer_tips(
                [{"question_text": "Q1", "category": "tech"}],
                document_analysis_with_skills,
                jd_analysis_fixture,
                candidate_profile=candidate_profile_with_skills,
            )

            call_kwargs = mock_get_prompt.call_args
            cp_arg = call_kwargs.kwargs.get("candidate_profile") or call_kwargs[1].get("candidate_profile", "")
            parsed = json.loads(cp_arg)

            # linkedin_experiences가 포함
            assert "linkedin_experiences" in parsed
            assert parsed["linkedin_experiences"][0]["company"] == "TechCorp"
            assert parsed["linkedin_experiences"][0]["title"] == "Senior Engineer"

            # linkedin_honors가 포함
            assert "linkedin_honors" in parsed
            assert parsed["linkedin_honors"][0]["title"] == "Top Contributor 2024"

    @pytest.mark.asyncio
    async def test_tips_red_flags_source_tags(
        self, jd_analysis_fixture, document_analysis_with_skills,
        candidate_profile_with_skills,
    ):
        """red_flags에 소스 태그 자동 보강"""
        from app.workflows.activities.decision_generation import _llm_generate_interviewer_tips

        async def mock_run_llm(llm, prompt_config, **kwargs):
            return {
                "resume_based_tips": [],
                "cover_letter_insights": [],
                "red_flags_to_watch": [
                    "GitHub 커밋 빈도가 낮음",
                    "LinkedIn 경력 검증 필요",
                    "이력서 경험 과장 가능성",
                    "기존 태그 있음 (GitHub)",  # 이미 태그 있음 → 재태그 안 함
                ],
            }

        with patch(RUN_LLM_PATCH, side_effect=mock_run_llm), \
             patch(GET_PROMPT_PATCH, return_value=MagicMock()), \
             patch(CACHED_LLM_PATCH), \
             patch(HEARTBEAT_PATCH):

            result = await _llm_generate_interviewer_tips(
                [{"question_text": "Q1", "category": "tech"}],
                document_analysis_with_skills,
                jd_analysis_fixture,
                candidate_profile=candidate_profile_with_skills,
            )

            assert result is not None
            flags = result.red_flags_to_watch

            # GitHub 키워드 → "(GitHub)" 태그
            github_flags = [f for f in flags if "(GitHub)" in f]
            assert len(github_flags) >= 1

            # LinkedIn 키워드 → "(LinkedIn)" 태그
            linkedin_flags = [f for f in flags if "(LinkedIn)" in f]
            assert len(linkedin_flags) >= 1

            # 이력서 키워드 → "(Resume)" 태그
            resume_flags = [f for f in flags if "(Resume)" in f]
            assert len(resume_flags) >= 1

            # 이미 태그가 있는 항목은 중복 태그 안 됨
            double_tagged = [f for f in flags if f.count("(GitHub)") > 1]
            assert len(double_tagged) == 0


# ============================================================
# TestDecisionSummaryExtraction (규칙 기반 fallback)
# ============================================================

class TestDecisionSummaryExtraction:
    """규칙 기반 Decision Summary 추출 동작 검증"""

    def test_extract_decision_summary_basic(
        self, jd_analysis_fixture, document_analysis_with_skills,
    ):
        """기본 규칙 기반 추출 동작"""
        from app.workflows.activities.decision_generation import _extract_decision_summary

        candidate_summary = {
            "key_strengths": [
                {"strength": "Python 능숙", "evidence": {"resume": True, "github": True}},
            ],
        }

        result = _extract_decision_summary(
            candidate_summary, jd_analysis_fixture,
            document_analysis_with_skills,
        )

        assert isinstance(result, DecisionSummary)
        assert result.experience != ""
        assert result.level != ""
        assert result.level_evidence != ""
        assert len(result.strengths) > 0

    def test_extract_decision_summary_empty_data(self, jd_analysis_fixture):
        """데이터가 모두 비어있을 때 graceful 처리"""
        from app.workflows.activities.decision_generation import _extract_decision_summary

        empty_doc = {"profile": {"skills": [], "experience_years": 0, "experiences": []}, "jd_match_score": 0.3}

        result = _extract_decision_summary(
            {}, jd_analysis_fixture, empty_doc,
        )

        assert isinstance(result, DecisionSummary)
        # 빈 데이터여도 에러 없이 DecisionSummary 생성
        assert result.jd_match != ""
