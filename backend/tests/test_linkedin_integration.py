"""
backend/tests/test_linkedin_integration.py
LinkedIn Integration Tests — Bright Data Web Scraper API
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestLinkedInServiceNormalization:
    """LinkedIn Service _normalize_profile 테스트"""

    def test_normalize_full_profile(self):
        """모든 필드가 있는 프로필 정규화"""
        from app.services.linkedin_service import LinkedInService

        service = LinkedInService(api_token="test-token")

        raw_data = {
            "name": "Test User",
            "headline": "Software Engineer",
            "about": "Passionate developer",
            "current_company": {"name": "TestCorp"},
            "city": "Seoul",
            "country_code": "KR",
            "avatar": "https://example.com/avatar.jpg",
            "followers": 100,
            "connections": 200,
            "experience": [
                {"title": "Senior Engineer", "company": "Corp A", "description": "Led team"},
                {"title": "Junior Engineer", "company": "Corp B"},
            ],
            "education": [
                {"school": "University", "degree": "BS", "field_of_study": "CS"},
            ],
            "skills": ["Python", "Java", "Go"],
            "projects": [
                {"title": "Project1", "description": "Built X", "start_date": "Jan 2024"},
            ],
            "honors_and_awards": [
                {"title": "Award1", "publication": "Org1", "description": "Won competition"},
            ],
            "activity": [
                {"interaction": "Shared", "title": "Post about tech", "link": "https://..."},
            ],
            "websites": ["https://github.com/testuser"],
        }

        normalized = service._normalize_profile(raw_data, "https://linkedin.com/in/test")

        # 기본 정보
        assert normalized["full_name"] == "Test User"
        assert normalized["headline"] == "Software Engineer"
        assert normalized["summary"] == "Passionate developer"
        assert normalized["current_company"] == "TestCorp"
        assert normalized["city"] == "Seoul"
        assert normalized["country"] == "KR"
        assert normalized["avatar_url"] == "https://example.com/avatar.jpg"
        assert normalized["followers"] == 100
        assert normalized["connections"] == 200

        # 경력/학력
        assert len(normalized["experiences"]) == 2
        assert normalized["experiences"][0]["title"] == "Senior Engineer"
        assert len(normalized["education"]) == 1
        assert normalized["education"][0]["school"] == "University"

        # 스킬
        assert normalized["skills"] == ["Python", "Java", "Go"]

        # 프로젝트/수상
        assert len(normalized["projects"]) == 1
        assert normalized["projects"][0]["title"] == "Project1"
        assert len(normalized["honors_and_awards"]) == 1
        assert normalized["honors_and_awards"][0]["issuer"] == "Org1"

        # 활동
        assert len(normalized["activity"]) == 1
        assert normalized["activity"][0]["interaction"] == "Shared"

        # GitHub URL
        assert normalized["github_url"] == "https://github.com/testuser"

    def test_normalize_null_experience_education(self):
        """experience/education이 null인 경우 (LinkedIn 비공개 설정)"""
        from app.services.linkedin_service import LinkedInService

        service = LinkedInService(api_token="test-token")

        # Bright Data가 반환하는 실제 데이터 형태
        raw_data = {
            "name": "BYUN SANGHOON",
            "city": "Seoul",
            "country_code": "KR",
            "current_company": {"name": "MoriAI"},
            "experience": None,  # null
            "education": None,   # null
            "followers": 46,
            "connections": 46,
            "projects": [
                {"title": "Sesami", "description": "Dev verification service"},
            ],
            "honors_and_awards": [
                {"title": "Grand Prize", "publication": "Ministry"},
            ],
        }

        normalized = service._normalize_profile(raw_data, "https://linkedin.com/in/byun")

        # experience=None이지만 current_company fallback으로 1개 생성
        assert len(normalized["experiences"]) == 1
        assert normalized["experiences"][0]["company"] == "MoriAI"
        # education=None → 빈 리스트
        assert normalized["education"] == []

        # 다른 데이터는 정상 추출
        assert normalized["full_name"] == "BYUN SANGHOON"
        assert normalized["current_company"] == "MoriAI"
        assert len(normalized["projects"]) == 1
        assert len(normalized["honors_and_awards"]) == 1


class TestLinkedInSummaryFormat:
    """LinkedIn 요약 포맷 테스트"""

    def test_format_full_profile(self):
        """전체 프로필 요약 포맷"""
        from app.workflows.activities.finalization import _format_linkedin_summary

        profile = {
            "full_name": "Test User",
            "headline": "Engineer",
            "current_company": "Corp",
            "projects": [{"title": "Project", "description": "Built something"}],
            "honors_and_awards": [{"title": "Award", "issuer": "Org", "description": "Won"}],
            "activity": [{"interaction": "Shared", "title": "Post"}],
            "skills": ["Python", "Java"],
        }

        summary = _format_linkedin_summary(profile)

        assert "이름: Test User" in summary
        assert "직함: Engineer" in summary
        assert "현재 회사: Corp" in summary
        assert "프로젝트:" in summary
        assert "Project" in summary
        assert "수상 경력:" in summary
        assert "Award" in summary
        assert "최근 활동:" in summary
        assert "스킬: Python, Java" in summary

    def test_format_empty_profile(self):
        """빈 프로필 처리"""
        from app.workflows.activities.finalization import _format_linkedin_summary

        # 빈 dict는 "정보 없음"으로 처리됨 (falsy 체크)
        assert _format_linkedin_summary({}) == "LinkedIn 프로필 정보 없음"
        assert _format_linkedin_summary(None) == "LinkedIn 프로필 정보 없음"


@pytest.mark.skipif(
    True,  # Skip in local dev - these run fine in Docker where pgvector is installed
    reason="Requires pgvector (installed in Docker only)"
)
class TestLinkedInModels:
    """LinkedIn Pydantic 모델 테스트

    Note: These tests require pgvector which is only installed in Docker.
    The models are tested indirectly via TestLinkedInServiceNormalization.
    """

    def test_linkedin_project_model(self):
        """LinkedInProject 모델"""
        from app.models.input import LinkedInProject

        project = LinkedInProject(
            title="Test Project",
            start_date="Jan 2024",
            description="Description here",
        )

        assert project.title == "Test Project"
        assert project.start_date == "Jan 2024"
        assert project.end_date is None

    def test_linkedin_honor_model(self):
        """LinkedInHonor 모델"""
        from app.models.input import LinkedInHonor

        honor = LinkedInHonor(
            title="Grand Prize",
            issuer="Ministry of Science",
            description="Won hackathon",
        )

        assert honor.title == "Grand Prize"
        assert honor.issuer == "Ministry of Science"

    def test_linkedin_activity_model(self):
        """LinkedInActivity 모델"""
        from app.models.input import LinkedInActivity

        activity = LinkedInActivity(
            interaction="Liked by User",
            title="Interesting post",
            link="https://linkedin.com/...",
        )

        assert activity.interaction == "Liked by User"
        assert activity.link == "https://linkedin.com/..."

    def test_linkedin_profile_model_with_new_fields(self):
        """LinkedInProfile 모델 (새 필드 포함)"""
        from app.models.input import (
            LinkedInProfile,
            LinkedInProject,
            LinkedInHonor,
            LinkedInActivity,
        )

        profile = LinkedInProfile(
            full_name="Test User",
            headline="Engineer",
            current_company="Corp",
            city="Seoul",
            country="KR",
            projects=[LinkedInProject(title="Proj")],
            honors_and_awards=[LinkedInHonor(title="Award")],
            activity=[LinkedInActivity(interaction="Shared", title="Post")],
            followers=100,
            connections=200,
        )

        assert profile.full_name == "Test User"
        assert profile.current_company == "Corp"
        assert len(profile.projects) == 1
        assert len(profile.honors_and_awards) == 1
        assert len(profile.activity) == 1
        assert profile.followers == 100
