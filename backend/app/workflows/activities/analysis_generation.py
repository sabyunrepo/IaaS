"""
backend/app/workflows/activities/analysis_generation.py
Deep Analysis 생성 Activity (LLM 강화 + 규칙 기반 fallback)
"""
import json
import logging
from typing import Any

from temporalio import activity

from app.core.observability import observe_activity
from app.models.deep_analysis import (
    DeepAnalysis, EngineeringDNAItem, RiskFlag, SkillMatchRow,
)

logger = logging.getLogger(__name__)


async def _llm_calculate_radar_scores(
    jd_analysis: dict,
    code_analysis: dict | None,
    document_analysis: dict,
    output_language: str = "ko",
    job_id: str | None = None,
) -> tuple[list[int], list[int]] | None:
    """LLM 기반 레이더 점수 계산 (실패 시 None 반환)"""
    try:
        from app.services.cached_llm import CachedLLMService
        from app.prompts import get_prompt_with_config
        from app.workflows.utils import run_llm_with_prompt_config_heartbeat
        from app.services.i18n_labels import _t

        # KG 증거 수집
        kg_context = ""
        if job_id:
            try:
                from app.services.graph_queries import get_interview_graph_queries
                queries = get_interview_graph_queries(job_id)
                conflicts = await queries._get_conflict_candidates()
                gaps = await queries._get_gap_candidates()
                if conflicts:
                    kg_context += f"Conflicts detected: {len(conflicts)}\n"
                    for c in conflicts[:3]:
                        kg_context += f"- {c.topic}\n"
                if gaps:
                    kg_context += f"Skill gaps detected: {len(gaps)}\n"
                    for g in gaps[:3]:
                        kg_context += f"- {g.topic}\n"
            except Exception as e:
                logger.debug(f"KG enrichment failed for radar: {e}")

        # 요약 데이터 준비
        code_summary = _t("no_code_analysis_data", output_language)
        if code_analysis:
            code_summary = json.dumps({
                "tech_stack": code_analysis.get("tech_stack", [])[:10],
                "quality_metrics": code_analysis.get("quality_metrics", {}),
                "risk_flags_count": len(code_analysis.get("risk_flags", [])),
                "repos_count": len(code_analysis.get("repositories", [])),
            }, ensure_ascii=False, default=str)

        doc_summary = json.dumps({
            "skills": (lambda s: list(s.keys())[:10] if isinstance(s, dict) else list(s)[:10] if s else [])(document_analysis.get("profile", {}).get("skills", [])),
            "experience_count": len(document_analysis.get("profile", {}).get("experiences", [])),
            "jd_match_score": document_analysis.get("jd_match_score", 0),
        }, ensure_ascii=False, default=str)

        jd_summary = json.dumps({
            "job_title": jd_analysis.get("job_title", ""),
            "requirements_count": len(jd_analysis.get("requirements", [])),
            "key_requirements": [r.get("skill", "") for r in jd_analysis.get("requirements", [])[:5]],
        }, ensure_ascii=False, default=str)

        prompt_config = get_prompt_with_config(
            "v2_generation.yaml", "radar_analysis",
            jd_analysis=jd_summary,
            code_analysis_summary=code_summary,
            document_analysis_summary=doc_summary,
            output_language=output_language,
            kg_context=kg_context,
        )

        llm = CachedLLMService()
        result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)

        if not isinstance(result, dict) or "candidate_scores" not in result:
            return None

        scores = result["candidate_scores"]
        if not isinstance(scores, list) or len(scores) != 5:
            return None

        # 점수 범위 보정 (0-100)
        candidate_scores = [max(0, min(100, int(s))) for s in scores]
        required_scores = [80, 80, 60, 70, 70]

        logger.info(f"LLM radar scores: {candidate_scores}")
        return candidate_scores, required_scores

    except Exception as e:
        logger.warning(f"LLM radar analysis failed, using fallback: {e}")
        return None


