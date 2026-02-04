"""
backend/app/services/document_parser.py
PDF/DOCX 텍스트 추출
- pymupdf4llm (primary, fast)
- Gemini 2.5 Flash (OCR fallback for scanned PDFs)
- Docling (optional, for complex tables)
"""
import asyncio
import base64
import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Gemini API rate limiter (2000 RPM = ~33 RPS, use conservative 5 concurrent)
_gemini_semaphore: asyncio.Semaphore | None = None


def _get_gemini_semaphore() -> asyncio.Semaphore:
    """Get or create Gemini API semaphore for rate limiting."""
    global _gemini_semaphore
    if _gemini_semaphore is None:
        # Allow up to 5 concurrent Gemini API calls
        # Conservative limit to stay well under 2000 RPM
        _gemini_semaphore = asyncio.Semaphore(5)
    return _gemini_semaphore

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".html"}
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


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
    """파일에서 구조화된 파싱 결과 반환

    Fallback 순서:
    1. pymupdf4llm (빠름, 텍스트 기반 PDF)
    2. Gemini 2.5 Flash (스캔/이미지 PDF OCR)
    3. Docling (복잡한 테이블, 선택적)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File too large: {file_size / 1024 / 1024:.1f}MB (max {MAX_FILE_SIZE_MB}MB)"
        )

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file format: {ext}")

    # PDF 파일 처리
    if ext == ".pdf":
        return await _parse_pdf(file_path)

    # DOCX 파일: Docling 시도
    if ext in (".docx", ".doc"):
        try:
            text = await _extract_with_docling(file_path)
            return ParseResult(
                text=text,
                metadata={"source": file_path, "format": ext},
                sections=_extract_sections(text),
                parser_used="docling",
            )
        except Exception as e:
            logger.warning(f"Docling failed for {file_path}: {e}")
            raise ValueError(f"Failed to parse DOCX: {file_path}")

    # Plain text files
    if ext in (".txt", ".md", ".html"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return ParseResult(
            text=text,
            metadata={"source": file_path, "format": ext},
            parser_used="plaintext",
        )

    raise ValueError(f"Unsupported file format: {ext}")


async def _parse_pdf(file_path: str) -> ParseResult:
    """PDF 파일 파싱 (다단계 fallback)"""
    from app.core.config import settings

    min_chars = settings.PDF_PARSER_MIN_CHARS

    # 1. pymupdf4llm 먼저 시도 (빠름)
    try:
        text = await _extract_with_pymupdf(file_path)
        if len(text.strip()) >= min_chars:
            logger.info(f"Parsed {file_path} with pymupdf4llm: {len(text)} chars")
            return ParseResult(
                text=text,
                metadata={"source": file_path, "format": ".pdf"},
                sections=_extract_sections(text),
                parser_used="pymupdf4llm",
            )
        else:
            logger.warning(
                f"pymupdf4llm extracted only {len(text)} chars (min: {min_chars}), "
                f"trying Gemini OCR"
            )
    except Exception as e:
        logger.warning(f"pymupdf4llm failed for {file_path}: {e}")

    # 2. Gemini 2.5 Flash OCR (스캔/이미지 PDF)
    if settings.GEMINI_API_KEY:
        try:
            text = await _extract_with_gemini(file_path)
            if text and len(text.strip()) >= min_chars:
                logger.info(f"Parsed {file_path} with Gemini OCR: {len(text)} chars")
                return ParseResult(
                    text=text,
                    metadata={"source": file_path, "format": ".pdf", "ocr": True},
                    sections=_extract_sections(text),
                    parser_used="gemini-2.5-flash",
                )
        except Exception as e:
            logger.warning(f"Gemini OCR failed for {file_path}: {e}")
    else:
        logger.debug("GEMINI_API_KEY not set, skipping Gemini OCR")

    # 3. Docling fallback (복잡한 테이블)
    try:
        text = await _extract_with_docling(file_path)
        logger.info(f"Parsed {file_path} with Docling: {len(text)} chars")
        return ParseResult(
            text=text,
            metadata={"source": file_path, "format": ".pdf"},
            sections=_extract_sections(text),
            parser_used="docling",
        )
    except Exception as e:
        logger.warning(f"Docling failed for {file_path}: {e}")

    # 4. 마지막 시도: pymupdf4llm 결과 반환 (짧더라도)
    try:
        text = await _extract_with_pymupdf(file_path)
        logger.warning(f"Using short pymupdf4llm result: {len(text)} chars")
        return ParseResult(
            text=text,
            metadata={"source": file_path, "format": ".pdf", "quality": "low"},
            sections=_extract_sections(text),
            parser_used="pymupdf4llm",
        )
    except Exception as e:
        raise ValueError(f"All parsers failed for: {file_path}") from e


async def _extract_with_gemini(file_path: str) -> str:
    """Gemini 2.0 Flash로 PDF OCR 텍스트 추출

    장점:
    - 네이티브 텍스트 추출 무료 (토큰 미청구)
    - 스캔/이미지 PDF 지원
    - 한글 OCR 품질 우수
    - 1000페이지까지 처리 가능

    Rate Limiting:
    - Semaphore로 동시 요청 제한 (5 concurrent)
    - 2000 RPM 제한 대비 보수적 설정
    """
    import httpx
    from app.core.config import settings

    # PDF를 base64로 인코딩
    with open(file_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode()

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    logger.info(f"Sending {file_size_mb:.1f}MB PDF to Gemini OCR")

    # Google AI Studio API 직접 호출 (LiteLLM 콜백 호환성 문제 우회)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"

    payload = {
        "contents": [{
            "parts": [
                {
                    "text": (
                        "이 PDF 문서의 전체 내용을 텍스트로 추출해주세요.\n"
                        "요구사항:\n"
                        "1. 원본의 구조와 형식을 최대한 유지하세요\n"
                        "2. 섹션 제목은 마크다운 헤더(#, ##)로 표시하세요\n"
                        "3. 표가 있으면 마크다운 테이블로 변환하세요\n"
                        "4. 이미지나 차트의 내용도 텍스트로 설명하세요\n"
                        "5. 요약하지 말고 전체 내용을 그대로 추출하세요"
                    )
                },
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": pdf_b64
                    }
                }
            ]
        }],
        "generationConfig": {
            "maxOutputTokens": 16000
        }
    }

    # Use semaphore to limit concurrent Gemini API calls
    semaphore = _get_gemini_semaphore()
    async with semaphore:
        logger.debug("Acquired Gemini semaphore, sending request...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

    # 응답에서 텍스트 추출
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return text
    except (KeyError, IndexError) as e:
        logger.error(f"Gemini API response parsing failed: {result}")
        raise ValueError(f"Gemini API response parsing failed: {e}")


async def _extract_with_docling(file_path: str) -> str:
    """IBM Docling으로 구조화된 텍스트 추출"""
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document.export_to_markdown()


async def _extract_with_pymupdf(file_path: str) -> str:
    """pymupdf4llm으로 PDF 텍스트 추출 (빠른 fallback)"""
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
