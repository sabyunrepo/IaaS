"""
backend/app/workflows/activities/decision_generation.py
Decision Support 생성 Activity (LLM 강화 + 규칙 기반 fallback)
"""
import json
import logging
from typing import Any

from temporalio import activity

from app.core.observability import observe_activity
from app.models.decision import (
    DecisionSupport, DecisionSummary, InterviewerGuideTips,
    JDCompetencyWeight, ResumeTip, CoverLetterInsight, KGEvidence,
)

logger = logging.getLogger(__name__)


async def _llm_generate_decision_summary(
    candidate_summary: dict,
    jd_analysis: dict,
    document_analysis: dict,
    output_language: str = "ko",
    job_id: str | None = None,
    candidate_profile: dict | None = None,
    code_analysis: dict | None = None,
) -> DecisionSummary | None:
    """LLM 기반 Decision Summary 생성 (실패 시 None 반환)"""
    try:
        from app.services.cached_llm import CachedLLMService
        from app.prompts import get_prompt_with_config
        from app.workflows.utils import run_llm_with_prompt_config_heartbeat
        from app.services.i18n_labels import _t

        # KG 증거 수집 — conflicts → concerns, gaps → 주의 영역
        kg_context = ""
        if job_id:
            try:
                from app.services.graph_queries import get_interview_graph_queries
                queries = get_interview_graph_queries(job_id)
                conflicts = await queries._get_conflict_candidates()
                gaps = await queries._get_gap_candidates()
                if conflicts:
                    kg_context += f"Conflicts requiring attention: {len(conflicts)}\n"
                    for c in conflicts[:5]:
                        kg_context += f"- {c.topic}\n"
                if gaps:
                    kg_context += f"Skill gaps identified: {len(gaps)}\n"
                    for g in gaps[:5]:
                        kg_context += f"- {g.topic}\n"
            except Exception as e:
                logger.debug(f"KG enrichment failed for decision summary: {e}")

        profile = document_analysis.get("profile", {})

        # JIT-43: candidate_profile 통합 데이터 → primary, document_analysis → fallback
        if candidate_profile and candidate_profile.get("skills"):
            skills_data = [s["canonical_name"] for s in candidate_profile["skills"][:15] if isinstance(s, dict) and s.get("canonical_name")]
            skill_sources = {
                s["canonical_name"]: s.get("sources", [])
                for s in candidate_profile["skills"][:15]
                if isinstance(s, dict) and s.get("canonical_name")
            }
        else:
            raw_skills = profile.get("skills", [])
            skills_data = raw_skills[:10] if isinstance(raw_skills, list) else list(raw_skills.keys())[:10]
            skill_sources = {}

        # LinkedIn 경력 데이터 enrichment
        linkedin_experiences = []
        if candidate_profile and candidate_profile.get("linkedin_experiences"):
            linkedin_experiences = candidate_profile["linkedin_experiences"][:3]

        # 경력 데이터: candidate_profile → profile fallback
        experiences = profile.get("experiences", [])[:3]
        if candidate_profile and candidate_profile.get("experiences"):
            experiences = candidate_profile["experiences"][:3]

        # JIT-44: HYBRID 코드 분석 깊이 컨텍스트
        code_depth_context = ""
        if code_analysis:
            ast_chunks = code_analysis.get("ast_chunk_count", 0)
            fn_count = code_analysis.get("analyzed_functions_count", 0)
            if ast_chunks > 0:
                code_depth_context = f"Code analysis depth: {fn_count} functions analyzed across {ast_chunks} AST chunks (direct code analysis)"

        candidate_profile_data = {
            "experience_years": profile.get("experience_years", 0),
            "experiences": experiences,
            "skills": skills_data,
            "skill_sources": skill_sources,
            "areas_to_probe": profile.get("areas_to_probe", [])[:3],
        }
        if code_depth_context:
            candidate_profile_data["code_depth_context"] = code_depth_context
        if linkedin_experiences:
            candidate_profile_data["linkedin_experiences"] = linkedin_experiences
        if candidate_profile and candidate_profile.get("data_completeness"):
            candidate_profile_data["data_completeness"] = candidate_profile["data_completeness"]
        # JIT-50: 추천서/봉사활동 서머리
        if candidate_profile and candidate_profile.get("recommendations_summary"):
            candidate_profile_data["recommendations_summary"] = candidate_profile["recommendations_summary"]
        if candidate_profile and candidate_profile.get("volunteer_summary"):
            candidate_profile_data["volunteer_summary"] = candidate_profile["volunteer_summary"]

        prompt_config = get_prompt_with_config(
            "v2_generation.yaml", "decision_summary",
            jd_analysis=json.dumps({
                "job_title": jd_analysis.get("job_title", ""),
                "requirements": jd_analysis.get("requirements", [])[:5],
            }, ensure_ascii=False, default=str),
            candidate_profile=json.dumps(candidate_profile_data, ensure_ascii=False, default=str),
            candidate_summary=json.dumps({
                "key_strengths": candidate_summary.get("key_strengths", [])[:3] if isinstance(candidate_summary, dict) else [],
            }, ensure_ascii=False, default=str),
            jd_match_score=document_analysis.get("jd_match_score", 0.5),
            output_language=output_language,
            kg_context=kg_context,
            code_depth_context=code_depth_context,
        )

        llm = CachedLLMService()
        result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)

        if not isinstance(result, dict):
            return None

        # 강점 소스 태그 자동 보강 — LLM이 누락 시 후처리
        SOURCE_TAGS = ("(Resume)", "(GitHub)", "(Resume + GitHub)", "(LinkedIn)", "(Multi-source)")
        raw_strengths = result.get("strengths", [])[:5]
        enriched_strengths = []
        for s in raw_strengths:
            if isinstance(s, str) and not any(tag in s for tag in SOURCE_TAGS):
                s_lower = s.lower()
                if any(w in s_lower for w in ["github", "레포", "repo", "커밋", "commit", "코드"]):
                    s = f"{s} (GitHub)"
                elif any(w in s_lower for w in ["linkedin", "링크드인"]):
                    s = f"{s} (LinkedIn)"
                elif any(w in s_lower for w in ["resume", "이력서", "경력", "경험"]):
                    # JIT-43: skill_sources에서 multi-source 여부 확인
                    if skill_sources:
                        matched_skill = next(
                            (sk for sk in skill_sources if sk.lower() in s_lower),
                            None,
                        )
                        if matched_skill and len(skill_sources[matched_skill]) > 1:
                            s = f"{s} (Multi-source)"
                        else:
                            s = f"{s} (Resume)"
                    else:
                        s = f"{s} (Resume)"
                else:
                    s = f"{s} (Resume)"
            enriched_strengths.append(s)

        summary = DecisionSummary(
            experience=result.get("experience", ""),
            jd_match=result.get("jd_match", _t("jd_medium", output_language)),
            level=result.get("level", "Mid"),
            level_evidence=result.get("level_evidence", ""),
            strengths=enriched_strengths,
            concerns=result.get("concerns", [])[:3],
        )
        logger.info(f"LLM decision summary: level={summary.level}, match={summary.jd_match}")
        return summary

    except Exception as e:
        logger.warning(f"LLM decision summary failed, using fallback: {e}")
        return None


