"""
ContextBudget — LLM 입력 컨텍스트 예산 관리자.

LLM 호출 시 섹션별 토큰 한도를 관리하여 비용을 제어한다.
순수 도메인 모델: 외부 의존성 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _estimate_tokens(text: str) -> int:
    """토큰 수를 추정한다. (영어 ~4 chars/token, 한국어 ~2 chars/token, 혼합 ~3)"""
    if not text:
        return 0
    return max(1, len(text) // 3)


def truncate_to_tokens(content: str, max_tokens: int) -> str:
    """콘텐츠를 max_tokens 이내로 자른다."""
    if not content:
        return ""
    estimated = _estimate_tokens(content)
    if estimated <= max_tokens:
        return content
    # 토큰당 ~3자 기준으로 잘라냄
    char_limit = max_tokens * 3
    return content[:char_limit] + "..."


@dataclass
class ContextBudget:
    """LLM 컨텍스트 예산 관리. Builder 패턴으로 섹션별 할당."""

    max_tokens: int = 8000
    allocation: dict[str, int] = field(default_factory=lambda: {
        "system_prompt": 1500,
        "jd_context": 1500,
        "code_chunks": 3000,
        "candidate_profile": 1000,
        "topic_context": 1000,
    })
    _used: dict[str, int] = field(default_factory=dict, repr=False)

    def allocate(self, section: str, content: str) -> str:
        """섹션에 콘텐츠를 할당하고, 토큰 한도 내로 잘라서 반환한다."""
        max_section = self.allocation.get(section, 1000)
        truncated = truncate_to_tokens(content, max_section)
        self._used[section] = _estimate_tokens(truncated)
        return truncated

    def used(self, section: str) -> int:
        """섹션별 사용된 토큰 수를 반환한다."""
        return self._used.get(section, 0)

    def total_used(self) -> int:
        """전체 사용된 토큰 수를 반환한다."""
        return sum(self._used.values())

    def remaining(self) -> int:
        """남은 토큰 수를 반환한다."""
        return max(0, self.max_tokens - self.total_used())

    def is_within_budget(self) -> bool:
        """예산 내인지 확인한다."""
        return self.total_used() <= self.max_tokens

    def summary(self) -> dict[str, int | bool]:
        """예산 사용 요약을 반환한다."""
        return {
            "max_tokens": self.max_tokens,
            "total_used": self.total_used(),
            "remaining": self.remaining(),
            "within_budget": self.is_within_budget(),
            **{f"used_{k}": v for k, v in self._used.items()},
        }
