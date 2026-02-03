"""
backend/app/services/conflict_detector.py
Claim-Evidence Conflict Detection for Interview Question Generation
Detects discrepancies between resume claims and code evidence
"""
import logging
from typing import Any

from pydantic import BaseModel, Field

from .graph_store import GraphStore, get_graph_store
from .knowledge_graph import KnowledgeGraphService, get_knowledge_graph

logger = logging.getLogger(__name__)


class ConflictAnalysis(BaseModel):
    """Analysis of a claim-evidence conflict."""
    claim: str
    claim_source: str  # e.g., "resume", "linkedin"
    expected_evidence: str
    actual_evidence: str | None
    conflict_type: str  # "missing", "contradicting", "overstated", "understated"
    severity: str  # "high", "medium", "low"
    confidence: int  # 0-100
    analysis: str
    recommended_probe: str


class ConflictReport(BaseModel):
    """Complete conflict detection report."""
    job_id: str
    total_claims_analyzed: int
    conflicts: list[ConflictAnalysis] = Field(default_factory=list)
    verified_claims: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class ConflictDetector:
    """Detects conflicts between candidate claims and code evidence.

    Uses Knowledge Graph traversal to find:
    1. Skills claimed but not demonstrated in code
    2. Experience levels that don't match code complexity
    3. Technologies mentioned but not found in repositories
    4. Inconsistencies between resume and actual contributions
    """

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.kg = get_knowledge_graph(job_id)
        self.store = get_graph_store(job_id)

    async def detect_all_conflicts(self) -> ConflictReport:
        """Run all conflict detection checks and generate a report."""
        logger.info(f"[{self.job_id}] Starting conflict detection")

        conflicts: list[ConflictAnalysis] = []
        verified: list[dict[str, Any]] = []

        # 1. Check for unverified skill claims
        skill_conflicts = await self._detect_skill_conflicts()
        conflicts.extend(skill_conflicts["conflicts"])
        verified.extend(skill_conflicts["verified"])

        # 2. Check for experience level mismatches
        exp_conflicts = await self._detect_experience_conflicts()
        conflicts.extend(exp_conflicts)

        # 3. Check for technology claim gaps
        tech_conflicts = await self._detect_technology_conflicts()
        conflicts.extend(tech_conflicts)

        # Store conflicts in graph for later use
        await self._store_conflicts(conflicts)

        report = ConflictReport(
            job_id=self.job_id,
            total_claims_analyzed=len(conflicts) + len(verified),
            conflicts=conflicts,
            verified_claims=verified,
            summary={
                "total_conflicts": len(conflicts),
                "high_severity": len([c for c in conflicts if c.severity == "high"]),
                "medium_severity": len([c for c in conflicts if c.severity == "medium"]),
                "low_severity": len([c for c in conflicts if c.severity == "low"]),
                "conflict_types": self._count_by_type(conflicts),
                "verification_rate": len(verified) / (len(conflicts) + len(verified)) * 100 if conflicts or verified else 0,
            },
        )

        logger.info(
            f"[{self.job_id}] Conflict detection complete: "
            f"{len(conflicts)} conflicts, {len(verified)} verified"
        )

        return report

    async def _detect_skill_conflicts(self) -> dict[str, Any]:
        """Detect conflicts between claimed skills and code evidence."""
        skills_with_evidence = await self.kg.get_skills_with_evidence()

        conflicts = []
        verified = []

        for skill_data in skills_with_evidence:
            skill_name = skill_data["skill"]
            is_claimed = skill_data["is_claimed"]
            is_verified = skill_data["verified"]
            evidence = skill_data["evidence"]

            if is_claimed and not is_verified:
                # Skill claimed but not found in code
                conflicts.append(ConflictAnalysis(
                    claim=f"Proficiency in {skill_name}",
                    claim_source="resume",
                    expected_evidence=f"Code demonstrating {skill_name} usage",
                    actual_evidence=None,
                    conflict_type="missing",
                    severity=self._determine_skill_severity(skill_name),
                    confidence=85,
                    analysis=f"Candidate claims {skill_name} on resume, but no evidence found in analyzed code repositories.",
                    recommended_probe=self._generate_skill_probe(skill_name),
                ))
            elif is_claimed and is_verified:
                # Verified claim
                verified.append({
                    "skill": skill_name,
                    "evidence_count": skill_data["evidence_count"],
                    "evidence_sources": [e["name"] for e in evidence[:3]],
                })

        return {"conflicts": conflicts, "verified": verified}

    async def _detect_experience_conflicts(self) -> list[ConflictAnalysis]:
        """Detect conflicts between stated experience level and code complexity."""
        conflicts = []

        # Get candidate profile info from KG
        work_experiences = await self.store.get_nodes_by_type("WorkExperience")
        repositories = await self.store.get_nodes_by_type("Repository")

        if not work_experiences or not repositories:
            return conflicts

        # Calculate average code complexity from repositories
        total_complexity = 0
        repo_count = 0
        for repo in repositories:
            if contrib := repo.get("properties", {}).get("candidate_contribution", {}):
                if avg_complexity := contrib.get("avg_complexity"):
                    total_complexity += avg_complexity
                    repo_count += 1

        if repo_count == 0:
            return conflicts

        avg_complexity = total_complexity / repo_count

        # Check if complexity matches stated experience
        # Note: This is a simplified heuristic - real implementation would be more nuanced
        for exp in work_experiences:
            position = exp.get("properties", {}).get("position", "")
            position_lower = position.lower()

            expected_complexity = self._expected_complexity_for_role(position_lower)

            if expected_complexity and avg_complexity < expected_complexity * 0.5:
                conflicts.append(ConflictAnalysis(
                    claim=f"Experience as {position}",
                    claim_source="resume",
                    expected_evidence=f"Code complexity >= {expected_complexity} for {position} role",
                    actual_evidence=f"Average complexity: {avg_complexity:.1f}",
                    conflict_type="overstated",
                    severity="medium",
                    confidence=70,
                    analysis=f"Code complexity ({avg_complexity:.1f}) appears lower than expected for stated {position} experience.",
                    recommended_probe=f"Can you walk me through a complex problem you solved as a {position}? What was the architectural approach?",
                ))

        return conflicts

    async def _detect_technology_conflicts(self) -> list[ConflictAnalysis]:
        """Detect conflicts between stated technologies and actual usage."""
        conflicts = []

        # Get skills from profile vs code
        profile_skills = await self.store.get_nodes_by_type("Skill")
        resume_skills = [s for s in profile_skills if s.get("properties", {}).get("source_type") == "resume"]
        code_skills = [s for s in profile_skills if s.get("properties", {}).get("source_type") == "code"]

        resume_skill_names = {s["name"].lower() for s in resume_skills}
        code_skill_names = {s["name"].lower() for s in code_skills}

        # Check for major technologies claimed but not in code
        major_techs = ["python", "java", "javascript", "react", "vue", "angular", "node.js",
                       "django", "fastapi", "spring", "postgresql", "mongodb", "kubernetes", "docker"]

        for tech in major_techs:
            if tech in resume_skill_names and tech not in code_skill_names:
                # Check if there might be related technologies
                related_found = self._find_related_tech(tech, code_skill_names)

                if not related_found:
                    conflicts.append(ConflictAnalysis(
                        claim=f"Experience with {tech.title()}",
                        claim_source="resume",
                        expected_evidence=f"Code using {tech.title()}",
                        actual_evidence="Not found in analyzed repositories",
                        conflict_type="missing",
                        severity="medium" if tech in ["python", "java", "javascript"] else "low",
                        confidence=75,
                        analysis=f"{tech.title()} listed on resume but not found in provided code samples.",
                        recommended_probe=f"Tell me about a project where you used {tech.title()}. What was your role and contribution?",
                    ))

        return conflicts

    async def _store_conflicts(self, conflicts: list[ConflictAnalysis]) -> None:
        """Store detected conflicts in the graph for later query."""
        for conflict in conflicts:
            # Find or create claim node
            claim_node = await self.store.find_node_by_name("Skill", conflict.claim.replace("Proficiency in ", "").replace("Experience with ", ""))
            claim_node_id = claim_node["id"] if claim_node else None

            # Create claim-evidence record
            await self.store.create_claim_evidence(
                claim_node_id=claim_node_id,
                evidence_node_id=None,
                evidence_type=conflict.conflict_type,
                evidence_strength=conflict.confidence,
                analysis=conflict.analysis,
                recommended_probe=conflict.recommended_probe,
            )

    def _determine_skill_severity(self, skill_name: str) -> str:
        """Determine severity of a missing skill based on its importance."""
        critical_skills = ["python", "java", "javascript", "sql", "git"]
        important_skills = ["react", "node.js", "docker", "kubernetes", "aws"]

        skill_lower = skill_name.lower()
        if any(s in skill_lower for s in critical_skills):
            return "high"
        elif any(s in skill_lower for s in important_skills):
            return "medium"
        return "low"

    def _generate_skill_probe(self, skill_name: str) -> str:
        """Generate an interview probe question for an unverified skill."""
        probes = {
            "python": "Can you describe your approach to structuring Python projects? What patterns do you typically use?",
            "java": "Walk me through how you would design a Java service with dependency injection. What frameworks have you used?",
            "javascript": "How do you handle asynchronous operations in JavaScript? Can you compare callbacks, promises, and async/await?",
            "react": "Explain your state management approach in React. When would you use context vs. Redux vs. other solutions?",
            "docker": "How do you structure a multi-container Docker application? Walk me through your docker-compose setup.",
            "kubernetes": "Describe how you would deploy a microservices application to Kubernetes. What resources would you define?",
            "postgresql": "How do you optimize PostgreSQL queries? Can you explain your approach to indexing?",
            "aws": "Walk me through designing a scalable architecture on AWS. What services would you use and why?",
        }

        skill_lower = skill_name.lower()
        for key, probe in probes.items():
            if key in skill_lower:
                return probe

        return f"Can you describe a specific project where you used {skill_name}? What challenges did you face and how did you solve them?"

    def _expected_complexity_for_role(self, position: str) -> float | None:
        """Return expected code complexity for different roles."""
        if any(t in position for t in ["senior", "lead", "principal", "staff"]):
            return 15.0
        elif any(t in position for t in ["mid", "regular", "software engineer"]):
            return 10.0
        elif any(t in position for t in ["junior", "associate", "entry"]):
            return 5.0
        return None

    def _find_related_tech(self, tech: str, code_skills: set[str]) -> bool:
        """Check if related technologies are present."""
        tech_relations = {
            "python": ["django", "fastapi", "flask", "pandas", "numpy"],
            "javascript": ["node.js", "react", "vue", "angular", "typescript"],
            "java": ["spring", "maven", "gradle", "kotlin"],
            "react": ["javascript", "typescript", "next.js"],
            "vue": ["javascript", "typescript", "nuxt"],
        }

        related = tech_relations.get(tech.lower(), [])
        return any(r in code_skills for r in related)

    def _count_by_type(self, conflicts: list[ConflictAnalysis]) -> dict[str, int]:
        """Count conflicts by type."""
        counts: dict[str, int] = {}
        for c in conflicts:
            counts[c.conflict_type] = counts.get(c.conflict_type, 0) + 1
        return counts


def get_conflict_detector(job_id: str) -> ConflictDetector:
    """Factory function to create a ConflictDetector instance."""
    return ConflictDetector(job_id)
