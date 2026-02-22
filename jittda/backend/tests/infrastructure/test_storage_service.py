"""
Storage Service 단위 테스트.

validate_upload 함수와 StorageService의 local backend 동작을 검증한다.
S3/R2 backend는 boto3 의존성으로 인해 별도 통합 테스트에서 검증한다.
"""
from __future__ import annotations

import json
import os

import pytest

from infrastructure.storage.storage_service import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    StorageService,
    validate_upload,
)


# ── validate_upload 테스트 ───────────────────────────────────────────


class TestValidateUpload:
    """파일 업로드 검증 함수 테스트."""

    # ── 확장자 검증 ──────────────────────────────────────────────

    def test_resume_pdf_allowed(self):
        """resume에 .pdf 파일은 허용된다."""
        validate_upload(
            file_name="resume.pdf",
            file_bytes=b"fake pdf content",
            file_type="resume",
        )

    def test_resume_docx_disallowed(self):
        """resume에 .docx 파일은 허용되지 않는다."""
        with pytest.raises(ValueError, match="허용되지 않는 파일 형식"):
            validate_upload(
                file_name="resume.docx",
                file_bytes=b"fake docx content",
                file_type="resume",
            )

    def test_cover_letter_pdf_allowed(self):
        """cover_letter에 .pdf 파일은 허용된다."""
        validate_upload(
            file_name="cover.pdf",
            file_bytes=b"fake pdf content",
            file_type="cover_letter",
        )

    def test_cover_letter_docx_allowed(self):
        """cover_letter에 .docx 파일은 허용된다."""
        validate_upload(
            file_name="cover.docx",
            file_bytes=b"fake docx content",
            file_type="cover_letter",
        )

    def test_portfolio_pdf_allowed(self):
        """portfolio에 .pdf 파일은 허용된다."""
        validate_upload(
            file_name="portfolio.pdf",
            file_bytes=b"fake pdf content",
            file_type="portfolio",
        )

    def test_portfolio_docx_allowed(self):
        """portfolio에 .docx 파일은 허용된다."""
        validate_upload(
            file_name="portfolio.docx",
            file_bytes=b"fake docx content",
            file_type="portfolio",
        )

    def test_txt_extension_disallowed(self):
        """모든 타입에서 .txt 파일은 허용되지 않는다."""
        for file_type in ("resume", "cover_letter", "portfolio"):
            with pytest.raises(ValueError, match="허용되지 않는 파일 형식"):
                validate_upload(
                    file_name="document.txt",
                    file_bytes=b"text content",
                    file_type=file_type,
                )

    def test_exe_extension_disallowed(self):
        """실행 파일은 허용되지 않는다."""
        with pytest.raises(ValueError, match="허용되지 않는 파일 형식"):
            validate_upload(
                file_name="malware.exe",
                file_bytes=b"\x00\x01\x02",
                file_type="resume",
            )

    def test_unknown_file_type_disallowed(self):
        """등록되지 않은 file_type은 빈 허용 목록 -> 모든 확장자 거부."""
        with pytest.raises(ValueError, match="허용되지 않는 파일 형식"):
            validate_upload(
                file_name="document.pdf",
                file_bytes=b"content",
                file_type="unknown_type",
            )

    def test_case_insensitive_extension(self):
        """확장자 검증은 대소문자를 구분하지 않는다."""
        validate_upload(
            file_name="resume.PDF",
            file_bytes=b"fake pdf content",
            file_type="resume",
        )

    # ── 크기 검증 ────────────────────────────────────────────────

    def test_file_size_within_limit(self):
        """MAX_FILE_SIZE 이내의 파일은 통과한다."""
        validate_upload(
            file_name="small.pdf",
            file_bytes=b"x" * 1024,  # 1KB
            file_type="resume",
        )

    def test_file_size_at_limit(self):
        """정확히 MAX_FILE_SIZE인 파일은 통과한다."""
        validate_upload(
            file_name="exact.pdf",
            file_bytes=b"x" * MAX_FILE_SIZE,
            file_type="resume",
        )

    def test_file_size_exceeds_limit(self):
        """MAX_FILE_SIZE 초과 파일은 거부된다."""
        with pytest.raises(ValueError, match="파일 크기가"):
            validate_upload(
                file_name="huge.pdf",
                file_bytes=b"x" * (MAX_FILE_SIZE + 1),
                file_type="resume",
            )

    # ── MIME 타입 검증 ───────────────────────────────────────────

    def test_pdf_correct_mime_passes(self):
        """PDF 확장자 + application/pdf MIME은 통과한다."""
        validate_upload(
            file_name="document.pdf",
            file_bytes=b"fake pdf",
            file_type="resume",
            content_type="application/pdf",
        )

    def test_pdf_wrong_mime_fails(self):
        """PDF 확장자 + text/plain MIME은 거부된다."""
        with pytest.raises(ValueError, match="MIME 타입이 일치하지 않습니다"):
            validate_upload(
                file_name="document.pdf",
                file_bytes=b"fake pdf",
                file_type="resume",
                content_type="text/plain",
            )

    def test_docx_correct_mime_passes(self):
        """DOCX 확장자 + 올바른 MIME은 통과한다."""
        validate_upload(
            file_name="document.docx",
            file_bytes=b"fake docx",
            file_type="cover_letter",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    def test_docx_wrong_mime_fails(self):
        """DOCX 확장자 + application/pdf MIME은 거부된다."""
        with pytest.raises(ValueError, match="MIME 타입이 일치하지 않습니다"):
            validate_upload(
                file_name="document.docx",
                file_bytes=b"fake docx",
                file_type="cover_letter",
                content_type="application/pdf",
            )

    def test_no_content_type_skips_mime_check(self):
        """content_type이 None이면 MIME 검증을 건너뛴다."""
        validate_upload(
            file_name="document.pdf",
            file_bytes=b"fake pdf",
            file_type="resume",
            content_type=None,
        )

    # ── 상수 검증 ────────────────────────────────────────────────

    def test_allowed_extensions_resume(self):
        """resume 허용 확장자는 .pdf만 포함한다."""
        assert ALLOWED_EXTENSIONS["resume"] == {".pdf"}

    def test_allowed_extensions_cover_letter(self):
        """cover_letter 허용 확장자는 .pdf와 .docx를 포함한다."""
        assert ALLOWED_EXTENSIONS["cover_letter"] == {".pdf", ".docx"}

    def test_allowed_extensions_portfolio(self):
        """portfolio 허용 확장자는 .pdf와 .docx를 포함한다."""
        assert ALLOWED_EXTENSIONS["portfolio"] == {".pdf", ".docx"}

    def test_max_file_size_is_50mb(self):
        """MAX_FILE_SIZE는 50MB이다."""
        assert MAX_FILE_SIZE == 50 * 1024 * 1024


# ── StorageService Local Backend 테스트 ──────────────────────────────


class TestStorageServiceLocal:
    """StorageService의 local backend 동작 검증."""

    @pytest.fixture()
    def storage(self, tmp_path, monkeypatch):
        """tmp_path를 사용하는 local StorageService 인스턴스."""
        monkeypatch.setenv("STORAGE_BACKEND", "local")
        monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))
        # 싱글톤 캐시 초기화
        import infrastructure.storage.storage_service as mod
        mod._instance = None
        svc = StorageService()
        yield svc
        mod._instance = None

    def test_upload_file(self, storage, tmp_path):
        """upload_file로 바이너리 파일을 저장한다."""
        content = b"Hello, World! PDF content here."
        key = "resumes/test-resume.pdf"

        result_path = storage.upload_file(key, content, "application/pdf")

        expected_path = os.path.join(str(tmp_path), key)
        assert result_path == expected_path
        assert os.path.exists(expected_path)
        with open(expected_path, "rb") as f:
            assert f.read() == content

    def test_upload_file_creates_directories(self, storage, tmp_path):
        """upload_file은 중간 디렉토리를 자동 생성한다."""
        content = b"nested file content"
        key = "deep/nested/dir/file.pdf"

        storage.upload_file(key, content)

        expected_path = os.path.join(str(tmp_path), key)
        assert os.path.exists(expected_path)

    def test_upload_json(self, storage, tmp_path):
        """upload_json으로 JSON 데이터를 저장한다."""
        data = {"name": "Test", "scores": [1, 2, 3], "nested": {"key": "value"}}
        key = "results/analysis.json"

        result_path = storage.upload_json(key, data)

        expected_path = os.path.join(str(tmp_path), key)
        assert result_path == expected_path
        with open(expected_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["name"] == "Test"
        assert loaded["scores"] == [1, 2, 3]
        assert loaded["nested"]["key"] == "value"

    def test_upload_json_ensures_ascii_false(self, storage, tmp_path):
        """upload_json은 한글을 유니코드 이스케이프 없이 저장한다."""
        data = {"title": "백엔드 엔지니어", "description": "Python 개발자 모집"}
        key = "results/korean.json"

        storage.upload_json(key, data)

        expected_path = os.path.join(str(tmp_path), key)
        with open(expected_path, "r", encoding="utf-8") as f:
            raw = f.read()
        assert "백엔드 엔지니어" in raw
        assert "\\u" not in raw

    def test_download_file_success(self, storage, tmp_path):
        """upload 후 download_file로 정상 다운로드한다."""
        content = b"Download test content"
        key = "downloads/test.pdf"

        storage.upload_file(key, content)
        result = storage.download_file(key)

        assert result == content

    def test_download_file_not_found(self, storage):
        """존재하지 않는 파일 download는 None을 반환한다."""
        result = storage.download_file("nonexistent/file.pdf")
        assert result is None

    def test_get_local_path(self, storage, tmp_path):
        """get_local_path는 절대 경로를 반환한다."""
        key = "resumes/test.pdf"
        expected = os.path.join(str(tmp_path), key)
        assert storage.get_local_path(key) == expected

    def test_get_url_returns_none_for_local(self, storage):
        """local backend에서 get_url은 None을 반환한다."""
        result = storage.get_url("some/key.pdf")
        assert result is None

    def test_upload_then_download_roundtrip(self, storage):
        """업로드 -> 다운로드 왕복 테스트."""
        original = b"\x00\x01\x02\xff\xfe binary data"
        key = "roundtrip/binary.bin"

        storage.upload_file(key, original)
        downloaded = storage.download_file(key)

        assert downloaded == original

    def test_upload_overwrite(self, storage, tmp_path):
        """같은 key로 재업로드하면 덮어쓴다."""
        key = "overwrite/file.pdf"

        storage.upload_file(key, b"version 1")
        storage.upload_file(key, b"version 2")

        result = storage.download_file(key)
        assert result == b"version 2"

    def test_upload_json_roundtrip(self, storage):
        """JSON 업로드 -> 바이트 다운로드 -> 파싱 왕복."""
        data = {"key": "value", "number": 42}
        key = "json-roundtrip/data.json"

        storage.upload_json(key, data)
        downloaded_bytes = storage.download_file(key)

        parsed = json.loads(downloaded_bytes.decode("utf-8"))
        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    def test_backend_defaults_to_local(self, monkeypatch):
        """STORAGE_BACKEND 미설정 시 local이 기본이다."""
        monkeypatch.delenv("STORAGE_BACKEND", raising=False)
        monkeypatch.setenv("LOCAL_STORAGE_PATH", "/tmp/test-storage")
        import infrastructure.storage.storage_service as mod
        mod._instance = None
        svc = StorageService()
        assert svc._backend == "local"
        mod._instance = None


# ── get_storage 싱글톤 테스트 ────────────────────────────────────────


class TestGetStorage:
    """get_storage 싱글톤 패턴 테스트."""

    def test_get_storage_returns_same_instance(self, tmp_path, monkeypatch):
        """get_storage는 동일 인스턴스를 반환한다."""
        monkeypatch.setenv("STORAGE_BACKEND", "local")
        monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))

        import infrastructure.storage.storage_service as mod
        mod._instance = None

        from infrastructure.storage.storage_service import get_storage

        first = get_storage()
        second = get_storage()
        assert first is second

        mod._instance = None

    def test_get_storage_creates_new_after_reset(self, tmp_path, monkeypatch):
        """_instance를 None으로 초기화하면 새 인스턴스를 생성한다."""
        monkeypatch.setenv("STORAGE_BACKEND", "local")
        monkeypatch.setenv("LOCAL_STORAGE_PATH", str(tmp_path))

        import infrastructure.storage.storage_service as mod
        mod._instance = None

        from infrastructure.storage.storage_service import get_storage

        first = get_storage()
        mod._instance = None
        second = get_storage()
        assert first is not second

        mod._instance = None
