"""
backend/app/workflows/activities/question_generation.py
질문 생성 Activities (토픽 선정 + 개별 질문 생성)

Enhancement Activities는 question_enhancement.py로 분리됨.
유틸리티(상수, 헬퍼)는 question_generation_utils.py로 분리됨.
"""
import logging
import uuid

from temporalio import activity

from app.core.observability import observe_activity
from app.services.activity_logger import ActivityLogger
from app.workflows.utils import run_llm_with_prompt_config_heartbeat

# ── 분리된 모듈 import ──
from app.workflows.activities.question_generation_utils import (
    TOTAL_QUESTIONS,
    get_distribution,
    format_distribution_for_prompt,
    build_candidate_context,
    format_candidates,
)

# Backwards-compatible alias (테스트에서 사용)
_format_candidates = format_candidates  # noqa: F841
from app.workflows.activities.question_enhancement import (  # noqa: F401 — re-export
    enhance_terminology,
    craft_evaluation_scenarios,
    design_follow_ups,
    generate_interviewer_notes,
    generate_decision_guide,
    revise_questions,
)

logger = logging.getLogger(__name__)


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
    dist = get_distribution(experience_level)

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
        # JIT-29: AST 소스 스니펫 + JD relevance score 포함 (backward compatible)
        evidence = dict(impl)
        relevance = impl.get("relevance_score", {})
        if relevance:
            evidence["jd_keyword_score"] = relevance.get("jd_keyword_score", 0)
            evidence["interview_potential"] = relevance.get("interview_potential", 0)
        if impl.get("source_snippet"):
            evidence["source_snippet"] = impl["source_snippet"][:500]
        candidates.append({
            "source": "code",
            "topic": topic,
            "evidence": evidence,
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

    # 후보 소스 분포 추적 — 코드/KG 기반 비율이 낮으면 경고
    from collections import Counter as _Counter
    source_dist = _Counter(c.get("source", "unknown") for c in candidates)
    code_based = sum(v for k, v in source_dist.items() if k in ("code", "vector_code") or k.startswith("kg_"))
    total_cands = len(candidates)
    if total_cands > 0 and code_based / total_cands < 0.3:
        logger.warning(
            f"select_topics: code/KG-based candidates only {code_based}/{total_cands} "
            f"({code_based * 100 // total_cands}%) — questions may lack code evidence"
        )
    logger.info(f"select_topics candidate sources: {dict(source_dist)}")

    cat_dist_text, diff_dist_text = format_distribution_for_prompt(dist)
    candidate_context = build_candidate_context(analysis, enriched_input)

    from app.prompts import get_prompt_with_config
    prompt_config = get_prompt_with_config(
        "question_generation.yaml", "select_topics",
        max_questions=max_questions,
        experience_level=experience_level,
        candidates=format_candidates(candidates),
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
        # confidence_score < 0.3 토픽 필터링 (근거 부족 → 환각 위험)
        MIN_CONFIDENCE = 0.3
        filtered = [
            t for t in result
            if not isinstance(t, dict)
            or t.get("confidence_score", 1.0) >= MIN_CONFIDENCE
        ]
        dropped = len(result) - len(filtered)
        if dropped > 0:
            logger.info(f"select_topics: dropped {dropped} low-confidence topics (< {MIN_CONFIDENCE})")

        # LLM이 source 필드를 누락한 topic에 candidates에서 source 복원
        candidate_source_map = {c["topic"]: c.get("source", "") for c in candidates if isinstance(c, dict)}
        restored = 0
        for topic in filtered:
            if isinstance(topic, dict) and not topic.get("source"):
                topic_text = topic.get("topic", "")
                # 완전 일치 먼저, 없으면 부분 매칭
                if topic_text in candidate_source_map:
                    topic["source"] = candidate_source_map[topic_text]
                    restored += 1
                else:
                    # 부분 매칭: candidate topic이 LLM topic에 포함되거나 그 반대
                    for cand_topic, cand_source in candidate_source_map.items():
                        if cand_topic and topic_text and (
                            cand_topic in topic_text or topic_text in cand_topic
                        ):
                            topic["source"] = cand_source
                            restored += 1
                            break
        if restored > 0:
            logger.info(f"select_topics: restored source for {restored}/{len(filtered)} topics from candidates")

        if alog:
            await alog.result("Topics selected", {
                "topics_count": len(filtered[:max_questions]),
                "candidates_considered": len(candidates),
                "low_confidence_dropped": dropped,
            })
        return filtered[:TOTAL_QUESTIONS]

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
                full_snippet = code_reference['code_snippet']
                snippet = full_snippet[:300]
                truncated = len(full_snippet) > 300
                evidence_context += f"```\n{snippet}\n```\n"
                if truncated:
                    evidence_context += f"[TRUNCATED — showing {len(snippet)}/{len(full_snippet)} chars. Do NOT assume content beyond this excerpt.]\n"

    elif topic.get("source") == "code":
        evidence = topic.get("evidence", {})
        file_path = evidence.get("file_path", "")
        description = evidence.get("description", "")
        why_notable = evidence.get("why_notable", "")
        snippet = evidence.get("code_snippet", "") or evidence.get("source_snippet", "")

        evidence_context = f"\n\nCode-based evidence:\n"
        if file_path:
            evidence_context += f"- File: {file_path}\n"
        if description:
            evidence_context += f"- Description: {description}\n"
        if why_notable:
            evidence_context += f"- Why notable: {why_notable}\n"
        # JIT-29: JD relevance 점수 포함 (AST 파이프라인에서 제공 시)
        jd_kw_score = evidence.get("jd_keyword_score", 0)
        interview_pot = evidence.get("interview_potential", 0)
        if jd_kw_score or interview_pot:
            evidence_context += f"- JD Relevance: keyword={jd_kw_score:.2f}, interview_potential={interview_pot:.2f}\n"
        if snippet:
            truncated_snippet = snippet[:500]
            evidence_context += f"```\n{truncated_snippet}\n```\n"
            if len(snippet) > 500:
                evidence_context += f"[TRUNCATED — showing {len(truncated_snippet)}/{len(snippet)} chars. Do NOT assume content beyond this excerpt.]\n"

        # Build code_reference for frontend display
        code_reference = {
            "file_path": file_path,
            "code_snippet": snippet,
        }

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

    # 카테고리별 데이터 소스 접근 제어 (evidence_context 코드 검색 포함)
    from app.workflows.activities.question_generation_utils import CATEGORY_DATA_ACCESS
    category = topic.get("category", "technical_depth")
    code_access_level = CATEGORY_DATA_ACCESS.get(category, {}).get("code_analysis", "full")

    # pgvector 시맨틱 검색으로 추가 컨텍스트 수집 (카테고리별 제어)
    if job_id:
        try:
            from app.services.vector_store import get_vector_store
            vs = get_vector_store(job_id)
            topic_text = topic.get("topic", "")
            if topic_text:
                # 프로필 검색: 모든 카테고리에서 실행 (코드 접근 제한 카테고리는 limit 축소)
                profile_limit = 3 if code_access_level in ("full", "project_scope") else 2
                vector_results = await vs.search_profile(topic_text, limit=profile_limit)

                # 코드 검색: 카테고리별 code_analysis 레벨에 따라 제어
                code_results = []
                if code_access_level == "full":
                    code_results = await vs.search_code(topic_text, limit=2)
                elif code_access_level == "project_scope":
                    code_results = await vs.search_code(topic_text, limit=1)
                # tech_stack_only, none → 코드 벡터 검색 스킵

                relevant = [r for r in (vector_results + code_results) if r["similarity"] >= 0.5]
                if relevant:
                    evidence_context += "\n\nSemantic matches (vector search):\n"
                    for r in relevant[:4]:
                        evidence_context += f"- [{r['content_key']}] {r['content_text'][:150]} (similarity: {r['similarity']:.2f})\n"

                # JIT-64: vector_code/vector_github 소스에서 code_reference 구성
                if not code_reference and code_results:
                    best_code = max(code_results, key=lambda r: r.get("similarity", 0))
                    if best_code.get("similarity", 0) >= 0.5:
                        code_reference = {
                            "file_path": best_code.get("content_key", ""),
                            "code_snippet": best_code.get("content_text", "")[:500],
                        }
        except Exception as e:
            logger.debug(f"Vector search failed for craft_question: {e}")

    from app.prompts import get_prompt_with_config
    # 카테고리별 특화 프롬프트 선택 (fallback → 범용 craft_question)
    category_prompt_key = f"craft_question_{category}"
    # 카테고리별 데이터 소스 필터링 — 불필요한 데이터 제외 (토큰 절감 + 품질 향상)
    candidate_context = build_candidate_context(analysis, enriched_input, category=category)
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

    # evidence_source 보강 — LLM이 미제공 시 topic 소스에서 자동 유추
    if not question.get("evidence_source"):
        source = topic.get("source", "")
        if source.startswith("kg_"):
            question["evidence_source"] = "KnowledgeGraph"
        elif source == "code":
            question["evidence_source"] = "Code"
        elif source in ("resume", "document"):
            question["evidence_source"] = "Resume"
        elif source == "linkedin":
            question["evidence_source"] = "LinkedIn"
        elif source == "portfolio":
            question["evidence_source"] = "Portfolio"
        elif source == "github":
            question["evidence_source"] = "GitHub"
        elif source.startswith("vector_"):
            # vector_ 하위 소스를 구체적 evidence_source로 매핑
            if source in ("vector_code", "vector_github"):
                question["evidence_source"] = "GitHub"
            elif source in ("vector_profile", "vector_linkedin"):
                question["evidence_source"] = "LinkedIn"
            elif source in ("vector_resume", "vector_document"):
                question["evidence_source"] = "Resume"
            elif source == "vector_portfolio":
                question["evidence_source"] = "Portfolio"
            else:
                question["evidence_source"] = "SemanticSearch"
        elif source == "jd_match":
            question["evidence_source"] = "JD"
        elif source == "generated":
            question["evidence_source"] = "Analysis"
        else:
            # source가 빈 경우: topic/question 내용 기반으로 evidence_source 추론
            topic_text = (topic.get("topic", "") + " " + question.get("question_text", "")).lower()
            if any(kw in topic_text for kw in ("github", "commit", "repository", "repo", "코드", "code", "pull request", "pr")):
                question["evidence_source"] = "GitHub"
            elif any(kw in topic_text for kw in ("linkedin", "경력", "career", "experience", "이력")):
                question["evidence_source"] = "LinkedIn"
            elif any(kw in topic_text for kw in ("resume", "이력서", "portfolio", "포트폴리오")):
                question["evidence_source"] = "Resume"
            elif any(kw in topic_text for kw in ("jd", "job description", "직무", "요구사항", "requirement")):
                question["evidence_source"] = "JD"
            else:
                question["evidence_source"] = "General"
                question.setdefault("_quality_flags", [])
                question["_quality_flags"].append("no_evidence_source")
                logger.warning(f"craft_question: no evidence_source for topic '{topic.get('topic', '')[:40]}', marked as General — may be generic")

    # Add KG provenance metadata
    if topic.get("source", "").startswith("kg_"):
        question["kg_source"] = topic.get("source")
        question["kg_category"] = topic.get("kg_category")

    # 코드 기반 질문인데 code_reference가 없으면 품질 경고
    if question.get("evidence_source") in ("Code", "GitHub", "KnowledgeGraph") and not code_reference:
        question.setdefault("_quality_flags", [])
        question["_quality_flags"].append("code_question_without_reference")
        logger.warning(f"craft_question: code-based question '{topic.get('topic', '')[:40]}' has no code_reference")

    # Add code reference if available (mapped to frontend schema: file, lines, snippet)
    if code_reference:
        line_start = code_reference.get("line_start")
        line_end = code_reference.get("line_end")
        lines_str = f"{line_start}-{line_end}" if line_start and line_end else (str(line_start) if line_start else None)
        question["code_reference"] = {
            "file": code_reference.get("file_path") or code_reference.get("file"),
            "lines": lines_str or code_reference.get("lines"),
            "snippet": code_reference.get("code_snippet") or code_reference.get("snippet"),
        }

    # follow_ups good/poor 보강 — LLM이 생략하면 기본 구조 삽입
    for fu in question.get("follow_ups", []):
        if not isinstance(fu, dict):
            continue
        if "good" not in fu or not isinstance(fu.get("good"), dict):
            fu["good"] = {"text": fu.get("listen_for", ""), "score": 7}
        if "poor" not in fu or not isinstance(fu.get("poor"), dict):
            fu["poor"] = {"text": "", "score": 2}

    # Use recommended probe if available and question_text is generic
    if recommended_probe and question.get("question_text", "").startswith("["):
        question["alternative_phrasing"] = question.get("alternative_phrasing", [])
        question["alternative_phrasing"].append(recommended_probe)

    return question


