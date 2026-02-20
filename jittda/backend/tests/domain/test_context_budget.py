"""ContextBudget 단위 테스트."""

from domain.analysis.context_budget import ContextBudget, _estimate_tokens, truncate_to_tokens


class TestEstimateTokens:
    def test_empty_string(self):
        assert _estimate_tokens("") == 0

    def test_short_string(self):
        assert _estimate_tokens("ab") == 1  # max(1, 2//3)

    def test_normal_string(self):
        text = "a" * 300
        assert _estimate_tokens(text) == 100  # 300 // 3

    def test_korean_mixed(self):
        text = "안녕하세요 Hello World"
        result = _estimate_tokens(text)
        assert result > 0


class TestTruncateToTokens:
    def test_empty_content(self):
        assert truncate_to_tokens("", 100) == ""

    def test_within_limit(self):
        text = "short text"
        assert truncate_to_tokens(text, 100) == text

    def test_truncation(self):
        text = "a" * 900  # ~300 tokens
        result = truncate_to_tokens(text, 100)
        assert len(result) < len(text)
        assert result.endswith("...")

    def test_exact_boundary(self):
        text = "a" * 300  # exactly 100 tokens
        result = truncate_to_tokens(text, 100)
        assert result == text  # should not truncate


class TestContextBudget:
    def test_default_allocation(self):
        budget = ContextBudget()
        assert budget.max_tokens == 8000
        assert "system_prompt" in budget.allocation
        assert "code_chunks" in budget.allocation

    def test_custom_allocation(self):
        budget = ContextBudget(max_tokens=4000, allocation={"section_a": 2000, "section_b": 2000})
        assert budget.max_tokens == 4000

    def test_allocate_within_limit(self):
        budget = ContextBudget()
        result = budget.allocate("system_prompt", "short text")
        assert result == "short text"
        assert budget.used("system_prompt") > 0

    def test_allocate_truncates(self):
        budget = ContextBudget(allocation={"tiny": 10})
        long_text = "a" * 300  # ~100 tokens, limit is 10
        result = budget.allocate("tiny", long_text)
        assert len(result) < len(long_text)
        assert result.endswith("...")

    def test_total_used(self):
        budget = ContextBudget()
        budget.allocate("system_prompt", "hello")
        budget.allocate("jd_context", "world")
        assert budget.total_used() == budget.used("system_prompt") + budget.used("jd_context")

    def test_remaining(self):
        budget = ContextBudget(max_tokens=100)
        budget.allocate("system_prompt", "hello")
        assert budget.remaining() == 100 - budget.total_used()

    def test_is_within_budget(self):
        budget = ContextBudget(max_tokens=10000)
        budget.allocate("system_prompt", "hello")
        assert budget.is_within_budget() is True

    def test_over_budget(self):
        budget = ContextBudget(max_tokens=1, allocation={"big": 10000})
        budget.allocate("big", "a" * 300)
        assert budget.is_within_budget() is False

    def test_summary(self):
        budget = ContextBudget()
        budget.allocate("system_prompt", "hello")
        summary = budget.summary()
        assert "max_tokens" in summary
        assert "total_used" in summary
        assert "remaining" in summary
        assert "within_budget" in summary
        assert "used_system_prompt" in summary

    def test_unknown_section_default(self):
        budget = ContextBudget()
        result = budget.allocate("unknown_section", "some content")
        assert result  # should use default 1000 limit
        assert budget.used("unknown_section") > 0
