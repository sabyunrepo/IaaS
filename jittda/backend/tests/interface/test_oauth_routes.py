"""
OAuth 인증 라우트 테스트 — redirect_uri 검증, exchange 플로우, 방어 로깅.

Phase 13 (JIT-347): OAuth E2E 테스트 코드.
ProxyHeadersMiddleware 설정 검증 + OAuth 전체 플로우 단위 테스트.
"""

from __future__ import annotations

import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient

from interface.api.middleware.auth import create_token


# ── Fixtures ─────────────────────────────────────────────────────────
# _mock_observability autouse fixture는 conftest.py에서 제공


@pytest.fixture()
def mock_pool():
    """DB Pool mock."""
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
def app(mock_pool):
    """테스트용 FastAPI 앱."""
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
def proxy_app(mock_pool):
    """TRUSTED_PROXY_HOSTS=* 인 앱 — 프록시 헤더 테스트용."""
    with (
        patch("infrastructure.persistence.pool._pool", mock_pool),
        patch("infrastructure.persistence.pool.get_pool", return_value=mock_pool),
        patch.dict("os.environ", {"TRUSTED_PROXY_HOSTS": "*"}),
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


@pytest.fixture()
def proxy_client(proxy_app):
    """프록시 헤더 신뢰 TestClient."""
    return TestClient(proxy_app, raise_server_exceptions=False)


# ── OAuth 리다이렉트 테스트 ──────────────────────────────────────────


class TestOAuthRedirect:
    """OAuth 로그인 엔드포인트 리다이렉트 검증."""

    def test_google_login_calls_authorize_redirect(self, client):
        """Google login은 authorize_redirect를 호출하고 redirect_uri에 callback 경로를 포함한다."""
        with patch("interface.api.routes.auth.oauth") as mock_oauth:
            mock_oauth.google.authorize_redirect = AsyncMock(
                return_value=RedirectResponse("https://accounts.google.com/o/oauth2/auth")
            )
            response = client.get("/api/auth/google", follow_redirects=False)
            assert response.status_code in (302, 307)

            call_args = mock_oauth.google.authorize_redirect.call_args
            redirect_uri = call_args[0][1]
            assert "/api/auth/google/callback" in redirect_uri

    def test_github_login_calls_authorize_redirect(self, client):
        """GitHub login은 authorize_redirect를 호출하고 redirect_uri에 callback 경로를 포함한다."""
        with patch("interface.api.routes.auth.oauth") as mock_oauth:
            mock_oauth.github.authorize_redirect = AsyncMock(
                return_value=RedirectResponse("https://github.com/login/oauth/authorize")
            )
            response = client.get("/api/auth/github", follow_redirects=False)
            assert response.status_code in (302, 307)

            call_args = mock_oauth.github.authorize_redirect.call_args
            redirect_uri = call_args[0][1]
            assert "/api/auth/github/callback" in redirect_uri


# ── ProxyHeaders 미들웨어 테스트 ─────────────────────────────────────


class TestProxyHeaders:
    """ProxyHeadersMiddleware 설정 및 동작 검증."""

    def test_proxy_headers_middleware_installed(self, app):
        """ProxyHeadersMiddleware가 user_middleware에 등록되어 있다."""
        from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

        middleware_classes = [m.cls for m in app.user_middleware]
        assert ProxyHeadersMiddleware in middleware_classes

    def test_forwarded_proto_reflected_in_redirect_uri(self, proxy_client):
        """X-Forwarded-Proto: https가 redirect_uri scheme에 반영된다."""
        with patch("interface.api.routes.auth.oauth") as mock_oauth:
            mock_oauth.google.authorize_redirect = AsyncMock(
                return_value=RedirectResponse("https://accounts.google.com/")
            )
            proxy_client.get(
                "/api/auth/google",
                headers={
                    "X-Forwarded-Proto": "https",
                    "X-Forwarded-For": "10.0.0.1",
                },
                follow_redirects=False,
            )

            call_args = mock_oauth.google.authorize_redirect.call_args
            redirect_uri = call_args[0][1]
            assert redirect_uri.startswith("https://"), (
                f"redirect_uri가 https로 시작하지 않음: {redirect_uri}"
            )


# ── OAuth 코드 교환 테스트 ───────────────────────────────────────────


class TestOAuthExchange:
    """임시 코드 → JWT 교환 플로우 검증."""

    def test_exchange_valid_code(self, client):
        """유효한 임시 코드로 JWT를 교환한다."""
        from interface.api.routes.auth import _auth_codes

        test_jwt = create_token("test-user", "test@jittda.com")
        test_code = "test-valid-code-12345"
        _auth_codes[test_code] = (test_jwt, time.time() + 30)

        response = client.post(f"/api/auth/exchange?code={test_code}")
        assert response.status_code == 200
        data = response.json()
        assert data["token"] == test_jwt
        assert test_code not in _auth_codes

    def test_exchange_expired_code_returns_401(self, client):
        """만료된 코드는 401을 반환한다."""
        from interface.api.routes.auth import _auth_codes

        test_jwt = create_token("test-user", "test@jittda.com")
        test_code = "test-expired-code"
        _auth_codes[test_code] = (test_jwt, time.time() - 10)

        response = client.post(f"/api/auth/exchange?code={test_code}")
        assert response.status_code == 401

    def test_exchange_invalid_code_returns_401(self, client):
        """존재하지 않는 코드는 401을 반환한다."""
        response = client.post("/api/auth/exchange?code=nonexistent-code")
        assert response.status_code == 401

    def test_exchange_code_single_use(self, client):
        """코드는 1회만 사용 가능하다 (2회차는 401)."""
        from interface.api.routes.auth import _auth_codes

        test_jwt = create_token("test-user", "test@jittda.com")
        test_code = "test-single-use-code"
        _auth_codes[test_code] = (test_jwt, time.time() + 30)

        response1 = client.post(f"/api/auth/exchange?code={test_code}")
        assert response1.status_code == 200

        response2 = client.post(f"/api/auth/exchange?code={test_code}")
        assert response2.status_code == 401


# ── OAuth Callback 테스트 ────────────────────────────────────────────


class TestOAuthCallbacks:
    """OAuth provider callback 처리 검증."""

    def test_google_callback_upserts_user_and_redirects(self, client):
        """Google callback은 사용자를 upsert하고 프론트엔드로 리다이렉트한다."""
        mock_userinfo = {
            "email": "user@gmail.com",
            "name": "Test User",
            "sub": "google-123",
        }
        with (
            patch("interface.api.routes.auth.oauth") as mock_oauth,
            patch("interface.api.routes.auth.UserRepository") as MockRepo,
        ):
            mock_oauth.google.authorize_access_token = AsyncMock(
                return_value={"userinfo": mock_userinfo}
            )
            mock_repo = MockRepo.return_value
            mock_repo.upsert_oauth_user = AsyncMock(
                return_value={"id": str(uuid.uuid4()), "email": "user@gmail.com"}
            )

            response = client.get("/api/auth/google/callback", follow_redirects=False)
            assert response.status_code == 307
            location = response.headers["location"]
            assert "/auth/callback?code=" in location

            mock_repo.upsert_oauth_user.assert_called_once_with(
                email="user@gmail.com",
                name="Test User",
                oauth_provider="google",
                oauth_id="google-123",
            )

    def test_google_callback_missing_userinfo_returns_400(self, client):
        """Google에서 userinfo가 없으면 400을 반환한다."""
        with patch("interface.api.routes.auth.oauth") as mock_oauth:
            mock_oauth.google.authorize_access_token = AsyncMock(
                return_value={"access_token": "token_without_userinfo"}
            )
            response = client.get("/api/auth/google/callback")
            assert response.status_code == 400

    def test_github_callback_upserts_user_and_redirects(self, client):
        """GitHub callback은 사용자를 upsert하고 프론트엔드로 리다이렉트한다."""
        mock_user_resp = MagicMock()
        mock_user_resp.json.return_value = {
            "id": 12345,
            "login": "testuser",
            "name": "Test User",
            "email": "user@github.com",
        }
        with (
            patch("interface.api.routes.auth.oauth") as mock_oauth,
            patch("interface.api.routes.auth.UserRepository") as MockRepo,
        ):
            mock_oauth.github.authorize_access_token = AsyncMock(
                return_value={"access_token": "gho_test123"}
            )
            mock_oauth.github.get = AsyncMock(return_value=mock_user_resp)
            mock_repo = MockRepo.return_value
            mock_repo.upsert_oauth_user = AsyncMock(
                return_value={"id": str(uuid.uuid4()), "email": "user@github.com"}
            )

            response = client.get("/api/auth/github/callback", follow_redirects=False)
            assert response.status_code == 307
            location = response.headers["location"]
            assert "/auth/callback?code=" in location

            mock_repo.upsert_oauth_user.assert_called_once_with(
                email="user@github.com",
                name="Test User",
                oauth_provider="github",
                oauth_id="12345",
            )

    def test_github_callback_fallback_email(self, client):
        """GitHub에서 email이 없으면 emails API로 fallback한다."""
        mock_user_resp = MagicMock()
        mock_user_resp.json.return_value = {
            "id": 99999,
            "login": "noemailuser",
            "name": "No Email",
            "email": None,
        }
        mock_emails_resp = MagicMock()
        mock_emails_resp.json.return_value = [
            {"email": "primary@example.com", "primary": True, "verified": True},
            {"email": "secondary@example.com", "primary": False, "verified": True},
        ]
        with (
            patch("interface.api.routes.auth.oauth") as mock_oauth,
            patch("interface.api.routes.auth.UserRepository") as MockRepo,
        ):
            mock_oauth.github.authorize_access_token = AsyncMock(
                return_value={"access_token": "gho_test"}
            )
            mock_oauth.github.get = AsyncMock(
                side_effect=[mock_user_resp, mock_emails_resp]
            )
            mock_repo = MockRepo.return_value
            mock_repo.upsert_oauth_user = AsyncMock(
                return_value={"id": str(uuid.uuid4()), "email": "primary@example.com"}
            )

            response = client.get("/api/auth/github/callback", follow_redirects=False)
            assert response.status_code == 307

            call_kwargs = mock_repo.upsert_oauth_user.call_args[1]
            assert call_kwargs["email"] == "primary@example.com"


# ── Localhost 경고 로깅 테스트 ───────────────────────────────────────


class TestLocalhostWarning:
    """프로덕션 환경에서 localhost redirect 방어 로깅 검증."""

    def test_warn_if_localhost_in_production(self):
        """프로덕션에서 localhost redirect_uri 생성 시 경고 로그를 남긴다."""
        from interface.api.routes.auth import _warn_if_localhost_redirect

        with patch.dict("os.environ", {"ENV": "production"}):
            with patch("structlog.get_logger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                _warn_if_localhost_redirect(
                    "http://localhost:8000/api/auth/google/callback", "google"
                )

                mock_logger.warning.assert_called_once()
                call_args = mock_logger.warning.call_args
                assert call_args[0][0] == "oauth_redirect_uri_suspicious"

    def test_no_warn_in_development(self):
        """개발 환경에서는 경고하지 않는다."""
        from interface.api.routes.auth import _warn_if_localhost_redirect

        with patch.dict("os.environ", {"ENV": "development"}):
            # structlog import가 실행되지 않으므로 mock 불필요
            _warn_if_localhost_redirect(
                "http://localhost:8000/api/auth/google/callback", "google"
            )

    def test_no_warn_for_production_url(self):
        """프로덕션 URL은 경고하지 않는다."""
        from interface.api.routes.auth import _warn_if_localhost_redirect

        with patch.dict("os.environ", {"ENV": "production"}):
            with patch("structlog.get_logger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                _warn_if_localhost_redirect(
                    "https://dev.jittda.com/api/auth/google/callback", "google"
                )

                mock_logger.warning.assert_not_called()


# ── /api/auth/me 테스트 ──────────────────────────────────────────────


class TestAuthMe:
    """인증된 사용자 정보 조회."""

    def test_get_me_authenticated(self, client):
        """인증된 사용자는 본인 정보를 조회할 수 있다."""
        token = create_token("user-123", "test@jittda.com")
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user-123"
        assert data["email"] == "test@jittda.com"

    def test_get_me_unauthenticated(self, client):
        """미인증 요청은 401을 반환한다."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """잘못된 토큰은 401을 반환한다."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
