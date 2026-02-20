---
title: "Tree-sitter Language Support"
type: component
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [tree-sitter, ast, language, grammar]
parent: "[[tree-sitter-ast/MOC]]"
children: []
depends-on:
  - "[[tree-sitter-ast/parser-setup]]"
  - "[[decisions/0006-tree-sitter-025]]"
affects:
  - "[[application/nodes/ast-analyzer-worker]]"
  - "[[application/nodes/skill-extractor-worker]]"
linear: [JIT-94]
phase: 2
---

# Tree-sitter Language Support

## 개요

Tree-sitter 0.25.x에서 지원하는 5개 언어(Python, JavaScript, TypeScript, Java, Go)의
`Language` 객체 생성 방법과 각 언어의 주요 노드 타입을 정리한다.
TypeScript는 별도 문법 패키지 없이 JavaScript 패키지를 재사용한다.

## 상세 설계

### 지원 언어 목록

| 언어 | 패키지 | 버전 | 노드 타입 (주요) |
|------|--------|------|-----------------|
| Python | `tree-sitter-python` | >=0.23.6 | `function_definition`, `class_definition`, `import_statement`, `import_from_statement` |
| JavaScript | `tree-sitter-javascript` | >=0.23.1 | `function_declaration`, `arrow_function`, `class_declaration`, `import_statement` |
| TypeScript | `tree-sitter-javascript` | >=0.23.1 | JS 문법 공유 (TSX/TS 구문 포함) |
| Java | `tree-sitter-java` | >=0.23.5 | `method_declaration`, `class_declaration`, `import_declaration` |
| Go | `tree-sitter-go` | >=0.23.4 | `function_declaration`, `method_declaration`, `import_declaration` |

### Language 객체 생성

```python
# infrastructure/analysis/tree_sitter_adapter.py (Language 초기화 발췌)
from tree_sitter import Language
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava

# 각 언어 패키지의 .language() 함수가 PyCapsule을 반환하며,
# Language() 생성자가 이를 Language 객체로 래핑한다.
languages: dict[str, Language] = {
    "python":     Language(tspython.language()),
    "javascript": Language(tsjs.language()),
    "typescript": Language(tsjs.language()),  # 동일 패키지, 동일 Language 객체
    "go":         Language(tsgo.language()),
    "java":       Language(tsjava.language()),
}
```

### 언어별 S-expression 쿼리 예시

#### Python — 함수 정의 추출

```scheme
; Python 함수 및 클래스 추출
(function_definition
  name: (identifier) @func.name
  parameters: (parameters) @func.params
  body: (block) @func.body)

(class_definition
  name: (identifier) @class.name
  body: (block) @class.body)

; import 구문
(import_statement
  name: (dotted_name) @import.module)

(import_from_statement
  module_name: (dotted_name) @import.from
  name: (dotted_name) @import.name)
```

#### JavaScript / TypeScript — 함수 및 화살표 함수

```scheme
; 일반 함수 선언
(function_declaration
  name: (identifier) @func.name
  parameters: (formal_parameters) @func.params)

; 화살표 함수 (변수 선언 포함)
(lexical_declaration
  (variable_declarator
    name: (identifier) @func.name
    value: (arrow_function) @func.arrow))

; 클래스
(class_declaration
  name: (identifier) @class.name)

; ES module import
(import_statement
  source: (string) @import.source)
```

#### Java — 메서드 및 클래스

```scheme
; 클래스 선언
(class_declaration
  name: (identifier) @class.name)

; 메서드 선언
(method_declaration
  name: (identifier) @method.name
  parameters: (formal_parameters) @method.params)

; import 선언
(import_declaration
  (scoped_identifier) @import.path)
```

#### Go — 함수 및 메서드

```scheme
; 함수 선언
(function_declaration
  name: (identifier) @func.name
  parameters: (parameter_list) @func.params)

; 메서드 선언 (리시버 포함)
(method_declaration
  receiver: (parameter_list) @method.receiver
  name: (field_identifier) @method.name)

; import
(import_declaration
  (import_spec
    path: (interpreted_string_literal) @import.path))
```

### 언어별 Strategy 클래스 구조

```python
# infrastructure/analysis/strategy.py
from abc import ABC, abstractmethod


class AnalysisStrategy(ABC):
    @abstractmethod
    def get_function_query_scm(self) -> str:
        """함수 추출용 S-expression 쿼리 문자열 반환"""
        ...

    @abstractmethod
    def get_import_query_scm(self) -> str:
        """import 추출용 S-expression 쿼리 문자열 반환"""
        ...


class PythonAnalysisStrategy(AnalysisStrategy):
    def get_function_query_scm(self) -> str:
        return """
        (function_definition
          name: (identifier) @func.name)
        (class_definition
          name: (identifier) @class.name)
        """

    def get_import_query_scm(self) -> str:
        return """
        (import_statement
          name: (dotted_name) @import.module)
        (import_from_statement
          module_name: (dotted_name) @import.from)
        """


class JavaScriptAnalysisStrategy(AnalysisStrategy):
    """TypeScript도 동일 Strategy 사용 (JS 문법 공유)"""

    def get_function_query_scm(self) -> str:
        return """
        (function_declaration
          name: (identifier) @func.name)
        (class_declaration
          name: (identifier) @class.name)
        """

    def get_import_query_scm(self) -> str:
        return """
        (import_statement
          source: (string) @import.source)
        """


class AnalysisStrategyFactory:
    _strategies: dict[str, type[AnalysisStrategy]] = {
        "python": PythonAnalysisStrategy,
        "javascript": JavaScriptAnalysisStrategy,
        "typescript": JavaScriptAnalysisStrategy,
        "java": JavaAnalysisStrategy,
        "go": GoAnalysisStrategy,
    }

    @classmethod
    def create(cls, language: str) -> AnalysisStrategy:
        strategy_cls = cls._strategies.get(language)
        if not strategy_cls:
            raise ValueError(f"No strategy for language: {language}")
        return strategy_cls()
```

## 관련 문서

- 상위: [[tree-sitter-ast/MOC]]
- 의존: [[tree-sitter-ast/parser-setup]], [[decisions/0006-tree-sitter-025]]
- 설계 원본: `plan/v5-design/phase2-infrastructure.md` §9.0, §9.2