async def _llm_generate_interviewer_tips(
    questions: list[dict],
    document_analysis: dict,
    jd_analysis: dict,
    output_language: str = "ko",
    job_id: str | None = None,
    candidate_profile: dict | None = None,
) -> InterviewerGuideTips | None:
    """LLM 기반 면접관 팁 생성 (실패 시 None 반환)"""
    try:
        from app.services.cached_llm import CachedLLMService
        from app.prompts import get_prompt_with_config
        from app.workflows.utils import run_llm_with_prompt_config_heartbeat

        # KG 증거 기반 면접관 팁 보강
        kg_context = ""
        if job_id:
            try:
                from app.services.graph_queries import get_interview_graph_queries
                queries = get_interview_graph_queries(job_id)
                # Evidence chains for top question topics
                for q in questions[:5]:
                    topic = q.get("topic", q.get("question_text", ""))
                    if topic:
                        evidence = await queries.get_evidence_chain_for_topic(topic)
                        if evidence:
                            kg_context += f"Evidence for '{topic[:50]}':\n"
                            for item in evidence[:2]:
                                if item.get("entity_type"):
                                    kg_context += f"  - {item['entity_type']}: {item.get('name', 'N/A')}\n"
            except Exception as e:
                logger.debug(f"KG enrichment failed for interviewer tips: {e}")

        profile = document_analysis.get("profile", {})
        question_summary = [
            {"idx": i + 1, "category": q.get("category", ""), "text": q.get("question_text", "")[:80]}
            for i, q in enumerate(questions[:10])
        ]

        # JIT-43: candidate_profile 통합 데이터 → primary, document_analysis → fallback
        experiences = profile.get("experiences", [])[:3]
        if candidate_profile and candidate_profile.get("experiences"):
            experiences = candidate_profile["experiences"][:3]

        areas_to_probe = profile.get("areas_to_probe", [])[:3]
        if candidate_profile and candidate_profile.get("areas_to_probe"):
            areas_to_probe = candidate_profile["areas_to_probe"][:3]

        candidate_profile_data = {
            "experiences": experiences,
            "areas_to_probe": areas_to_probe,
        }

        # LinkedIn 통합 데이터 추가
        if candidate_profile:
            if candidate_profile.get("skills"):
                candidate_profile_data["unified_skills"] = [
                    {"name": s["canonical_name"], "sources": s.get("sources", [])}
                    for s in candidate_profile["skills"][:10]
                    if isinstance(s, dict) and s.get("canonical_name")
                ]
            if candidate_profile.get("linkedin_experiences"):
                candidate_profile_data["linkedin_experiences"] = candidate_profile["linkedin_experiences"][:3]
            if candidate_profile.get("linkedin_honors"):
                candidate_profile_data["linkedin_honors"] = candidate_profile["linkedin_honors"][:3]
            # JIT-50: 추천서/봉사활동 서머리 주입
            if candidate_profile.get("recommendations_summary"):
                candidate_profile_data["recommendations_summary"] = candidate_profile["recommendations_summary"]
            if candidate_profile.get("volunteer_summary"):
                candidate_profile_data["volunteer_summary"] = candidate_profile["volunteer_summary"]

        prompt_config = get_prompt_with_config(
            "v2_generation.yaml", "interviewer_tips",
            questions=json.dumps(question_summary, ensure_ascii=False, default=str),
            candidate_profile=json.dumps(candidate_profile_data, ensure_ascii=False, default=str),
            cover_letter=json.dumps(
                document_analysis.get("cover_letter_analysis", {}),
                ensure_ascii=False, default=str,
            ),
            job_title=jd_analysis.get("job_title", ""),
            output_language=output_language,
            kg_context=kg_context,
        )

        llm = CachedLLMService()
        result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)

        if not isinstance(result, dict):
            return None

        # resume_based_tips 변환
        resume_tips = []
        for tip in result.get("resume_based_tips", [])[:5]:
            if isinstance(tip, dict):
                resume_tips.append(ResumeTip(
                    section=tip.get("section", ""),
                    insight=tip.get("insight", ""),
                    question_link=tip.get("question_link"),
                ))

        # cover_letter_insights 변환
        cl_insights = []
        for ins in result.get("cover_letter_insights", [])[:3]:
            if isinstance(ins, dict):
                cl_insights.append(CoverLetterInsight(
                    highlight=ins.get("highlight", ""),
                    interpretation=ins.get("interpretation", ""),
                    follow_up_opportunity=ins.get("follow_up_opportunity"),
                ))

        # red_flags 소스 태그 자동 보강
        SOURCE_TAGS = ("(Resume)", "(GitHub)", "(LinkedIn)", "(Resume + GitHub)", "(Multi-source)")

        def _enrich_source_tag(items: list) -> list:
            enriched = []
            for item in items[:5]:
                if isinstance(item, str) and not any(tag in item for tag in SOURCE_TAGS):
                    item_lower = item.lower()
                    if any(w in item_lower for w in ["github", "레포", "repo", "커밋", "commit", "코드", "code"]):
                        item = f"{item} (GitHub)"
                    elif any(w in item_lower for w in ["linkedin", "경력", "추천"]):
                        item = f"{item} (LinkedIn)"
                    elif any(w in item_lower for w in ["resume", "이력서", "경험", "포트폴리오"]):
                        item = f"{item} (Resume)"
                enriched.append(item)
            return enriched

        tips = InterviewerGuideTips(
            resume_based_tips=resume_tips,
            cover_letter_insights=cl_insights,
            red_flags_to_watch=_enrich_source_tag(result.get("red_flags_to_watch", [])),
        )
        logger.info(f"LLM interviewer tips: {len(resume_tips)} tips, {len(tips.red_flags_to_watch)} red flags")
        return tips

    except Exception as e:
        logger.warning(f"LLM interviewer tips failed, using fallback: {e}")
        return None


