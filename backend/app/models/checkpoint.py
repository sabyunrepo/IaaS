"""
backend/app/models/checkpoint.py
체크포인트 및 캐시 모델
"""
from datetime import datetime
from typing import Literal, TypeAlias

from pydantic import BaseModel

PipelineStep: TypeAlias = Literal[
    "enrich_input",
    "plan",
    "document_analysis",
    "code_analysis",
    "jd_analysis",
    "aggregate_analysis",
    "select_topics",
    "craft_questions",
    "review_quality",
    "finalize",
]

PIPELINE_STEPS: list[PipelineStep] = [
    "enrich_input", "plan", "document_analysis", "code_analysis",
    "jd_analysis", "aggregate_analysis", "select_topics",
    "craft_questions", "review_quality", "finalize",
]


class CheckpointMeta(BaseModel):
    job_id: str
    step: PipelineStep
    status: Literal["completed", "failed", "partial"]
    saved_at: datetime
    size_bytes: int
    storage: Literal["redis", "s3", "both"]


class CheckpointStatus(BaseModel):
    job_id: str
    steps: list[dict]
    completed_steps: list[PipelineStep]
    resume_point: PipelineStep | None = None
    total_steps: int
    completed_count: int


class RetryRequest(BaseModel):
    from_step: PipelineStep | None = None
    force_rerun: bool = False


class RetryResponse(BaseModel):
    job_id: str
    status: str
    resume_from: PipelineStep
    skipped_steps: list[PipelineStep]
    cached_steps: list[PipelineStep]


# --- LLM Cache ---

class LLMCacheEntry(BaseModel):
    model: str
    prompt_hash: str
    content: str
    usage: dict
    cached_at: datetime
    ttl_seconds: int
    hit_count: int = 0


class LLMCacheStats(BaseModel):
    total_hits: int
    total_misses: int
    hit_rate: float
    estimated_cost_saved: float
    total_tokens_saved: int
