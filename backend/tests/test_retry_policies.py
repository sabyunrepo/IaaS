"""Workflow retry policies and document parser limits tests."""
import pytest
from datetime import timedelta


class TestRetryPolicies:
    def test_default_retry_exists(self):
        from app.workflows.interview_workflow import DEFAULT_RETRY
        assert DEFAULT_RETRY.maximum_attempts == 3

    def test_llm_retry_exists(self):
        from app.workflows.interview_workflow import LLM_RETRY
        assert LLM_RETRY.maximum_attempts == 3
        assert "ValueError" in LLM_RETRY.non_retryable_error_types

    def test_external_api_retry_exists(self):
        from app.workflows.interview_workflow import EXTERNAL_API_RETRY
        assert EXTERNAL_API_RETRY.maximum_attempts == 4

    def test_default_retry_backoff(self):
        from app.workflows.interview_workflow import DEFAULT_RETRY
        assert DEFAULT_RETRY.backoff_coefficient == 2.0

    def test_llm_retry_initial_interval(self):
        from app.workflows.interview_workflow import LLM_RETRY
        assert LLM_RETRY.initial_interval == timedelta(seconds=2)

    def test_external_api_max_interval(self):
        from app.workflows.interview_workflow import EXTERNAL_API_RETRY
        assert EXTERNAL_API_RETRY.maximum_interval == timedelta(seconds=120)


class TestRetryPolicyImport:
    def test_retry_policy_imported(self):
        from temporalio.common import RetryPolicy
        assert RetryPolicy is not None

    def test_workflow_uses_retry_policy(self):
        import inspect
        from app.workflows.interview_workflow import InterviewGenerationWorkflow
        source = inspect.getsource(InterviewGenerationWorkflow.run)
        assert "retry_policy" in source


class TestDocumentParserLimits:
    def test_max_file_size_constant(self):
        from app.services.document_parser import MAX_FILE_SIZE_MB
        assert MAX_FILE_SIZE_MB == 50

    def test_max_file_size_bytes(self):
        from app.services.document_parser import MAX_FILE_SIZE_BYTES
        assert MAX_FILE_SIZE_BYTES == 50 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_large_file_rejected(self, tmp_path):
        # Create a file that's "too large" by lowering the threshold temporarily
        from app.services import document_parser
        original = document_parser.MAX_FILE_SIZE_BYTES
        document_parser.MAX_FILE_SIZE_BYTES = 10  # 10 bytes

        f = tmp_path / "big.txt"
        f.write_text("A" * 100)

        try:
            with pytest.raises(ValueError, match="File too large"):
                await document_parser.parse_document(str(f))
        finally:
            document_parser.MAX_FILE_SIZE_BYTES = original

    @pytest.mark.asyncio
    async def test_small_file_accepted(self, tmp_path):
        from app.services.document_parser import parse_document
        f = tmp_path / "small.txt"
        f.write_text("Hello")
        result = await parse_document(str(f))
        assert result.text == "Hello"
