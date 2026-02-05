"""
backend/tests/test_llm_resilient.py
LLM Resilient Infrastructure Integration Tests

테스트 범위:
1. LiteLLM Router 설정 검증
2. JSON 파서 기능 검증
3. Instructor 클라이언트 검증
4. Resilient completion 검증
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

# =============================================================================
# JSON Parser Tests
# =============================================================================

class TestJSONParser:
    """JSON 파싱 기능 테스트"""

    def test_extract_json_from_markdown_code_block(self):
        """Markdown 코드 블록에서 JSON 추출"""
        from app.services.json_parser import extract_json_from_response

        text = '''Here is the result:
```json
{"name": "test", "value": 123}
```
That's all.'''

        result = extract_json_from_response(text)
        assert result == '{"name": "test", "value": 123}'

    def test_extract_json_from_plain_block(self):
        """일반 코드 블록에서 JSON 추출"""
        from app.services.json_parser import extract_json_from_response

        text = '''Result:
```
{"key": "value"}
```'''

        result = extract_json_from_response(text)
        assert result == '{"key": "value"}'

    def test_extract_json_object_pattern(self):
        """JSON 객체 패턴 추출"""
        from app.services.json_parser import extract_json_from_response

        text = 'The answer is {"result": true, "data": [1, 2, 3]} as expected.'
        result = extract_json_from_response(text)
        assert result == '{"result": true, "data": [1, 2, 3]}'

    def test_extract_json_array_pattern(self):
        """JSON 배열 패턴 추출"""
        from app.services.json_parser import extract_json_from_response

        text = 'Items: [{"id": 1}, {"id": 2}] end.'
        result = extract_json_from_response(text)
        assert result == '[{"id": 1}, {"id": 2}]'

    def test_repair_trailing_comma(self):
        """Trailing comma 수정"""
        from app.services.json_parser import repair_json

        text = '{"name": "test", "value": 123,}'
        result = repair_json(text)
        assert result == '{"name": "test", "value": 123}'

    def test_repair_python_style_values(self):
        """Python 스타일 값 수정"""
        from app.services.json_parser import repair_json

        text = '{"active": True, "data": None, "valid": False}'
        result = repair_json(text)
        assert result == '{"active": true, "data": null, "valid": false}'

    def test_safe_parse_json_success(self):
        """안전한 JSON 파싱 성공"""
        from app.services.json_parser import safe_parse_json

        text = '{"name": "test"}'
        result = safe_parse_json(text)
        assert result == {"name": "test"}

    def test_safe_parse_json_with_markdown(self):
        """Markdown 포함 JSON 파싱"""
        from app.services.json_parser import safe_parse_json

        text = '''```json
{"result": "success"}
```'''
        result = safe_parse_json(text)
        assert result == {"result": "success"}

    def test_safe_parse_json_with_repair(self):
        """수정이 필요한 JSON 파싱"""
        from app.services.json_parser import safe_parse_json

        text = '{"active": True, "count": 5,}'
        result = safe_parse_json(text)
        assert result == {"active": True, "count": 5}

    def test_safe_parse_json_failure_returns_default(self):
        """파싱 실패 시 기본값 반환"""
        from app.services.json_parser import safe_parse_json

        text = 'This is not JSON at all'
        result = safe_parse_json(text, default={"error": True})
        assert result == {"error": True}

    def test_safe_parse_json_failure_raises(self):
        """파싱 실패 시 예외 발생"""
        from app.services.json_parser import safe_parse_json

        text = 'Not JSON'
        with pytest.raises(ValueError):
            safe_parse_json(text, raise_on_failure=True)

    def test_is_valid_json(self):
        """유효한 JSON 확인"""
        from app.services.json_parser import is_valid_json

        assert is_valid_json('{"valid": true}') is True
        assert is_valid_json('not json') is False
        assert is_valid_json('') is False

    def test_json_to_str(self):
        """객체를 JSON 문자열로 변환"""
        from app.services.json_parser import json_to_str

        obj = {"한글": "테스트", "number": 123}
        result = json_to_str(obj)
        assert "한글" in result  # ensure_ascii=False
        assert "테스트" in result


# =============================================================================
# Router Tests
# =============================================================================

class TestLLMRouter:
    """LiteLLM Router 테스트"""

    def test_router_initialization(self):
        """Router 초기화 테스트"""
        from app.services.llm_router import get_router

        # Should not raise even without API keys (will raise RuntimeError)
        # This tests the import and basic structure
        try:
            router = get_router()
            assert router is not None
        except RuntimeError as e:
            # Expected if no API keys configured
            assert "No LLM API keys configured" in str(e)

    def test_get_available_models(self):
        """사용 가능한 모델 목록"""
        from app.services.llm_router import get_available_models

        try:
            models = get_available_models()
            assert isinstance(models, list)
        except RuntimeError:
            # Expected if no API keys
            pass

    def test_get_model_info(self):
        """모델 정보 조회"""
        from app.services.llm_router import get_model_info

        try:
            info = get_model_info()
            assert "models" in info
            assert "fallbacks" in info
            assert "routing_strategy" in info
        except RuntimeError:
            # Expected if no API keys
            pass


# =============================================================================
# Response Validation Tests
# =============================================================================

class TestResponseValidation:
    """응답 검증 테스트"""

    def test_validate_response_success(self):
        """정상 응답 검증"""
        from app.services.llm_resilient import validate_response

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, world!"
        mock_response.choices[0].finish_reason = "stop"

        result = validate_response(mock_response)
        assert result is True

    def test_validate_response_empty_error(self):
        """빈 응답 에러"""
        from app.services.llm_resilient import validate_response, EmptyResponseError

        mock_response = MagicMock()
        mock_response.choices = []

        with pytest.raises(EmptyResponseError):
            validate_response(mock_response)

    def test_validate_response_truncated_error(self):
        """잘린 응답 에러"""
        from app.services.llm_resilient import validate_response, TruncatedResponseError

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Truncated..."
        mock_response.choices[0].finish_reason = "length"

        with pytest.raises(TruncatedResponseError):
            validate_response(mock_response, allow_truncated=False)

    def test_validate_response_truncated_allowed(self):
        """잘린 응답 허용"""
        from app.services.llm_resilient import validate_response

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Truncated..."
        mock_response.choices[0].finish_reason = "length"

        result = validate_response(mock_response, allow_truncated=True)
        assert result is True

    def test_get_response_content(self):
        """응답 content 추출"""
        from app.services.llm_resilient import get_response_content

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test content"

        result = get_response_content(mock_response)
        assert result == "Test content"

    def test_get_response_content_empty(self):
        """빈 응답에서 content 추출"""
        from app.services.llm_resilient import get_response_content

        result = get_response_content(None)
        assert result == ""


# =============================================================================
# LLM Config Tests
# =============================================================================

class TestLLMConfig:
    """LLM Config 테스트"""

    def test_get_model_for_activity_exact_match(self):
        """Activity별 모델 정확 매칭"""
        from app.services.llm_config import get_model_for_activity

        model = get_model_for_activity("analyze_documents")
        assert "moonshot" in model or model == "openai:gpt-4o"

        model = get_model_for_activity("analyze_code")
        assert "glm-4.7" in model or "moonshot" in model

    def test_get_model_for_activity_prefix_match(self):
        """Activity별 모델 prefix 매칭"""
        from app.services.llm_config import get_model_for_activity

        # HYBRID 코드 분석 prefix 매칭
        model = get_model_for_activity("code_deep_analysis_src/main.py")
        assert "glm-4.7" in model or "moonshot" in model

    def test_get_model_for_activity_default(self):
        """Activity별 모델 기본값"""
        from app.services.llm_config import get_model_for_activity

        model = get_model_for_activity("unknown_activity")
        # Should return default from settings
        assert model is not None

    def test_is_native_pydantic_ai_model(self):
        """Native pydantic-ai 모델 확인"""
        from app.services.llm_config import _is_native_pydantic_ai_model

        assert _is_native_pydantic_ai_model("openai:gpt-4o") is True
        assert _is_native_pydantic_ai_model("anthropic:claude-3-sonnet") is True
        assert _is_native_pydantic_ai_model("zai/glm-4.5-flash") is False
        assert _is_native_pydantic_ai_model("cohere/command") is False


# =============================================================================
# Instructor Integration Tests
# =============================================================================

class TestInstructorIntegration:
    """Instructor 통합 테스트"""

    def test_instructor_client_initialization(self):
        """Instructor 클라이언트 초기화"""
        # This test verifies the import and basic structure
        from app.services.llm_structured import get_instructor_client

        try:
            client = get_instructor_client()
            assert client is not None
        except RuntimeError:
            # Expected if no API keys
            pass

    def test_create_messages_helper(self):
        """메시지 헬퍼 함수"""
        from app.services.llm_structured import (
            create_system_message,
            create_user_message,
            create_messages,
        )

        sys_msg = create_system_message("You are a helpful assistant.")
        assert sys_msg == {"role": "system", "content": "You are a helpful assistant."}

        user_msg = create_user_message("Hello!")
        assert user_msg == {"role": "user", "content": "Hello!"}

        messages = create_messages("System prompt", "User input")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"


# =============================================================================
# Integration Tests (Require API Keys)
# =============================================================================

@pytest.mark.integration
class TestLLMIntegration:
    """실제 API 호출 통합 테스트 (API 키 필요)"""

    @pytest.mark.asyncio
    async def test_resilient_completion_with_mock(self):
        """Resilient completion 모킹 테스트"""
        from app.services.llm_resilient import resilient_completion

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"

        with patch('app.services.llm_resilient.get_router') as mock_get_router:
            mock_router = MagicMock()
            mock_router.acompletion = AsyncMock(return_value=mock_response)
            mock_get_router.return_value = mock_router

            result = await resilient_completion(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello"}],
                max_retries=1,
            )

            assert result is not None
            assert result.choices[0].message.content == "Test response"

    @pytest.mark.asyncio
    async def test_structured_output_with_mock(self):
        """Structured output 모킹 테스트"""
        from pydantic import BaseModel
        from app.services.llm_structured import get_structured_output

        class TestModel(BaseModel):
            name: str
            value: int

        mock_result = TestModel(name="test", value=42)

        with patch('app.services.llm_structured.get_instructor_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_result)
            mock_get_client.return_value = mock_client

            result = await get_structured_output(
                model="gpt-4o",
                response_model=TestModel,
                messages=[{"role": "user", "content": "Generate test data"}],
            )

            assert result.name == "test"
            assert result.value == 42


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
