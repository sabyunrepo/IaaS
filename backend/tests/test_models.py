"""Unit tests for data models."""
import pytest
from app.models.enums import JobStatus, QuestionCategory
from app.models.input import InputData, CreateJobRequest

JD_TEXT = "Python 백엔드 개발자를 모집합니다. 3년 이상의 경험이 필요하며 FastAPI와 PostgreSQL 경험자 우대합니다."


class TestEnums:
    def test_job_status_values(self):
        assert JobStatus.PENDING == "pending"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"

    def test_question_category_values(self):
        cats = [c.value for c in QuestionCategory]
        assert "role_fit" in cats
        assert "technical_depth" in cats


class TestInputData:
    def test_minimal_input(self):
        data = InputData(jd_text=JD_TEXT, experience_level="시니어")
        assert data.jd_text == JD_TEXT
        assert data.experience_level == "시니어"

    def test_full_input(self):
        data = InputData(
            jd_text=JD_TEXT,
            experience_level="시니어",
            git_url="https://github.com/user/repo",
            linkedin_url="https://linkedin.com/in/user",
        )
        assert data.git_url == "https://github.com/user/repo"

    def test_jd_text_too_short(self):
        with pytest.raises(Exception):
            InputData(jd_text="short", experience_level="시니어")


class TestCreateJobRequest:
    def test_create_job_request(self):
        req = CreateJobRequest(
            input_data=InputData(jd_text=JD_TEXT, experience_level="주니어"),
        )
        assert req.input_data.jd_text == JD_TEXT
        assert req.callback_url is None
