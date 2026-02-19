"""
LLM 클라이언트 테스트 — InstructorClient, LangfusePromptManager

외부 서비스(OpenAI, Langfuse)는 모두 mock 처리.
실제 API 호출 없음.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

instructor = pytest.importorskip("instructor")
pytest.importorskip("langfuse")
pytest.importorskip("openai")

from pydantic import BaseModel  # noqa: E402

from infrastructure.llm.instructor_client import InstructorClient  # noqa: E402
from infrastructure.llm.langfuse_client import LangfusePromptManager  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


class _SampleModel(BaseModel):
    name: str
    value: int


_MESSAGES = [{"role": "user", "content": "Hello"}]


# ---------------------------------------------------------------------------
# InstructorClient
# ---------------------------------------------------------------------------


class TestInstructorClientInit:
    def test_default_model_and_retries(self):
        mock_raw = MagicMock()
        mock_patched = MagicMock()

        with (
            patch("infrastructure.llm.instructor_client.instructor.from_openai", return_value=mock_patched),
            patch("infrastructure.llm.instructor_client.AsyncOpenAI", return_value=mock_raw),
        ):
            client = InstructorClient(api_key="test-key")

        assert client._model == "kimi-k2.5"
        assert client._max_retries == 3
        assert client._client is mock_patched

    def test_custom_model_and_retries(self):
        mock_raw = MagicMock()
        mock_patched = MagicMock()

        with (
            patch("infrastructure.llm.instructor_client.instructor.from_openai", return_value=mock_patched),
            patch("infrastructure.llm.instructor_client.AsyncOpenAI", return_value=mock_raw),
        ):
            client = InstructorClient(
                api_key="key",
                base_url="https://custom.api/v1",
                model="custom-model",
                max_retries=5,
            )

        assert client._model == "custom-model"
        assert client._max_retries == 5

    def test_openai_client_created_with_correct_args(self):
        mock_raw = MagicMock()

        with (
            patch("infrastructure.llm.instructor_client.instructor.from_openai"),
            patch("infrastructure.llm.instructor_client.AsyncOpenAI", return_value=mock_raw) as mock_cls,
        ):
            InstructorClient(api_key="my-key", base_url="https://example.com/v1")

        mock_cls.assert_called_once_with(api_key="my-key", base_url="https://example.com/v1")


class TestInstructorClientCreate:
    @pytest.mark.asyncio
    async def test_create_calls_completions_with_defaults(self):
        mock_completions = AsyncMock(return_value=_SampleModel(name="test", value=1))
        mock_inner_client = MagicMock()
        mock_inner_client.chat.completions.create = mock_completions

        with (
            patch("infrastructure.llm.instructor_client.instructor.from_openai", return_value=mock_inner_client),
            patch("infrastructure.llm.instructor_client.AsyncOpenAI"),
        ):
            client = InstructorClient(api_key="key")
            result = await client.create(
                response_model=_SampleModel,
                messages=_MESSAGES,
            )

        mock_completions.assert_awaited_once_with(
            model="kimi-k2.5",
            response_model=_SampleModel,
            messages=_MESSAGES,
            temperature=0.7,
            max_retries=3,
        )
        assert result.name == "test"
        assert result.value == 1

    @pytest.mark.asyncio
    async def test_create_overrides_model_and_retries(self):
        mock_completions = AsyncMock(return_value=_SampleModel(name="x", value=0))
        mock_inner_client = MagicMock()
        mock_inner_client.chat.completions.create = mock_completions

        with (
            patch("infrastructure.llm.instructor_client.instructor.from_openai", return_value=mock_inner_client),
            patch("infrastructure.llm.instructor_client.AsyncOpenAI"),
        ):
            client = InstructorClient(api_key="key")
            await client.create(
                response_model=_SampleModel,
                messages=_MESSAGES,
                model="other-model",
                temperature=0.0,
                max_retries=1,
            )

        mock_completions.assert_awaited_once_with(
            model="other-model",
            response_model=_SampleModel,
            messages=_MESSAGES,
            temperature=0.0,
            max_retries=1,
        )


# ---------------------------------------------------------------------------
# LangfusePromptManager
# ---------------------------------------------------------------------------


class TestLangfusePromptManagerInit:
    def test_langfuse_created_with_correct_args(self):
        with patch("infrastructure.llm.langfuse_client.Langfuse") as mock_cls:
            LangfusePromptManager(
                public_key="pub",
                secret_key="sec",
                host="https://custom.langfuse.com",
            )

        mock_cls.assert_called_once_with(
            public_key="pub",
            secret_key="sec",
            host="https://custom.langfuse.com",
        )

    def test_default_host(self):
        with patch("infrastructure.llm.langfuse_client.Langfuse") as mock_cls:
            LangfusePromptManager(public_key="pub", secret_key="sec")

        _, kwargs = mock_cls.call_args
        assert kwargs["host"] == "https://cloud.langfuse.com"


class TestLangfusePromptManagerGetPrompt:
    def _make_manager(self, mock_langfuse_instance):
        with patch("infrastructure.llm.langfuse_client.Langfuse", return_value=mock_langfuse_instance):
            return LangfusePromptManager(public_key="pub", secret_key="sec")

    def test_get_prompt_returns_messages_and_config(self):
        mock_prompt = MagicMock()
        mock_prompt.get_langchain_prompt.return_value = [{"role": "system", "content": "You are helpful."}]
        mock_prompt.config = {"temperature": 0.5}

        mock_lf = MagicMock()
        mock_lf.get_prompt.return_value = mock_prompt

        manager = self._make_manager(mock_lf)
        result = manager.get_prompt("my-prompt")

        mock_lf.get_prompt.assert_called_once_with("my-prompt", label="production")
        assert result["messages"] == [{"role": "system", "content": "You are helpful."}]
        assert result["config"] == {"temperature": 0.5}
        assert result["raw"] is mock_prompt

    def test_get_prompt_uses_custom_label(self):
        mock_prompt = MagicMock()
        mock_prompt.config = {}
        mock_lf = MagicMock()
        mock_lf.get_prompt.return_value = mock_prompt

        manager = self._make_manager(mock_lf)
        manager.get_prompt("p", label="staging")

        mock_lf.get_prompt.assert_called_once_with("p", label="staging")

    def test_get_prompt_falls_back_on_exception(self):
        fallback = [{"role": "user", "content": "fallback"}]

        mock_lf = MagicMock()
        mock_lf.get_prompt.side_effect = ConnectionError("network error")

        manager = self._make_manager(mock_lf)
        result = manager.get_prompt("missing-prompt", fallback=fallback)

        assert result["messages"] == fallback
        assert result["config"] == {}
        assert result["raw"] is None

    def test_get_prompt_raises_when_no_fallback(self):
        mock_lf = MagicMock()
        mock_lf.get_prompt.side_effect = RuntimeError("server down")

        manager = self._make_manager(mock_lf)

        with pytest.raises(RuntimeError, match="server down"):
            manager.get_prompt("broken-prompt")

    def test_get_prompt_without_get_langchain_prompt_attr(self):
        """get_langchain_prompt 메서드가 없는 프롬프트 객체 처리."""
        mock_prompt = MagicMock(spec=[])  # no attributes
        mock_lf = MagicMock()
        mock_lf.get_prompt.return_value = mock_prompt

        manager = self._make_manager(mock_lf)
        result = manager.get_prompt("plain-prompt")

        assert result["messages"] == []
        assert result["config"] == {}


class TestLangfusePromptManagerCompilePrompt:
    def _make_manager(self, mock_langfuse_instance):
        with patch("infrastructure.llm.langfuse_client.Langfuse", return_value=mock_langfuse_instance):
            return LangfusePromptManager(public_key="pub", secret_key="sec")

    def test_compile_prompt_calls_compile_with_variables(self):
        compiled = [{"role": "user", "content": "Hi Alice"}]
        mock_prompt = MagicMock()
        mock_prompt.compile.return_value = compiled

        mock_lf = MagicMock()
        mock_lf.get_prompt.return_value = mock_prompt

        manager = self._make_manager(mock_lf)
        result = manager.compile_prompt("greeting", name="Alice")

        mock_lf.get_prompt.assert_called_once_with("greeting", label="production")
        mock_prompt.compile.assert_called_once_with(name="Alice")
        assert result == compiled

    def test_compile_prompt_uses_custom_label(self):
        mock_prompt = MagicMock()
        mock_prompt.compile.return_value = []

        mock_lf = MagicMock()
        mock_lf.get_prompt.return_value = mock_prompt

        manager = self._make_manager(mock_lf)
        manager.compile_prompt("p", label="staging", key="val")

        mock_lf.get_prompt.assert_called_once_with("p", label="staging")
