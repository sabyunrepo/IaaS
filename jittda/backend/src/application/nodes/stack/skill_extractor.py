"""
SkillExtractor Worker (W9) — 기술 스택 추출.

AST 분석 결과에서 사용된 라이브러리, 프레임워크, 패턴을 추출하고
JD 요구사항과 매칭하여 숙련도를 평가한다.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel, Field

from application.states.stack_state import StackState
from infrastructure.llm.instructor_client import InstructorClient

logger = logging.getLogger(__name__)


class ExtractedSkill(BaseModel):
    """추출된 개별 스킬."""

    skill_name: str
    proficiency: str  # beginner | intermediate | advanced | expert
    evidence_count: int = Field(ge=0)
    evidence_sources: list[str]
    confidence: str  # high | medium | low


class SkillExtractionResult(BaseModel):
    """스킬 추출 결과."""

    skills: list[ExtractedSkill]
    primary_language: str
    secondary_languages: list[str]
    frameworks: list[str]


SKILL_EXTRACTION_PROMPT = """You are a technical skill assessor. Analyze the AST analysis results and code imports to extract the candidate's technical skills.

For each skill:
- skill_name: The technology/framework/language name
- proficiency: Based on usage depth and complexity (beginner/intermediate/advanced/expert)
- evidence_count: How many files/functions use this skill
- evidence_sources: File paths where this skill is demonstrated
- confidence: Your assessment confidence (high/medium/low)

Also identify:
- primary_language: The most used programming language
- secondary_languages: Other languages used
- frameworks: Frameworks and libraries detected from imports"""


async def skill_extractor_worker(state: StackState) -> dict[str, Any]:
    """AST 결과에서 기술 스택을 추출한다."""
    ast_analysis = state.get("ast_analysis", [])
    jd_tech_stack = state.get("jd_tech_stack", [])

    if not ast_analysis:
        return {"skill_extraction": None}

    # import 정보와 언어 통계 준비
    all_imports: list[str] = []
    lang_counts: dict[str, int] = {}

    for analysis in ast_analysis:
        lang = analysis.get("language", "")
        lang_counts[lang] = lang_counts.get(lang, 0) + 1
        all_imports.extend(analysis.get("imports", []))

    unique_imports = sorted(set(all_imports))

    # LLM으로 스킬 추출
    client = InstructorClient(
        api_key=os.environ.get("LLM_API_KEY", ""),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.moonshot.cn/v1"),
    )

    context = (
        f"Languages used: {lang_counts}\n"
        f"Total files analyzed: {len(ast_analysis)}\n"
        f"Imports found: {unique_imports[:100]}\n"
        f"JD required tech stack: {jd_tech_stack}\n\n"
        f"Sample AST analysis (first 5 files):\n"
    )
    for a in ast_analysis[:5]:
        context += (
            f"- {a.get('file_path', '')}: "
            f"{a.get('total_functions', 0)} functions, "
            f"{a.get('total_classes', 0)} classes\n"
        )

    try:
        result = await client.create(
            response_model=SkillExtractionResult,
            messages=[
                {"role": "system", "content": SKILL_EXTRACTION_PROMPT},
                {"role": "user", "content": context},
            ],
            temperature=0.3,
        )
        return {"skill_extraction": result.model_dump()}
    except Exception as e:
        logger.error("skill_extractor_worker failed: %s", e)
        return {"skill_extraction": None}
