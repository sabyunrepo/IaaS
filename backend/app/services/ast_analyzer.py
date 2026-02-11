"""
backend/app/services/ast_analyzer.py
AST 구조 분석 (Python: ast, JS/TS: tree-sitter, fallback)

Extracted from code_analyzer.py for SRP compliance.
"""
import logging
import os

logger = logging.getLogger(__name__)

# 디렉토리 순회 시 건너뛸 디렉토리명
_SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tox", ".mypy_cache"}

# 확장자 → 언어 매핑
_EXT_TO_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}

async def analyze_ast(
    files: list[dict],
    primary_language: str | None = None,
) -> dict:
    """AST 구조 분석 (Python: ast, JS/TS: tree-sitter, fallback)

    Note: diff 모드에서는 source 대신 diff 필드 사용 시도
    """
    functions = []
    classes = []
    imports = []
    patterns = []
    parser_used = "fallback"

    if primary_language and primary_language.lower() == "python":
        parser_used = "ast"
        import ast as ast_mod
        for f in files:
            # diff 모드 호환: source 없으면 diff에서 추출 시도
            source = f.get("source", "") or f.get("diff", "")
            if not source:
                continue
            try:
                tree = ast_mod.parse(source)
                for node in ast_mod.walk(tree):
                    if isinstance(node, ast_mod.FunctionDef):
                        functions.append({
                            "name": node.name,
                            "params": [a.arg for a in node.args.args],
                            "decorators": [
                                d.id if isinstance(d, ast_mod.Name) else str(d)
                                for d in node.decorator_list
                            ],
                            "complexity": f.get("complexity", 0),
                        })
                    elif isinstance(node, ast_mod.ClassDef):
                        classes.append({
                            "name": node.name,
                            "bases": [
                                b.id if isinstance(b, ast_mod.Name) else str(b)
                                for b in node.bases
                            ],
                            "methods": [
                                n.name for n in node.body
                                if isinstance(n, ast_mod.FunctionDef)
                            ],
                        })
                    elif isinstance(node, ast_mod.Import):
                        for alias in node.names:
                            imports.append({"module": alias.name, "alias": alias.asname})
                    elif isinstance(node, ast_mod.ImportFrom):
                        imports.append({"module": node.module, "alias": None})
            except SyntaxError:
                continue

    elif primary_language and primary_language.lower() in ("javascript", "typescript"):
        try:
            import tree_sitter_javascript as ts_js
            import tree_sitter_typescript as ts_ts
            from tree_sitter import Language, Parser

            if primary_language.lower() == "typescript":
                language = Language(ts_ts.language_typescript())
            else:
                language = Language(ts_js.language())

            ts_parser = Parser(language)
            parser_used = "tree_sitter"

            for f in files:
                # diff 모드 호환: source 없으면 diff에서 추출 시도
                source = f.get("source", "") or f.get("diff", "")
                if not source:
                    continue
                try:
                    tree = ts_parser.parse(source.encode("utf-8"))
                    _walk_ts_node(tree.root_node, functions, classes, imports, f)
                except Exception:
                    continue
        except ImportError:
            logger.warning("tree-sitter JS/TS bindings not installed, using fallback")

    # Fallback for unsupported languages: use Lizard metrics if available
    if parser_used == "fallback" and primary_language:
        parser_used = "lizard_metrics"
        for f in files:
            # Lizard function_metrics may be embedded in file data
            func_metrics = f.get("function_metrics", [])
            for fm in func_metrics:
                functions.append({
                    "name": fm.get("function_name", ""),
                    "params": [],
                    "decorators": [],
                    "complexity": fm.get("cyclomatic_complexity", 0),
                    "nloc": fm.get("nloc", 0),
                    "analysis_method": "lizard_metrics",
                })

            # Basic file-level info from Lizard
            if f.get("complexity") or f.get("nloc"):
                filename = f.get("filename", "")
                if filename and not any(fn.get("name") == filename for fn in functions):
                    functions.append({
                        "name": f"file:{filename}",
                        "params": [],
                        "decorators": [],
                        "complexity": f.get("complexity", 0),
                        "nloc": f.get("nloc", 0),
                        "analysis_method": "lizard_metrics",
                    })

    return {
        "functions": functions[:50],
        "classes": classes[:30],
        "patterns": patterns,
        "imports": imports[:50],
        "parser_used": parser_used,
    }


