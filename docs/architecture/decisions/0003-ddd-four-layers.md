---
title: "ADR-0003: DDD Four Layers"
type: adr
status: accepted
date: 2026-02-15
decision-makers: ["@sabyun"]
related-adrs: ["[[decisions/0002-clean-slate-not-migration]]", "[[decisions/0001-langgraph-over-temporal]]"]
impacts: ["[[jittda/backend/src/]]"]
tags: [ddd, architecture, layered-architecture, dependency-rule]
---

# ADR-0003: DDD Four Layers

## 컨텍스트

v5.0 초기 설계에서 LangGraph 노드에 비즈니스 로직이 혼재하는 문제가 발생했다. 1차 설계 리뷰(`plan/review1.md`)에서 "DDD 미적용"이 치명적 결함 4가지 중 하나로 지적되었다: "유지보수 어려움, 계층 분리 없음". 2차 리뷰(`plan/review2.md`)에서는 Interface Layer를 Application과 분리하고 의존성 규칙을 더 엄격히 적용하도록 추가 지적이 있었다.

코드 구조 패턴 선택이 필요했다. 후보는 기존 MVC 패턴 유지, Hexagonal Architecture, DDD 4-Layer였다.

소스: `plan/v5-design/phase0-scaffolding.md` §4, `jittda_doc/jittda-v5-brainstorming-log.md` §16

---

## 결정 옵션

### 옵션 A: MVC (Model-View-Controller)

FastAPI 기반의 일반적인 MVC 구조.

**장점:**
- 구조가 단순하여 빠른 초기 개발 가능
- 대부분의 개발자에게 친숙한 패턴

**단점:**
- Controller에 비즈니스 로직이 혼재되는 경향
- LangGraph 오케스트레이션 레이어의 위치가 불명확
- 외부 서비스(GitHub API, LLM)와 비즈니스 로직의 경계가 모호해짐
- 단위 테스트 시 외부 의존성 Mock 처리가 복잡

### 옵션 B: Hexagonal Architecture (Ports & Adapters)

포트와 어댑터 패턴으로 핵심 도메인을 외부에서 격리.

**장점:**
- 도메인 순수성 보장
- 어댑터 교체 용이

**단점:**
- Port 인터페이스 정의와 Adapter 구현이 분리되어 파일 수가 증가
- LangGraph Application Layer와 Domain Layer의 경계 정의가 추가로 필요
- v5.0의 HMAS 구조와 직접 매핑되지 않음

### 옵션 C: DDD 4-Layer (domain / application / infrastructure / interface) (선택)

Domain, Application, Infrastructure, Interface 4계층으로 엄격하게 분리. 단방향 의존성 규칙 적용.

**장점:**
- LangGraph StateGraph가 Application Layer에 자연스럽게 위치
- Domain Layer가 외부 의존성 제로 (순수 Python + Pydantic만)
- 인프라 어댑터 교체가 Domain에 영향을 주지 않음
- Worker별 단위 테스트에서 Domain 로직만 격리 테스트 가능
- 2차 리뷰 지적사항인 Interface Layer 분리가 명시적으로 구현됨

**단점:**
- 초기 구조 설계에 시간 필요
- 작은 기능도 4계층을 통과해야 하는 verbosity

---

## 결정

**옵션 C: DDD 4-Layer (domain / application / infrastructure / interface)**

---

## 의존성 규칙 (엄격 적용)

```
의존성 방향 (단방향만 허용):

  Interface -> Application -> Domain <- Infrastructure
                              ^
                              | (Domain은 외부를 모른다)
```

| 방향 | 허용 여부 |
|------|---------|
| `interface` → `application` | 허용 |
| `application` → `domain` | 허용 |
| `infrastructure` → `domain` (모델 리턴) | 허용 |
| `domain` → `infrastructure` | **절대 금지** |
| `domain` → `application` | 금지 |
| `infrastructure` → `application` | 금지 |

**핵심 규칙:**
- `domain/`은 어떤 외부 패키지도 import하지 않는다 (순수 Python + Pydantic만)
- LangGraph 노드는 Application Layer의 Thin Wrapper다 — 비즈니스 로직을 직접 작성하지 않고 domain + infrastructure 호출만 조합
- `infrastructure/`는 `domain/` 모델을 리턴하도록 구현

---

## 근거

1. **LangGraph 위치 명확화**: StateGraph, 노드 함수, 서브그래프는 Application Layer(`application/graphs/`, `application/nodes/`)에 위치 — 오케스트레이션 로직이 비즈니스 로직과 분리됨
2. **Domain 순수성**: `scoring_formulas.py`(899줄 순수 비즈니스 로직)와 같은 검증된 로직을 `domain/scoring/calculator.py`에 안전하게 이식 가능
3. **어댑터 교체 가능성**: GitHub GraphQL 클라이언트, LLM 모델(Kimi K2.5 → 다른 모델) 교체 시 `infrastructure/` 내부만 수정
4. **테스트 용이성**: Domain 단위 테스트에서 외부 서비스 Mock 불필요 — 순수 Python 함수로 테스트

---

## 디렉토리 구조

```
jittda/backend/src/
├── interface/         # [Layer 1] 외부 어댑터 (Web/HTTP)
│   ├── api/
│   │   ├── routes/    # jobs.py, auth.py, health.py
│   │   ├── middleware/
│   │   └── schemas/   # API 요청/응답 스키마
│   └── websocket/
│       └── stream_manager.py
│
├── application/       # [Layer 2] 오케스트레이션 + 유스케이스
│   ├── graphs/        # LangGraph StateGraph 정의
│   ├── nodes/         # LangGraph 노드 (Thin Wrapper)
│   ├── states/        # TypedDict State 정의
│   └── use_cases/
│
├── domain/            # [Layer 3] 순수 비즈니스 로직 (외부 의존성 0)
│   ├── identity/      # Identity Resolution
│   ├── scoring/       # 점수 산출 공식
│   ├── matching/      # JD 매칭, Funnel Selection
│   ├── question/      # 질문 생성 규칙
│   └── analysis/      # 분석 도메인 모델
│
└── infrastructure/    # [Layer 4] 외부 서비스 어댑터
    ├── git/           # blame_runner, clone_manager, mailmap_writer
    ├── github/        # graphql_client, rest_client
    ├── analysis/      # tree_sitter_adapter, radon, sonarqube
    ├── llm/           # instructor_client, langfuse
    ├── linkedin/      # brightdata_client
    ├── embedding/     # pgvector_store
    └── persistence/   # job_repository, analysis_repository
```

---

## 결과

- `jittda/backend/src/` 하위에 4계층 구조 설정 (JIT-82)
- LangGraph 노드는 domain + infrastructure 호출만 조합하는 Thin Wrapper로 구현
- `domain/` 내 파일은 `fastapi`, `langraph`, `httpx` 등 외부 패키지 import 금지 — 코드 리뷰에서 violation 즉시 수정

---

## 관련 ADR

- ADR-0002: Clean Slate (새 디렉토리에서 DDD를 처음부터 올바르게 설계)
- ADR-0001: LangGraph (Application Layer의 구체적 오케스트레이션 도구)
- ADR-0004: Reference Passing (Application Layer State 설계 방식)
