"""
CLAVE Worker (W4) — 코드 스타일로메트리 분석.

LLM 기반: 후보자의 코딩 스타일 지문을 추출하여 일관성을 평가.
전용 인프라 어댑터 없음 → InstructorClient로 구현.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from application.states.forensic_state import ForensicState
from infrastructure.llm.instructor_client import InstructorClient


class StyleFingerprint(BaseModel):
    """코딩 스타일 지문."""

    naming_convention: str  # camelCase | snake_case | PascalCase | mixed
    indentation_style: str  # spaces_2 | spaces_4 | tabs | mixed
    comment_density: float = Field(ge=0.0, le=1.0)
    avg_function_length: float = Field(ge=0.0)
    error_handling_pattern: str  # try-catch | if-error | none | mixed
    consistency_score: float = Field(ge=0.0, le=1.0)
    distinctive_patterns: list[str]


CLAVE_SYSTEM_PROMPT = """You are a code stylometry analyzer. Extract the coding style fingerprint from code samples.

Analyze:
1. Naming conventions (camelCase, snake_case, PascalCase, mixed)
2. Indentation style (spaces_2, spaces_4, tabs, mixed)
3. Comment density (ratio of comment lines to total)
4. Average function length in lines
5. Error handling patterns (try-catch, if-error, none, mixed)
6. Overall style consistency (0.0 = very inconsistent, 1.0 = perfectly consistent)
7. Distinctive patterns unique to this author

A consistency_score below 0.5 may indicate multiple authors or AI-assisted code."""


async def clave_worker(state: ForensicState) -> dict[str, Any]:
    """코드 스타일로메트리 분석을 수행한다."""
    cleaned_diffs = state.get("cleaned_diffs", [])

    if not cleaned_diffs:
        return {"clave_fingerprint": None}

    # 코드 샘플 수집
    code_samples = []
    for diff in cleaned_diffs[:15]:
        bodies = diff.get("function_bodies", [])
        if bodies:
            code_samples.append(
                f"# File: {diff['file_path']} ({diff.get('language', 'unknown')})\n"
                + "\n\n".join(bodies[:5])
            )

    if not code_samples:
        return {"clave_fingerprint": None}

    import os

    client = InstructorClient(
        api_key=os.environ.get("LLM_API_KEY", ""),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.moonshot.cn/v1"),
    )

    sample_text = "\n---\n".join(s[:3000] for s in code_samples)

    fingerprint = await client.create(
        response_model=StyleFingerprint,
        messages=[
            {"role": "system", "content": CLAVE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze the coding style:\n\n{sample_text}"},
        ],
        temperature=0.3,
    )

    return {"clave_fingerprint": fingerprint.model_dump()}