def _extract_decision_summary(
    candidate_summary: dict,
    jd_analysis: dict,
    document_analysis: dict,
    lang: str = "ko",
    experience_level: str = "미들",
    code_analysis: dict | None = None,
) -> DecisionSummary:
    """후보자 요약에서 Decision Summary 추출"""
    from app.services.i18n_labels import _t

    profile = document_analysis.get("profile", {})

    # 경력 요약 — profile 우선, 없으면 candidate_summary에서 추출
    experiences = profile.get("experiences", [])
    experience_years = profile.get("experience_years")

    # candidate_summary fallback for experience
    if not experiences and isinstance(candidate_summary, dict):
        co = candidate_summary.get("candidate_overview", {})
        if isinstance(co, dict):
            if experience_years is None:
                experience_years = co.get("experience_years", 0)
            cs_position = co.get("current_position", "")
            if cs_position:
                experiences = [{"company": "", "role": cs_position}]

    if experience_years is None:
        experience_years = 0

    experience_str = _t("years_n", lang, n=experience_years)
    if experiences:
        latest_exp = experiences[0] if experiences else {}
        company = latest_exp.get("company", "")
        role = latest_exp.get("role", latest_exp.get("title", ""))
        if company and role:
            experience_str = _t("years_at_company", lang, years=experience_years, role=role, company=company)

    # JD 매칭 레벨 (Google re:Work threshold — scoring_formulas.py)
    from app.services.scoring_formulas import (
        classify_jd_match, map_experience_level_label, classify_experience_level,
    )
    jd_match_score = document_analysis.get("jd_match_score", 0.5)
    jd_match_level = classify_jd_match(jd_match_score)  # "High" | "Medium" | "Low"
    jd_match = _t(f"jd_{jd_match_level.lower()}", lang)

    # 레벨: experience_level 파라미터 우선, SFIA v9 경력 기반 fallback
    level = map_experience_level_label(experience_level)
    level_evidence = ""
    if experience_level not in ("CTO/VP", "시니어", "미들", "주니어", "신입"):
        # 미인식 레벨 → SFIA v9 + Dreyfus 경력 기반 분류
        level, _ = classify_experience_level(experience_years)
        level_evidence = f"SFIA v9: {experience_years}년 경력 기반 자동 분류 (Resume)"
    else:
        level_evidence = f"사용자 지정 레벨: {experience_level} → {level}"

    # 강점 추출 — profile.skills 우선, 없으면 candidate_summary.technical_expertise
    strengths = []
    raw_skills = profile.get("skills", [])
    skill_list = (
        list(raw_skills.keys()) if isinstance(raw_skills, dict)
        else list(raw_skills) if raw_skills else []
    )

    # candidate_summary fallback for skills
    if not skill_list and isinstance(candidate_summary, dict):
        tech = candidate_summary.get("technical_expertise", {})
        if isinstance(tech, dict):
            for key in ["languages", "frameworks", "tools"]:
                for item in tech.get(key, [])[:3]:
                    if isinstance(item, dict):
                        skill_list.append(item.get("skill", item.get("tool", "")))
                    elif isinstance(item, str):
                        skill_list.append(item)

    key_skills = skill_list[:3]
    for skill in key_skills:
        if skill:
            strengths.append(f"{skill} ({_t('resume', lang)})")

    # Code analysis에서 추가 강점
    if isinstance(candidate_summary, dict):
        cs_strengths = candidate_summary.get("key_strengths", [])
        if isinstance(cs_strengths, list):
            for s in cs_strengths[:2]:
                if isinstance(s, dict):
                    strength_text = s.get("strength", "")
                    evidence = s.get("evidence", {})
                    source = _t("multi_source", lang) if isinstance(evidence, dict) and len(evidence) > 1 else _t("resume", lang)
                    if strength_text:
                        strengths.append(f"{strength_text} ({source})")
                elif isinstance(s, str):
                    strengths.append(s)

    # JIT-63: 우려사항 추출 — areas_to_probe + JD 스킬 갭 + 데이터 완전성 교차 활용
    concerns = []
    risk_flags = profile.get("areas_to_probe", [])
    for flag in risk_flags[:3]:
        if isinstance(flag, str):
            concerns.append(flag)
        elif isinstance(flag, dict):
            concerns.append(flag.get("concern", flag.get("area", "")))

    # JD 필수 스킬 갭 기반 우려사항 보강
    if len(concerns) < 3:
        jd_requirements = jd_analysis.get("requirements", [])
        candidate_skills_lower = {s.lower() for s in skill_list if isinstance(s, str)}
        for req in jd_requirements:
            if len(concerns) >= 3:
                break
            req_skill = req.get("skill", "") if isinstance(req, dict) else str(req)
            category = req.get("category", "") if isinstance(req, dict) else ""
            if category in ("필수", "required", "must") and req_skill.lower() not in candidate_skills_lower:
                concerns.append(f"JD 필수 요구사항 '{req_skill}' 관련 경험 미확인")

    # 데이터 완전성 기반 우려사항 보강
    if len(concerns) < 1:
        if not code_analysis:
            concerns.append(_t("no_code_data", lang) if _t("no_code_data", lang) != "no_code_data" else "GitHub 코드 데이터 없어 기술 역량 직접 검증 불가")

    return DecisionSummary(
        experience=experience_str,
        jd_match=jd_match,
        level=level,
        level_evidence=level_evidence,
        strengths=strengths[:5],
        concerns=concerns[:3],
    )


