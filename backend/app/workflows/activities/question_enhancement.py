"""
backend/app/workflows/activities/question_enhancement.py
질문 Enhancement Activities — 용어설명, 평가시나리오, 꼬리질문, 면접관노트, 의사결정가이드, 수정

Extracted from question_generation.py for SRP compliance.
"""
import json
import logging

from temporalio import activity

from app.core.observability import observe_activity
from app.workflows.utils import run_llm_with_prompt_config_heartbeat

logger = logging.getLogger(__name__)


@activity.defn
@observe_activity(name="enhance_terminology", phase="question_generation")
async def enhance_terminology(questions: list[dict], enriched_input: dict) -> dict:
    """3c. Terminology Agent — 전문용어에 비개발자용 설명 추가"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt_with_config

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    prompt_config = get_prompt_with_config(
        "question_generation.yaml", "enhance_terminology",
        output_language=output_language,
        questions_json=json.dumps(questions[:25], ensure_ascii=False, default=str),
    )
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)
    from app.services.cached_llm import validate_llm_output
    validated = validate_llm_output(result, activity_name="enhance_terminology")

    # 용어 설명 커버리지 검증 — plain_explanation 누락 감지
    if isinstance(validated, dict):
        total_terms = 0
        missing_explanation = 0
        for q_key, q_data in validated.items():
            terms = q_data if isinstance(q_data, list) else q_data.get("terminology", []) if isinstance(q_data, dict) else []
            for term in terms:
                if isinstance(term, dict):
                    total_terms += 1
                    explanation = term.get("plain_explanation", "") or term.get("explanation", "")
                    if not explanation or len(str(explanation).strip()) < 3:
                        missing_explanation += 1
        if total_terms > 0:
            coverage = round((total_terms - missing_explanation) / total_terms * 100, 1)
            logger.info(f"enhance_terminology: {total_terms} terms, {coverage}% have explanations")
            if missing_explanation > 0:
                logger.warning(f"enhance_terminology: {missing_explanation}/{total_terms} terms missing plain_explanation")

    return validated


@activity.defn
@observe_activity(name="craft_evaluation_scenarios", phase="question_generation")
async def craft_evaluation_scenarios(questions: list[dict], enriched_input: dict) -> dict:
    """3d. Scenario Writer Agent — 3단계 평가 시나리오 생성"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt_with_config

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")
    experience_level = raw_input.get("experience_level", "미들")

    prompt_config = get_prompt_with_config(
        "question_generation.yaml", "craft_evaluation_scenarios",
        output_language=output_language,
        experience_level=experience_level,
        questions_json=json.dumps(questions[:25], ensure_ascii=False, default=str),
    )
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)
    from app.services.cached_llm import validate_llm_output
    validated = validate_llm_output(result, activity_name="craft_evaluation_scenarios")

    # 3단계 시나리오 구조 검증 — expert/mid_level/low_level 존재 확인
    EXPECTED_LEVELS = {"expert", "mid_level", "low_level"}
    if isinstance(validated, dict):
        total_questions = 0
        incomplete_questions = 0
        for q_key, q_data in validated.items():
            if not isinstance(q_data, dict):
                continue
            total_questions += 1
            present_levels = set(q_data.keys()) & EXPECTED_LEVELS
            if present_levels != EXPECTED_LEVELS:
                incomplete_questions += 1
                missing = EXPECTED_LEVELS - present_levels
                logger.warning(f"craft_evaluation_scenarios: {q_key} missing levels: {missing}")
        if total_questions > 0:
            coverage = round((total_questions - incomplete_questions) / total_questions * 100, 1)
            logger.info(f"craft_evaluation_scenarios: {total_questions} questions, {coverage}% have all 3 levels")

    return validated


@activity.defn
@observe_activity(name="design_follow_ups", phase="question_generation")
async def design_follow_ups(questions: list[dict], enriched_input: dict) -> dict:
    """3e. Follow-up Designer Agent — 후속질문 분기 설계"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt_with_config

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")
    experience_level = raw_input.get("experience_level", "미들")

    prompt_config = get_prompt_with_config(
        "question_generation.yaml", "design_follow_ups",
        output_language=output_language,
        experience_level=experience_level,
        questions_json=json.dumps(questions[:25], ensure_ascii=False, default=str),
    )
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)
    from app.services.cached_llm import validate_llm_output
    return validate_llm_output(result, activity_name="design_follow_ups")


@activity.defn
@observe_activity(name="generate_interviewer_notes", phase="question_generation")
async def generate_interviewer_notes(questions: list[dict], enriched_input: dict) -> dict:
    """3f. Interviewer Note Agent — 면접관 참고 노트"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt_with_config

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    prompt_config = get_prompt_with_config(
        "question_generation.yaml", "generate_interviewer_notes",
        output_language=output_language,
        questions_json=json.dumps(questions[:25], ensure_ascii=False, default=str),
    )
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)
    from app.services.cached_llm import validate_llm_output
    return validate_llm_output(result, activity_name="generate_interviewer_notes")


@activity.defn
@observe_activity(name="generate_decision_guide", phase="question_generation")
async def generate_decision_guide(analysis: dict, enriched_input: dict) -> dict:
    """3g. Decision Guide Agent — 채용 의사결정 가이드"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt_with_config

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")
    experience_level = raw_input.get("experience_level", "미들")

    # Summarize analysis for the prompt
    analysis_summary = json.dumps({
        k: v.get("summary", str(v)[:500]) if isinstance(v, dict) else str(v)[:500]
        for k, v in analysis.items()
    }, ensure_ascii=False, default=str)

    categories = ["role_fit", "technical_depth", "execution_ownership", "communication", "risk_flags"]
    category_summary = json.dumps(categories, ensure_ascii=False)

    prompt_config = get_prompt_with_config(
        "question_generation.yaml", "generate_decision_guide",
        output_language=output_language,
        experience_level=experience_level,
        analysis_summary=analysis_summary,
        category_summary=category_summary,
    )
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)
    from app.services.cached_llm import validate_llm_output
    return validate_llm_output(result, activity_name="generate_decision_guide")


@activity.defn
@observe_activity(name="revise_questions", phase="question_generation")
async def revise_questions(questions: list[dict], review_feedback: dict, enriched_input: dict) -> list[dict]:
    """3h. Quality Review revision — 피드백 기반 질문 수정"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt_with_config

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    prompt_config = get_prompt_with_config(
        "question_generation.yaml", "revise_questions",
        output_language=output_language,
        questions_json=json.dumps(questions, ensure_ascii=False, default=str),
        review_feedback=json.dumps(review_feedback, ensure_ascii=False, default=str),
    )
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)
    return result if isinstance(result, list) else questions
