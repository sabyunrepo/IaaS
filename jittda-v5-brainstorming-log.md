# Jittda Sniper v5.0 — 브레인스토밍 & 설계 논의 기록

> **날짜:** 2026-02-15 (토)
> **세션:** 3개 연속 세션 (약 6시간)
> **참여:** sabyun (프로젝트 오너) + Claude (AI 아키텍트)
> **결과물:** 18개 섹션 종합 설계서 + 44개 Linear 티켓 + 7개 Phase 참조 문서

---

## 목차

1. [프로젝트 비전 & 초기 요구사항](#1-프로젝트-비전--초기-요구사항)
2. [비전 문서 분석 (souce1-6.md)](#2-비전-문서-분석-souce1-6md)
3. [명확화 질문 & 핵심 의사결정 (4라운드)](#3-명확화-질문--핵심-의사결정-4라운드)
4. [3가지 아키텍처 접근법 비교 & 확정](#4-3가지-아키텍처-접근법-비교--확정)
5. [초기 설계서 작성 (17개 섹션)](#5-초기-설계서-작성-17개-섹션)
6. [설계 리뷰 1차 — 치명적 결함 4가지](#6-설계-리뷰-1차--치명적-결함-4가지)
7. [설계 리뷰 반영 — 재설계 (Plan Mode)](#7-설계-리뷰-반영--재설계-plan-mode)
8. [설계 리뷰 2차 — "마이그레이션이 아닌 재건축"](#8-설계-리뷰-2차--마이그레이션이-아닌-재건축)
9. [최종 설계서 작성 (18개 섹션)](#9-최종-설계서-작성-18개-섹션)
10. [3계층 HMAS 에이전트 아키텍처](#10-3계층-hmas-에이전트-아키텍처)
11. [Identity Resolution Pipeline](#11-identity-resolution-pipeline)
12. [JD 기반 Funnel Selection](#12-jd-기반-funnel-selection)
13. [4대 핵심 지표 체계](#13-4대-핵심-지표-체계)
14. [정적 분석 도구 Full Toolchain](#14-정적-분석-도구-full-toolchain)
15. [질문 생성 엔진 — 3가지 전략](#15-질문-생성-엔진--3가지-전략)
16. [DDD 4계층 아키텍처](#16-ddd-4계층-아키텍처)
17. [Instructor + Pydantic 구조화 출력](#17-instructor--pydantic-구조화-출력)
18. [벡터 검색 (RAG) 전략](#18-벡터-검색-rag-전략)
19. [extra.md 아키텍처 최적화 반영](#19-extramd-아키텍처-최적화-반영)
20. [프론트엔드 시각화 전략 (D3.js)](#20-프론트엔드-시각화-전략-d3js)
21. [레거시 자산 선별 가이드](#21-레거시-자산-선별-가이드)
22. [인프라 구성 (Docker + Cloudflare Tunnel)](#22-인프라-구성-docker--cloudflare-tunnel)
23. [Linear 프로젝트 & 44개 티켓 생성](#23-linear-프로젝트--44개-티켓-생성)
24. [마스터 CLAUDE.md 업데이트](#24-마스터-claudemd-업데이트)
25. [최종 산출물 & 생성 파일 목록](#25-최종-산출물--생성-파일-목록)

---

## 1. 프로젝트 비전 & 초기 요구사항

> **sabyun**: plan 폴더의 souce 마크다운 파일들 읽어보고 현재 프로젝트를 전면 개선할거야, 병렬로 최대한 속도도 빠르게 하고 플랜도 각각의 상황에 플랜 에이전트가 에이전트 로직을 생성하면 해당 방식대로 에이전트들이 움직일수 있도록(현재를 플랜만 세우지 실제로는 랭체인 형식으로 진행되는것같은데) 랭그래프와 도구를 사용해서 에이전트 효율을 높이고 인풋 컨텍스트를 최대한 줄이고 벡터 검색을 통해 유의미한 정보만을 골라서 아웃풋을 낼수있도록, 인풋 아웃풋이 다음 에이전트에 넘어갈때 연결성이 제대로 확보되도록, 실질적으로 에이전트 로직이 유기적으로 동적으로 피드백을 주고 받으면서 작동할수 있도록 결과물도 최선의 유의미한 결과물이 나올수 있도록 프롬프트도 구체적 및 퓨샷 적용으로 작성하고. 디자인 패턴을 사용해서 하드코딩 되지 않도록 설계를 진행하고.

### sabyun이 명시한 핵심 요구사항

| # | 요구사항 | 상세 |
|---|---------|------|
| 1 | LangGraph 전환 | Temporal → LangGraph로 실질적 에이전트 로직 구현 |
| 2 | 벡터 검색 통합 | 인풋 컨텍스트 최소화, 유의미한 정보만 선별 |
| 3 | 에이전트 연결성 | 인풋↔아웃풋 간 연결성 확보, 동적 피드백 |
| 4 | 디자인 패턴 | 하드코딩 금지, 패턴 기반 추상화 |
| 5 | 프롬프트 엔지니어링 | 구체적 + 퓨샷 적용 |
| 6 | 구조화 출력 | Instructor/Pydantic 기반 Tool Calling |
| 7 | 정적 분석 도구 | SDK 활용, 정적 분석 프로그램 통합 |
| 8 | 단계별 계획 | 인프라 수정 → 최종 플랜 → Linear 티켓 |

---

## 2. 비전 문서 분석 (souce1-6.md)

브레인스토밍 시작 시 `plan/` 폴더의 6개 비전 문서를 병렬 탐색하여 프로젝트 컨텍스트를 파악했다.

### souce1.md — 기술 아키텍처 초안

- **3개 전문 에이전트 병렬 구조**: Collector Agent + Forensic Agent + Metric Agent
- **기술 스택**: GraphQL, PyDriller, Tree-sitter, Radon/Lizard, SonarQube, Datasketch, LangGraph
- **핵심 원칙**: Noise-Free, Semantic Analysis, Parallel Execution
- **가중 합산 모델(WSM)**: 논리력(30%) + 전문성(30%) + 안정성(20%) + 진정성(20%)

### souce4.md — HMAS 3계층 아키텍처 (핵심)

- **Level 1 — Meta-Agent**: 전략/총괄, 레포 우선순위, 최종 리포트 합성
- **Level 2 — 3 Supervisor**: Forensic(진위) / Logic(품질) / Stack(숙련도)
- **Level 3 — Worker Agents**: Collector, Cleaner, Metric, Pattern, Vibector 등
- **설계 철학**: "확률적 AI(LLM) + 결정론적 알고리즘(Static Analysis) 하이브리드"
- **상태 기반 제어**: LangGraph StateGraph + Checkpointer

### souce5.md — 질문 생성 엔진 & UI/UX

- **3가지 질문 생성 전략**:
  - 전략 A: Negative Selection — "안 한 이유" 묻기
  - 전략 B: Intentional Complexity — "높은 난이도의 의도" 묻기
  - 전략 C: Evolution — "코드의 변화 과정" 묻기
- **현실적 면접 시나리오**: 회피형 답변 패턴 + 압박 파생 질문
- **대시보드 UI/UX**: 3초 요약 카드 → 레이더 차트 → 드릴다운 트리맵 → Interview Mode

### souce2,3,6 — 보완 문서

- souce2: 코드 수집 전략 상세 (GraphQL 쿼리 최적화, 레이트 리밋)
- souce3: 포렌식 분석 상세 (git blame 옵션, Vibector AI 탐지, SCAA 스타일로메트리)
- souce6: 데이터 수집 전략 + 리스크 분석

### 현재 vs 비전 갭 분석

| 영역 | 현재 (Temporal Pipeline v4.0) | 비전 (souce1-6) |
|------|------------------------------|-----------------|
| 오케스트레이션 | Temporal.io 고정 4-Phase | HMAS 3계층 (Meta→Supervisor→Worker) |
| 에이전트 패턴 | 이름만 Agent, 실제는 단일 LLM 호출 | LangGraph StateGraph 동적 라우팅 |
| 데이터 전달 | plain dict, 암묵적 키 합의 | 타입 안전 State |
| 분석 도구 | PyGithub + PyDriller + Kimi LLM | + AST(Tree-sitter) + Radon/Lizard + SonarQube |
| 벡터/RAG | pgvector 부분 사용 (KG 구축용) | 전면 RAG 기반 컨텍스트 검색 |
| 질문 생성 | 4소스 순차 수집 + LLM | Negative Selection/Intentional Complexity/Evolution 3전략 |
| 프론트엔드 | Vite + React 19 | D3.js 레이더차트 + 드릴다운 트리맵 |

---

## 3. 명확화 질문 & 핵심 의사결정 (4라운드)

비전 문서 분석 후 4가지 핵심 결정을 순차적으로 확정했다.

### Q1. Temporal vs LangGraph 관계

| 선택지 | 설명 |
|--------|------|
| A. 공존 (Temporal 유지 + LangGraph 추가) | 기존 Temporal 위에 LangGraph 레이어 |
| **B. LangGraph 전면 교체 (선택)** | **Temporal 완전 제거, LangGraph만으로 전체 파이프라인** |
| C. LangGraph 점진적 대체 | 단계별 이관 |

> **sabyun 결정**: LangGraph 전면 교체 — Temporal의 durability, retry, observability를 LangGraph에서 재구현하는 가장 도전적인 경로.

### Q2. 구조화 출력 라이브러리

| 라이브러리 | 방식 | 적합 상황 |
|-----------|------|----------|
| **Instructor (선택)** | **Pydantic 기반 Tool Calling** | **상용 API 사용 시** |
| Outlines | FSM 제어 | 로컬 모델 최적화 시 |
| Marvin | 객체 지향적 추상화 | 간단한 데이터 추출 시 |

### Q3. 정적 분석 범위

| 선택지 | 도구 |
|--------|------|
| **Full Stack (선택)** | **Tree-sitter + Radon/Lizard + SonarQube + Datasketch + Vibector + CLAVE** |
| Minimal | Tree-sitter + Radon만 |
| SonarQube Only | SonarQube에 위임 |

> **sabyun**: "정적분석도 더 있어야하는거 아냐?" → cloc + pydeps/dependency-cruiser 추가 권장

### Q4. 마이그레이션 전략

| 선택지 | 설명 |
|--------|------|
| **Big Bang (선택)** | **일괄 전환** |
| Strangler Fig | 점진적 교체 |
| Parallel Run | 양쪽 동시 운영 후 전환 |

---

## 4. 3가지 아키텍처 접근법 비교 & 확정

### 접근법 A: Pure LangGraph HMAS (추천 → 확정)

전체를 LangGraph StateGraph로 구현. 3계층 서브그래프 중첩.

```
MetaGraph
├── ForensicSupervisor (수집/정제/진정성)
│   └── Collector, Cleaner, Vibector, CLAVE Workers
├── LogicSupervisor (복잡도/품질)
│   └── ASTAnalyzer, ComplexityMeter, QualityScanner, PatternDetector Workers
└── StackSupervisor (전문성/스택)
    └── SkillExtractor, APIDepthAnalyzer, ArchitectureEvaluator Workers
```

| 장점 | 단점 |
|------|------|
| plan 문서 비전과 직접 매핑 | LangGraph 서브그래프 디버깅 복잡 |
| 의존성 최소 (LangGraph만) | Temporal durability를 Checkpointer로 재구현 |
| 동적 라우팅/피드백 루프 자유 | 분산 실행 시 LangGraph Cloud 필요 가능 |
| Checkpointer로 상태 지속성 확보 | 새 기술 학습 곡선 |

### 접근법 B: LangGraph + Celery Workers (미채택)

- 장점: 중량 작업 수평 스케일링, Redis 이미 보유
- 단점: 2개 시스템 관리, LangGraph 장점 반감

### 접근법 C: LangGraph + CrewAI (미채택)

- 장점: 에이전트 정의 직관적, 빠른 프로토타이핑
- 단점: CrewAI 추상화가 LangGraph와 중복, 커스터마이징 한계

### 접근법 A 확정 근거

1. **단일 프레임워크**로 전체 파이프라인 통제 — 디버깅 포인트 최소화
2. plan 문서의 HMAS 비전을 **서브그래프 중첩**으로 자연스럽게 구현
3. PostgreSQL Checkpointer로 Temporal 수준의 **durability** 확보
4. Instructor + Pydantic State로 **타입 안전한 에이전트 간 통신**
5. Tool-calling 패턴으로 정적 분석 도구들을 **동적으로 선택/실행**

---

## 5. 초기 설계서 작성 (17개 섹션)

접근법 A 확정 후 `plan/2026-02-15-langgraph-hmas-migration-design.md`에 17개 섹션 종합 설계서를 작성했다.

### 핵심 아키텍처 결정

1. **3계층 HMAS**: MetaAgent → 3 Supervisors (Forensic/Logic/Stack) → 11 Workers
2. **병렬 실행**: Forensic + Logic 병렬 → Stack은 Logic AST 결과 의존 → Fan-in
3. **11개 Worker 도구 매핑**: PyGithub, PyDriller, Tree-sitter, Radon/Lizard, SonarQube, Datasketch, Vibector, CLAVE
4. **4대 지표**: 논리력(30%) + 전문성(30%) + 안정성(20%) + 진정성(20%)
5. **Instructor + Pydantic**: LLM 출력 자동 검증/재시도
6. **벡터 검색 RAG**: 질문 생성 시 LLM 입력 90% 축소
7. **6 Phase 마이그레이션**: 인프라 → Worker → Graph → 질문 → 프론트 → 테스트
8. **25개 Linear 티켓** 예정

---

## 6. 설계 리뷰 1차 — 치명적 결함 4가지

> **sabyun**: plan/review1.md 리뷰 반영해줘

review1.md는 시스템 아키텍트 관점의 비판적 리뷰로, 초기 설계의 **4가지 치명적 결함**을 지적했다.

### 총평

> "화려한 오케스트레이션(LangGraph)에 집중하느라, 정작 분석할 데이터의 '순도(Purity)'와 '적합성(Relevance)'을 놓쳤습니다."

### 결함 1: Identity Resolution 부재

- **문제**: 단순 `git clone` 후 전체 분석 — 지원자 식별 로직 없음
- **비판**: 여러 이메일/닉네임/컴퓨터에서 커밋한 경우를 전혀 미고려
- **해결**: GitHub Node ID 기반 추적 + 동적 `.mailmap` 생성 + 3단계 포렌식 쿼리 도입

### 결함 2: JD 기반 적합성 선별 부재

- **문제**: 모든 레포지토리를 분석 — 백엔드 지원자의 React 토이 프로젝트까지 심층 분석
- **비판**: 토큰/시간 낭비, "질문은 JD 기반이어야 한다" 요구사항 미충족
- **해결**: Funnel Selection Architecture 도입 (Metadata Filter → Vector Relevance → 기여도 임계치)

### 결함 3: DDD 미적용

- **문제**: LangGraph 노드에 비즈니스 로직 혼재
- **비판**: 유지보수 어려움, 계층 분리 없음
- **해결**: Domain/Application/Infrastructure 엄격 분리, `domain`은 `infrastructure`를 절대 import 금지

### 결함 4: 기존 코드 맹목적 포팅

- **비판**: "과거의 코드를 맹목적으로 가져오는 것은 기술 부채를 이자까지 쳐서 가져오는 것"
- **해결**: 전수 조사(Audit) 후 통합/폐기 결정

---

## 7. 설계 리뷰 반영 — 재설계 (Plan Mode)

review1.md 반영을 위해 Plan Mode로 전환하여 기존 코드베이스를 심층 탐색했다.

### 3개 병렬 탐색 에이전트

1. **Identity Resolution 분석**: 기존 8단계 휴리스틱(AuthorMatch 모델) 발견. git blame -w -M -C, mailmap, AST 프루닝 누락 확인
2. **DDD 감사**: 60% 재사용 가능(scoring_formulas 899줄 순수 로직), 30% 재설계 필요(Activity → Service), 10% 폐기(Temporal 전용 코드)
3. **JD 선별/벡터 검색 분석**: 정규식 기반 tech 추출(15개 언어만), 메타데이터 스코어링(lang 30% + size 30% + keyword 40%), LLM tech_stack 미활용, JD-repo 벡터 매칭 부재

### 핵심 발견

| 기존 코드 | 판정 | 근거 |
|-----------|------|------|
| `scoring_formulas.py` (899줄) | 100% 이전 | 순수 비즈니스 로직, 외부 의존성 없음 |
| `github_service.py` (1094줄) | 분리 후 재작성 | domain/identity + infrastructure/github로 분할 |
| `code_analyzer.py` (681줄) | 재설계 | infrastructure/analysis 어댑터 + LangGraph 노드 |
| `cached_llm.py` (772줄) | 아이디어 참조 | Redis 캐싱 아이디어만 차용, 구현은 재작성 |
| `vector_store.py` (227줄) | 확장 | `compute_jd_repo_similarity()` 추가 |
| 16개 Activity 파일 | 전면 변환 | `@activity.defn` → LangGraph 노드 함수 |
| Temporal 워크플로우 | 폐기 | LangGraph로 완전 대체 |

---

## 8. 설계 리뷰 2차 — "마이그레이션이 아닌 재건축"

> **sabyun**: plan/review2.md 리뷰 반영해서 최종 설계계획 전체적으로 작성해서 md 파일로 작성해줘

review2.md의 핵심 비판: **용어와 접근법 수정 필요**

### 핵심 변경점

| 지적 | 수정 |
|------|------|
| Phase 4 "Temporal 제거" 존재 | **Phase 4 삭제** — 처음부터 미설치 |
| `004_langgraph_migration.py` Alembic 스크립트 | **Fresh init.sql** 하나로 초기화 |
| 기존 코드 위에서 작업하는 인상 | **`jittda/` 완전히 새로운 디렉토리** |
| infrastructure → domain 침범 우려 | **의존성 규칙 엄격화**, Interface Layer 명시 분리 |
| Makefile 구체성 부족 | **make up/down/logs/shell/test/clean/infra-clean** 표준화 |
| Cloudflare Tunnel 미비 | **docker-compose에 cloudflared 서비스 고정** |

### Clean Slate 원칙 확정

1. `jittda/`는 **완전히 새로운 디렉토리**에서 시작
2. Temporal 코드가 **애초에 존재하지 않음** (제거할 것이 없음)
3. DB는 **Fresh init.sql** 하나로 초기화 (Alembic revision 히스토리 금지)
4. 기존 Vantict 코드는 **참조용 라이브러리(Read-only)**로만 취급
5. **"파일 복사-붙여넣기 금지, 로직 이식 허용"**

---

## 9. 최종 설계서 작성 (18개 섹션)

review1 + review2 모든 지적사항을 반영하여 `plan/2026-02-15-v5-final-design.md`에 18개 섹션 종합 설계서를 작성했다.

### 18개 섹션 구성

| § | 섹션 | 내용 |
|---|------|------|
| 1 | Executive Summary | 핵심 변경점 테이블 (AS-IS → TO-BE) |
| 2 | 설계 철학 및 핵심 원칙 | 8개 원칙 (Noise-Free, Semantic, Identity-First 등) |
| 3 | Clean Slate 접근 전략 | 레거시 자산 선별 가이드 |
| 4 | DDD 아키텍처 및 디렉토리 구조 | 4계층 + 의존성 규칙 |
| 5 | 기술 스택 선정 | 최신 버전 포함 전체 스택 |
| 6 | 3계층 HMAS 아키텍처 | MetaAgent → Supervisor → Worker |
| 7 | Identity Resolution Pipeline | GitHub Node ID + mailmap + 3단계 포렌식 |
| 8 | JD 기반 Funnel Selection | 3단계 필터 (Hard → Relevance → Vector) |
| 9 | Worker Agent 상세 설계 | 11개 Worker 개별 사양 |
| 10 | LangGraph 그래프 설계 | MetaState + 서브그래프 + Fan-out/Fan-in |
| 11 | 4대 핵심 지표 체계 | 가중 합산 모델 상세 |
| 12 | Pydantic 모델 + Instructor 통합 | 구조화 출력 + 자동 검증 |
| 13 | 벡터 검색 (RAG) 전략 | pgvector + AST 경계 청크 분할 |
| 14 | 프롬프트 엔지니어링 | Langfuse-first + YAML fallback |
| 15 | 인프라 구성 | Docker Compose + Cloudflare Tunnel + init.sql |
| 16 | 프론트엔드 설계 | 7개 D3.js 차트 + 5개 탭 |
| 17 | 테스트 전략 | Domain 단위 → 통합 → E2E |
| 18 | Phase별 구현 로드맵 | 6 Phase, 42일, 42개 티켓 |

### review 반영 확인

| review1 지적 | 반영 섹션 |
|-------------|----------|
| Identity Resolution Pipeline | §7 |
| JD 기반 Funnel Selection | §8 |
| DDD + Clean Infrastructure | §4 |
| Cloudflare Tunnel | §15 |
| AI Code Heatmap | §16 |
| D3.js + WebSocket 스트리밍 | §16 |

| review2 지적 | 반영 섹션 |
|-------------|----------|
| Clean Slate — `jittda/` 신규 | §3 |
| "Temporal 제거" Phase 삭제 | §18 |
| Fresh init.sql | §15 |
| DDD 의존성 엄격화 | §4 |
| Interface Layer 분리 | §4 |
| Makefile 표준화 | §15 |

---

## 10. 3계층 HMAS 에이전트 아키텍처

브레인스토밍에서 가장 깊이 논의된 핵심 아키텍처.

### 계층 구조

```
Level 1: MetaAgent (전략/총괄)
├── 사용자 요청 접수 (GitHub URL + JD)
├── Funnel Selection으로 분석 대상 결정
├── Supervisor 작업 할당
└── 최종 리포트 합성 (Synthesis)

Level 2: 3 Supervisors (영역별 관리)
├── ForensicSupervisor (진위/포렌식)
│   └── 순수 기여 추출, AI 탐지, 표절 검사
├── LogicSupervisor (코드 품질)
│   └── AST 분석, 복잡도, 품질, 패턴 탐지
└── StackSupervisor (기술 숙련도)
    └── 스킬 추출, API 깊이, 아키텍처 평가

Level 3: 11 Worker Agents (실행/측정)
├── W1 CollectorWorker — GitHub GraphQL 데이터 수집
├── W2 CleanerWorker — git-filter-repo 노이즈 제거
├── W3 VibectorWorker — AI 코드 탐지 (WPM 분석)
├── W4 CLAVEWorker — 스타일로메트리 (코드 지문)
├── W5 PlagiarismWorker — Datasketch MinHash/LSH
├── W6 ASTAnalyzerWorker — Tree-sitter AST 파싱
├── W7 ComplexityMeterWorker — Radon/Lizard 복잡도
├── W8 QualityScannerWorker — SonarQube 정적 분석
├── W9 SkillExtractorWorker — 기술 스택 프로파일링
├── W10 APIDepthAnalyzerWorker — API 호출 깊이
└── W11 ArchitectureEvaluatorWorker — 디자인 패턴/SOLID
```

### 실행 흐름 (Fan-out/Fan-in)

```
MetaAgent
    │
    ├── ForensicSupervisor ──┐
    │   (W1→W2→W3,W4,W5)    │  ← 병렬 실행
    │                        │
    ├── LogicSupervisor ─────┤
    │   (W6→W7,W8)           │
    │                        │
    └── StackSupervisor ─────┘  ← LogicSupervisor AST 결과 의존
        (W9,W10,W11)
            │
            ▼
        Fan-in → MetaAgent Synthesis
```

### BaseWorker Template Method

```python
class BaseWorker(ABC):
    @abstractmethod
    async def collect(self, state) -> dict: ...
    @abstractmethod
    async def analyze(self, data) -> dict: ...
    @abstractmethod
    async def validate(self, result) -> bool: ...

    async def execute(self, state):
        data = await self.collect(state)
        result = await self.analyze(data)
        if not await self.validate(result):
            return await self.retry(state)
        return result
```

### 핵심 설계 논의

- **Temporal durability 대체**: PostgreSQL `AsyncPostgresSaver.from_conn_string()` Checkpointer로 상태 지속성 확보
- **Temporal heartbeat 대체**: LangGraph `graph.astream()` + WebSocket 브로드캐스팅
- **Temporal Worker 대체**: LangGraph가 FastAPI 내 백그라운드 태스크로 실행, 별도 Worker 프로세스 불필요
- **StackSupervisor 의존성**: LogicSupervisor의 AST 결과(Tree-sitter 파싱 데이터)에 의존하므로 완전 병렬 불가 → Forensic + Logic 병렬 실행 후 Stack 순차 실행

---

## 11. Identity Resolution Pipeline

review1에서 가장 강하게 비판된 부분. 기존 설계에 완전히 누락되어 있었다.

### 3단계 파이프라인

```
Stage 1: GitHub Node ID 기반 추적
  ├── GraphQL databaseId 조회 (이메일 변경 무관)
  └── GitHub API fallback (REST)

Stage 2: 동적 .mailmap 생성
  ├── 커밋 히스토리에서 이름/이메일 추출
  ├── Levenshtein Distance 유사도 분석
  └── 동일인 추정 → 클러스터링 → .mailmap 파일 생성

Stage 3: 3단계 포렌식 Blame
  ├── Level 1 (Git Internal): git blame -w -M -C -C --line-porcelain
  │   └── -w: 공백 무시, -M: 파일 이동 추적, -C -C: 코드 복사 식별
  ├── Level 2 (Semantic Pruning): Tree-sitter AST 파싱
  │   └── import, 주석, Config, 자동생성 코드 제거 → 함수/클래스 본문만
  └── Level 3 (Pure Contribution): 순수 기여분 산출
      └── 총 LoC - AI코드 - 복사코드 = 순수 기여
```

### 기존 코드 → 재설계 매핑

| 기존 (github_service.py) | 재설계 |
|--------------------------|--------|
| `resolve_author_by_identity()` 8단계 휴리스틱 | `domain/identity/resolver.py` 확장 |
| AuthorMatch 우선순위 (0.5~1.0) | Levenshtein 클러스터링 추가 |
| `verify_cross_repo()` | 유지 + mailmap 통합 |
| 단순 git clone | 3단계 포렌식 Blame으로 교체 |

---

## 12. JD 기반 Funnel Selection

review1에서 두 번째로 비판된 부분. "모든 레포 분석은 토큰 낭비."

### 3단계 퍼널

```
입력: 지원자 GitHub URL + JD 텍스트
         │
Stage 1: Hard Filter (메타데이터)
    ├── isFork: false
    ├── 최근 업데이트: 6개월 이내
    ├── 최소 사이즈 (비어있지 않은 레포)
    └── 결과: N개 → 약 50~70% 제거
         │
Stage 2: LLM Relevance Scoring
    ├── JD tech_stack과 레포 언어/README 매칭
    ├── LLM이 0-100 관련도 점수 부여
    └── 결과: 상위 10~15개
         │
Stage 3: Vector Similarity
    ├── JD 요구사항 텍스트 임베딩
    ├── 레포 README/Description 임베딩
    ├── Cosine Similarity 계산
    └── 결과: 상위 3~5개 (심층 분석 대상)
```

### 기존 코드와의 차이

- **기존**: 정규식 기반 tech 추출(15개 언어만), 메타데이터 스코어링(lang 30% + size 30% + keyword 40%)
- **신규**: LLM tech_stack 활용 + 벡터 유사도 + 기여도 임계치(조직 레포 10% 이상)

---

## 13. 4대 핵심 지표 체계

souce1, souce4에서 제안되고 브레인스토밍에서 확정된 가중 합산 모델.

### 가중 합산 모델 (WSM)

```
최종 점수 = Logic(30%) + Mastery(30%) + Stability(20%) + Authenticity(20%)
```

| 지표 | 가중치 | 측정 방식 | 도구 |
|------|--------|----------|------|
| **논리력 (Logic)** | 30% | CC(순환복잡도), Halstead($D$, $V$, $E$), Cognitive Complexity | Radon, Lizard |
| **전문성 (Mastery)** | 30% | API 호출 깊이(Level 1~3), 디자인 패턴 사용, SOLID 준수 | Tree-sitter AST |
| **안정성 (Stability)** | 20% | 기술 부채 비율, Code Smells/LoC, Rework Rate, Code Churn | SonarQube |
| **진정성 (Authenticity)** | 20% | 순수 기여 비율, WPM(AI 탐지), 스타일로메트리, 표절도 | Vibector, CLAVE, Datasketch |

### 수치화 공식

```
논리력: Score_logic = 1 / (1 + α·M_avg + β·D_avg) × 100
전문성: Score_mastery = Σ(Count_API × Weight_Level)
안정성: Score_stability = 1 - (CodeSmells/LoC) - (ChurnRate × penalty)
진정성: Index_real = (LoC_total - LoC_AI - LoC_Copy) / LoC_total × 100
```

---

## 14. 정적 분석 도구 Full Toolchain

sabyun이 상세한 도구 목록을 직접 제시하고, 추가 필요 여부를 질문.

### 확정된 분석 도구 매핑

| 영역 | 도구 | 용도 |
|------|------|------|
| **구문 분석** | Tree-sitter 0.24+ | AST 파싱, Semantic Diff, 코드 구조 분석 |
| **복잡도** | Radon (Python) | McCabe CC, Halstead, Maintainability Index |
| **복잡도** | Lizard | 다국어 CC (C, C++, Java, JS 등) |
| **품질** | SonarQube API | 기술 부채, Code Smells, 보안 취약점 |
| **보안** | Bandit | Python 보안 분석 |
| **중복/표절** | Datasketch (MinHash/LSH) | FOSS 대비 유사도 분석 |
| **AI 탐지** | Vibector | WPM 분석 (인간 한계 40-80 WPM 초과 감시) |
| **스타일로메트리** | CLAVE (SCAA 기반) | 코드 지문 분석, 대리 코딩 탐지 |
| **Git 포렌식** | PyDriller | 커밋 순회, 저자 식별, Diff 추출 |
| **노이즈 제거** | git-filter-repo | 바이너리, node_modules 등 제거 |
| **통계** | cloc | 정확한 LOC/언어 통계 (SonarQube 보완) |
| **의존성** | pydeps/dependency-cruiser | 의존성 그래프 (아키텍처 패턴 평가) |

> **SonarQube가 커버하는 것**: 코드 중복(CPD), 린트, 인지적 복잡도, 기술 부채. **추가 권장**: cloc + pydeps (경량 보완).

---

## 15. 질문 생성 엔진 — 3가지 전략

souce5.md에서 깊이 논의된 핵심 차별화 기능.

### 전략 A: "안 한 이유 (Negative Selection)" 묻기

- **로직**: AST 분석 결과, 사용될 법한 패턴이 의도적으로 사용되지 않은 구간 감지
- **예시**: "대량 연산인데 async/await를 적용하지 않으셨는데, 동시성 이슈를 우려하셨나요?"
- **합격 기준**: 트레이드오프 이해 ("데이터 순서가 중요해서 안정성을 택했습니다")
- **불합격 징후**: "그냥 짜다보니 그렇게 됐습니다" 또는 "AI가 그렇게 짜줬습니다"

### 전략 B: "높은 난이도의 의도 (Intentional Complexity)" 묻기

- **로직**: Halstead $D$와 CC가 국소적으로 매우 높은 구간 식별
- **예시**: "validateToken의 순환 복잡도가 매우 높습니다. 하나의 함수에 유지한 아키텍처적 이유는?"
- **합격 기준**: "보안 감사를 위해 응집도를 높였습니다" (메타 인지)
- **불합격 징후**: "복잡한 줄 몰랐습니다"

### 전략 C: "코드의 변화 과정 (Evolution)" 묻기

- **로직**: Git 히스토리에서 Code Churn이 높거나 구조 대거 변경된 지점 추적
- **예시**: "PaymentGateway가 3번이나 구조가 바뀌었는데, 초기 설계에서 예상 못한 문제는?"
- **핵심**: 해당 코드를 직접 고민하며 수정해본 사람만 답할 수 있음. AI는 최종 결과물만 알지 수정의 역사는 모름.

### 현실적 면접 시나리오 — 회피형 답변 대응

| 패턴 | 회피형 답변 예시 | 파생 질문 |
|------|----------------|----------|
| 스파게티 코드 | "비즈니스 로직이 복잡해서... 확장성을 고려해서..." | "결제 수단 추가 시 기존 코드 수정 필요한가요? (OCP 확인)" |
| AI/복붙 의심 | "Best Practice를 따르기 위해 습관적으로 적용..." | "useCallback의 메모리 비용 대비 이득 근거는?" |
| 테스트 부재 | "속도가 생명이라(MVP) 수동 테스트했습니다..." | "배포 후 버그 시 디버깅 시간이 더 들지 않나요?" |

---

## 16. DDD 4계층 아키텍처

review1, review2에서 반복 강조된 아키텍처 원칙.

### 4계층 구조 및 의존성 규칙

```
Interface Layer (Web/HTTP 어댑터)
    │ 호출
    ▼
Application Layer (LangGraph 흐름 제어, 유스케이스)
    │ 호출
    ▼
Domain Layer (순수 비즈니스 로직 — 외부 의존성 ZERO)
    ▲ 구현
    │
Infrastructure Layer (GitHub API, Git CLI, LLM Client 등)
```

### 의존성 규칙 (엄격)

- ✅ `application` → `domain` (호출)
- ✅ `infrastructure` → `domain` (모델 리턴)
- ✅ `interface` → `application` (호출)
- 🚫 `domain` → `infrastructure` (**절대 금지**)
- 🚫 `domain` → `application` (**금지**)
- 🚫 `infrastructure` → `application` (**금지**)

### 디렉토리 구조

```
jittda/
├── backend/src/
│   ├── domain/           # 순수 비즈니스 로직
│   │   ├── identity/     # Identity Resolution
│   │   ├── scoring/      # 점수 산출 공식
│   │   ├── matching/     # JD 매칭, Funnel Selection
│   │   └── models/       # 도메인 모델
│   ├── application/      # LangGraph 오케스트레이션
│   │   ├── graphs/       # MetaGraph, Supervisor, Worker
│   │   ├── nodes/        # LangGraph 노드 함수
│   │   └── services/     # 유스케이스
│   ├── infrastructure/   # 외부 서비스 어댑터
│   │   ├── github/       # GraphQL, REST 클라이언트
│   │   ├── git/          # CLI 래퍼, blame, filter-repo
│   │   ├── analysis/     # Tree-sitter, Radon, SonarQube
│   │   ├── llm/          # Instructor + Langfuse
│   │   ├── linkedin/     # BrightData 스크레이퍼
│   │   └── vector/       # pgvector 래퍼
│   └── interface/        # API + WebSocket
│       └── api/v1/
├── frontend/
└── infra/
```

---

## 17. Instructor + Pydantic 구조화 출력

4가지 명확화 질문 중 Q2에서 확정된 선택.

### 선택 근거

| 기준 | Instructor + Pydantic | Outlines | Marvin |
|------|----------------------|----------|--------|
| 상용 API 호환 | ✅ 최적 | ❌ 로컬 전용 | ✅ |
| 타입 검증 | ✅ Pydantic v2 자동 | ⚠️ 수동 | ⚠️ |
| 재시도 로직 | ✅ max_retries=3 내장 | ❌ | ❌ |
| Tool Calling | ✅ 네이티브 | ❌ | ⚠️ |

### 통합 패턴

```python
import instructor
from pydantic import BaseModel, ConfigDict

class AnalysisResult(BaseModel):
    model_config = ConfigDict(strict=True)  # Pydantic v2

    score: float
    evidence: list[str]
    confidence: float

# Instructor 자동 검증/재시도
client = instructor.from_openai(openai_client)
result = client.chat.completions.create(
    model="kimi-k2.5",
    response_model=AnalysisResult,
    max_retries=3,
    messages=[...]
)
```

---

## 18. 벡터 검색 (RAG) 전략

sabyun의 초기 요구: "인풋 컨텍스트를 최대한 줄이고 벡터 검색을 통해 유의미한 정보만 골라서 아웃풋을 낼 수 있도록"

### 설계

- **임베딩 모델**: text-embedding-3-small (1536D)
- **저장소**: pgvector (PostgreSQL 확장)
- **청크 분할**: AST 함수/클래스 경계 기준 (텍스트 기반 분할 아님)
- **컨텍스트 예산**: LLM 호출당 최대 8000 토큰

### 활용 시나리오

| 시나리오 | 벡터 검색 활용 |
|---------|--------------|
| Funnel Selection Stage 3 | JD ↔ Repo README 코사인 유사도 |
| 질문 생성 | 질문 주제와 관련된 코드 청크만 검색 |
| LLM 프롬프트 입력 축소 | 전체 코드 대신 관련 함수/클래스만 주입 → **90% 토큰 절감** |

### 임베딩 모델 불일치 발견

- Vector Store: text-embedding-3-small (1536D)
- Skill Normalizer: all-MiniLM-L6-v2 (384D)
- → **통일 필요** (설계서에 반영)

---

## 19. extra.md 아키텍처 최적화 반영

> **sabyun**: plan/extra.md 파일 확인해서 해당 2026-02-15-v5-final-design.md 최종적으로 업데이트 해줘

extra.md는 시니어 아키텍트 관점의 7가지 최적화 사항.

### 반영된 7가지 변경

| # | 변경 | 상세 |
|---|------|------|
| 1 | **의존성 최신화** | LangGraph 1.0.8+, Tree-sitter 0.24.7+, Instructor 1.7.0+ |
| 2 | **Reference Passing** | State에 Raw Data 대신 DB ID만 전달 (State Bloat 방지) |
| 3 | **SonarQube On-Demand** | Docker Profile `["analysis"]`로 필요 시만 구동 |
| 4 | **Monorepo 구조** | `backend/src/`, `frontend/`, `infra/` 물리적 격리 |
| 5 | **Cloudflare Tunnel 분리** | `infra-tunnel/` 독립 프로젝트, 생명주기 분리 |
| 6 | **Tree-sitter 0.24 Breaking Change** | `.so` 빌드 폐기 → Python 패키지 네이티브 바인딩 |
| 7 | **Backend/Frontend Dockerfile** | Multi-stage build, Hot Reload 지원 |

### Reference Passing 패턴 (핵심 변경)

```python
# AS-IS: State에 Raw Data 직접 포함 (메모리 힙 폭발 위험)
class MetaState(TypedDict):
    raw_ast_data: dict          # 수십 MB 가능
    full_blame_output: str      # 수 MB

# TO-BE: DB ID만 전달 (Reference Passing)
class MetaState(TypedDict):
    input_data_ref: str         # DB UUID
    forensic_result_ref: str    # DB UUID
    logic_result_ref: str       # DB UUID

# 노드 구현 패턴: Load → Process → Save → Return Ref
async def worker_node(state: MetaState) -> dict:
    data = await db.load(state["input_data_ref"])   # Load
    result = process(data)                            # Process
    ref = await db.save(result)                       # Save
    return {"logic_result_ref": ref}                  # Return Ref
```

---

## 20. 프론트엔드 시각화 전략 (D3.js)

souce5.md에서 상세 논의된 UI/UX 설계.

### 3초 판단 UI 흐름

```
1. 최상단: 3초 요약 카드 (신호등 🟢🟡🔴 + 한 줄 평)
   └── "기본기 탄탄(🟢), 최신 스택 부족(🟡), 보안 취약(🔴)"
   └── AI 생성 의심 12% 경고 아이콘

2. 중단: 4대 지표 레이더 차트 (논리력/전문성/안정성/진정성)
   └── 찌그러진 모양으로 직관적 성향 파악
   └── Hover 시 백분위 점수 팝업

3. 하단: 드릴다운 트리맵 (D3.js Treemap)
   └── 사각형 크기 = LoC, 색상 = 위험도
   └── 클릭 → 사이드 패널 (요약 + 면접 질문)

4. 면접 모드: Interview Card UI
   └── 질문 + 의도 + Check 체크박스 + 평가 버튼
```

### 7개 D3.js 차트 목록

1. **Radar Chart** — 4대 지표 비교
2. **Treemap** — 파일별 위험도/크기 시각화
3. **AI Code Heatmap** — Human vs AI 생성 비율
4. **Skill Treemap** — 기술 스택 사용량/깊이
5. **Code Churn Timeline** — 시간대별 코드 변경 패턴
6. **Contribution Sunburst** — 기여자별 기여 분포
7. **Complexity Distribution** — 복잡도 분포 히스토그램

---

## 21. 레거시 자산 선별 가이드

review2에서 확정된 **"파일 복사-붙여넣기 금지, 로직 이식 허용"** 원칙.

### [Asset] 핵심 로직 — Port Logic, Rewrite Code (60%)

| 기존 파일 | 판정 | 재작성 위치 |
|-----------|------|-----------|
| `scoring_formulas.py` (899줄) | 로직 100% 유지, 클래스 구조로 변경 | `domain/scoring/calculator.py` |
| `prompts/*.yaml` | Instructor 포맷 호환성 검증 후 이동 | `infrastructure/llm/prompts/` |
| JD 분석/매칭 로직 | 벡터 검색과 결합 | `domain/matching/funnel.py` |
| AuthorMatch 모델 (23줄) | 확장 (MailmapEntry, IdentityCluster 추가) | `domain/identity/models.py` |

### [Reference] 참조 대상 — Read Only (30%)

| 기존 파일 | 판정 | 참조 사항 |
|-----------|------|----------|
| `github_service.py` (1094줄) | 분리 후 완전 재작성 | Identity Resolution + infrastructure/github |
| `cached_llm.py` (772줄) | Redis 캐싱 아이디어만 참조 | 데코레이터 패턴으로 재작성 |
| `code_analyzer.py` (681줄) | 재설계 | infrastructure/analysis + LangGraph 노드 |

### [Liability] 폐기 대상 — Do Not Copy (10%)

- Temporal 관련 모든 코드: `workflows/`, `activities/`, `worker.py`
- 기존 DB 마이그레이션 스크립트: `alembic/versions/*.py`
- SVG 차트 컴포넌트 → D3.js 전면 교체
- 구형 정규식 파서 → Instructor(Structured Output)로 대체

---

## 22. 인프라 구성 (Docker + Cloudflare Tunnel)

review1, review2, extra.md 모두에서 논의된 인프라 설계.

### Docker Compose 구성 (최종)

```
jittda/docker-compose.yml
├── backend (python:3.11-slim, Multi-stage)
├── frontend (Node + Nginx Multi-stage)
├── postgres (16 + pgvector + pg_trgm)
├── redis (7)
├── sonarqube (profiles: ["analysis"] — On-Demand)
└── external network: jittda-public

infra-tunnel/docker-compose.yml (독립 프로젝트)
├── cloudflared (Cloudflare Tunnel)
└── network: jittda-public (생성)
```

### Makefile 표준 타겟

```makefile
make up           # 전체 서비스 시작
make down         # 전체 서비스 중지
make logs         # 로그 확인
make shell        # 백엔드 컨테이너 접속
make test         # 테스트 실행
make clean        # 컨테이너 정리
make infra-clean  # 볼륨까지 삭제 후 재시작
make tunnel-up    # Cloudflare Tunnel 시작
make tunnel-down  # Cloudflare Tunnel 중지
```

### DB 초기화 — Fresh init.sql

- Alembic 히스토리 없는 깨끗한 스키마
- LangGraph Checkpoint 테이블 포함 (3.0.x 호환)
- pgvector 확장, pg_trgm 확장 포함

---

## 23. Linear 프로젝트 & 44개 티켓 생성

> **sabyun**: 단계별 계획을 세부적으로 작성해줘. 리니어 프로젝트를 생성해서 해당 프로젝트의 이슈나 마일스톤을 활용해서 각각의 단계별로 세부적으로 작성해줘.

### 프로젝트 생성

- **프로젝트**: Jittda Sniper v5.0 — Clean Slate Reconstruction
- **팀**: Jittda (JIT)

### 7개 마일스톤

| Phase | 마일스톤 | 기간 | 티켓 수 |
|-------|---------|------|---------|
| 0 | Scaffolding | 3일 | 4개 |
| 1 | Domain Layer | 5일 | 6개 (+JIT-124) |
| 2 | Infrastructure Layer | 7일 | 8개 (+JIT-125) |
| 3 | Application Layer — Graphs | 7일 | 6개 |
| 4 | 질문 생성 + Enhancement | 5일 | 5개 |
| 5 | 출력 + 프론트엔드 | 10일 | 9개 |
| 6 | 통합 테스트 + 정리 | 5일 | 4개 |

### 42+2개 이슈 (JIT-82 ~ JIT-125)

| 범위 | Phase | 핵심 |
|------|-------|------|
| JIT-82~85 | Phase 0 | 프로젝트 초기화, Docker, DB, Makefile |
| JIT-86~91 + **JIT-124** | Phase 1 | Identity Resolution, Funnel, Scoring, **LinkedIn 도메인 모델** |
| JIT-92~99 + **JIT-125** | Phase 2 | Git, GitHub, Tree-sitter, Instructor, pgvector, **LinkedIn 어댑터** |
| JIT-100~105 | Phase 3 | State, Forensic/Logic/Stack Graph, MetaAgent, WebSocket |
| JIT-106~110 | Phase 4 | TopicSelector, QuestionCrafter, QualityGate, Langfuse |
| JIT-111~119 | Phase 5 | OutputAssembler, D3.js 차트, ResultPage 탭 |
| JIT-120~123 | Phase 6 | Domain 테스트, E2E, Playwright, 벤치마크 |

### LinkedIn 이슈 추가 (세션 중 발견)

> **Claude**: "설계서에 LinkedIn은 언급만 있고 전용 구현 티켓이 빠져 있습니다."
> **sabyun**: (승인)

- **JIT-124** (Phase 1): LinkedIn 프로필 도메인 모델 — 경력/스킬/학력 구조화
- **JIT-125** (Phase 2): LinkedIn 어댑터 — BrightData 클라이언트 + 프로필 스크레이핑

---

## 24. 마스터 CLAUDE.md 업데이트

> **sabyun**: 분산된 설계도를 마스터 프롬프트에서 각각의 주제별로 레퍼런스로 해당 md 파일 참조할 수 있도록 마스터 프롬프트 추가해줘. 뭐할때 뭐봐야하는지.

### 변경 사항

1. **타이틀**: `v4.0` → `v5.0` + 재건축 상태 표시
2. **Tech Stack**: LangGraph, D3.js, Instructor, Tree-sitter 반영
3. **Operation Rules**: v5.0 Phase 설계 문서 필수 참조 규칙 + DDD 규칙 추가
4. **Auto-Routing**: v5.0 키워드 8개 추가 → 각각 해당 Phase 문서로 라우팅
5. **Context Mapping**: v5.0 참조 테이블 21행 추가, 기존 v4.0 문서는 "레거시 — Read-only" 분리

### Auto-Routing 테이블 (v5.0 추가분)

| 키워드 | 라우팅 |
|--------|--------|
| jittda, v5, HMAS, LangGraph | → Phase별 설계문서 참조 |
| identity, mailmap, blame | → `phase1-domain.md` |
| funnel, scoring, 지표 | → `phase1-domain.md` |
| tree-sitter, AST, radon | → `phase2-infrastructure.md` |
| instructor, langfuse, 프롬프트 | → `phase2-infrastructure.md` + `phase4-questions.md` |
| StateGraph, supervisor, worker | → `phase3-application.md` |
| D3, 차트, radar, treemap | → `phase5-output-frontend.md` |

---

## 25. 최종 산출물 & 생성 파일 목록

### 생성된 파일

| 파일 | 내용 | 크기 |
|------|------|------|
| `plan/2026-02-15-langgraph-hmas-migration-design.md` | 초기 설계서 (17개 섹션) — review 이전 | ~29K 토큰 |
| `plan/2026-02-15-v5-migration-implementation-plan.md` | 초기 구현 계획 — review 이전 | ~14K |
| `plan/2026-02-15-v5-final-design.md` | **최종 설계서 (18개 섹션)** — review1+2+extra 반영 | ~87K |
| `plan/v5-design/phase0-scaffolding.md` | Phase 0 설계 참조 | - |
| `plan/v5-design/phase1-domain.md` | Phase 1 설계 참조 | - |
| `plan/v5-design/phase2-infrastructure.md` | Phase 2 설계 참조 | - |
| `plan/v5-design/phase3-application.md` | Phase 3 설계 참조 | - |
| `plan/v5-design/phase4-questions.md` | Phase 4 설계 참조 | - |
| `plan/v5-design/phase5-output-frontend.md` | Phase 5 설계 참조 | - |
| `plan/v5-design/phase6-testing.md` | Phase 6 설계 참조 | - |
| `docs/plans/2026-02-15-jittda-v5-reconstruction.md` | TDD 기반 상세 구현 계획 | ~34K |

### Linear 프로젝트

- **프로젝트**: Jittda Sniper v5.0 — Clean Slate Reconstruction
- **마일스톤**: Phase 0 ~ Phase 6 (7개)
- **이슈**: JIT-82 ~ JIT-125 (44개)
- **총 구현 기간**: 42일 (6 Phase)

---

## 핵심 설계 결정 요약

| # | 결정 | 근거 | sabyun 피드백 |
|---|------|------|--------------|
| 1 | LangGraph 전면 교체 | Temporal → LangGraph로 동적 에이전트 구현 | "현재는 플랜만 세우지 실제로는 랭체인 형식" |
| 2 | Pure LangGraph HMAS | 3가지 접근법 중 단일 프레임워크 통제 | 접근법 A 선택 |
| 3 | Instructor + Pydantic | 상용 API 호환, 자동 검증/재시도 | 구조화 출력 라이브러리 선택 |
| 4 | Full Stack 정적 분석 | Tree-sitter + Radon + SonarQube + Datasketch + Vibector + CLAVE | "정적분석도 더 있어야하는거 아냐?" |
| 5 | Big Bang 마이그레이션 | 일괄 전환 — Clean Slate | 마이그레이션 전략 선택 |
| 6 | Identity Resolution | review1 지적 → GitHub Node ID + mailmap + 3단계 포렌식 | review1.md 반영 |
| 7 | Funnel Selection | review1 지적 → 3단계 필터로 토큰 비용 최소화 | review1.md 반영 |
| 8 | DDD 4계층 | review1 지적 → domain→infrastructure import 절대 금지 | review1.md 반영 |
| 9 | Clean Slate 재건축 | review2 지적 → "마이그레이션이 아닌 재건축" | review2.md 반영 |
| 10 | Reference Passing | extra.md → State Bloat 방지, DB ID만 전달 | extra.md 반영 |
| 11 | SonarQube On-Demand | extra.md → Docker Profile로 메모리 효율화 | extra.md 반영 |
| 12 | Tree-sitter 0.24 대응 | extra.md → Breaking Change 네이티브 바인딩 | extra.md 반영 |
| 13 | Cloudflare Tunnel 분리 | extra.md → infra-tunnel/ 독립 프로젝트 | extra.md 반영 |
| 14 | LinkedIn 티켓 추가 | 설계서에 언급만 있고 티켓 누락 발견 | Claude 발견 → sabyun 승인 |
