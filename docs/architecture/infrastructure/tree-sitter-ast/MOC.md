---
title: "Tree-sitter AST"
type: moc
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[infrastructure/MOC]]"
linear: [JIT-94]
---

# Tree-sitter AST

> 소스코드를 추상 구문 트리(AST)로 파싱하는 어댑터 계층.
> Python, JavaScript, TypeScript, Java, Go 5개 언어를 지원하며,
> ASTAnalyzerWorker(W6), CleanerWorker(W2), SkillExtractorWorker(W9), ArchitectureEvaluatorWorker(W11)에서 사용된다.

## 설계 결정

- Tree-sitter **0.25.x** 기준 (ADR-0006 참조)
- `.so` 빌드 방식(`Language.build_library`) 폐기 — 언어별 Python 패키지 바인딩 직접 사용
- `QueryCursor` 분리 패턴 (0.25.x Breaking Change 반영)
- `Parser`는 Thread-safe하지 않으므로 매 요청마다 새로 생성

## 문서 목록

| 문서 | 설명 |
|------|------|
| [[tree-sitter-ast/parser-setup\|parser-setup]] | 0.25.x 설정 코드, TreeSitterAdapter 클래스 |
| [[tree-sitter-ast/language-support\|language-support]] | 지원 언어 목록, Language 객체 생성 방법 |
| [[tree-sitter-ast/query-cursor-api\|query-cursor-api]] | QueryCursor 기반 캡처/매칭 코드 |

```dataview
TABLE status, updated, tags
FROM "docs/architecture/infrastructure/tree-sitter-ast"
WHERE file.name != "MOC"
SORT file.name ASC
```

## 관련 ADR

- [[decisions/0006-tree-sitter-025|ADR-0006: Tree-sitter 0.25 Migration]]

```dataview
LIST
FROM "docs/architecture/decisions"
WHERE contains(impacts, this.file.link)
SORT date DESC
```

## 사용 Worker

| Worker | 사용 목적 |
|--------|----------|
| W2 CleanerWorker | diff 정제 시 함수 경계 탐지 |
| W6 ASTAnalyzerWorker | 전체 레포 AST 분석, semantic diff 생성 |
| W9 SkillExtractorWorker | import 구문 파싱으로 기술 스택 추출 |
| W11 ArchitectureEvaluatorWorker | AST 패턴으로 아키텍처 평가 |
