"""
backend/app/workflows/activities/knowledge_graph_activities.py
Knowledge Graph Activities for Temporal Workflow
"""
import logging

from temporalio import activity

from app.core.observability import observe_activity

logger = logging.getLogger(__name__)


@activity.defn
@observe_activity(name="build_knowledge_graph", phase="analysis")
async def build_knowledge_graph(
    job_id: str,
    profile: dict | None = None,
    code_analysis: dict | None = None,
    jd_analysis: dict | None = None,
) -> dict:
    """
    Build Knowledge Graph from analysis results.

    1. Extract entities from each analysis domain
    2. Store entities and relationships in graph store
    3. Run conflict detection
    4. Return summary for question generation

    This activity should be called after document_analysis, code_analysis, and jd_analysis
    are complete, typically in Phase 2 of the workflow.
    """
    from app.services.knowledge_graph import get_knowledge_graph
    from app.services.conflict_detector import get_conflict_detector

    activity.heartbeat("Initializing Knowledge Graph...")
    kg = get_knowledge_graph(job_id)

    entity_counts = {
        "candidate": 0,
        "code": 0,
        "jd": 0,
    }
    relation_counts = {
        "candidate": 0,
        "code": 0,
        "jd": 0,
    }

    # Extract and store candidate entities from profile
    if profile:
        activity.heartbeat("Extracting candidate entities...")
        try:
            result = await kg.extract_and_store_candidate_entities(profile)
            entity_counts["candidate"] = len(result.entities)
            relation_counts["candidate"] = len(result.relations)
            logger.info(f"[{job_id}] Extracted {len(result.entities)} candidate entities")
        except Exception as e:
            logger.warning(f"[{job_id}] Failed to extract candidate entities: {e}")

    # Extract and store code entities
    if code_analysis:
        activity.heartbeat("Extracting code entities...")
        try:
            result = await kg.extract_and_store_code_entities(code_analysis)
            entity_counts["code"] = len(result.entities)
            relation_counts["code"] = len(result.relations)
            logger.info(f"[{job_id}] Extracted {len(result.entities)} code entities")
        except Exception as e:
            logger.warning(f"[{job_id}] Failed to extract code entities: {e}")

    # Extract and store JD entities
    if jd_analysis:
        activity.heartbeat("Extracting JD entities...")
        try:
            result = await kg.extract_and_store_jd_entities(jd_analysis)
            entity_counts["jd"] = len(result.entities)
            relation_counts["jd"] = len(result.relations)
            logger.info(f"[{job_id}] Extracted {len(result.entities)} JD entities")
        except Exception as e:
            logger.warning(f"[{job_id}] Failed to extract JD entities: {e}")

    # Run conflict detection
    activity.heartbeat("Running conflict detection...")
    conflict_report = None
    try:
        detector = get_conflict_detector(job_id)
        conflict_report = await detector.detect_all_conflicts()
        logger.info(
            f"[{job_id}] Conflict detection complete: "
            f"{conflict_report.summary.get('total_conflicts', 0)} conflicts found"
        )
    except Exception as e:
        logger.warning(f"[{job_id}] Conflict detection failed: {e}")

    # Get KG summary
    activity.heartbeat("Generating KG summary...")
    summary = await kg.get_summary()

    return {
        "status": "success",
        "entity_counts": entity_counts,
        "relation_counts": relation_counts,
        "total_entities": sum(entity_counts.values()),
        "total_relations": sum(relation_counts.values()),
        "conflict_summary": conflict_report.summary if conflict_report else {},
        "kg_summary": summary,
    }


@activity.defn
@observe_activity(name="get_kg_question_candidates", phase="generation")
async def get_kg_question_candidates(
    job_id: str,
    limit: int = 25,
    balance_categories: bool = True,
) -> dict:
    """
    Get question candidates from Knowledge Graph.

    This activity queries the KG for:
    1. Skill depth questions (verified skills with evidence)
    2. Gap questions (unmatched JD requirements)
    3. Conflict questions (claim-evidence discrepancies)
    4. Implementation review questions (notable code patterns)

    Should be called before question generation to provide KG-based topics.
    """
    from app.services.graph_queries import get_interview_graph_queries

    activity.heartbeat("Querying Knowledge Graph for question candidates...")

    try:
        queries = get_interview_graph_queries(job_id)
        candidates = await queries.get_top_question_candidates(
            limit=limit,
            balance_categories=balance_categories,
        )

        # Convert to serializable format
        candidates_list = []
        for c in candidates:
            candidates_list.append({
                "topic": c.topic,
                "category": c.category,
                "priority": c.priority,
                "evidence_chain": c.evidence_chain,
                "context": c.context,
                "recommended_probe": c.recommended_probe,
                "code_reference": c.code_reference,
            })

        # Get summary for logging
        summary = await queries.get_kg_summary_for_question_generation()

        logger.info(
            f"[{job_id}] Found {len(candidates_list)} KG question candidates "
            f"(by_category: {summary.get('question_generation', {}).get('by_category', {})})"
        )

        return {
            "status": "success",
            "candidates": candidates_list,
            "summary": summary.get("question_generation", {}),
        }

    except Exception as e:
        logger.warning(f"[{job_id}] KG question query failed: {e}")
        return {
            "status": "fallback",
            "candidates": [],
            "summary": {},
            "error": str(e),
        }


@activity.defn
@observe_activity(name="get_evidence_chain", phase="generation")
async def get_evidence_chain(job_id: str, topic: str) -> dict:
    """
    Get the full evidence chain for a specific topic.

    Used during question generation to provide context and code references.
    """
    from app.services.graph_queries import get_interview_graph_queries

    activity.heartbeat(f"Getting evidence chain for {topic}...")

    try:
        queries = get_interview_graph_queries(job_id)
        evidence = await queries.get_evidence_chain_for_topic(topic)

        return {
            "status": "success",
            "topic": topic,
            "evidence_chain": evidence,
        }

    except Exception as e:
        logger.warning(f"[{job_id}] Evidence chain query failed for {topic}: {e}")
        return {
            "status": "error",
            "topic": topic,
            "evidence_chain": [],
            "error": str(e),
        }


@activity.defn
@observe_activity(name="clear_knowledge_graph", phase="cleanup")
async def clear_knowledge_graph(job_id: str) -> dict:
    """
    Clear all Knowledge Graph data for a job.

    Used during cleanup or when reprocessing a job.
    """
    from app.services.knowledge_graph import get_knowledge_graph

    activity.heartbeat("Clearing Knowledge Graph...")

    try:
        kg = get_knowledge_graph(job_id)
        await kg.clear()

        return {
            "status": "success",
            "job_id": job_id,
        }

    except Exception as e:
        logger.warning(f"[{job_id}] KG clear failed: {e}")
        return {
            "status": "error",
            "job_id": job_id,
            "error": str(e),
        }
