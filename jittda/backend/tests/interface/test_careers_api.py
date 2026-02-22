"""
Careers API 통합 테스트 — TestClient + AsyncMock 기반.

Public 커리어 페이지 조회 + 지원 제출 + 에러 케이스 검증.
인증 불필요한 public 엔드포인트이므로 auth_headers 없이 테스트한다.
psycopg3는 PostgreSQL 전용이므로 Repository/Pool을 AsyncMock으로 대체한다.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def mock_pool():
    """DB Pool mock — get_pool()이 호출되면 AsyncMock 반환."""
    mock = MagicMock()
    mock.connection.return_value.__aenter__ = AsyncMock()
    mock.connection.return_value.__aexit__ = AsyncMock()
    stats_mock = MagicMock()
    stats_mock.pool_size = 2
    stats_mock.pool_available = 2
    stats_mock.requests_waiting = 0
    mock.get_stats.return_value = stats_mock
    return mock


@pytest.fixture()
def sample_company():
    """샘플 회사 정보."""
    return {
        "id": str(uuid.uuid4()),
        "company_name": "Jittda Inc.",
        "company_slug": "jittda",
        "company_logo": "https://jittda.com/logo.png",
        "company_description": "AI Interview Platform",
        "name": "Jittda Inc.",
    }


@pytest.fixture()
def sample_posting_id():
    return str(uuid.uuid4())


@pytest.fixture()
def sample_active_posting(sample_posting_id, sample_company):
    """활성 상태의 샘플 Posting."""
    return {
        "id": sample_posting_id,
        "user_id": sample_company["id"],
        "title": "Backend Engineer",
        "department": "Engineering",
        "jd_description": "Python FastAPI developer needed.",
        "jd_languages": ["Python"],
        "jd_tech_stack": ["FastAPI", "PostgreSQL"],
        "jd_experience_years": 3,
        "auto_analyze": False,
        "status": "active",
        "created_at": "2026-02-23T00:00:00+00:00",
        "updated_at": "2026-02-23T00:00:00+00:00",
    }


@pytest.fixture()
def sample_draft_posting(sample_company):
    """비활성 상태의 샘플 Posting."""
    return {
        "id": str(uuid.uuid4()),
        "user_id": sample_company["id"],
        "title": "Frontend Engineer",
        "department": "Engineering",
        "jd_description": "React developer needed.",
        "jd_languages": ["TypeScript"],
        "jd_tech_stack": ["React", "Next.js"],
        "jd_experience_years": 2,
        "auto_analyze": False,
        "status": "draft",
        "created_at": "2026-02-23T00:00:00+00:00",
        "updated_at": "2026-02-23T00:00:00+00:00",
    }


@pytest.fixture()
def app(mock_pool):
    """테스트용 FastAPI 앱 — DB Pool + Temporal Client mock."""
    with (
        patch("infrastructure.persistence.pool._pool", mock_pool),
        patch("infrastructure.persistence.pool.get_pool", return_value=mock_pool),
    ):
        from interface.api.main import create_app

        test_app = create_app()
        test_app.state.temporal_client = AsyncMock()
        test_app.state.redis_bridge = None
        yield test_app


@pytest.fixture()
def client(app):
    """TestClient 인스턴스."""
    return TestClient(app, raise_server_exceptions=False)


# ── 커리어 페이지 조회 테스트 ────────────────────────────────────────


class TestGetCareerPage:
    """GET /api/careers/{slug} 테스트."""

    def test_get_career_page_success(
        self, client, sample_company, sample_active_posting
    ):
        """유효한 slug로 커리어 페이지를 조회한다."""
        with (
            patch("interface.api.routes.careers.UserRepository") as MockUserRepo,
            patch("interface.api.routes.careers.PostingRepository") as MockPostingRepo,
        ):
            MockUserRepo.return_value.get_by_slug = AsyncMock(
                return_value=sample_company
            )
            MockPostingRepo.return_value.list_active_by_slug = AsyncMock(
                return_value=[sample_active_posting]
            )

            response = client.get("/api/careers/jittda")
            assert response.status_code == 200
            data = response.json()
            assert data["company"]["name"] == "Jittda Inc."
            assert data["company"]["slug"] == "jittda"
            assert len(data["postings"]) == 1
            assert data["postings"][0]["title"] == "Backend Engineer"

    def test_get_career_page_empty_postings(self, client, sample_company):
        """공고가 없는 회사 커리어 페이지도 정상 조회한다."""
        with (
            patch("interface.api.routes.careers.UserRepository") as MockUserRepo,
            patch("interface.api.routes.careers.PostingRepository") as MockPostingRepo,
        ):
            MockUserRepo.return_value.get_by_slug = AsyncMock(
                return_value=sample_company
            )
            MockPostingRepo.return_value.list_active_by_slug = AsyncMock(
                return_value=[]
            )

            response = client.get("/api/careers/jittda")
            assert response.status_code == 200
            data = response.json()
            assert data["postings"] == []

    def test_get_career_page_not_found_slug(self, client):
        """존재하지 않는 slug는 404를 반환한다."""
        with patch(
            "interface.api.routes.careers.UserRepository"
        ) as MockUserRepo:
            MockUserRepo.return_value.get_by_slug = AsyncMock(return_value=None)

            response = client.get("/api/careers/nonexistent-company")
            assert response.status_code == 404


# ── 공고 상세 조회 테스트 ────────────────────────────────────────────


class TestGetCareerPosting:
    """GET /api/careers/{slug}/{postingId} 테스트."""

    def test_get_career_posting_success(
        self, client, sample_company, sample_active_posting
    ):
        """활성 공고의 상세를 정상 조회한다."""
        with (
            patch("interface.api.routes.careers.UserRepository") as MockUserRepo,
            patch("interface.api.routes.careers.PostingRepository") as MockPostingRepo,
        ):
            MockUserRepo.return_value.get_by_slug = AsyncMock(
                return_value=sample_company
            )
            MockPostingRepo.return_value.get = AsyncMock(
                return_value=sample_active_posting
            )

            response = client.get(
                f"/api/careers/jittda/{sample_active_posting['id']}"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["company"]["name"] == "Jittda Inc."
            assert data["posting"]["title"] == "Backend Engineer"
            assert data["posting"]["jd_description"] == "Python FastAPI developer needed."

    def test_get_career_posting_not_found_slug(self, client):
        """존재하지 않는 slug는 404."""
        posting_id = str(uuid.uuid4())
        with patch(
            "interface.api.routes.careers.UserRepository"
        ) as MockUserRepo:
            MockUserRepo.return_value.get_by_slug = AsyncMock(return_value=None)

            response = client.get(f"/api/careers/nonexistent/{posting_id}")
            assert response.status_code == 404

    def test_get_career_posting_not_found_posting(
        self, client, sample_company
    ):
        """존재하지 않는 posting은 404."""
        posting_id = str(uuid.uuid4())
        with (
            patch("interface.api.routes.careers.UserRepository") as MockUserRepo,
            patch("interface.api.routes.careers.PostingRepository") as MockPostingRepo,
        ):
            MockUserRepo.return_value.get_by_slug = AsyncMock(
                return_value=sample_company
            )
            MockPostingRepo.return_value.get = AsyncMock(return_value=None)

            response = client.get(f"/api/careers/jittda/{posting_id}")
            assert response.status_code == 404

    def test_get_career_posting_wrong_company(
        self, client, sample_company, sample_active_posting
    ):
        """다른 회사의 posting은 404 (user_id 불일치)."""
        wrong_posting = {**sample_active_posting, "user_id": str(uuid.uuid4())}
        with (
            patch("interface.api.routes.careers.UserRepository") as MockUserRepo,
            patch("interface.api.routes.careers.PostingRepository") as MockPostingRepo,
        ):
            MockUserRepo.return_value.get_by_slug = AsyncMock(
                return_value=sample_company
            )
            MockPostingRepo.return_value.get = AsyncMock(return_value=wrong_posting)

            response = client.get(
                f"/api/careers/jittda/{sample_active_posting['id']}"
            )
            assert response.status_code == 404

    def test_get_career_posting_inactive_returns_404(
        self, client, sample_company, sample_draft_posting
    ):
        """비활성 공고는 404를 반환한다."""
        with (
            patch("interface.api.routes.careers.UserRepository") as MockUserRepo,
            patch("interface.api.routes.careers.PostingRepository") as MockPostingRepo,
        ):
            MockUserRepo.return_value.get_by_slug = AsyncMock(
                return_value=sample_company
            )
            MockPostingRepo.return_value.get = AsyncMock(
                return_value=sample_draft_posting
            )

            response = client.get(
                f"/api/careers/jittda/{sample_draft_posting['id']}"
            )
            assert response.status_code == 404

    def test_get_career_posting_invalid_uuid_returns_400(self, client):
        """잘못된 posting UUID 형식은 400."""
        response = client.get("/api/careers/jittda/not-a-uuid")
        assert response.status_code == 400


# ── 지원 제출 테스트 ─────────────────────────────────────────────────


class TestApplyToPosting:
    """POST /api/careers/{slug}/{postingId}/apply 테스트."""

    def test_apply_success(
        self, client, sample_company, sample_active_posting
    ):
        """정상 지원은 200과 application_id를 반환한다."""
        app_id = str(uuid.uuid4())
        with (
            patch("interface.api.routes.careers.UserRepository") as MockUserRepo,
            patch("interface.api.routes.careers.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.careers.ApplicationRepository") as MockAppRepo,
        ):
            MockUserRepo.return_value.get_by_slug = AsyncMock(
                return_value=sample_company
            )
            MockPostingRepo.return_value.get = AsyncMock(
                return_value=sample_active_posting
            )
            MockAppRepo.return_value.create = AsyncMock(return_value=app_id)

            response = client.post(
                f"/api/careers/jittda/{sample_active_posting['id']}/apply",
                json={
                    "candidate_name": "Kim Chulsoo",
                    "candidate_email": "kim@example.com",
                    "github_username": "kimchulsoo",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["application_id"] == app_id
            assert "message" in data

    def test_apply_not_found_slug_returns_404(self, client):
        """존재하지 않는 회사 slug에 지원은 404."""
        posting_id = str(uuid.uuid4())
        with patch(
            "interface.api.routes.careers.UserRepository"
        ) as MockUserRepo:
            MockUserRepo.return_value.get_by_slug = AsyncMock(return_value=None)

            response = client.post(
                f"/api/careers/nonexistent/{posting_id}/apply",
                json={
                    "candidate_name": "Kim Chulsoo",
                    "candidate_email": "kim@example.com",
                },
            )
            assert response.status_code == 404

    def test_apply_not_found_posting_returns_404(
        self, client, sample_company
    ):
        """존재하지 않는 공고에 지원은 404."""
        posting_id = str(uuid.uuid4())
        with (
            patch("interface.api.routes.careers.UserRepository") as MockUserRepo,
            patch("interface.api.routes.careers.PostingRepository") as MockPostingRepo,
        ):
            MockUserRepo.return_value.get_by_slug = AsyncMock(
                return_value=sample_company
            )
            MockPostingRepo.return_value.get = AsyncMock(return_value=None)

            response = client.post(
                f"/api/careers/jittda/{posting_id}/apply",
                json={
                    "candidate_name": "Kim Chulsoo",
                    "candidate_email": "kim@example.com",
                },
            )
            assert response.status_code == 404

    def test_apply_inactive_posting_returns_400(
        self, client, sample_company, sample_draft_posting
    ):
        """비활성 공고에 지원은 400."""
        with (
            patch("interface.api.routes.careers.UserRepository") as MockUserRepo,
            patch("interface.api.routes.careers.PostingRepository") as MockPostingRepo,
        ):
            MockUserRepo.return_value.get_by_slug = AsyncMock(
                return_value=sample_company
            )
            MockPostingRepo.return_value.get = AsyncMock(
                return_value=sample_draft_posting
            )

            response = client.post(
                f"/api/careers/jittda/{sample_draft_posting['id']}/apply",
                json={
                    "candidate_name": "Kim Chulsoo",
                    "candidate_email": "kim@example.com",
                },
            )
            assert response.status_code == 400

    def test_apply_duplicate_email_returns_409(
        self, client, sample_company, sample_active_posting
    ):
        """중복 이메일로 지원은 409를 반환한다."""
        with (
            patch("interface.api.routes.careers.UserRepository") as MockUserRepo,
            patch("interface.api.routes.careers.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.careers.ApplicationRepository") as MockAppRepo,
        ):
            MockUserRepo.return_value.get_by_slug = AsyncMock(
                return_value=sample_company
            )
            MockPostingRepo.return_value.get = AsyncMock(
                return_value=sample_active_posting
            )
            MockAppRepo.return_value.create = AsyncMock(
                side_effect=Exception("unique constraint violation: duplicate key")
            )

            response = client.post(
                f"/api/careers/jittda/{sample_active_posting['id']}/apply",
                json={
                    "candidate_name": "Kim Chulsoo",
                    "candidate_email": "kim@example.com",
                },
            )
            assert response.status_code == 409

    def test_apply_invalid_posting_uuid_returns_400(self, client):
        """잘못된 posting UUID에 지원은 400."""
        response = client.post(
            "/api/careers/jittda/not-a-uuid/apply",
            json={
                "candidate_name": "Kim Chulsoo",
                "candidate_email": "kim@example.com",
            },
        )
        assert response.status_code == 400

    def test_apply_missing_required_fields_returns_422(
        self, client, sample_active_posting
    ):
        """필수 필드 누락 시 422 (Pydantic 검증)."""
        response = client.post(
            f"/api/careers/jittda/{sample_active_posting['id']}/apply",
            json={},
        )
        assert response.status_code == 422

    def test_apply_empty_name_returns_422(
        self, client, sample_active_posting
    ):
        """빈 이름으로 지원은 422 (min_length=1)."""
        response = client.post(
            f"/api/careers/jittda/{sample_active_posting['id']}/apply",
            json={
                "candidate_name": "",
                "candidate_email": "kim@example.com",
            },
        )
        assert response.status_code == 422
