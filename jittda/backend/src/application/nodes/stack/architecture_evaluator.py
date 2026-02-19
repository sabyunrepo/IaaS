"""
ArchitectureEvaluator Worker (W11) — 아키텍처 패턴 평가.

코드 구조, 디자인 패턴, 계층 분리, 의존성 관리를 분석하여
아키텍처 설계 역량을 평가한다.
"""
from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field

from application.states.stack_state import StackState
from infrastructure.llm.instructor_client import InstructorClient


class ArchitectureEvaluation(BaseModel):
    """아키텍처 평가 결과."""

    patterns_detected: list[str]  # MVC, DDD, Clean Architecture, etc.
    layer_separation: float = Field(ge=0.0, le=1.0)  # 계층 분리 점수
    dependency_management: float = Field(ge=0.0, le=1.0)  # 의존성 관리 점수
    code_organization: float = Field(ge=0.0, le=1.0)  # 코드 조직화 점수
    testing_patterns: list[str]  # unit, integration, e2e
    overall_score: float = Field(ge=0.0, le=1.0)
    strengths: list[str]
    weaknesses: list[str]


ARCHITECTURE_PROMPT = """You are a software architecture evaluator. Analyze the code structure to assess the candidate's architecture skills.

Evaluate:
1. Design patterns used (MVC, Repository, Factory, Observer, etc.)
2. Layer separation (presentation/business/data layers, DDD boundaries)
3. Dependency management (DI, interfaces, loose coupling)
4. Code organization (module structure, naming conventions, file organization)
5. Testing patterns (unit tests, integration tests, test fixtures)

Score each dimension 0.0 to 1.0 and provide an overall assessment."""


async def architecture_evaluator_worker(state: StackState) -> dict[str, Any]:
    """코드 아키텍처를 평가한다."""
    ast_analysis = state.get("ast_analysis", [])
    cleaned_diffs = state.get("cleaned_diffs", [])

    if not ast_analysis:
        return {"architecture_eval": None}

    # 파일 구조 분석
    file_paths = [a.get("file_path", "") for a in ast_analysis]
    class_info = []
    for a in ast_analysis[:15]:
        classes = a.get("classes", [])
        imports = a.get("imports", [])
        if classes or len(imports) > 3:
            class_info.append({
                "file": a.get("file_path", ""),
                "classes": [c.get("name", "") for c in classes],
                "imports": imports[:20],
                "functions": len(a.get("functions", [])),
            })

    client = InstructorClient(
        api_key=os.environ.get("LLM_API_KEY", ""),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.moonshot.cn/v1"),
    )

    context = (
        f"File structure ({len(file_paths)} files):\n{file_paths[:30]}\n\n"
        f"Class and import analysis:\n{class_info}\n\n"
        f"Code samples:\n"
    )
    for diff in cleaned_diffs[:5]:
        bodies = diff.get("function_bodies", [])
        if bodies:
            context += f"# {diff.get('file_path', '')}\n{bodies[0][:1500]}\n---\n"

    result = await client.create(
        response_model=ArchitectureEvaluation,
        messages=[
            {"role": "system", "content": ARCHITECTURE_PROMPT},
            {"role": "user", "content": context},
        ],
        temperature=0.3,
    )

    return {"architecture_eval": result.model_dump()}
