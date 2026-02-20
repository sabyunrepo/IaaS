---
title: "Infrastructure Layer"
type: moc
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[MOC]]"
---

# Infrastructure Layer

> 외부 서비스 어댑터 계층. Domain이 정의한 Port를 구현하는 Adapter들.
> Git, GitHub, Tree-sitter, LLM, Vector DB 등 외부 의존성을 캡슐화한다.

## 어댑터 목록

| 어댑터 | 역할 | 외부 서비스 |
|--------|------|------------|
| [[git-adapter/MOC\|Git Adapter]] | Git clone, blame, mailmap | git CLI |
| [[github-client/MOC\|GitHub Client]] | GraphQL/REST API | GitHub API v4/v3 |
| [[tree-sitter-ast/MOC\|Tree-sitter AST]] | 소스코드 파싱 + 구조 추출 | Tree-sitter 0.25 |
| [[complexity-analysis/MOC\|Complexity Analysis]] | 순환복잡도, Halstead, MI | Radon, Lizard |
| [[plagiarism-detection/MOC\|Plagiarism Detection]] | 코드 유사도 탐지 | Datasketch MinHash |
| [[llm-instructor/MOC\|LLM Instructor]] | 구조화 LLM 호출 | Instructor + Langfuse |
| [[vector-search/MOC\|Vector Search]] | 벡터 유사도 검색 | pgvector 0.8 |
| [[linkedin-adapter/MOC\|LinkedIn Adapter]] | LinkedIn 프로필 스크레이핑 | BrightData |
| [[voice-pipeline/MOC\|Voice Pipeline]] | 음성 입출력 파이프라인 | Silero VAD, Whisper, TTS |

## 문서 목록

```dataview
TABLE status, updated, tags
FROM "docs/architecture/infrastructure"
WHERE file.name != "MOC"
SORT file.name ASC
```

## 관련 ADR

```dataview
LIST
FROM "docs/architecture/decisions"
WHERE contains(impacts, this.file.link)
SORT date DESC
```
