"""
backend/app/workflows/activities/document_analysis.py
문서 분석 Activity (이력서/포트폴리오/커버레터)
"""
from temporalio import activity

from app.core.observability import observe_activity
from app.core.logging import get_logger, JobContextMiddleware
from app.services.activity_logger import ActivityLogger

logger = get_logger(__name__)


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
    from app.workflows.utils import run_llm_with_heartbeat

    # Initialize activity logger
    job_id = input_data.get("job_id")
    alog = ActivityLogger(job_id, "document_analysis", "analyzing") if job_id else None

    doc_keys = ["resume_path", "portfolio_path", "cover_letter_path"]
    available_docs = [k for k in doc_keys if input_data.get(k)]

    if alog:
        await alog.start("Starting document analysis", {
            "available_documents": available_docs,
        })

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
                logger.info(
                    "document_parsed",
                    doc_key=doc_key,
                    parser=result.parser_used,
                    chars=len(result.text),
                    sections=len(result.sections),
                )
            except Exception as e:
                logger.warning(
                    "document_parse_failed",
                    doc_key=doc_key,
                    error=str(e),
                )

    if not documents:
        if alog:
            await alog.result("No documents to analyze", {
                "profile_keys": [],
                "parse_results": [],
            })
        return {"profile": {}, "raw_texts": [], "parse_info": []}

    # LLM으로 프로필 추출 (Activity별 최적 모델 사용)
    activity.heartbeat("Extracting candidate profile with LLM...")
    if alog:
        await alog.progress("Extracting candidate profile with LLM", {
            "documents_count": len(documents),
            "total_chars": sum(len(d) for d in documents),
        })

    from app.prompts import get_prompt
    output_language = input_data.get("language_config", {}).get("output_language", "ko")
    prompt = get_prompt("document_analysis.yaml", "extract_profile", documents="\n---\n".join(documents), output_language=output_language)
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    profile = await run_llm_with_heartbeat(llm, prompt, "analyze_documents", interval=30.0)

    # 벡터 스토어에 프로필 저장 (job_id가 있을 경우)
    job_id = input_data.get("job_id")
    kg_entity_count = 0

    if job_id and isinstance(profile, dict):
        activity.heartbeat("Storing profile embeddings...")
        try:
            from app.services.vector_store import get_vector_store
            vs = get_vector_store(job_id)
            await vs.store_profile(profile)
            with JobContextMiddleware(job_id=job_id, activity="analyze_documents"):
                logger.info("profile_embeddings_stored", job_id=job_id)
        except Exception as e:
            logger.warning("vector_store_failed", error=str(e), job_id=job_id)

        # Extract and store KG entities (non-blocking)
        activity.heartbeat("Extracting KG entities from profile...")
        try:
            from app.services.knowledge_graph import get_knowledge_graph
            kg = get_knowledge_graph(job_id)
            extraction_result = await kg.extract_and_store_candidate_entities(profile)
            kg_entity_count = len(extraction_result.entities)
            with JobContextMiddleware(job_id=job_id, activity="analyze_documents"):
                logger.info(
                    "kg_entities_extracted",
                    entity_count=kg_entity_count,
                )
        except Exception as e:
            logger.warning("kg_extraction_failed", error=str(e), job_id=job_id)

    # Log final result
    if alog:
        profile_keys = list(profile.keys()) if isinstance(profile, dict) else []
        await alog.result("Document analysis completed", {
            "profile_keys": profile_keys,
            "parse_results": parse_results,
            "kg_entity_count": kg_entity_count,
        })

    return {
        "profile": profile if isinstance(profile, dict) else {},
        "raw_texts": documents,
        "parse_info": parse_results,
        "kg_entity_count": kg_entity_count,
    }
