"""
backend/app/workflows/activities/question_generation.py
질문 생성 Activities (토픽 선정 + 개별 질문 생성)
"""
import logging
import uuid

from temporalio import activity

from app.core.observability import observe_activity
from app.services.activity_logger import ActivityLogger
from app.workflows.utils import run_llm_with_heartbeat

logger = logging.getLogger(__name__)

# ── 경험 레벨별 퍼센트 기반 카테고리 배분 ──
# 각 레벨에서 중요한 질문 유형에 더 높은 비율 할당
TOTAL_QUESTIONS = 20

CATEGORY_DISTRIBUTION: dict[str, dict[str, dict]] = {
    # 신입: 기초 기술력 + 성장 가능성 + 커뮤니케이션 중심
    "신입": {
        "role_fit":             {"count": 6, "difficulty": ["Easy", "Easy", "Easy", "Medium", "Medium", "Hard"]},
        "technical_depth":      {"count": 5, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"]},
        "execution_ownership":  {"count": 3, "difficulty": ["Easy", "Medium", "Hard"]},
        "communication":        {"count": 4, "difficulty": ["Easy", "Easy", "Medium", "Hard"]},
        "risk_flags":           {"count": 2, "difficulty": ["Easy", "Medium"]},
    },
    # 주니어: 성장 가능성 + 기초 기술력 중심
    "주니어": {
        "role_fit":             {"count": 6, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Medium", "Hard"]},
        "technical_depth":      {"count": 5, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"]},
        "execution_ownership":  {"count": 3, "difficulty": ["Easy", "Medium", "Hard"]},
        "communication":        {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
        "risk_flags":           {"count": 2, "difficulty": ["Easy", "Medium"]},
    },
    # 미들: 균형 잡힌 배분
    "미들": {
        "role_fit":             {"count": 5, "difficulty": ["Easy", "Easy", "Medium", "Medium", "Hard"]},
        "technical_depth":      {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
        "execution_ownership":  {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
        "communication":        {"count": 4, "difficulty": ["Easy", "Medium", "Medium", "Hard"]},
        "risk_flags":           {"count": 3, "difficulty": ["Easy", "Medium", "Hard"]},
    },
    # 시니어: 실행력 + 리스크 + 기술 깊이 중심
    "시니어": {
        "role_fit":             {"count": 3, "difficulty": ["Medium", "Medium", "Hard"]},
        "technical_depth":      {"count": 4, "difficulty": ["Medium", "Medium", "Hard", "Hard"]},
        "execution_ownership":  {"count": 5, "difficulty": ["Easy", "Medium", "Medium", "Hard", "Hard"]},
        "communication":        {"count": 4, "difficulty": ["Medium", "Medium", "Hard", "Hard"]},
        "risk_flags":           {"count": 4, "difficulty": ["Easy", "Medium", "Hard", "Hard"]},
    },
    # CTO/VP: 리더십 + 전략적 실행력 + 리스크 관리 중심
    "CTO/VP": {
        "role_fit":             {"count": 3, "difficulty": ["Medium", "Hard", "Hard"]},
        "technical_depth":      {"count": 3, "difficulty": ["Medium", "Hard", "Hard"]},
        "execution_ownership":  {"count": 5, "difficulty": ["Medium", "Medium", "Hard", "Hard", "Hard"]},
        "communication":        {"count": 4, "difficulty": ["Medium", "Medium", "Hard", "Hard"]},
        "risk_flags":           {"count": 5, "difficulty": ["Medium", "Medium", "Hard", "Hard", "Hard"]},
    },
}


def _get_distribution(experience_level: str) -> dict[str, dict]:
    """경험 레벨에 맞는 카테고리 배분 반환 (fallback: 미들)"""
    return CATEGORY_DISTRIBUTION.get(experience_level, CATEGORY_DISTRIBUTION["미들"])


def _format_distribution_for_prompt(dist: dict[str, dict]) -> tuple[str, str]:
    """프롬프트용 카테고리 배분 + 난이도 배분 텍스트 생성"""
    cat_lines = []
    diff_lines = []
    for cat, info in dist.items():
        count = info["count"]
        pct = round(count / TOTAL_QUESTIONS * 100)
        cat_desc = {
            "role_fit": "Culture fit, motivation, career goals, growth potential",
            "technical_depth": "Technical skills, problem-solving, architecture",
            "execution_ownership": "Project delivery, ownership, impact, leadership",
            "communication": "Collaboration, explanation ability, conflict resolution",
            "risk_flags": "Gaps, concerns, areas needing clarification",
        }
        cat_lines.append(f"- **{cat}** ({pct}%): {count} topics — {cat_desc.get(cat, '')}")

        # 난이도 카운트
        from collections import Counter
        diff_count = Counter(info["difficulty"])
        diff_str = ", ".join(f"{d}:{c}" for d, c in sorted(diff_count.items(), key=lambda x: ["Easy", "Medium", "Hard"].index(x[0])))
        diff_lines.append(f"- **{cat}** ({count} topics): {diff_str}")

    return "\n      ".join(cat_lines), "\n      ".join(diff_lines)


@activity.defn
@observe_activity(name="select_topics", phase="question_generation")
async def select_topics(analysis: dict, enriched_input: dict, job_id: str | None = None) -> list[dict]:
    """
    20개 질문 토픽 선정 — 경험 레벨별 퍼센트 기반 카테고리 배분

    선정 기준:
    1. Knowledge Graph 기반 후보 (skill_depth, gap_probe, conflict_probe, implementation_review)
    2. 코드에서 발견된 주목할 만한 구현
    3. JD 요구사항과의 매칭
    4. 경험 레벨에 맞는 카테고리 비율 + 난이도
    """
    from app.services.cached_llm import CachedLLMService

    # Initialize activity logger
    alog = ActivityLogger(job_id, "select_topics", "generating") if job_id else None

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    experience_level = raw_input.get("experience_level", "미들")
    max_questions = TOTAL_QUESTIONS  # 고정 20개 (퍼센트 기반)
    dist = _get_distribution(experience_level)

    if alog:
        await alog.start("Selecting question topics", {
            "experience_level": experience_level,
            "max_questions": max_questions,
            "distribution": {cat: info["count"] for cat, info in dist.items()},
        })

    # 질문 후보 수집
    candidates = []

    # Knowledge Graph 기반 후보 (highest priority)
    if job_id:
        activity.heartbeat("Fetching KG-based question candidates...")
        try:
            from app.services.graph_queries import get_interview_graph_queries
            queries = get_interview_graph_queries(job_id)
            kg_candidates = await queries.get_top_question_candidates(
                limit=30,
                balance_categories=True,
            )

            for kgc in kg_candidates:
                # Map KG category to interview category
                category_map = {
                    "skill_depth": "technical_depth",
                    "gap_probe": "role_fit",
                    "conflict_probe": "risk_flags",
                    "implementation_review": "execution_ownership",
                    "partial_match_probe": "technical_depth",
                }

                # KG 후보에 가중치 부스트 적용 (evidence-backed = higher priority)
                kg_boost = 0.15  # KG evidence backing bonus
                base_score = kgc.priority / 100  # Normalize to 0-1
                boosted_score = min(1.0, base_score + kg_boost)

                candidates.append({
                    "source": f"kg_{kgc.category}",
                    "topic": kgc.topic,
                    "evidence": {
                        "evidence_chain": kgc.evidence_chain,
                        "code_reference": kgc.code_reference,
                        "recommended_probe": kgc.recommended_probe,
                    },
                    "score": boosted_score,
                    "kg_category": kgc.category,
                    "interview_category": category_map.get(kgc.category, "technical_depth"),
                })

            logger.info(f"[{job_id}] Added {len(kg_candidates)} KG-based candidates")
        except Exception as e:
            logger.warning(f"[{job_id}] KG query failed (using fallback): {e}")

    # 코드 기반 후보
    code_analysis = analysis.get("code_analysis", {})
    for impl in code_analysis.get("top_question_candidates", []):
        # Skip if already added from KG
        topic = impl.get("title", "unknown")
        if any(c["topic"] == topic for c in candidates):
            continue
        candidates.append({
            "source": "code",
            "topic": topic,
            "evidence": impl,
            "score": impl.get("question_potential", 0.5),
        })

    # JD 기반 후보
    jd_analysis = analysis.get("jd_analysis", {})
    for req in jd_analysis.get("requirements", []):
        skill = req.get("skill", "") if isinstance(req, dict) else str(req)
        category = req.get("category", "우대") if isinstance(req, dict) else "우대"
        # Skip if already added from KG
        if any(c["topic"] == skill for c in candidates):
            continue
        candidates.append({
            "source": "jd_match",
            "topic": skill,
            "evidence": {},
            "score": 0.7 if category == "필수" else 0.5,
        })

    activity.heartbeat(f"Selecting {max_questions} topics from {len(candidates)} candidates...")

    cat_dist_text, diff_dist_text = _format_distribution_for_prompt(dist)

    from app.prompts import get_prompt
    prompt = get_prompt(
        "question_generation.yaml", "select_topics",
        max_questions=max_questions,
        experience_level=experience_level,
        candidates=_format_candidates(candidates),
        category_distribution=cat_dist_text,
        difficulty_distribution=diff_dist_text,
    )

    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_heartbeat(llm, prompt, "select_topics", interval=30.0)
    if isinstance(result, list):
        if alog:
            await alog.result("Topics selected", {
                "topics_count": len(result[:max_questions]),
                "candidates_considered": len(candidates),
            })
        return result[:TOTAL_QUESTIONS]

    # Fallback: 경험 레벨별 배분에 따라 placeholder 토픽 생성
    topics = []
    candidate_idx = 0
    for cat, info in dist.items():
        for j in range(info["count"]):
            if candidate_idx < len(candidates):
                topics.append({
                    "category": cat,
                    "topic": candidates[candidate_idx]["topic"],
                    "difficulty": info["difficulty"][j] if j < len(info["difficulty"]) else "Medium",
                    "source": candidates[candidate_idx]["source"],
                })
                candidate_idx += 1
            else:
                topics.append({
                    "category": cat,
                    "topic": f"{cat}_topic_{j+1}",
                    "difficulty": info["difficulty"][j] if j < len(info["difficulty"]) else "Medium",
                    "source": "generated",
                })
    if alog:
        await alog.result("Topics selected (fallback)", {
            "topics_count": len(topics),
            "candidates_considered": len(candidates),
        })
    return topics[:max_questions]


@activity.defn
@observe_activity(name="craft_question", phase="question_generation")
async def craft_question(
    topic: dict,
    analysis: dict,
    enriched_input: dict,
    job_id: str | None = None,
) -> dict:
    """
    단일 질문 상세 생성

    생성 내용:
    - 메인 질문 + 대체 표현
    - 예상 답변 (3레벨)
    - 평가 시나리오
    - 꼬리질문
    - 용어 설명
    - Knowledge Graph evidence chain (if available)
    """
    from app.services.cached_llm import CachedLLMService

    llm = CachedLLMService()
    raw_input = enriched_input.get("raw_input", {})
    language_config = raw_input.get("language_config", {})
    output_language = language_config.get("output_language", "ko")
    experience_level = raw_input.get("experience_level", "미들")

    # Extract KG evidence if available
    evidence_context = ""
    code_reference = None
    recommended_probe = None

    if topic.get("source", "").startswith("kg_"):
        evidence = topic.get("evidence", {})
        evidence_chain = evidence.get("evidence_chain", [])
        code_reference = evidence.get("code_reference")
        recommended_probe = evidence.get("recommended_probe")

        if evidence_chain:
            evidence_context = "\n\nEvidence chain:\n"
            for item in evidence_chain[:5]:  # Limit to 5 items
                evidence_context += f"- {item.get('type', 'Unknown')}: {item.get('name', 'N/A')}\n"

        if code_reference:
            evidence_context += f"\nCode reference: {code_reference.get('file_path', 'N/A')}\n"
            if code_reference.get('code_snippet'):
                snippet = code_reference['code_snippet'][:300]  # Truncate
                evidence_context += f"```\n{snippet}\n```\n"

    # Get additional evidence from KG if job_id is available
    if job_id and not evidence_context:
        try:
            from app.services.graph_queries import get_interview_graph_queries
            queries = get_interview_graph_queries(job_id)
            kg_evidence = await queries.get_evidence_chain_for_topic(topic.get("topic", ""))
            if kg_evidence:
                evidence_context = "\n\nKG Evidence:\n"
                for item in kg_evidence[:5]:
                    if item.get("entity_type"):
                        evidence_context += f"- {item['entity_type']}: {item.get('name', 'N/A')}\n"
        except Exception as e:
            logger.debug(f"KG evidence fetch failed for {topic.get('topic')}: {e}")

    from app.prompts import get_prompt
    prompt = get_prompt(
        "question_generation.yaml", "craft_question",
        output_language=output_language,
        experience_level=experience_level,
        topic=topic.get("topic"),
        category=topic.get("category"),
        difficulty=topic.get("difficulty"),
        evidence_context=evidence_context if evidence_context else "",
        recommended_probe=recommended_probe if recommended_probe else "",
    )

    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_heartbeat(llm, prompt, "craft_question", interval=30.0)

    question = result if isinstance(result, dict) else {}
    # 고유 ID 강제 할당 — LLM이 중복 ID를 생성하는 문제 방지
    question["id"] = f"q-{topic.get('category', 'x')[:4]}-{uuid.uuid4().hex[:8]}"
    question.setdefault("question_text", f"[{topic.get('topic')}] 관련 질문")
    question.setdefault("category", topic.get("category", "technical_depth"))
    question.setdefault("difficulty", topic.get("difficulty", "Medium"))
    question.setdefault("language", output_language)
    question.setdefault("topic", topic.get("topic"))

    # Add KG provenance metadata
    if topic.get("source", "").startswith("kg_"):
        question["kg_source"] = topic.get("source")
        question["kg_category"] = topic.get("kg_category")

    # Add code reference if available
    if code_reference:
        question["code_reference"] = {
            "file_path": code_reference.get("file_path"),
            "line_start": code_reference.get("line_start"),
            "line_end": code_reference.get("line_end"),
            "repository": code_reference.get("repository"),
        }

    # Use recommended probe if available and question_text is generic
    if recommended_probe and question.get("question_text", "").startswith("["):
        question["alternative_phrasing"] = question.get("alternative_phrasing", [])
        question["alternative_phrasing"].append(recommended_probe)

    return question


@activity.defn
@observe_activity(name="enhance_terminology", phase="question_generation")
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
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_heartbeat(llm, prompt, "enhance_terminology", interval=30.0)
    return result if isinstance(result, dict) else {}


@activity.defn
@observe_activity(name="craft_evaluation_scenarios", phase="question_generation")
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
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_heartbeat(llm, prompt, "craft_evaluation_scenarios", interval=30.0)
    return result if isinstance(result, dict) else {}


@activity.defn
@observe_activity(name="design_follow_ups", phase="question_generation")
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
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_heartbeat(llm, prompt, "design_follow_ups", interval=30.0)
    return result if isinstance(result, dict) else {}


@activity.defn
@observe_activity(name="generate_interviewer_notes", phase="question_generation")
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
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_heartbeat(llm, prompt, "generate_interviewer_notes", interval=30.0)
    return result if isinstance(result, dict) else {}


@activity.defn
@observe_activity(name="generate_decision_guide", phase="question_generation")
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
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_heartbeat(llm, prompt, "generate_decision_guide", interval=30.0)
    return result if isinstance(result, dict) else {}


@activity.defn
@observe_activity(name="revise_questions", phase="question_generation")
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
    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_heartbeat(llm, prompt, "revise_questions", interval=30.0)
    return result if isinstance(result, list) else questions


def _format_candidates(candidates: list[dict]) -> str:
    lines = []
    for i, c in enumerate(candidates[:30]):
        lines.append(f"{i+1}. [{c['source']}] {c['topic']} (score: {c['score']})")
    return "\n".join(lines)
