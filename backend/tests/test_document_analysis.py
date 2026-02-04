"""
backend/tests/test_document_analysis.py
Phase 2: Document Analysis Activity 단위 테스트

테스트 항목:
- P2D-01: 문서 파싱 (Docling primary)
- P2D-02: 문서 파싱 폴백 (pymupdf4llm)
- P2D-03: LLM 프로필 추출
- P2D-04: 문서 없을 때 처리
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ============================================================
# P2D-01: 문서 파싱 테스트
# ============================================================

class TestDocumentParsing:
    """P2D-01: 문서 파싱 테스트"""

    @pytest.mark.asyncio
    async def test_parse_document_txt(self, tmp_path):
        """TXT 파일 파싱"""
        from app.services.document_parser import parse_document

        test_file = tmp_path / "test.txt"
        test_file.write_text("이름: 홍길동\n경력: 5년")

        result = await parse_document(str(test_file))

        assert "홍길동" in result.text
        assert result.parser_used == "plaintext"

    @pytest.mark.asyncio
    async def test_parse_document_not_found(self):
        """존재하지 않는 파일"""
        from app.services.document_parser import parse_document

        with pytest.raises(FileNotFoundError):
            await parse_document("/nonexistent/file.pdf")


# ============================================================
# P2D-03: LLM 프로필 추출 테스트
# ============================================================

class TestLlmProfileExtraction:
    """P2D-03: LLM 프로필 추출 테스트"""

    @pytest.mark.asyncio
    async def test_analyze_documents_returns_profile(self):
        """문서 분석 결과에 프로필 포함"""
        from app.workflows.activities.document_analysis import analyze_documents
        from unittest.mock import patch

        input_data = {"resume_path": "/tmp/resume.txt"}

        class MockParseResult:
            text = "이름: 테스트 유저\n경력: 5년\nGitHub: https://github.com/test"
            parser_used = "plaintext"
            sections = ["header", "experience"]

        mock_profile = {
            "name": "테스트 유저",
            "experience_years": 5,
            "skills": ["Python", "FastAPI"],
        }

        async def mock_parse_document(path):
            return MockParseResult()

        async def mock_llm_run(prompt, **kwargs):
            return mock_profile

        with patch("app.workflows.activities.document_analysis.activity") as mock_activity, \
             patch("app.services.document_parser.parse_document", side_effect=mock_parse_document), \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await analyze_documents(input_data)

            assert "profile" in result
            assert "raw_texts" in result
            assert "parse_info" in result

    @pytest.mark.asyncio
    async def test_analyze_documents_no_documents(self):
        """문서가 없을 때"""
        from app.workflows.activities.document_analysis import analyze_documents
        from unittest.mock import patch

        input_data = {}  # 문서 경로 없음

        with patch("app.workflows.activities.document_analysis.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await analyze_documents(input_data)

            assert result["profile"] == {}
            assert result["raw_texts"] == []
            assert result["parse_info"] == []


# ============================================================
# P2D-04: 오류 처리 테스트
# ============================================================

class TestDocumentAnalysisErrorHandling:
    """문서 분석 오류 처리 테스트"""

    @pytest.mark.asyncio
    async def test_parse_failure_continues(self):
        """파싱 실패 시 계속 진행"""
        from app.workflows.activities.document_analysis import analyze_documents
        from unittest.mock import patch

        input_data = {
            "resume_path": "/tmp/bad.pdf",
            "portfolio_path": "/tmp/good.txt",
        }

        call_count = [0]

        class MockParseResult:
            text = "Portfolio content"
            parser_used = "plaintext"
            sections = []

        async def mock_parse_document(path):
            call_count[0] += 1
            if "bad" in path:
                raise ValueError("Parse failed")
            return MockParseResult()

        async def mock_llm_run(prompt, **kwargs):
            return {"name": "Test"}

        with patch("app.workflows.activities.document_analysis.activity") as mock_activity, \
             patch("app.services.document_parser.parse_document", side_effect=mock_parse_document), \
             patch("app.services.cached_llm.CachedLLMService.run", side_effect=mock_llm_run):

            mock_activity.heartbeat = MagicMock()

            result = await analyze_documents(input_data)

            # 두 파일 모두 시도해야 함
            assert call_count[0] == 2
            # 하나는 성공해서 raw_texts에 포함
            assert len(result["raw_texts"]) == 1


# ============================================================
# Activity 통합 테스트
# ============================================================

class TestDocumentAnalysisIntegration:
    """Document Analysis Activity 통합 테스트"""

    def test_activity_is_defn(self):
        """Activity 데코레이터 확인"""
        from app.workflows.activities.document_analysis import analyze_documents
        assert hasattr(analyze_documents, "__temporal_activity_definition")

    @pytest.mark.asyncio
    async def test_output_structure(self):
        """출력 구조 검증"""
        from app.workflows.activities.document_analysis import analyze_documents
        from unittest.mock import patch

        input_data = {}

        with patch("app.workflows.activities.document_analysis.activity") as mock_activity:
            mock_activity.heartbeat = MagicMock()

            result = await analyze_documents(input_data)

            # 필수 필드 확인
            assert "profile" in result
            assert "raw_texts" in result
            assert "parse_info" in result
