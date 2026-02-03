"""
backend/app/services/graph_store.py
PostgreSQL-based Knowledge Graph Store for entity and relationship persistence
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Literal

from sqlalchemy import select, delete, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.database import KGNodeDB, KGEdgeDB, ClaimEvidenceDB

logger = logging.getLogger(__name__)

# Type aliases for entity and relation types
EntityType = Literal[
    # Candidate Domain
    "Skill", "WorkExperience", "Education", "Project", "Certification",
    # Code Domain
    "Repository", "CodePattern", "NotableImplementation", "TechStack",
    # JD Domain
    "Requirement", "Responsibility", "CompanyInfo",
]

RelationType = Literal[
    # Skill relationships
    "has_skill", "demonstrated_by", "requires", "matches",
    # Evidence relationships
    "supported_by", "contradicted_by", "verified_by",
    # Work relationships
    "worked_at", "used_technology", "contributed_to",
    # JD relationships
    "requires_skill", "prefers_skill", "matches_requirement",
    # Code relationships
    "implements_pattern", "contains_code", "shows_proficiency",
]

EvidenceType = Literal["supporting", "contradicting", "neutral", "missing"]


class GraphStore:
    """PostgreSQL-based Knowledge Graph Store.

    Provides CRUD operations for Knowledge Graph nodes and edges,
    with support for relationship queries and claim-evidence tracking.
    """

    def __init__(self, job_id: str):
        self.job_id = uuid.UUID(job_id) if isinstance(job_id, str) else job_id

    # ==========================================
    # Node Operations
    # ==========================================

    async def create_node(
        self,
        entity_type: str,
        name: str,
        properties: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
        embedding: list[float] | None = None,
    ) -> str:
        """Create a new KG node and return its ID."""
        node_id = uuid.uuid4()
        async with async_session() as session:
            node = KGNodeDB(
                id=node_id,
                job_id=self.job_id,
                entity_type=entity_type,
                name=name,
                properties=properties or {},
                provenance=provenance,
                embedding=embedding,
            )
            session.add(node)
            await session.commit()
            logger.debug(f"[{self.job_id}] Created node: {entity_type}/{name}")
        return str(node_id)

    async def create_nodes_batch(
        self,
        nodes: list[dict[str, Any]],
    ) -> list[str]:
        """Batch create multiple nodes. Returns list of node IDs."""
        node_ids = []
        async with async_session() as session:
            for node_data in nodes:
                node_id = uuid.uuid4()
                node = KGNodeDB(
                    id=node_id,
                    job_id=self.job_id,
                    entity_type=node_data["entity_type"],
                    name=node_data["name"],
                    properties=node_data.get("properties", {}),
                    provenance=node_data.get("provenance"),
                    embedding=node_data.get("embedding"),
                )
                session.add(node)
                node_ids.append(str(node_id))
            await session.commit()
        logger.info(f"[{self.job_id}] Batch created {len(node_ids)} nodes")
        return node_ids

    async def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get a node by ID."""
        async with async_session() as session:
            stmt = select(KGNodeDB).where(KGNodeDB.id == uuid.UUID(node_id))
            result = await session.execute(stmt)
            node = result.scalar_one_or_none()
            if node:
                return self._node_to_dict(node)
        return None

    async def get_nodes_by_type(self, entity_type: str) -> list[dict[str, Any]]:
        """Get all nodes of a specific type for this job."""
        async with async_session() as session:
            stmt = select(KGNodeDB).where(
                and_(
                    KGNodeDB.job_id == self.job_id,
                    KGNodeDB.entity_type == entity_type,
                )
            )
            result = await session.execute(stmt)
            nodes = result.scalars().all()
            return [self._node_to_dict(n) for n in nodes]

    async def find_node_by_name(
        self,
        entity_type: str,
        name: str,
    ) -> dict[str, Any] | None:
        """Find a node by entity type and name."""
        async with async_session() as session:
            stmt = select(KGNodeDB).where(
                and_(
                    KGNodeDB.job_id == self.job_id,
                    KGNodeDB.entity_type == entity_type,
                    KGNodeDB.name == name,
                )
            )
            result = await session.execute(stmt)
            node = result.scalar_one_or_none()
            if node:
                return self._node_to_dict(node)
        return None

    async def update_node(
        self,
        node_id: str,
        properties: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> bool:
        """Update node properties and/or provenance."""
        async with async_session() as session:
            stmt = select(KGNodeDB).where(KGNodeDB.id == uuid.UUID(node_id))
            result = await session.execute(stmt)
            node = result.scalar_one_or_none()
            if node:
                if properties:
                    node.properties = {**node.properties, **properties}
                if provenance:
                    node.provenance = {**(node.provenance or {}), **provenance}
                await session.commit()
                return True
        return False

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and its associated edges."""
        async with async_session() as session:
            stmt = delete(KGNodeDB).where(KGNodeDB.id == uuid.UUID(node_id))
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    # ==========================================
    # Edge Operations
    # ==========================================

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: dict[str, Any] | None = None,
        confidence: int = 100,
    ) -> str:
        """Create an edge between two nodes."""
        edge_id = uuid.uuid4()
        async with async_session() as session:
            edge = KGEdgeDB(
                id=edge_id,
                job_id=self.job_id,
                source_id=uuid.UUID(source_id),
                target_id=uuid.UUID(target_id),
                relation_type=relation_type,
                properties=properties or {},
                confidence=confidence,
            )
            session.add(edge)
            await session.commit()
            logger.debug(f"[{self.job_id}] Created edge: {relation_type}")
        return str(edge_id)

    async def create_edges_batch(
        self,
        edges: list[dict[str, Any]],
    ) -> list[str]:
        """Batch create multiple edges."""
        edge_ids = []
        async with async_session() as session:
            for edge_data in edges:
                edge_id = uuid.uuid4()
                edge = KGEdgeDB(
                    id=edge_id,
                    job_id=self.job_id,
                    source_id=uuid.UUID(edge_data["source_id"]),
                    target_id=uuid.UUID(edge_data["target_id"]),
                    relation_type=edge_data["relation_type"],
                    properties=edge_data.get("properties", {}),
                    confidence=edge_data.get("confidence", 100),
                )
                session.add(edge)
                edge_ids.append(str(edge_id))
            await session.commit()
        logger.info(f"[{self.job_id}] Batch created {len(edge_ids)} edges")
        return edge_ids

    async def get_edges_by_relation(self, relation_type: str) -> list[dict[str, Any]]:
        """Get all edges of a specific relation type for this job."""
        async with async_session() as session:
            stmt = select(KGEdgeDB).where(
                and_(
                    KGEdgeDB.job_id == self.job_id,
                    KGEdgeDB.relation_type == relation_type,
                )
            )
            result = await session.execute(stmt)
            edges = result.scalars().all()
            return [self._edge_to_dict(e) for e in edges]

    async def get_outgoing_edges(self, node_id: str) -> list[dict[str, Any]]:
        """Get all outgoing edges from a node."""
        async with async_session() as session:
            stmt = select(KGEdgeDB).where(
                KGEdgeDB.source_id == uuid.UUID(node_id)
            )
            result = await session.execute(stmt)
            edges = result.scalars().all()
            return [self._edge_to_dict(e) for e in edges]

    async def get_incoming_edges(self, node_id: str) -> list[dict[str, Any]]:
        """Get all incoming edges to a node."""
        async with async_session() as session:
            stmt = select(KGEdgeDB).where(
                KGEdgeDB.target_id == uuid.UUID(node_id)
            )
            result = await session.execute(stmt)
            edges = result.scalars().all()
            return [self._edge_to_dict(e) for e in edges]

    # ==========================================
    # Claim-Evidence Operations
    # ==========================================

    async def create_claim_evidence(
        self,
        claim_node_id: str | None,
        evidence_node_id: str | None,
        evidence_type: str,
        evidence_strength: int,
        analysis: str | None = None,
        recommended_probe: str | None = None,
    ) -> str:
        """Create a claim-evidence verification record."""
        record_id = uuid.uuid4()
        async with async_session() as session:
            record = ClaimEvidenceDB(
                id=record_id,
                job_id=self.job_id,
                claim_node_id=uuid.UUID(claim_node_id) if claim_node_id else None,
                evidence_node_id=uuid.UUID(evidence_node_id) if evidence_node_id else None,
                evidence_type=evidence_type,
                evidence_strength=evidence_strength,
                analysis=analysis,
                recommended_probe=recommended_probe,
            )
            session.add(record)
            await session.commit()
            logger.debug(f"[{self.job_id}] Created claim-evidence: {evidence_type}")
        return str(record_id)

    async def get_claim_evidence_by_type(
        self,
        evidence_type: str,
    ) -> list[dict[str, Any]]:
        """Get all claim-evidence records of a specific type."""
        async with async_session() as session:
            stmt = select(ClaimEvidenceDB).where(
                and_(
                    ClaimEvidenceDB.job_id == self.job_id,
                    ClaimEvidenceDB.evidence_type == evidence_type,
                )
            ).order_by(ClaimEvidenceDB.evidence_strength.desc())
            result = await session.execute(stmt)
            records = result.scalars().all()
            return [self._claim_evidence_to_dict(r) for r in records]

    async def get_all_claim_evidence(self) -> list[dict[str, Any]]:
        """Get all claim-evidence records for this job."""
        async with async_session() as session:
            stmt = select(ClaimEvidenceDB).where(
                ClaimEvidenceDB.job_id == self.job_id
            ).order_by(ClaimEvidenceDB.evidence_strength.desc())
            result = await session.execute(stmt)
            records = result.scalars().all()
            return [self._claim_evidence_to_dict(r) for r in records]

    # ==========================================
    # Graph Query Operations
    # ==========================================

    async def traverse_from_node(
        self,
        node_id: str,
        relation_types: list[str] | None = None,
        direction: Literal["outgoing", "incoming", "both"] = "outgoing",
        max_depth: int = 2,
    ) -> list[dict[str, Any]]:
        """Traverse the graph from a starting node.

        Returns a list of paths, where each path contains nodes and edges.
        """
        visited = set()
        paths = []

        async def _traverse(current_id: str, current_path: list, depth: int):
            if depth > max_depth or current_id in visited:
                return
            visited.add(current_id)

            edges = []
            if direction in ("outgoing", "both"):
                edges.extend(await self.get_outgoing_edges(current_id))
            if direction in ("incoming", "both"):
                edges.extend(await self.get_incoming_edges(current_id))

            for edge in edges:
                if relation_types and edge["relation_type"] not in relation_types:
                    continue

                next_id = edge["target_id"] if edge["source_id"] == current_id else edge["source_id"]
                next_node = await self.get_node(next_id)
                if next_node:
                    new_path = current_path + [{"edge": edge, "node": next_node}]
                    paths.append(new_path)
                    await _traverse(next_id, new_path, depth + 1)

        start_node = await self.get_node(node_id)
        if start_node:
            await _traverse(node_id, [{"node": start_node}], 0)

        return paths

    async def find_paths_between(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 3,
    ) -> list[list[dict[str, Any]]]:
        """Find all paths between two nodes up to max_depth."""
        paths = []

        async def _find_path(current_id: str, path: list, visited: set):
            if len(path) > max_depth:
                return
            if current_id == target_id:
                paths.append(path.copy())
                return
            if current_id in visited:
                return

            visited.add(current_id)
            edges = await self.get_outgoing_edges(current_id)

            for edge in edges:
                next_node = await self.get_node(edge["target_id"])
                if next_node:
                    path.append({"edge": edge, "node": next_node})
                    await _find_path(edge["target_id"], path, visited)
                    path.pop()

            visited.remove(current_id)

        start_node = await self.get_node(source_id)
        if start_node:
            await _find_path(source_id, [{"node": start_node}], set())

        return paths

    async def get_graph_summary(self) -> dict[str, Any]:
        """Get summary statistics of the knowledge graph for this job."""
        async with async_session() as session:
            # Count nodes by type
            node_stmt = text("""
                SELECT entity_type, COUNT(*) as count
                FROM kg_nodes
                WHERE job_id = :job_id
                GROUP BY entity_type
            """)
            node_result = await session.execute(node_stmt, {"job_id": str(self.job_id)})
            node_counts = {row[0]: row[1] for row in node_result.fetchall()}

            # Count edges by type
            edge_stmt = text("""
                SELECT relation_type, COUNT(*) as count
                FROM kg_edges
                WHERE job_id = :job_id
                GROUP BY relation_type
            """)
            edge_result = await session.execute(edge_stmt, {"job_id": str(self.job_id)})
            edge_counts = {row[0]: row[1] for row in edge_result.fetchall()}

            # Count claim-evidence by type
            claim_stmt = text("""
                SELECT evidence_type, COUNT(*) as count
                FROM claim_evidence
                WHERE job_id = :job_id
                GROUP BY evidence_type
            """)
            claim_result = await session.execute(claim_stmt, {"job_id": str(self.job_id)})
            claim_counts = {row[0]: row[1] for row in claim_result.fetchall()}

        return {
            "job_id": str(self.job_id),
            "node_counts": node_counts,
            "edge_counts": edge_counts,
            "claim_evidence_counts": claim_counts,
            "total_nodes": sum(node_counts.values()),
            "total_edges": sum(edge_counts.values()),
            "total_claim_evidence": sum(claim_counts.values()),
        }

    # ==========================================
    # Cleanup Operations
    # ==========================================

    async def clear_all(self) -> None:
        """Clear all KG data for this job."""
        async with async_session() as session:
            # Delete in order due to foreign keys
            await session.execute(
                delete(ClaimEvidenceDB).where(ClaimEvidenceDB.job_id == self.job_id)
            )
            await session.execute(
                delete(KGEdgeDB).where(KGEdgeDB.job_id == self.job_id)
            )
            await session.execute(
                delete(KGNodeDB).where(KGNodeDB.job_id == self.job_id)
            )
            await session.commit()
        logger.info(f"[{self.job_id}] Cleared all KG data")

    # ==========================================
    # Helper Methods
    # ==========================================

    def _node_to_dict(self, node: KGNodeDB) -> dict[str, Any]:
        return {
            "id": str(node.id),
            "job_id": str(node.job_id),
            "entity_type": node.entity_type,
            "name": node.name,
            "properties": node.properties,
            "provenance": node.provenance,
            "created_at": node.created_at.isoformat() if node.created_at else None,
        }

    def _edge_to_dict(self, edge: KGEdgeDB) -> dict[str, Any]:
        return {
            "id": str(edge.id),
            "job_id": str(edge.job_id),
            "source_id": str(edge.source_id),
            "target_id": str(edge.target_id),
            "relation_type": edge.relation_type,
            "properties": edge.properties,
            "confidence": edge.confidence,
            "created_at": edge.created_at.isoformat() if edge.created_at else None,
        }

    def _claim_evidence_to_dict(self, record: ClaimEvidenceDB) -> dict[str, Any]:
        return {
            "id": str(record.id),
            "job_id": str(record.job_id),
            "claim_node_id": str(record.claim_node_id) if record.claim_node_id else None,
            "evidence_node_id": str(record.evidence_node_id) if record.evidence_node_id else None,
            "evidence_type": record.evidence_type,
            "evidence_strength": record.evidence_strength,
            "analysis": record.analysis,
            "recommended_probe": record.recommended_probe,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }


def get_graph_store(job_id: str) -> GraphStore:
    """Factory function to create a GraphStore instance."""
    return GraphStore(job_id)