def _build_interviewer_tips(
    questions: list[dict],
    document_analysis: dict,
    jd_analysis: dict,
    lang: str = "ko",
) -> InterviewerGuideTips:
    """면접관 팁 구성"""
    from app.services.i18n_labels import _t

    # 이력서 기반 팁
    resume_tips = []
    profile = document_analysis.get("profile", {})
    experiences = profile.get("experiences", [])

    for exp in experiences[:3]:
        company = exp.get("company", "")
        role = exp.get("role", exp.get("title", ""))
        if company and role:
            # 관련 질문 찾기
            related_q_ids = []
            for i, q in enumerate(questions):
                q_text = q.get("question_text", "").lower()
                if company.lower() in q_text or role.lower() in q_text:
                    related_q_ids.append(i + 1)

            resume_tips.append(ResumeTip(
                section=f"{role} @ {company}",
                insight=_t("verify_resume_achievements", lang),
                question_link=f"Q{',Q'.join(str(q) for q in related_q_ids)}" if related_q_ids else None,
            ))

    # 커버레터 인사이트 (있는 경우)
    cover_letter_insights = []
    cover_letter = document_analysis.get("cover_letter_analysis", {})
    if cover_letter:
        motivations = cover_letter.get("motivations", [])
        for m in motivations[:2]:
            if isinstance(m, str):
                cover_letter_insights.append(CoverLetterInsight(
                    highlight=m,
                    interpretation=_t("request_specific_examples", lang),
                    follow_up_opportunity=_t("ask_for_supporting_evidence", lang),
                ))

    # Red flags — 각 항목에 데이터 출처 어노테이션
    red_flags = []
    areas_to_probe = profile.get("areas_to_probe", [])
    for area in areas_to_probe[:3]:
        if isinstance(area, str):
            flag_text = area
        elif isinstance(area, dict):
            flag_text = area.get("concern", area.get("area", ""))
        else:
            continue
        if flag_text and "(Resume)" not in flag_text and "(GitHub)" not in flag_text:
            flag_text = f"{flag_text} (Resume)"
        if flag_text:
            red_flags.append(flag_text)

    return InterviewerGuideTips(
        resume_based_tips=resume_tips[:5],
        cover_letter_insights=cover_letter_insights[:3],
        red_flags_to_watch=red_flags[:5],
    )


