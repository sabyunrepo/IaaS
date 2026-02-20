---
title: "ADR-0002: Clean Slate Not Migration"
type: adr
status: accepted
date: 2026-02-15
decision-makers: ["@sabyun"]
related-adrs: ["[[decisions/0001-langgraph-over-temporal]]", "[[decisions/0003-ddd-four-layers]]"]
impacts: ["[[jittda/]]"]
tags: [clean-slate, migration, architecture, reconstruction]
---

# ADR-0002: Clean Slate Not Migration

## 컨텍스트

v5.0 설계 초기에는 기존 `backend/` 디렉토리 위에서 Temporal을 제거하고 LangGraph로 교체하는 점진적 마이그레이션 방식이 검토되었다. 초기 설계서에는 "Phase 4: Temporal 제거"가 별도 단계로 존재하고, Alembic 마이그레이션 스크립트(`004_langgraph_migration.py`)로 DB를 전환하는 계획이 포함되어 있었다.

1차 설계 리뷰(`plan/review2.md`)에서 핵심 비판이 제기되었다: "기존 코드 위에서 작업하는 인상", "과거의 코드를 맹목적으로 가져오는 것은 기술 부채를 이자까지 쳐서 가져오는 것". 특히 Temporal 관련 코드(`workflows/`, `activities/`, `worker.py`)가 이미 코드베이스에 존재하는 상태에서 마이그레이션을 시도하면, 의존성 충돌과 불완전한 제거로 인한 기술 부채가 발생한다는 지적이었다.

소스: `plan/v5-design/phase0-scaffolding.md` §3, `jittda_doc/jittda-v5-brainstorming-log.md` §8

---

## 결정 옵션

### 옵션 A: 점진적 마이그레이션 (Strangler Fig)

기존 `backend/` 위에서 단계적으로 Temporal을 LangGraph로 교체.

**장점:**
- 기존 코드를 즉시 활용 가능
- 서비스 연속성 유지
- 각 단계별 롤백 가능

**단점:**
- Temporal 코드가 LangGraph 코드와 장기간 공존 → 혼재 상태
- "Phase 4: Temporal 제거" 단계가 별도로 필요 → 과도기 비용
- 기존 Alembic 히스토리를 유지하거나 복잡한 마이그레이션 스크립트 필요
- DDD 4계층 구조를 기존 코드 위에 덧씌우는 과정에서 경계가 불명확해짐
- 기존 코드의 설계 결함(LangGraph 노드에 비즈니스 로직 혼재)이 그대로 유입될 위험

### 옵션 B: Clean Slate — 완전 재건축 (선택)

`jittda/` 신규 디렉토리를 생성하여 처음부터 DDD 구조로 구축. 기존 코드는 참조(Read-only)로만 활용.

**장점:**
- Temporal 코드가 애초에 존재하지 않음 — "제거"할 것이 없음
- Fresh `init.sql` 하나로 DB 초기화 — Alembic revision 히스토리 불필요
- DDD 4계층 구조를 처음부터 올바르게 설계 가능
- 기술 부채 없이 시작
- 기존 레거시 코드의 설계 결함이 새 코드베이스에 유입되지 않음

**단점:**
- 기존 코드의 검증된 비즈니스 로직을 재작성해야 함 (예: `scoring_formulas.py` 899줄)
- 초기 셋업 시간 필요
- 기존 DB 데이터와의 연속성 단절

---

## 결정

**옵션 B: Clean Slate — 완전 재건축**

sabyun의 확정: "`jittda/`는 완전히 새로운 디렉토리에서 시작. Temporal 코드가 애초에 존재하지 않음(제거할 것이 없음)."

---

## 근거

1. **용어의 정확성**: "마이그레이션이 아닌 재건축". 마이그레이션은 기존 시스템을 유지하면서 전환하는 것이고, 재건축은 새로운 시스템을 처음부터 구축하는 것이다.
2. **기술 부채 제로화**: 기존 코드베이스의 결함(DDD 미적용, Temporal 의존성 혼재)을 이어받지 않음
3. **Temporal 인프라 완전 배제**: `temporalio` 패키지가 `pyproject.toml`에 처음부터 포함되지 않음 — "제거"라는 작업 자체가 불필요
4. **DB 단순화**: 기존 Alembic revision 히스토리 없이 `infra/postgres/init.sql` 단일 파일로 스키마 초기화
5. **레거시 자산의 현명한 활용**: 완전 폐기가 아닌 3분류 정책 적용

---

## 레거시 자산 분류 원칙

**"파일 복사-붙여넣기 금지, 로직 이식 허용"**

| 분류 | 대상 예시 | 처리 |
|------|----------|------|
| **[Asset]** 핵심 로직 | `scoring_formulas.py` (899줄 순수 비즈니스 로직) | 로직 이식, DDD/Pydantic 스타일로 재작성 |
| **[Reference]** 참조 대상 | `cached_llm.py` Redis 캐싱 패턴 | 아이디어만 참조, 코드는 완전 재작성 |
| **[Liability]** 폐기 대상 | `workflows/`, `activities/`, `worker.py` | 신규 코드베이스에 절대 포함 금지 |

폐기 대상 전체 목록:
- `workflows/`, `activities/`, `worker.py` — Temporal 관련, 존재 자체가 불필요
- `alembic/versions/*.py` — 레거시 DB 히스토리, Fresh init.sql로 대체
- SVG 차트 컴포넌트 — D3.js로 전면 교체
- 정규식 기반 파서 — Instructor(Structured Output)로 대체
- `core/temporal.py`, `core/temporal_interceptors.py` — Temporal 인프라
- `activity_logger.py` — Temporal 전용 로깅

---

## 결과

- `jittda/` 신규 디렉토리 생성 (기존 `backend/`와 독립)
- `jittda/backend/pyproject.toml`에 `temporalio` 패키지 미포함
- `jittda/infra/postgres/init.sql` 단일 파일로 전체 스키마 정의 (LangGraph Checkpoint 테이블 포함)
- 기존 `backend/` 디렉토리는 Read-only 참조 라이브러리로만 활용

---

## 관련 ADR

- ADR-0001: LangGraph 전환 결정 (Temporal 코드 폐기의 직접 원인)
- ADR-0003: DDD 4-Layer 구조 (Clean Slate에서 올바르게 적용 가능한 구조)
