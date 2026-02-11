"""
backend/tests/test_code_analysis_prompts.py
프롬프트 빌더 함수 단위 테스트 (JIT-26, JIT-28)

테스트 항목:
- build_overview_prompt(): Overview Agent 프롬프트
- build_deep_analysis_prompt(): Deep Analysis Agent 프롬프트 + 토큰 예산 동적화
- build_synthesis_prompt(): Synthesis Agent 프롬프트 + JD relevance score
"""
import pytest

from app.services.code_analysis_prompts import (
    build_overview_prompt,
    build_deep_analysis_prompt,
    build_synthesis_prompt,
)


# ============================================================
# TestBuildOverviewPrompt
# ============================================================

class TestBuildOverviewPrompt:
    """build_overview_prompt — Stage 1 프롬프트 생성"""

    def test_basic_structure(self):
        """프롬프트에 'Tech Stack', 'File Summary' 섹션 포함"""
        prompt = build_overview_prompt(
            files=[{"filename": "main.py", "added": 100, "complexity": 5}],
            commit_diffs=[{"file_path": "main.py", "commit_hash": "abc123", "diff": "+print('hi')"}],
            ast_summary={"functions": [{"name": "main"}], "classes": [], "parser_used": "ast"},
            jd_tech_stack=["Python", "FastAPI"],
        )

        assert "Tech Stack" in prompt
        assert "File Summary" in prompt
        assert "Python" in prompt
        assert "FastAPI" in prompt
        assert "main.py" in prompt

    def test_with_ranked_chunks(self):
        """ranked_chunks 전달 시 청크 메타데이터 포함"""
        ranked_chunks = [
            {
                "name": "handle_request",
                "type": "function",
                "file_path": "api/routes.py",
                "char_count": 500,
                "identifiers": ["request", "response"],
                "imports": ["from fastapi import Request"],
                "relevance_score": {
                    "total_score": 0.85,
                    "jd_keyword_score": 0.7,
                },
            }
        ]

        prompt = build_overview_prompt(
            files=[],
            commit_diffs=[],
            ast_summary={"functions": [], "classes": [], "parser_used": "ast"},
            jd_tech_stack=["Python"],
            ranked_chunks=ranked_chunks,
        )

        assert "JD-Ranked Code Chunks" in prompt
        assert "handle_request" in prompt
        assert "api/routes.py" in prompt

    def test_without_ranked_chunks(self):
        """ranked_chunks=None → 청크 섹션 생략"""
        prompt = build_overview_prompt(
            files=[],
            commit_diffs=[],
            ast_summary={"functions": [], "classes": [], "parser_used": "ast"},
            jd_tech_stack=["Python"],
            ranked_chunks=None,
        )

        assert "JD-Ranked Code Chunks" not in prompt

    def test_empty_inputs(self):
        """모든 빈 입력 → 에러 없이 유효한 프롬프트"""
        prompt = build_overview_prompt(
            files=[],
            commit_diffs=[],
            ast_summary={},
            jd_tech_stack=[],
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 50  # 프롬프트 프레임워크 최소 길이
        assert "Your Task" in prompt


# ============================================================
# TestBuildDeepAnalysisPrompt
# ============================================================

class TestBuildDeepAnalysisPrompt:
    """build_deep_analysis_prompt — Stage 2 프롬프트 생성"""

    def test_source_code_priority(self):
        """source_code 있으면 diff 대신 사용"""
        prompt = build_deep_analysis_prompt(
            file_info={
                "path": "service.py",
                "source_code": "def create_user(name):\n    return User(name=name)\n",
                "diff": "should not appear",
            },
            commit_history=[],
            jd_tech_stack=["Python"],
        )

        assert "create_user" in prompt
        assert "should not appear" not in prompt
        assert "Source Code" in prompt

    def test_diff_fallback(self):
        """source_code 없으면 diff 사용"""
        prompt = build_deep_analysis_prompt(
            file_info={
                "path": "service.py",
                "diff": "+def old_func():\n+    pass",
            },
            commit_history=[],
            jd_tech_stack=["Python"],
        )

        assert "old_func" in prompt
        assert "Code/Diff Content" in prompt

    def test_metadata_section(self):
        """identifiers/imports/decorators → 'Code Metadata' 섹션"""
        prompt = build_deep_analysis_prompt(
            file_info={
                "path": "handler.py",
                "source_code": "pass",
                "identifiers": ["Request", "Response", "JSONResponse"],
                "imports": ["from fastapi import Request"],
                "decorators": ["app.get"],
                "relevance_score": {
                    "jd_keyword_score": 0.8,
                    "interview_potential": 0.6,
                },
            },
            commit_history=[],
            jd_tech_stack=["FastAPI"],
        )

        assert "Code Metadata" in prompt
        assert "Request" in prompt
        assert "fastapi" in prompt
        assert "app.get" in prompt
        assert "JD Relevance" in prompt

    def test_source_truncation_default(self):
        """기본 8000자 예산으로 소스 절삭"""
        long_source = "x = 1\n" * 2000  # ~12K chars
        prompt = build_deep_analysis_prompt(
            file_info={
                "path": "big.py",
                "source_code": long_source,
            },
            commit_history=[],
            jd_tech_stack=[],
        )

        # 프롬프트 내 소스코드가 8000자 이하로 잘림
        assert len(prompt) < len(long_source) + 2000  # 프롬프트 오버헤드 감안

    def test_token_budget_20k(self):
        """JIT-28: token_budget=20000 → 20K자까지 허용"""
        long_source = "y = 2\n" * 5000  # ~25K chars
        prompt = build_deep_analysis_prompt(
            file_info={
                "path": "big.py",
                "source_code": long_source,
            },
            commit_history=[],
            jd_tech_stack=[],
            token_budget=20_000,
        )

        # 20K 예산: 소스가 20000자로 절삭되어야 함
        assert "y = 2" in prompt
        # 25K 원본보다 짧아야 함 (20K + 오버헤드)
        assert len(prompt) < 23_000

    def test_token_budget_50k(self):
        """JIT-28: token_budget=50000 → 50K자까지 허용"""
        long_source = "z = 3\n" * 12000  # ~60K chars
        prompt = build_deep_analysis_prompt(
            file_info={
                "path": "huge.py",
                "source_code": long_source,
            },
            commit_history=[],
            jd_tech_stack=[],
            token_budget=50_000,
        )

        # 50K 예산: 60K 원본이 50K로 절삭
        assert len(prompt) < 53_000

    def test_token_budget_clamp_minimum(self):
        """JIT-28: token_budget < 2000 → 2000으로 클램핑"""
        source = "a = 1\n" * 1000  # ~6K chars
        prompt = build_deep_analysis_prompt(
            file_info={
                "path": "small.py",
                "source_code": source,
            },
            commit_history=[],
            jd_tech_stack=[],
            token_budget=500,  # 2000 미만 → 2000으로 클램핑
        )

        # 2000자 + 오버헤드 이내
        assert len(prompt) < 5000

    def test_token_budget_clamp_maximum(self):
        """JIT-28: token_budget > 50000 → 50000으로 클램핑"""
        long_source = "b = 1\n" * 20000  # ~100K chars
        prompt = build_deep_analysis_prompt(
            file_info={
                "path": "massive.py",
                "source_code": long_source,
            },
            commit_history=[],
            jd_tech_stack=[],
            token_budget=100_000,  # 50000 초과 → 50000으로 클램핑
        )

        # 50K 클램핑 + 오버헤드 이내
        assert len(prompt) < 53_000


# ============================================================
# TestBuildSynthesisPrompt
# ============================================================

class TestBuildSynthesisPrompt:
    """build_synthesis_prompt — Stage 3 프롬프트 생성"""

    def test_basic_structure(self):
        """'Overview Analysis', 'Deep Analysis Results' 섹션 포함"""
        prompt = build_synthesis_prompt(
            overview={
                "tech_overview": "FastAPI backend service",
                "primary_languages": ["Python"],
                "frameworks_detected": ["FastAPI"],
                "key_files": [{"path": "main.py"}],
            },
            deep_analyses=[
                {
                    "file_path": "main.py",
                    "patterns_found": ["Repository"],
                    "algorithms_used": [],
                    "code_quality_score": 0.8,
                    "notable_aspects": ["Clean architecture"],
                    "question_candidates": ["How did you design the API?"],
                }
            ],
            repo_info={"name": "test-repo"},
            jd_tech_stack=["Python", "FastAPI"],
        )

        assert "Overview Analysis" in prompt
        assert "Deep Analysis Results" in prompt
        assert "test-repo" in prompt
        assert "FastAPI backend service" in prompt
        assert "Repository" in prompt
        assert "main.py" in prompt

    def test_jd_relevance_in_deep_analyses(self):
        """JIT-28: deep_analyses에 relevance_score → JD Relevance 라인 포함"""
        prompt = build_synthesis_prompt(
            overview={
                "tech_overview": "API service",
                "primary_languages": ["Python"],
                "frameworks_detected": [],
                "key_files": [],
            },
            deep_analyses=[
                {
                    "file_path": "api/handler.py",
                    "patterns_found": ["Factory"],
                    "algorithms_used": [],
                    "code_quality_score": 0.9,
                    "notable_aspects": ["Clean error handling"],
                    "question_candidates": ["Q1"],
                    "relevance_score": {
                        "jd_keyword_score": 0.85,
                        "interview_potential": 0.7,
                        "confidence": "high",
                    },
                }
            ],
            repo_info={"name": "api-repo"},
            jd_tech_stack=["Python"],
        )

        assert "JD Relevance" in prompt
        assert "keyword=0.85" in prompt
        assert "interview_potential=0.70" in prompt
        assert "confidence=high" in prompt

    def test_jd_relevance_ranking_section(self):
        """JIT-28: overview의 key_files → JD Relevance Ranking 섹션"""
        prompt = build_synthesis_prompt(
            overview={
                "tech_overview": "Backend",
                "primary_languages": ["Python"],
                "frameworks_detected": [],
                "key_files": [
                    {"path": "models.py", "relevance_score": 0.9, "reason": "Core data models"},
                    {"path": "routes.py", "relevance_score": 0.7, "reason": "API endpoints"},
                ],
            },
            deep_analyses=[],
            repo_info={"name": "test"},
            jd_tech_stack=["Python"],
        )

        assert "JD Relevance Ranking" in prompt
        assert "models.py" in prompt
        assert "relevance=0.9" in prompt
        assert "Core data models" in prompt

    def test_no_relevance_score_graceful(self):
        """JIT-28: relevance_score 없는 deep_analyses → JD Relevance 라인 생략"""
        prompt = build_synthesis_prompt(
            overview={
                "tech_overview": "Service",
                "primary_languages": [],
                "frameworks_detected": [],
                "key_files": [],
            },
            deep_analyses=[
                {
                    "file_path": "util.py",
                    "patterns_found": [],
                    "algorithms_used": [],
                    "code_quality_score": 0.5,
                    "notable_aspects": [],
                    "question_candidates": [],
                    # relevance_score 없음
                }
            ],
            repo_info={"name": "test"},
            jd_tech_stack=[],
        )

        assert "JD Relevance" not in prompt
        assert "JD Relevance Ranking" not in prompt

    def test_empty_key_files_no_ranking_section(self):
        """JIT-28: key_files=[] → JD Relevance Ranking 섹션 생략"""
        prompt = build_synthesis_prompt(
            overview={
                "tech_overview": "Service",
                "primary_languages": [],
                "frameworks_detected": [],
                "key_files": [],
            },
            deep_analyses=[],
            repo_info={"name": "test"},
            jd_tech_stack=[],
        )

        assert "JD Relevance Ranking" not in prompt
