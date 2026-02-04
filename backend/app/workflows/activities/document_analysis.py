"""
backend/app/workflows/activities/document_analysis.py
문서 분석 Activity (이력서/포트폴리오/커버레터)
"""
import logging

from temporalio import activity

from app.core.observability import observe_activity

logger = logging.getLogger(__name__)


@activity.defn
@observe_activity(name="analyze_documents", phase="analysis")
async def analyze_documents(input_data: dict) -> dict:
    """
    이력서/포트폴리오 분석

    1. 문서 텍스트 추출 (Docling primary, pymupdf4llm fallback)
    2. LLM으로 프로필 구조화 추출
    3. 벡터 스토어에 프로필 임베딩 저장
    """
    from app.services.document_parser import parse_document
    from app.services.cached_llm import CachedLLMService

    llm = CachedLLMService()
    documents = []
    parse_results = []

    for doc_key in ("resume_path", "portfolio_path", "cover_letter_path"):
        path = input_data.get(doc_key)
        if path:
            activity.heartbeat(f"Parsing {doc_key}...")
            try:
                result = await parse_document(path)
                documents.append(f"## {doc_key}\n{result.text}")
                parse_results.append({
                    "key": doc_key,
                    "parser": result.parser_used,
                    "sections": len(result.sections),
                    "chars": len(result.text),
                })
                logger.info(f"Parsed {doc_key} with {result.parser_used}: {len(result.text)} chars")
            except Exception as e:
                logger.warning(f"Failed to parse {doc_key}: {e}")

    if not documents:
        return {"profile": {}, "raw_texts": [], "parse_info": []}

    # LLM으로 프로필 추출 (Activity별 최적 모델 사용)
    activity.heartbeat("Extracting candidate profile with LLM...")
    from app.prompts import get_prompt
    prompt = get_prompt("document_analysis.yaml", "extract_profile", documents="\n---\n".join(documents))
    profile = await llm.run(prompt, activity_name="analyze_documents")

    # 벡터 스토어에 프로필 저장 (job_id가 있을 경우)
    job_id = input_data.get("job_id")
    kg_entity_count = 0

    if job_id and isinstance(profile, dict):
        activity.heartbeat("Storing profile embeddings...")
        try:
            from app.services.vector_store import get_vector_store
            vs = get_vector_store(job_id)
            await vs.store_profile(profile)
            logger.info(f"Stored profile embeddings for job {job_id}")
        except Exception as e:
            logger.warning(f"Vector store failed (non-fatal): {e}")

        # Extract and store KG entities (non-blocking)
        activity.heartbeat("Extracting KG entities from profile...")
        try:
            from app.services.knowledge_graph import get_knowledge_graph
            kg = get_knowledge_graph(job_id)
            extraction_result = await kg.extract_and_store_candidate_entities(profile)
            kg_entity_count = len(extraction_result.entities)
            logger.info(f"Extracted {kg_entity_count} KG entities for job {job_id}")
        except Exception as e:
            logger.warning(f"KG extraction failed (non-fatal): {e}")

    return {
        "profile": profile if isinstance(profile, dict) else {},
        "raw_texts": documents,
        "parse_info": parse_results,
        "kg_entity_count": kg_entity_count,
    }
