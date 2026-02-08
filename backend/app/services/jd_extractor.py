"""
backend/app/services/jd_extractor.py
Extract KG entities from JD (Job Description) analysis results
"""
import logging
from typing import Any

from .entity_models import ExtractedEntity, ExtractedRelation, ExtractionResult

logger = logging.getLogger(__name__)


class JDEntityExtractor:
    """Extract KG entities from JD analysis results."""

    def __init__(self, source: str = "jd_analysis"):
        self.source = source

    def extract(self, jd_analysis: dict[str, Any]) -> ExtractionResult:
        """Extract entities and relations from JDAnalysis."""
        entities: list[ExtractedEntity] = []
        relations: list[ExtractedRelation] = []

        provenance_base = {
            "source": self.source,
            "extraction_method": "jd_analysis",
        }

        job_title = jd_analysis.get("job_title", "Unknown Position")
        company_name = jd_analysis.get("company_name", "Unknown Company")

        # Company Info entity
        if company_name != "Unknown Company":
            entities.append(ExtractedEntity(
                entity_type="CompanyInfo",
                name=company_name,
                properties={
                    "culture": jd_analysis.get("company_culture", []),
                },
                provenance=provenance_base,
            ))

        # Requirements
        for req in jd_analysis.get("requirements", []):
            req_name = req.get("skill", "Unknown Requirement")
            req_category = req.get("category", "필수")

            entities.append(ExtractedEntity(
                entity_type="Requirement",
                name=req_name,
                properties={
                    "category": req_category,
                    "detail": req.get("detail"),
                    "experience_years": req.get("experience_years"),
                    "priority": "required" if req_category == "필수" else "preferred",
                },
                provenance={
                    **provenance_base,
                    "field": "requirements",
                },
            ))

            # Relation to job
            relation_type = "requires_skill" if req_category == "필수" else "prefers_skill"
            relations.append(ExtractedRelation(
                source_name=job_title,
                source_type="Job",
                target_name=req_name,
                target_type="Requirement",
                relation_type=relation_type,
                confidence=100,
            ))

        # Responsibilities
        for i, resp in enumerate(jd_analysis.get("responsibilities", [])):
            resp_name = f"Responsibility_{i+1}"
            entities.append(ExtractedEntity(
                entity_type="Responsibility",
                name=resp_name,
                properties={
                    "description": resp,
                },
                provenance={
                    **provenance_base,
                    "field": "responsibilities",
                },
            ))

        # Skill matches - create match relations
        for match in jd_analysis.get("skill_matches", []):
            if match.get("candidate_skill"):
                relations.append(ExtractedRelation(
                    source_name=match["candidate_skill"],
                    source_type="Skill",
                    target_name=match["required_skill"],
                    target_type="Requirement",
                    relation_type="matches_requirement",
                    confidence=int(match.get("confidence", 0) * 100),
                    properties={
                        "match_type": match.get("match_type"),
                        "evidence": match.get("evidence"),
                    },
                ))

        logger.info(f"Extracted {len(entities)} entities and {len(relations)} relations from JD analysis")

        return ExtractionResult(
            entities=entities,
            relations=relations,
            metadata={
                "job_title": job_title,
                "company_name": company_name,
                "overall_match_score": jd_analysis.get("overall_match_score", 0),
                "gaps": jd_analysis.get("gaps", []),
                "strengths": jd_analysis.get("strengths", []),
            },
        )


def get_jd_extractor(source: str = "jd_analysis") -> JDEntityExtractor:
    return JDEntityExtractor(source)
