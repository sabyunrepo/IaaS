"""
backend/app/services/entity_models.py
Pydantic models for Knowledge Graph entity extraction
"""
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ExtractedEntity(BaseModel):
    """Base model for extracted KG entities."""
    entity_type: str
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)

    @field_validator("entity_type", "name", mode="before")
    @classmethod
    def ensure_string(cls, v):
        """Ensure string fields are not None."""
        if v is None:
            return "Unknown"
        return str(v)


class ExtractedRelation(BaseModel):
    """Model for extracted KG relations."""
    source_name: str
    source_type: str
    target_name: str
    target_type: str
    relation_type: str
    confidence: int = 100  # 0-100 scale
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("source_name", "source_type", "target_name", "target_type", "relation_type", mode="before")
    @classmethod
    def ensure_string(cls, v):
        """Ensure string fields are not None."""
        if v is None:
            return "Unknown"
        return str(v)


class ExtractionResult(BaseModel):
    """Result of entity extraction from a document or analysis."""
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relations: list[ExtractedRelation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
