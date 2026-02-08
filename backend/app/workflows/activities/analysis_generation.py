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
        formula_radar = _formula_radar(jd_analysis, code_analysis or {}, document_analysis)
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

        # 실제 코드 메트릭으로 note 검증/보강
        actual_metrics = code_analysis.get("quality_metrics", {})
        metric_map = {
            "test": f"test_coverage: {actual_metrics.get('test_coverage', 0)}% (GitHub)",
            "doc": f"documentation_score: {actual_metrics.get('documentation_score', 0)}% (GitHub)",
            "iac": f"iac_score: {actual_metrics.get('iac_score', 0)}% (GitHub)",
            "complex": f"complexity_score: {actual_metrics.get('complexity_score', 0)} (GitHub)",
        }

        items = []
        for item in result[:6]:
            if not isinstance(item, dict):
                continue
            color = sanitize_color(item.get("color", "slate"))
            note = item.get("note")
            # LLM note가 없거나 빈 경우, 실제 메트릭에서 보강
            label_lower = item.get("label", "").lower()
            if not note:
                for key, metric_note in metric_map.items():
                    if key in label_lower:
                        note = metric_note
                        break
            items.append(EngineeringDNAItem(
                label=item.get("label", ""),
                value=max(0, min(100, int(item.get("value", 0)))),
                display=item.get("display", ""),
                color=color,
                note=note,
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
    experience_level: str = "미들",
) -> tuple[list[int], list[int], list[str], str]:
    """5축 레이더 점수 계산 (Evidence-Based Scoring)

    축: [role_fit, technical, execution, communication, code_quality]

    산업 표준 기반 결정론적 공식 사용:
    - McCabe (1976): Cyclomatic Complexity
    - SFIA v9: Experience level classification
    - SonarQube SQALE: Code quality composite
    - Bird et al. (2011): Code ownership & stability

    Returns:
        (candidate_scores, required_scores, sources, confidence)
    """
    from app.services.scoring_formulas import calculate_radar_scores as _formula_radar

    radar = _formula_radar(jd_analysis, code_analysis, document_analysis, experience_level)
    return radar.candidate, radar.required, radar.sources, radar.confidence


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
        note=f"test_coverage: {test_coverage}% (GitHub)",
    ))

    # 문서화 품질
    doc_score = quality.get("documentation_score", 0)
    doc_display = _t("excellent", lang) if doc_score >= 80 else _t("moderate", lang) if doc_score >= 50 else _t("poor", lang)
    items.append(EngineeringDNAItem(
        label=_t("doc_quality", lang),
        value=doc_score,
        display=doc_display,
        color="blue" if doc_score >= 80 else "amber" if doc_score >= 50 else "red",
        note=f"documentation_score: {doc_score}% (GitHub)",
    ))

    # IaC 사용 여부
    iac_score = quality.get("iac_score", 0)
    items.append(EngineeringDNAItem(
        label=_t("iac", lang),
        value=iac_score,
        display=_t("confirmed", lang) if iac_score >= 50 else _t("unconfirmed", lang),
        color="emerald" if iac_score >= 50 else "red",
        note=f"iac_score: {iac_score}% (GitHub)" if iac_score >= 50 else _t("iac_not_found", lang),
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
        note=f"complexity_score: {complexity} (GitHub)",
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
        # 축별 공식 근거 + LLM 추론 결합
        for i, src in enumerate(axis_sources):
            axis_name = ["role_fit", "technical", "execution", "communication", "code_quality"][i] if i < 5 else f"axis_{i}"
            llm_note = llm_reasoning.get(axis_name, "")
            combined = f"{src} | LLM: {llm_note}" if llm_note else f"{src} | LLM-bounded"
            score_sources.append(combined)
    else:
        radar_candidate, radar_required, axis_sources, confidence = _calculate_radar_scores(
            jd_analysis, code_analysis, document_analysis, experience_level
        )
        score_sources.extend(axis_sources)
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

    # 5. 전체 매칭 점수 계산 (Evidence-Based Weighted Composite)
    from app.services.scoring_formulas import (
        calculate_overall_match,
        calculate_code_quality_score,
        classify_experience_level,
        calculate_data_confidence,
        extract_code_stats,
    )

    # 스킬 매칭 평균
    skill_match_avg = 0
    if skill_table:
        skill_match_avg = sum(row.confidence for row in skill_table) // len(skill_table)

    # 코드 품질 점수 (repositories에서 stats 집계)
    quality_metrics, code_stats = extract_code_stats(code_analysis)
    cq = calculate_code_quality_score(quality_metrics, code_stats)

    # 경험 적합도
    profile = document_analysis.get("profile", {})
    exp_years = profile.get("experience_years", 0) or 0
    _, exp_score = classify_experience_level(exp_years)

    # JD 매칭 점수
    jd_match = document_analysis.get("jd_match_score", 0.5)

    overall_result = calculate_overall_match(skill_match_avg, cq.score, exp_score, jd_match)
    overall_match = overall_result.score
    score_sources.append(f"overall_match: {overall_result.source}")

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

    logger.info(
        f"Deep Analysis generated: overall_match={overall_match}% "
        f"(confidence={data_conf_tier}/{data_conf_score})"
    )
    return deep_analysis.model_dump()
