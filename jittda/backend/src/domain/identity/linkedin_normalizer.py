"""
LinkedIn 프로필 정규화 함수

BrightData raw JSON → LinkedInProfile 도메인 모델 변환.
순수 함수, 외부 의존성 없음 (stdlib datetime만 허용).
"""
from datetime import date

from domain.identity.linkedin_models import (
    LinkedInCertification,
    LinkedInEducation,
    LinkedInExperience,
    LinkedInProfile,
    LinkedInSkill,
)


def _calc_duration(start: str | None, end: str | None) -> int:
    """
    "YYYY-MM" 형식 날짜를 개월 수로 변환.

    end가 None이면 오늘 날짜를 사용한다.
    start가 None이면 0을 반환한다.
    """
    if start is None:
        return 0

    start_year, start_month = map(int, start.split("-"))

    if end is None:
        today = date.today()
        end_year, end_month = today.year, today.month
    else:
        end_year, end_month = map(int, end.split("-"))

    months = (end_year - start_year) * 12 + (end_month - start_month)
    return max(months, 0)


def normalize_linkedin_profile(raw_data: dict) -> LinkedInProfile:
    """
    BrightData raw JSON → LinkedInProfile.

    is_current 판정 기준: end_date is None AND start_date is not None
    """
    raw_experiences = raw_data.get("experiences", []) or []
    raw_educations = raw_data.get("educations", []) or []
    raw_skills = raw_data.get("skills", []) or []
    raw_certifications = raw_data.get("certifications", []) or []

    experiences: list[LinkedInExperience] = []
    for exp in raw_experiences:
        start_date = exp.get("start_date")
        end_date = exp.get("end_date")
        is_current = (end_date is None) and (start_date is not None)
        duration_months = _calc_duration(start_date, end_date)

        experiences.append(
            LinkedInExperience(
                company=exp["company"],
                title=exp["title"],
                duration_months=duration_months,
                start_date=start_date,
                end_date=end_date,
                description=exp.get("description", ""),
                location=exp.get("location"),
                is_current=is_current,
            )
        )

    educations: list[LinkedInEducation] = []
    for edu in raw_educations:
        educations.append(
            LinkedInEducation(
                school=edu["school"],
                degree=edu.get("degree"),
                field_of_study=edu.get("field_of_study"),
                start_year=edu.get("start_year"),
                end_year=edu.get("end_year"),
            )
        )

    skills: list[LinkedInSkill] = []
    for skill in raw_skills:
        skills.append(
            LinkedInSkill(
                name=skill["name"],
                endorsement_count=skill.get("endorsement_count", 0),
            )
        )

    certifications: list[LinkedInCertification] = []
    for cert in raw_certifications:
        certifications.append(
            LinkedInCertification(
                name=cert["name"],
                issuer=cert["issuer"],
                issue_date=cert.get("issue_date"),
                credential_url=cert.get("credential_url"),
            )
        )

    return LinkedInProfile(
        name=raw_data["name"],
        headline=raw_data.get("headline"),
        location=raw_data.get("location"),
        summary=raw_data.get("summary", ""),
        profile_url=raw_data["profile_url"],
        experiences=experiences,
        educations=educations,
        skills=skills,
        certifications=certifications,
    )
