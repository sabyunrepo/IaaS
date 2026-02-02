"""
backend/app/services/storage_service.py
Object Storage 서비스 — local 파일시스템 또는 Cloudflare R2 지원
STORAGE_BACKEND: "local" (기본) | "r2"
"""
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class StorageService:
    """Unified storage interface: local filesystem or Cloudflare R2."""

    def __init__(self):
        from app.core.config import settings
        self._backend = settings.STORAGE_BACKEND  # "local" | "r2"
        self._local_path = settings.LOCAL_STORAGE_PATH
        self._r2_client = None
        self._bucket = None
        self._public_url = None

        if self._backend == "r2":
            self._init_r2(settings)

    def _init_r2(self, settings) -> None:
        """Initialize Cloudflare R2 client (S3-compatible API)."""
        import boto3
        if not settings.R2_ACCOUNT_ID:
            raise ValueError("R2_ACCOUNT_ID is required when STORAGE_BACKEND=r2")

        self._bucket = settings.R2_BUCKET
        self._public_url = settings.R2_PUBLIC_URL
        self._r2_client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create R2 bucket if it doesn't exist."""
        try:
            self._r2_client.head_bucket(Bucket=self._bucket)
        except Exception:
            try:
                self._r2_client.create_bucket(Bucket=self._bucket)
                logger.info(f"Created R2 bucket: {self._bucket}")
            except Exception as e:
                logger.warning(f"Could not create bucket {self._bucket}: {e}")

    # ─── Public API ───────────────────────────────────────────

    def upload_json(self, key: str, data: dict) -> str:
        """Upload JSON data. Returns storage path or URL."""
        body = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        if self._backend == "r2":
            return self._upload_r2(key, body.encode("utf-8"), "application/json")
        return self._save_local(key, data)

    def upload_file(self, key: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload raw file bytes."""
        if self._backend == "r2":
            return self._upload_r2(key, file_bytes, content_type)
        return self._save_local_bytes(key, file_bytes)

    def download_json(self, key: str) -> dict | None:
        """Download JSON data by key."""
        if self._backend == "r2":
            return self._download_r2(key)
        return self._load_local(key)

    def get_public_url(self, key: str) -> str | None:
        """Get public URL for a key (R2 public bucket only)."""
        if self._backend == "r2" and self._public_url:
            return f"{self._public_url.rstrip('/')}/{key}"
        return None

    # ─── R2 Backend ───────────────────────────────────────────

    def _upload_r2(self, key: str, body: bytes, content_type: str) -> str:
        self._r2_client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
        url = f"r2://{self._bucket}/{key}"
        logger.info(f"Uploaded to {url}")
        return url

    def _download_r2(self, key: str) -> dict | None:
        try:
            response = self._r2_client.get_object(Bucket=self._bucket, Key=key)
            return json.loads(response["Body"].read().decode("utf-8"))
        except Exception as e:
            logger.error(f"R2 download failed for {key}: {e}")
            return None

    # ─── Local Backend ────────────────────────────────────────

    def _save_local(self, key: str, data: dict) -> str:
        path = os.path.join(self._local_path, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"Saved locally to {path}")
        return path

    def _save_local_bytes(self, key: str, file_bytes: bytes) -> str:
        path = os.path.join(self._local_path, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"Saved locally to {path}")
        return path

    def _load_local(self, key: str) -> dict | None:
        path = os.path.join(self._local_path, key)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)


_instance: StorageService | None = None


def get_storage() -> StorageService:
    """Singleton storage service."""
    global _instance
    if _instance is None:
        _instance = StorageService()
    return _instance
