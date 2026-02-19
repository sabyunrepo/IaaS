"""
TreeSitterAdapter 테스트 — Tree-sitter 0.25.x QueryCursor API.

tree_sitter 패키지가 없으면 전체 모듈을 스킵한다.
모든 테스트는 동기 함수 (Tree-sitter는 동기 API).
"""
import pytest

# tree_sitter 패키지가 없으면 모듈 전체 스킵
pytest.importorskip("tree_sitter")

from infrastructure.analysis.tree_sitter_adapter import TreeSitterAdapter  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

PYTHON_SIMPLE = """\
def hello(name: str) -> str:
    return f"Hello, {name}"


def add(a: int, b: int) -> int:
    return a + b
"""

PYTHON_CLASS = """\
class Greeter:
    def greet(self, name: str) -> str:
        return f"Hi, {name}"
"""

PYTHON_IMPORTS = """\
import os
import sys
from pathlib import Path
from collections import defaultdict
"""

JAVASCRIPT_SIMPLE = """\
function greet(name) {
    return "Hello, " + name;
}
"""

TYPESCRIPT_SIMPLE = """\
function add(a: number, b: number): number {
    return a + b;
}
"""

JAVA_SIMPLE = """\
public class Greeter {
    public String greet(String name) {
        return "Hello, " + name;
    }
}
"""

GO_SIMPLE = """\
package main

func greet(name string) string {
    return "Hello, " + name
}
"""


@pytest.fixture(scope="module")
def adapter() -> TreeSitterAdapter:
    return TreeSitterAdapter()


# ---------------------------------------------------------------------------
# parse_code — 5개 언어 파싱
# ---------------------------------------------------------------------------


