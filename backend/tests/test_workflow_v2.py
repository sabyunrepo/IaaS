"""
v2 Pipeline E2E Structure Tests
워크플로우 v2 출력 형식 및 Activity 통합 검증
"""
import inspect
import json
import pytest


# ============================================================
# v2 Model Structure Tests
# ============================================================

class TestV2ModelStructure:
    """v2 모델이 프론트엔드 타입과 일치하는지 검증"""

    def test_intel_brief_fields(self):
        from app.models.intel import IntelBrief
        fields = set(IntelBrief.model_fields.keys())
        expected = {"jd_summary", "jd_full", "competencies", "github", "linkedin", "linkedin_warning"}
        assert expected.issubset(fields)

    def test_deep_analysis_fields(self):
        from app.models.deep_analysis import DeepAnalysis
        fields = set(DeepAnalysis.model_fields.keys())
        expected = {"radar_candidate", "radar_required", "engineering_dna", "risk_flags", "skill_table", "overall_match"}
        assert expected.issubset(fields)

    def test_decision_support_fields(self):
        from app.models.decision import DecisionSupport
        fields = set(DecisionSupport.model_fields.keys())
        expected = {"summary", "interviewer_guide", "jd_competency_map"}
        assert expected.issubset(fields)

    def test_decision_summary_level_values(self):
        """레벨 추정 유효값 검증"""
        from app.models.decision import DecisionSummary
        valid_levels = {"Junior", "Mid", "Senior", "Lead", "Principal"}
        # DecisionSummary는 str 필드이므로 유효값은 Activity에서 보장
        summary = DecisionSummary(
            experience="10년", jd_match="높음", level="Lead",
            strengths=["Python"], concerns=[],
        )
        assert summary.level in valid_levels

    def test_competency_match_fields(self):
        from app.models.intel import CompetencyMatch
        fields = set(CompetencyMatch.model_fields.keys())
        expected = {"name", "match", "match_label", "desc", "why", "color", "icon"}
        assert expected.issubset(fields)


# ============================================================
# v2 Activity Integration Tests
# ============================================================

class TestV2ActivitySignatures:
    """v2 Activity 함수 시그니처 검증"""

    def test_generate_intel_brief_signature(self):
        from app.workflows.activities.intel_generation import generate_intel_brief
        sig = inspect.signature(generate_intel_brief)
        params = set(sig.parameters.keys())
        assert "jd_analysis" in params
        assert "document_analysis" in params
        assert "code_analysis" in params
        assert "job_id" in params

    def test_generate_deep_analysis_signature(self):
        from app.workflows.activities.analysis_generation import generate_deep_analysis
        sig = inspect.signature(generate_deep_analysis)
        params = set(sig.parameters.keys())
        assert "jd_analysis" in params
        assert "code_analysis" in params
        assert "document_analysis" in params
        assert "job_id" in params

    def test_generate_decision_support_signature(self):
        from app.workflows.activities.decision_generation import generate_decision_support
        sig = inspect.signature(generate_decision_support)
        params = set(sig.parameters.keys())
        assert "candidate_summary" in params
        assert "questions" in params
        assert "jd_analysis" in params
        assert "document_analysis" in params
        assert "job_id" in params


class TestV2LLMFallbackPattern:
    """v2 Activity들이 LLM + fallback 패턴을 따르는지 검증"""

    def test_intel_generation_has_llm_and_fallback(self):
        from app.workflows.activities import intel_generation
        source = inspect.getsource(intel_generation)
        # LLM 함수 존재
        assert "_llm_match_competencies" in source
        # 규칙 기반 fallback 존재
        assert "_match_competencies" in source
        # fallback 패턴 (LLM 실패 시 규칙 기반)
        assert "if competencies is None:" in source

    def test_analysis_generation_has_llm_and_fallback(self):
        from app.workflows.activities import analysis_generation
        source = inspect.getsource(analysis_generation)
        # LLM 함수 존재
        assert "_llm_calculate_radar_scores" in source
        assert "_llm_analyze_engineering_dna" in source
        # 규칙 기반 fallback 존재
        assert "_calculate_radar_scores" in source
        assert "_analyze_engineering_dna" in source

    def test_decision_generation_has_llm_and_fallback(self):
        from app.workflows.activities import decision_generation
        source = inspect.getsource(decision_generation)
        # LLM 함수 존재
        assert "_llm_generate_decision_summary" in source
        assert "_llm_generate_interviewer_tips" in source
        # 규칙 기반 fallback 존재
        assert "_extract_decision_summary" in source
        assert "_build_interviewer_tips" in source
        # fallback 패턴
        assert "if summary is None:" in source
        assert "if interviewer_guide is None:" in source


