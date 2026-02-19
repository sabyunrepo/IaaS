"""
LinkedIn 프로필 도메인 모델 테스트

TDD: 테스트 먼저 작성 후 모델 구현
"""
import pytest
from pydantic import ValidationError

from domain.identity.linkedin_models import (
    LinkedInCertification,
    LinkedInEducation,
    LinkedInExperience,
    LinkedInProfile,
    LinkedInSkill,
)
from domain.identity.linkedin_normalizer import normalize_linkedin_profile


# ---------------------------------------------------------------------------
# LinkedInExperience
# ---------------------------------------------------------------------------


class TestLinkedInExperience:
    def test_creation(self):
        exp = LinkedInExperience(
            company="Kakao",
            title="Backend Engineer",
            duration_months=24,
        )
        assert exp.company == "Kakao"
        assert exp.title == "Backend Engineer"
        assert exp.duration_months == 24
        assert exp.description == ""
        assert exp.is_current is False
        assert exp.start_date is None
        assert exp.end_date is None
        assert exp.location is None

    def test_full_creation(self):
        exp = LinkedInExperience(
            company="Naver",
            title="ML Engineer",
            duration_months=12,
            start_date="2023-01",
            end_date="2024-01",
            description="LLM 서비스 개발",
            location="Seoul, Korea",
            is_current=False,
        )
        assert exp.start_date == "2023-01"
        assert exp.end_date == "2024-01"
        assert exp.description == "LLM 서비스 개발"
        assert exp.location == "Seoul, Korea"

    def test_negative_duration_rejected(self):
        with pytest.raises(ValidationError):
            LinkedInExperience(
                company="Kakao",
                title="Backend Engineer",
                duration_months=-1,
            )

    def test_zero_duration_allowed(self):
        exp = LinkedInExperience(
            company="Kakao",
            title="Intern",
            duration_months=0,
        )
        assert exp.duration_months == 0

    def test_is_current_true(self):
        exp = LinkedInExperience(
            company="Line",
            title="Senior Engineer",
            duration_months=18,
            is_current=True,
        )
        assert exp.is_current is True

    def test_missing_company_rejected(self):
        with pytest.raises(ValidationError):
            LinkedInExperience(title="Engineer", duration_months=12)  # type: ignore[call-arg]

    def test_missing_title_rejected(self):
        with pytest.raises(ValidationError):
            LinkedInExperience(company="Kakao", duration_months=12)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# LinkedInEducation
# ---------------------------------------------------------------------------


class TestLinkedInEducation:
    def test_creation_minimal(self):
        edu = LinkedInEducation(school="KAIST")
        assert edu.school == "KAIST"
        assert edu.degree is None
        assert edu.field_of_study is None
        assert edu.start_year is None
        assert edu.end_year is None

    def test_creation_full(self):
        edu = LinkedInEducation(
            school="Seoul National University",
            degree="Bachelor of Science",
            field_of_study="Computer Science",
            start_year=2018,
            end_year=2022,
        )
        assert edu.degree == "Bachelor of Science"
        assert edu.field_of_study == "Computer Science"
        assert edu.start_year == 2018
        assert edu.end_year == 2022

    def test_missing_school_rejected(self):
        with pytest.raises(ValidationError):
            LinkedInEducation(degree="B.S.")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# LinkedInSkill
# ---------------------------------------------------------------------------


class TestLinkedInSkill:
    def test_creation_minimal(self):
        skill = LinkedInSkill(name="Python")
        assert skill.name == "Python"
        assert skill.endorsement_count == 0

    def test_creation_with_endorsements(self):
        skill = LinkedInSkill(name="Kubernetes", endorsement_count=42)
        assert skill.endorsement_count == 42

    def test_negative_endorsements_rejected(self):
        with pytest.raises(ValidationError):
            LinkedInSkill(name="Python", endorsement_count=-1)

    def test_missing_name_rejected(self):
        with pytest.raises(ValidationError):
            LinkedInSkill(endorsement_count=10)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# LinkedInCertification
# ---------------------------------------------------------------------------


