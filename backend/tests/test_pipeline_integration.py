"""
backend/tests/test_pipeline_integration.py
코드 분석 파이프라인 통합 테스트 (JIT-26)

합성 레포로 전체 파이프라인 E2E 검증.
외부 API/Docker 불필요 — tmp_path 합성 레포만 사용.
"""
import pytest


class TestPipelineIntegration:
    """코드 분석 파이프라인 E2E 통합 테스트"""

    def _create_fastapi_repo(self, tmp_path):
        """합성 FastAPI 프로젝트 레포 생성"""
        (tmp_path / "main.py").write_text(
            "from fastapi import FastAPI\n\n"
            "app = FastAPI()\n\n"
            "@app.get('/health')\n"
            "async def health_check():\n"
            "    return {'status': 'ok'}\n\n"
            "@app.post('/users')\n"
            "async def create_user(name: str):\n"
            "    return {'name': name}\n"
        )
        (tmp_path / "models.py").write_text(
            "from pydantic import BaseModel\n\n"
            "class User(BaseModel):\n"
            "    name: str\n"
            "    email: str\n\n"
            "class UserCreate(BaseModel):\n"
            "    name: str\n"
        )
        (tmp_path / "utils.py").write_text(
            "import os\n\n"
            "def get_env(key: str) -> str:\n"
            "    return os.getenv(key, '')\n"
        )

    def test_directory_to_chunks_to_scoring(self, tmp_path):
        """analyze_directory → rank_chunks: FastAPI 관련 청크가 유틸리티보다 높은 점수"""
        from app.services.ast_analyzer import analyze_directory
        from app.services.chunk_scorer import rank_chunks_by_relevance

        self._create_fastapi_repo(tmp_path)

        # Step 1: analyze_directory
        chunks = analyze_directory(str(tmp_path))
        assert len(chunks) >= 3  # 최소 3개 이상의 함수/클래스 청크

        # Step 2: rank_chunks_by_relevance
        jd_tech_stack = ["Python", "FastAPI", "PostgreSQL"]
        ranked = rank_chunks_by_relevance(
            chunks=chunks,
            jd_tech_stack=jd_tech_stack,
            token_budget=50_000,
        )

        assert len(ranked) >= 1

        # FastAPI 엔드포인트 함수가 유틸리티 함수보다 JD 관련성이 높아야 함
        fastapi_chunks = [c for c in ranked if "fastapi" in " ".join(c.get("imports", [])).lower() or "app" in c.get("source_code", "").lower()]
        util_chunks = [c for c in ranked if c.get("file_path", "").endswith("utils.py")]

        if fastapi_chunks and util_chunks:
            best_fastapi_score = max(
                c.get("relevance_score", {}).get("total_score", 0) for c in fastapi_chunks
            )
            best_util_score = max(
                c.get("relevance_score", {}).get("total_score", 0) for c in util_chunks
            )
            assert best_fastapi_score >= best_util_score

    def test_chunks_to_overview_prompt(self, tmp_path):
        """청크 → build_overview_prompt: 프롬프트에 합성 레포 파일명 포함"""
        from app.services.ast_analyzer import analyze_directory
        from app.services.chunk_scorer import rank_chunks_by_relevance
        from app.services.code_analysis_prompts import build_overview_prompt

        self._create_fastapi_repo(tmp_path)

        chunks = analyze_directory(str(tmp_path))
        ranked = rank_chunks_by_relevance(
            chunks=chunks,
            jd_tech_stack=["Python", "FastAPI"],
            token_budget=50_000,
        )

        prompt = build_overview_prompt(
            files=[{"filename": "main.py", "added": 50, "complexity": 3}],
            commit_diffs=[],
            ast_summary={"functions": [{"name": "health_check"}], "classes": [], "parser_used": "ast"},
            jd_tech_stack=["Python", "FastAPI"],
            ranked_chunks=ranked,
        )

        assert "main.py" in prompt
        assert "JD-Ranked Code Chunks" in prompt
        # 랭킹된 청크 중 하나의 이름이 프롬프트에 포함
        any_chunk_name_in_prompt = any(c["name"] in prompt for c in ranked)
        assert any_chunk_name_in_prompt

    def test_token_budget_respected(self, tmp_path):
        """token_budget=500 → 선택된 청크 총 char_count < budget*4"""
        from app.services.ast_analyzer import analyze_directory
        from app.services.chunk_scorer import rank_chunks_by_relevance

        self._create_fastapi_repo(tmp_path)

        chunks = analyze_directory(str(tmp_path))
        token_budget = 500

        ranked = rank_chunks_by_relevance(
            chunks=chunks,
            jd_tech_stack=["Python", "FastAPI"],
            token_budget=token_budget,
        )

        # 선택된 청크의 총 char_count//4가 토큰 예산 이하
        total_est_tokens = sum(c.get("char_count", 0) // 4 for c in ranked)
        assert total_est_tokens <= token_budget

    @pytest.mark.asyncio
    async def test_validation_on_full_result(self, sample_jd_tech_stack, valid_repo_result):
        """전체 결과 dict → validate_code_analysis, valid=True"""
        from unittest.mock import patch, MagicMock
        from app.workflows.activities.code_analysis import validate_code_analysis

        with patch("app.core.observability.is_langfuse_enabled", return_value=False), \
             patch("app.workflows.activities.code_analysis.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()
            result = await validate_code_analysis(valid_repo_result)

        assert result["valid"] is True
        assert result["issues"] == []
        assert result["metrics"]["commit_count"] == 50
