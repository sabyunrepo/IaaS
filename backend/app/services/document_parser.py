"""
backend/app/services/document_parser.py
PDF/DOCX 텍스트 추출
- OpenAI GPT-4.1 mini vision (primary, 고품질 OCR + 구조화 추출)
- pymupdf4llm (fallback, 무료 텍스트 기반 PDF)
- Docling (DOCX 처리)
"""
import asyncio
import base64
import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# OpenAI vision rate limiter (conservative 5 concurrent)
_openai_vision_semaphore: asyncio.Semaphore | None = None


def _get_openai_vision_semaphore() -> asyncio.Semaphore:
    """Get or create OpenAI vision API semaphore for rate limiting."""
    global _openai_vision_semaphore
    if _openai_vision_semaphore is None:
        _openai_vision_semaphore = asyncio.Semaphore(5)
    return _openai_vision_semaphore


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".html"}
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# pymupdf4llm 텍스트 추출 결과가 이 길이 미만이면 스캔 PDF로 간주 → OCR fallback
MIN_TEXT_LENGTH_FOR_OCR_FALLBACK = 100


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
    1. OpenAI GPT-4.1 mini vision (고품질 OCR + 구조화 추출)
    2. pymupdf4llm (무료 fallback, 텍스트 기반 PDF)
    3. Docling (DOCX 전용)
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

    # DOCX 파일: python-docx
    if ext in (".docx", ".doc"):
        try:
            text = await _extract_with_docx(file_path)
            return ParseResult(
                text=text,
                metadata={"source": file_path, "format": ext},
                sections=_extract_sections(text),
                parser_used="python-docx",
            )
        except Exception as e:
            logger.warning(f"python-docx failed for {file_path}: {e}")
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
    """PDF 파일 파싱

    1차: OpenAI GPT-4.1 mini vision (고품질 OCR + 구조화 추출)
    2차: pymupdf4llm (무료 fallback)
    """
    from app.core.config import settings

    # Step 1: OpenAI GPT-4.1 mini vision (primary)
    if settings.OPENAI_API_KEY:
        try:
            text = await _extract_with_openai_vision(file_path)
            logger.info(
                f"OpenAI vision extracted {len(text)} chars from {file_path}"
            )
            return ParseResult(
                text=text,
                metadata={"source": file_path, "format": ".pdf", "ocr": True},
                sections=_extract_sections(text),
                parser_used="openai-gpt-4.1-mini",
            )
        except Exception as e:
            logger.warning(
                f"OpenAI vision failed for {file_path}: {e}, "
                f"falling back to pymupdf4llm"
            )

    # Step 2: pymupdf4llm fallback (무료, 텍스트 기반 PDF)
    try:
        text = await _extract_with_pymupdf(file_path)
        if text and len(text.strip()) >= MIN_TEXT_LENGTH_FOR_OCR_FALLBACK:
            logger.info(
                f"pymupdf4llm extracted {len(text)} chars from {file_path}"
            )
            return ParseResult(
                text=text,
                metadata={"source": file_path, "format": ".pdf"},
                sections=_extract_sections(text),
                parser_used="pymupdf4llm",
            )
        logger.warning(
            f"pymupdf4llm returned only {len(text.strip()) if text else 0} chars"
        )
    except Exception as e:
        logger.error(f"pymupdf4llm also failed for {file_path}: {e}")

    raise ValueError(f"Failed to parse PDF with all methods: {file_path}")


async def _extract_with_openai_vision(file_path: str) -> str:
    """OpenAI GPT-4.1 mini vision으로 PDF OCR 텍스트 추출

    PDF 페이지를 이미지로 변환 → GPT-4.1 mini vision API로 텍스트 추출
    - 비용: $0.40/$1.60 per 1M tokens (이미지 토큰 포함)
    - 이력서 1장 기준: ~$0.01 이하
    - 최대 20페이지까지 처리 (이력서/포트폴리오 충분)
    """
    import httpx
    from app.core.config import settings

    # PDF → 이미지 변환 (pymupdf/fitz 사용)
    page_images = await _pdf_to_images(file_path, max_pages=20)
    if not page_images:
        raise ValueError(f"Failed to convert PDF to images: {file_path}")

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    logger.info(
        f"Sending {len(page_images)} pages ({file_size_mb:.1f}MB PDF) "
        f"to OpenAI GPT-4.1 mini vision"
    )

    # 메시지 구성: 프롬프트 + 페이지 이미지들
    content: list[dict] = [
        {
            "type": "text",
            "text": (
                "이 PDF 문서의 전체 내용을 텍스트로 추출해주세요.\n"
                "요구사항:\n"
                "1. 원본의 구조와 형식을 최대한 유지하세요\n"
                "2. 섹션 제목은 마크다운 헤더(#, ##)로 표시하세요\n"
                "3. 표가 있으면 마크다운 테이블로 변환하세요\n"
                "4. 이미지나 차트의 내용도 텍스트로 설명하세요\n"
                "5. 요약하지 말고 전체 내용을 그대로 추출하세요"
            ),
        }
    ]

    for img_b64 in page_images:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_b64}",
                "detail": "high",
            },
        })

    payload = {
        "model": "gpt-4.1-mini",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 16000,
        "temperature": 0.0,
    }

    semaphore = _get_openai_vision_semaphore()
    async with semaphore:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        logger.error(f"OpenAI vision response parsing failed: {result}")
        raise ValueError(f"OpenAI vision response parsing failed: {e}")


async def _pdf_to_images(
    file_path: str,
    max_pages: int = 20,
    dpi: int = 200,
) -> list[str]:
    """PDF 페이지를 PNG 이미지(base64)로 변환

    pymupdf(fitz)를 사용하여 추가 시스템 의존성 없이 변환.
    CPU-bound 작업이므로 asyncio.to_thread()로 실행.
    """
    return await asyncio.to_thread(_pdf_to_images_sync, file_path, max_pages, dpi)


def _pdf_to_images_sync(
    file_path: str,
    max_pages: int = 20,
    dpi: int = 200,
) -> list[str]:
    """PDF 페이지를 PNG 이미지(base64)로 변환 (동기 구현)"""
    import fitz

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        logger.error(f"Failed to open PDF with fitz: {file_path}: {e}")
        return []

    images = []
    page_count = min(len(doc), max_pages)
    zoom = dpi / 72  # fitz 기본 72 DPI
    matrix = fitz.Matrix(zoom, zoom)

    for i in range(page_count):
        try:
            page = doc[i]
            pix = page.get_pixmap(matrix=matrix)
            img_bytes = pix.tobytes("png")
            img_b64 = base64.b64encode(img_bytes).decode()
            images.append(img_b64)
        except Exception as e:
            logger.warning(f"Failed to render page {i+1}: {e}")
            continue

    doc.close()
    logger.debug(f"Converted {len(images)}/{page_count} pages to images")
    return images


async def _extract_with_docx(file_path: str) -> str:
    """python-docx로 DOCX 텍스트 추출 (경량, GPU 불필요)"""
    from docx import Document

    def _read() -> str:
        doc = Document(file_path)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    return await asyncio.to_thread(_read)


async def _extract_with_pymupdf(file_path: str) -> str:
    """pymupdf4llm으로 PDF 텍스트 추출 (무료 fallback)

    CPU-bound 작업이므로 asyncio.to_thread()로 실행.
    """
    import pymupdf4llm
    return await asyncio.to_thread(pymupdf4llm.to_markdown, file_path)


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
