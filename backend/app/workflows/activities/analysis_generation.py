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
    DeepAnalysis, RiskFlag, SkillMatchRow,
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
                    for c in conflicts[:5]:
                        kg_context += f"- {c.topic}\n"
                if gaps:
                    kg_context += f"Skill gaps detected: {len(gaps)}\n"
                    for g in gaps[:5]:
                        kg_context += f"- {g.topic}\n"
            except Exception as e:
                logger.debug(f"KG enrichment failed for radar: {e}")

        # 결정론적 공식 기반 기준 점수 선계산 (LLM 참고용)
        from app.services.scoring_formulas import (
            calculate_radar_scores as _formula_radar,
        )
        formula_radar = _formula_radar(
            jd_analysis, code_analysis or {}, document_analysis,
            output_language=output_language,
        )
        formula_base = {
            "role_fit": formula_radar.candidate[0],
            "technical": formula_radar.candidate[1],
            "execution": formula_radar.candidate[2],
            "communication": formula_radar.candidate[3],
            "code_quality": formula_radar.candidate[4],
        }
        formula_sources = formula_radar.sources

        # 요약 데이터 준비
        code_summary = _t("no_code_analysis_data", output_language)
        if code_analysis:
            # JIT-29: AST/JD-Aware 신포맷 필드 추가 (backward compatible)
            summary_data = {
                "tech_stack": code_analysis.get("tech_stack", [])[:10],
                "quality_metrics": code_analysis.get("quality_metrics", {}),
                "risk_flags_count": len(code_analysis.get("risk_flags", [])),
                "repos_count": len(code_analysis.get("repositories", [])),
            }
            # 신포맷 필드 — 있을 때만 추가
            if code_analysis.get("jd_relevance_scores"):
                summary_data["jd_relevance_scores"] = code_analysis["jd_relevance_scores"]
            if code_analysis.get("ast_chunk_count"):
                summary_data["ast_chunk_count"] = code_analysis["ast_chunk_count"]
            if code_analysis.get("analyzed_functions_count"):
                summary_data["analyzed_functions_count"] = code_analysis["analyzed_functions_count"]
            if code_analysis.get("hybrid_metadata"):
                summary_data["hybrid_metadata"] = code_analysis["hybrid_metadata"]
            code_summary = json.dumps(summary_data, ensure_ascii=False, default=str)

        raw_skills = document_analysis.get("profile", {}).get("skills", [])
        skills_to_summarize = []
        if isinstance(raw_skills, dict):
            skills_to_summarize.extend(
                skill
                for skill_list in raw_skills.values() if isinstance(skill_list, list)
                for skill in skill_list if isinstance(skill, str)
            )
        elif isinstance(raw_skills, list):
            skills_to_summarize.extend(skill for skill in raw_skills if isinstance(skill, str))

        doc_summary = json.dumps({
            "skills": skills_to_summarize[:10],
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
            formula_base_scores=json.dumps(formula_base, ensure_ascii=False),
            formula_sources=json.dumps(formula_sources, ensure_ascii=False),
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

        # 결정론적 기준 점수와 비교하여 ±15% 범위로 바운딩
        from app.services.scoring_formulas import get_required_scores
        for i in range(5):
            base = formula_radar.candidate[i]
            max_delta = max(15, int(base * 0.15))
            candidate_scores[i] = max(
                base - max_delta,
                min(base + max_delta, candidate_scores[i]),
            )

        required_scores = formula_radar.required

        # LLM reasoning 추출 (축별 근거) — 5축 모두 존재 검증 + 누락 보강
        llm_reasoning = result.get("reasoning", {})
        if not isinstance(llm_reasoning, dict):
            llm_reasoning = {}

        axis_names = ["role_fit", "technical", "execution", "communication", "code_quality"]
        for i, axis in enumerate(axis_names):
            reason = llm_reasoning.get(axis, "")
            if not reason or not isinstance(reason, str) or len(reason.strip()) < 5:
                # LLM이 누락한 축 → formula_sources 기반 자동 보강
                fallback_src = formula_radar.sources[i] if i < len(formula_radar.sources) else ""
                llm_reasoning[axis] = f"{fallback_src} (formula-based)" if fallback_src else "Data insufficient"

        logger.info(f"LLM radar scores (bounded): {candidate_scores}, formula base: {formula_radar.candidate}")
        return candidate_scores, required_scores, formula_radar.sources, llm_reasoning

    except Exception as e:
        logger.warning(f"LLM radar analysis failed, using fallback: {e}")
        return None


def _calculate_radar_scores(
    jd_analysis: dict,
    code_analysis: dict | None,
    document_analysis: dict,
    experience_level: str = "미들",
    linkedin_profile: dict | None = None,
    output_language: str = "ko",
    candidate_profile: dict | None = None,
) -> tuple[list[int], list[int], list[str], str, list[str]]:
    """5축 레이더 점수 계산 (Evidence-Based Scoring)

    축: [role_fit, technical, execution, communication, code_quality]

    산업 표준 기반 결정론적 공식 사용:
    - McCabe (1976): Cyclomatic Complexity
    - SFIA v9: Experience level classification
    - SonarQube SQALE: Code quality composite
    - Bird et al. (2011): Code ownership & stability

    Returns:
        (candidate_scores, required_scores, sources, confidence, human_sources)
    """
    from app.services.scoring_formulas import calculate_radar_scores as _formula_radar

    radar = _formula_radar(
        jd_analysis, code_analysis, document_analysis, experience_level,
        linkedin_profile=linkedin_profile, output_language=output_language,
        candidate_profile=candidate_profile,
    )
    return radar.candidate, radar.required, radar.sources, radar.confidence, radar.human_sources


def _extract_risk_flags(
    code_analysis: dict | None,
    document_analysis: dict,
    lang: str = "ko",
) -> list[RiskFlag]:
    """리스크 플래그 추출"""
    from app.services.i18n_labels import _t

    flags = []

    # 코드 분석 기반 리스크 — (GitHub) 소스 어노테이션
    if code_analysis:
        code_risks = code_analysis.get("risk_flags", [])
        for risk in code_risks:
            if isinstance(risk, dict):
                detail = risk.get("detail", risk.get("description", ""))
                if detail and "(GitHub)" not in detail:
                    detail = f"{detail} (GitHub)"
                flags.append(RiskFlag(
                    label=risk.get("label", _t("risk", lang)),
                    detail=detail,
                ))
            elif isinstance(risk, str):
                detail = f"{risk} (GitHub)" if "(GitHub)" not in risk else risk
                flags.append(RiskFlag(label=_t("caution", lang), detail=detail))

    # 문서 분석 기반 리스크 — (Resume) 소스 어노테이션
    profile = document_analysis.get("profile", {})
    areas_to_probe = profile.get("areas_to_probe", [])
    for area in areas_to_probe[:3]:
        if isinstance(area, str):
            detail = f"{area} (Resume)" if "(Resume)" not in area else area
            flags.append(RiskFlag(label=_t("needs_verification", lang), detail=detail))

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

        # 필수 스킬 우선 정렬 + 최대 15개 (Issue #245)
        sorted_requirements = sorted(
            jd_requirements,
            key=lambda r: 0 if r.get("category") in ("필수", "required", "must") else 1,
        )

        raw_candidate_skills = document_analysis.get("profile", {}).get("skills", [])
        candidate_skills = [
            skill
            for skill_list in raw_candidate_skills.values()
            for skill in skill_list
        ] if isinstance(raw_candidate_skills, dict) else list(raw_candidate_skills or [])
        code_skills = code_analysis.get("tech_stack", []) if code_analysis else []
        # JIT-29: JD relevance scores가 있으면 스킬에 매칭 점수 보강
        jd_relevance = code_analysis.get("jd_relevance_scores", {}) if code_analysis else {}

        jd_text = json.dumps(
            [{"skill": r.get("skill", r.get("text", "")), "category": r.get("category", "우대")} for r in sorted_requirements[:15]],
            ensure_ascii=False,
        )
        candidate_text = json.dumps(candidate_skills[:15], ensure_ascii=False) if candidate_skills else "[]"
        # JIT-29: jd_relevance 있으면 스킬 + 점수 형태로 전달 (backward compatible)
        if jd_relevance and code_skills:
            enriched_skills = []
            for skill in list(code_skills)[:15]:
                skill_str = str(skill)
                score = jd_relevance.get(skill_str, {})
                if isinstance(score, dict):
                    enriched_skills.append({"skill": skill_str, "jd_score": score.get("score", 0)})
                else:
                    enriched_skills.append(skill_str)
            code_text = json.dumps(enriched_skills, ensure_ascii=False)
        else:
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
        # confidence ↔ type 유효 범위 (프롬프트 CONSISTENCY RULES와 동기화)
        _CONFIDENCE_RANGES: dict[str, tuple[int, int]] = {
            "exact": (70, 100),
            "similar": (50, 89),
            "partial": (30, 69),
            "none": (0, 30),
        }
        corrected_count = 0
        rows = []
        for item in result[:15]:
            if not isinstance(item, dict):
                continue
            match_type = item.get("type", "none")
            if match_type not in valid_types:
                match_type = "none"
            confidence = max(0, min(100, int(item.get("confidence", 0))))

            # confidence ↔ type 불일치 자동 보정
            lo, hi = _CONFIDENCE_RANGES[match_type]
            if confidence < lo or confidence > hi:
                corrected_count += 1
                confidence = max(lo, min(hi, confidence))

            rows.append(SkillMatchRow(
                skill=item.get("skill", ""),
                candidate=item.get("candidate", "—"),
                type=match_type,
                evidence=item.get("evidence", "No evidence"),
                confidence=confidence,
            ))

        if corrected_count > 0:
            logger.warning(f"Skill matching: {corrected_count}/{len(rows)} rows had confidence ↔ type mismatch — auto-corrected")
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

    candidate_skills = [
        skill
        for skill_list in raw_candidate_skills.values()
        for skill in skill_list
    ] if isinstance(raw_candidate_skills, dict) else list(raw_candidate_skills or [])

    code_skills = [
        skill
        for skill_list in raw_code_skills.values()
        for skill in skill_list
    ] if isinstance(raw_code_skills, dict) else list(raw_code_skills or [])

    all_candidate_skills = set(s.lower() for s in candidate_skills + code_skills)

    # 필수 스킬 우선 정렬 + 최대 15개 (Issue #245)
    sorted_reqs = sorted(
        jd_requirements,
        key=lambda r: 0 if r.get("category") in ("필수", "required", "must") else 1,
    )
    for req in sorted_reqs[:15]:
        skill = req.get("skill", req.get("text", ""))
        skill_lower = skill.lower()

        from app.services.i18n_labels import _t

        # 매칭 타입 결정 — 양방향 매칭 (길이 가드 적용)
        match_type = "none"
        candidate_skill = "—"
        evidence = _t("no_evidence", lang)
        confidence = 0

        # 1단계: 이력서 스킬에서 매칭
        resume_source = ""
        for cs in candidate_skills:
            cs_lower = cs.lower()
            if skill_lower == cs_lower:
                match_type, candidate_skill = "exact", cs
                resume_source = f"Resume: {cs} listed"
                evidence, confidence = resume_source, 95
                break
            elif len(cs_lower) >= 3 and cs_lower in skill_lower:
                match_type, candidate_skill = "similar", cs
                resume_source = f"Resume: {cs} (similar)"
                evidence, confidence = resume_source, 75
                break
            elif len(skill_lower) >= 3 and skill_lower in cs_lower:
                match_type, candidate_skill = "similar", cs
                resume_source = f"Resume: {cs} (related)"
                evidence, confidence = resume_source, 70
                break

        # 2단계: 코드 분석 tech_stack에서 매칭 (보강 또는 신규)
        code_source = ""
        if code_analysis:
            for cs in code_skills:
                cs_lower = cs.lower()
                if skill_lower == cs_lower:
                    code_source = f"GitHub: {cs} detected"
                    if match_type == "none":
                        match_type, candidate_skill = "exact", cs
                        evidence, confidence = code_source, 90
                    else:
                        # Resume + GitHub 이중 확인 → confidence 상향
                        evidence = f"{resume_source} + {code_source}"
                        confidence = min(100, confidence + 5)
                    break
                elif len(cs_lower) >= 3 and cs_lower in skill_lower:
                    code_source = f"GitHub: {cs} (partial)"
                    if match_type == "none":
                        match_type, candidate_skill = "partial", cs
                        evidence, confidence = code_source, 65
                    elif resume_source:
                        evidence = f"{resume_source} + {code_source}"
                    break
                elif len(skill_lower) >= 3 and skill_lower in cs_lower:
                    code_source = f"GitHub: {cs} (related)"
                    if match_type == "none":
                        match_type, candidate_skill = "partial", cs
                        evidence, confidence = code_source, 60
                    elif resume_source:
                        evidence = f"{resume_source} + {code_source}"
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
    experience_level: str = "미들",
    linkedin_profile: dict | None = None,
    candidate_profile: dict | None = None,
) -> dict:
    """Deep Analysis 생성

    Args:
        jd_analysis: JD 분석 결과
        code_analysis: 코드 분석 결과 (optional)
        document_analysis: 문서 분석 결과
        job_id: Job ID (observability용)
        output_language: 출력 언어
        experience_level: 경험 레벨 (CTO/VP, 시니어, 미들, 주니어, 신입)
        linkedin_profile: LinkedIn 프로필 데이터 (optional)

    Returns:
        DeepAnalysis 데이터 (Evidence-Based Scoring 적용)
    """
    logger.info(f"Generating Deep Analysis for job_id={job_id} (level={experience_level})")
    activity.heartbeat()

    # 1. 5축 레이더 점수 계산 (LLM 우선, 규칙 기반 fallback)
    # LLM 결과도 결정론적 공식 기반 ±15% 범위로 바운딩
    score_sources = []
    llm_radar = await _llm_calculate_radar_scores(jd_analysis, code_analysis, document_analysis, output_language, job_id=job_id)
    if llm_radar:
        radar_candidate, radar_required, axis_sources, llm_reasoning = llm_radar
        # human_sources 가져오기 (formula_radar에서)
        from app.services.scoring_formulas import calculate_radar_scores as _formula_radar_fn
        _hr = _formula_radar_fn(
            jd_analysis, code_analysis or {}, document_analysis,
            experience_level, linkedin_profile=linkedin_profile,
            output_language=output_language,
            candidate_profile=candidate_profile,
        )
        # 비개발자 친화 human_sources 우선 사용 (Issue #245)
        if _hr.human_sources:
            score_sources.extend(_hr.human_sources)
        else:
            for i, src in enumerate(axis_sources):
                axis_name = ["role_fit", "technical", "execution", "communication", "code_quality"][i] if i < 5 else f"axis_{i}"
                llm_note = llm_reasoning.get(axis_name, "")
                combined = f"{src} | LLM: {llm_note}" if llm_note else f"{src} | LLM-bounded"
                score_sources.append(combined)
    else:
        radar_candidate, radar_required, axis_sources, confidence, human_sources = _calculate_radar_scores(
            jd_analysis, code_analysis, document_analysis, experience_level,
            candidate_profile=candidate_profile,
        )
        # human_sources 우선 사용 (Issue #245)
        if human_sources:
            score_sources.extend(human_sources)
        else:
            score_sources.extend(axis_sources)
    activity.heartbeat()

    # 2. Engineering DNA — JIT-16: 프론트엔드에서 제거됨, 빈 리스트 반환
    engineering_dna: list = []
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

    # 5. 전체 매칭 점수 계산 (Evidence-Based Weighted Composite)
    from app.services.scoring_formulas import (
        calculate_overall_match,
        calculate_code_quality_score,
        classify_experience_level,
        calculate_data_confidence,
        extract_code_stats,
    )

    # 스킬 매칭 평균 — JD 카테고리 가중 (Issue #245)
    # 필수 스킬의 exact match가 우대 스킬의 partial match보다 높은 가중치
    skill_match_avg = 0
    if skill_table:
        jd_req_map = {}
        for req in jd_analysis.get("requirements", []):
            s = req.get("skill", "").lower()
            if s:
                jd_req_map[s] = req.get("category", "우대")

        total_w = 0.0
        weighted_sum = 0.0
        for row in skill_table:
            cat = jd_req_map.get(row.skill.lower(), "우대")
            w = 1.0 if cat in ("필수", "required", "must") else 0.5
            weighted_sum += row.confidence * w
            total_w += w
        skill_match_avg = int(weighted_sum / max(total_w, 0.001))

    # 코드 품질 점수 (repositories에서 stats 집계)
    quality_metrics, code_stats = extract_code_stats(code_analysis)
    cq = calculate_code_quality_score(quality_metrics, code_stats)

    # 경험 적합도
    profile = document_analysis.get("profile", {})
    exp_years = profile.get("experience_years", 0) or 0
    _, exp_score = classify_experience_level(exp_years)

    # JD 매칭 점수
    jd_match = document_analysis.get("jd_match_score", 0.5)

    overall_result = calculate_overall_match(
        skill_match_avg, cq.score, exp_score, jd_match,
        output_language=output_language,
    )
    overall_match = overall_result.score
    # human_source 우선 사용 (Issue #245)
    score_sources.append(overall_result.human_source or f"overall_match: {overall_result.source}")

    # 6. 데이터 신뢰도 계산
    has_linkedin = linkedin_profile is not None and bool(linkedin_profile)
    linkedin_positions = 0
    if has_linkedin:
        experiences = linkedin_profile.get("experiences") or linkedin_profile.get("experience") or []
        linkedin_positions = len(experiences) if isinstance(experiences, list) else 0

    has_resume = bool(
        profile.get("skills")
        or profile.get("experiences")
        or profile.get("experience_years")
    )

    github_commits = code_stats.get("total_commits", 0) if code_stats else 0
    data_conf_tier, data_conf_score = calculate_data_confidence(
        has_github=code_analysis is not None and github_commits > 0,
        has_linkedin=has_linkedin,
        has_resume=has_resume,
        github_commits=github_commits,
        linkedin_positions=linkedin_positions,
    )

    deep_analysis = DeepAnalysis(
        radar_candidate=radar_candidate,
        radar_required=radar_required,
        engineering_dna=engineering_dna,
        risk_flags=risk_flags,
        skill_table=skill_table,
        overall_match=overall_match,
        score_sources=score_sources,
        data_confidence=data_conf_tier,
        data_confidence_score=data_conf_score,
    )

    # === Post-processing 품질 검증 ===

    # 레이더 점수 축별 근거 커버리지 검증
    llm_sourced = sum(1 for s in score_sources if "LLM:" in s and "formula-based" not in s)
    formula_only = sum(1 for s in score_sources if "formula-based" in s)
    if score_sources:
        reasoning_coverage = round(llm_sourced / min(5, len(score_sources)) * 100, 1)
        logger.info(f"Radar reasoning coverage: {reasoning_coverage}% LLM-sourced ({llm_sourced}/5), {formula_only} formula-fallback")
        if formula_only >= 3:
            logger.warning(f"Radar reasoning: {formula_only}/5 axes fell back to formula-only — LLM reasoning quality low")

    # 스킬 테이블 품질 검증
    if skill_table:
        no_evidence = sum(1 for r in skill_table if not r.evidence or r.evidence in ("No evidence", "—", ""))
        zero_conf = sum(1 for r in skill_table if r.confidence == 0)
        type_conf_mismatch = sum(
            1 for r in skill_table
            if r.type == "exact" and r.confidence < 70
            or r.type == "none" and r.confidence > 30
        )
        logger.info(f"Skill table: {len(skill_table)} rows, no_evidence={no_evidence}, zero_conf={zero_conf}, type_conf_mismatch={type_conf_mismatch}")
        if no_evidence > len(skill_table) // 2:
            logger.warning(f"Skill table: {no_evidence}/{len(skill_table)} rows lack evidence")
        if type_conf_mismatch > 0:
            logger.warning(f"Skill table: {type_conf_mismatch} rows have type↔confidence mismatch (e.g., exact but <70%)")

    logger.info(
        f"Deep Analysis generated: overall_match={overall_match}% "
        f"(confidence={data_conf_tier}/{data_conf_score})"
    )
    return deep_analysis.model_dump()
