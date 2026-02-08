"""
backend/app/services/code_extractor.py
Extract KG entities from code analysis results
"""
import logging
from typing import Any

from .entity_models import ExtractedEntity, ExtractedRelation, ExtractionResult

logger = logging.getLogger(__name__)


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


def get_code_extractor(source: str = "code_analysis") -> CodeEntityExtractor:
    return CodeEntityExtractor(source)
