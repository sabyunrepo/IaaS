"""
backend/app/services/document_parser.py
PDF/DOCX 텍스트 추출 (Docling primary, pymupdf4llm fallback)
"""
import logging
import os

logger = logging.getLogger(__name__)


async def extract_text(file_path: str) -> str:
    """파일에서 텍스트 추출 (PDF/DOCX 지원)"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    # Docling 시도
    try:
        return await _extract_with_docling(file_path)
    except Exception as e:
        logger.warning(f"Docling failed for {file_path}: {e}")

    # Fallback: pymupdf4llm (PDF only)
    if ext == ".pdf":
        try:
            return await _extract_with_pymupdf(file_path)
        except Exception as e:
            logger.warning(f"pymupdf4llm failed for {file_path}: {e}")

    # Fallback: plain text read
    if ext in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    raise ValueError(f"Unsupported file format: {ext}")


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
