"""
Storage Service — local/R2/S3 추상화.

레거시 backend/app/services/storage_service.py 포팅.
STORAGE_BACKEND: "local" (기본) | "r2" | "s3"
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# 파일 타입별 허용 확장자
ALLOWED_EXTENSIONS: dict[str, set[str]] = {
    "resume": {".pdf"},
    "cover_letter": {".pdf", ".docx"},
    "portfolio": {".pdf", ".docx"},
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class StorageService:
    """Unified storage interface: local filesystem or cloud object store."""

    def __init__(self) -> None:
        self._backend = os.environ.get("STORAGE_BACKEND", "local")
        self._local_path = os.environ.get("LOCAL_STORAGE_PATH", "/data/uploads")
        self._s3_client = None
        self._bucket: str | None = None
        self._public_url: str | None = None

        if self._backend in ("r2", "s3"):
            self._init_s3()

    def _init_s3(self) -> None:
        """Initialize S3-compatible client (R2/S3)."""
        import boto3

        endpoint_url = os.environ.get("S3_ENDPOINT_URL")
        access_key = os.environ.get("S3_ACCESS_KEY_ID", os.environ.get("AWS_ACCESS_KEY_ID"))
        secret_key = os.environ.get("S3_SECRET_ACCESS_KEY", os.environ.get("AWS_SECRET_ACCESS_KEY"))
        self._bucket = os.environ.get("S3_BUCKET", "jittda-uploads")
        self._public_url = os.environ.get("S3_PUBLIC_URL")

        kwargs: dict = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
        }
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
            kwargs["region_name"] = "auto"

        self._s3_client = boto3.client("s3", **kwargs)
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self._s3_client.head_bucket(Bucket=self._bucket)
        except Exception:
            try:
                self._s3_client.create_bucket(Bucket=self._bucket)
                logger.info("Created bucket: %s", self._bucket)
            except Exception as e:
                logger.warning("Could not create bucket %s: %s", self._bucket, e)

    # ─── Public API ───────────────────────────────────────────

    def upload_file(
        self, key: str, file_bytes: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        """Upload raw file bytes. Returns storage path or URL."""
        if self._backend in ("r2", "s3"):
            return self._upload_s3(key, file_bytes, content_type)
        return self._save_local_bytes(key, file_bytes)

    def upload_json(self, key: str, data: dict) -> str:
        """Upload JSON data. Returns storage path or URL."""
        body = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        if self._backend in ("r2", "s3"):
            return self._upload_s3(key, body.encode("utf-8"), "application/json")
        return self._save_local(key, data)

    def download_file(self, key: str) -> bytes | None:
        """Download raw file bytes by key."""
        if self._backend in ("r2", "s3"):
            return self._download_s3_bytes(key)
        return self._load_local_bytes(key)

    def get_url(self, key: str) -> str | None:
        """Get public URL for a key."""
        if self._backend in ("r2", "s3") and self._public_url:
            return f"{self._public_url.rstrip('/')}/{key}"
        return None

    def get_local_path(self, key: str) -> str:
        """Get absolute local filesystem path for a key."""
        return os.path.join(self._local_path, key)

    # ─── S3-compatible Backend ────────────────────────────────

    def _upload_s3(self, key: str, body: bytes, content_type: str) -> str:
        self._s3_client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
        url = f"s3://{self._bucket}/{key}"
        logger.info("Uploaded to %s", url)
        return url

    def _download_s3_bytes(self, key: str) -> bytes | None:
        try:
            response = self._s3_client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except Exception as e:
            logger.error("S3 download failed for %s: %s", key, e)
            return None

    # ─── Local Backend ────────────────────────────────────────

    def _save_local(self, key: str, data: dict) -> str:
        path = os.path.join(self._local_path, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Saved locally to %s", path)
        return path

    def _save_local_bytes(self, key: str, file_bytes: bytes) -> str:
        path = os.path.join(self._local_path, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(file_bytes)
        logger.info("Saved locally to %s", path)
        return path

    def _load_local_bytes(self, key: str) -> bytes | None:
        path = os.path.join(self._local_path, key)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()


_instance: StorageService | None = None


def get_storage() -> StorageService:
    """Singleton storage service."""
    global _instance
    if _instance is None:
        _instance = StorageService()
    return _instance


def validate_upload(
    file_name: str,
    file_bytes: bytes,
    file_type: str,
    content_type: str | None = None,
) -> None:
    """파일 업로드 검증: 확장자 + 크기 + MIME 타입."""
    # 확장자 검증
    ext = Path(file_name).suffix.lower()
    allowed = ALLOWED_EXTENSIONS.get(file_type, set())
    if ext not in allowed:
        raise ValueError(
            f"허용되지 않는 파일 형식입니다. {file_type}에 허용: {', '.join(sorted(allowed))}"
        )

    # 크기 검증
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError(f"파일 크기가 {MAX_FILE_SIZE // (1024*1024)}MB를 초과합니다.")

    # MIME 타입 검증
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    expected_mime = mime_map.get(ext)
    if content_type and expected_mime and content_type != expected_mime:
        raise ValueError(f"파일 확장자와 MIME 타입이 일치하지 않습니다: {ext} vs {content_type}")
