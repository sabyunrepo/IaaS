"""
backend/app/workflows/activities/document_analysis.py
문서 분석 Activity (이력서/포트폴리오/커버레터)
"""
import logging

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def analyze_documents(input_data: dict) -> dict:
    """
    이력서/포트폴리오 분석

    1. 문서 텍스트 추출 (Docling)
    2. LLM으로 프로필 구조화 추출
    3. 벡터 스토어에 저장
    """
    from app.services.document_parser import extract_text
    from app.services.cached_llm import CachedLLMService

    llm = CachedLLMService()
    documents = []

    for doc_key in ("resume_path", "portfolio_path", "cover_letter_path"):
        path = input_data.get(doc_key)
        if path:
            activity.heartbeat(f"Parsing {doc_key}...")
            try:
                text = await extract_text(path)
                documents.append(f"## {doc_key}\n{text}")
            except Exception as e:
                logger.warning(f"Failed to parse {doc_key}: {e}")

    if not documents:
        return {"profile": {}, "raw_texts": []}

    # LLM으로 프로필 추출
    activity.heartbeat("Extracting candidate profile with LLM...")
    prompt = (
        "Extract a structured candidate profile from the following documents. "
        "Include: name, contact, education, work experience, skills, projects, certifications.\n\n"
        + "\n---\n".join(documents)
    )
    profile = await llm.run(prompt)

    return {
        "profile": profile if isinstance(profile, dict) else {},
        "raw_texts": documents,
    }
