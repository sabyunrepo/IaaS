"""
backend/app/services/entity_extractors.py
Barrel re-export for backwards compatibility.

Individual extractors are in:
- entity_models.py: Pydantic base models
- candidate_extractor.py: CandidateEntityExtractor
- code_extractor.py: CodeEntityExtractor
- jd_extractor.py: JDEntityExtractor
"""
from .entity_models import ExtractedEntity, ExtractedRelation, ExtractionResult
from .candidate_extractor import CandidateEntityExtractor, get_candidate_extractor
from .code_extractor import CodeEntityExtractor, get_code_extractor
from .jd_extractor import JDEntityExtractor, get_jd_extractor

__all__ = [
    "ExtractedEntity",
    "ExtractedRelation",
    "ExtractionResult",
    "CandidateEntityExtractor",
    "get_candidate_extractor",
    "CodeEntityExtractor",
    "get_code_extractor",
    "JDEntityExtractor",
    "get_jd_extractor",
]