class TestLinkedInCertification:
    def test_creation_minimal(self):
        cert = LinkedInCertification(name="AWS SAA", issuer="Amazon")
        assert cert.name == "AWS SAA"
        assert cert.issuer == "Amazon"
        assert cert.issue_date is None
        assert cert.credential_url is None

    def test_creation_full(self):
        cert = LinkedInCertification(
            name="CKA",
            issuer="CNCF",
            issue_date="2024-03",
            credential_url="https://cred.example.com/abc123",
        )
        assert cert.issue_date == "2024-03"
        assert cert.credential_url == "https://cred.example.com/abc123"

    def test_missing_name_rejected(self):
        with pytest.raises(ValidationError):
            LinkedInCertification(issuer="Amazon")  # type: ignore[call-arg]

    def test_missing_issuer_rejected(self):
        with pytest.raises(ValidationError):
            LinkedInCertification(name="AWS SAA")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# LinkedInProfile
# ---------------------------------------------------------------------------


class TestLinkedInProfile:
    def _make_experience(
        self,
        company: str = "Kakao",
        title: str = "Engineer",
        duration_months: int = 12,
        is_current: bool = False,
        start_date: str | None = None,
    ) -> LinkedInExperience:
        return LinkedInExperience(
            company=company,
            title=title,
            duration_months=duration_months,
            is_current=is_current,
            start_date=start_date,
        )

    def test_creation_minimal(self):
        profile = LinkedInProfile(
            name="Alice Kim",
            profile_url="https://linkedin.com/in/alicekim",
        )
        assert profile.name == "Alice Kim"
        assert profile.profile_url == "https://linkedin.com/in/alicekim"
        assert profile.headline is None
        assert profile.location is None
        assert profile.summary == ""
        assert profile.experiences == []
        assert profile.educations == []
        assert profile.skills == []
        assert profile.certifications == []

    def test_creation_full(self):
        exp = self._make_experience(duration_months=24, is_current=True)
        edu = LinkedInEducation(school="KAIST", degree="M.S.", field_of_study="CS")
        skill = LinkedInSkill(name="Python", endorsement_count=99)
        cert = LinkedInCertification(name="CKA", issuer="CNCF")

        profile = LinkedInProfile(
            name="Bob Lee",
            headline="Senior Backend Engineer",
            location="Seoul, Korea",
            summary="12년 경력의 백엔드 엔지니어",
            profile_url="https://linkedin.com/in/boblee",
            experiences=[exp],
            educations=[edu],
            skills=[skill],
            certifications=[cert],
        )
        assert profile.headline == "Senior Backend Engineer"
        assert len(profile.experiences) == 1
        assert len(profile.educations) == 1
        assert len(profile.skills) == 1
        assert len(profile.certifications) == 1

    def test_total_experience_months_empty(self):
        profile = LinkedInProfile(
            name="Alice Kim",
            profile_url="https://linkedin.com/in/alicekim",
        )
        assert profile.total_experience_months == 0

    def test_total_experience_months_single(self):
        exp = self._make_experience(duration_months=18)
        profile = LinkedInProfile(
            name="Alice Kim",
            profile_url="https://linkedin.com/in/alicekim",
            experiences=[exp],
        )
        assert profile.total_experience_months == 18

    def test_total_experience_months_multiple(self):
        exp1 = self._make_experience(duration_months=24)
        exp2 = self._make_experience(company="Naver", duration_months=36)
        profile = LinkedInProfile(
            name="Alice Kim",
            profile_url="https://linkedin.com/in/alicekim",
            experiences=[exp1, exp2],
        )
        assert profile.total_experience_months == 60

    def test_current_company_found(self):
        exp_old = self._make_experience(company="Kakao", duration_months=24, is_current=False)
        exp_current = self._make_experience(
            company="Naver", duration_months=6, is_current=True, start_date="2024-01"
        )
        profile = LinkedInProfile(
            name="Alice Kim",
            profile_url="https://linkedin.com/in/alicekim",
            experiences=[exp_current, exp_old],
        )
        assert profile.current_company == "Naver"

    def test_current_company_none_when_no_current(self):
        exp = self._make_experience(company="Kakao", duration_months=24, is_current=False)
        profile = LinkedInProfile(
            name="Alice Kim",
            profile_url="https://linkedin.com/in/alicekim",
            experiences=[exp],
        )
        assert profile.current_company is None

    def test_current_company_empty_experiences(self):
        profile = LinkedInProfile(
            name="Alice Kim",
            profile_url="https://linkedin.com/in/alicekim",
        )
        assert profile.current_company is None

    def test_missing_name_rejected(self):
        with pytest.raises(ValidationError):
            LinkedInProfile(profile_url="https://linkedin.com/in/x")  # type: ignore[call-arg]

    def test_missing_profile_url_rejected(self):
        with pytest.raises(ValidationError):
            LinkedInProfile(name="Alice Kim")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# normalize_linkedin_profile
