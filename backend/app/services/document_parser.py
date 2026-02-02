"""
backend/app/services/document_parser.py
PDF/DOCX 텍스트 추출 (Docling primary, pymupdf4llm fallback)
"""
import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".html"}


@dataclass
class ParseResult:
    """문서 파싱 결과"""
    text: str
    metadata: dict = field(default_factory=dict)
    sections: list[dict] = field(default_factory=list)
    parser_used: str = "unknown"


async def extract_text(file_path: str) -> str:
    """파일에서 텍스트 추출 (PDF/DOCX 지원)"""
    result = await parse_document(file_path)
    return result.text


async def parse_document(file_path: str) -> ParseResult:
    """파일에서 구조화된 파싱 결과 반환"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file format: {ext}")

    # Docling 시도
    try:
        text = await _extract_with_docling(file_path)
        sections = _extract_sections(text)
        return ParseResult(
            text=text,
            metadata={"source": file_path, "format": ext},
            sections=sections,
            parser_used="docling",
        )
    except Exception as e:
        logger.warning(f"Docling failed for {file_path}: {e}")

    # Fallback: pymupdf4llm (PDF only)
    if ext == ".pdf":
        try:
            text = await _extract_with_pymupdf(file_path)
            return ParseResult(
                text=text,
                metadata={"source": file_path, "format": ext},
                sections=_extract_sections(text),
                parser_used="pymupdf4llm",
            )
        except Exception as e:
            logger.warning(f"pymupdf4llm failed for {file_path}: {e}")

    # Fallback: plain text read
    if ext in (".txt", ".md", ".html"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return ParseResult(
            text=text,
            metadata={"source": file_path, "format": ext},
            parser_used="plaintext",
        )

    raise ValueError(f"All parsers failed for: {file_path}")


async def _extract_with_docling(file_path: str) -> str:
    """IBM Docling으로 구조화된 텍스트 추출"""
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()


async def _extract_with_pymupdf(file_path: str) -> str:
    """pymupdf4llm으로 PDF 텍스트 추출 (fallback)"""
    import pymupdf4llm
    return pymupdf4llm.to_markdown(file_path)


def _extract_sections(text: str) -> list[dict]:
    """마크다운 텍스트에서 섹션 구분"""
    sections = []
    current_title = "Introduction"
    current_lines = []

    for line in text.split("\n"):
        if line.startswith("# ") or line.startswith("## "):
            if current_lines:
                sections.append({
                    "title": current_title,
                    "content": "\n".join(current_lines).strip(),
                })
            current_title = line.lstrip("# ").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append({
            "title": current_title,
            "content": "\n".join(current_lines).strip(),
        })

    return sections