def _map_jd_competencies(
    jd_analysis: dict,
    questions: list[dict],
) -> list[JDCompetencyWeight]:
    """JD 역량과 질문 매핑"""
    competencies = []
    jd_requirements = jd_analysis.get("requirements", [])

    # 각 요구사항에 대해 가중치와 관련 질문 계산
    total_weight = len(jd_requirements) if jd_requirements else 1
    base_weight = 1.0 / total_weight if total_weight > 0 else 0.2

    for i, req in enumerate(jd_requirements[:5]):
        skill = req.get("skill", req.get("text", f"Competency {i+1}"))
        skill_lower = skill.lower()

        # 관련 질문 찾기
        related_questions = []
        for q_idx, q in enumerate(questions):
            q_text = q.get("question_text", "").lower()
            q_skills = q.get("skills_assessed", [])
            q_skills_lower = [s.lower() for s in q_skills]

            if skill_lower in q_text or any(skill_lower in s for s in q_skills_lower):
                related_questions.append(q_idx + 1)

        # 가중치 조정 (관련 질문이 많을수록 높은 가중치)
        weight = base_weight
        if related_questions:
            weight = min(0.4, base_weight + 0.05 * len(related_questions))

        competencies.append(JDCompetencyWeight(
            competency=skill,
            weight=round(weight, 2),
            related_questions=related_questions[:5],
        ))

    # 가중치 정규화 (합이 1.0이 되도록)
    total = sum(c.weight for c in competencies)
    if total > 0:
        for c in competencies:
            c.weight = round(c.weight / total, 2)

    return competencies