def _walk_ts_node(
    node,
    functions: list,
    classes: list,
    imports: list,
    file_info: dict,
) -> None:
    """tree-sitter 노드를 순회하며 함수, 클래스, import 추출"""
    ntype = node.type

    if ntype in ("function_declaration", "method_definition"):
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")
        params = []
        if params_node:
            for child in params_node.children:
                if child.type in ("identifier", "required_parameter", "optional_parameter"):
                    params.append(child.text.decode("utf-8"))
        functions.append({
            "name": name_node.text.decode("utf-8") if name_node else "<anonymous>",
            "params": params,
            "decorators": [],
            "complexity": file_info.get("complexity", 0),
        })

    elif ntype == "arrow_function":
        parent = node.parent
        name = "<arrow>"
        if parent and parent.type == "variable_declarator":
            name_node = parent.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
        params_node = node.child_by_field_name("parameters")
        params = []
        if params_node:
            for child in params_node.children:
                if child.type in ("identifier", "required_parameter", "optional_parameter"):
                    params.append(child.text.decode("utf-8"))
        functions.append({
            "name": name,
            "params": params,
            "decorators": [],
            "complexity": file_info.get("complexity", 0),
        })

    elif ntype == "class_declaration":
        name_node = node.child_by_field_name("name")
        methods = []
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "method_definition":
                    m_name = child.child_by_field_name("name")
                    if m_name:
                        methods.append(m_name.text.decode("utf-8"))
        classes.append({
            "name": name_node.text.decode("utf-8") if name_node else "<anonymous>",
            "bases": [],
            "methods": methods,
        })

    elif ntype == "import_statement":
        source_node = node.child_by_field_name("source")
        imports.append({
            "module": source_node.text.decode("utf-8").strip("'\"") if source_node else "",
            "alias": None,
        })

    for child in node.children:
        _walk_ts_node(child, functions, classes, imports, file_info)


# ============================================================
# analyze_directory — clone 디렉토리에서 직접 파싱 [JIT-21]
# ============================================================

async def analyze_directory(
    clone_dir: str,
    file_types: list[str],
) -> dict:
    """clone 디렉토리의 소스 파일을 직접 파싱하여 함수/클래스 청크 + 메타데이터 추출.

    Args:
        clone_dir: clone된 레포 디렉토리 경로
        file_types: 파싱할 파일 확장자 목록 (예: [".py", ".js", ".ts"])

    Returns:
        {"chunks": [ChunkDict, ...]}
        ChunkDict keys: name, type, identifiers, imports, decorators,
                        source_code, char_count, file_path
    """
    chunks: list[dict] = []

    for root, dirs, filenames in os.walk(clone_dir):
        # 숨김 디렉토리 및 불필요한 디렉토리 제외
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith(".")]

        for filename in filenames:
            ext = os.path.splitext(filename)[1]
            if ext not in file_types:
                continue

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, clone_dir)

            try:
                with open(filepath, encoding="utf-8", errors="replace") as fh:
                    source = fh.read()
            except (OSError, UnicodeDecodeError):
                continue

            if not source.strip():
                continue

            lang = _EXT_TO_LANG.get(ext)
            if lang == "python":
                _parse_python_chunks(source, rel_path, chunks)
            elif lang in ("javascript", "typescript"):
                _parse_ts_chunks(source, rel_path, lang, chunks)

    return {"chunks": chunks}


def _parse_python_chunks(
    source: str,
    file_path: str,
    chunks: list[dict],
) -> None:
    """Python 소스에서 함수/클래스 청크를 추출하여 chunks 리스트에 추가."""
    import ast as ast_mod

    # 파일 전체의 import 문 추출
    file_imports: list[str] = []
    try:
        tree = ast_mod.parse(source)
    except SyntaxError:
        return

    for node in ast_mod.walk(tree):
        if isinstance(node, ast_mod.Import):
            for alias in node.names:
                file_imports.append(f"import {alias.name}")
        elif isinstance(node, ast_mod.ImportFrom):
            module = node.module or ""
            names = ", ".join(a.name for a in node.names)
            file_imports.append(f"from {module} import {names}")

    source_lines = source.splitlines()

    for node in ast_mod.iter_child_nodes(tree):
        if isinstance(node, ast_mod.FunctionDef) or isinstance(node, ast_mod.AsyncFunctionDef):
            chunk_source = ast_mod.get_source_segment(source, node) or _get_lines(source_lines, node)
            identifiers = _extract_python_identifiers(node)
            decorators = _extract_python_decorators(node)

            chunks.append({
                "name": node.name,
                "type": "function",
                "identifiers": identifiers,
                "imports": list(file_imports),
                "decorators": decorators,
                "source_code": chunk_source,
                "char_count": len(chunk_source),
                "file_path": file_path,
            })

        elif isinstance(node, ast_mod.ClassDef):
            chunk_source = ast_mod.get_source_segment(source, node) or _get_lines(source_lines, node)
            identifiers = _extract_python_identifiers(node)
            decorators = _extract_python_decorators(node)

            chunks.append({
                "name": node.name,
                "type": "class",
                "identifiers": identifiers,
                "imports": list(file_imports),
                "decorators": decorators,
                "source_code": chunk_source,
                "char_count": len(chunk_source),
                "file_path": file_path,
            })


def _extract_python_identifiers(node) -> list[str]:
    """AST 노드에서 사용된 변수/함수명(Name 노드)을 추출."""
    import ast as ast_mod

    identifiers: set[str] = set()
    for child in ast_mod.walk(node):
        if isinstance(child, ast_mod.Name):
            identifiers.add(child.id)
        elif isinstance(child, ast_mod.arg):
            identifiers.add(child.arg)
    return sorted(identifiers)


