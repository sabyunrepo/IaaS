"""Document parser and document analysis activity tests."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from dataclasses import fields


class TestParseResult:
    def test_parse_result_dataclass(self):
        from app.services.document_parser import ParseResult
        r = ParseResult(text="hello", parser_used="docling")
        assert r.text == "hello"
        assert r.metadata == {}
        assert r.sections == []
        assert r.parser_used == "docling"

    def test_parse_result_fields(self):
        from app.services.document_parser import ParseResult
        names = {f.name for f in fields(ParseResult)}
        assert names == {"text", "metadata", "sections", "parser_used"}


class TestSupportedExtensions:
    def test_pdf_supported(self):
        from app.services.document_parser import SUPPORTED_EXTENSIONS
        assert ".pdf" in SUPPORTED_EXTENSIONS

    def test_docx_supported(self):
        from app.services.document_parser import SUPPORTED_EXTENSIONS
        assert ".docx" in SUPPORTED_EXTENSIONS

    def test_unsupported_extension(self):
        from app.services.document_parser import SUPPORTED_EXTENSIONS
        assert ".xyz" not in SUPPORTED_EXTENSIONS


class TestExtractSections:
    def test_extract_sections_basic(self):
        from app.services.document_parser import _extract_sections
        text = "# Title\nContent here\n## Sub\nMore content"
        sections = _extract_sections(text)
        assert len(sections) >= 2
        assert sections[0]["title"] == "Title"

    def test_extract_sections_empty(self):
        from app.services.document_parser import _extract_sections
        sections = _extract_sections("")
        assert isinstance(sections, list)

    def test_extract_sections_no_headers(self):
        from app.services.document_parser import _extract_sections
        sections = _extract_sections("Just plain text\nAnother line")
        assert len(sections) == 1
        assert sections[0]["title"] == "Introduction"


class TestParseDocumentValidation:
    @pytest.mark.asyncio
    async def test_file_not_found(self):
        from app.services.document_parser import parse_document
        with pytest.raises(FileNotFoundError):
            await parse_document("/nonexistent/file.pdf")

    @pytest.mark.asyncio
    async def test_unsupported_format(self, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("data")
        from app.services.document_parser import parse_document
        with pytest.raises(ValueError, match="Unsupported"):
            await parse_document(str(f))

    @pytest.mark.asyncio
    async def test_plaintext_fallback(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello world")
        from app.services.document_parser import parse_document
        result = await parse_document(str(f))
        assert result.text == "Hello world"
        assert result.parser_used == "plaintext"


class TestGeminiOCR:
    """Gemini 2.5 Flash OCR 관련 테스트"""

    @pytest.mark.asyncio
    async def test_gemini_ocr_fallback_when_pymupdf_short(self, tmp_path, monkeypatch):
        """pymupdf4llm 결과가 짧을 때 Gemini OCR로 폴백"""
        from unittest.mock import AsyncMock
        import app.services.document_parser as dp

        # PDF 파일 생성
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        # pymupdf4llm이 짧은 텍스트 반환하도록 모킹
        monkeypatch.setattr(dp, "_extract_with_pymupdf", AsyncMock(return_value="short"))

        # Gemini API 모킹 - 텍스트가 PDF_PARSER_MIN_CHARS(200) 이상이어야 함
        gemini_text = (
            "# Resume\n"
            "## 경력\n"
            "Python 백엔드 개발자로 5년간 다양한 프로젝트를 수행했습니다.\n"
            "대규모 트래픽 처리와 마이크로서비스 아키텍처 설계 경험이 있습니다.\n"
            "## 기술 스택\n"
            "- FastAPI, Django, Flask 프레임워크 활용\n"
            "- PostgreSQL, Redis, MongoDB 데이터베이스 운영\n"
            "- Docker, Kubernetes, AWS 클라우드 인프라 구축\n"
            "## 학력\n"
            "서울대학교 컴퓨터공학과 학사 졸업\n"
        )
        monkeypatch.setattr(dp, "_extract_with_gemini", AsyncMock(return_value=gemini_text))

        # settings 모킹 - patch the config module that gets imported
        class MockSettings:
            GEMINI_API_KEY = "fake-key"
            PDF_PARSER_MIN_CHARS = 200

        monkeypatch.setattr("app.core.config.settings", MockSettings())

        result = await dp._parse_pdf(str(pdf_file))
        assert result.parser_used == "gemini-2.5-flash"
        assert "경력" in result.text
        assert result.metadata.get("ocr") is True

    @pytest.mark.asyncio
    async def test_pymupdf_used_when_sufficient(self, tmp_path, monkeypatch):
        """pymupdf4llm 결과가 충분히 길면 그대로 사용"""
        from unittest.mock import AsyncMock
        import app.services.document_parser as dp

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        long_text = "A" * 500  # 충분히 긴 텍스트
        monkeypatch.setattr(dp, "_extract_with_pymupdf", AsyncMock(return_value=long_text))

        class MockSettings:
            GEMINI_API_KEY = "fake-key"
            PDF_PARSER_MIN_CHARS = 200

        monkeypatch.setattr("app.core.config.settings", MockSettings())

        result = await dp._parse_pdf(str(pdf_file))
        assert result.parser_used == "pymupdf4llm"
        assert len(result.text) == 500

    @pytest.mark.asyncio
    async def test_gemini_skipped_when_no_api_key(self, tmp_path, monkeypatch):
        """GEMINI_API_KEY 미설정 시 Gemini 스킵"""
        from unittest.mock import AsyncMock
        import app.services.document_parser as dp

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        # pymupdf4llm 짧은 결과
        monkeypatch.setattr(dp, "_extract_with_pymupdf", AsyncMock(return_value="short"))

        # Docling도 실패
        monkeypatch.setattr(
            dp, "_extract_with_docling",
            AsyncMock(side_effect=Exception("Docling failed"))
        )

        class MockSettings:
            GEMINI_API_KEY = None  # 미설정
            PDF_PARSER_MIN_CHARS = 200

        monkeypatch.setattr("app.core.config.settings", MockSettings())

        # 최종 결과는 짧은 pymupdf4llm 결과
        result = await dp._parse_pdf(str(pdf_file))
        assert result.parser_used == "pymupdf4llm"
        assert result.metadata.get("quality") == "low"


class TestDocumentAnalysisActivity:
    def test_activity_exists(self):
        from app.workflows.activities.document_analysis import analyze_documents
        assert callable(analyze_documents)

    def test_activity_is_defn(self):
        from app.workflows.activities.document_analysis import analyze_documents
        assert hasattr(analyze_documents, "__temporal_activity_definition")
