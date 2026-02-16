제공해주신 방대한 기술 자료와 분석 보고서, 그리고 이전에 논의된 내용을 바탕으로 **프로젝트 '짓다(Jitta)'**를 위한 **최종 기술 설계안 및 실행 플랜**을 작성했습니다.

이 설계안은 **'에이전트 병렬화(Parallelization)'**를 통한 속도 향상, **'AST 및 Git 포렌식'**을 통한 데이터의 정확도 확보, 그리고 **'계층적 멀티 에이전트 시스템(HMAS)'**을 통한 결정론적 수치 산출에 초점을 맞추고 있습니다.

---

# [Project Jitta] 최종 기술 아키텍처 및 구현 로드맵

## 1. 시스템 설계 철학 (Architectural Philosophy)

본 시스템은 **"확률적 AI(LLM)와 결정론적 알고리즘(Static Analysis)의 하이브리드 결합"**을 지향합니다.
단순히 LLM에게 "이 코드 어때?"라고 묻는 것이 아니라, 수학적으로 계산된 지표(Fact)를 LLM에게 제공하여 해석(Insight)하게 함으로써 할루시네이션을 원천 차단하고 신뢰도를 보장합니다.

### 핵심 설계 원칙
1.  **계층적 오케스트레이션 (Hierarchical Orchestration):** 단일 에이전트의 부하를 막기 위해 **전략(Meta) - 관리(Supervisor) - 실행(Worker)**의 3계층 구조를 채택합니다.
2.  **상태 기반 제어 (Stateful Graph Workflow):** 복잡한 순환 참조와 에러 복구를 위해 **LangGraph**를 사용하여 상태(State)를 명시적으로 관리하고 체크포인트를 저장합니다.
3.  **이벤트 기반 병렬 처리 (Event-Driven Parallelization):** 다수의 레포지토리와 파일을 동시에 분석하기 위해 **Fan-out/Fan-in** 패턴을 적용, 분석 속도를 극대화합니다.

---

## 2. 상세 기술 스택 및 도구 선정 (Tech Stack Selection)

소스 코드 분석의 깊이와 시스템의 확장성을 고려하여 최적의 도구를 선정했습니다.

| 구분 | 선정 기술 | 선정 근거 및 활용 방안 |
| :--- | :--- | :--- |
| **Orchestration** | **LangGraph** | 순환 로직, 상태 저장(Checkpointing), Human-in-the-loop 지원 등 복잡한 워크플로우 제어에 최적화됨. |
| **VCS Analysis** | **PyDriller** | Git 메타데이터 추출, 커밋 순회, 수정된 파일 추적 등을 위한 파이썬 표준 프레임워크. |
| **Parsing** | **Tree-sitter** | 텍스트가 아닌 구문(Syntax) 단위 분석을 통해 포맷팅 노이즈를 제거하고 시맨틱 Diff를 추출. |
| **Filtering** | **git-filter-repo** | 바이너리, 대용량 파일, 히스토리 내 민감 정보 등을 사전 제거하여 분석 효율성 증대. |
| **Complexity** | **Radon / Lizard** | 순환 복잡도(McCabe) 및 Halstead 지표 산출을 위한 경량화된 정적 분석 도구. |
| **Persistence** | **PostgreSQL + pgvector** | 분석 결과(JSON)와 벡터 임베딩(RAG)을 통합 저장. 시계열 데이터(Hypertable) 관리 용이. |
| **Caching** | **Redis** | 에이전트 간 메시지 패싱 및 단기 상태(Short-term Memory) 저장, 속도 최적화. |
| **Frontend** | **Next.js + D3.js** | SSR을 통한 빠른 로딩 및 복잡한 계층 데이터(Treemap, Sunburst)의 인터랙티브 시각화. |

---

## 3. 계층적 멀티 에이전트 아키텍처 (HMAS Design)