async def _llm_analyze_engineering_dna(code_analysis: dict | None, output_language: str = "ko", job_id: str | None = None) -> list[EngineeringDNAItem] | None:
    """LLM 기반 Engineering DNA 분석 (실패 시 None 반환)"""
    if not code_analysis:
        return None

    try:
        from app.services.cached_llm import CachedLLMService
        from app.prompts import get_prompt_with_config
        from app.workflows.utils import run_llm_with_prompt_config_heartbeat

        # VectorStore 코드 패턴 검색
        kg_context = ""
        if job_id:
            try:
                from app.services.vector_store import get_vector_store
                vs = get_vector_store(job_id)
                for query in ["test coverage", "code quality", "architecture patterns"][:3]:
                    results = await vs.search_code(query, limit=2)
                    for r in results:
                        if r["similarity"] >= 0.5:
                            kg_context += f"- {query}: {r['content_text'][:100]} (sim={r['similarity']:.2f})\n"
            except Exception as e:
                logger.debug(f"Vector code enrichment failed for engineering DNA: {e}")

        code_data = json.dumps({
            "quality_metrics": code_analysis.get("quality_metrics", {}),
            "tech_stack": code_analysis.get("tech_stack", [])[:10],
            "patterns": code_analysis.get("patterns", [])[:5] if isinstance(code_analysis.get("patterns"), list) else [],
            "risk_flags": code_analysis.get("risk_flags", [])[:5],
        }, ensure_ascii=False, default=str)

        prompt_config = get_prompt_with_config(
            "v2_generation.yaml", "engineering_dna",
            code_analysis=code_data,
            output_language=output_language,
            kg_context=kg_context,
        )

        llm = CachedLLMService()
        result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)

        if not isinstance(result, list):
            return None

        from app.services.match_config import sanitize_color

        items = []
        for item in result[:6]:
            if not isinstance(item, dict):
                continue
            color = sanitize_color(item.get("color", "slate"))
            items.append(EngineeringDNAItem(
                label=item.get("label", ""),
                value=max(0, min(100, int(item.get("value", 0)))),
                display=item.get("display", ""),
                color=color,
                note=item.get("note"),
                tooltip=item.get("tooltip"),
            ))

        if items:
            logger.info(f"LLM engineering DNA: {len(items)} items")
            return items
        return None

    except Exception as e:
        logger.warning(f"LLM engineering DNA failed, using fallback: {e}")
        return None


