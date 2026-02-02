"""Unit tests for storage service."""
import json
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock


class TestStorageServiceLocal:
    def test_importable(self):
        from app.services.storage_service import StorageService, get_storage
        assert StorageService is not None
        assert callable(get_storage)

    def test_upload_and_download_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from app.services.storage_service import StorageService
            svc = StorageService.__new__(StorageService)
            svc._backend = "local"
            svc._local_path = tmpdir
            svc._r2_client = None
            svc._bucket = None
            svc._public_url = None

            data = {"questions": [{"id": 1, "text": "test"}]}
            path = svc.upload_json("test/output.json", data)
            assert os.path.exists(path)

            loaded = svc.download_json("test/output.json")
            assert loaded["questions"][0]["text"] == "test"

    def test_download_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from app.services.storage_service import StorageService
            svc = StorageService.__new__(StorageService)
            svc._backend = "local"
            svc._local_path = tmpdir
            svc._r2_client = None
            svc._bucket = None
            svc._public_url = None

            assert svc.download_json("nonexistent.json") is None

    def test_upload_file_local(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from app.services.storage_service import StorageService
            svc = StorageService.__new__(StorageService)
            svc._backend = "local"
            svc._local_path = tmpdir
            svc._r2_client = None
            svc._bucket = None
            svc._public_url = None

            path = svc.upload_file("docs/resume.pdf", b"fake-pdf-content", "application/pdf")
            assert os.path.exists(path)
            with open(path, "rb") as f:
                assert f.read() == b"fake-pdf-content"


class TestStorageR2Config:
    def test_r2_endpoint_property(self):
        from app.core.config import Settings
        s = Settings(R2_ACCOUNT_ID="abc123", STORAGE_BACKEND="r2")
        assert s.r2_endpoint == "https://abc123.r2.cloudflarestorage.com"

    def test_r2_endpoint_none_without_account(self):
        from app.core.config import Settings
        s = Settings(STORAGE_BACKEND="local")
        assert s.r2_endpoint is None

    def test_storage_config_r2(self):
        from app.core.config import Settings
        s = Settings(R2_ACCOUNT_ID="abc123", STORAGE_BACKEND="r2", R2_BUCKET="my-bucket")
        cfg = s.storage_config
        assert cfg["backend"] == "r2"
        assert cfg["bucket"] == "my-bucket"
        assert "r2.cloudflarestorage.com" in cfg["endpoint_url"]

    def test_storage_config_local(self):
        from app.core.config import Settings
        s = Settings(STORAGE_BACKEND="local")
        cfg = s.storage_config
        assert cfg["backend"] == "local"
        assert "path" in cfg


class TestStorageR2Methods:
    def test_r2_methods_exist(self):
        from app.services.storage_service import StorageService
        assert hasattr(StorageService, "_upload_r2")
        assert hasattr(StorageService, "_download_r2")
        assert hasattr(StorageService, "_ensure_bucket")
        assert hasattr(StorageService, "get_public_url")

    def test_public_url_local_returns_none(self):
        from app.services.storage_service import StorageService
        svc = StorageService.__new__(StorageService)
        svc._backend = "local"
        svc._public_url = None
        assert svc.get_public_url("test/file.json") is None

    def test_public_url_r2(self):
        from app.services.storage_service import StorageService
        svc = StorageService.__new__(StorageService)
        svc._backend = "r2"
        svc._public_url = "https://pub-xxx.r2.dev"
        assert svc.get_public_url("outputs/script.json") == "https://pub-xxx.r2.dev/outputs/script.json"


class TestFinalizationUsesStorage:
    def test_finalization_imports_storage(self):
        import inspect
        from app.workflows.activities import finalization
        source = inspect.getsource(finalization)
        assert "get_storage" in source
        assert "upload_json" in source
