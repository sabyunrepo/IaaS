"""
backend/app/services/graph_queries.py
Graph Query Service for Interview Question Generation
Provides high-level query methods for extracting question candidates from the Knowledge Graph
"""
import logging
from typing import Any

from pydantic import BaseModel, Field

from .knowledge_graph import KnowledgeGraphService, get_knowledge_graph
from .conflict_detector import ConflictDetector, get_conflict_detector

logger = logging.getLogger(__name__)


class QuestionCandidate(BaseModel):
    """A candidate topic for interview question generation."""
    topic: str
    category: str  # "skill_depth", "gap_probe", "conflict_probe", "implementation_review"
    priority: float  # Higher = more important to ask
    evidence_chain: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    recommended_probe: str | None = None
    code_reference: dict[str, Any] | None = None


class InterviewGraphQueries:
    """High-level query interface for interview question generation.

    Provides methods to extract question candidates from the Knowledge Graph,
    combining skill analysis, gap detection, and conflict identification.
    """

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.kg = get_knowledge_graph(job_id)
        self.conflict_detector = get_conflict_detector(job_id)

    async def get_all_question_candidates(self) -> list[QuestionCandidate]:
        """Get all question candidates from the Knowledge Graph.

        Combines:
        1. Skill depth questions (verified skills with code evidence)
        2. Gap questions (JD requirements not matched)
        3. Conflict questions (claim-evidence discrepancies)
        4. Implementation review questions (notable code patterns)

        Returns sorted by priority.
        """
        logger.info(f"[{self.job_id}] Gathering question candidates from KG")

        candidates: list[QuestionCandidate] = []

        # 1. Skill depth questions
        skill_questions = await self._get_skill_depth_candidates()
        candidates.extend(skill_questions)

        # 2. Gap questions
        gap_questions = await self._get_gap_candidates()
        candidates.extend(gap_questions)

        # 3. Conflict questions
        conflict_questions = await self._get_conflict_candidates()
        candidates.extend(conflict_questions)

        # 4. Implementation review questions
        impl_questions = await self._get_implementation_candidates()
        candidates.extend(impl_questions)

        # Sort by priority
        candidates.sort(key=lambda x: x.priority, reverse=True)

        logger.info(f"[{self.job_id}] Found {len(candidates)} question candidates")
        return candidates

    async def _get_skill_depth_candidates(self) -> list[QuestionCandidate]:
        """Get candidates for deep skill probing based on verified evidence."""
        candidates = []
        skill_questions = await self.kg.get_skill_depth_questions()

        for sq in skill_questions:
            # Build evidence chain
            evidence_chain = []
            for impl in sq.get("implementations", []):
                evidence_chain.append({
                    "type": "NotableImplementation",
                    "name": impl["implementation"],
                    "repository": impl["repository"],
                    "file_path": impl.get("file_path"),
                    "description": impl.get("description"),
                })

            code_reference = None
            if sq.get("implementations"):
                impl = sq["implementations"][0]
                code_reference = {
                    "file_path": impl.get("file_path"),
                    "repository": impl.get("repository"),
                    "code_snippet": impl.get("code_snippet"),
                    "why_notable": impl.get("why_notable"),
                }

            candidates.append(QuestionCandidate(
                topic=sq["skill"],
                category="skill_depth",
                priority=sq.get("priority", 50),
                evidence_chain=evidence_chain,
                context={
                    "evidence_count": sq["evidence_count"],
                    "question_potential": sum(i.get("question_potential", 0) for i in sq.get("implementations", [])),
                },
                code_reference=code_reference,
            ))

        return candidates

    async def _get_gap_candidates(self) -> list[QuestionCandidate]:
        """Get candidates for probing gaps between JD and candidate skills."""
        candidates = []
        gap_questions = await self.kg.get_gap_questions()

        for gq in gap_questions:
            priority = 80 if gq.get("priority") == "required" else 50

            if gq["question_type"] == "gap_probe":
                candidates.append(QuestionCandidate(
                    topic=gq["requirement"],
                    category="gap_probe",
                    priority=priority,
                    evidence_chain=[],
                    context={
                        "probe_reason": gq.get("probe_reason"),
                        "requirement_priority": gq.get("priority"),
                    },
                    recommended_probe=f"The role requires {gq['requirement']}. Can you tell me about your experience with this?",
                ))
            elif gq["question_type"] == "partial_match_probe":
                candidates.append(QuestionCandidate(
                    topic=gq["requirement"],
                    category="partial_match_probe",
                    priority=priority * 0.8,  # Slightly lower than full gaps
                    evidence_chain=[{"type": "SkillMatch", **m} for m in gq.get("matches", [])],
                    context={
                        "probe_reason": gq.get("probe_reason"),
                        "partial_matches": gq.get("matches"),
                    },
                    recommended_probe=f"You have some experience with {gq['requirement']}, but can you elaborate on your depth of knowledge?",
                ))

        return candidates

    async def _get_conflict_candidates(self) -> list[QuestionCandidate]:
        """Get candidates for probing claim-evidence conflicts."""
        candidates = []

        # Run conflict detection
        report = await self.conflict_detector.detect_all_conflicts()

        for conflict in report.conflicts:
            priority_map = {"high": 90, "medium": 70, "low": 40}
            priority = priority_map.get(conflict.severity, 50)

            candidates.append(QuestionCandidate(
                topic=conflict.claim,
                category="conflict_probe",
                priority=priority,
                evidence_chain=[{
                    "type": "Conflict",
                    "conflict_type": conflict.conflict_type,
                    "expected": conflict.expected_evidence,
                    "actual": conflict.actual_evidence,
                }],
                context={
                    "claim_source": conflict.claim_source,
                    "conflict_type": conflict.conflict_type,
                    "severity": conflict.severity,
                    "analysis": conflict.analysis,
                },
                recommended_probe=conflict.recommended_probe,
            ))

        return candidates

    async def _get_implementation_candidates(self) -> list[QuestionCandidate]:
        """Get candidates for implementation/code review questions."""
        candidates = []

        # Get notable implementations directly
        from .graph_store import get_graph_store
        store = get_graph_store(self.job_id)

        implementations = await store.get_nodes_by_type("NotableImplementation")

        for impl in implementations:
            props = impl.get("properties", {})
            question_potential = props.get("question_potential", 0)

            if question_potential < 0.5:  # Skip low-potential implementations
                continue

            candidates.append(QuestionCandidate(
                topic=impl["name"],
                category="implementation_review",
                priority=question_potential * 100,
                evidence_chain=[],
                context={
                    "description": props.get("description"),
                    "why_notable": props.get("why_notable"),
                    "file_path": props.get("file_path"),
                },
                code_reference={
                    "file_path": props.get("file_path"),
                    "line_start": props.get("line_start"),
                    "line_end": props.get("line_end"),
                    "code_snippet": props.get("code_snippet"),
                },
                recommended_probe=f"I noticed an interesting implementation in {props.get('file_path', 'your code')}. Can you walk me through your thought process here?",
            ))

        return candidates

    async def get_question_candidates_by_category(
        self,
        category: str,
    ) -> list[QuestionCandidate]:
        """Get question candidates filtered by category."""
        all_candidates = await self.get_all_question_candidates()
        return [c for c in all_candidates if c.category == category]

    async def get_top_question_candidates(
        self,
        limit: int = 25,
        balance_categories: bool = True,
    ) -> list[QuestionCandidate]:
        """Get top question candidates with optional category balancing.

        Args:
            limit: Maximum number of candidates to return
            balance_categories: If True, ensure representation from all categories

        Returns:
            Sorted list of question candidates
        """
        all_candidates = await self.get_all_question_candidates()

        if not balance_categories or len(all_candidates) <= limit:
            return all_candidates[:limit]

        # Balance across categories (include partial_match_probe)
        categories = ["skill_depth", "gap_probe", "conflict_probe", "implementation_review", "partial_match_probe"]
        active_categories = [cat for cat in categories if any(c.category == cat for c in all_candidates)]
        per_category = max(3, limit // len(active_categories)) if active_categories else 5

        balanced = []
        by_category: dict[str, list[QuestionCandidate]] = {}

        for c in all_candidates:
            by_category.setdefault(c.category, []).append(c)

        # Take top from each active category
        for cat in active_categories:
            cat_candidates = by_category.get(cat, [])
            balanced.extend(cat_candidates[:per_category])

        # Fill remaining slots with highest priority overall
        remaining = limit - len(balanced)
        if remaining > 0:
            used_topics = {c.topic for c in balanced}
            extras = [c for c in all_candidates if c.topic not in used_topics]
            balanced.extend(extras[:remaining])

        # Final sort by priority
        balanced.sort(key=lambda x: x.priority, reverse=True)

        return balanced[:limit]

    async def get_evidence_chain_for_topic(self, topic: str) -> list[dict[str, Any]]:
        """Get the full evidence chain for a specific topic.

        Traverses the graph to find all connected evidence for a skill/topic.
        """
        from .graph_store import get_graph_store
        store = get_graph_store(self.job_id)

        # Try to find the topic as a Skill first
        skill = await store.find_node_by_name("Skill", topic)
        if skill:
            # Traverse from skill to find all evidence
            paths = await store.traverse_from_node(
                skill["id"],
                relation_types=["demonstrated_by", "contains_code", "supported_by"],
                direction="both",
                max_depth=3,
            )

            evidence_chain = []
            for path in paths:
                for step in path:
                    if "node" in step:
                        node = step["node"]
                        evidence_chain.append({
                            "entity_type": node["entity_type"],
                            "name": node["name"],
                            "properties": node["properties"],
                        })
                    if "edge" in step:
                        edge = step["edge"]
                        evidence_chain.append({
                            "relation": edge["relation_type"],
                            "confidence": edge["confidence"],
                        })

            return evidence_chain

        # Try as a Requirement
        req = await store.find_node_by_name("Requirement", topic)
        if req:
            paths = await store.traverse_from_node(
                req["id"],
                relation_types=["matches_requirement", "requires_skill"],
                direction="both",
                max_depth=2,
            )

            evidence_chain = []
            for path in paths:
                for step in path:
                    if "node" in step:
                        node = step["node"]
                        evidence_chain.append({
                            "entity_type": node["entity_type"],
                            "name": node["name"],
                            "properties": node["properties"],
                        })

            return evidence_chain

        return []

    async def get_kg_summary_for_question_generation(self) -> dict[str, Any]:
        """Get a summary of KG data relevant for question generation."""
        summary = await self.kg.get_summary()

        # Add question-specific stats
        all_candidates = await self.get_all_question_candidates()
        by_category = {}
        for c in all_candidates:
            by_category[c.category] = by_category.get(c.category, 0) + 1

        return {
            **summary,
            "question_generation": {
                "total_candidates": len(all_candidates),
                "by_category": by_category,
                "top_priority": all_candidates[0].priority if all_candidates else 0,
            },
        }


def get_interview_graph_queries(job_id: str) -> InterviewGraphQueries:
    """Factory function to create an InterviewGraphQueries instance."""
    return InterviewGraphQueries(job_id)
