"""
backend/app/workflows/activities/question_generation.py
질문 생성 Activities (토픽 선정 + 개별 질문 생성)
"""
import logging
import uuid

from temporalio import activity

from app.core.observability import observe_activity
from app.services.activity_logger import ActivityLogger
from app.workflows.utils import run_llm_with_prompt_config_heartbeat

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


def _build_candidate_context(analysis: dict, enriched_input: dict) -> str:
    """
    후보자 정보를 LLM 프롬프트용 요약 텍스트로 조합.
    document_analysis, code_analysis, linkedin_profile, jd_analysis에서 핵심 정보 추출.
    각 섹션은 graceful degradation (데이터 없으면 스킵).
    """
    sections = []

    # 1. 이력서/포트폴리오 프로필
    doc = analysis.get("document_analysis", {})
    profile = doc.get("profile", {})
    if profile:
        parts = []
        if profile.get("name"):
            parts.append(f"Name: {profile['name']}")
        if profile.get("summary"):
            parts.append(f"Summary: {profile['summary'][:200]}")
        skills = profile.get("skills", [])
        if skills:
            parts.append(f"Skills: {', '.join(skills[:15])}")
        experience = profile.get("work_experience") or profile.get("experience", [])
        if experience and isinstance(experience, list):
            exp_lines = []
            for exp in experience[:3]:
                if isinstance(exp, dict):
                    role = exp.get("title") or exp.get("role", "")
                    company = exp.get("company", "")
                    if role or company:
                        exp_lines.append(f"  - {role} @ {company}")
                elif isinstance(exp, str):
                    exp_lines.append(f"  - {exp[:100]}")
            if exp_lines:
                parts.append("Work Experience:\n" + "\n".join(exp_lines))
        projects = profile.get("projects", [])
        if projects and isinstance(projects, list):
            proj_lines = []
            for proj in projects[:3]:
                if isinstance(proj, dict):
                    proj_lines.append(f"  - {proj.get('name', proj.get('title', ''))}: {proj.get('description', '')[:80]}")
                elif isinstance(proj, str):
                    proj_lines.append(f"  - {proj[:100]}")
            if proj_lines:
                parts.append("Projects:\n" + "\n".join(proj_lines))
        if parts:
            sections.append("## Resume/Portfolio\n" + "\n".join(parts))

    # 2. LinkedIn 프로필
    raw_input = enriched_input.get("raw_input", {})
    linkedin = raw_input.get("linkedin_profile") or enriched_input.get("linkedin_profile", {})
    if linkedin and isinstance(linkedin, dict):
        parts = []
        name = linkedin.get("full_name") or linkedin.get("name", "")
        headline = linkedin.get("headline", "")
        if name:
            parts.append(f"Name: {name}")
        if headline:
            parts.append(f"Headline: {headline}")
        experiences = linkedin.get("experiences") or linkedin.get("experience", [])
        if experiences and isinstance(experiences, list):
            for exp in experiences[:3]:
                if isinstance(exp, dict):
                    title = exp.get("title", "")
                    company = exp.get("company_name") or exp.get("company", "")
                    if title or company:
                        parts.append(f"  - {title} @ {company}")
        li_skills = linkedin.get("skills", [])
        if li_skills and isinstance(li_skills, list):
            skill_names = []
            for s in li_skills[:10]:
                skill_names.append(s.get("name", str(s)) if isinstance(s, dict) else str(s))
            parts.append(f"Skills: {', '.join(skill_names)}")
        if parts:
            sections.append("## LinkedIn Profile\n" + "\n".join(parts))

    # 3. 코드 분석
    code = analysis.get("code_analysis", {})
    if code:
        parts = []
        langs = code.get("languages") or code.get("tech_stack", [])
        if langs:
            if isinstance(langs, dict):
                parts.append(f"Languages: {', '.join(list(langs.keys())[:10])}")
            elif isinstance(langs, list):
                parts.append(f"Tech Stack: {', '.join(str(l) for l in langs[:10])}")
        repo_summary = code.get("summary") or code.get("repo_summary", "")
        if repo_summary and isinstance(repo_summary, str):
            parts.append(f"Summary: {repo_summary[:200]}")
        top_candidates = code.get("top_question_candidates", [])
        if top_candidates:
            cand_lines = [f"  - {c.get('title', '')}" for c in top_candidates[:5] if isinstance(c, dict)]
            if cand_lines:
                parts.append("Notable Implementations:\n" + "\n".join(cand_lines))
        if parts:
            sections.append("## Code Analysis (GitHub)\n" + "\n".join(parts))

    # 4. JD 매칭 요약
    jd = analysis.get("jd_analysis", {})
    if jd:
        parts = []
        title = jd.get("job_title", "")
        if title:
            parts.append(f"Target Role: {title}")
        reqs = jd.get("requirements", [])
        if reqs:
            req_skills = []
            for r in reqs[:8]:
                if isinstance(r, dict):
                    req_skills.append(r.get("skill", str(r)))
                else:
                    req_skills.append(str(r))
            parts.append(f"Key Requirements: {', '.join(req_skills)}")
        if parts:
            sections.append("## JD Requirements\n" + "\n".join(parts))

    if not sections:
        return ""

    return "\n\n".join(sections)


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

    # pgvector 시맨틱 검색 기반 후보 (JD 요구사항으로 프로필/코드 벡터 검색)
    if job_id:
        activity.heartbeat("Searching vector store for semantic matches...")
        try:
            from app.services.vector_store import get_vector_store
            vs = get_vector_store(job_id)

            # JD 핵심 요구사항으로 시맨틱 검색
            jd_analysis = analysis.get("jd_analysis", {})
            jd_requirements = jd_analysis.get("requirements", [])
            search_queries = []
            for req in jd_requirements[:5]:  # 상위 5개 요구사항
                skill = req.get("skill", "") if isinstance(req, dict) else str(req)
                if skill:
                    search_queries.append(skill)

            # 프로필 + 코드 벡터 검색
            for query in search_queries:
                for kind, search_fn in [("profile", vs.search_profile), ("code", vs.search_code)]:
                    try:
                        results = await search_fn(query, limit=3)
                        for r in results:
                            if r["similarity"] < 0.5:  # 유사도 임계값
                                continue
                            # 중복 방지
                            topic_key = f"{query} ({r['content_key']})"
                            if any(c["topic"] == topic_key for c in candidates):
                                continue
                            candidates.append({
                                "source": f"vector_{kind}",
                                "topic": topic_key,
                                "evidence": {
                                    "content_key": r["content_key"],
                                    "content_text": r["content_text"][:200],
                                    "similarity": r["similarity"],
                                },
                                "score": round(r["similarity"] * 0.8, 2),  # 시맨틱 점수 (0.8 스케일)
                            })
                    except Exception as e:
                        logger.debug(f"Vector search failed for {kind}/{query}: {e}")

            logger.info(f"[{job_id}] Added vector search candidates (total candidates: {len(candidates)})")
        except Exception as e:
            logger.warning(f"[{job_id}] Vector search failed (using fallback): {e}")

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
    candidate_context = _build_candidate_context(analysis, enriched_input)

    from app.prompts import get_prompt_with_config
    prompt_config = get_prompt_with_config(
        "question_generation.yaml", "select_topics",
        max_questions=max_questions,
        experience_level=experience_level,
        candidates=_format_candidates(candidates),
        category_distribution=cat_dist_text,
        difficulty_distribution=diff_dist_text,
        candidate_context=candidate_context,
    )

    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)

    # LLM이 {"topics": [...]} 형태로 반환할 경우 배열 추출
    if isinstance(result, dict) and "topics" in result and isinstance(result["topics"], list):
        logger.info("select_topics: extracted list from wrapped dict")
        result = result["topics"]

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

    # pgvector 시맨틱 검색으로 추가 컨텍스트 수집
    if job_id:
        try:
            from app.services.vector_store import get_vector_store
            vs = get_vector_store(job_id)
            topic_text = topic.get("topic", "")
            if topic_text:
                vector_results = await vs.search_profile(topic_text, limit=3)
                code_results = await vs.search_code(topic_text, limit=2)
                relevant = [r for r in (vector_results + code_results) if r["similarity"] >= 0.5]
                if relevant:
                    evidence_context += "\n\nSemantic matches (vector search):\n"
                    for r in relevant[:4]:
                        evidence_context += f"- [{r['content_key']}] {r['content_text'][:150]} (similarity: {r['similarity']:.2f})\n"
        except Exception as e:
            logger.debug(f"Vector search failed for craft_question: {e}")

    from app.prompts import get_prompt_with_config
    # 카테고리별 특화 프롬프트 선택 (fallback → 범용 craft_question)
    category = topic.get("category", "technical_depth")
    category_prompt_key = f"craft_question_{category}"
    candidate_context = _build_candidate_context(analysis, enriched_input)
    try:
        prompt_config = get_prompt_with_config(
            "question_generation.yaml", category_prompt_key,
            output_language=output_language,
            experience_level=experience_level,
            topic=topic.get("topic"),
            category=category,
            difficulty=topic.get("difficulty"),
            evidence_context=evidence_context if evidence_context else "",
            recommended_probe=recommended_probe if recommended_probe else "",
            candidate_context=candidate_context,
        )
        logger.info(f"Using category-specific prompt: {category_prompt_key}")
    except (KeyError, Exception) as e:
        logger.warning(f"Category prompt '{category_prompt_key}' not found, falling back to generic: {e}")
        prompt_config = get_prompt_with_config(
            "question_generation.yaml", "craft_question",
            output_language=output_language,
            experience_level=experience_level,
            topic=topic.get("topic"),
            category=category,
            difficulty=topic.get("difficulty"),
            evidence_context=evidence_context if evidence_context else "",
            recommended_probe=recommended_probe if recommended_probe else "",
            candidate_context=candidate_context,
        )

    # LLM 호출 중 주기적 heartbeat 전송 (타임아웃 방지)
    result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)

    from app.services.cached_llm import validate_llm_output
    question = validate_llm_output(
        result,
        required_fields=["question_text", "follow_ups", "evaluation_criteria"],
        activity_name="craft_question",
    )

    # 고유 ID 강제 할당 — LLM이 중복 ID를 생성하는 문제 방지
    question["id"] = f"q-{topic.get('category', 'x')[:4]}-{uuid.uuid4().hex[:8]}"
    question.setdefault("question_text", f"[{topic.get('topic')}] 관련 질문")
    question.setdefault("category", topic.get("category", "technical_depth"))
    question.setdefault("difficulty", topic.get("difficulty", "Medium"))
    question.setdefault("language", output_language)
    question.setdefault("topic", topic.get("topic"))

    # 필수 필드 검증 — LLM이 빈 질문 텍스트를 반환하는 경우 방지
    if not question.get("question_text") or question["question_text"].startswith("["):
        question["_quality_flag"] = "low_quality_text"
        logger.warning(f"craft_question produced low quality text: {question.get('question_text', '')[:50]}")

    # 평가 시나리오 기본값 보장
    question.setdefault("evaluation_scenarios", {
        "excellent": "",
        "acceptable": "",
        "poor": "",
    })

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
    from app.prompts import get_prompt_with_config
    import json

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
    return validate_llm_output(result, activity_name="enhance_terminology")


@activity.defn
@observe_activity(name="craft_evaluation_scenarios", phase="question_generation")
async def craft_evaluation_scenarios(questions: list[dict], enriched_input: dict) -> dict:
    """3d. Scenario Writer Agent — 3단계 평가 시나리오 생성"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt_with_config
    import json

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
    return validate_llm_output(result, activity_name="craft_evaluation_scenarios")


@activity.defn
@observe_activity(name="design_follow_ups", phase="question_generation")
async def design_follow_ups(questions: list[dict], enriched_input: dict) -> dict:
    """3e. Follow-up Designer Agent — 후속질문 분기 설계"""
    from app.services.cached_llm import CachedLLMService
    from app.prompts import get_prompt_with_config
    import json

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
    import json

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
    import json

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


def _format_candidates(candidates: list[dict]) -> str:
    lines = []
    for i, c in enumerate(candidates[:30]):
        lines.append(f"{i+1}. [{c['source']}] {c['topic']} (score: {c['score']})")
    return "\n".join(lines)
