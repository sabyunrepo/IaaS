"""Unit tests for auth service (JWT, API Key, Fernet)."""
import pytest
from app.services.auth_service import (
    create_jwt, verify_jwt,
    create_api_key, verify_api_key, hash_api_key,
    encrypt_token, decrypt_token,
    API_KEY_PREFIX,
)


class TestJWT:
    def test_create_and_verify(self):
        payload = {"sub": "user-123", "email": "test@test.com"}
        token = create_jwt(payload)
        assert isinstance(token, str)
        decoded = verify_jwt(token)
        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["email"] == "test@test.com"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_invalid_token(self):
        result = verify_jwt("invalid.token.string")
        assert result is None

    def test_empty_token(self):
        result = verify_jwt("")
        assert result is None


class TestAPIKey:
    def test_create_api_key_format(self):
        raw, hashed = create_api_key()
        assert raw.startswith(API_KEY_PREFIX)
        assert len(hashed) == 64  # SHA-256 hex digest

    def test_verify_api_key(self):
        raw, hashed = create_api_key()
        assert verify_api_key(raw, hashed) is True
        assert verify_api_key("wrong_key", hashed) is False

    def test_hash_api_key_consistent(self):
        raw, hashed = create_api_key()
        assert hash_api_key(raw) == hashed

    def test_unique_keys(self):
        key1, _ = create_api_key()
        key2, _ = create_api_key()
        assert key1 != key2


class TestFernet:
    def test_encrypt_produces_output(self):
        encrypted = encrypt_token("test-token")
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        assert encrypted != "test-token"

    def test_get_fernet_returns_instance(self):
        from app.services.auth_service import get_fernet
        from cryptography.fernet import Fernet
        f = get_fernet()
        assert isinstance(f, Fernet)
