---
title: "LLM Instructor"
type: moc
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[infrastructure/MOC]]"
tags: [instructor, pydantic, langfuse, llm, kimi]
---

# LLM Instructor

> Instructor + Pydantic + Langfuse 통합 계층.
> 모든 LLM 호출의 구조화 출력(Structured Output)을 보장하고,
> Langfuse로 프롬프트 버저닝 및 실행 추적을 수행한다.

## 역할

- OpenAI 호환 API(Kimi K2.5)에 Instructor 패턴 적용
- Pydantic v2 모델 기반 자동 타입 검증 + `max_retries=3` 자동 재시도
- Langfuse-first 아키텍처: 런타임 프롬프트를 Langfuse에서 풀링
- `@observe` 데코레이터로 모든 LLM 호출 자동 추적

## 문서 목록

| 문서 | 내용 |
|------|------|
| [[llm-instructor/instructor-setup\|Instructor Setup]] | `from_provider()` API, Kimi K2.5 연동 |
| [[llm-instructor/langfuse-integration\|Langfuse Integration]] | 추적, 프롬프트 버저닝, `@observe` |
| [[llm-instructor/prompt-management\|Prompt Management]] | YAML 프롬프트 관리, Langfuse-first 아키텍처 |

## 아키텍처 위치

```
infrastructure/llm/
├── instructor_client.py     # Instructor + Langfuse 통합 클라이언트
├── langfuse_client.py       # Langfuse 프롬프트 관리
└── models/                  # Pydantic 출력 모델
    ├── interview_question.py
    └── analysis_result.py
```

## 적용 Worker 목록

| Worker | LLM 용도 |
|--------|----------|
| W4 CLAVEWorker | 스타일로메트리 패턴 추출 |
| W9 SkillExtractorWorker | JD 기반 기술 스택 매핑 |
| W10 APIDepthAnalyzerWorker | API 활용 깊이 평가 |
| W11 ArchitectureEvaluatorWorker | SOLID/디자인 패턴 평가 |
| QuestionCrafter | 3전략 면접 질문 생성 |
| Enhancement Agents | 질문 개선 (난이도/접근성/검증력) |

## 관련 ADR

- [[decisions/0005-instructor-pydantic|ADR-0005: Instructor + Pydantic for Structured LLM Output]]

## 관련 문서

```dataview
TABLE status, updated, tags
FROM "docs/architecture/infrastructure/llm-instructor"
WHERE file.name != "MOC"
SORT file.name ASC
```
