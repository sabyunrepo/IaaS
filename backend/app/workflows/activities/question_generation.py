"""
backend/app/workflows/activities/question_generation.py
질문 생성 Activities (토픽 선정 + 개별 질문 생성)
"""
import logging

from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def select_topics(analysis: dict, enriched_input: dict) -> list[dict]:
    """
    25개 질문 토픽 선정 (5카테고리 × 5)

    선정 기준:
    1. 코드에서 발견된 주목할 만한 구현
    2. JD 요구사항과의 매칭
    3. 경험 레벨에 맞는 난이도
    """
    from app.services.cached_llm import CachedLLMService

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    experience_level = raw_input.get("experience_level", "미들")
    max_questions = raw_input.get("max_questions", 25)

    # 질문 후보 수집
    candidates = []

    # 코드 기반 후보
    code_analysis = analysis.get("code_analysis", {})
    for impl in code_analysis.get("top_question_candidates", []):
        candidates.append({
            "source": "code",
            "topic": impl.get("title", "unknown"),
            "evidence": impl,
            "score": impl.get("question_potential", 0.5),
        })

    # JD 기반 후보
    jd_analysis = analysis.get("jd_analysis", {})
    for req in jd_analysis.get("requirements", []):
        skill = req.get("skill", "") if isinstance(req, dict) else str(req)
        category = req.get("category", "우대") if isinstance(req, dict) else "우대"
        candidates.append({
            "source": "jd_match",
            "topic": skill,
            "evidence": {},
            "score": 0.7 if category == "필수" else 0.5,
        })

    activity.heartbeat(f"Selecting {max_questions} topics from {len(candidates)} candidates...")

    from app.prompts import get_prompt
    prompt = get_prompt(
        "question_generation.yaml", "select_topics",
        max_questions=max_questions,
        experience_level=experience_level,
        candidates=_format_candidates(candidates),
    )

    result = await llm.run(prompt)
    if isinstance(result, list):
        return result[:max_questions]

    # Fallback: generate placeholder topics from candidates
    topics = []
    categories = ["role_fit", "technical_depth", "execution_ownership", "communication", "risk_flags"]
    for i, cat in enumerate(categories):
        for j in range(5):
            idx = i * 5 + j
            if idx < len(candidates):
                topics.append({
                    "category": cat,
                    "topic": candidates[idx]["topic"],
                    "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"][j],
                    "source": candidates[idx]["source"],
                })
            else:
                topics.append({
                    "category": cat,
                    "topic": f"{cat}_topic_{j+1}",
                    "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"][j],
                    "source": "generated",
                })
    return topics[:max_questions]


@activity.defn
async def craft_question(
    topic: dict,
    analysis: dict,
    enriched_input: dict,
) -> dict:
    """
    단일 질문 상세 생성

    생성 내용:
    - 메인 질문 + 대체 표현
    - 예상 답변 (3레벨)
    - 평가 시나리오
    - 꼬리질문
    - 용어 설명
    """
    from app.services.cached_llm import CachedLLMService

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    language_config = raw_input.get("language_config", {})
    output_language = language_config.get("output_language", "ko")
    experience_level = raw_input.get("experience_level", "미들")

    from app.prompts import get_prompt
    prompt = get_prompt(
        "question_generation.yaml", "craft_question",
        output_language=output_language,
        experience_level=experience_level,
        topic=topic.get("topic"),
        category=topic.get("category"),
        difficulty=topic.get("difficulty"),
    )

    result = await llm.run(prompt)

    question = result if isinstance(result, dict) else {}
    question.setdefault("question_text", f"[{topic.get('topic')}] 관련 질문")
    question.setdefault("category", topic.get("category", "technical_depth"))
    question.setdefault("difficulty", topic.get("difficulty", "Medium"))
    question.setdefault("language", output_language)
    question.setdefault("topic", topic.get("topic"))

    return question


@activity.defn
async def enhance_terminology(questions: list[dict], enriched_input: dict) -> dict:
    """3c. Terminology Agent — 전문용어에 비개발자용 설명 추가"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt
    import json

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    prompt = get_prompt(
        "question_generation.yaml", "enhance_terminology",
        output_language=output_language,
        questions_json=json.dumps(questions[:25], ensure_ascii=False, default=str),
    )
    result = await llm.run(prompt)
    return result if isinstance(result, dict) else {}


@activity.defn
async def craft_evaluation_scenarios(questions: list[dict], enriched_input: dict) -> dict:
    """3d. Scenario Writer Agent — 3단계 평가 시나리오 생성"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt
    import json

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")
    experience_level = raw_input.get("experience_level", "미들")

    prompt = get_prompt(
        "question_generation.yaml", "craft_evaluation_scenarios",
        output_language=output_language,
        experience_level=experience_level,
        questions_json=json.dumps(questions[:25], ensure_ascii=False, default=str),
    )
    result = await llm.run(prompt)
    return result if isinstance(result, dict) else {}


@activity.defn
async def design_follow_ups(questions: list[dict], enriched_input: dict) -> dict:
    """3e. Follow-up Designer Agent — 후속질문 분기 설계"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt
    import json

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")
    experience_level = raw_input.get("experience_level", "미들")

    prompt = get_prompt(
        "question_generation.yaml", "design_follow_ups",
        output_language=output_language,
        experience_level=experience_level,
        questions_json=json.dumps(questions[:25], ensure_ascii=False, default=str),
    )
    result = await llm.run(prompt)
    return result if isinstance(result, dict) else {}


@activity.defn
async def generate_interviewer_notes(questions: list[dict], enriched_input: dict) -> dict:
    """3f. Interviewer Note Agent — 면접관 참고 노트"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt
    import json

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    prompt = get_prompt(
        "question_generation.yaml", "generate_interviewer_notes",
        output_language=output_language,
        questions_json=json.dumps(questions[:25], ensure_ascii=False, default=str),
    )
    result = await llm.run(prompt)
    return result if isinstance(result, dict) else {}


@activity.defn
async def generate_decision_guide(analysis: dict, enriched_input: dict) -> dict:
    """3g. Decision Guide Agent — 채용 의사결정 가이드"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt
    import json

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

    prompt = get_prompt(
        "question_generation.yaml", "generate_decision_guide",
        output_language=output_language,
        experience_level=experience_level,
        analysis_summary=analysis_summary,
        category_summary=category_summary,
    )
    result = await llm.run(prompt)
    return result if isinstance(result, dict) else {}


@activity.defn
async def revise_questions(questions: list[dict], review_feedback: dict, enriched_input: dict) -> list[dict]:
    """3h. Quality Review revision — 피드백 기반 질문 수정"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt
    import json

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    output_language = raw_input.get("language_config", {}).get("output_language", "ko")

    prompt = get_prompt(
        "question_generation.yaml", "revise_questions",
        output_language=output_language,
        questions_json=json.dumps(questions, ensure_ascii=False, default=str),
        review_feedback=json.dumps(review_feedback, ensure_ascii=False, default=str),
    )
    result = await llm.run(prompt)
    return result if isinstance(result, list) else questions


def _format_candidates(candidates: list[dict]) -> str:
    lines = []
    for i, c in enumerate(candidates[:30]):
        lines.append(f"{i+1}. [{c['source']}] {c['topic']} (score: {c['score']})")
    return "\n".join(lines)
