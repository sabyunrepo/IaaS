"""
APIDepthAnalyzer Worker (W10) — API 사용 깊이 분석.

AST에서 추출한 함수 호출 패턴을 분석하여 라이브러리/프레임워크 API의
사용 깊이(표면적 사용 vs 심층 활용)를 평가한다.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel, Field

from application.states.stack_state import StackState
from infrastructure.llm.instructor_client import InstructorClient

logger = logging.getLogger(__name__)


class APIDepthScore(BaseModel):
    """개별 API 사용 깊이 점수."""

    api_name: str
    depth_level: str  # surface | intermediate | deep | expert
    usage_count: int = Field(ge=0)
    advanced_features_used: list[str]
    depth_score: float = Field(ge=0.0, le=1.0)


class APIDepthResult(BaseModel):
    """API 깊이 분석 결과."""

    api_scores: list[APIDepthScore]
    avg_depth_score: float = Field(ge=0.0, le=1.0)


API_DEPTH_PROMPT = """You are an API usage depth analyzer. Examine the code's import statements and function usage to assess how deeply the candidate uses each library/framework API.

Depth levels:
- surface: Only uses basic, commonly known features
- intermediate: Uses moderately advanced features, understands configuration
- deep: Uses advanced APIs, custom extensions, internal mechanisms
- expert: Demonstrates framework internals knowledge, contributes patterns

Return a depth_score (0.0 = surface only, 1.0 = expert-level usage)."""


async def api_depth_worker(state: StackState) -> dict[str, Any]:
    """API 사용 깊이를 분석한다."""
    ast_analysis = state.get("ast_analysis", [])
    cleaned_diffs = state.get("cleaned_diffs", [])

    if not ast_analysis:
        return {"api_depth_scores": []}

    # import + 함수 정보 수집
    import_info = []
    for analysis in ast_analysis[:10]:
        imports = analysis.get("imports", [])
        functions = analysis.get("functions", [])
        if imports:
            import_info.append({
                "file": analysis.get("file_path", ""),
                "imports": imports,
                "function_names": [f.get("name", "") for f in functions[:10]],
            })

    if not import_info:
        return {"api_depth_scores": []}

    # 코드 샘플 추가
    code_samples = []
    for diff in cleaned_diffs[:5]:
        bodies = diff.get("function_bodies", [])
        if bodies:
            code_samples.append(f"# {diff.get('file_path', '')}\n" + "\n".join(bodies[:3]))

    client = InstructorClient(
        api_key=os.environ.get("LLM_API_KEY", ""),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.moonshot.cn/v1"),
    )

    context = f"Import analysis:\n{import_info}\n\nCode samples:\n" + "\n---\n".join(
        s[:2000] for s in code_samples
    )

    try:
        result = await client.create(
            response_model=APIDepthResult,
            messages=[
                {"role": "system", "content": API_DEPTH_PROMPT},
                {"role": "user", "content": context},
            ],
            temperature=0.3,
        )
        return {"api_depth_scores": [s.model_dump() for s in result.api_scores]}
    except Exception as e:
        logger.error("api_depth_worker failed: %s", e)
        return {"api_depth_scores": []}
