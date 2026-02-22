"""
Postings API 통합 테스트 — TestClient + AsyncMock 기반.

채용 공고 CRUD + 소유권 검증 + 입력 유효성 전체 검증.
psycopg3는 PostgreSQL 전용이므로 Repository/Pool을 AsyncMock으로 대체한다.
"""
from __future__ import annotations

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


# ── 인증 테스트 ──────────────────────────────────────────────────────


class TestPostingAuthentication:
    """인증 관련 테스트."""

    def test_create_posting_requires_auth(self, client):
        """미인증 사용자의 Posting 생성은 401을 반환한다."""
        response = client.post(
            "/api/postings",
            json={"title": "Backend Engineer"},
        )
        assert response.status_code == 401

    def test_list_postings_requires_auth(self, client):
        """미인증 사용자의 Posting 목록 조회는 401을 반환한다."""
        response = client.get("/api/postings")
        assert response.status_code == 401

    def test_get_posting_requires_auth(self, client, sample_posting_id):
        """미인증 사용자의 Posting 조회는 401을 반환한다."""
        response = client.get(f"/api/postings/{sample_posting_id}")
        assert response.status_code == 401

    def test_update_posting_requires_auth(self, client, sample_posting_id):
        """미인증 사용자의 Posting 수정은 401을 반환한다."""
        response = client.put(
            f"/api/postings/{sample_posting_id}",
            json={"title": "Updated"},
        )
        assert response.status_code == 401

    def test_delete_posting_requires_auth(self, client, sample_posting_id):
        """미인증 사용자의 Posting 삭제는 401을 반환한다."""
        response = client.delete(f"/api/postings/{sample_posting_id}")
        assert response.status_code == 401


# ── Posting CRUD 테스트 ──────────────────────────────────────────────


class TestPostingCRUD:
    """Posting 생성/조회/수정/삭제 정상 흐름 테스트."""

    def test_create_posting_success(self, client, auth_headers, auth_token):
        """인증된 사용자의 Posting 생성은 201을 반환한다."""
        payload = decode_token(auth_token)
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            posting_id = str(uuid.uuid4())
            mock_repo.create = AsyncMock(return_value=posting_id)
            mock_repo.get = AsyncMock(return_value={
                "id": posting_id,
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
            })

            response = client.post(
                "/api/postings",
                json={
                    "title": "Backend Engineer",
                    "department": "Engineering",
                    "jd_description": "Python FastAPI",
                    "jd_languages": ["Python"],
                    "jd_tech_stack": ["FastAPI", "PostgreSQL"],
                    "jd_experience_years": 3,
                },
                headers=auth_headers,
            )
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == posting_id
            assert data["title"] == "Backend Engineer"
            assert data["status"] == "draft"
            assert data["application_count"] == 0

    def test_list_postings_success(self, client, auth_headers, mock_posting):
        """인증된 사용자의 Posting 목록 조회는 200을 반환한다."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.list_by_user = AsyncMock(return_value=[mock_posting])

            response = client.get("/api/postings", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == mock_posting["id"]

    def test_list_postings_with_status_filter(self, client, auth_headers, mock_posting):
        """status 필터로 Posting 목록을 조회한다."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.list_by_user = AsyncMock(return_value=[mock_posting])

            response = client.get(
                "/api/postings?status=draft",
                headers=auth_headers,
            )
            assert response.status_code == 200
            mock_repo.list_by_user.assert_called_once()

    def test_get_posting_success(self, client, auth_headers, mock_posting):
        """소유한 Posting을 정상 조회한다."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=mock_posting)

            response = client.get(
                f"/api/postings/{mock_posting['id']}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json()["id"] == mock_posting["id"]
            assert response.json()["title"] == "Backend Engineer"

    def test_update_posting_success(self, client, auth_headers, mock_posting):
        """소유한 Posting을 정상 수정한다."""
        updated_posting = {**mock_posting, "title": "Senior Backend Engineer"}
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(
                side_effect=[mock_posting, updated_posting]
            )
            mock_repo.update = AsyncMock()

            response = client.put(
                f"/api/postings/{mock_posting['id']}",
                json={"title": "Senior Backend Engineer"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json()["title"] == "Senior Backend Engineer"

    def test_update_posting_no_changes(self, client, auth_headers, mock_posting):
        """변경사항 없는 수정 요청도 200을 반환한다."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(
                side_effect=[mock_posting, mock_posting]
            )

            response = client.put(
                f"/api/postings/{mock_posting['id']}",
                json={},
                headers=auth_headers,
            )
            assert response.status_code == 200

    def test_delete_posting_success(self, client, auth_headers, mock_posting):
        """소유한 Posting을 정상 삭제한다. 204 반환."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=mock_posting)
            mock_repo.delete = AsyncMock()

            response = client.delete(
                f"/api/postings/{mock_posting['id']}",
                headers=auth_headers,
            )
            assert response.status_code == 204


# ── IDOR (Insecure Direct Object Reference) 테스트 ──────────────────


class TestPostingIDOR:
    """Posting 소유권 검증 테스트 — 타 사용자 접근 차단."""

    def test_get_other_users_posting_forbidden(
        self, client, other_auth_headers, mock_posting
    ):
        """다른 사용자의 Posting 조회는 403."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=mock_posting)

            response = client.get(
                f"/api/postings/{mock_posting['id']}",
                headers=other_auth_headers,
            )
            assert response.status_code == 403

    def test_update_other_users_posting_forbidden(
        self, client, other_auth_headers, mock_posting
    ):
        """다른 사용자의 Posting 수정은 403."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=mock_posting)

            response = client.put(
                f"/api/postings/{mock_posting['id']}",
                json={"title": "Hacked"},
                headers=other_auth_headers,
            )
            assert response.status_code == 403

    def test_delete_other_users_posting_forbidden(
        self, client, other_auth_headers, mock_posting
    ):
        """다른 사용자의 Posting 삭제는 403."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=mock_posting)

            response = client.delete(
                f"/api/postings/{mock_posting['id']}",
                headers=other_auth_headers,
            )
            assert response.status_code == 403


