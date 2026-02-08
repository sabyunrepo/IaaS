"""
backend/app/services/candidate_extractor.py
Extract KG entities from candidate profile analysis
"""
import logging
from typing import Any

from .entity_models import ExtractedEntity, ExtractedRelation, ExtractionResult

logger = logging.getLogger(__name__)


class CandidateEntityExtractor:
    """Extract KG entities from candidate profile analysis."""

    def __init__(self, source: str = "document_analysis"):
        self.source = source

    def extract(self, profile: dict[str, Any]) -> ExtractionResult:
        """Extract entities and relations from a CandidateProfile."""
        entities: list[ExtractedEntity] = []
        relations: list[ExtractedRelation] = []

        provenance_base = {
            "source": self.source,
            "extraction_method": "structured_extraction",
        }

        # Extract Skills
        for skill in profile.get("skills", []):
            skill_name = skill if isinstance(skill, str) else skill.get("name", str(skill))
            skill_level = skill.get("level", "unknown") if isinstance(skill, dict) else "mentioned"

            entities.append(ExtractedEntity(
                entity_type="Skill",
                name=skill_name,
                properties={
                    "level": skill_level,
                    "category": self._categorize_skill(skill_name),
                    "source_type": "resume",
                },
                provenance={
                    **provenance_base,
                    "field": "skills",
                },
            ))

        # Extract Work Experience
        for exp in profile.get("work_history", []):
            exp_name = f"{exp.get('position', 'Unknown')} at {exp.get('company', 'Unknown')}"
            entities.append(ExtractedEntity(
                entity_type="WorkExperience",
                name=exp_name,
                properties={
                    "company": exp.get("company"),
                    "position": exp.get("position"),
                    "period": exp.get("period"),
                    "description": exp.get("description"),
                    "tech_stack": exp.get("tech_stack", []),
                },
                provenance={
                    **provenance_base,
                    "field": "work_history",
                },
            ))

            # Create relations for tech stack in work experience
            for tech in exp.get("tech_stack", []):
                relations.append(ExtractedRelation(
                    source_name=exp_name,
                    source_type="WorkExperience",
                    target_name=tech,
                    target_type="Skill",
                    relation_type="used_technology",
                    confidence=90,
                ))

        # Extract Education
        for edu in profile.get("education", []):
            edu_name = f"{edu.get('degree', '')} in {edu.get('major', 'Unknown')} from {edu.get('institution', 'Unknown')}"
            entities.append(ExtractedEntity(
                entity_type="Education",
                name=edu_name.strip(),
                properties={
                    "institution": edu.get("institution"),
                    "degree": edu.get("degree"),
                    "major": edu.get("major"),
                    "graduation_year": edu.get("graduation_year"),
                },
                provenance={
                    **provenance_base,
                    "field": "education",
                },
            ))

        # Extract Projects
        for proj in profile.get("projects", []):
            proj_name = proj.get("name", "Unknown Project")
            entities.append(ExtractedEntity(
                entity_type="Project",
                name=proj_name,
                properties={
                    "description": proj.get("description"),
                    "role": proj.get("role"),
                    "tech_stack": proj.get("tech_stack", []),
                    "period": proj.get("period"),
                    "url": proj.get("url"),
                },
                provenance={
                    **provenance_base,
                    "field": "projects",
                },
            ))

            # Create relations for project tech stack
            for tech in proj.get("tech_stack", []):
                relations.append(ExtractedRelation(
                    source_name=proj_name,
                    source_type="Project",
                    target_name=tech,
                    target_type="Skill",
                    relation_type="used_technology",
                    confidence=85,
                ))

        # Create has_skill relations from candidate to skills
        candidate_name = profile.get("name", "Candidate")
        for skill_entity in [e for e in entities if e.entity_type == "Skill"]:
            relations.append(ExtractedRelation(
                source_name=candidate_name,
                source_type="Candidate",
                target_name=skill_entity.name,
                target_type="Skill",
                relation_type="has_skill",
                confidence=80,  # Claims from resume need verification
            ))

        logger.info(f"Extracted {len(entities)} entities and {len(relations)} relations from profile")

        return ExtractionResult(
            entities=entities,
            relations=relations,
            metadata={
                "candidate_name": candidate_name,
                "experience_years": profile.get("experience_years"),
                "source": self.source,
            },
        )

    def _categorize_skill(self, skill_name: str) -> str:
        """Categorize a skill based on common patterns."""
        skill_lower = skill_name.lower()

        categories = {
            "programming_language": ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php", "swift", "kotlin"],
            "frontend": ["react", "vue", "angular", "svelte", "html", "css", "tailwind", "bootstrap", "next.js", "nuxt"],
            "backend": ["fastapi", "django", "flask", "express", "spring", "node.js", "rails", "laravel", "asp.net"],
            "database": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "sqlite"],
            "cloud": ["aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ansible"],
            "data_science": ["pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "spark", "hadoop"],
            "devops": ["ci/cd", "jenkins", "github actions", "gitlab", "docker", "kubernetes"],
        }

        for category, keywords in categories.items():
            if any(kw in skill_lower for kw in keywords):
                return category

        return "other"


def get_candidate_extractor(source: str = "document_analysis") -> CandidateEntityExtractor:
    return CandidateEntityExtractor(source)