시스템은 **LangGraph** 기반의 **Supervisor-Worker 패턴**으로 구성됩니다. 이는 단일 에이전트의 병목 현상을 해소하고 각 분석 영역의 전문성을 강화합니다.

### Level 1: The Meta-Agent (전략 및 총괄)
*   **역할:** 사용자 요청(Github URL)을 접수하고 전체 분석 파이프라인의 상태를 모니터링합니다.
*   **기능:**
    *   분석할 레포지토리의 우선순위 결정.
    *   각 Supervisor에게 작업 할당 및 최종 리포트 합성(Synthesis).
    *   분석 실패 시 재시도 전략(Retry Policy) 수립.

### Level 2: The Supervisor Agents (영역별 관리자)
각 Supervisor는 자신의 도메인에 특화된 Worker들을 거느리며, 중간 결과를 검증하고 요약합니다.

1.  **Forensic Supervisor (진위 여부 판별):**
    *   포크(Fork) 여부, 유령 기여, AI 생성 코드 의심 구간 필터링 지휘.
2.  **Logic Supervisor (코드 품질 분석):**
    *   알고리즘 복잡도, 아키텍처 패턴, 안티 패턴 분석 지휘.
3.  **Stack Supervisor (기술 숙련도 분석):**
    *   사용된 프레임워크의 깊이(API Depth), 최신 문법 활용도 분석 지휘.

### Level 3: The Worker Agents (실행 및 측정)
실제 연산과 데이터 추출을 담당하며, **병렬(Fan-out)**로 실행됩니다.

*   **Collector Agent:** GraphQL을 사용해 `isFork: false` 조건으로 레포지토리 리스트 및 메타데이터 수집.
*   **Cleaner Agent:** `git-filter-repo` 및 LSH 알고리즘으로 보일러플레이트 및 오픈소스 중복 제거.
*   **Metric Agent:** AST 파싱을 통해 Halstead Metrics($V$, $D$, $E$) 및 McCabe 순환 복잡도($M$) 계산.
*   **Pattern Agent:** 소스 코드 내 디자인 패턴(Singleton, Factory 등) 및 SOLID 원칙 준수 여부 스캔.
*   **Vibector Agent:** 커밋 시간차($\Delta Time$)와 코드량($\Delta LoC$)을 분석하여 분당 타이핑 속도가 인간 한계(40-80 WPM)를 초과하는지 감시.

---

## 4. 핵심 분석 알고리즘 및 수치화 모델 (Methodology)

소스 자료에 기반하여, 단순한 감이 아닌 **'결정론적 수치(Deterministic Metrics)'**를 산출합니다.

### A. 논리력 점수 (Logic Score) - 알고리즘 효율성
*   **측정 공식:** 할스테드 난이도($D$)와 순환 복잡도($M$)의 역상관 관계 분석.
    *   $$Score_{logic} = \frac{1}{1 + \alpha(M_{avg}) + \beta(D_{avg})} \times 100$$
    *   복잡한 기능을 구현하면서도 $M$과 $D$를 낮게 유지할수록 고득점.

### B. 전문성 점수 (Mastery Score) - 프레임워크 깊이
*   **측정 방식:** AST 노드 내 API 호출 깊이(Depth) 가중치 합산.
    *   예: Spring Boot에서 단순 `@Controller`(Level 1) vs `@AOP` + `@Transactional(propagation=...)`(Level 3).
    *   $$Score_{mastery} = \sum (Count_{API} \times Weight_{Level})$$

### C. 안정성 점수 (Stability Score) - 유지보수성
*   **측정 지표:** 기술 부채 비율(Code Smells/LoC) 및 리워크 비율(Rework Rate).
    *   Code Churn 분석을 통해 작성 후 3주 이내에 수정/삭제된 코드 비율이 높으면 감점 (시행착오로 간주).

