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


class TestDocumentAnalysisActivity:
    def test_activity_exists(self):
        from app.workflows.activities.document_analysis import analyze_documents
        assert callable(analyze_documents)

    def test_activity_is_defn(self):
        from app.workflows.activities.document_analysis import analyze_documents
        assert hasattr(analyze_documents, "__temporal_activity_definition")
