"""domain/matching/language_extensions.py 단위 테스트."""
from domain.matching.language_extensions import (
    get_extensions_for_languages,
    get_sparse_checkout_patterns,
    ext_to_tree_sitter_language,
    is_tree_sitter_supported,
)


class TestGetExtensionsForLanguages:
    """get_extensions_for_languages 함수 테스트."""

    def test_single_language(self):
        result = get_extensions_for_languages(["python"])
        assert result == {".py": "python"}

    def test_multiple_languages(self):
        result = get_extensions_for_languages(["python", "typescript"])
        assert ".py" in result
        assert ".ts" in result
        assert ".tsx" in result
        assert result[".py"] == "python"
        assert result[".ts"] == "typescript"

    def test_javascript_includes_jsx(self):
        result = get_extensions_for_languages(["javascript"])
        assert ".js" in result
        assert ".jsx" in result

    def test_empty_returns_default_five(self):
        result = get_extensions_for_languages([])
        assert len(result) == 5
        assert ".py" in result
        assert ".java" in result
        assert ".go" in result

    def test_unknown_language_falls_back_to_default(self):
        result = get_extensions_for_languages(["brainfuck"])
        assert len(result) == 5  # default

    def test_case_insensitive(self):
        result = get_extensions_for_languages(["Python", "TYPESCRIPT"])
        assert ".py" in result
        assert ".ts" in result

    def test_cpp_aliases(self):
        r1 = get_extensions_for_languages(["cpp"])
        r2 = get_extensions_for_languages(["c++"])
        assert r1 == r2
        assert ".cpp" in r1

    def test_csharp_aliases(self):
        r1 = get_extensions_for_languages(["csharp"])
        r2 = get_extensions_for_languages(["c#"])
        assert r1 == r2
        assert ".cs" in r1

    def test_mixed_known_unknown(self):
        result = get_extensions_for_languages(["python", "nonexistent", "go"])
        assert ".py" in result
        assert ".go" in result
        assert len(result) == 2


class TestGetSparseCheckoutPatterns:
    """get_sparse_checkout_patterns 함수 테스트."""

    def test_empty_returns_empty(self):
        assert get_sparse_checkout_patterns([]) == []

    def test_python_patterns(self):
        patterns = get_sparse_checkout_patterns(["python"])
        assert "*.py" in patterns
        # 공통 패턴도 포함
        assert "*.json" in patterns
        assert "*.yaml" in patterns

    def test_multiple_languages(self):
        patterns = get_sparse_checkout_patterns(["python", "typescript"])
        assert "*.py" in patterns
        assert "*.ts" in patterns
        assert "*.tsx" in patterns

    def test_sorted(self):
        patterns = get_sparse_checkout_patterns(["typescript", "python"])
        assert patterns == sorted(patterns)

    def test_no_duplicates(self):
        patterns = get_sparse_checkout_patterns(["python", "python"])
        py_count = patterns.count("*.py")
        assert py_count == 1


class TestExtToTreeSitterLanguage:
    """ext_to_tree_sitter_language 함수 테스트."""

    def test_known_extensions(self):
        assert ext_to_tree_sitter_language(".py") == "python"
        assert ext_to_tree_sitter_language(".ts") == "typescript"
        assert ext_to_tree_sitter_language(".tsx") == "typescript"
        assert ext_to_tree_sitter_language(".go") == "go"

    def test_unknown_extension(self):
        assert ext_to_tree_sitter_language(".xyz") is None

    def test_cpp_extension(self):
        assert ext_to_tree_sitter_language(".cpp") == "cpp"


class TestIsTreeSitterSupported:
    """is_tree_sitter_supported 함수 테스트."""

    def test_supported(self):
        assert is_tree_sitter_supported("python") is True
        assert is_tree_sitter_supported("javascript") is True
        assert is_tree_sitter_supported("typescript") is True
        assert is_tree_sitter_supported("java") is True
        assert is_tree_sitter_supported("go") is True

    def test_not_supported(self):
        assert is_tree_sitter_supported("rust") is False
        assert is_tree_sitter_supported("kotlin") is False
        assert is_tree_sitter_supported("cpp") is False
