---
title: "Tree-sitter QueryCursor API"
type: component
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [tree-sitter, ast, query, cursor, 0.25.x]
parent: "[[tree-sitter-ast/MOC]]"
children: []
depends-on:
  - "[[tree-sitter-ast/parser-setup]]"
  - "[[tree-sitter-ast/language-support]]"
  - "[[decisions/0006-tree-sitter-025]]"
affects:
  - "[[application/nodes/ast-analyzer-worker]]"
  - "[[application/nodes/skill-extractor-worker]]"
  - "[[application/nodes/architecture-evaluator-worker]]"
linear: [JIT-94]
phase: 2
---

# Tree-sitter QueryCursor API

## 개요

Tree-sitter 0.25.x에서 도입된 `Query` + `QueryCursor` 분리 패턴을 다룬다.
0.24.x의 `query.captures(root_node)` 직접 호출 방식은 **폐기**되었으며,
0.25.x에서는 반드시 `QueryCursor`를 경유해야 한다.
캡처(captures), 매칭(matches), 범위 제한(set_point_range), 바이트 범위 제한(set_byte_range)을 포함한다.

## 상세 설계

### 핵심 개념

| 객체 | 역할 |
|------|------|
| `Query` | S-expression 패턴을 컴파일한 불변 객체. 언어 + 쿼리 문자열로 생성 |
| `QueryCursor` | `Query`를 AST 노드에 실행하는 커서. 캡처/매칭 결과 반환 |
| `captures` | 이름 붙은 노드(`@name`) 목록 반환. 캡처 이름별로 그룹화 |
| `matches` | 패턴 전체가 매칭된 결과 목록 반환. 여러 캡처를 묶어 하나의 매칭으로 반환 |

### API 변경 이력

```python
# 0.24.x 구형 API (사용 금지)
query = language.query(query_scm)          # Language 메서드
captures = query.captures(root_node)       # Query 객체에서 직접 호출

# 0.25.x 신형 API (필수)
from tree_sitter import Query, QueryCursor
query = Query(language, query_scm)         # Query 생성자
cursor = QueryCursor(query)                # QueryCursor로 래핑
captures = cursor.captures(root_node)      # QueryCursor를 통해 호출
```

### 코드 예시

#### 기본 캡처 — 함수 추출

```python
# infrastructure/analysis/tree_sitter_adapter.py
from tree_sitter import Language, Parser, Query, QueryCursor


class TreeSitterAdapter:
    def __init__(self):
        # parser-setup.md 참조
        self.languages: dict[str, Language] = { ... }

    def extract_functions(self, root_node, lang_name: str) -> list[dict]:
        """0.25.x QueryCursor API로 함수/클래스 추출.

        Args:
            root_node: parser.parse(code).root_node
            lang_name: 언어 식별자

        Returns:
            [{"name": "func_name", "node": Node, "capture": "func.name"}, ...]
        """
        query_scm = """
        (function_definition
          name: (identifier) @func.name)
        (class_definition
          name: (identifier) @class.name)
        """
        language = self.languages[lang_name]
        query = Query(language, query_scm)
        cursor = QueryCursor(query)
        # captures() 반환: dict[str, list[Node]]
        # 키는 캡처 이름("func.name", "class.name"), 값은 노드 목록
        captures: dict[str, list] = cursor.captures(root_node)

        results = []
        for capture_name, nodes in captures.items():
            for node in nodes:
                results.append({
                    "name": node.text.decode("utf-8"),
                    "node": node,
                    "capture": capture_name,
                    "start_line": node.start_point[0],
                    "end_line": node.end_point[0],
                })
        return results
```

#### matches() — 다중 캡처를 하나의 패턴으로 묶기

```python
    def extract_function_with_params(
        self, root_node, lang_name: str
    ) -> list[dict]:
        """함수 이름 + 파라미터를 한 번에 추출. matches() 사용."""
        query_scm = """
        (function_definition
          name: (identifier) @func.name
          parameters: (parameters) @func.params)
        """
        language = self.languages[lang_name]
        query = Query(language, query_scm)
        cursor = QueryCursor(query)
        # matches() 반환: list[tuple[int, dict[str, list[Node]]]]
        # 각 튜플: (pattern_index, {capture_name: [Node, ...]})
        matches = cursor.matches(root_node)

        results = []
        for _pattern_idx, capture_dict in matches:
            name_nodes = capture_dict.get("func.name", [])
            param_nodes = capture_dict.get("func.params", [])
            if name_nodes:
                results.append({
                    "name": name_nodes[0].text.decode("utf-8"),
                    "params_text": (
                        param_nodes[0].text.decode("utf-8")
                        if param_nodes else ""
                    ),
                    "start_line": name_nodes[0].start_point[0],
                })
        return results
```