def _calculate_radar_scores(
    jd_analysis: dict,
    code_analysis: dict | None,
    document_analysis: dict,
) -> tuple[list[int], list[int]]:
    """5축 레이더 점수 계산

    축: [role_fit, technical, execution, communication, code_quality]
    """
    # JD 요구 점수 (기본값)
    required_scores = [80, 80, 60, 70, 70]

    # 후보자 점수 계산
    candidate_scores = [50, 50, 50, 50, 50]  # 기본값

    profile = document_analysis.get("profile", {})
    skills = profile.get("skills", [])

    # Role Fit: JD 매칭 점수 기반
    jd_match = document_analysis.get("jd_match_score", 0.5)
    candidate_scores[0] = min(100, int(jd_match * 100 + 20))

    # Technical: 기술 스킬 기반
    if code_analysis:
        tech_stack = code_analysis.get("tech_stack", [])
        tech_score = min(100, 50 + len(tech_stack) * 5)
        candidate_scores[1] = tech_score

        # 코드 품질 지표 반영
        quality = code_analysis.get("quality_metrics", {})
        test_coverage = quality.get("test_coverage", 0)
        candidate_scores[1] = min(100, (candidate_scores[1] + test_coverage) // 2 + 20)

    # Execution: 경험 기반
    experiences = profile.get("experiences", [])
    execution_score = min(100, 40 + len(experiences) * 10)
    candidate_scores[2] = execution_score

    # Communication: 문서 품질 기반
    if code_analysis:
        doc_quality = code_analysis.get("quality_metrics", {}).get("documentation_score", 50)
        candidate_scores[3] = min(100, doc_quality + 20)

    # Code Quality: 테스트 커버리지, 문서화, 아키텍처 패턴 기반
    if code_analysis:
        quality = code_analysis.get("quality_metrics", {})
        test_cov = quality.get("test_coverage", 0)
        doc_score = quality.get("documentation_score", 50)
        complexity = quality.get("complexity_score", 50)
        raw = (test_cov * 0.4 + doc_score * 0.3 + max(0, 100 - complexity) * 0.3)
        candidate_scores[4] = max(20, min(100, int(raw)))
    else:
        candidate_scores[4] = 50

    return candidate_scores, required_scores


def _analyze_engineering_dna(code_analysis: dict | None, lang: str = "ko") -> list[EngineeringDNAItem]:
    """Engineering DNA 분석"""
    from app.services.i18n_labels import _t

    items = []

    if not code_analysis:
        items.append(EngineeringDNAItem(
            label=_t("code_analysis", lang),
            value=0,
            display=_t("unconfirmed", lang),
            color="slate",
            note=_t("no_github_data", lang),
        ))
        return items

    quality = code_analysis.get("quality_metrics", {})

    # 테스트 커버리지
    test_coverage = quality.get("test_coverage", 0)
    items.append(EngineeringDNAItem(
        label=_t("test_coverage", lang),
        value=test_coverage,
        display=f"{test_coverage}%",
        color="emerald" if test_coverage >= 70 else "amber" if test_coverage >= 40 else "red",
    ))

    # 문서화 품질
    doc_score = quality.get("documentation_score", 0)
    doc_display = _t("excellent", lang) if doc_score >= 80 else _t("moderate", lang) if doc_score >= 50 else _t("poor", lang)
    items.append(EngineeringDNAItem(
        label=_t("doc_quality", lang),
        value=doc_score,
        display=doc_display,
        color="blue" if doc_score >= 80 else "amber" if doc_score >= 50 else "red",
    ))

    # IaC 사용 여부
    iac_score = quality.get("iac_score", 0)
    items.append(EngineeringDNAItem(
        label=_t("iac", lang),
        value=iac_score,
        display=_t("confirmed", lang) if iac_score >= 50 else _t("unconfirmed", lang),
        color="emerald" if iac_score >= 50 else "red",
        note=_t("iac_not_found", lang) if iac_score < 50 else None,
        tooltip=_t("iac_tooltip", lang),
    ))

    # 코드 복잡도
    complexity = quality.get("complexity_score", 50)
    complexity_display = _t("low", lang) if complexity <= 30 else _t("moderate", lang) if complexity <= 70 else _t("high", lang)
    items.append(EngineeringDNAItem(
        label=_t("code_complexity", lang),
        value=complexity,
        display=complexity_display,
        color="emerald" if complexity <= 30 else "amber" if complexity <= 70 else "red",
    ))

    return items


def _extract_risk_flags(
    code_analysis: dict | None,
    document_analysis: dict,
    lang: str = "ko",
) -> list[RiskFlag]:
    """리스크 플래그 추출"""
    from app.services.i18n_labels import _t

    flags = []

    # 코드 분석 기반 리스크
    if code_analysis:
        code_risks = code_analysis.get("risk_flags", [])
        for risk in code_risks:
            if isinstance(risk, dict):
                flags.append(RiskFlag(
                    label=risk.get("label", _t("risk", lang)),
                    detail=risk.get("detail", risk.get("description", "")),
                ))
            elif isinstance(risk, str):
                flags.append(RiskFlag(label=_t("caution", lang), detail=risk))

    # 문서 분석 기반 리스크
    profile = document_analysis.get("profile", {})
    areas_to_probe = profile.get("areas_to_probe", [])
    for area in areas_to_probe[:3]:  # 상위 3개
        if isinstance(area, str):
            flags.append(RiskFlag(label=_t("needs_verification", lang), detail=area))

    return flags[:5]  # 최대 5개


async def _llm_build_skill_table(
    jd_analysis: dict,
    code_analysis: dict | None,
    document_analysis: dict,
    output_language: str = "ko",
    job_id: str | None = None,
) -> list[SkillMatchRow] | None:
    """LLM 기반 시맨틱 스킬 매칭 (실패 시 None 반환)"""
    try:
        from app.services.cached_llm import CachedLLMService
        from app.prompts import get_prompt_with_config
        from app.workflows.utils import run_llm_with_prompt_config_heartbeat

        jd_requirements = jd_analysis.get("requirements", [])
        if not jd_requirements:
            return None

        raw_candidate_skills = document_analysis.get("profile", {}).get("skills", [])
        candidate_skills = (
            list(raw_candidate_skills.keys()) if isinstance(raw_candidate_skills, dict)
            else list(raw_candidate_skills) if raw_candidate_skills else []
        )
        code_skills = code_analysis.get("tech_stack", []) if code_analysis else []

        jd_text = json.dumps(
            [r.get("skill", r.get("text", "")) for r in jd_requirements[:6]],
            ensure_ascii=False,
        )
        candidate_text = json.dumps(candidate_skills[:15], ensure_ascii=False) if candidate_skills else "[]"
        code_text = json.dumps(list(code_skills)[:15], ensure_ascii=False) if code_skills else "[]"

        prompt_config = get_prompt_with_config(
            "v2_generation.yaml", "skill_matching",
            jd_requirements=jd_text,
            candidate_skills=candidate_text,
            code_skills=code_text,
            output_language=output_language,
        )

        # Langfuse 모델 오버라이드 방지 — Kimi 모델 강제 사용
        from app.services.llm_config import KIMI_CHAT_MODEL
        prompt_config.model = KIMI_CHAT_MODEL

        llm = CachedLLMService()
        result = await run_llm_with_prompt_config_heartbeat(llm, prompt_config, interval=30.0)

        if not isinstance(result, list):
            return None

        valid_types = {"exact", "similar", "partial", "none"}
        rows = []
        for item in result[:6]:
            if not isinstance(item, dict):
                continue
            match_type = item.get("type", "none")
            if match_type not in valid_types:
                match_type = "none"
            rows.append(SkillMatchRow(
                skill=item.get("skill", ""),
                candidate=item.get("candidate", "—"),
                type=match_type,
                evidence=item.get("evidence", "No evidence"),
                confidence=max(0, min(100, int(item.get("confidence", 0)))),
            ))

        if rows:
            logger.info(f"LLM skill matching: {len(rows)} rows, avg confidence={sum(r.confidence for r in rows)//len(rows)}%")
            return rows
        return None

    except Exception as e:
        logger.warning(f"LLM skill matching failed, using fallback: {e}")
        return None


def _build_skill_table(
    jd_analysis: dict,
    code_analysis: dict | None,
    document_analysis: dict,
    lang: str = "ko",
) -> list[SkillMatchRow]:
    """스킬 매칭 테이블 생성 (규칙 기반 fallback)"""
    rows = []

    jd_requirements = jd_analysis.get("requirements", [])
    raw_candidate_skills = document_analysis.get("profile", {}).get("skills", [])
    raw_code_skills = code_analysis.get("tech_stack", []) if code_analysis else []

    # skills가 dict인 경우 키만 추출 (list/dict 모두 지원)
    candidate_skills = (
        list(raw_candidate_skills.keys()) if isinstance(raw_candidate_skills, dict)
        else list(raw_candidate_skills) if raw_candidate_skills else []
    )
    code_skills = (
        list(raw_code_skills.keys()) if isinstance(raw_code_skills, dict)
        else list(raw_code_skills) if raw_code_skills else []
    )

    all_candidate_skills = set(s.lower() for s in candidate_skills + code_skills)

    for req in jd_requirements[:6]:  # 상위 6개
        skill = req.get("skill", req.get("text", ""))
        skill_lower = skill.lower()

        from app.services.i18n_labels import _t

        # 매칭 타입 결정 — 양방향 매칭 (길이 가드 적용)
        match_type = "none"
        candidate_skill = "—"
        evidence = _t("no_evidence", lang)
        confidence = 0

        # 1단계: 이력서 스킬에서 매칭
        for cs in candidate_skills:
            cs_lower = cs.lower()
            if skill_lower == cs_lower:
                match_type, candidate_skill = "exact", cs
                evidence, confidence = _t("resume", lang), 95
                break
            # 후보자 스킬이 JD 요구사항에 포함 (역방향, e.g. "openai" in "llm api or...")
            elif len(cs_lower) >= 3 and cs_lower in skill_lower:
                match_type, candidate_skill = "similar", cs
                evidence, confidence = _t("resume", lang), 75
                break
            # JD 키워드가 후보자 스킬에 포함 (정방향, e.g. "api" in "fastapi")
            elif len(skill_lower) >= 3 and skill_lower in cs_lower:
                match_type, candidate_skill = "similar", cs
                evidence, confidence = _t("resume", lang), 70
                break

        # 2단계: 코드 분석 tech_stack에서 매칭
        if match_type == "none" and code_analysis:
            for cs in code_skills:
                cs_lower = cs.lower()
                if skill_lower == cs_lower:
                    match_type, candidate_skill = "exact", cs
                    evidence, confidence = "GitHub", 90
                    break
                elif len(cs_lower) >= 3 and cs_lower in skill_lower:
                    match_type, candidate_skill = "partial", cs
                    evidence, confidence = "GitHub", 65
                    break
                elif len(skill_lower) >= 3 and skill_lower in cs_lower:
                    match_type, candidate_skill = "partial", cs
                    evidence, confidence = "GitHub", 60
                    break

        rows.append(SkillMatchRow(
            skill=skill,
            candidate=candidate_skill,
            type=match_type,
            evidence=evidence,
            confidence=confidence,
        ))

    return rows


@activity.defn
@observe_activity(name="generate_deep_analysis", phase="finalization")
async def generate_deep_analysis(
    jd_analysis: dict,
    code_analysis: dict | None,
    document_analysis: dict,
    job_id: str | None = None,
    output_language: str = "ko",
) -> dict:
    """Deep Analysis 생성

    Args:
        jd_analysis: JD 분석 결과
        code_analysis: 코드 분석 결과 (optional)
        document_analysis: 문서 분석 결과
        job_id: Job ID (observability용)

    Returns:
        DeepAnalysis 데이터
    """
    logger.info(f"Generating Deep Analysis for job_id={job_id}")
    activity.heartbeat()

    # 1. 5축 레이더 점수 계산 (LLM 우선, 규칙 기반 fallback)
    llm_radar = await _llm_calculate_radar_scores(jd_analysis, code_analysis, document_analysis, output_language, job_id=job_id)
    if llm_radar:
        radar_candidate, radar_required = llm_radar
    else:
        radar_candidate, radar_required = _calculate_radar_scores(
            jd_analysis, code_analysis, document_analysis
        )
    activity.heartbeat()

    # 2. Engineering DNA 분석 (LLM 우선, 규칙 기반 fallback)
    engineering_dna = await _llm_analyze_engineering_dna(code_analysis, output_language, job_id=job_id)
    if engineering_dna is None:
        engineering_dna = _analyze_engineering_dna(code_analysis, lang=output_language)
    activity.heartbeat()

    # 3. 리스크 플래그 추출
    risk_flags = _extract_risk_flags(code_analysis, document_analysis, lang=output_language)
    activity.heartbeat()

    # 4. 스킬 매칭 테이블 생성 (LLM 우선, 규칙 기반 fallback)
    skill_table = await _llm_build_skill_table(
        jd_analysis, code_analysis, document_analysis,
        output_language=output_language, job_id=job_id,
    )
    if skill_table is None:
        skill_table = _build_skill_table(jd_analysis, code_analysis, document_analysis, lang=output_language)
    activity.heartbeat()

    # 전체 매칭 점수 계산
    if skill_table:
        avg_confidence = sum(row.confidence for row in skill_table) / len(skill_table)
        overall_match = int(avg_confidence)
    else:
        overall_match = 50

    deep_analysis = DeepAnalysis(
        radar_candidate=radar_candidate,
        radar_required=radar_required,
        engineering_dna=engineering_dna,
        risk_flags=risk_flags,
        skill_table=skill_table,
        overall_match=overall_match,
    )

    logger.info(f"Deep Analysis generated: overall_match={overall_match}%")
    return deep_analysis.model_dump()
