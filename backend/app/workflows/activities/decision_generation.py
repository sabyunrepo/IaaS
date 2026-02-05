"""
backend/app/workflows/activities/decision_generation.py
Decision Support 생성 Activity
"""
import logging
from typing import Any

from temporalio import activity

from app.core.observability import observe_activity
from app.models.decision import (
    DecisionSupport, DecisionSummary, InterviewerGuideTips,
    JDCompetencyWeight, ResumeTip, CoverLetterInsight,
)

logger = logging.getLogger(__name__)


def _extract_decision_summary(
    candidate_summary: dict,
    jd_analysis: dict,
    document_analysis: dict,
) -> DecisionSummary:
    """후보자 요약에서 Decision Summary 추출"""
    profile = document_analysis.get("profile", {})

    # 경력 요약
    experiences = profile.get("experiences", [])
    experience_years = profile.get("experience_years", 0)
    experience_str = f"{experience_years}년"
    if experiences:
        latest_exp = experiences[0] if experiences else {}
        company = latest_exp.get("company", "")
        role = latest_exp.get("role", latest_exp.get("title", ""))
        if company and role:
            experience_str = f"{experience_years}년 ({role} @ {company})"

    # JD 매칭 레벨
    jd_match_score = document_analysis.get("jd_match_score", 0.5)
    if jd_match_score >= 0.8:
        jd_match = "높음"
    elif jd_match_score >= 0.6:
        jd_match = "중간"
    else:
        jd_match = "낮음"

    # 레벨 추정
    level = "Mid"
    if experience_years >= 7:
        level = "Senior"
    elif experience_years >= 10:
        level = "Lead"
    elif experience_years <= 2:
        level = "Junior"

    # 강점 추출
    strengths = []
    key_skills = profile.get("skills", [])[:3]
    for skill in key_skills:
        strengths.append(f"{skill} (이력서)")

    # Code analysis에서 추가 강점
    if isinstance(candidate_summary, dict):
        cs_strengths = candidate_summary.get("key_strengths", [])
        if isinstance(cs_strengths, list):
            for s in cs_strengths[:2]:
                if isinstance(s, dict):
                    strength_text = s.get("strength", "")
                    evidence = s.get("evidence", {})
                    source = "Multi-source" if isinstance(evidence, dict) and len(evidence) > 1 else "이력서"
                    if strength_text:
                        strengths.append(f"{strength_text} ({source})")
                elif isinstance(s, str):
                    strengths.append(s)

    # 우려사항 추출
    concerns = []
    risk_flags = profile.get("areas_to_probe", [])
    for flag in risk_flags[:3]:
        if isinstance(flag, str):
            concerns.append(flag)
        elif isinstance(flag, dict):
            concerns.append(flag.get("concern", flag.get("area", "")))

    return DecisionSummary(
        experience=experience_str,
        jd_match=jd_match,
        level=level,
        strengths=strengths[:5],
        concerns=concerns[:3],
    )


def _build_interviewer_tips(
    questions: list[dict],
    document_analysis: dict,
    jd_analysis: dict,
) -> InterviewerGuideTips:
    """면접관 팁 구성"""
    # 시간 배분 계산
    category_counts = {}
    for q in questions:
        cat = q.get("category", "기타")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    total_time = 60  # 기본 60분
    time_allocation = {}
    for cat, count in category_counts.items():
        cat_time = int((count / len(questions)) * total_time) if questions else 10
        time_allocation[cat] = f"{cat_time}분"

    # 면접 진행 순서
    category_order = ["role_fit", "technical_depth", "execution_ownership", "communication", "risk_flags"]
    existing_cats = [c for c in category_order if c in category_counts]
    interview_flow = " → ".join(
        f"{cat}({time_allocation.get(cat, '10분')})" for cat in existing_cats
    )

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
                area=f"{role} @ {company}",
                detail=f"해당 경력 관련 구체적 성과와 역할 확인",
                source="이력서",
            ))

    # 커버레터 인사이트 (있는 경우)
    cover_letter_insights = []
    cover_letter = document_analysis.get("cover_letter_analysis", {})
    if cover_letter:
        motivations = cover_letter.get("motivations", [])
        for m in motivations[:2]:
            if isinstance(m, str):
                cover_letter_insights.append(CoverLetterInsight(
                    claim=m,
                    verify_with="관련 경험 구체적 사례 요청",
                ))

    # Red flags
    red_flags = []
    areas_to_probe = profile.get("areas_to_probe", [])
    for area in areas_to_probe[:3]:
        if isinstance(area, str):
            red_flags.append(area)
        elif isinstance(area, dict):
            red_flags.append(area.get("concern", area.get("area", "")))

    # Positive signals
    positive_signals = [
        "구체적 수치 기반 성과 설명",
        "실패 경험과 학습 내용 공유",
        "팀 협업 사례 구체적 언급",
    ]

    return InterviewerGuideTips(
        interview_flow=interview_flow,
        time_allocation=time_allocation,
        resume_based_tips=resume_tips[:5],
        cover_letter_insights=cover_letter_insights[:3],
        red_flags_to_watch=red_flags[:5],
        positive_signals=positive_signals,
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
        skill = req.get("skill", req.get("text", f"역량{i+1}"))
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

    # 1. 후보자 요약 생성
    summary = _extract_decision_summary(candidate_summary, jd_analysis, document_analysis)
    activity.heartbeat()

    # 2. 면접관 가이드 팁 생성
    interviewer_guide = _build_interviewer_tips(questions, document_analysis, jd_analysis)
    activity.heartbeat()

    # 3. JD 역량 매핑
    jd_competency_map = _map_jd_competencies(jd_analysis, questions)

    decision_support = DecisionSupport(
        summary=summary,
        interviewer_guide=interviewer_guide,
        jd_competency_map=jd_competency_map,
    )

    logger.info(f"Decision Support generated with {len(jd_competency_map)} competencies mapped")
    return decision_support.model_dump()