### D. 진정성 지수 (Authenticity Index) - 인간 기여도
*   **필터링:** AI 생성 의심 구간(Vibector 탐지) 및 오픈소스 복사 구간(LSH 탐지)을 총 기여량에서 차감.
    *   $$Index_{real} = \frac{LoC_{total} - (LoC_{AI} + LoC_{Copy})}{LoC_{total}} \times 100$$

---

## 5. 단계별 구현 플랜 (Implementation Roadmap)

### Phase 1: 기반 인프라 구축 (Weeks 1-3)
*   **목표:** 데이터 파이프라인 및 기본 분석 환경 구성.
*   **Action Items:**
    1.  **LangGraph Setup:** StateGraph 정의 (Schema: `RepoState`, `AnalysisResult`).
    2.  **DB Schema:** PostgreSQL에 `repositories`, `commits`, `metrics` 테이블 및 Hypertable 설정.
    3.  **Collector Agent:** GitHub GraphQL API 연동 및 Rate Limit 관리 로직(Redis) 구현.

### Phase 2: 분석 엔진 코어 개발 (Weeks 4-7)
*   **목표:** 정적 분석 도구 통합 및 수치화 로직 구현.
*   **Action Items:**
    1.  **PyDriller & Tree-sitter 연동:** 파이썬 환경에서 Git 히스토리 순회 및 AST 파싱 모듈 개발.
    2.  **Metrics Calculation:** Halstead 및 McCabe 복잡도 계산 알고리즘 포팅 (Python `radon` 라이브러리 활용).
    3.  **Vibector 구현:** 커밋 타임스탬프 기반 타이핑 속도 분석 로직 개발.

### Phase 3: 에이전트 오케스트레이션 및 병렬화 (Weeks 8-10)
*   **목표:** 분석 속도 최적화 및 에이전트 간 협업 구현.
*   **Action Items:**
    1.  **Map-Reduce 패턴 적용:** 다수 파일 분석을 Worker 에이전트들에게 분산(Map)하고 Supervisor가 취합(Reduce)하는 로직 구현.
    2.  **State Management:** LangGraph의 Checkpointer를 활용하여 긴 분석 과정 중단 시 재개(Resume) 기능 구현.

### Phase 4: 대시보드 및 리포트 생성 (Weeks 11-12)
*   **목표:** 비기술자 CEO를 위한 시각화 및 면접 질문 생성.
*   **Action Items:**
    1.  **Visualization:** Next.js + D3.js로 '기술 부채 Treemap', '숙련도 Radar Chart' 구현.
    2.  **LLM Synthesis:** 산출된 수치 데이터를 프롬프트에 주입하여 "이 지원자는 동시성 처리에 강점이 있으나 보안 설정에 약점이 있음"과 같은 자연어 리포트 및 면접 질문 생성.

---

## 6. 최종 산출물 예시 (Deliverables)

이 시스템을 통해 채용 담당자(CEO)는 다음과 같은 **'Jitta 리포트'**를 받아보게 됩니다.

1.  **종합 등급 (예: A-)**: 4가지 핵심 지표(논리력, 전문성, 안정성, 진정성)의 가중 합산 결과.
2.  **스킬 트리맵 (Skill Treemap)**: 지원자가 사용한 기술 스택의 실제 사용량과 깊이를 시각화 (단순 나열 아님).
3.  **킬러 질문 (Killer Questions)**:
    *   *"Repo A의 `AuthService.java`에서 순환 복잡도가 15로 매우 높습니다. 이를 리팩토링하지 않고 유지한 이유는 무엇입니까?"*
    *   *"최근 3개월간 AI 생성 코드로 의심되는 커밋이 40%입니다. 본인이 직접 설계한 로직은 어느 부분입니까?"*

이 설계안은 **'결정론적 데이터'**를 통해 신뢰성을 확보하고, **'에이전트 병렬화'**를 통해 속도를 잡으며, **'계층적 구조'**를 통해 확장성을 보장하는 가장 확실한 기술적 접근법입니다.
