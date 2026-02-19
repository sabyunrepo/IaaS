---
title: "Tree-sitter Parser Setup"
type: component
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [tree-sitter, ast, parser, infrastructure]
parent: "[[tree-sitter-ast/MOC]]"
children:
  - "[[tree-sitter-ast/language-support]]"
  - "[[tree-sitter-ast/query-cursor-api]]"
depends-on:
  - "[[decisions/0006-tree-sitter-025]]"
affects:
  - "[[application/nodes/ast-analyzer-worker]]"
  - "[[application/nodes/cleaner-worker]]"
linear: [JIT-94]
phase: 2
---

# Tree-sitter Parser Setup

## 개요

Tree-sitter 0.25.x 기반 `TreeSitterAdapter` 클래스 설정 코드.
`Language.build_library()` 방식(.so 파일 빌드)은 0.24에서 이미 폐기되었으며,
0.25.x에서는 언어별 Python 패키지 바인딩(`tree_sitter_python` 등)을 직접 사용한다.
`Parser`는 Thread-safe하지 않으므로 매 요청마다 새 인스턴스를 생성한다.

## 상세 설계

### 핵심 개념

| 개념 | 설명 |
|------|------|
| `Language` | 특정 언어의 문법 정의 객체. 어댑터 초기화 시 언어 패키지에서 로드 |
| `Parser` | 코드 문자열을 AST로 변환. Thread-safe 하지 않아 요청당 생성 |
| `Tree` | `parser.parse()` 결과. `root_node`로 전체 AST 접근 |
| `Node` | AST의 개별 노드. `type`, `text`, `start_point`, `end_point` 보유 |

### 의존성 버전

```toml
# pyproject.toml (ADR-0006 결정사항)
tree-sitter = ">=0.25.2"
tree-sitter-python = ">=0.23.6"
tree-sitter-javascript = ">=0.23.1"
tree-sitter-go = ">=0.23.4"
tree-sitter-java = ">=0.23.5"
```

### 코드 예시

```python
# infrastructure/analysis/tree_sitter_adapter.py
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava


class TreeSitterAdapter:
    """Tree-sitter 0.25.x 기반 AST 어댑터.

    주의:
        - `Parser`는 Thread-safe하지 않으므로 매 요청마다 `get_parser()`로 새 인스턴스를 생성한다.
        - `Language` 객체는 불변이므로 어댑터 인스턴스에서 공유해도 안전하다.
        - 0.24.x의 `Language.build_library()` 빌드 방식은 사용하지 않는다.
    """

    def __init__(self):
        # 0.25.x: 언어별 패키지에서 직접 Language 객체 로딩
        self.languages: dict[str, Language] = {
            "python": Language(tspython.language()),
            "javascript": Language(tsjs.language()),
            "typescript": Language(tsjs.language()),  # JS 문법 공유
            "go": Language(tsgo.language()),
            "java": Language(tsjava.language()),
        }

    def get_parser(self, lang_name: str) -> Parser:
        """Parser는 Thread-safe하지 않으므로 매 요청마다 생성.

        Args:
            lang_name: "python" | "javascript" | "typescript" | "go" | "java"

        Returns:
            해당 언어로 초기화된 Parser 인스턴스

        Raises:
            ValueError: 지원하지 않는 언어
        """
        if lang_name not in self.languages:
            raise ValueError(
                f"Unsupported language: {lang_name}. "
                f"Supported: {list(self.languages.keys())}"
            )
        return Parser(self.languages[lang_name])

    def parse_code(self, code: str, lang_name: str):
        """코드 문자열을 AST Tree로 변환.

        Args:
            code: 파싱할 소스코드 문자열
            lang_name: 언어 식별자

        Returns:
            tree_sitter.Tree 객체. `tree.root_node`로 루트 노드 접근
        """
        parser = self.get_parser(lang_name)
        return parser.parse(bytes(code, "utf8"))

    def get_language(self, lang_name: str) -> Language:
        """Query 생성에 필요한 Language 객체 반환."""
        if lang_name not in self.languages:
            raise ValueError(f"Unsupported language: {lang_name}")
        return self.languages[lang_name]
```

### 언어 자동 감지

```python
# infrastructure/analysis/language_detector.py
from pathlib import Path

EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
}

def detect_language(file_path: str) -> str | None:
    """파일 확장자로 언어 식별자 반환. 미지원 확장자는 None."""
    ext = Path(file_path).suffix.lower()
    return EXTENSION_MAP.get(ext)
```

## 관련 문서

- 상위: [[tree-sitter-ast/MOC]]
- 의존: [[decisions/0006-tree-sitter-025]]
- 하위: [[tree-sitter-ast/language-support]], [[tree-sitter-ast/query-cursor-api]]
- 설계 원본: `plan/v5-design/phase2-infrastructure.md` §9.0, §9.3