# ---------------------------------------------------------------------------


class TestNormalizeLinkedInProfile:
    def _make_raw(self) -> dict:
        return {
            "name": "Charlie Park",
            "headline": "AI Engineer",
            "location": "Busan, Korea",
            "summary": "AI 분야 8년 경력",
            "profile_url": "https://linkedin.com/in/charliepark",
            "experiences": [
                {
                    "company": "Kakao Brain",
                    "title": "Research Engineer",
                    "start_date": "2022-03",
                    "end_date": None,
                    "description": "LLM 파인튜닝",
                    "location": "Seoul",
                },
                {
                    "company": "Naver Clova",
                    "title": "ML Engineer",
                    "start_date": "2019-01",
                    "end_date": "2022-02",
                    "description": "OCR 모델 개발",
                    "location": "Seongnam",
                },
            ],
            "educations": [
                {
                    "school": "POSTECH",
                    "degree": "M.S.",
                    "field_of_study": "Computer Science",
                    "start_year": 2017,
                    "end_year": 2019,
                }
            ],
            "skills": [
                {"name": "PyTorch", "endorsement_count": 55},
                {"name": "Python", "endorsement_count": 120},
            ],
            "certifications": [
                {
                    "name": "Google ML Engineer",
                    "issuer": "Google",
                    "issue_date": "2023-06",
                    "credential_url": "https://credential.example.com/abc",
                }
            ],
        }

    def test_full_data_normalization(self):
        raw = self._make_raw()
        profile = normalize_linkedin_profile(raw)

        assert isinstance(profile, LinkedInProfile)
        assert profile.name == "Charlie Park"
        assert profile.headline == "AI Engineer"
        assert profile.location == "Busan, Korea"
        assert len(profile.experiences) == 2
        assert len(profile.educations) == 1
        assert len(profile.skills) == 2
        assert len(profile.certifications) == 1

    def test_minimal_data_normalization(self):
        raw = {
            "name": "Dave Oh",
            "profile_url": "https://linkedin.com/in/daveoh",
        }
        profile = normalize_linkedin_profile(raw)
        assert profile.name == "Dave Oh"
        assert profile.experiences == []
        assert profile.educations == []
        assert profile.skills == []
        assert profile.certifications == []
        assert profile.total_experience_months == 0

    def test_duration_calculation_start_and_end(self):
        raw = {
            "name": "Eve Choi",
            "profile_url": "https://linkedin.com/in/evechoi",
            "experiences": [
                {
                    "company": "Coupang",
                    "title": "SRE",
                    "start_date": "2021-01",
                    "end_date": "2023-01",
                }
            ],
        }
        profile = normalize_linkedin_profile(raw)
        # 2021-01 → 2023-01 = 24 months
        assert profile.experiences[0].duration_months == 24

    def test_current_job_detection(self):
        raw = {
            "name": "Frank Yoon",
            "profile_url": "https://linkedin.com/in/frankyoon",
            "experiences": [
                {
                    "company": "Toss",
                    "title": "Platform Engineer",
                    "start_date": "2023-06",
                    "end_date": None,
                }
            ],
        }
        profile = normalize_linkedin_profile(raw)
        exp = profile.experiences[0]
        assert exp.is_current is True
        assert profile.current_company == "Toss"

    def test_past_job_not_current(self):
        raw = {
            "name": "Grace Jang",
            "profile_url": "https://linkedin.com/in/gracejang",
            "experiences": [
                {
                    "company": "Krafton",
                    "title": "GameDev",
                    "start_date": "2020-01",
                    "end_date": "2022-12",
                }
            ],
        }
        profile = normalize_linkedin_profile(raw)
        exp = profile.experiences[0]
        assert exp.is_current is False
        assert profile.current_company is None

    def test_no_start_date_not_current(self):
        raw = {
            "name": "Hana Kim",
            "profile_url": "https://linkedin.com/in/hanakim",
            "experiences": [
                {
                    "company": "Daum",
                    "title": "Dev",
                    "start_date": None,
                    "end_date": None,
                }
            ],
        }
        profile = normalize_linkedin_profile(raw)
        exp = profile.experiences[0]
        # is_current = end is None AND start is not None → False here (start is None)
        assert exp.is_current is False