class TestParseCode:
    def test_python_parse_returns_tree(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(PYTHON_SIMPLE, "python")
        assert tree is not None
        assert tree.root_node is not None
        assert tree.root_node.type == "module"

    def test_javascript_parse_returns_tree(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(JAVASCRIPT_SIMPLE, "javascript")
        assert tree is not None
        assert tree.root_node is not None

    def test_typescript_parse_returns_tree(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(TYPESCRIPT_SIMPLE, "typescript")
        assert tree is not None
        assert tree.root_node is not None

    def test_java_parse_returns_tree(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(JAVA_SIMPLE, "java")
        assert tree is not None
        assert tree.root_node is not None

    def test_go_parse_returns_tree(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(GO_SIMPLE, "go")
        assert tree is not None
        assert tree.root_node is not None

    def test_unsupported_language_raises(self, adapter: TreeSitterAdapter):
        with pytest.raises(ValueError, match="Unsupported language"):
            adapter.parse_code("x = 1", "ruby")


# ---------------------------------------------------------------------------
# get_parser
# ---------------------------------------------------------------------------


class TestGetParser:
    def test_returns_parser_for_supported_language(self, adapter: TreeSitterAdapter):
        from tree_sitter import Parser

        parser = adapter.get_parser("python")
        assert isinstance(parser, Parser)

    def test_unsupported_language_raises(self, adapter: TreeSitterAdapter):
        with pytest.raises(ValueError, match="Unsupported language"):
            adapter.get_parser("cobol")

    def test_each_call_returns_new_instance(self, adapter: TreeSitterAdapter):
        """Parser는 Thread-safe하지 않으므로 새 인스턴스여야 한다."""
        p1 = adapter.get_parser("python")
        p2 = adapter.get_parser("python")
        assert p1 is not p2


# ---------------------------------------------------------------------------
# extract_functions
# ---------------------------------------------------------------------------


class TestExtractFunctions:
    def test_python_extracts_two_functions(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(PYTHON_SIMPLE, "python")
        funcs = adapter.extract_functions(tree.root_node, "python")

        assert len(funcs) == 2
        names = {f["name"] for f in funcs}
        assert "hello" in names
        assert "add" in names

    def test_python_function_has_required_keys(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(PYTHON_SIMPLE, "python")
        funcs = adapter.extract_functions(tree.root_node, "python")

        for func in funcs:
            assert "name" in func
            assert "start_line" in func
            assert "end_line" in func
            assert "body" in func

    def test_python_function_line_numbers_are_correct(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(PYTHON_SIMPLE, "python")
        funcs = adapter.extract_functions(tree.root_node, "python")

        hello = next(f for f in funcs if f["name"] == "hello")
        assert hello["start_line"] == 1
        assert hello["end_line"] == 2

    def test_python_function_body_contains_source(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(PYTHON_SIMPLE, "python")
        funcs = adapter.extract_functions(tree.root_node, "python")

        hello = next(f for f in funcs if f["name"] == "hello")
        assert "def hello" in hello["body"]
        assert "return" in hello["body"]

    def test_python_empty_code_returns_empty_list(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code("", "python")
        funcs = adapter.extract_functions(tree.root_node, "python")
        assert funcs == []

    def test_python_no_functions_returns_empty_list(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code("x = 42\ny = x + 1\n", "python")
        funcs = adapter.extract_functions(tree.root_node, "python")
        assert funcs == []

    def test_javascript_extracts_function(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(JAVASCRIPT_SIMPLE, "javascript")
        funcs = adapter.extract_functions(tree.root_node, "javascript")

        assert len(funcs) >= 1
        names = {f["name"] for f in funcs}
        assert "greet" in names

    def test_java_extracts_method(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(JAVA_SIMPLE, "java")
        funcs = adapter.extract_functions(tree.root_node, "java")

        assert len(funcs) >= 1
        names = {f["name"] for f in funcs}
        assert "greet" in names

    def test_go_extracts_function(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(GO_SIMPLE, "go")
        funcs = adapter.extract_functions(tree.root_node, "go")

        assert len(funcs) >= 1
        names = {f["name"] for f in funcs}
        assert "greet" in names

    def test_unsupported_language_raises(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code("", "python")
        with pytest.raises(ValueError, match="Unsupported language"):
            adapter.extract_functions(tree.root_node, "ruby")


# ---------------------------------------------------------------------------
# extract_imports
# ---------------------------------------------------------------------------


class TestExtractImports:
    def test_python_extracts_all_imports(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(PYTHON_IMPORTS, "python")
        imports = adapter.extract_imports(tree.root_node, "python")

        assert len(imports) == 4

    def test_python_import_strings_contain_module_names(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(PYTHON_IMPORTS, "python")
        imports = adapter.extract_imports(tree.root_node, "python")

        combined = "\n".join(imports)
        assert "os" in combined
        assert "sys" in combined
        assert "pathlib" in combined
        assert "collections" in combined

    def test_python_empty_code_returns_empty_list(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code("", "python")
        imports = adapter.extract_imports(tree.root_node, "python")
        assert imports == []

    def test_python_no_imports_returns_empty_list(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code("x = 1\n", "python")
        imports = adapter.extract_imports(tree.root_node, "python")
        assert imports == []

    def test_unsupported_language_raises(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code("", "python")
        with pytest.raises(ValueError, match="Unsupported language"):
            adapter.extract_imports(tree.root_node, "ruby")


# ---------------------------------------------------------------------------
# extract_classes
# ---------------------------------------------------------------------------


class TestExtractClasses:
    def test_python_extracts_class(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(PYTHON_CLASS, "python")
        classes = adapter.extract_classes(tree.root_node, "python")

        assert len(classes) == 1
        assert classes[0]["name"] == "Greeter"

    def test_python_class_has_required_keys(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(PYTHON_CLASS, "python")
        classes = adapter.extract_classes(tree.root_node, "python")

        cls = classes[0]
        assert "name" in cls
        assert "start_line" in cls
        assert "end_line" in cls

    def test_python_class_line_numbers_correct(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(PYTHON_CLASS, "python")
        classes = adapter.extract_classes(tree.root_node, "python")

        cls = classes[0]
        assert cls["start_line"] == 1

    def test_python_empty_code_returns_empty_list(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code("", "python")
        classes = adapter.extract_classes(tree.root_node, "python")
        assert classes == []

    def test_python_no_classes_returns_empty_list(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code("def foo(): pass\n", "python")
        classes = adapter.extract_classes(tree.root_node, "python")
        assert classes == []

    def test_java_extracts_class(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code(JAVA_SIMPLE, "java")
        classes = adapter.extract_classes(tree.root_node, "java")

        assert len(classes) >= 1
        names = {c["name"] for c in classes}
        assert "Greeter" in names

    def test_unsupported_language_raises(self, adapter: TreeSitterAdapter):
        tree = adapter.parse_code("", "python")
        with pytest.raises(ValueError, match="Unsupported language"):
            adapter.extract_classes(tree.root_node, "ruby")