@activity.defn
@observe_activity(name="generate_decision_support", phase="finalization")
async def generate_decision_support(
    candidate_summary: dict,
    questions: list[dict],
    jd_analysis: dict,
    document_analysis: dict,
    job_id: str | None = None,
    output_language: str = "ko",
    experience_level: str = "미들",
    candidate_profile: dict | None = None,
    code_analysis: dict | None = None,
) -> dict:
    """Decision Support 생성

    Args:
        candidate_summary: 후보자 요약 데이터
        questions: 생성된 질문 목록
        jd_analysis: JD 분석 결과
        document_analysis: 문서 분석 결과
        job_id: Job ID (observability용)

    Returns:
        DecisionSupport 데이터
    """
    logger.info(f"Generating Decision Support for job_id={job_id}")
    activity.heartbeat()

    # 0-pre. candidate_profile에서 추가 데이터 추출
    profile_cover_letter = None
    profile_areas_to_probe = []
    profile_linkedin_honors = []
    if candidate_profile:
        profile_cover_letter = candidate_profile.get("cover_letter_insights")
        profile_areas_to_probe = candidate_profile.get("areas_to_probe", [])
        profile_linkedin_honors = candidate_profile.get("linkedin_honors", [])

    # 0. KG 근거 사전 수집 (decision_summary와 interviewer_tips에서 중복 호출 방지)
    kg_evidence = None
    if job_id:
        try:
            from app.services.graph_queries import get_interview_graph_queries
            queries = get_interview_graph_queries(job_id)
            conflicts = await queries._get_conflict_candidates()
            gaps = await queries._get_gap_candidates()
            conflict_topics = [c.topic for c in (conflicts or [])[:5]]
            gap_topics = [g.topic for g in (gaps or [])[:5]]
            if conflict_topics or gap_topics:
                kg_evidence = KGEvidence(
                    conflicts=conflict_topics,
                    gaps=gap_topics,
                    conflict_count=len(conflicts or []),
                    gap_count=len(gaps or []),
                )
                logger.info(f"KG evidence collected: {len(conflict_topics)} conflicts, {len(gap_topics)} gaps")
        except Exception as e:
            logger.debug(f"KG evidence collection failed (non-fatal): {e}")

    # 1. 후보자 요약 생성 (LLM 우선, 규칙 기반 fallback)
    summary = await _llm_generate_decision_summary(
        candidate_summary, jd_analysis, document_analysis, output_language,
        job_id=job_id, candidate_profile=candidate_profile,
        code_analysis=code_analysis,
    )
    if summary is None:
        summary = _extract_decision_summary(candidate_summary, jd_analysis, document_analysis, lang=output_language, experience_level=experience_level, code_analysis=code_analysis)
    elif not summary.concerns:
        # JIT-66: LLM이 유효한 summary를 반환했으나 concerns가 빈 배열인 경우
        # 기존 LLM 결과(strengths, level 등)를 보존하면서 concerns만 fallback에서 가져옴
        fallback_summary = _extract_decision_summary(candidate_summary, jd_analysis, document_analysis, lang=output_language, experience_level=experience_level, code_analysis=code_analysis)
        summary.concerns = fallback_summary.concerns
        logger.info(f"JIT-66: LLM concerns empty, filled {len(summary.concerns)} concerns from fallback")

    # JIT-66: 최종 concerns 최소 1개 검증
    if not summary.concerns:
        summary.concerns = ["추가 검증이 필요한 영역이 면접에서 확인되어야 합니다"]
        logger.warning("JIT-66: No concerns after all fallbacks, using minimum default")
    activity.heartbeat()

    # 2. 면접관 가이드 팁 생성 (LLM 우선, 규칙 기반 fallback)
    interviewer_guide = await _llm_generate_interviewer_tips(
        questions, document_analysis, jd_analysis, output_language,
        job_id=job_id, candidate_profile=candidate_profile,
    )
    if interviewer_guide is None:
        interviewer_guide = _build_interviewer_tips(questions, document_analysis, jd_analysis, lang=output_language)
    activity.heartbeat()

    # 3. JD 역량 매핑
    jd_competency_map = _map_jd_competencies(jd_analysis, questions)

    decision_support = DecisionSupport(
        summary=summary,
        interviewer_guide=interviewer_guide,
        jd_competency_map=jd_competency_map,
        kg_evidence=kg_evidence,
    )

    # === Post-processing 품질 검증 ===

    # Decision Summary: 강점에 소스 태그 존재 확인
    if summary.strengths:
        SOURCE_TAGS = ("(Resume)", "(GitHub)", "(Resume + GitHub)", "(LinkedIn)", "(Multi-source)", "(다중 소스)")
        strengths_with_source = sum(1 for s in summary.strengths if any(tag in s for tag in SOURCE_TAGS))
        logger.info(f"Decision summary: {len(summary.strengths)} strengths, {strengths_with_source} with source tags")
        if strengths_with_source < len(summary.strengths) // 2:
            logger.warning(f"Decision summary: {len(summary.strengths) - strengths_with_source} strengths lack source citation")

    # Decision Summary: 우려사항 비어있지 않은지 + level_evidence 존재 확인
    if summary.concerns:
        empty_concerns = sum(1 for c in summary.concerns if not c or len(c.strip()) < 5)
        if empty_concerns > 0:
            logger.warning(f"Decision summary: {empty_concerns} concerns with insufficient description")
    if not summary.level_evidence or len(summary.level_evidence.strip()) < 10:
        logger.warning("Decision summary: level_evidence missing or too short — SFIA/Dreyfus classification not cited")

    # Decision 내부 일관성: jd_match vs strengths/concerns 비율
    strengths_count = len(summary.strengths) if summary.strengths else 0
    concerns_count = len(summary.concerns) if summary.concerns else 0
    jd_match_lower = (summary.jd_match or "").lower()
    is_positive_match = any(w in jd_match_lower for w in ["높음", "strong", "우수", "적합", "high"])
    is_negative_match = any(w in jd_match_lower for w in ["낮음", "low", "부족", "미달", "weak"])
    if is_positive_match and concerns_count > strengths_count:
        logger.warning(
            f"Decision consistency issue: jd_match='{summary.jd_match}' (positive) "
            f"but concerns({concerns_count}) > strengths({strengths_count})"
        )
    elif is_negative_match and strengths_count > concerns_count + 2:
        logger.warning(
            f"Decision consistency issue: jd_match='{summary.jd_match}' (negative) "
            f"but strengths({strengths_count}) >> concerns({concerns_count})"
        )

    # Interviewer Guide: red_flags 소스 어노테이션 확인
    if interviewer_guide.red_flags_to_watch:
        flags_with_source = sum(1 for f in interviewer_guide.red_flags_to_watch if "(Resume)" in f or "(GitHub)" in f or "(LinkedIn)" in f)
        if flags_with_source < len(interviewer_guide.red_flags_to_watch) // 2:
            logger.warning(f"Interviewer guide: {len(interviewer_guide.red_flags_to_watch) - flags_with_source} red flags lack source annotation")

    logger.info(f"Decision Support generated with {len(jd_competency_map)} competencies mapped")

    result = decision_support.model_dump()

    # candidate_profile 확장 데이터 부착
    if candidate_profile:
        # 커버레터 인사이트 → 동기/적합성 판단 보강
        if profile_cover_letter:
            result["cover_letter_insights"] = profile_cover_letter
        # LinkedIn 수상/인증 → 인증/수상 근거
        if profile_linkedin_honors:
            result["linkedin_honors"] = profile_linkedin_honors[:5]
        # 프로필 기반 areas_to_probe → concerns 보강
        if profile_areas_to_probe and summary:
            existing_concerns = set((c or "").lower() for c in (summary.concerns or []))
            for area in profile_areas_to_probe[:3]:
                if isinstance(area, str) and area.lower() not in existing_concerns:
                    if len(summary.concerns or []) < 5:
                        if summary.concerns is None:
                            summary.concerns = []
                        summary.concerns.append(f"{area} (Profile)")
            # Update result with enriched summary
            result["summary"] = summary.model_dump() if hasattr(summary, 'model_dump') else result.get("summary", {})
        # 데이터 완전성 정보
        result["data_completeness"] = candidate_profile.get("data_completeness", 0.0)
        result["confidence_level"] = candidate_profile.get("confidence_level", "medium")

    return result