# ── 입력 검증 테스트 ─────────────────────────────────────────────────


class TestPostingInputValidation:
    """UUID 형식 및 파라미터 검증."""

    def test_invalid_uuid_get_returns_400(self, client, auth_headers):
        """잘못된 UUID 형식 GET은 400."""
        response = client.get(
            "/api/postings/not-a-uuid",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_invalid_uuid_put_returns_400(self, client, auth_headers):
        """잘못된 UUID 형식 PUT은 400."""
        response = client.put(
            "/api/postings/not-a-uuid",
            json={"title": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_invalid_uuid_delete_returns_400(self, client, auth_headers):
        """잘못된 UUID 형식 DELETE는 400."""
        response = client.delete(
            "/api/postings/not-a-uuid",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_nonexistent_posting_returns_404(self, client, auth_headers):
        """존재하지 않는 Posting은 404."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=None)

            response = client.get(
                f"/api/postings/{uuid.uuid4()}",
                headers=auth_headers,
            )
            assert response.status_code == 404

    def test_update_nonexistent_posting_returns_404(self, client, auth_headers):
        """존재하지 않는 Posting 수정은 404."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=None)

            response = client.put(
                f"/api/postings/{uuid.uuid4()}",
                json={"title": "Updated"},
                headers=auth_headers,
            )
            assert response.status_code == 404

    def test_delete_nonexistent_posting_returns_404(self, client, auth_headers):
        """존재하지 않는 Posting 삭제는 404."""
        with patch(
            "interface.api.routes.postings.PostingRepository"
        ) as MockRepo:
            mock_repo = MockRepo.return_value
            mock_repo.get = AsyncMock(return_value=None)

            response = client.delete(
                f"/api/postings/{uuid.uuid4()}",
                headers=auth_headers,
            )
            assert response.status_code == 404

    def test_create_posting_missing_title_returns_422(self, client, auth_headers):
        """title 없이 Posting 생성은 422 (Pydantic 검증)."""
        response = client.post(
            "/api/postings",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_posting_empty_title_returns_422(self, client, auth_headers):
        """빈 title로 Posting 생성은 422 (min_length=1)."""
        response = client.post(
            "/api/postings",
            json={"title": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_list_postings_limit_out_of_range(self, client, auth_headers):
        """limit 범위 초과는 422."""
        response = client.get(
            "/api/postings?limit=0",
            headers=auth_headers,
        )
        assert response.status_code == 422

        response = client.get(
            "/api/postings?limit=201",
            headers=auth_headers,
        )
        assert response.status_code == 422
