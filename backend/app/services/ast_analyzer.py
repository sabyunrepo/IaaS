"""
backend/app/services/ast_analyzer.py
AST 구조 분석 (Python: ast, JS/TS: tree-sitter, fallback)

Extracted from code_analyzer.py for SRP compliance.
"""
import logging

logger = logging.getLogger(__name__)


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
