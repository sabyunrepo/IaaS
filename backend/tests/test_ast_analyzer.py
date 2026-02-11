"""
backend/tests/test_ast_analyzer.py
AST 파서 확장 — analyze_directory() 단위 테스트 [JIT-21]

테스트 항목:
- AD-01: Python 소스 파일에서 함수/클래스 청크 + 메타데이터 추출
- AD-02: JS/TS 소스 파일에서 함수/클래스 청크 + 메타데이터 추출
- AD-03: 빈 디렉토리 / 비매칭 확장자 → 빈 결과
- AD-04: 기존 analyze_ast() 함수 동작 유지 (하위 호환)
- AD-05: 메타데이터 필드 완전성 검증
"""
import pytest
import textwrap


# ============================================================
# AD-01: Python 소스 파일에서 함수/클래스 청크 + 메타데이터 추출
# ============================================================

class TestAnalyzeDirectoryPython:
    """Python 소스 파일 파싱 및 메타데이터 추출"""

    @pytest.mark.asyncio
    async def test_python_function_chunk(self, tmp_path):
        """Python 함수를 청크 단위로 추출하고 메타데이터 포함"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "main.py").write_text(textwrap.dedent("""\
            import os
            from pathlib import Path

            def hello(name: str) -> str:
                greeting = f"Hello, {name}"
                return greeting
        """))

        result = await analyze_directory(str(tmp_path), [".py"])

        assert len(result["chunks"]) >= 1
        func_chunk = next(c for c in result["chunks"] if c["name"] == "hello")
        assert func_chunk["type"] == "function"
        assert "name" in func_chunk["identifiers"]
        assert "greeting" in func_chunk["identifiers"]
        assert func_chunk["file_path"].endswith("main.py")
        assert func_chunk["char_count"] > 0
        assert "def hello" in func_chunk["source_code"]

    @pytest.mark.asyncio
    async def test_python_class_chunk(self, tmp_path):
        """Python 클래스를 청크 단위로 추출하고 데코레이터/메서드 포함"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "service.py").write_text(textwrap.dedent("""\
            from dataclasses import dataclass

            @dataclass
            class UserService:
                name: str

                def get_user(self, user_id: int):
                    return {"id": user_id, "name": self.name}
        """))

        result = await analyze_directory(str(tmp_path), [".py"])

        class_chunk = next(c for c in result["chunks"] if c["name"] == "UserService")
        assert class_chunk["type"] == "class"
        assert "dataclass" in class_chunk["decorators"]
        assert class_chunk["char_count"] > 0

    @pytest.mark.asyncio
    async def test_python_imports_extracted(self, tmp_path):
        """Python import 문이 파일별로 추출됨"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "app.py").write_text(textwrap.dedent("""\
            import os
            from pathlib import Path
            from typing import Optional

            def run():
                pass
        """))

        result = await analyze_directory(str(tmp_path), [".py"])

        func_chunk = next(c for c in result["chunks"] if c["name"] == "run")
        assert any("os" in imp for imp in func_chunk["imports"])
        assert any("pathlib" in imp or "Path" in imp for imp in func_chunk["imports"])


# ============================================================
# AD-02: JS/TS 소스 파일에서 함수/클래스 청크 + 메타데이터 추출
# ============================================================

class TestAnalyzeDirectoryJsTs:
    """JS/TS 소스 파일 파싱 및 메타데이터 추출"""

    @pytest.mark.asyncio
    async def test_js_function_chunk(self, tmp_path):
        """JavaScript 함수를 청크 단위로 추출"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "index.js").write_text(textwrap.dedent("""\
            import express from 'express';

            function createApp(port) {
                const app = express();
                app.listen(port);
                return app;
            }
        """))

        try:
            result = await analyze_directory(str(tmp_path), [".js"])
        except ImportError:
            pytest.skip("tree-sitter JS bindings not installed")

        assert len(result["chunks"]) >= 1
        func_chunk = next(c for c in result["chunks"] if c["name"] == "createApp")
        assert func_chunk["type"] == "function"
        assert func_chunk["file_path"].endswith("index.js")
        assert func_chunk["char_count"] > 0

    @pytest.mark.asyncio
    async def test_ts_class_chunk(self, tmp_path):
        """TypeScript 클래스를 청크 단위로 추출"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "user.ts").write_text(textwrap.dedent("""\
            import { Injectable } from '@nestjs/common';

            class UserService {
                constructor(private readonly db: Database) {}

                async findById(id: number) {
                    return this.db.find(id);
                }
            }
        """))

        try:
            result = await analyze_directory(str(tmp_path), [".ts"])
        except ImportError:
            pytest.skip("tree-sitter TS bindings not installed")

        assert len(result["chunks"]) >= 1
        class_chunk = next(c for c in result["chunks"] if c["name"] == "UserService")
        assert class_chunk["type"] == "class"
        assert class_chunk["char_count"] > 0


# ============================================================
# AD-03: 빈 디렉토리 / 비매칭 확장자 → 빈 결과
# ============================================================

class TestAnalyzeDirectoryEdgeCases:
    """엣지 케이스 처리"""

    @pytest.mark.asyncio
    async def test_empty_directory(self, tmp_path):
        """빈 디렉토리 → 빈 결과"""
        from app.services.ast_analyzer import analyze_directory

        result = await analyze_directory(str(tmp_path), [".py"])

        assert result["chunks"] == []

    @pytest.mark.asyncio
    async def test_no_matching_extensions(self, tmp_path):
        """매칭되는 확장자 없음 → 빈 결과"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "README.md").write_text("# Hello")
        (tmp_path / "data.json").write_text("{}")

        result = await analyze_directory(str(tmp_path), [".py"])

        assert result["chunks"] == []

    @pytest.mark.asyncio
    async def test_syntax_error_file_skipped(self, tmp_path):
        """문법 오류 파일은 건너뛰고 나머지 파싱"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "good.py").write_text("def good():\n    return 1\n")
        (tmp_path / "bad.py").write_text("def bad(\n")  # SyntaxError

        result = await analyze_directory(str(tmp_path), [".py"])

        names = [c["name"] for c in result["chunks"]]
        assert "good" in names

    @pytest.mark.asyncio
    async def test_git_and_hidden_dirs_excluded(self, tmp_path):
        """.git, __pycache__, node_modules 등 제외"""
        from app.services.ast_analyzer import analyze_directory

        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config.py").write_text("def git_internal(): pass\n")

        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "cached.py").write_text("def cached(): pass\n")

        (tmp_path / "real.py").write_text("def real_func(): pass\n")

        result = await analyze_directory(str(tmp_path), [".py"])

        names = [c["name"] for c in result["chunks"]]
        assert "real_func" in names
        assert "git_internal" not in names
        assert "cached" not in names


# ============================================================
# AD-04: 기존 analyze_ast() 함수 동작 유지 (하위 호환)
# ============================================================

class TestAnalyzeAstBackwardCompat:
    """기존 analyze_ast() 하위 호환성"""

    @pytest.mark.asyncio
    async def test_analyze_ast_still_works(self):
        """기존 analyze_ast() 함수가 동일하게 동작"""
        from app.services.ast_analyzer import analyze_ast

        files = [
            {
                "source": "def hello():\n    pass\n\nclass Foo:\n    def bar(self):\n        pass\n",
            }
        ]

        result = await analyze_ast(files, primary_language="python")

        assert "functions" in result
        assert "classes" in result
        assert "imports" in result
        assert "parser_used" in result
        assert any(f["name"] == "hello" for f in result["functions"])
        assert any(c["name"] == "Foo" for c in result["classes"])


# ============================================================
# AD-05: 메타데이터 필드 완전성 검증
# ============================================================

class TestChunkMetadataCompleteness:
    """각 청크에 필수 메타데이터 필드가 모두 존재"""

    @pytest.mark.asyncio
    async def test_all_metadata_fields_present(self, tmp_path):
        """모든 필수 메타데이터 필드 존재 확인"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "sample.py").write_text(textwrap.dedent("""\
            import json
            from os.path import join

            @staticmethod
            def process_data(items: list) -> dict:
                result = {}
                for item in items:
                    result[item] = True
                return result
        """))

        result = await analyze_directory(str(tmp_path), [".py"])

        required_fields = {
            "name", "type", "identifiers", "imports",
            "decorators", "source_code", "char_count", "file_path",
        }

        assert len(result["chunks"]) >= 1
        for chunk in result["chunks"]:
            missing = required_fields - set(chunk.keys())
            assert not missing, f"Missing fields: {missing}"

    @pytest.mark.asyncio
    async def test_identifiers_are_sets_of_strings(self, tmp_path):
        """identifiers는 문자열 set (또는 list)"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "calc.py").write_text(textwrap.dedent("""\
            def add(a, b):
                total = a + b
                return total
        """))

        result = await analyze_directory(str(tmp_path), [".py"])

        chunk = result["chunks"][0]
        assert isinstance(chunk["identifiers"], (set, list))
        assert all(isinstance(i, str) for i in chunk["identifiers"])

    @pytest.mark.asyncio
    async def test_decorators_extracted_correctly(self, tmp_path):
        """데코레이터가 문자열 리스트로 추출"""
        from app.services.ast_analyzer import analyze_directory

        (tmp_path / "api.py").write_text(textwrap.dedent("""\
            import pytest

            @pytest.fixture
            def client():
                return "test_client"

            @staticmethod
            def helper():
                pass
        """))

        result = await analyze_directory(str(tmp_path), [".py"])

        client_chunk = next(c for c in result["chunks"] if c["name"] == "client")
        assert isinstance(client_chunk["decorators"], list)
        # pytest.fixture 또는 Attribute 형태로 추출
        assert len(client_chunk["decorators"]) >= 1

        helper_chunk = next(c for c in result["chunks"] if c["name"] == "helper")
        assert "staticmethod" in helper_chunk["decorators"]
