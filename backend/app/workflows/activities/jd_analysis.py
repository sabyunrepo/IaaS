"""
backend/app/workflows/activities/jd_analysis.py
채용공고(JD) 분석 Activity
"""
import logging

from temporalio import activity

from app.core.observability import observe_activity
from app.services.activity_logger import ActivityLogger

logger = logging.getLogger(__name__)


@activity.defn
@observe_activity(name="analyze_jd", phase="analysis")
async def analyze_jd(jd_text: str, job_id: str | None = None) -> dict:
    """
    채용공고(JD) 분석

    1. 요구사항 추출
    2. 스킬 추출
    3. 회사 문화 추출
    """
    from app.services.cached_llm import CachedLLMService

    # Initialize activity logger
    alog = ActivityLogger(job_id, "jd_analysis", "analyzing") if job_id else None

    if alog:
        await alog.start("Starting JD analysis", {
            "jd_text_length": len(jd_text),
        })

    llm = CachedLLMService()

    from app.prompts import get_prompt
    prompt = get_prompt("jd_analysis.yaml", "analyze", jd_text=jd_text)

    activity.heartbeat("Starting JD analysis LLM call...")

    if alog:
        await alog.progress("Extracting requirements with LLM", {})

    result = await llm.run(prompt, activity_name="analyze_jd")

    activity.heartbeat("JD analysis LLM call completed")

    jd_result = {}
    kg_entity_count = 0

    if isinstance(result, dict):
        jd_result = {
            "job_title": result.get("job_title"),
            "company_name": result.get("company_name"),
            "requirements": result.get("requirements", []),
            "responsibilities": result.get("responsibilities", []),
            "company_culture": result.get("company_culture", []),
            "tech_stack": result.get("tech_stack", []),
            "skill_matches": [],
            "overall_match_score": 0,
            "gaps": [],
            "strengths": [],
        }
    else:
        jd_result = {
            "job_title": None,
            "company_name": None,
            "requirements": [],
            "responsibilities": [],
            "company_culture": [],
            "tech_stack": [],
            "skill_matches": [],
            "overall_match_score": 0,
            "gaps": [],
            "strengths": [],
        }

    # Extract and store KG entities (non-blocking)
    if job_id and jd_result.get("job_title"):
        activity.heartbeat("Extracting KG entities from JD analysis...")
        try:
            from app.services.knowledge_graph import get_knowledge_graph
            kg = get_knowledge_graph(job_id)
            extraction_result = await kg.extract_and_store_jd_entities(jd_result)
            kg_entity_count = len(extraction_result.entities)
            logger.info(f"Extracted {kg_entity_count} KG entities from JD for job {job_id}")
        except Exception as e:
            logger.warning(f"KG extraction failed (non-fatal): {e}")

    # Log final result
    if alog:
        await alog.result("JD analysis completed", {
            "job_title": jd_result.get("job_title"),
            "company_name": jd_result.get("company_name"),
            "requirements_count": len(jd_result.get("requirements", [])),
            "responsibilities_count": len(jd_result.get("responsibilities", [])),
            "tech_stack": jd_result.get("tech_stack", []),
            "kg_entity_count": kg_entity_count,
        })

    return {
        **jd_result,
        "kg_entity_count": kg_entity_count,
    }
