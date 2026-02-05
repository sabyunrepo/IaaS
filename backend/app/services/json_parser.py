"""
backend/app/services/json_parser.py
Safe JSON Parser - 불완전한 LLM 응답 처리

Features:
- Markdown 코드 블록 추출
- JSON 객체/배열 패턴 추출
- 일반적인 JSON 오류 자동 수정
- 잘린 JSON 부분 복구 시도
"""
import json
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# JSON Extraction
# =============================================================================

def extract_json_from_response(text: str) -> str | None:
    """LLM 응답에서 JSON 추출

    처리 순서:
    1. ```json ... ``` 코드 블록
    2. ``` ... ``` 일반 코드 블록
    3. JSON 객체/배열 패턴

    Args:
        text: LLM 응답 텍스트

    Returns:
        추출된 JSON 문자열 또는 None
    """
    if not text:
        return None

    text = text.strip()

    # 1. ```json ... ``` 블록 추출
    json_block_match = re.search(r'```json\s*([\s\S]*?)```', text, re.IGNORECASE)
    if json_block_match:
        return json_block_match.group(1).strip()

    # 2. ``` ... ``` 일반 블록 추출
    code_block_match = re.search(r'```\s*([\s\S]*?)```', text)
    if code_block_match:
        content = code_block_match.group(1).strip()
        # JSON처럼 보이는지 확인
        if content.startswith(('{', '[')):
            return content

    # 3. JSON 객체 패턴 추출 (가장 바깥쪽)
    # 중첩된 객체를 올바르게 처리하기 위해 괄호 카운팅 사용
    obj_start = text.find('{')
    arr_start = text.find('[')

    if obj_start == -1 and arr_start == -1:
        return None

    # 더 먼저 나오는 것 선택
    if obj_start == -1:
        start_idx = arr_start
        open_char, close_char = '[', ']'
    elif arr_start == -1:
        start_idx = obj_start
        open_char, close_char = '{', '}'
    else:
        if obj_start < arr_start:
            start_idx = obj_start
            open_char, close_char = '{', '}'
        else:
            start_idx = arr_start
            open_char, close_char = '[', ']'

    # 괄호 매칭으로 끝 찾기
    depth = 0
    in_string = False
    escape_next = False
    end_idx = -1

    for i, char in enumerate(text[start_idx:], start=start_idx):
        if escape_next:
            escape_next = False
            continue

        if char == '\\':
            escape_next = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                end_idx = i + 1
                break

    if end_idx > start_idx:
        return text[start_idx:end_idx]

    # 매칭 실패 시 시작점부터 끝까지 반환 (불완전한 JSON)
    return text[start_idx:]


# =============================================================================
# JSON Repair
# =============================================================================

def repair_json(text: str) -> str:
    """일반적인 JSON 오류 수정

    수정 항목:
    - Trailing comma 제거
    - 홑따옴표 → 쌍따옴표
    - Unquoted keys 수정
    - Python 스타일 None/True/False → JSON 스타일

    Args:
        text: JSON 문자열

    Returns:
        수정된 JSON 문자열
    """
    if not text:
        return text

    # 1. Trailing comma 제거 (배열/객체 끝)
    # },] 또는 },} 패턴의 쉼표 제거
    text = re.sub(r',(\s*[}\]])', r'\1', text)

    # 2. Python 스타일 → JSON 스타일
    # None → null (문자열 내부가 아닌 경우만)
    text = re.sub(r'\bNone\b', 'null', text)
    text = re.sub(r'\bTrue\b', 'true', text)
    text = re.sub(r'\bFalse\b', 'false', text)

    # 3. 홑따옴표 → 쌍따옴표 (주의: 문자열 내부의 apostrophe 손상 가능)
    # 간단한 패턴만 처리
    # {'key': 'value'} → {"key": "value"}
    text = re.sub(r"'([^']*)'(\s*:)", r'"\1"\2', text)  # key
    text = re.sub(r":\s*'([^']*)'", r': "\1"', text)    # string value

    # 4. Unquoted keys 수정 (간단한 케이스)
    # {key: "value"} → {"key": "value"}
    text = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', text)

    return text


