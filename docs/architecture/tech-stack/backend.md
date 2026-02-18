---
title: "Backend Tech Stack"
type: component
layer: crosscutting
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[tech-stack/MOC]]"
depends-on: []
affects: []
linear: ""
tags: [backend, python, fastapi, langgraph, tech-stack]
---

# Backend Tech Stack

> Python 3.11 + FastAPI + LangGraph 1.0.8 기반 백엔드.
> DDD 4계층 (Interface, Application, Domain, Infrastructure).

## 핵심 의존성 (pyproject.toml)

| 영역 | 기술 | 버전 | 선정 근거 |
|------|------|------|----------|
| **Runtime** | Python | 3.11 | Pydantic v2 최적화 |
| **Web Framework** | FastAPI | 0.119+ | Pydantic v2 네이티브 |
| **Orchestration** | LangGraph | 1.0.8+ (GA) | StateGraph HMAS, Checkpointer |
| **Checkpointer** | langgraph-checkpoint-postgres | 3.0.4+ | PostgreSQL 재활용 |
| **Structured Output** | Instructor | 1.7.0+ | Pydantic v2, 자동 재시도 |
| **AST Parsing** | Tree-sitter | 0.24.7+ | 네이티브 바인딩 |
| **Python Complexity** | Radon | 6.0.1+ | CC/Halstead/MI |
| **Multi-lang Complexity** | Lizard | 1.17.10+ | CC + NLOC |
| **Quality Gate** | SonarQube | Community | On-Demand |
| **Plagiarism** | Datasketch | 1.6.5+ | MinHash/LSH |
| **Git History** | PyDriller | 2.9+ | 커밋 순회 |
| **DB** | psycopg | 3.2.0+ | PostgreSQL async |
| **Vector** | pgvector | 0.3.6+ | 벡터 검색 |
| **Cache** | Redis | 5.2.0+ (Python client) | LLM 캐시 |
| **LLM** | Kimi K2.5 | - | Langfuse-first |
| **Tracing** | Langfuse | 2.57.0+ | 프롬프트 관리 + 추적 |
| **GitHub** | gql + PyGithub | 3.5.0+ / 2.5.0+ | GraphQL + REST |
| **Similarity** | python-Levenshtein | 0.26.0+ | Identity Resolution |

## Tree-sitter 0.24.x 주의사항

> Breaking Change: 0.24.x부터 `.so` 빌드 방식 폐기, Python 네이티브 바인딩으로 전환.

```toml
# 0.24.x 통일 (혼용 금지)
"tree-sitter>=0.24.7",
"tree-sitter-python>=0.24.1",
"tree-sitter-javascript>=0.24.1",
"tree-sitter-typescript>=0.24.1",
"tree-sitter-java>=0.24.1",
"tree-sitter-go>=0.24.1",
```

## 폐기된 기술

| 기술 | 이유 |
|------|------|
| Temporal | LangGraph로 대체 (ADR-0001) |
| Alembic | Fresh init.sql (Clean Slate) |
| LangChain | Instructor로 대체 (ADR-0005) |
| 정규식 파서 | Instructor Structured Output |

## 관련 문서

- [[decisions/0001-langgraph-over-temporal]] -- LangGraph 선택
- [[decisions/0005-instructor-pydantic]] -- Instructor 선택
- [[decisions/0006-tree-sitter-025]] -- Tree-sitter 0.24.x
- [[tech-stack/version-matrix]] -- 전체 버전 매트릭스
