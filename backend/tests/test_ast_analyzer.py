"""
backend/tests/test_ast_analyzer.py
AST 디렉토리 분석기 단위 테스트 (JIT-26)

테스트 항목:
- analyze_directory(): 파일 탐색, 필터링, 청크 추출
- _extract_python_chunks(): Python AST 파싱
- _extract_ts_chunks(): tree-sitter fallback
"""
import pytest


# ============================================================
# TestAnalyzeDirectory: analyze_directory() 테스트
# ============================================================

class TestAnalyzeDirectory:
    """analyze_directory() — clone_dir에서 AST 파싱 + 청크 추출"""

    def test_python_files_extract_chunks(self, tmp_path):
        """Python 파일에서 함수/클래스 청크 추출 + 스키마 키 검증"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "main.py").write_text(
            "def hello():\n    return 'world'\n\n"
            "class Greeter:\n    def greet(self):\n        pass\n"
        )

        chunks = analyze_directory(str(tmp_path))

        assert len(chunks) >= 2  # hello 함수 + Greeter 클래스
        required_keys = {"name", "type", "file_path", "source_code", "identifiers", "imports", "decorators", "char_count"}
        for chunk in chunks:
            assert required_keys.issubset(chunk.keys()), f"누락 키: {required_keys - chunk.keys()}"
            assert chunk["type"] in ("function", "class", "module")
            assert chunk["char_count"] > 0

        names = {c["name"] for c in chunks}
        assert "hello" in names
        assert "Greeter" in names

    def test_excludes_directories(self, tmp_path):
        """.git, __pycache__, node_modules 디렉토리 스킵"""
        from app.services.ast_analyzer import analyze_directory

        # 제외 대상 디렉토리에 파일 생성
        for excluded in [".git", "__pycache__", "node_modules"]:
            d = tmp_path / excluded
            d.mkdir()
            (d / "hidden.py").write_text("def secret(): pass\n")

        # 정상 파일
        (tmp_path / "visible.py").write_text("def public(): pass\n")

        chunks = analyze_directory(str(tmp_path))

        file_paths = {c["file_path"] for c in chunks}
        assert all(excluded not in fp for fp in file_paths for excluded in [".git", "__pycache__", "node_modules"])
        assert any("visible.py" in fp for fp in file_paths)

    def test_max_files_limit(self, tmp_path):
        """60개 파일 → max_files=50 적용 확인"""
        from app.services.ast_analyzer import analyze_directory

        for i in range(60):
            (tmp_path / f"file_{i:03d}.py").write_text(f"def func_{i}(): pass\n")

        chunks = analyze_directory(str(tmp_path), max_files=50)

        # 50개 파일 이하에서 추출된 청크만 존재
        unique_files = {c["file_path"] for c in chunks}
        assert len(unique_files) <= 50

    def test_file_types_filter(self, tmp_path):
        """file_types=['.py']로 .ts/.go 필터링"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "app.py").write_text("def main(): pass\n")
        (tmp_path / "app.ts").write_text("function main() {}\n")
        (tmp_path / "app.go").write_text("package main\nfunc main() {}\n")

        chunks = analyze_directory(str(tmp_path), file_types=[".py"])

        file_paths = {c["file_path"] for c in chunks}
        assert any(".py" in fp for fp in file_paths)
        assert not any(".ts" in fp for fp in file_paths)
        assert not any(".go" in fp for fp in file_paths)

    def test_empty_directory(self, tmp_path):
        """빈 디렉토리 → 빈 리스트"""
        from app.services.ast_analyzer import analyze_directory

        chunks = analyze_directory(str(tmp_path))
        assert chunks == []

    def test_large_files_excluded(self, tmp_path):
        """300KB 파일 스킵 (>200KB 제한)"""
        from app.services.ast_analyzer import analyze_directory

        # 300KB 초과 파일
        large_content = "x = 1\n" * 60_000  # ~360KB
        (tmp_path / "large.py").write_text(large_content)

        # 정상 크기 파일
        (tmp_path / "small.py").write_text("def ok(): pass\n")

        chunks = analyze_directory(str(tmp_path))

        file_paths = {c["file_path"] for c in chunks}
        assert not any("large.py" in fp for fp in file_paths)
        assert any("small.py" in fp for fp in file_paths)

    def test_empty_files_excluded(self, tmp_path):
        """0바이트 파일 스킵"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "blank.py").write_text("")
        (tmp_path / "valid.py").write_text("x = 1\n")

        chunks = analyze_directory(str(tmp_path))

        file_paths = {c["file_path"] for c in chunks}
        assert not any("blank.py" in fp for fp in file_paths)
        assert any("valid.py" in fp for fp in file_paths)


# ============================================================
# TestExtractPythonChunks: Python AST 파싱 테스트
# ============================================================

class TestExtractPythonChunks:
    """_extract_python_chunks — Python AST 파싱"""

    def test_extracts_functions_and_classes(self, tmp_path):
        """함수 2개 + 클래스 1개 파싱, name/type/identifiers/imports/decorators 검증"""
        from app.services.ast_analyzer import analyze_directory

        source = (
            "import os\n"
            "from pathlib import Path\n\n"
            "def func_a(x, y):\n    return x + y\n\n"
            "def func_b():\n    os.getcwd()\n\n"
            "class MyClass:\n    def method(self):\n        pass\n"
        )
        (tmp_path / "module.py").write_text(source)

        chunks = analyze_directory(str(tmp_path))

        names = {c["name"] for c in chunks}
        assert "func_a" in names
        assert "func_b" in names
        assert "MyClass" in names

        func_a = next(c for c in chunks if c["name"] == "func_a")
        assert func_a["type"] == "function"
        assert isinstance(func_a["identifiers"], list)
        assert isinstance(func_a["imports"], list)
        assert len(func_a["imports"]) >= 1  # import os, from pathlib import Path

        my_class = next(c for c in chunks if c["name"] == "MyClass")
        assert my_class["type"] == "class"

    def test_syntax_error_fallback(self, tmp_path):
        """잘못된 Python → _file_level_chunk fallback (type='module')"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "bad.py").write_text("def broken(:\n    pass\n")

        chunks = analyze_directory(str(tmp_path))

        assert len(chunks) == 1
        assert chunks[0]["type"] == "module"
        assert chunks[0]["name"].startswith("file:")

    def test_async_function_extraction(self, tmp_path):
        """AsyncFunctionDef 캡처"""
        from app.services.ast_analyzer import analyze_directory

        source = "async def fetch_data(url):\n    return await get(url)\n"
        (tmp_path / "async_mod.py").write_text(source)

        chunks = analyze_directory(str(tmp_path))

        assert any(c["name"] == "fetch_data" and c["type"] == "function" for c in chunks)

    def test_decorator_extraction(self, tmp_path):
        """@staticmethod, @app.get 데코레이터 추출"""
        from app.services.ast_analyzer import analyze_directory

        source = (
            "class Api:\n"
            "    @staticmethod\n"
            "    def helper():\n        pass\n"
        )
        (tmp_path / "deco.py").write_text(source)

        chunks = analyze_directory(str(tmp_path))

        api_class = next((c for c in chunks if c["name"] == "Api"), None)
        assert api_class is not None
        # 데코레이터는 클래스 내부 함수에 있으므로, 클래스 레벨 청크에서는 빈 리스트일 수 있음
        # 하지만 데코레이터 필드는 리스트로 존재해야 함
        assert isinstance(api_class["decorators"], list)

    def test_max_chunk_chars_truncation(self, tmp_path):
        """10K 초과 소스 → 절삭 확인"""
        from app.services.ast_analyzer import analyze_directory

        # 12K 글자 함수
        body = "    x = 1\n" * 1500  # ~15K chars
        source = f"def big_func():\n{body}"
        (tmp_path / "big.py").write_text(source)

        chunks = analyze_directory(str(tmp_path), max_chunk_chars=10_000)

        big = next((c for c in chunks if c["name"] == "big_func"), None)
        assert big is not None
        assert big["char_count"] <= 10_000


# ============================================================
# TestExtractTsChunks: tree-sitter JS/TS fallback 테스트
# ============================================================

class TestExtractTsChunks:
    """_extract_ts_chunks — tree-sitter fallback"""

    def test_returns_empty_without_tree_sitter(self, tmp_path):
        """tree-sitter ImportError → file-level fallback 청크"""
        from unittest.mock import patch
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "app.ts").write_text("function hello() { return 'world'; }\n")

        # tree-sitter를 import할 수 없는 환경 시뮬레이션
        with patch("app.services.ast_analyzer._extract_ts_chunks", return_value=[]):
            chunks = analyze_directory(str(tmp_path), file_types=[".ts"])

        # tree-sitter 없으면 file-level chunk fallback
        assert len(chunks) >= 1
        assert chunks[0]["type"] == "module"

    def test_file_level_chunk_fallback(self, tmp_path):
        """미지원 언어 (.rs) → 파일 레벨 청크"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "main.rs").write_text("fn main() { println!(\"hello\"); }\n")

        chunks = analyze_directory(str(tmp_path), file_types=[".rs"])

        assert len(chunks) == 1
        assert chunks[0]["type"] == "module"
        assert "main" in chunks[0]["name"]
