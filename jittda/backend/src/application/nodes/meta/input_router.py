"""
InputRouter 노드 — 입력 파싱 + 소스 라우팅 + JD 자동 파싱 (Phase 0).

Job의 input_data를 파싱하여 분석에 필요한 정보를 추출하고
적절한 분석 경로를 결정한다.
jd_description이 있고 jd_languages가 비어있으면 LLM으로 자동 추출한다.
"""
from __future__ import annotations

import logging
from typing import Any

from application.states.meta_state import MetaState
from infrastructure.persistence.repository import JobRepository

logger = logging.getLogger(__name__)


async def _parse_jd_description(jd_description: str) -> dict[str, list[str]]:
    """JD 설명 텍스트에서 언어/기술 스택을 LLM으로 추출한다.

    Returns:
        {"languages": [...], "tech_stack": [...]}
    """
    try:
        from infrastructure.llm.instructor_client import InstructorClient

        client = InstructorClient()
        result = await client.create_completion(
            model=None,  # 기본 모델 사용
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a job description analyzer. Extract programming languages "
                        "and tech stack from the given job description. "
                        "Return ONLY a JSON object with two fields:\n"
                        '- "languages": list of programming language names (lowercase, e.g. "python", "typescript")\n'
                        '- "tech_stack": list of frameworks/tools/libraries (lowercase, e.g. "react", "fastapi", "postgresql")\n'
                        "Be precise. Only include technologies explicitly mentioned or strongly implied."
                    ),
                },
                {"role": "user", "content": jd_description},
            ],
            response_format={"type": "json_object"},
        )

        import json

        parsed = json.loads(result) if isinstance(result, str) else result
        return {
            "languages": parsed.get("languages", []),
            "tech_stack": parsed.get("tech_stack", []),
        }
    except Exception as e:
        logger.warning("JD description LLM parsing failed: %s", e)
        return {"languages": [], "tech_stack": []}


async def input_router_node(state: MetaState) -> dict[str, Any]:
    """입력 데이터를 파싱하고 분석 경로를 결정한다."""
    job_id = state["job_id"]

    try:
        # DB에서 input_data 로드
        repo = JobRepository()
        job = await repo.get(job_id)

        if not job:
            return {
                "status": "failed",
                "errors": state.get("errors", []) + [f"Job {job_id} not found"],
            }

        input_data = job.get("input_data", {})

        # JD 자동 파싱: jd_description 있고 jd_languages 비어있을 때
        jd_description = input_data.get("jd_description", "")
        jd_languages = input_data.get("jd_languages", [])
        jd_tech_stack = input_data.get("jd_tech_stack", [])

        if jd_description and not jd_languages:
            logger.info("JD description detected without languages, running LLM parsing for job %s", job_id)
            parsed = await _parse_jd_description(jd_description)
            if parsed["languages"]:
                input_data["jd_languages"] = parsed["languages"]
                logger.info("Auto-parsed JD languages: %s", parsed["languages"])
            if parsed["tech_stack"] and not jd_tech_stack:
                input_data["jd_tech_stack"] = parsed["tech_stack"]
                logger.info("Auto-parsed JD tech stack: %s", parsed["tech_stack"])
            # DB에 업데이트된 input_data 저장
            await repo.update_input_data(job_id, input_data)

        # 상태 업데이트
        await repo.update_status(job_id, "collecting", progress=0.05)

        return {
            "input_data_ref": job_id,
            "status": "collecting",
            "current_phase": "plan_generator",
        }
    except Exception as e:
        logger.error("input_router_node failed for job %s: %s", job_id, e)
        return {
            "status": "failed",
            "errors": state.get("errors", []) + [f"input_router: {e}"],
        }
