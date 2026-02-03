"""
backend/app/services/knowledge_graph.py
Core Knowledge Graph Service for Vantict Sniper
Orchestrates entity extraction, graph building, and claim-evidence verification
"""
import logging
from typing import Any

from .graph_store import GraphStore, get_graph_store
from .entity_extractors import (
    CandidateEntityExtractor,
    CodeEntityExtractor,
    JDEntityExtractor,
    ExtractionResult,
    ExtractedEntity,
    ExtractedRelation,
    get_candidate_extractor,
    get_code_extractor,
    get_jd_extractor,
)

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Main orchestration service for Knowledge Graph operations.

    Coordinates entity extraction, graph storage, relationship building,
    and provides unified access to graph data for question generation.
    """

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.store = get_graph_store(job_id)
        self._node_cache: dict[str, str] = {}  # name:type -> node_id mapping

    # ==========================================
    # Entity Extraction from Analysis Results
    # ==========================================

    async def extract_and_store_candidate_entities(
        self,
        profile: dict[str, Any],
    ) -> ExtractionResult:
        """Extract and store entities from candidate profile."""
        logger.info(f"[{self.job_id}] Extracting candidate entities")

        extractor = get_candidate_extractor()
        result = extractor.extract(profile)

        await self._store_extraction_result(result)

        logger.info(
            f"[{self.job_id}] Stored {len(result.entities)} candidate entities, "
            f"{len(result.relations)} relations"
        )
        return result

    async def extract_and_store_code_entities(
        self,
        code_analysis: dict[str, Any],
    ) -> ExtractionResult:
        """Extract and store entities from code analysis."""
        logger.info(f"[{self.job_id}] Extracting code entities")

        extractor = get_code_extractor()
        result = extractor.extract(code_analysis)

        await self._store_extraction_result(result)

        logger.info(
            f"[{self.job_id}] Stored {len(result.entities)} code entities, "
            f"{len(result.relations)} relations"
        )
        return result

    async def extract_and_store_jd_entities(
        self,
        jd_analysis: dict[str, Any],
    ) -> ExtractionResult:
        """Extract and store entities from JD analysis."""
        logger.info(f"[{self.job_id}] Extracting JD entities")

        extractor = get_jd_extractor()
        result = extractor.extract(jd_analysis)

        await self._store_extraction_result(result)

        logger.info(
            f"[{self.job_id}] Stored {len(result.entities)} JD entities, "
            f"{len(result.relations)} relations"
        )
        return result

    async def _store_extraction_result(self, result: ExtractionResult) -> None:
        """Store extraction result in the graph store."""
        # First, create all entities
        for entity in result.entities:
            cache_key = f"{entity.name}:{entity.entity_type}"

            # Check if entity already exists
            existing = await self.store.find_node_by_name(entity.entity_type, entity.name)
            if existing:
                # Update existing node with new properties
                merged_props = {**existing.get("properties", {}), **entity.properties}
                await self.store.update_node(
                    existing["id"],
                    properties=merged_props,
                    provenance=entity.provenance,
                )
                self._node_cache[cache_key] = existing["id"]
            else:
                # Create new node
                node_id = await self.store.create_node(
                    entity_type=entity.entity_type,
                    name=entity.name,
                    properties=entity.properties,
                    provenance=entity.provenance,
                )
                self._node_cache[cache_key] = node_id

        # Then, create all relations
        for relation in result.relations:
            source_key = f"{relation.source_name}:{relation.source_type}"
            target_key = f"{relation.target_name}:{relation.target_type}"

            source_id = self._node_cache.get(source_key)
            target_id = self._node_cache.get(target_key)

            # If source/target not in cache, try to find or create
            if not source_id:
                existing = await self.store.find_node_by_name(
                    relation.source_type, relation.source_name
                )
                if existing:
                    source_id = existing["id"]
                    self._node_cache[source_key] = source_id
                else:
                    # Create placeholder node
                    source_id = await self.store.create_node(
                        entity_type=relation.source_type,
                        name=relation.source_name,
                        properties={"placeholder": True},
                    )
                    self._node_cache[source_key] = source_id

            if not target_id:
                existing = await self.store.find_node_by_name(
                    relation.target_type, relation.target_name
                )
                if existing:
                    target_id = existing["id"]
                    self._node_cache[target_key] = target_id
                else:
                    # Create placeholder node
                    target_id = await self.store.create_node(
                        entity_type=relation.target_type,
                        name=relation.target_name,
                        properties={"placeholder": True},
                    )
                    self._node_cache[target_key] = target_id

            await self.store.create_edge(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation.relation_type,
                properties=relation.properties,
                confidence=relation.confidence,
            )

    # ==========================================
    # Graph Query Operations
    # ==========================================

    async def get_skills_with_evidence(self) -> list[dict[str, Any]]:
        """Get all skills with their evidence chains.

        Returns skills linked to their demonstration sources (code, projects, etc.)
        """
        skills = await self.store.get_nodes_by_type("Skill")
        result = []

        for skill in skills:
            skill_id = skill["id"]

            # Get incoming edges (demonstrated_by relations)
            edges = await self.store.get_incoming_edges(skill_id)
            evidence = []

            for edge in edges:
                if edge["relation_type"] == "demonstrated_by":
                    evidence_node = await self.store.get_node(edge["source_id"])
                    if evidence_node:
                        evidence.append({
                            "type": evidence_node["entity_type"],
                            "name": evidence_node["name"],
                            "properties": evidence_node["properties"],
                            "confidence": edge["confidence"],
                        })

            # Check if skill is from resume (has_skill relation)
            outgoing = await self.store.get_incoming_edges(skill_id)
            is_claimed = any(e["relation_type"] == "has_skill" for e in outgoing)

            result.append({
                "skill": skill["name"],
                "properties": skill["properties"],
                "is_claimed": is_claimed,
                "evidence_count": len(evidence),
                "evidence": evidence,
                "verified": len(evidence) > 0,
            })

        return result

    async def get_unverified_claims(self) -> list[dict[str, Any]]:
        """Get skills claimed in resume but not demonstrated in code."""
        skills_with_evidence = await self.get_skills_with_evidence()
        return [s for s in skills_with_evidence if s["is_claimed"] and not s["verified"]]

    async def get_jd_requirement_matches(self) -> list[dict[str, Any]]:
        """Get JD requirements with their match status."""
        requirements = await self.store.get_nodes_by_type("Requirement")
        result = []

        for req in requirements:
            req_id = req["id"]

            # Get matches_requirement edges
            edges = await self.store.get_incoming_edges(req_id)
            matches = []

            for edge in edges:
                if edge["relation_type"] == "matches_requirement":
                    skill_node = await self.store.get_node(edge["source_id"])
                    if skill_node:
                        matches.append({
                            "skill": skill_node["name"],
                            "confidence": edge["confidence"],
                            "match_type": edge["properties"].get("match_type"),
                            "evidence": edge["properties"].get("evidence"),
                        })

            result.append({
                "requirement": req["name"],
                "priority": req["properties"].get("priority", "required"),
                "matches": matches,
                "is_matched": len(matches) > 0,
                "best_match_confidence": max((m["confidence"] for m in matches), default=0),
            })

        return result

    async def get_notable_implementations_for_skill(
        self,
        skill_name: str,
    ) -> list[dict[str, Any]]:
        """Get notable implementations that demonstrate a specific skill."""
        skill = await self.store.find_node_by_name("Skill", skill_name)
        if not skill:
            return []

        # Traverse: Skill -[demonstrated_by]-> Repository -[contains_code]-> NotableImplementation
        result = []
        edges = await self.store.get_incoming_edges(skill["id"])

        for edge in edges:
            if edge["relation_type"] == "demonstrated_by":
                repo_node = await self.store.get_node(edge["source_id"])
                if repo_node and repo_node["entity_type"] == "Repository":
                    # Get implementations in this repo
                    repo_edges = await self.store.get_outgoing_edges(repo_node["id"])
                    for repo_edge in repo_edges:
                        if repo_edge["relation_type"] == "contains_code":
                            impl = await self.store.get_node(repo_edge["target_id"])
                            if impl and impl["entity_type"] == "NotableImplementation":
                                result.append({
                                    "implementation": impl["name"],
                                    "repository": repo_node["name"],
                                    "file_path": impl["properties"].get("file_path"),
                                    "description": impl["properties"].get("description"),
                                    "why_notable": impl["properties"].get("why_notable"),
                                    "question_potential": impl["properties"].get("question_potential", 0),
                                    "code_snippet": impl["properties"].get("code_snippet"),
                                })

        return sorted(result, key=lambda x: x["question_potential"], reverse=True)

    async def get_skill_depth_questions(self) -> list[dict[str, Any]]:
        """Get skills suitable for depth probing based on evidence strength.

        Returns skills with high evidence for deep technical discussion.
        """
        skills = await self.get_skills_with_evidence()

        # Filter to verified skills with substantial evidence
        question_candidates = []
        for skill in skills:
            if skill["verified"] and skill["evidence_count"] >= 1:
                implementations = await self.get_notable_implementations_for_skill(skill["skill"])
                if implementations:
                    question_candidates.append({
                        "skill": skill["skill"],
                        "evidence_count": skill["evidence_count"],
                        "evidence": skill["evidence"],
                        "implementations": implementations[:3],  # Top 3
                        "question_type": "skill_depth",
                        "priority": skill["evidence_count"] * 10 + (
                            sum(i["question_potential"] for i in implementations[:3])
                        ),
                    })

        return sorted(question_candidates, key=lambda x: x["priority"], reverse=True)

    async def get_gap_questions(self) -> list[dict[str, Any]]:
        """Get questions about gaps between JD requirements and candidate skills."""
        requirements = await self.get_jd_requirement_matches()

        gap_questions = []
        for req in requirements:
            if not req["is_matched"]:
                gap_questions.append({
                    "requirement": req["requirement"],
                    "priority": req["priority"],
                    "question_type": "gap_probe",
                    "probe_reason": f"JD requires {req['requirement']} but no evidence found",
                })
            elif req["best_match_confidence"] < 70:
                gap_questions.append({
                    "requirement": req["requirement"],
                    "priority": req["priority"],
                    "question_type": "partial_match_probe",
                    "probe_reason": f"Partial match for {req['requirement']} (confidence: {req['best_match_confidence']}%)",
                    "matches": req["matches"],
                })

        return gap_questions

    async def get_conflict_questions(self) -> list[dict[str, Any]]:
        """Get questions about conflicts between claims and evidence."""
        claim_evidence_records = await self.store.get_claim_evidence_by_type("contradicting")

        conflict_questions = []
        for record in claim_evidence_records:
            claim_node = await self.store.get_node(record["claim_node_id"]) if record["claim_node_id"] else None
            evidence_node = await self.store.get_node(record["evidence_node_id"]) if record["evidence_node_id"] else None

            conflict_questions.append({
                "claim": claim_node["name"] if claim_node else "Unknown claim",
                "evidence": evidence_node["name"] if evidence_node else "No evidence",
                "evidence_type": record["evidence_type"],
                "evidence_strength": record["evidence_strength"],
                "analysis": record["analysis"],
                "recommended_probe": record["recommended_probe"],
                "question_type": "conflict_probe",
            })

        return conflict_questions

    # ==========================================
    # Graph Summary and Statistics
    # ==========================================

    async def get_summary(self) -> dict[str, Any]:
        """Get comprehensive summary of the knowledge graph."""
        store_summary = await self.store.get_graph_summary()

        # Add derived statistics
        skills_with_evidence = await self.get_skills_with_evidence()
        unverified_claims = await self.get_unverified_claims()
        jd_matches = await self.get_jd_requirement_matches()

        return {
            **store_summary,
            "skills_summary": {
                "total_skills": len(skills_with_evidence),
                "verified_skills": len([s for s in skills_with_evidence if s["verified"]]),
                "unverified_claims": len(unverified_claims),
            },
            "jd_summary": {
                "total_requirements": len(jd_matches),
                "matched_requirements": len([r for r in jd_matches if r["is_matched"]]),
                "unmatched_requirements": len([r for r in jd_matches if not r["is_matched"]]),
            },
        }

    # ==========================================
    # Cleanup
    # ==========================================

    async def clear(self) -> None:
        """Clear all KG data for this job."""
        await self.store.clear_all()
        self._node_cache.clear()
        logger.info(f"[{self.job_id}] Cleared knowledge graph")


def get_knowledge_graph(job_id: str) -> KnowledgeGraphService:
    """Factory function to create a KnowledgeGraphService instance."""
    return KnowledgeGraphService(job_id)