def attempt_partial_json_recovery(text: str) -> dict | list | None:
    """잘린 JSON 부분 복구 시도

    토큰 한도로 잘린 JSON을 복구 시도.
    마지막 완전한 요소까지 파싱.

    Args:
        text: 불완전한 JSON 문자열

    Returns:
        파싱된 객체 또는 None
    """
    if not text:
        return None

    # 가능한 닫는 괄호 조합
    closers = [
        '',          # 이미 완전할 수 있음
        '}',         # 객체 닫기
        '"}',        # 문자열 + 객체 닫기
        '"}]',       # 문자열 + 배열 내 객체 닫기
        ']',         # 배열 닫기
        '"]',        # 문자열 + 배열 닫기
        '}}',        # 중첩 객체 닫기
        '"}}',       # 문자열 + 중첩 객체
        ']}}',       # 배열 + 중첩 객체
        '"}]}',      # 복잡한 중첩
        'null}',     # null 값 + 객체 닫기
        '0}',        # 숫자 + 객체 닫기
    ]

    # 뒤에서부터 잘라가며 시도
    for trim_amount in range(0, min(100, len(text)), 1):
        partial = text if trim_amount == 0 else text[:-trim_amount]

        for closer in closers:
            try:
                candidate = partial + closer
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    return None


# =============================================================================
# Main Parser
# =============================================================================

def safe_parse_json(
    text: str,
    default: Any = None,
    raise_on_failure: bool = False,
) -> dict | list | None:
    """안전한 JSON 파싱 (여러 단계 시도)

    파싱 순서:
    1. JSON 추출
    2. 직접 파싱
    3. JSON 수정 후 파싱
    4. 부분 복구 시도

    Args:
        text: LLM 응답 텍스트
        default: 파싱 실패 시 반환값
        raise_on_failure: True면 실패 시 예외 발생

    Returns:
        파싱된 객체 또는 default

    Raises:
        ValueError: raise_on_failure=True이고 파싱 실패 시
    """
    if not text:
        if raise_on_failure:
            raise ValueError("Empty input text")
        return default

    # Step 1: JSON 추출
    json_text = extract_json_from_response(text)
    if not json_text:
        logger.warning("No JSON found in response")
        if raise_on_failure:
            raise ValueError("No JSON found in response")
        return default

    # Step 2: 직접 파싱
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.debug(f"Direct parse failed: {e}")

    # Step 3: JSON 수정 후 파싱
    try:
        repaired = repair_json(json_text)
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        logger.debug(f"Repaired parse failed: {e}")

    # Step 4: 부분 복구 시도
    result = attempt_partial_json_recovery(json_text)
    if result is not None:
        logger.info("Recovered partial JSON successfully")
        return result

    # 모든 시도 실패
    logger.warning(
        f"All JSON parsing attempts failed. "
        f"Original length: {len(text)}, Extracted length: {len(json_text)}"
    )

    if raise_on_failure:
        raise ValueError(f"Failed to parse JSON from response")

    return default


def parse_json_or_raw(text: str) -> dict | list | str:
    """JSON 파싱 시도, 실패 시 원본 텍스트 반환

    LLM이 JSON 대신 plain text를 반환한 경우에도 처리 가능.

    Args:
        text: LLM 응답 텍스트

    Returns:
        파싱된 JSON 객체 또는 원본 텍스트
    """
    result = safe_parse_json(text)
    if result is not None:
        return result
    return text.strip()


# =============================================================================
# Validation Helpers
# =============================================================================

def is_valid_json(text: str) -> bool:
    """유효한 JSON인지 확인"""
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def json_to_str(obj: Any, ensure_ascii: bool = False, indent: int | None = None) -> str:
    """객체를 JSON 문자열로 변환 (UTF-8 유지)"""
    return json.dumps(obj, ensure_ascii=ensure_ascii, indent=indent)
