"""
Jobs API 통합 테스트 — TestClient + AsyncMock 기반.

FastAPI 의존성 주입 체인(인증 → Repository → Temporal) 전체 검증.
psycopg3는 PostgreSQL 전용이므로 Repository/Pool을 AsyncMock으로 대체한다.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from interface.api.middleware.auth import create_token


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
    mock.get_stats.return_value = {"pool_size": 2, "pool_available": 2, "requests_waiting": 0}
    return mock


@pytest.fixture()
def sample_job_id():
    return str(uuid.uuid4())


@pytest.fixture()
def mock_job(sample_job_id, auth_token):
    """인증된 사용자 소유의 샘플 Job."""
    from interface.api.middleware.auth import decode_token

    payload = decode_token(auth_token)
    return {
        "id": sample_job_id,
        "user_id": payload["sub"],
        "status": "completed",
        "progress": 1.0,
        "input_data": {"candidate_username": "testuser"},
        "result_data": {"summary": "test result"},
        "error_message": None,
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
        # Temporal client mock
        test_app.state.temporal_client = AsyncMock()
        test_app.state.redis_bridge = None
        yield test_app


@pytest.fixture()
def client(app):
    """TestClient 인스턴스."""
    return TestClient(app, raise_server_exceptions=False)


# ── 인증 테스트 ──────────────────────────────────────────────────────


class TestAuthentication:
    """인증 관련 테스트."""

    def test_create_job_requires_auth(self, client):
        """미인증 사용자의 Job 생성은 401을 반환한다."""
        response = client.post(
            "/api/jobs",
            json={"candidate_username": "testuser"},
        )
        assert response.status_code == 401

    def test_list_jobs_unauthenticated_returns_empty(self, client):
        """미인증 사용자의 Job 목록 조회는 빈 리스트를 반환한다."""
        response = client.get("/api/jobs")
        assert response.status_code == 200
        assert response.json() == []


# ── Job CRUD 테스트 ──────────────────────────────────────────────────


class TestJobCRUD:
    """Job 생성/조회 정상 흐름 테스트."""

    def test_create_job_authenticated(self, client, auth_headers):
        """인증된 사용자의 Job 생성은 201을 반환한다."""
        with patch(
            "interface.api.routes.jobs.JobRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            job_id = str(uuid.uuid4())
            mock_repo.create = AsyncMock(return_value=job_id)

            response = client.post(
                "/api/jobs",
                json={"candidate_username": "testuser"},
                headers=auth_headers,
            )
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == job_id
            assert data["status"] == "pending"

    def test_create_job_missing_input(self, client, auth_headers):
        """github_urls와 candidate_username 모두 없으면 400."""
        response = client.post(
            "/api/jobs",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_get_job_success(self, client, auth_headers, mock_job):
        """소유한 Job을 정상 조회한다."""
        with patch(
            "interface.api.routes.jobs.JobRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=mock_job)

            response = client.get(
                f"/api/jobs/{mock_job['id']}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json()["id"] == mock_job["id"]

    def test_get_job_result_completed(self, client, auth_headers, mock_job):
        """완료된 Job의 결과를 조회한다."""
        with patch(
            "interface.api.routes.jobs.JobRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=mock_job)

            response = client.get(
                f"/api/jobs/{mock_job['id']}/result",
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json() == {"summary": "test result"}

    def test_get_job_result_not_completed(self, client, auth_headers, sample_job_id):
        """미완료 Job 결과 조회는 400."""
        pending_job = {
            "id": sample_job_id,
            "user_id": None,
            "status": "running",
            "progress": 0.5,
            "input_data": {},
            "result_data": None,
            "error_message": None,
        }
        with patch(
            "interface.api.routes.jobs.JobRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=pending_job)

            response = client.get(
                f"/api/jobs/{sample_job_id}/result",
                headers=auth_headers,
            )
            assert response.status_code == 400


# ── IDOR (Insecure Direct Object Reference) 테스트 ──────────────────


class TestIDOR:
    """Job 소유권 검증 테스트 — 타 사용자 접근 차단."""

    def test_access_other_users_job_forbidden(
        self, client, other_auth_headers, mock_job
    ):
        """다른 사용자의 Job 접근은 403."""
        with patch(
            "interface.api.routes.jobs.JobRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=mock_job)

            response = client.get(
                f"/api/jobs/{mock_job['id']}",
                headers=other_auth_headers,
            )
            assert response.status_code == 403

    def test_access_other_users_job_result_forbidden(
        self, client, other_auth_headers, mock_job
    ):
        """다른 사용자의 Job 결과 접근도 403."""
        with patch(
            "interface.api.routes.jobs.JobRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=mock_job)

            response = client.get(
                f"/api/jobs/{mock_job['id']}/result",
                headers=other_auth_headers,
            )
            assert response.status_code == 403

    def test_anon_job_accessible_by_anyone(self, client, auth_headers):
        """user_id가 None인 Job은 누구나 접근 가능 (하위 호환)."""
        anon_job = {
            "id": str(uuid.uuid4()),
            "user_id": None,
            "status": "completed",
            "progress": 1.0,
            "input_data": {},
            "result_data": {},
            "error_message": None,
        }
        with patch(
            "interface.api.routes.jobs.JobRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=anon_job)

            response = client.get(
                f"/api/jobs/{anon_job['id']}",
                headers=auth_headers,
            )
            assert response.status_code == 200


# ── 입력 검증 테스트 ─────────────────────────────────────────────────


class TestInputValidation:
    """UUID 형식 및 파라미터 검증."""

    def test_invalid_uuid_returns_400(self, client, auth_headers):
        """잘못된 UUID 형식은 400."""
        response = client.get(
            "/api/jobs/not-a-uuid",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_nonexistent_job_returns_404(self, client, auth_headers):
        """존재하지 않는 Job은 404."""
        with patch(
            "interface.api.routes.jobs.JobRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=None)

            response = client.get(
                f"/api/jobs/{uuid.uuid4()}",
                headers=auth_headers,
            )
            assert response.status_code == 404

    def test_list_jobs_limit_out_of_range(self, client, auth_headers):
        """limit 범위 초과는 422."""
        response = client.get(
            "/api/jobs?limit=0",
            headers=auth_headers,
        )
        assert response.status_code == 422

        response = client.get(
            "/api/jobs?limit=101",
            headers=auth_headers,
        )
        assert response.status_code == 422


# ── Health Check 테스트 ──────────────────────────────────────────────


class TestHealthCheck:
    """Health check 엔드포인트 테스트."""

    def test_health_check_returns_200(self, client, mock_pool):
        """Health check는 200과 pool stats를 반환한다."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "5.0.0"