def _extract_python_decorators(node) -> list[str]:
    """AST 노드의 데코레이터 리스트를 문자열로 추출."""
    import ast as ast_mod

    decorators: list[str] = []
    for d in getattr(node, "decorator_list", []):
        if isinstance(d, ast_mod.Name):
            decorators.append(d.id)
        elif isinstance(d, ast_mod.Attribute):
            # @pytest.fixture → "pytest.fixture"
            parts = []
            current = d
            while isinstance(current, ast_mod.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast_mod.Name):
                parts.append(current.id)
            decorators.append(".".join(reversed(parts)))
        elif isinstance(d, ast_mod.Call):
            # @app.get("/path") → 함수 부분만 추출
            func = d.func
            if isinstance(func, ast_mod.Name):
                decorators.append(func.id)
            elif isinstance(func, ast_mod.Attribute):
                parts = []
                current = func
                while isinstance(current, ast_mod.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast_mod.Name):
                    parts.append(current.id)
                decorators.append(".".join(reversed(parts)))
    return decorators


def _get_lines(source_lines: list[str], node) -> str:
    """ast 노드의 소스 코드를 줄 번호로 추출 (get_source_segment fallback)."""
    start = getattr(node, "lineno", 1) - 1
    end = getattr(node, "end_lineno", start + 1)
    return "\n".join(source_lines[start:end])


def _parse_ts_chunks(
    source: str,
    file_path: str,
    lang: str,
    chunks: list[dict],
) -> None:
    """JS/TS 소스에서 함수/클래스 청크를 추출하여 chunks 리스트에 추가."""
    try:
        import tree_sitter_javascript as ts_js
        import tree_sitter_typescript as ts_ts
        from tree_sitter import Language, Parser
    except ImportError:
        raise ImportError("tree-sitter JS/TS bindings not installed")

    if lang == "typescript":
        language = Language(ts_ts.language_typescript())
    else:
        language = Language(ts_js.language())

    ts_parser = Parser(language)

    try:
        tree = ts_parser.parse(source.encode("utf-8"))
    except Exception:
        return

    # 파일 전체의 import 추출
    file_imports: list[str] = []
    _collect_ts_imports(tree.root_node, file_imports)

    # 최상위 함수/클래스 추출
    _collect_ts_chunks(tree.root_node, file_path, file_imports, source, chunks)


def _collect_ts_imports(node, file_imports: list[str]) -> None:
    """tree-sitter 루트 노드에서 import 문을 수집."""
    for child in node.children:
        if child.type == "import_statement":
            file_imports.append(child.text.decode("utf-8"))
        elif child.type == "import_declaration":
            file_imports.append(child.text.decode("utf-8"))


def _collect_ts_chunks(
    node,
    file_path: str,
    file_imports: list[str],
    source: str,
    chunks: list[dict],
) -> None:
    """tree-sitter 노드를 순회하며 함수/클래스 청크를 수집."""
    for child in node.children:
        ntype = child.type

        if ntype in ("function_declaration", "method_definition"):
            name_node = child.child_by_field_name("name")
            chunk_source = child.text.decode("utf-8")
            identifiers = _collect_ts_identifiers(child)

            chunks.append({
                "name": name_node.text.decode("utf-8") if name_node else "<anonymous>",
                "type": "function",
                "identifiers": sorted(identifiers),
                "imports": list(file_imports),
                "decorators": [],
                "source_code": chunk_source,
                "char_count": len(chunk_source),
                "file_path": file_path,
            })

        elif ntype == "lexical_declaration":
            # const foo = () => {} 패턴
            for decl in child.children:
                if decl.type == "variable_declarator":
                    value = decl.child_by_field_name("value")
                    if value and value.type == "arrow_function":
                        name_node = decl.child_by_field_name("name")
                        chunk_source = child.text.decode("utf-8")
                        identifiers = _collect_ts_identifiers(value)

                        chunks.append({
                            "name": name_node.text.decode("utf-8") if name_node else "<arrow>",
                            "type": "function",
                            "identifiers": sorted(identifiers),
                            "imports": list(file_imports),
                            "decorators": [],
                            "source_code": chunk_source,
                            "char_count": len(chunk_source),
                            "file_path": file_path,
                        })

        elif ntype == "class_declaration":
            name_node = child.child_by_field_name("name")
            chunk_source = child.text.decode("utf-8")
            identifiers = _collect_ts_identifiers(child)

            chunks.append({
                "name": name_node.text.decode("utf-8") if name_node else "<anonymous>",
                "type": "class",
                "identifiers": sorted(identifiers),
                "imports": list(file_imports),
                "decorators": [],
                "source_code": chunk_source,
                "char_count": len(chunk_source),
                "file_path": file_path,
            })

        elif ntype == "export_statement":
            # export function / export class 패턴
            _collect_ts_chunks(child, file_path, file_imports, source, chunks)


def _collect_ts_identifiers(node) -> set[str]:
    """tree-sitter 노드에서 identifier를 재귀적으로 수집."""
    identifiers: set[str] = set()

    if node.type == "identifier":
        identifiers.add(node.text.decode("utf-8"))

    for child in node.children:
        identifiers.update(_collect_ts_identifiers(child))

    return identifiers
