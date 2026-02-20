> [시스템 아키텍트] 역할: Jittda Sniper v5.0 수석 설계자
> 태도: 비판적, 분석적, 현실적, 효율성 중심

제출하신 **'Vantict Sniper v5.0 (현 Jittda Sniper v5.0)' 초기 설계안**에 대한 정밀 리뷰 결과입니다.
전반적으로 **'어떻게(How)'**에 대한 기술적 깊이가 부족하며, 특히 **데이터의 무결성(Data Integrity)**과 **분석 비용 효율성(Cost Efficiency)** 측면에서 치명적인 결함이 발견되었습니다.

이를 보완하기 위한 비판적 리뷰와 구체적인 개선 가이드를 전달합니다.

---

# Jittda Sniper v5.0 초기 설계 리뷰 보고서

## 1. 총평 (Executive Summary)

> **"화려한 오케스트레이션(LangGraph)에 집중하느라, 정작 분석할 데이터의 '순도(Purity)'와 '적합성(Relevance)'을 놓쳤습니다."**

초기 설계는 Temporal을 LangGraph로 교체하는 구조적 변화에만 치중되어 있습니다. 채용 담당자가 가장 중요하게 보는 **"이 코드를 정말 지원자가 짰는가?"(Identity)**와 **"이 프로젝트가 우리 회사 업무와 관련이 있는가?"(Relevance)**를 검증하는 로직이 빈약합니다. 단순 `git clone` 후 전체 분석을 돌리는 방식은 노이즈가 많고 토큰 비용 낭비가 심합니다.

---

## 2. 주요 결함 및 기술적 개선 권고

### 2.1 [Core Logic] 사용자 식별 및 기여분 추출 (Identity & Purity)

**🔴 문제점:**

* 설계안의 `CollectorWorker`는 단순히 레포지토리를 수집한다고만 명시되어 있습니다.
* 지원자가 여러 이메일(개인/회사/학교)을 쓰거나, 닉네임을 변경했거나, 다른 컴퓨터에서 커밋했을 경우를 전혀 고려하지 않았습니다.
* 단순 `git blame`은 공백 수정, 파일 이동, 리팩토링까지 '기여'로 잡습니다. 이는 거품 섞인 분석 결과를 초래합니다.

**✅ 개선 권고 (Identity Resolution Pipeline 도입):**

1. **GitHub Node ID 기반 추적:** 이메일이 바뀌어도 변하지 않는 GitHub 고유 ID(`databaseId`)를 GraphQL로 조회하여 유저를 특정해야 합니다.
2. **동적 `.mailmap` 생성:** 레포지토리 내 커밋 히스토리에서 이름/이메일 유사도(Levenshtein Distance)를 분석하여, 동일인으로 추정되는 커밋을 하나로 묶는 클러스터링 로직이 필요합니다.
3. **3단계 포렌식 쿼리 적용:**
* **Level 1 (Git Internal):** `git blame -w -M -C -C --line-porcelain` 옵션을 사용하여 공백(`-w`), 파일 이동(`-M`), 코드 복사(`-C`)를 제외한 **순수 로직 작성분**만 추출하십시오.
* **Level 2 (Semantic Pruning):** **Tree-sitter**를 사용하여 AST 파싱 후, `import` 구문, 주석, Config 설정, 자동 생성된 코드(Generated Code)를 제거하고 **함수/클래스 본문**만 남기십시오.



### 2.2 [Efficiency] JD 기반 적합성 선별 (Relevance Filtering)

**🔴 문제점:**

* 모든 레포지토리를 분석하려고 합니다. 백엔드 지원자가 3년 전에 만든 'React 토이 프로젝트'나 '알고리즘 문제 풀이' 레포까지 심층 분석하는 것은 리소스(LLM 토큰, 시간) 낭비입니다.
* "질문은 무조건 JD 기반이어야 한다"는 요구사항을 충족하려면, 분석 대상 선정부터 JD와 연관되어야 합니다.

**✅ 개선 권고 (Funnel Selection Architecture 도입):**

