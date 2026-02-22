"""
Applications API 통합 테스트 — TestClient + AsyncMock 기반.

지원 CRUD + 분석 트리거 + 결과 조회 + 소유권 검증 전체 검증.
소유권은 Posting을 통해 간접 검증한다 (Posting 소유자만 Application 접근 가능).
psycopg3는 PostgreSQL 전용이므로 Repository/Pool을 AsyncMock으로 대체한다.
"""
from __future__ import annotations

import sys
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from interface.api.middleware.auth import create_token, decode_token


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def auth_token():
    """테스트용 JWT 토큰을 생성한다."""
    return create_token(user_id=str(uuid.uuid4()), email="test@jittda.com")


@pytest.fixture()
def auth_headers(auth_token):
    """인증 헤더를 반환한다."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture()
def other_user_token():
    """다른 사용자의 JWT 토큰을 생성한다."""
    return create_token(user_id=str(uuid.uuid4()), email="other@jittda.com")


@pytest.fixture()
def other_auth_headers(other_user_token):
    """다른 사용자의 인증 헤더를 반환한다."""
    return {"Authorization": f"Bearer {other_user_token}"}


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
def sample_posting_id():
    return str(uuid.uuid4())


@pytest.fixture()
def sample_app_id():
    return str(uuid.uuid4())


@pytest.fixture()
def mock_posting(sample_posting_id, auth_token):
    """인증된 사용자 소유의 샘플 Posting."""
    payload = decode_token(auth_token)
    return {
        "id": sample_posting_id,
        "user_id": payload["sub"],
        "title": "Backend Engineer",
        "department": "Engineering",
        "jd_description": "Python FastAPI",
        "jd_languages": ["Python"],
        "jd_tech_stack": ["FastAPI", "PostgreSQL"],
        "jd_experience_years": 3,
        "auto_analyze": False,
        "status": "draft",
        "created_at": "2026-02-23T00:00:00+00:00",
        "updated_at": "2026-02-23T00:00:00+00:00",
        "application_count": 0,
    }


@pytest.fixture()
def mock_application(sample_posting_id, sample_app_id):
    """샘플 Application."""
    return {
        "id": sample_app_id,
        "posting_id": sample_posting_id,
        "candidate_name": "Hong Gildong",
        "candidate_email": "hong@example.com",
        "github_username": "honggildong",
        "github_urls": ["https://github.com/honggildong/project"],
        "linkedin_url": "https://linkedin.com/in/honggildong",
        "resume_path": None,
        "cover_letter_path": None,
        "portfolio_path": None,
        "memo": "Recommended by CTO",
        "source": "admin_manual",
        "status": "pending",
        "job_id": None,
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


# ── Helper ───────────────────────────────────────────────────────────


def _url(posting_id: str, app_id: str | None = None, suffix: str = "") -> str:
    """Application API URL을 생성한다."""
    base = f"/api/postings/{posting_id}/applications"
    if app_id:
        base = f"{base}/{app_id}"
    if suffix:
        base = f"{base}/{suffix}"
    return base


# ── 인증 테스트 ──────────────────────────────────────────────────────


class TestApplicationAuthentication:
    """인증 관련 테스트."""

    def test_create_application_requires_auth(self, client, sample_posting_id):
        """미인증 사용자의 Application 생성은 401."""
        response = client.post(
            _url(sample_posting_id),
            json={"candidate_name": "Test User"},
        )
        assert response.status_code == 401

    def test_list_applications_requires_auth(self, client, sample_posting_id):
        """미인증 사용자의 Application 목록 조회는 401."""
        response = client.get(_url(sample_posting_id))
        assert response.status_code == 401


# ── Application CRUD 테스트 ──────────────────────────────────────────


class TestApplicationCRUD:
    """Application 생성/조회/수정/삭제 정상 흐름 테스트."""

    def test_create_application_success(
        self, client, auth_headers, mock_posting, mock_application, sample_posting_id
    ):
        """인증된 사용자의 Application 생성은 201."""
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            mock_app_repo = MockAppRepo.return_value
            mock_app_repo.create = AsyncMock(return_value=mock_application["id"])
            mock_app_repo.get = AsyncMock(return_value=mock_application)

            response = client.post(
                _url(sample_posting_id),
                json={
                    "candidate_name": "Hong Gildong",
                    "candidate_email": "hong@example.com",
                    "github_username": "honggildong",
                },
                headers=auth_headers,
            )
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == mock_application["id"]
            assert data["posting_id"] == sample_posting_id
            assert data["candidate_name"] == "Hong Gildong"

    def test_list_applications_success(
        self, client, auth_headers, mock_posting, mock_application, sample_posting_id
    ):
        """인증된 사용자의 Application 목록 조회는 200."""
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            MockAppRepo.return_value.list_by_posting = AsyncMock(
                return_value=[mock_application]
            )

            response = client.get(
                _url(sample_posting_id),
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == mock_application["id"]

    def test_get_application_success(
        self, client, auth_headers, mock_posting, mock_application,
        sample_posting_id, sample_app_id,
    ):
        """지원 상세를 정상 조회한다."""
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            MockAppRepo.return_value.get = AsyncMock(return_value=mock_application)

            response = client.get(
                _url(sample_posting_id, sample_app_id),
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json()["id"] == sample_app_id

    def test_update_application_success(
        self, client, auth_headers, mock_posting, mock_application,
        sample_posting_id, sample_app_id,
    ):
        """지원 정보를 정상 수정한다."""
        updated = {**mock_application, "memo": "Updated memo"}
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            mock_app_repo = MockAppRepo.return_value
            mock_app_repo.get = AsyncMock(side_effect=[mock_application, updated])
            mock_app_repo.update = AsyncMock()

            response = client.put(
                _url(sample_posting_id, sample_app_id),
                json={"memo": "Updated memo"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json()["memo"] == "Updated memo"

    def test_delete_application_success(
        self, client, auth_headers, mock_posting, mock_application,
        sample_posting_id, sample_app_id,
    ):
        """지원을 정상 삭제한다. 204 반환."""
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            mock_app_repo = MockAppRepo.return_value
            mock_app_repo.get = AsyncMock(return_value=mock_application)
            mock_app_repo.delete = AsyncMock()

            response = client.delete(
                _url(sample_posting_id, sample_app_id),
                headers=auth_headers,
            )
            assert response.status_code == 204


# ── 분석 트리거 + 결과 조회 테스트 ───────────────────────────────────


class TestApplicationAnalysis:
    """분석 시작 및 결과 조회 테스트."""

    def test_analyze_application_success(
        self, client, auth_headers, mock_posting, mock_application,
        sample_posting_id, sample_app_id, app,
    ):
        """분석 시작은 202를 반환하고 Temporal Workflow를 트리거한다."""
        mock_workflow = MagicMock()
        mock_workflow.run = MagicMock()
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
            patch("interface.api.routes.applications.JobRepository") as MockJobRepo,
            patch.dict("sys.modules", {
                "application.temporal": MagicMock(TASK_QUEUE="test-queue"),
                "application.temporal.workflows": MagicMock(AnalysisPipeline=mock_workflow),
            }),
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            mock_app_repo = MockAppRepo.return_value
            mock_app_repo.get = AsyncMock(return_value=mock_application)
            mock_app_repo.link_job = AsyncMock()

            job_id = str(uuid.uuid4())
            MockJobRepo.return_value.create = AsyncMock(return_value=job_id)

            response = client.post(
                _url(sample_posting_id, sample_app_id, "analyze"),
                headers=auth_headers,
            )
            assert response.status_code == 202
            data = response.json()
            assert data["job_id"] == job_id
            assert data["status"] == "analyzing"

    def test_analyze_already_in_progress_returns_409(
        self, client, auth_headers, mock_posting,
        sample_posting_id, sample_app_id, mock_application,
    ):
        """이미 분석 중인 Application은 409."""
        analyzing_app = {**mock_application, "status": "analyzing"}
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            MockAppRepo.return_value.get = AsyncMock(return_value=analyzing_app)

            response = client.post(
                _url(sample_posting_id, sample_app_id, "analyze"),
                headers=auth_headers,
            )
            assert response.status_code == 409

    def test_get_result_success(
        self, client, auth_headers, mock_posting,
        sample_posting_id, sample_app_id, mock_application,
    ):
        """완료된 분석 결과를 정상 조회한다."""
        job_id = str(uuid.uuid4())
        app_with_job = {**mock_application, "job_id": job_id}
        completed_job = {
            "id": job_id,
            "status": "completed",
            "result_data": {"summary": "Analysis result"},
        }
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
            patch("interface.api.routes.applications.JobRepository") as MockJobRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            MockAppRepo.return_value.get = AsyncMock(return_value=app_with_job)
            MockJobRepo.return_value.get = AsyncMock(return_value=completed_job)

            response = client.get(
                _url(sample_posting_id, sample_app_id, "result"),
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json() == {"summary": "Analysis result"}

    def test_get_result_no_analysis_started_returns_400(
        self, client, auth_headers, mock_posting,
        sample_posting_id, sample_app_id, mock_application,
    ):
        """분석이 시작되지 않은 Application의 결과 조회는 400."""
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            MockAppRepo.return_value.get = AsyncMock(return_value=mock_application)

            response = client.get(
                _url(sample_posting_id, sample_app_id, "result"),
                headers=auth_headers,
            )
            assert response.status_code == 400

    def test_get_result_not_completed_returns_400(
        self, client, auth_headers, mock_posting,
        sample_posting_id, sample_app_id, mock_application,
    ):
        """미완료 Job의 결과 조회는 400."""
        job_id = str(uuid.uuid4())
        app_with_job = {**mock_application, "job_id": job_id}
        running_job = {
            "id": job_id,
            "status": "running",
            "result_data": None,
        }
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
            patch("interface.api.routes.applications.JobRepository") as MockJobRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            MockAppRepo.return_value.get = AsyncMock(return_value=app_with_job)
            MockJobRepo.return_value.get = AsyncMock(return_value=running_job)

            response = client.get(
                _url(sample_posting_id, sample_app_id, "result"),
                headers=auth_headers,
            )
            assert response.status_code == 400


# ── IDOR — Posting 소유권 기반 접근 제어 ─────────────────────────────


class TestApplicationIDOR:
    """Posting을 통한 Application 소유권 검증 테스트."""

    def test_other_user_cannot_list_applications(
        self, client, other_auth_headers, mock_posting, sample_posting_id
    ):
        """다른 사용자는 Posting의 Application 목록을 조회할 수 없다. 403."""
        with patch(
            "interface.api.routes.applications.PostingRepository"
        ) as MockPostingRepo:
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)

            response = client.get(
                _url(sample_posting_id),
                headers=other_auth_headers,
            )
            assert response.status_code == 403

    def test_other_user_cannot_create_application(
        self, client, other_auth_headers, mock_posting, sample_posting_id
    ):
        """다른 사용자는 Application을 생성할 수 없다. 403."""
        with patch(
            "interface.api.routes.applications.PostingRepository"
        ) as MockPostingRepo:
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)

            response = client.post(
                _url(sample_posting_id),
                json={"candidate_name": "Attacker"},
                headers=other_auth_headers,
            )
            assert response.status_code == 403

    def test_other_user_cannot_delete_application(
        self, client, other_auth_headers, mock_posting,
        sample_posting_id, sample_app_id,
    ):
        """다른 사용자는 Application을 삭제할 수 없다. 403."""
        with patch(
            "interface.api.routes.applications.PostingRepository"
        ) as MockPostingRepo:
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)

            response = client.delete(
                _url(sample_posting_id, sample_app_id),
                headers=other_auth_headers,
            )
            assert response.status_code == 403


# ── 입력 검증 테스트 ─────────────────────────────────────────────────


class TestApplicationInputValidation:
    """UUID 형식 및 존재 여부 검증."""

    def test_invalid_posting_uuid_returns_400(self, client, auth_headers):
        """잘못된 posting UUID 형식은 400."""
        response = client.get(
            _url("not-a-uuid"),
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_invalid_app_uuid_returns_400(
        self, client, auth_headers, mock_posting, sample_posting_id
    ):
        """잘못된 application UUID 형식은 400."""
        with patch(
            "interface.api.routes.applications.PostingRepository"
        ) as MockPostingRepo:
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)

            response = client.get(
                _url(sample_posting_id, "not-a-uuid"),
                headers=auth_headers,
            )
            assert response.status_code == 400

    def test_nonexistent_posting_returns_404(self, client, auth_headers):
        """존재하지 않는 Posting의 Application 조회는 404."""
        posting_id = str(uuid.uuid4())
        with patch(
            "interface.api.routes.applications.PostingRepository"
        ) as MockPostingRepo:
            MockPostingRepo.return_value.get = AsyncMock(return_value=None)

            response = client.get(
                _url(posting_id),
                headers=auth_headers,
            )
            assert response.status_code == 404

    def test_nonexistent_application_returns_404(
        self, client, auth_headers, mock_posting, sample_posting_id
    ):
        """존재하지 않는 Application 조회는 404."""
        app_id = str(uuid.uuid4())
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            MockAppRepo.return_value.get = AsyncMock(return_value=None)

            response = client.get(
                _url(sample_posting_id, app_id),
                headers=auth_headers,
            )
            assert response.status_code == 404

    def test_application_wrong_posting_returns_404(
        self, client, auth_headers, mock_posting, sample_posting_id
    ):
        """다른 Posting에 속한 Application 조회는 404."""
        app_id = str(uuid.uuid4())
        wrong_app = {
            "id": app_id,
            "posting_id": str(uuid.uuid4()),  # 다른 posting_id
            "candidate_name": "Wrong",
            "candidate_email": "wrong@example.com",
            "github_username": None,
            "github_urls": [],
            "linkedin_url": None,
            "resume_path": None,
            "cover_letter_path": None,
            "portfolio_path": None,
            "memo": None,
            "source": "admin_manual",
            "status": "pending",
            "job_id": None,
            "created_at": "2026-02-23T00:00:00+00:00",
            "updated_at": "2026-02-23T00:00:00+00:00",
        }
        with (
            patch("interface.api.routes.applications.PostingRepository") as MockPostingRepo,
            patch("interface.api.routes.applications.ApplicationRepository") as MockAppRepo,
        ):
            MockPostingRepo.return_value.get = AsyncMock(return_value=mock_posting)
            MockAppRepo.return_value.get = AsyncMock(return_value=wrong_app)

            response = client.get(
                _url(sample_posting_id, app_id),
                headers=auth_headers,
            )
            assert response.status_code == 404
