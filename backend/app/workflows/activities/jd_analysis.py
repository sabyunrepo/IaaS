"""
backend/app/workflows/activities/jd_analysis.py
채용공고(JD) 분석 Activity
"""
import logging

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def analyze_jd(jd_text: str) -> dict:
    """
    채용공고(JD) 분석

    1. 요구사항 추출
    2. 스킬 추출
    3. 회사 문화 추출
    """
    from app.services.cached_llm import CachedLLMService

    llm = CachedLLMService()

    prompt = (
        "Analyze the following job description and extract:\n"
        "1. job_title\n"
        "2. company_name\n"
        "3. requirements (list of {skill, category: '필수'|'우대', level})\n"
        "4. responsibilities (list of strings)\n"
        "5. company_culture (list of strings)\n"
        "6. tech_stack (list of technology names)\n\n"
        f"Job Description:\n{jd_text}"
    )

    result = await llm.run(prompt)

    if isinstance(result, dict):
        return {
            "job_title": result.get("job_title"),
            "company_name": result.get("company_name"),
            "requirements": result.get("requirements", []),
            "responsibilities": result.get("responsibilities", []),
            "company_culture": result.get("company_culture", []),
            "tech_stack": result.get("tech_stack", []),
            "skill_matches": [],
            "overall_match_score": 0,
            "gaps": [],
            "strengths": [],
        }

    return {
        "job_title": None,
        "company_name": None,
        "requirements": [],
        "responsibilities": [],
        "company_culture": [],
        "tech_stack": [],
        "skill_matches": [],
        "overall_match_score": 0,
        "gaps": [],
        "strengths": [],
    }
