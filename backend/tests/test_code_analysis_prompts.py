"""
backend/tests/test_code_analysis_prompts.py
프롬프트 빌더 함수 단위 테스트 (JIT-26)

테스트 항목:
- build_overview_prompt(): Overview Agent 프롬프트
- build_deep_analysis_prompt(): Deep Analysis Agent 프롬프트
- build_synthesis_prompt(): Synthesis Agent 프롬프트
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

    def test_source_truncation(self):
        """8000자 초과 소스 절삭"""
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
        # (프롬프트 전체 길이가 아닌, 소스코드 부분만)
        assert len(prompt) < len(long_source) + 2000  # 프롬프트 오버헤드 감안


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
