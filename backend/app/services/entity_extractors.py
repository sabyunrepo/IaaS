"""
backend/app/services/entity_extractors.py
Domain-specific entity extractors for Knowledge Graph population
"""
import logging
import re
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================
# Pydantic Models for Extracted Entities
# ============================================

class ExtractedEntity(BaseModel):
    """Base model for extracted KG entities."""
    entity_type: str
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)


class ExtractedRelation(BaseModel):
    """Model for extracted KG relations."""
    source_name: str
    source_type: str
    target_name: str
    target_type: str
    relation_type: str
    confidence: int = 100  # 0-100 scale
    properties: dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    """Result of entity extraction from a document or analysis."""
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relations: list[ExtractedRelation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================
# Candidate Profile Extractor
# ============================================

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


# ============================================
# Code Analysis Extractor
# ============================================

class CodeEntityExtractor:
    """Extract KG entities from code analysis results."""

    def __init__(self, source: str = "code_analysis"):
        self.source = source

    def extract(self, code_analysis: dict[str, Any]) -> ExtractionResult:
        """Extract entities and relations from CodeAnalysis."""
        entities: list[ExtractedEntity] = []
        relations: list[ExtractedRelation] = []

        provenance_base = {
            "source": self.source,
            "extraction_method": "code_analysis",
        }

        # Extract from repositories
        for repo in code_analysis.get("repositories", []):
            repo_name = repo.get("repo_name", repo.get("name", "Unknown"))
            repo_url = repo.get("repo_url", "")

            # Repository entity
            entities.append(ExtractedEntity(
                entity_type="Repository",
                name=repo_name,
                properties={
                    "url": repo_url,
                    "language": repo.get("language"),
                    "language_ratio": repo.get("language_ratio"),
                    "total_files": repo.get("total_files"),
                    "analyzed_files": repo.get("analyzed_files"),
                    "jd_match_score": repo.get("jd_match_score", 0),
                    "contributors_count": repo.get("contributors_count", 0),
                },
                provenance={
                    **provenance_base,
                    "repo_url": repo_url,
                },
            ))

            # Tech stack entities with demonstrated_by relation
            for tech in repo.get("tech_stack", []):
                # Create skill entity if not exists
                skill_exists = any(e.name == tech and e.entity_type == "Skill" for e in entities)
                if not skill_exists:
                    entities.append(ExtractedEntity(
                        entity_type="Skill",
                        name=tech,
                        properties={
                            "source_type": "code",
                            "verified": True,  # Found in actual code
                        },
                        provenance={
                            **provenance_base,
                            "repo_url": repo_url,
                            "field": "tech_stack",
                        },
                    ))

                relations.append(ExtractedRelation(
                    source_name=tech,
                    source_type="Skill",
                    target_name=repo_name,
                    target_type="Repository",
                    relation_type="demonstrated_by",
                    confidence=95,  # High confidence - found in code
                ))

            # Code patterns
            for pattern in repo.get("patterns", []):
                pattern_name = f"{pattern.get('pattern_type', 'unknown')}:{pattern.get('name', 'unnamed')}"
                entities.append(ExtractedEntity(
                    entity_type="CodePattern",
                    name=pattern_name,
                    properties={
                        "pattern_type": pattern.get("pattern_type"),
                        "file_path": pattern.get("file_path"),
                        "line_start": pattern.get("line_start"),
                        "line_end": pattern.get("line_end"),
                        "code_snippet": pattern.get("code_snippet", "")[:500],  # Truncate for storage
                        "explanation": pattern.get("explanation"),
                    },
                    provenance={
                        **provenance_base,
                        "repo_url": repo_url,
                        "file_path": pattern.get("file_path"),
                    },
                ))

                relations.append(ExtractedRelation(
                    source_name=repo_name,
                    source_type="Repository",
                    target_name=pattern_name,
                    target_type="CodePattern",
                    relation_type="contains_code",
                    confidence=100,
                ))

            # Notable implementations
            for impl in repo.get("notable_implementations", []):
                impl_name = impl.get("title", "Notable Implementation")
                entities.append(ExtractedEntity(
                    entity_type="NotableImplementation",
                    name=impl_name,
                    properties={
                        "description": impl.get("description"),
                        "file_path": impl.get("file_path"),
                        "line_start": impl.get("line_start"),
                        "line_end": impl.get("line_end"),
                        "code_snippet": impl.get("code_snippet", "")[:500],
                        "why_notable": impl.get("why_notable"),
                        "question_potential": impl.get("question_potential", 0),
                    },
                    provenance={
                        **provenance_base,
                        "repo_url": repo_url,
                        "file_path": impl.get("file_path"),
                    },
                ))

                relations.append(ExtractedRelation(
                    source_name=repo_name,
                    source_type="Repository",
                    target_name=impl_name,
                    target_type="NotableImplementation",
                    relation_type="contains_code",
                    confidence=100,
                ))

            # Candidate contribution metrics
            contrib = repo.get("candidate_contribution", {})
            if contrib:
                relations.append(ExtractedRelation(
                    source_name="Candidate",
                    source_type="Candidate",
                    target_name=repo_name,
                    target_type="Repository",
                    relation_type="contributed_to",
                    confidence=100,
                    properties={
                        "total_commits": contrib.get("total_commits", 0),
                        "total_additions": contrib.get("total_additions", 0),
                        "total_deletions": contrib.get("total_deletions", 0),
                        "avg_complexity": contrib.get("avg_complexity", 0),
                    },
                ))

        # Combined tech stack (verified skills from code)
        for tech in code_analysis.get("combined_tech_stack", []):
            skill_exists = any(e.name == tech and e.entity_type == "Skill" for e in entities)
            if not skill_exists:
                entities.append(ExtractedEntity(
                    entity_type="Skill",
                    name=tech,
                    properties={
                        "source_type": "code",
                        "verified": True,
                    },
                    provenance={
                        **provenance_base,
                        "field": "combined_tech_stack",
                    },
                ))

        logger.info(f"Extracted {len(entities)} entities and {len(relations)} relations from code analysis")

        return ExtractionResult(
            entities=entities,
            relations=relations,
            metadata={
                "total_repositories": len(code_analysis.get("repositories", [])),
                "total_patterns": code_analysis.get("total_patterns", 0),
                "total_notable_implementations": code_analysis.get("total_notable_implementations", 0),
            },
        )


# ============================================
# JD Analysis Extractor
# ============================================

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


# ============================================
# Factory Functions
# ============================================

def get_candidate_extractor(source: str = "document_analysis") -> CandidateEntityExtractor:
    return CandidateEntityExtractor(source)


def get_code_extractor(source: str = "code_analysis") -> CodeEntityExtractor:
    return CodeEntityExtractor(source)


def get_jd_extractor(source: str = "jd_analysis") -> JDEntityExtractor:
    return JDEntityExtractor(source)
