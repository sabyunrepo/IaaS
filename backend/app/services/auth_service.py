"""
backend/app/services/auth_service.py
JWT 생성/검증, API Key 생성/검증, Fernet 암호화
"""
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.core.config import settings

logger = logging.getLogger(__name__)

# --- JWT ---

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24


def create_jwt(payload: dict, expires_delta: timedelta | None = None) -> str:
    """JWT 토큰 생성"""
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt(token: str) -> dict:
    """JWT 토큰 검증 → payload 반환. 실패 시 None."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


# --- API Key ---

API_KEY_PREFIX = "vnt_"


def create_api_key() -> tuple[str, str]:
    """API Key 생성 → (raw_key, sha256_hash)"""
    raw = API_KEY_PREFIX + secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """API Key 검증 (constant-time comparison)"""
    computed = hashlib.sha256(raw_key.encode()).hexdigest()
    return hmac.compare_digest(computed, stored_hash)


def hash_api_key(raw_key: str) -> str:
    """API Key → SHA-256 해시"""
    return hashlib.sha256(raw_key.encode()).hexdigest()


# --- Fernet 암호화 (OAuth access_token 저장용) ---

_DEV_FERNET_KEY = Fernet.generate_key()


def get_fernet() -> Fernet:
    """Fernet 인스턴스 (OAUTH_TOKEN_ENCRYPTION_KEY)"""
    key = settings.OAUTH_TOKEN_ENCRYPTION_KEY
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        if not getattr(settings, "is_local", True):
            raise ValueError(
                "OAUTH_TOKEN_ENCRYPTION_KEY가 유효한 Fernet 키가 아닙니다. "
                "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" 으로 생성하세요."
            )
        logger.warning("OAUTH_TOKEN_ENCRYPTION_KEY 무효 → 개발용 임시 키 사용 (프로세스 재시작 시 토큰 무효화)")
        return Fernet(_DEV_FERNET_KEY)


def encrypt_token(token: str) -> str:
    """OAuth access_token 암호화"""
    return get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """OAuth access_token 복호화"""
    return get_fernet().decrypt(encrypted.encode()).decode()
