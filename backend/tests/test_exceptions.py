"""Unit tests for custom exception hierarchy."""
import pytest
from app.exceptions import (
    VantictBaseError, JobNotFoundError, JobAlreadyExistsError,
    AuthenticationError, AuthorizationError, ValidationError,
    RateLimitError, TemporalError, DocumentParseError, LinkedInFetchError,
)


class TestExceptionHierarchy:
    def test_job_not_found(self):
        err = JobNotFoundError("abc-123")
        assert err.status_code == 404
        assert err.code == "JOB_NOT_FOUND"
        assert "abc-123" in err.message

    def test_job_already_exists(self):
        err = JobAlreadyExistsError("abc-123")
        assert err.status_code == 409

    def test_authentication_error(self):
        err = AuthenticationError()
        assert err.status_code == 401
        assert err.code == "UNAUTHORIZED"

    def test_authorization_error(self):
        err = AuthorizationError()
        assert err.status_code == 403
        assert err.code == "FORBIDDEN"

    def test_validation_error(self):
        err = ValidationError("bad input")
        assert err.status_code == 422
        assert "bad input" in err.message

    def test_rate_limit_error(self):
        err = RateLimitError()
        assert err.status_code == 429

    def test_temporal_error(self):
        err = TemporalError("workflow crashed")
        assert err.status_code == 500
        assert "workflow crashed" in err.message

    def test_document_parse_error(self):
        err = DocumentParseError("corrupt PDF", source="resume.pdf")
        assert err.status_code == 422
        assert err.source == "resume.pdf"

    def test_linkedin_fetch_error(self):
        err = LinkedInFetchError()
        assert err.status_code == 502

    def test_all_inherit_from_base(self):
        errors = [
            JobNotFoundError("x"), AuthenticationError(),
            AuthorizationError(), ValidationError("x"),
            RateLimitError(), TemporalError(), LinkedInFetchError(),
        ]
        for err in errors:
            assert isinstance(err, VantictBaseError)

    def test_detail_structure(self):
        err = JobNotFoundError("test-id")
        assert err.detail == {"code": "JOB_NOT_FOUND", "message": "Job not found: test-id"}