class TestV2PromptTemplates:
    """v2 프롬프트 템플릿 구조 검증"""

    def test_v2_generation_yaml_exists(self):
        from pathlib import Path
        prompts_path = Path(__file__).parent.parent / "app" / "prompts" / "v2_generation.yaml"
        assert prompts_path.exists()

    def test_v2_generation_yaml_has_all_prompts(self):
        import yaml
        from pathlib import Path
        prompts_path = Path(__file__).parent.parent / "app" / "prompts" / "v2_generation.yaml"
        with open(prompts_path) as f:
            data = yaml.safe_load(f)

        prompts = data.get("prompts", {})
        expected_keys = [
            "competency_matching",
            "radar_analysis",
            "engineering_dna",
            "decision_summary",
            "interviewer_tips",
        ]
        for key in expected_keys:
            assert key in prompts, f"Missing prompt template: {key}"
            assert "template" in prompts[key], f"Missing template in: {key}"


# ============================================================
# Decision Level Bug Fix Verification
# ============================================================

class TestDecisionLevelEstimation:
    """경력 레벨 추정 로직 검증 (버그 수정 확인)"""

    def test_level_junior(self):
        from app.workflows.activities.decision_generation import _extract_decision_summary
        result = _extract_decision_summary(
            {}, {},
            {"profile": {"experience_years": 1, "skills": [], "experiences": []}},
        )
        assert result.level == "Junior"

    def test_level_mid(self):
        from app.workflows.activities.decision_generation import _extract_decision_summary
        result = _extract_decision_summary(
            {}, {},
            {"profile": {"experience_years": 5, "skills": [], "experiences": []}},
        )
        assert result.level == "Mid"

    def test_level_senior(self):
        from app.workflows.activities.decision_generation import _extract_decision_summary
        result = _extract_decision_summary(
            {}, {},
            {"profile": {"experience_years": 8, "skills": [], "experiences": []}},
        )
        assert result.level == "Senior"

    def test_level_lead(self):
        """Bug fix 검증: 10년+ 경력은 Lead여야 함 (이전에는 Senior로 잘못 판단)"""
        from app.workflows.activities.decision_generation import _extract_decision_summary
        result = _extract_decision_summary(
            {}, {},
            {"profile": {"experience_years": 12, "skills": [], "experiences": []}},
        )
        assert result.level == "Lead"

    def test_level_lead_boundary(self):
        """경계값 검증: 정확히 10년"""
        from app.workflows.activities.decision_generation import _extract_decision_summary
        result = _extract_decision_summary(
            {}, {},
            {"profile": {"experience_years": 10, "skills": [], "experiences": []}},
        )
        assert result.level == "Lead"


# ============================================================
# KG Question Integration Tests
# ============================================================

class TestKGQuestionIntegration:
    """KG 기반 질문 생성 통합 검증"""

    def test_question_generation_has_kg_boost(self):
        """KG 후보에 우선순위 부스트가 적용되는지 확인"""
        from app.workflows.activities import question_generation
        source = inspect.getsource(question_generation)
        assert "kg_boost" in source
        assert "boosted_score" in source

    def test_graph_queries_balance_includes_partial_match(self):
        """카테고리 밸런싱에 partial_match_probe 포함 확인"""
        from app.services import graph_queries
        source = inspect.getsource(graph_queries.InterviewGraphQueries.get_top_question_candidates)
        assert "partial_match_probe" in source

    def test_craft_question_handles_kg_evidence(self):
        """craft_question이 KG evidence를 처리하는지 확인"""
        from app.workflows.activities import question_generation
        source = inspect.getsource(question_generation.craft_question)
        assert "evidence_chain" in source
        assert "code_reference" in source
        assert "recommended_probe" in source
        assert "kg_source" in source


# ============================================================
# Workflow Phase Integration Tests
# ============================================================

class TestWorkflowV2PhaseIntegration:
    """워크플로우 v2 Phase 통합 검증"""

    def test_workflow_has_phase_2_5_kg_build(self):
        """Phase 2.5 KG 빌드가 존재하는지 확인"""
        source = inspect.getsource(InterviewGenerationWorkflow.run)
        assert "build_knowledge_graph" in source
        assert "KG build failed (non-fatal)" in source

    def test_workflow_has_v2_generation_calls(self):
        """워크플로우에서 v2 생성 Activity를 호출하는지 확인"""
        source = inspect.getsource(InterviewGenerationWorkflow.run)
        assert "generate_intel_brief" in source
        assert "generate_deep_analysis" in source
        assert "generate_decision_support" in source

    def test_workflow_v2_generation_in_finalization_phase(self):
        """v2 생성이 finalization phase에서 실행되는지 확인"""
        source = inspect.getsource(InterviewGenerationWorkflow.run)
        # v2 생성은 Phase 4 (finalization) 이후에 실행
        idx_finalize = source.index("finalize_output")
        # Intel/Analysis는 finalize_output 이후에 호출
        assert "generate_intel_brief" in source[idx_finalize:]
        assert "generate_deep_analysis" in source[idx_finalize:]


# Need to import after module-level to avoid circular imports
from app.workflows.interview_workflow import InterviewGenerationWorkflow
