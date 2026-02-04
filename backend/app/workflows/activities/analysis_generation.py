"""
backend/app/workflows/activities/analysis_generation.py
Deep Analysis 생성 Activity
"""
import logging
from typing import Any

from temporalio import activity

from app.core.observability import observe_activity
from app.models.deep_analysis import (
    DeepAnalysis, EngineeringDNAItem, RiskFlag, SkillMatchRow,
)

logger = logging.getLogger(__name__)


def _calculate_radar_scores(
    jd_analysis: dict,
    code_analysis: dict | None,
    document_analysis: dict,
) -> tuple[list[int], list[int]]:
    """5축 레이더 점수 계산

    축: [role_fit, technical, execution, communication, risk]
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

    # Risk: 리스크 플래그 기반 (낮을수록 좋음)
    risk_flags = code_analysis.get("risk_flags", []) if code_analysis else []
    candidate_scores[4] = max(30, 100 - len(risk_flags) * 15)

    return candidate_scores, required_scores


def _analyze_engineering_dna(code_analysis: dict | None) -> list[EngineeringDNAItem]:
    """Engineering DNA 분석"""
    items = []

    if not code_analysis:
        items.append(EngineeringDNAItem(
            label="코드 분석",
            value=0,
            display="미확인",
            color="slate",
            note="GitHub 데이터가 제공되지 않았습니다",
        ))
        return items

    quality = code_analysis.get("quality_metrics", {})

    # 테스트 커버리지
    test_coverage = quality.get("test_coverage", 0)
    items.append(EngineeringDNAItem(
        label="테스트 커버리지",
        value=test_coverage,
        display=f"{test_coverage}%",
        color="emerald" if test_coverage >= 70 else "amber" if test_coverage >= 40 else "red",
    ))

    # 문서화 품질
    doc_score = quality.get("documentation_score", 0)
    doc_display = "우수" if doc_score >= 80 else "보통" if doc_score >= 50 else "미흡"
    items.append(EngineeringDNAItem(
        label="문서화 품질",
        value=doc_score,
        display=doc_display,
        color="blue" if doc_score >= 80 else "amber" if doc_score >= 50 else "red",
    ))

    # IaC 사용 여부
    iac_score = quality.get("iac_score", 0)
    items.append(EngineeringDNAItem(
        label="IaC",
        value=iac_score,
        display="확인됨" if iac_score >= 50 else "미확인",
        color="emerald" if iac_score >= 50 else "red",
        note="Terraform, Ansible 같은 자동화 도구 사용 흔적이 GitHub에서 발견되지 않았습니다" if iac_score < 50 else None,
        tooltip="서버 환경을 코드 파일로 관리하는 방식",
    ))

    # 코드 복잡도
    complexity = quality.get("complexity_score", 50)
    complexity_display = "낮음" if complexity <= 30 else "보통" if complexity <= 70 else "높음"
    items.append(EngineeringDNAItem(
        label="코드 복잡도",
        value=complexity,
        display=complexity_display,
        color="emerald" if complexity <= 30 else "amber" if complexity <= 70 else "red",
    ))

    return items


def _extract_risk_flags(
    code_analysis: dict | None,
    document_analysis: dict,
) -> list[RiskFlag]:
    """리스크 플래그 추출"""
    flags = []

    # 코드 분석 기반 리스크
    if code_analysis:
        code_risks = code_analysis.get("risk_flags", [])
        for risk in code_risks:
            if isinstance(risk, dict):
                flags.append(RiskFlag(
                    label=risk.get("label", "리스크"),
                    detail=risk.get("detail", risk.get("description", "")),
                ))
            elif isinstance(risk, str):
                flags.append(RiskFlag(label="주의", detail=risk))

    # 문서 분석 기반 리스크
    profile = document_analysis.get("profile", {})
    areas_to_probe = profile.get("areas_to_probe", [])
    for area in areas_to_probe[:3]:  # 상위 3개
        if isinstance(area, str):
            flags.append(RiskFlag(label="확인 필요", detail=area))

    return flags[:5]  # 최대 5개


def _build_skill_table(
    jd_analysis: dict,
    code_analysis: dict | None,
    document_analysis: dict,
) -> list[SkillMatchRow]:
    """스킬 매칭 테이블 생성"""
    rows = []

    jd_requirements = jd_analysis.get("requirements", [])
    candidate_skills = document_analysis.get("profile", {}).get("skills", [])
    code_skills = code_analysis.get("tech_stack", []) if code_analysis else []

    all_candidate_skills = set(s.lower() for s in candidate_skills + code_skills)

    for req in jd_requirements[:6]:  # 상위 6개
        skill = req.get("skill", req.get("text", ""))
        skill_lower = skill.lower()

        # 매칭 타입 결정
        match_type = "none"
        candidate_skill = "—"
        evidence = "증거 없음"
        confidence = 0

        for cs in candidate_skills:
            if skill_lower == cs.lower():
                match_type = "exact"
                candidate_skill = cs
                evidence = "이력서"
                confidence = 95
                break
            elif skill_lower in cs.lower() or cs.lower() in skill_lower:
                match_type = "similar"
                candidate_skill = cs
                evidence = "이력서"
                confidence = 75
                break

        # 코드 분석에서 확인
        if match_type == "none" and code_analysis:
            for cs in code_skills:
                if skill_lower == cs.lower():
                    match_type = "exact"
                    candidate_skill = cs
                    evidence = "GitHub"
                    confidence = 90
                    break
                elif skill_lower in cs.lower() or cs.lower() in skill_lower:
                    match_type = "partial"
                    candidate_skill = cs
                    evidence = "GitHub"
                    confidence = 60
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

    # 1. 5축 레이더 점수 계산
    radar_candidate, radar_required = _calculate_radar_scores(
        jd_analysis, code_analysis, document_analysis
    )
    activity.heartbeat()

    # 2. Engineering DNA 분석
    engineering_dna = _analyze_engineering_dna(code_analysis)
    activity.heartbeat()

    # 3. 리스크 플래그 추출
    risk_flags = _extract_risk_flags(code_analysis, document_analysis)
    activity.heartbeat()

    # 4. 스킬 매칭 테이블 생성
    skill_table = _build_skill_table(jd_analysis, code_analysis, document_analysis)

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