1. **Metadata Filter:** 언어, 스택, 최근 업데이트 날짜로 1차 필터링 (Hard Filter).
2. **Vector Relevance Scoring:**
* JD의 요구사항 텍스트와 각 레포지토리의 `README`/`Description`을 임베딩(Embedding)합니다.
* **Cosine Similarity**를 계산하여 JD와 의미론적으로 가장 유사한 상위 3~5개 프로젝트만 선별하십시오.


3. **Organization Repo 필터링:** 조직 레포지토리의 경우, 유저의 기여도(Commits/PRs)가 임계치(예: 10% 이상)를 넘지 않으면 과감히 제외하십시오.

### 2.3 [Architecture] 백엔드 구조 및 패턴

**🔴 문제점:**

* 기존 설계는 LangGraph 노드 안에 비즈니스 로직이 섞여 있을 가능성이 높습니다. 이는 유지보수를 어렵게 합니다.
* `Makefile`이나 인프라 설정이 구체적이지 않거나 잘못된 관행(예: 로컬 포트 직접 노출 등)을 따를 위험이 있습니다.

**✅ 개선 권고 (DDD + Clean Infrastructure):**

1. **DDD(Domain-Driven Design) 적용:**
* **Domain Layer:** 순수 비즈니스 로직(예: 점수 산출 공식, 포렌식 규칙)은 외부 의존성 없이 작성.
* **Application Layer:** LangGraph 흐름 제어, 유스케이스 정의.
* **Infrastructure Layer:** GitHub API, Git CLI, LLM Client 등 기술적 구현체 격리.


2. **Cloudflare Tunnel 도입:** `ngrok` 대신 Cloudflare Tunnel(Zero Trust)을 사용하여, 포트 포워딩 없이 안전하게 로컬 서버를 외부(프론트엔드/Webhook)에 노출하십시오.
3. **Makefile 표준화:** `up`, `down`, `logs`, `shell`, `test` 등 표준 타겟을 정의하여 개발 경험(DX)을 통일하십시오.

### 2.4 [UI/UX] 프론트엔드 시각화

**🔴 문제점:**

* 기존 SVG 방식은 데이터 밀도가 낮아 '심층 분석'이라는 느낌을 주기 어렵습니다.

**✅ 개선 권고 (React + Tailwind + D3.js):**

1. **기술 스택:** React 19 + Tailwind CSS로 빠른 UI 개발, D3.js로 커스텀 차트 구현.
2. **AI Code Heatmap:** 파일별로 인간 작성(Human) vs AI 생성(Generated) 비율을 시각적으로 보여주는 히트맵을 추가하십시오.
3. **실시간 스트리밍:** LangGraph의 실행 상태(State)를 WebSocket으로 받아, 분석 단계별 진행 상황을 실시간으로 보여주십시오 (예: "Git 포렌식 중...", "JD 적합성 분석 중...").

---

## 3. 수정된 실행 계획 (Action Items)

설계 승인 시, 아래 순서대로 **Jittda Sniper v5.0** 구축을 시작해야 합니다.

1. **Scaffolding (인프라 구축):**
* `jittda-v5` 신규 디렉토리 생성.
* DDD 폴더 구조 (`domain`, `application`, `infrastructure`) 수립.
* `docker-compose.yml` (Postgres, Redis, Cloudflare Tunnel) 및 `Makefile` 작성.


2. **Core Logic 구현 (우선순위 최상):**
* `infrastructure/git_forensic`: Git Blame + Tree-sitter Pruning 모듈 구현.
* `domain/service`: Identity Resolution (유저 식별) 로직 구현.


3. **Selector 구현:**
* Gemini Embedding을 활용한 JD <-> Repo 유사도 분석기 구현.


4. **Integration (LangGraph):**
* 구현된 모듈을 LangGraph 노드로 연결.


과거의 코드를 맹목적으로 가져오는 것은 기술 부채를 이자까지 쳐서 가져오는 것과 같습니다. 철저한 '선별적 마이그레이션(Selective Migration)'이 필요합니다."

기존 프로젝트를 전수 조사(Audit)하여, 새 아키텍처(DDD + LangGraph)에 통합할 요소와 폐기할 요소를분석하여 최종 설계에 반영하세요
