---
title: "ADR-0006: Tree-sitter 0.25 Migration"
type: adr
status: proposed
date: 2026-02-19
decision-makers: ["@sabyun"]
related-adrs: []
impacts: ["[[infrastructure/tree-sitter-ast/MOC]]"]
tags: [tree-sitter, ast, breaking-change]
---

# ADR-0006: Tree-sitter 0.25 Migration

## 상태

proposed

## 컨텍스트

`plan/v5-design/phase2-infrastructure.md` §9.0에서 확인된 내용:

Tree-sitter 0.24 기준으로 `phase2-infrastructure.md` 설계가 작성되었다.
0.24에서 이미 `.so` 파일 빌드 방식(`Language.build_library`)이 폐기되어
언어별 Python 패키지 바인딩(`tree_sitter_python`, `tree_sitter_javascript` 등)을
직접 사용하는 방식으로 전환이 완료되었다.

그러나 `docs/plans/2026-02-19-architecture-documentation-design.md` §6.1의
기술 스택 업데이트 내용에 따르면:

- v5 설계서에서 채택한 버전: `>=0.24.7`
- 최종 채택 결정: `>=0.25.2`
- 변경 사유: **`QueryCursor` API, ABI v15 Breaking Change**

0.25.x에서 `QueryCursor` API가 재설계되었다. 기존 0.24.x에서는
`Language.query()` → `Query.captures(node)` 직접 호출 방식이었으나,
0.25.x에서는 `Query` + `QueryCursor` 분리 패턴으로 변경되었다.

```python
# 0.24.x 구형 API
query = language.query(query_scm)
captures = query.captures(root_node)  # Query 객체에서 직접 호출

# 0.25.x 신형 API
from tree_sitter import Query, QueryCursor
query = Query(language, query_scm)
cursor = QueryCursor(query)
captures = cursor.captures(root_node)  # QueryCursor를 거쳐 호출
```

`infrastructure/analysis/tree_sitter_adapter.py`의 `extract_functions` 메서드 등
Query API를 사용하는 모든 코드가 마이그레이션 대상이 된다.

### 영향 범위

- `ASTAnalyzerWorker (W6)`: Tree-sitter 5개 언어 파싱 (Python, JS, TS, Java, Go)
- `CleanerWorker (W2)`: Tree-sitter 기반 diff 정제
- `SkillExtractorWorker (W9)`: import parser
- `ArchitectureEvaluatorWorker (W11)`: AST pattern detector

---

## 검토한 옵션

### 옵션 A: Tree-sitter 0.24.x에 유지

**설명**: 기존 설계서 기준인 `>=0.24.7`을 그대로 사용한다.

**장점**:
- `phase2-infrastructure.md`의 코드 예시를 수정 없이 사용 가능
- 마이그레이션 비용 없음

**단점**:
- ABI v15 미지원 — 향후 언어 문법 패키지들이 ABI v15 이상 요구 시 호환성 차단
- 0.25.x에서 추가된 QueryCursor 성능 최적화 미활용
- 장기적으로 어차피 마이그레이션이 불가피함 — 기술 부채 누적

---

### 옵션 B: Tree-sitter 0.25.x로 마이그레이션 (선택)

**설명**: `>=0.25.2`로 버전을 올리고, QueryCursor 신형 API로 전환한다.

**장점**:
- ABI v15 지원 — 언어 문법 패키지 최신 버전과 호환 보장
- QueryCursor 분리 패턴으로 더 명시적인 쿼리 실행 제어
- 향후 Tree-sitter 생태계 업데이트 따라가기 용이
- 0.24에서 이미 `.so` 빌드 방식 폐기를 처리한 상태이므로, 추가 마이그레이션 비용이 상대적으로 낮음

**단점**:
- `tree_sitter_adapter.py`의 `extract_functions` 및 Query 사용 코드 전체 수정 필요
- 신형 API에 맞게 테스트 케이스 업데이트 필요

---

## 결정

**옵션 B 채택: Tree-sitter 0.25.x로 마이그레이션**

v5.0은 Clean Slate 재건축이므로 레거시 코드 부담이 없다.
0.24.x 기반의 phase2 설계 코드 예시를 0.25.x API로 재작성하는 비용보다,
0.24.x를 고집해서 발생할 장기 호환성 문제가 더 크다.

ABI v15는 언어 문법 패키지들(`tree_sitter_python`, `tree_sitter_javascript` 등)이
앞으로 따라갈 표준이므로, 처음부터 0.25.x 기반으로 시작하는 것이 옳다.

---

## 결과

### 코드 변경 사항

`TreeSitterAdapter.extract_functions` 및 Query를 사용하는 모든 메서드를
0.25.x QueryCursor API로 재작성한다:

```python
# infrastructure/analysis/tree_sitter_adapter.py (0.25.x 기준)
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava

class TreeSitterAdapter:
    def __init__(self):
        self.languages = {
            "python": Language(tspython.language()),
            "javascript": Language(tsjs.language()),
            "typescript": Language(tsjs.language()),
            "go": Language(tsgo.language()),
            "java": Language(tsjava.language()),
        }

    def extract_functions(self, root_node, lang_name: str) -> list[dict]:
        """0.25.x QueryCursor API로 함수/클래스 추출"""
        query_scm = """
        (function_definition
          name: (identifier) @func.name)
        """
        query = Query(self.languages[lang_name], query_scm)
        cursor = QueryCursor(query)
        captures = cursor.captures(root_node)
        return [{"name": node.text.decode(), "node": node} for node in captures]
```

### 의존성 버전 고정

```toml
# pyproject.toml
tree-sitter = ">=0.25.2"
tree-sitter-python = ">=0.23.6"
tree-sitter-javascript = ">=0.23.1"
tree-sitter-go = ">=0.23.4"
tree-sitter-java = ">=0.23.5"
```

### 적용 대상 Linear 티켓

- JIT-94: Tree-sitter 어댑터 구현 시 0.25.x API 기준으로 작성
- JIT-95 이후 Tree-sitter를 사용하는 모든 Worker

### 참조

- `plan/v5-design/phase2-infrastructure.md` §9.0
- `docs/plans/2026-02-19-architecture-documentation-design.md` §6.1, §6.2
- `[[infrastructure/tree-sitter-ast/query-cursor-api]]`
