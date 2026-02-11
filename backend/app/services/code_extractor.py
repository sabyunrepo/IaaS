"""
backend/app/services/code_extractor.py
Extract KG entities from code analysis results

JIT-25: 호환성 개선 — tech_stack/patterns 중첩 접근 + AST 청크 메타데이터 지원
"""
import logging
from typing import Any

from .entity_models import ExtractedEntity, ExtractedRelation, ExtractionResult

logger = logging.getLogger(__name__)


def _repo_field(repo: dict, field: str, default=None):
    """repo dict에서 직접 또는 analysis 내부에서 필드 조회 (호환성)

    JIT-25: analyze_code()(old)와 analyze_single_repo()(HYBRID) 모두 대응.
    old: repo["analysis"]["tech_stack"]
    HYBRID: repo["analysis"]["tech_stack"] (synthesis_result)
    일부 데이터: repo["tech_stack"] (직접)
    """
    val = repo.get(field)
    if val:
        return val
    analysis = repo.get("analysis")
    if isinstance(analysis, dict):
        val = analysis.get(field)
        if val:
            return val
    return default if default is not None else []


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

            # Repository entity — JIT-25: hybrid_metadata 포함
            hybrid_meta = repo.get("hybrid_metadata", {})
            repo_properties = {
                "url": repo_url,
                "language": repo.get("language"),
                "language_ratio": repo.get("language_ratio"),
                "total_files": repo.get("total_files"),
                "analyzed_files": repo.get("analyzed_files"),
                "jd_match_score": repo.get("jd_match_score", 0),
                "contributors_count": repo.get("contributors_count", 0),
            }
            # JIT-25: AST 파이프라인 메타데이터 (있을 때만)
            if hybrid_meta:
                repo_properties["pipeline_type"] = "hybrid" if hybrid_meta.get("use_ast_pipeline") else "legacy"
                repo_properties["ranked_chunks_count"] = hybrid_meta.get("ranked_chunks_count", 0)

            entities.append(ExtractedEntity(
                entity_type="Repository",
                name=repo_name,
                properties=repo_properties,
                provenance={
                    **provenance_base,
                    "repo_url": repo_url,
                },
            ))

            # Tech stack entities — JIT-25: 직접 + analysis 내부 모두 탐색
            tech_stack = _repo_field(repo, "tech_stack", [])
            for tech in tech_stack:
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
                    confidence=95,
                ))

            # Code patterns — JIT-25: 직접 + analysis 내부 모두 탐색
            patterns = _repo_field(repo, "patterns", [])
            for pattern in patterns:
                # HYBRID synthesis는 패턴을 문자열 리스트로 반환할 수 있음
                if isinstance(pattern, str):
                    pattern_name = pattern
                    entities.append(ExtractedEntity(
                        entity_type="CodePattern",
                        name=pattern_name,
                        properties={
                            "pattern_type": "detected",
                            "source": "synthesis",
                        },
                        provenance={
                            **provenance_base,
                            "repo_url": repo_url,
                        },
                    ))
                elif isinstance(pattern, dict):
                    pattern_name = f"{pattern.get('pattern_type', 'unknown')}:{pattern.get('name', 'unnamed')}"
                    entities.append(ExtractedEntity(
                        entity_type="CodePattern",
                        name=pattern_name,
                        properties={
                            "pattern_type": pattern.get("pattern_type"),
                            "file_path": pattern.get("file_path"),
                            "line_start": pattern.get("line_start"),
                            "line_end": pattern.get("line_end"),
                            "code_snippet": pattern.get("code_snippet", "")[:500],
                            "explanation": pattern.get("explanation"),
                        },
                        provenance={
                            **provenance_base,
                            "repo_url": repo_url,
                            "file_path": pattern.get("file_path"),
                        },
                    ))
                else:
                    continue

                relations.append(ExtractedRelation(
                    source_name=repo_name,
                    source_type="Repository",
                    target_name=pattern_name,
                    target_type="CodePattern",
                    relation_type="contains_code",
                    confidence=100,
                ))

            # Notable implementations — JIT-25: 직접 + analysis 내부 모두 탐색
            notables = _repo_field(repo, "notable_implementations", [])
            for impl in notables:
                if isinstance(impl, str):
                    impl_name = impl
                    impl_props = {"description": impl, "source": "synthesis"}
                elif isinstance(impl, dict):
                    impl_name = impl.get("title", "Notable Implementation")
                    impl_props = {
                        "description": impl.get("description"),
                        "file_path": impl.get("file_path"),
                        "line_start": impl.get("line_start"),
                        "line_end": impl.get("line_end"),
                        "code_snippet": impl.get("code_snippet", "")[:500],
                        "why_notable": impl.get("why_notable"),
                        "question_potential": impl.get("question_potential", 0),
                    }
                else:
                    continue

                entities.append(ExtractedEntity(
                    entity_type="NotableImplementation",
                    name=impl_name,
                    properties=impl_props,
                    provenance={
                        **provenance_base,
                        "repo_url": repo_url,
                        "file_path": impl_props.get("file_path") if isinstance(impl_props, dict) else None,
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
            if not contrib:
                # JIT-25 호환: HYBRID 경로에서는 driller stats가 다른 위치
                contrib = {
                    "total_commits": repo.get("candidate_commits", 0),
                    "total_additions": repo.get("candidate_additions", 0),
                    "avg_complexity": repo.get("avg_complexity", 0),
                }
            if contrib and (contrib.get("total_commits", 0) > 0 or contrib.get("total_additions", 0) > 0):
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

            # Candidate identification metadata (JIT-23/25)
            candidate_id = repo.get("candidate_identification", {})
            if candidate_id and candidate_id.get("identified_username"):
                relations.append(ExtractedRelation(
                    source_name="Candidate",
                    source_type="Candidate",
                    target_name=repo_name,
                    target_type="Repository",
                    relation_type="identified_as",
                    confidence=candidate_id.get("confidence", 50),
                    properties={
                        "username": candidate_id.get("identified_username"),
                        "method": candidate_id.get("method"),
                    },
                ))

            # Static analysis entities
            static = repo.get("static_analysis")
            if static:
                self._extract_static_analysis_entities(
                    static, repo_name, repo_url, entities, relations, provenance_base,
                )

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


    def _extract_static_analysis_entities(
        self,
        static: dict,
        repo_name: str,
        repo_url: str,
        entities: list[ExtractedEntity],
        relations: list[ExtractedRelation],
        provenance_base: dict,
    ) -> None:
        """정적 분석 결과 → KG 엔티티 (SecurityFinding, ComplexityHotspot, CodeMetric)"""

        # 1. 보안 취약점 → SecurityFinding 엔티티 (상위 10개)
        for finding in static.get("security_findings", [])[:10]:
            finding_name = f"{finding.get('rule_id', 'unknown')}:{finding.get('file_path', '')}"
            entities.append(ExtractedEntity(
                entity_type="SecurityFinding",
                name=finding_name,
                properties={
                    "severity": finding.get("severity"),
                    "message": finding.get("message", "")[:300],
                    "file_path": finding.get("file_path"),
                    "line": finding.get("line"),
                    "tool": finding.get("tool", "semgrep"),
                },
                provenance={
                    **provenance_base,
                    "repo_url": repo_url,
                    "extraction_method": "static_analysis",
                },
            ))
            relations.append(ExtractedRelation(
                source_name=repo_name,
                source_type="Repository",
                target_name=finding_name,
                target_type="SecurityFinding",
                relation_type="has_vulnerability",
                confidence=90,
            ))

        # 2. 복잡도 핫스팟 → ComplexityHotspot 엔티티 (CC ≥ 15)
        for func in static.get("function_metrics", []):
            cc = func.get("cyclomatic_complexity", 0)
            if cc >= 15:
                hotspot_name = f"{func.get('file_path', '')}:{func.get('function_name', '')}"
                entities.append(ExtractedEntity(
                    entity_type="ComplexityHotspot",
                    name=hotspot_name,
                    properties={
                        "cc": cc,
                        "nloc": func.get("nloc", 0),
                        "language": func.get("language", ""),
                    },
                    provenance={
                        **provenance_base,
                        "repo_url": repo_url,
                        "extraction_method": "lizard",
                    },
                ))
                relations.append(ExtractedRelation(
                    source_name=repo_name,
                    source_type="Repository",
                    target_name=hotspot_name,
                    target_type="ComplexityHotspot",
                    relation_type="has_complexity_issue",
                    confidence=95,
                ))

        # 3. 코드 메트릭 요약 → CodeMetric 엔티티
        metric_name = f"{repo_name}_metrics"
        entities.append(ExtractedEntity(
            entity_type="CodeMetric",
            name=metric_name,
            properties={
                "avg_cc": static.get("overall_avg_cc"),
                "max_cc": static.get("overall_max_cc"),
                "security_score": static.get("security_score"),
                "documentation_ratio": static.get("documentation_ratio"),
                "total_nloc": static.get("total_nloc"),
                "maintainability_index": static.get("maintainability_index"),
                "language_breakdown": static.get("language_breakdown", {}),
                "has_tests": static.get("has_tests", False),
                "test_to_code_ratio": static.get("test_to_code_ratio", 0),
            },
            provenance={
                **provenance_base,
                "repo_url": repo_url,
                "extraction_method": "static_analysis",
            },
        ))
        relations.append(ExtractedRelation(
            source_name=repo_name,
            source_type="Repository",
            target_name=metric_name,
            target_type="CodeMetric",
            relation_type="measured_by",
            confidence=100,
        ))


def get_code_extractor(source: str = "code_analysis") -> CodeEntityExtractor:
    return CodeEntityExtractor(source)
