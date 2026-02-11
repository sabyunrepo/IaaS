"""
backend/app/services/ast_analyzer.py
AST 구조 분석 (Python: ast, JS/TS: tree-sitter, fallback)

Extracted from code_analyzer.py for SRP compliance.

JIT-21/24: analyze_directory() — clone_dir에서 직접 AST 파싱 + 청크 메타데이터 추출
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# analyze_directory 지원 확장자
_SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
}

# 제외 디렉토리
_EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tox", "dist", "build"}


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


# =========================================================================
# analyze_directory — clone_dir에서 직접 AST 파싱 + 청크 메타데이터 추출 (JIT-21/24)
# =========================================================================


def analyze_directory(
    clone_dir: str,
    file_types: list[str] | None = None,
    max_files: int = 50,
    max_chunk_chars: int = 10_000,
) -> list[dict]:
    """clone_dir에서 소스 파일을 읽어 함수/클래스 단위 청크를 추출

    chunk_scorer.rank_chunks_by_relevance()의 입력 포맷:
    {name, type, file_path, source_code, identifiers, imports, decorators, char_count}

    Args:
        clone_dir: shallow clone 디렉토리 경로
        file_types: 분석 대상 확장자 (예: [".py", ".ts"]). None이면 전체 지원 언어.
        max_files: 최대 분석 파일 수
        max_chunk_chars: 청크별 최대 문자 수

    Returns:
        청크 dict 리스트
    """
    ext_set = set(file_types) if file_types else set(_SUPPORTED_EXTENSIONS.keys())
    # 지원 언어만 필터
    ext_set = ext_set & set(_SUPPORTED_EXTENSIONS.keys())
    if not ext_set:
        ext_set = {".py"}

    # 파일 수집 (크기 역순 = 큰 파일 우선)
    candidates: list[tuple[int, str, str]] = []
    for root, dirs, filenames in os.walk(clone_dir):
        dirs[:] = [d for d in dirs if d not in _EXCLUDE_DIRS]
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext not in ext_set:
                continue
            abs_path = os.path.join(root, fname)
            try:
                fsize = os.path.getsize(abs_path)
            except OSError:
                continue
            if fsize == 0 or fsize > 200_000:
                continue
            rel_path = os.path.relpath(abs_path, clone_dir)
            candidates.append((fsize, rel_path, abs_path))

    candidates.sort(key=lambda x: x[0], reverse=True)

    chunks: list[dict] = []
    files_processed = 0

    for _, rel_path, abs_path in candidates:
        if files_processed >= max_files:
            break
        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as fh:
                source = fh.read()
        except OSError:
            continue

        ext = Path(rel_path).suffix.lower()
        lang = _SUPPORTED_EXTENSIONS.get(ext, "")
        file_chunks = _extract_chunks(source, rel_path, lang, max_chunk_chars)
        chunks.extend(file_chunks)
        files_processed += 1

    logger.info(f"analyze_directory: {files_processed} files → {len(chunks)} chunks from {clone_dir}")
    return chunks


def _extract_chunks(
    source: str,
    file_path: str,
    lang: str,
    max_chars: int,
) -> list[dict]:
    """소스 코드에서 함수/클래스 단위 청크 추출"""
    if lang == "python":
        return _extract_python_chunks(source, file_path, max_chars)
    # JS/TS: tree-sitter 사용 시도, 실패 시 전체 파일을 하나의 청크로
    if lang in ("javascript", "typescript"):
        ts_chunks = _extract_ts_chunks(source, file_path, lang, max_chars)
        if ts_chunks:
            return ts_chunks
    # 기타 언어 또는 파서 실패: 파일 전체를 하나의 청크로
    return _file_level_chunk(source, file_path, max_chars)


def _extract_python_chunks(
    source: str,
    file_path: str,
    max_chars: int,
) -> list[dict]:
    """Python AST로 함수/클래스 청크 추출"""
    import ast as ast_mod

    chunks: list[dict] = []
    lines = source.splitlines(keepends=True)

    # 파일 레벨 imports 수집
    file_imports: list[str] = []
    try:
        tree = ast_mod.parse(source)
    except SyntaxError:
        return _file_level_chunk(source, file_path, max_chars)

    for node in ast_mod.iter_child_nodes(tree):
        if isinstance(node, ast_mod.Import):
            for alias in node.names:
                file_imports.append(f"import {alias.name}")
        elif isinstance(node, ast_mod.ImportFrom):
            file_imports.append(f"from {node.module or ''} import ...")

    for node in ast_mod.iter_child_nodes(tree):
        if isinstance(node, (ast_mod.FunctionDef, ast_mod.AsyncFunctionDef)):
            chunk_source = ast_mod.get_source_segment(source, node) or ""
            if not chunk_source:
                # fallback: 줄 번호 기반
                start = node.lineno - 1
                end = node.end_lineno or (start + 1)
                chunk_source = "".join(lines[start:end])
            chunk_source = chunk_source[:max_chars]

            decorators = []
            for d in node.decorator_list:
                if isinstance(d, ast_mod.Name):
                    decorators.append(d.id)
                elif isinstance(d, ast_mod.Attribute):
                    decorators.append(ast_mod.unparse(d))
                else:
                    decorators.append(ast_mod.unparse(d))

            identifiers = _extract_python_identifiers(node)

            chunks.append({
                "name": node.name,
                "type": "function",
                "file_path": file_path,
                "source_code": chunk_source,
                "identifiers": identifiers,
                "imports": file_imports,
                "decorators": decorators,
                "char_count": len(chunk_source),
            })

        elif isinstance(node, ast_mod.ClassDef):
            chunk_source = ast_mod.get_source_segment(source, node) or ""
            if not chunk_source:
                start = node.lineno - 1
                end = node.end_lineno or (start + 1)
                chunk_source = "".join(lines[start:end])
            chunk_source = chunk_source[:max_chars]

            decorators = []
            for d in node.decorator_list:
                if isinstance(d, ast_mod.Name):
                    decorators.append(d.id)
                elif isinstance(d, ast_mod.Attribute):
                    decorators.append(ast_mod.unparse(d))
                else:
                    decorators.append(ast_mod.unparse(d))

            identifiers = _extract_python_identifiers(node)

            chunks.append({
                "name": node.name,
                "type": "class",
                "file_path": file_path,
                "source_code": chunk_source,
                "identifiers": identifiers,
                "imports": file_imports,
                "decorators": decorators,
                "char_count": len(chunk_source),
            })

    if not chunks:
        return _file_level_chunk(source, file_path, max_chars)

    return chunks


def _extract_python_identifiers(node) -> list[str]:
    """Python AST 노드에서 식별자(변수명, 호출명) 추출"""
    import ast as ast_mod
    identifiers: set[str] = set()
    for child in ast_mod.walk(node):
        if isinstance(child, ast_mod.Name):
            identifiers.add(child.id)
        elif isinstance(child, ast_mod.Attribute):
            identifiers.add(child.attr)
        elif isinstance(child, ast_mod.FunctionDef):
            identifiers.add(child.name)
        elif isinstance(child, ast_mod.AsyncFunctionDef):
            identifiers.add(child.name)
    return list(identifiers)[:50]


def _extract_ts_chunks(
    source: str,
    file_path: str,
    lang: str,
    max_chars: int,
) -> list[dict]:
    """tree-sitter로 JS/TS 청크 추출. 실패 시 빈 리스트."""
    try:
        if lang == "typescript":
            import tree_sitter_typescript as ts_ts
            from tree_sitter import Language, Parser
            language = Language(ts_ts.language_typescript())
        else:
            import tree_sitter_javascript as ts_js
            from tree_sitter import Language, Parser
            language = Language(ts_js.language())

        parser = Parser(language)
        tree = parser.parse(source.encode("utf-8"))
    except (ImportError, Exception):
        return []

    file_imports: list[str] = []
    chunks: list[dict] = []
    _walk_ts_for_chunks(tree.root_node, source, file_path, file_imports, chunks, max_chars)
    return chunks


def _walk_ts_for_chunks(
    node,
    source: str,
    file_path: str,
    file_imports: list[str],
    chunks: list[dict],
    max_chars: int,
) -> None:
    """tree-sitter 노드에서 청크 추출"""
    ntype = node.type

    if ntype == "import_statement":
        src_node = node.child_by_field_name("source")
        if src_node:
            file_imports.append(src_node.text.decode("utf-8").strip("'\""))

    if ntype in ("function_declaration", "method_definition", "arrow_function"):
        chunk_text = source[node.start_byte:node.end_byte][:max_chars]
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode("utf-8") if name_node else "<anonymous>"

        if ntype == "arrow_function" and node.parent and node.parent.type == "variable_declarator":
            pname = node.parent.child_by_field_name("name")
            if pname:
                name = pname.text.decode("utf-8")

        identifiers = _extract_ts_identifiers(node)
        chunks.append({
            "name": name,
            "type": "function",
            "file_path": file_path,
            "source_code": chunk_text,
            "identifiers": identifiers,
            "imports": list(file_imports),
            "decorators": [],
            "char_count": len(chunk_text),
        })
        return  # 중첩 함수는 별도 추출하지 않음

    if ntype == "class_declaration":
        chunk_text = source[node.start_byte:node.end_byte][:max_chars]
        name_node = node.child_by_field_name("name")
        name = name_node.text.decode("utf-8") if name_node else "<anonymous>"
        identifiers = _extract_ts_identifiers(node)
        chunks.append({
            "name": name,
            "type": "class",
            "file_path": file_path,
            "source_code": chunk_text,
            "identifiers": identifiers,
            "imports": list(file_imports),
            "decorators": [],
            "char_count": len(chunk_text),
        })
        return

    for child in node.children:
        _walk_ts_for_chunks(child, source, file_path, file_imports, chunks, max_chars)


def _extract_ts_identifiers(node) -> list[str]:
    """tree-sitter 노드에서 식별자 추출"""
    identifiers: set[str] = set()

    def _walk(n):
        if n.type == "identifier":
            identifiers.add(n.text.decode("utf-8"))
        for child in n.children:
            _walk(child)

    _walk(node)
    return list(identifiers)[:50]


def _file_level_chunk(
    source: str,
    file_path: str,
    max_chars: int,
) -> list[dict]:
    """파일 전체를 단일 청크로 반환 (파서 실패 / 비지원 언어 fallback)"""
    if not source.strip():
        return []
    truncated = source[:max_chars]
    name = Path(file_path).stem
    return [{
        "name": f"file:{name}",
        "type": "module",
        "file_path": file_path,
        "source_code": truncated,
        "identifiers": [],
        "imports": [],
        "decorators": [],
        "char_count": len(truncated),
    }]
