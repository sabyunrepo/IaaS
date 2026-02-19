"""
TreeSitterAdapter — Tree-sitter 0.25.x 기반 AST 파싱 어댑터.

ADR-0006: Tree-sitter 0.25.x 사용. QueryCursor 분리 패턴 필수.
- Query(language, pattern) → QueryCursor(query) → cursor.captures(root_node)
- captures() 반환값: dict[str, list[Node]]
- Parser는 Thread-safe하지 않으므로 매 요청마다 생성.
- 도메인 모델 import 없음 (순수 infrastructure 유틸리티).
"""
from __future__ import annotations

from tree_sitter import Language, Parser, Query, QueryCursor


class TreeSitterAdapter:
    """Tree-sitter 0.25.x 기반 AST 파싱 어댑터."""

    SUPPORTED_LANGUAGES = ("python", "javascript", "typescript", "java", "go")

    def __init__(self) -> None:
        import tree_sitter_go as tsgo
        import tree_sitter_java as tsjava
        import tree_sitter_javascript as tsjs
        import tree_sitter_python as tspython

        self.languages: dict[str, Language] = {
            "python": Language(tspython.language()),
            "javascript": Language(tsjs.language()),
            "go": Language(tsgo.language()),
            "java": Language(tsjava.language()),
        }

        # TypeScript: 전용 패키지 우선, 없으면 JavaScript 문법으로 fallback
        try:
            from tree_sitter_typescript import language_typescript

            self.languages["typescript"] = Language(language_typescript())
        except ImportError:
            self.languages["typescript"] = Language(tsjs.language())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_parser(self, lang_name: str) -> Parser:
        """Parser는 Thread-safe하지 않으므로 매 요청마다 생성."""
        if lang_name not in self.languages:
            raise ValueError(
                f"Unsupported language: {lang_name}. "
                f"Supported: {self.SUPPORTED_LANGUAGES}"
            )
        return Parser(self.languages[lang_name])

    def parse_code(self, code: str, lang_name: str) -> "tree_sitter.Tree":
        """소스 코드를 파싱하여 AST 트리를 반환."""
        parser = self.get_parser(lang_name)
        return parser.parse(bytes(code, "utf8"))

    def extract_functions(self, root_node: "tree_sitter.Node", lang_name: str) -> list[dict]:
        """함수/메서드 정의를 추출한다.

        Tree-sitter 0.25.x QueryCursor API 사용:
            query = Query(language, pattern)
            cursor = QueryCursor(query)
            captures = cursor.captures(root_node)  # dict[str, list[Node]]

        Returns:
            list of {"name": str, "start_line": int, "end_line": int, "body": str}
        """
        patterns = {
            "python": """
                (function_definition
                    name: (identifier) @func.name) @func.def
            """,
            "javascript": """
                [
                    (function_declaration
                        name: (identifier) @func.name) @func.def
                    (method_definition
                        name: (property_identifier) @func.name) @func.def
                    (arrow_function) @func.def
                ]
            """,
            "typescript": """
                [
                    (function_declaration
                        name: (identifier) @func.name) @func.def
                    (method_definition
                        name: (property_identifier) @func.name) @func.def
                ]
            """,
            "java": """
                (method_declaration
                    name: (identifier) @func.name) @func.def
            """,
            "go": """
                (function_declaration
                    name: (identifier) @func.name) @func.def
            """,
        }

        if lang_name not in patterns:
            raise ValueError(
                f"Unsupported language: {lang_name}. "
                f"Supported: {self.SUPPORTED_LANGUAGES}"
            )

        language = self.languages[lang_name]
        query = Query(language, patterns[lang_name])
        cursor = QueryCursor(query)
        captures: dict[str, list] = cursor.captures(root_node)

        # captures["func.def"] → 함수 전체 노드 리스트
        # captures["func.name"] → 함수 이름 노드 리스트 (없을 수도 있음 e.g. 화살표 함수)
        func_defs: list = captures.get("func.def", [])
        func_names: list = captures.get("func.name", [])

        # 이름 노드를 시작 바이트 기준으로 빠르게 찾기 위한 매핑
        # (start_byte → name_text)
        name_by_start: dict[int, str] = {}
        for name_node in func_names:
            name_by_start[name_node.start_byte] = name_node.text.decode("utf8")

        results: list[dict] = []
        for func_node in func_defs:
            # 함수 이름: 자식 노드 중 identifier 탐색
            func_name = self._find_child_name(func_node, name_by_start)
            results.append(
                {
                    "name": func_name,
                    "start_line": func_node.start_point[0] + 1,  # 0-indexed → 1-indexed
                    "end_line": func_node.end_point[0] + 1,
                    "body": func_node.text.decode("utf8") if func_node.text else "",
                }
            )
        return results

    def extract_imports(self, root_node: "tree_sitter.Node", lang_name: str) -> list[str]:
        """import 구문을 추출한다. 기술 스택 매핑에 사용.

        Returns:
            list of import statement strings
        """
        patterns = {
            "python": """
                [
                    (import_statement) @import
                    (import_from_statement) @import
                ]
            """,
            "javascript": """
                [
                    (import_statement) @import
                    (call_expression
                        function: (identifier) @require.call
                        arguments: (arguments (string) @import))
                ]
            """,
            "typescript": """
                [
                    (import_statement) @import
                ]
            """,
            "java": """
                (import_declaration) @import
            """,
            "go": """
                [
                    (import_declaration) @import
                    (import_spec) @import
                ]
            """,
        }

        if lang_name not in patterns:
            raise ValueError(
                f"Unsupported language: {lang_name}. "
                f"Supported: {self.SUPPORTED_LANGUAGES}"
            )

        language = self.languages[lang_name]
        query = Query(language, patterns[lang_name])
        cursor = QueryCursor(query)
        captures: dict[str, list] = cursor.captures(root_node)

        import_nodes: list = captures.get("import", [])
        return [
            node.text.decode("utf8").strip()
            for node in import_nodes
            if node.text
        ]

    def extract_classes(self, root_node: "tree_sitter.Node", lang_name: str) -> list[dict]:
        """클래스 정의를 추출한다.

        Returns:
            list of {"name": str, "start_line": int, "end_line": int}
        """
        patterns = {
            "python": """
                (class_definition
                    name: (identifier) @class.name) @class.def
            """,
            "javascript": """
                (class_declaration
                    name: (identifier) @class.name) @class.def
            """,
            "typescript": """
                (class_declaration
                    name: (type_identifier) @class.name) @class.def
            """,
            "java": """
                (class_declaration
                    name: (identifier) @class.name) @class.def
            """,
            "go": """
                (type_declaration
                    (type_spec
                        name: (type_identifier) @class.name
                        type: (struct_type))) @class.def
            """,
        }

        if lang_name not in patterns:
            raise ValueError(
                f"Unsupported language: {lang_name}. "
                f"Supported: {self.SUPPORTED_LANGUAGES}"
            )

        language = self.languages[lang_name]
        query = Query(language, patterns[lang_name])
        cursor = QueryCursor(query)
        captures: dict[str, list] = cursor.captures(root_node)

        class_defs: list = captures.get("class.def", [])
        class_names: list = captures.get("class.name", [])

        name_by_start: dict[int, str] = {}
        for name_node in class_names:
            name_by_start[name_node.start_byte] = name_node.text.decode("utf8")

        results: list[dict] = []
        for class_node in class_defs:
            class_name = self._find_child_name(class_node, name_by_start)
            results.append(
                {
                    "name": class_name,
                    "start_line": class_node.start_point[0] + 1,
                    "end_line": class_node.end_point[0] + 1,
                }
            )
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_child_name(
        self,
        node: "tree_sitter.Node",
        name_map: dict[int, str],
    ) -> str:
        """name_map에서 node 범위 내의 이름을 찾는다.

        name_map은 {start_byte: name_text} 형태.
        node의 자식 중 start_byte가 name_map에 있는 것을 반환.
        못 찾으면 "<anonymous>" 반환.
        """
        for child in node.children:
            if child.start_byte in name_map:
                return name_map[child.start_byte]
            # 한 단계 더 내려가서 탐색 (e.g. method_definition 내부)
            for grandchild in child.children:
                if grandchild.start_byte in name_map:
                    return name_map[grandchild.start_byte]
        return "<anonymous>"