#### 범위 제한 — diff 청크에만 쿼리 적용

```python
    def query_in_range(
        self,
        root_node,
        lang_name: str,
        query_scm: str,
        start_line: int,
        end_line: int,
    ) -> dict[str, list]:
        """변경된 라인 범위 내 노드만 쿼리. CleanerWorker(W2)에서 사용.

        Args:
            start_line: diff hunk 시작 라인 (0-indexed)
            end_line: diff hunk 끝 라인 (0-indexed)
        """
        language = self.languages[lang_name]
        query = Query(language, query_scm)
        cursor = QueryCursor(query)
        # 포인트는 (row, column) 형식 (0-indexed)
        cursor.set_point_range(
            start_point=(start_line, 0),
            end_point=(end_line + 1, 0),
        )
        return cursor.captures(root_node)

    def query_in_byte_range(
        self,
        root_node,
        lang_name: str,
        query_scm: str,
        start_byte: int,
        end_byte: int,
    ) -> dict[str, list]:
        """바이트 오프셋 범위 내 노드만 쿼리."""
        language = self.languages[lang_name]
        query = Query(language, query_scm)
        cursor = QueryCursor(query)
        cursor.set_byte_range(start_byte, end_byte)
        return cursor.captures(root_node)
```

#### import 파싱 — SkillExtractorWorker(W9) 용

```python
    def extract_imports(self, root_node, lang_name: str) -> list[str]:
        """import 구문에서 모듈명 추출. SkillExtractorWorker에서 기술 스택 파악에 사용."""
        query_scm_by_lang = {
            "python": """
                (import_statement
                  name: (dotted_name) @import.module)
                (import_from_statement
                  module_name: (dotted_name) @import.from)
            """,
            "javascript": """
                (import_statement
                  source: (string) @import.source)
            """,
            "go": """
                (import_spec
                  path: (interpreted_string_literal) @import.path)
            """,
        }
        query_scm = query_scm_by_lang.get(lang_name, "")
        if not query_scm:
            return []

        language = self.languages[lang_name]
        query = Query(language, query_scm)
        cursor = QueryCursor(query)
        captures = cursor.captures(root_node)

        modules = []
        for _capture_name, nodes in captures.items():
            for node in nodes:
                raw = node.text.decode("utf-8").strip("\"'")
                modules.append(raw)
        return modules
```

### ASTAnalyzerWorker(W6) 통합 예시

```python
# application/nodes/ast_analyzer_worker.py (발췌)
from infrastructure.analysis.tree_sitter_adapter import TreeSitterAdapter
from infrastructure.analysis.language_detector import detect_language

adapter = TreeSitterAdapter()


async def ast_analyzer_worker(state: dict) -> dict:
    """W6: 레포 전체 파일 AST 분석."""
    repo_files: list[dict] = state["repo_files"]  # [{path, content}, ...]

    ast_trees = {}
    code_chunks = []

    for file_info in repo_files:
        lang = detect_language(file_info["path"])
        if lang is None:
            continue

        tree = adapter.parse_code(file_info["content"], lang)
        root = tree.root_node

        # 함수/클래스 단위 청크 추출
        functions = adapter.extract_functions(root, lang)
        for func in functions:
            code_chunks.append({
                "file_path": file_info["path"],
                "language": lang,
                "name": func["name"],
                "start_line": func["start_line"],
                "end_line": func["end_line"],
                "content": func["node"].text.decode("utf-8"),
            })

        ast_trees[file_info["path"]] = {
            "language": lang,
            "root_node": root,  # Reference Passing — raw data 아님
        }

    return {
        "ast_trees_ref": id(ast_trees),   # Reference Passing (ADR-0004)
        "code_chunks": code_chunks,
    }
```

## 관련 문서

- 상위: [[tree-sitter-ast/MOC]]
- 의존: [[tree-sitter-ast/parser-setup]], [[tree-sitter-ast/language-support]]
- 의존 ADR: [[decisions/0006-tree-sitter-025]]
- 영향: `application/nodes/ast_analyzer_worker.py`, `application/nodes/cleaner_worker.py`
- 설계 원본: `plan/v5-design/phase2-infrastructure.md` §9.0, §9.3
