# Jittda Live 설계 브레인스토밍 기록

> **세션**: 2026-02-16 11:04 ~ 2026-02-17 08:32 (KST)
> **참여**: sabyun (기획/요구사항) + Claude (설계/리서치)
> **컨텍스트 소진**: 3회 (대규모 세션)
> **산출물**: 설계서, MVP PRD, 와이어프레임, Linear 프로젝트 (69개 이슈)

---

## 목차

1. [브레인스토밍 시작 — 초기 요구사항](#1-브레인스토밍-시작--초기-요구사항)
2. [명확화 질문 & 의사결정](#2-명확화-질문--의사결정)
3. [기술 스택 리서치 & 확정](#3-기술-스택-리서치--확정)
4. [아키텍처 접근법 비교 & 확정](#4-아키텍처-접근법-비교--확정)
5. [Knowledge Graph 하이브리드 설계](#5-knowledge-graph-하이브리드-설계)
6. [Graph-First 분석 파이프라인](#6-graph-first-분석-파이프라인)
7. [Agentic Graph RAG — 도구 기반 그래프 탐색](#7-agentic-graph-rag--도구-기반-그래프-탐색)
8. [LangGraph HMAS 에이전트 아키텍처](#8-langgraph-hmas-에이전트-아키텍처)
9. [데스크탑 앱 상세 아키텍처](#9-데스크탑-앱-상세-아키텍처)
10. [디자인 패턴 & 추상화 전략](#10-디자인-패턴--추상화-전략)
11. [SOLID 원칙 매핑](#11-solid-원칙-매핑)
12. [실시간 데이터 플로우](#12-실시간-데이터-플로우)
13. [면접관 대시보드 UI/UX](#13-면접관-대시보드-uiux)
14. [KG 스키마 & Graph-First 파이프라인](#14-kg-스키마--graph-first-파이프라인)
15. [2계층 질문 시스템](#15-2계층-질문-시스템)
16. [백엔드 확장 설계](#16-백엔드-확장-설계)
17. [에러 처리 체계](#17-에러-처리-체계)
18. [자기 설명적 에러 코드](#18-자기-설명적-에러-코드)
19. [Sentry + Infisical 통합](#19-sentry--infisical-통합)
20. [DB 스키마](#20-db-스키마)
21. [면접 결과물 전체 맵](#21-면접-결과물-전체-맵)
22. [Phase 로드맵 & Linear 티켓](#22-phase-로드맵--linear-티켓)
23. [프로모 코드 + 결제 준비](#23-프로모-코드--결제-준비)
24. [최종 산출물](#24-최종-산출물)

---

## 1. 브레인스토밍 시작 — 초기 요구사항

> **sabyun**: v5.0 설계를 바꾸는게 필요할 것 같아. 지금은 웹에서만 질문 만들어주고 정보 보여주는건데 이걸 개선해서 실시간 면접 AI 가이드 기능을 지원하도록 할거야. 면접자 데이터 분석을 끝내고 데스크탑 프로그램에서 접속해서 해당 면접자를 선택하고 면접을 진행하면 OS 마이크와 시스템 사운드 캡쳐를 오프라인인지, 온라인 면접인지에 따라 동적으로 챕쳐하고 면접자 화자분리가 필요한(오프라인)에서 화자분리를 하고 STT화 해서 실시간으로 AI가 상황을 인식하고 우리가 미리 면접자 정보를 벡터나 그래프 같은 곳에 저장한 정보를 실시간으로 파악해서 면접에 필요한 질문 생성을 해주는게 목표야.

**제공된 최소 기능 요구서 핵심:**

1. **OS 네이티브 오디오 캡처**: 서드파티 가상 드라이버 없이 시스템 오디오 + 마이크 캡처
   - macOS: ScreenCaptureKit / CoreAudio
   - Windows: WASAPI 루프백
2. **엣지 기반 VAD**: Silero VAD (WASM), 무음 1.5초 이상 → 발화 완전 종료 인식
3. **초저지연 RAG**: LanceDB 인프로세스, 0.1초 이내 검색
4. **실시간 LLM 질문 생성**: Groq TTFT 0.14초
5. **토픽 커버리지 추적**: 카테고리별 프로그레스바
6. **면접 종료 후 AI 종합 분석 + 시각화**

**프로젝트 컨텍스트:**
- 기존 **Jittda Sniper v5.0**: 서버 사이드 분석 (LangGraph HMAS + DDD), 42개 티켓, 42일 로드맵
- 새로운 **Jittda Live**: v5.0 위에 데스크탑 앱으로 실시간 면접 가이드 확장

---

## 2. 명확화 질문 & 의사결정

| # | 질문 | sabyun 결정 |
|---|------|-------------|
| 1 | **프로젝트 관계** — 웹/앱 별도? 통합? | 웹 유지 + 질문 생성을 라이브로 이동 + 데이터/결과 양쪽 공유 |
| 2 | **타겟 OS** | macOS 우선, 인터페이스 추상화로 Windows 확장성 확보 |
| 3 | **면접 유형** | 온라인(채널 분리) + 오프라인(AI 화자분리) 둘 다 MVP |
| 4 | **STT 서비스** | Deepgram Nova-3 + 인터페이스 추상화 (교체 가능) |
| 5 | **서버 통신** | REST(전/후) + WebSocket(면접 중) |
| 6 | **질문 생성 방식** | 하이브리드 — AI 자동 추천 + 면접관 수동 요청 병행 |
| 7 | **결과 분석** | 전체 리포트 (스코어카드 + 타임라인 + 시각화 + v5.0 통합) |
| 8 | **사전 분석** | v5.0 분석 필수 선행 → Live에 동기화 |

---

## 3. 기술 스택 리서치 & 확정

### 데스크탑 프레임워크

| 항목 | Electron (v33+) | Tauri v2 (v2.2+) | Neutralino |
|------|:---:|:---:|:---:|
| 번들 크기 | ~100MB+ | ~2-10MB | ~2-5MB |
| 메모리 | ~200-400MB | ~30-40MB | ~30-50MB |
| 시스템 오디오 캡처 | `electron-audio-loopback` 즉시 사용 | Rust 직접 래핑 필요 | 불가 |
| npm 생태계 | 전체 사용 가능 | 제한적 | 없음 |
| **결정** | **MVP 추천** | 향후 마이그레이션 고려 | 탈락 |

### 실시간 STT 서비스 비교 (한국어+영어, 2026년 2월 기준)

| 서비스 | 실시간 스트리밍 | 한국어 WER | 레이턴시 | 화자분리 | 가격 |
|--------|:---:|---|---|:---:|---|
| **Deepgram Nova-3** | WebSocket | Tier 2 (7-16%) | <300ms | 내장 | $0.0077/분 |
| **ElevenLabs Scribe v2 RT** | WebSocket | "Good" (10-20%) | ~150ms | 미확인 | 별도 확인 |
| **AssemblyAI Universal** | WebSocket | 99+ 언어 균일 | ~300ms | 내장 (95개 언어) | $0.0025/분 |
| **Soniox** | WebSocket | 60+ 언어 | 미공개 | 실시간 내장 | 저렴 |

> **핵심 발견**: Reddit — "Deepgram/AssemblyAI는 영어에선 훌륭하지만 아시아 언어 정확도와 구두점은 크게 떨어진다"

### 확정 기술 스택

| 계층 | 선택 | 이유 |
|------|------|------|
| **데스크탑** | Electron v33+ | 시스템 오디오 캡처 생태계 최성숙 |
| **오디오 캡처** | electron-audio-loopback | macOS/Windows, 외부 드라이버 불필요 |
| **VAD** | Silero VAD + @ricky0123/vad | WASM, 87.7% TPR, MIT |
| **STT** | Deepgram Nova-3 | 한국어 WER 최저, 멀티채널, 화자분리 |
| **로컬 벡터 DB** | LanceDB v0.26 | 서버 없는 임베디드, TS 네이티브 |
| **실시간 LLM** | Groq (TTFT 0.14초) | 실시간 질문 생성 최적 |
| **한국어 보완** | Together AI (Qwen-2.5/SOLAR) | 한국어 특화 모델 선택지 |

---

## 4. 아키텍처 접근법 비교 & 확정

### 3가지 접근법

| 기준 | A: Monorepo 확장 | B: 독립 레포 | C: Turborepo |
|------|:---:|:---:|:---:|
| v5.0 영향 | 중간 (디렉토리 추가) | 최소 | 대폭 (구조 변경) |
| 타입 공유 | 직접 import | npm 패키지 | 워크스페이스 패키지 |
| 개발 속도 | **빠름** | 보통 | 초기 느림 |
| MVP 적합성 | **높음** | 높음 | 낮음 |

### sabyun 피드백 → 설계 전환

> **sabyun**: v5.0은 아직 구현 안 했어.

**핵심 전환**: v5.0 미구현 → **처음부터 통합 설계** 가능. 1인 개발에서 MSA는 과잉.

**확정: 통합 Monorepo**

```
jittda/
├── backend/      # 단일 백엔드 (분석 + 라이브)
├── frontend/     # 웹 (분석 결과 + 라이브 결과 열람)
├── desktop/      # Electron (실시간 면접 가이드)
├── shared/       # 웹 + 데스크탑 공유 타입
└── infra/        # Docker, DB, Tunnel
```

---

## 5. Knowledge Graph 하이브리드 설계

> **sabyun**: 면접자의 깃 분석데이터나 레주메 커버레터 포트폴리오 링크드인 정보들에서 가져온것들을 postgres만으로 효율적으로 정보 추출하기 힘들것같은데 실시간으로 해당 정보 바탕으로 질문을 생성해야하는데 말이 안되는것같아. 그래프나 RAG를 사용해서 해야할것같은데.

### 왜 PostgreSQL만으로는 안 되는가

| 질의 유형 | PostgreSQL | 벡터 DB | Knowledge Graph |
|-----------|:---:|:---:|:---:|
| 의미 검색 | SQL LIKE (부정확) | **벡터 유사도** | - |
| 관계 탐색 (출처 추적) | JOIN (느림) | 불가 | **그래프 탐색** |
| 모순 탐지 (삼각 검증) | 불가 | 불가 | **삼각 검증** |
| 다중 홉 추론 | 복잡한 서브쿼리 | 불가 | **1-2홉 탐색** |

### 확정: 하이브리드 — 서버 KG + 클라이언트 로컬 검색

```
[서버 - v5.0 분석 단계]
PostgreSQL(원본) + NetworkX(Python 그래프)
    → 분석 결과를 Knowledge Graph로 구축
    → JSON 직렬화 + 벡터 임베딩 export

         ↓ 면접 시작 전 동기화

[클라이언트 - Electron 실시간]
LanceDB(벡터 검색) + graphology(인메모리 그래프)
    → 하이브리드 쿼리 엔진 (<100ms)
```

### 실제 면접 시뮬레이션

**지원자 발화**: "Redis를 써서 속도를 많이 높였고, 혼자서 캐싱 레이어를 다 구축했습니다"

1. STT 수신 (300ms)
2. LanceDB 벡터 검색 (20ms) → 이력서: "팀 프로젝트로 Redis 캐시 구현", 코드: blame 95%
3. graphology 그래프 탐색 (5ms) → 모순 발견: "팀 프로젝트" ↔ "혼자 구축"
4. Groq LLM (640ms) → 꼬리질문 생성
5. **전체: ~670ms (발화 종료 → 질문 카드 표시)**

---

## 6. Graph-First 분석 파이프라인

> **sabyun**: v5.0으로 분석할때 바로바로 그래프 RAG에 해당 데이터를 주입하고 통합하면 되지않나? 그렇게 하면 한번에 될것같은데 분석결과를 낼때도 효율성이 증대될 수 있을것 같은데.

### 기존 vs 개선

```
[기존 — 분산]
각 Worker → analysis_results 테이블에 JSON 저장 → ProfileSynthesizer가 전부 합침 (병목)

[개선 — 그래프 중심]
CollectorWorker → 그래프에 노드/엣지 추가
CleanerWorker   → 기존 노드에 blame 속성 추가
SkillExtractor  → 그래프 쿼리로 선행 결과 활용
ComplexityMeter → 파일 노드에 복잡도 속성 추가
ProfileSynthesizer → 그래프 순회 한 번으로 완성!
```

### 효율성 증대 포인트

| 단계 | 기존 (분산) | 개선 (그래프 중심) |
|------|-----------|-----------------|
| SkillExtractor | 코드만 보고 추출 | 이력서+LinkedIn+코드 교차 확인 → 정확도 향상 |
| ProfileSynthesizer | 5개 Worker JSON 전부 로드 | 그래프 순회 한 번 → O(N) |
| QualityGate | 질문 하나씩 검증 | "미검증 스킬" 즉시 쿼리 |
| 모순 탐지 | 불가능 (별도 로직 필요) | 분석 중 **자동** CONTRADICTS 엣지 생성 |

---

## 7. Agentic Graph RAG — 도구 기반 그래프 탐색

> **sabyun**: 기존 v5.0을 지금 추가되는 기능들로 최적화 더 할 수 있는 방법 찾아봐. 그래프 노드 탐색 툴로 호출해서 작업한다면 불필요한 input 토큰 많이 사용할 필요없이 필요한거 알아서 가져가서 쓸 수 있을것 같은데.

### 핵심 변경: 고정 컨텍스트 → 도구 기반 동적 탐색

```
[기존] 각 Worker 결과 JSON → 수동으로 8000토큰 맞춰 잘라 붙이기 → LLM에 전달
[개선] LLM에게 그래프 탐색 도구 세트 제공 → LLM이 필요한 정보만 선택적 조회
```

### 토큰 절감 효과

| 단계 | 기존 | 개선 | 절감 |
|------|------|------|------|
| QuestionCrafter (질문 1개당) | ~8,000 토큰 | ~2,500 토큰 | **-69%** |
| ProfileSynthesizer | ~12,000 토큰 | ~4,000 토큰 | **-67%** |
| QualityGate | ~6,000 토큰 | ~1,500 토큰 | **-75%** |
| **25개 질문 생성 전체** | **~200,000 토큰** | **~62,500 토큰** | **-69%** |

### 그래프 탐색 도구 세트

```python
@tool get_candidate_overview()      # 전체 요약 (~50 토큰)
@tool get_skill_evidence()          # 특정 스킬 증거 (~200 토큰)
@tool find_contradictions()         # 모순점 목록 (~150 토큰)
@tool get_jd_coverage()             # JD 매칭 상태 (~200 토큰)
@tool get_code_deep_dive()          # 파일 상세 (~300 토큰)
@tool get_unverified_topics()       # 미검증 토픽 (~100 토큰)
@tool traverse_context()            # 범용 N홉 탐색 (~100-500 토큰)
```

---

## 8. LangGraph HMAS 에이전트 아키텍처

v5.0의 LangGraph 1.0 기반 **3계층 HMAS(Heterogeneous Multi-Agent System)**을 Jittda Live로 확장한 에이전트 구조.

### v5.0 분석 에이전트 — 3계층 HMAS

```
                    ┌──────────────┐
                    │  MetaAgent   │  ← LangGraph StateGraph 최상위
                    │  (조율자)     │     모든 Worker 결과를 KG에 통합
                    └──────┬───────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  Forensic    │ │   Logic      │ │   Stack      │
    │  Supervisor  │ │  Supervisor  │ │  Supervisor  │
    │  (신원 검증) │ │  (코드 분석) │ │  (스택 분석) │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
    ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
    │ Identity    │  │ AST Parser  │  │ Skill       │
    │ Resolution  │  │ (Tree-sitter)│ │ Extractor   │
    │ Worker      │  ├─────────────┤  ├─────────────┤
    ├─────────────┤  │ Complexity  │  │ Resume      │
    │ Blame       │  │ Meter       │  │ Analyzer    │
    │ Filter      │  │ (Radon)     │  ├─────────────┤
    │ Worker      │  ├─────────────┤  │ LinkedIn    │
    ├─────────────┤  │ Plagiarism  │  │ Parser      │
    │ AI Code     │  │ Detector    │  ├─────────────┤
    │ Detector    │  │ (Datasketch)│  │ CrossRef    │
    │ Worker      │  └─────────────┘  │ Worker      │
    └─────────────┘                   └─────────────┘
```

**핵심 설계:**
- **MetaAgent**: Fan-out/Fan-in 패턴으로 3개 Supervisor를 병렬 실행
- **Supervisor**: 자기 산하 Worker들을 순차/병렬 조율
- **Worker**: 단일 책임 원칙 — 1개 Worker = 1개 분석 도메인
- **State**: Reference Passing — LangGraph State에는 DB ID만, Raw Data는 DB에 저장 (State Checkpoint 최적화)

### Live 면접 에이전트 — LiveAgent Graph

```python
# application/graphs/live_agent.py — LangGraph StateGraph

class LiveAgentState(TypedDict):
    session_id: str
    transcript_segments: list[str]      # 최근 N개 발화
    active_triggers: list[str]          # 발동된 트리거
    generated_questions: list[dict]     # 생성된 질문
    coverage_status: dict[str, float]   # 토픽별 커버리지
    kg_snapshot_id: str                 # KG 참조 ID

# LiveAgent StateGraph 흐름:
#
# [transcript_received]
#      ↓
# [analyze_utterance] → 키워드 추출, 벡터 검색, 그래프 탐색
#      ↓
# [evaluate_triggers] → 모순 감지, 모호 답변, 토픽 미커버 체크
#      ↓ (트리거 발동 시에만)
# [generate_questions] → Groq LLM + 그래프 도구 호출
#      ↓
# [update_coverage] → 토픽 커버리지 갱신, 스코어 업데이트
#      ↓
# [emit_to_client] → WebSocket으로 클라이언트에 전송
```

### Worker → 그래프 주입 패턴 (통합 도구 인터페이스)

v5.0 분석과 Live 면접이 **동일한 그래프 도구 세트**를 사용:

```python
# 서버 (v5.0 분석) — NetworkX 기반
@tool
def get_skill_evidence(candidate_id: str, skill_name: str) -> dict:
    """서버: NetworkX 그래프에서 스킬 증거 탐색"""
    graph = networkx_adapter.get_graph(candidate_id)
    return graph.get_skill_evidence(skill_name)

# 클라이언트 (Live 면접) — graphology 기반
// desktop/src/services/graph-tools.ts
export const getSkillEvidence = (skillName: string): SkillEvidence => {
  // 동일한 로직, graphology 구현
  return graphStore.getSkillEvidence(skillName);
};
```

**핵심**: Port/Adapter 패턴으로 `GraphQueryEngine` 인터페이스를 정의하고, 서버(NetworkX)와 클라이언트(graphology)가 각각 Adapter를 구현. LLM 도구 호출 시 동일한 시그니처로 작동.

### Worker 간 교차 참조 — Graph-First 패턴

```python
# 기존: Worker가 독립적으로 JSON 저장 → 교차 참조 불가
# 개선: Worker가 KG에 노드/엣지 추가 → 후속 Worker가 그래프 쿼리로 선행 결과 활용

# SkillExtractor가 CleanerWorker의 blame 결과를 그래프에서 바로 참조:
class SkillExtractor(BaseWorker):
    async def execute(self, state: AnalysisState) -> AnalysisState:
        kg = self.kg_adapter.get_graph(state["candidate_id"])

        for repo_node in kg.get_nodes(type="Repo"):
            # 선행 Worker가 이미 추가한 blame 데이터를 그래프에서 조회
            blame = kg.get_edge_data(state["candidate_id"], repo_node, rel="BLAME_RATIO")
            techs = kg.get_neighbors(repo_node, rel="USES_TECH")

            for tech in techs:
                # 코드 + 이력서 + LinkedIn 교차 검증
                resume_claims = kg.get_nodes(type="Claim", filter={"skill": tech})
                linkedin_data = kg.get_nodes(type="Experience", filter={"tech": tech})

                proficiency = self._calculate_proficiency(blame, resume_claims, linkedin_data)
                kg.add_edge(state["candidate_id"], f"skill:{tech}",
                           rel="HAS_SKILL", proficiency=proficiency,
                           evidence_sources=["git", "resume", "linkedin"])
```

### InterviewSession 상태 머신 (Template Method)

```python
# domain/models/interview_session.py

class InterviewSession(ABC):
    """면접 세션 생명주기 — Template Method 패턴"""

    status: SessionStatus  # CREATED → PREPARING → READY → LIVE → ENDING → COMPLETED

    async def run(self):
        await self.prepare()       # 추상: 서브클래스가 구현
        self.status = "READY"
        await self.start()         # 추상: 오디오 캡처 시작
        self.status = "LIVE"
        await self._monitor()      # 공통: 토픽 커버리지 추적, 종료 조건 체크
        self.status = "ENDING"
        await self.finalize()      # 추상: 데이터 업로드, 스코어카드 생성
        self.status = "COMPLETED"

class OnlineInterviewSession(InterviewSession):
    """온라인(화상) 면접 — Channel Muxing"""
    async def prepare(self):
        self.audio_config = ChannelMuxConfig(mic="left", system="right")
        await self.sync_kg_to_local()
        await self.load_deck()

class OfflineInterviewSession(InterviewSession):
    """오프라인(대면) 면접 — AI 화자분리"""
    async def prepare(self):
        self.audio_config = DiarizationConfig(mic_only=True, diarization="deepgram")
        await self.sync_kg_to_local()
        await self.load_deck()
```

### Command Pattern — 면접관 액션

```python
# domain/commands/interview_commands.py

class InterviewCommand(ABC):
    """면접관 액션을 Command로 캡슐화 — Undo/Redo + 로깅"""
    async def execute(self) -> None: ...
    async def undo(self) -> None: ...

class RequestNewQuestionCommand(InterviewCommand):
    """면접관이 '다른 질문 보여줘' 버튼 클릭"""
    async def execute(self):
        context = self.build_context(self.session)
        questions = await self.llm.generate_probing(context)
        self.event_bus.emit('llm:question-ready', questions)
        self.log_action("MANUAL_QUESTION_REQUEST", questions)

class MarkQuestionUsedCommand(InterviewCommand):
    """면접관이 질문 카드를 '사용함' 처리"""
    async def execute(self):
        self.card.status = "USED"
        self.card.asked_at = datetime.utcnow()
        self.coverage_tracker.update(self.card.topic_id)
        self.event_bus.emit('coverage:updated', self.coverage_tracker.status)

class EndInterviewCommand(InterviewCommand):
    """면접 종료 → 미검증 역량 경고 → 확인 후 종료"""
    async def execute(self):
        uncovered = self.coverage_tracker.get_uncovered()
        if uncovered:
            confirm = await self.ui.show_warning(uncovered)
            if not confirm:
                return  # 계속 진행
        await self.session.finalize()
```

---

## 9. 데스크탑 앱 상세 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                 Electron v33+ App                    │
│                                                      │
│  ┌─ Renderer Process (React + Vite) ──────────────┐ │
│  │  Silero VAD (WASM) | graphology | Dashboard UI │ │
│  │              EventBus 연결                       │ │
│  └───────────────────┬────────────────────────────┘ │
│                      │ IPC                           │
│  ┌───────────────────┴────────────────────────────┐ │
│  │          Main Process (Node.js)                 │ │
│  │  Audio Manager | LanceDB v0.26 | Deepgram WS   │ │
│  └───────┬─────────────────────────────────────────┘ │
│          │ stdio pipe                                │
│  ┌───────┴─────────────────────────────────────────┐ │
│  │     Child Process (Native Audio Binary)          │ │
│  │  macOS: ScreenCaptureKit / CoreAudio             │ │
│  │  출력: PCM Stereo (L=Mic, R=System)              │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

**온라인 vs 오프라인 면접:**

| 모드 | 화자 분리 방식 | 오디오 소스 |
|------|---------------|------------|
| 온라인 (화상) | Channel Muxing (L=Mic, R=System) | 마이크 + 시스템 사운드 |
| 오프라인 (대면) | Deepgram AI Diarization | 마이크만 |

---

## 10. 디자인 패턴 & 추상화 전략

> **sabyun**: 아키텍쳐 설계할때 디자인패턴 최대한 이용하고 추상화를 최대화로 해서(효율적인) 로직이 바뀌거나 추가되거나 할때 많은 로드가 걸리지 않도록 설계단에서부터 해당 염두해두고 설계하면 좋을것같아.

### 6계층 추상화 레이어

| 레이어 | 패턴 | 역할 |
|--------|------|------|
| Layer 6: UI | Observer | EventBus 구독만, 직접 의존 없음 |
| Layer 5: Application | Mediator | 파이프라인 조율, 컴포넌트 간 직접 참조 금지 |
| Layer 4: Domain | Strategy | 면접 모드별/분석 전략별 교체 가능 |
| Layer 3: Service | Template Method | 공통 흐름 고정, 세부 단계만 Override |
| Layer 2: Port | Port/Adapter | 모든 외부 의존을 Interface로 차단 |
| Layer 1: Adapter | Adapter | 실제 구현체, 교체 시 여기만 수정 |

### Port/Adapter 적용 예시

```python
# shared/ports/stt.py — Port 예시
class STTProvider(Protocol):
    async def connect(self, config: STTConfig) -> None: ...
    async def stream(self, audio: AsyncIterator[AudioChunk]) -> AsyncIterator[TranscriptSegment]: ...
    async def disconnect(self) -> None: ...

# backend/adapters/stt/deepgram.py — Adapter 예시
class DeepgramSTTAdapter:
    """Deepgram Nova-3 구현체. 교체 대상은 이 파일뿐."""
```

**교체 가능성 있는 Adapter 목록:**

| Port | 현재 Adapter | 교체 후보 | 영향 범위 |
|------|-------------|----------|----------|
| STTProvider | DeepgramAdapter | AssemblyAI, ElevenLabs | Adapter 파일 1개 |
| LLMProvider | GroqAdapter (실시간) | Cerebras, Together AI | Adapter 파일 1개 |
| VectorStore | LanceDBAdapter | ChromaDB | Adapter 파일 1개 |
| GraphStore | NetworkXAdapter (서버) | Neo4j | Adapter 파일 1개 |
| BillingPort | FreeTierAdapter | StripeAdapter | Adapter 파일 1개 |

---

## 11. SOLID 원칙 매핑

> **sabyun**: SOLID 원칙도 추가해서 해당 방향으로 진행하자.

| 원칙 | 적용 | 구체적 규칙 |
|------|------|------------|
| **S** — Single Responsibility | Adapter 1개 = 외부 서비스 1개 | `DeepgramAdapter`가 VAD까지 담당 금지 |
| **O** — Open/Closed | Port 수정 금지, 새 Adapter 추가만 | `STTProvider` Protocol 확정 후 시그니처 변경 금지 |
| **L** — Liskov Substitution | 모든 Adapter는 Port 계약 100% 충족 | 런타임 검증으로 LSP 위반 즉시 실패 |
| **I** — Interface Segregation | 큰 인터페이스 금지, 역할별 분리 | `LLMProvider` → `Completable`, `Streamable`, `ToolCallable`, `Embeddable` 분리 |
| **D** — Dependency Inversion | 상위 레이어는 Port에만 의존 | `Pipeline`이 `DeepgramAdapter` 직접 import 금지 |

**ISP 적용 — LLM 인터페이스 분리:**

```python
class Completable(Protocol):     # 단순 텍스트 생성
class Streamable(Protocol):      # 스트리밍 (실시간 UI용)
class ToolCallable(Protocol):    # 도구 호출 (Agentic Graph RAG용)
class Embeddable(Protocol):      # 임베딩 (벡터 검색용)

# Groq: Completable + Streamable + ToolCallable (임베딩 미지원)
# Kimi K2.5: Completable + ToolCallable + Embeddable (스트리밍 불필요)
```

---

## 12. 실시간 데이터 플로우

면접 시작 → 질문 생성까지 7단계, Pipeline 패턴으로 각 단계 독립 교체 가능:

```
Stage 1: Audio Capture (Child Process) — PCM Stereo 48kHz
    ↓ IPC stdio pipe
Stage 2: Audio Normalization (Main Process) — 리샘플링 16kHz + 노이즈 게이트
    ↓ IPC → Renderer
Stage 3: VAD Gate (Renderer WASM) — Silero VAD, 발화 구간만 통과
    ↓ EventBus
Stage 4: STT (Main → Deepgram WebSocket) — 실시간 전사 + 화자 태그
    ↓ IPC → Renderer
Stage 5: Hybrid RAG (Renderer) — LanceDB 벡터 + graphology 그래프
    ↓ EventBus
Stage 6: LLM Question Gen (Renderer → Groq API) — 꼬리질문 동적 생성
    ↓ EventBus
Stage 7: UI Update (React) — 질문 카드 + 프로그레스바 갱신
```

**레이턴시 버짓 (E2E < 700ms):**

| Stage | 목표 | 비고 |
|-------|------|------|
| Audio → Main | <10ms | IPC |
| Normalization | <5ms | |
| VAD | <1ms | WASM |
| STT (Deepgram) | <300ms | 네트워크 |
| Hybrid RAG | <60ms | 로컬 |
| LLM (Groq) | <300ms | TTFT |
| UI Render | <16ms | React |
| **합계** | **<692ms** | |

---

## 13. 면접관 대시보드 UI/UX

> **sabyun**: 면접관이 보는 화면구성은 어떻게 돼? 보여지는 방법과 어떤식으로 어떤 정보가 보여지는지도 확인해보자.

### 윈도우 구성

| 항목 | 설정 |
|------|------|
| 기본 크기 | **420x900px** (좁고 긴 사이드바형) |
| 위치 | 화면 우측 고정 (드래그 이동 가능) |
| Always on Top | 토글 (기본 ON) |
| 테마 | 다크/라이트 (기본 다크 — 시선 부담 감소) |

### 면접 3단계별 화면 전환

```
[대기] ──시작──▶ [라이브] ──종료──▶ [리포트]
```

### 라이브 면접 화면 — 3개 존

- **Zone A** (상단 40px): 상태 바 — 녹음 상태, 경과 시간, STT 상태, 모드
- **Zone B** (중앙 ~65%): 메인 질문 카드 영역 — AI 추천 카드 + 사용 완료 카드
- **Zone C** (하단 ~35%): 커버리지 + 미니 전사 — 토픽 프로그레스바, 실시간 대화 요약

### 질문 카드 우선순위 색상

| 우선순위 | 색상 | 용도 |
|----------|------|------|
| 빨강 | `#EF4444` | 모순 발견 — 즉시 확인 필요 |
| 주황 | `#F59E0B` | 미검증 핵심 역량 — 확인 권장 |
| 파랑 | `#3B82F6` | 일반 심화 질문 |
| 초록 | `#10B981` | 실시간 꼬리질문 (대화 맥락) |

---

## 14. KG 스키마 & Graph-First 파이프라인

### 노드 타입

| 노드 | 생성 시점 |
|------|----------|
| Candidate | Identity Resolution Worker |
| Skill | Resume + LinkedIn + Code 분석 시 |
| Company / Position | Resume/LinkedIn 파싱 시 |
| Repo / Tech | GitHub 수집 + AST 분석 시 |
| Claim / Evidence | 이력서/코드 분석 시 |
| JD / JDRequirement | JD 파싱 시 |
| InterviewSegment | Live 면접 STT 시 |

### 핵심 엣지

| 엣지 | From → To | 의미 |
|------|-----------|------|
| HAS_SKILL | Candidate → Skill | 보유 스킬 |
| EVIDENCED_BY | Skill → Evidence | 스킬 증거 연결 |
| CLAIMED | Candidate → Claim | 주장/기재 사항 |
| SUPPORTS / CONTRADICTS | Evidence → Claim | 증거 검증 |
| REQUIRES | JD → JDRequirement | JD 요구사항 |
| VERIFIED_BY | JDRequirement → InterviewSegment | 면접 중 검증됨 |

---

## 15. 2계층 질문 시스템

> **sabyun**: 면접 라이브때 실시간으로 만드는것보다 미리 주제별로 몇개 질문 만들어놓고 그 기반 및 실시간으로 질문 생성하는게 좋지않을까?

### Layer 1: Question Deck (사전 생성)

- 면접 시작 전, v5.0 KG 분석 결과 기반으로 주제별 질문 카드 미리 생성
- 서버에서 Kimi K2.5로 깊이 있는 분석
- 클라이언트에 동기화 → 즉시 사용 가능, 0ms 지연
- 네트워크 장애 시에도 Deck으로 면접 진행 가능

### Layer 2: Real-time Probing (실시간 보조)

- 면접 대화 흐름에 따라 동적 생성 (클라이언트, Groq)
- Deck에 없는 꼬리질문, 새로운 모순점, 맥락 기반 심화
- 대화 맥락 반영, 예측 불가 상황 대응

### Deck 구조

```python
class QuestionDeck:
    groups: list[TopicGroup]       # 주제별 그룹 (5-8개)
    red_flags: list[QuestionCard]  # 모순/위험 신호 (별도 분리)
    ice_breakers: list[QuestionCard]  # 오프닝 질문 (1-2개)

class TopicGroup:
    topic: str              # "MSA 경험" 등
    cards: list[QuestionCard]  # 주제별 2-3개 질문
    status: TopicStatus     # PENDING / PARTIAL / VERIFIED
```

---

## 16. 백엔드 확장 설계

v5.0 분석 백엔드와 Live 면접 백엔드가 **하나의 FastAPI 앱** 안에 DDD 계층으로 공존:

```
backend/src/
├── domain/           # 순수 비즈니스 로직
│   ├── models/       # candidate, knowledge_graph, question_deck, interview_session, scorecard
│   ├── strategies/   # question/, scoring/
│   ├── workers/      # v5.0 분석 Worker들
│   └── services/     # deck_generator, live_analyzer, report_builder
├── application/      # 유스케이스 (CQS 패턴)
│   ├── commands/     # start_analysis, generate_deck, start_interview...
│   ├── queries/      # get_candidate, get_deck, get_scorecard...
│   └── graphs/       # LangGraph StateGraph 정의
├── infrastructure/   # Adapter 구현
│   ├── adapters/     # stt/deepgram, llm/kimi+groq, graph/networkx...
│   └── persistence/  # PostgreSQL Repository
└── interface/        # API + WebSocket
    └── api/v1/       # candidates, analysis, decks, interviews, reports
```

---

## 17. 에러 처리 체계

> **sabyun**: 에러 처리 로직을 확실히 구조화하고 로그도 확실하게. 하나의 잡이나 요청마다 UUID를 부여, 어디에서 어떻게 문제가 발생했는지 확실한 에러처리 로직이 있으면 좋겠어. 구글에서 예외처리 하는 방식 확인해보고.

### 핵심 원칙 (Google AIP-193 기반)

| 원칙 | 적용 |
|------|------|
| 모든 요청에 Correlation ID | UUID v7 (시간순 정렬 가능) |
| 에러 계층 상속 | BaseError → DomainError → 구체 에러 |
| Partial Error 금지 | 성공 or 실패 명확 |
| reason + domain 쌍 불변 | 같은 에러 = 같은 (reason, domain) |

### Correlation ID 전파

```
Client → X-Correlation-ID → 미들웨어 → ContextVar
    → API Layer [uuid] → Application [uuid] → Domain [uuid] → Infrastructure [uuid]
    → Response + X-Correlation-ID
```

---

## 18. 자기 설명적 에러 코드

> **sabyun**: 에러코드만으로 찾아보면 어떤 에러인지 어디서 나는 에러인지를 찾을 수 있도록 하면 좋을것같은데. 좀더 최신 에러처리 기법 없나?

### 조사 결과 — 3가지 최신 기법 종합

| 출처 | 기법 | 적용 |
|------|------|------|
| **RFC 9457** (2024 IETF) | Problem Details — `type` URI + 확장 필드 | 에러 응답 포맷 표준 |
| **Stripe** | 계층적 코드 + `doc_url` | 에러 코드 네이밍 |
| **ErrorPrism** (ByteDance 2025) | Error Wrapping Chain | 근본 원인 체인 |

### 에러 코드 형식: `{도메인}-{심각도}-{계층}-{순번}`

```
JL-2-F-0020
│   │  │  │
│   │  │  └── 순번 (4자리)
│   │  └───── 계층: I(Interface) A(Application) D(Domain) F(inFrastructure) C(Client)
│   └──────── 심각도: 1=Critical, 2=High, 3=Medium, 4=Low
└──────────── 도메인: JA(analysis), JL(live), JR(report), JS(sync), JC(common)
```

### 에러 코드 예시

| 코드 | 이름 | 설명 |
|------|------|------|
| JA-2-F-0002 | GITHUB_CLONE_FAILED | 레포 클론 실패 |
| JA-2-F-0005 | KG_CONSTRUCTION_FAILED | Knowledge Graph 구축 실패 |
| JL-1-F-0010 | STT_CONNECTION_LOST | STT WebSocket 연결 끊김 |
| JL-2-F-0020 | LLM_TIMEOUT | 실시간 LLM 응답 시간 초과 |
| JL-3-D-0001 | ANALYSIS_NOT_COMPLETED | 사전 분석 미완료 |

---

## 19. Sentry + Infisical 통합

> **sabyun**: 센트리도 적용, Infisical 환경변수 관리도 다른곳에서 셀프호스팅하는거 사용해줘.

### 관측성 스택

```
[외부 셀프호스팅 서버]
  Sentry Self-Hosted (sentry.jittda.io) — 에러/성능 모니터링
  Infisical Self-Hosted (secrets.jittda.io) — 시크릿/환경변수 관리
      ↓
  Backend (sentry-sdk + infisical-sdk)
  Desktop (Sentry Electron SDK + infisical-node-sdk)
```

### Sentry ↔ 에러 코드 연동

- `before_send` 훅으로 BaseError 발생 시 에러 코드 메타데이터 자동 주입
- Sentry Fingerprint = 에러 코드 → 같은 에러 자동 그룹핑
- 에러 체인(Error Chain) → Sentry breadcrumbs로 전파 경로 시각화

### Infisical 통합

- 앱 시작 시 `SecretsManager`가 Infisical에서 전체 시크릿 fetch
- `.env`에는 접속 정보 3개만: `INFISICAL_HOST`, `INFISICAL_CLIENT_ID`, `INFISICAL_CLIENT_SECRET`
- 구조화 로깅: structlog JSON + correlation_id 자동 주입 + layer/component 자동 감지

---

## 20. DB 스키마

15+ 테이블, PostgreSQL 16 + pgvector + pg_trgm:

```
candidates ──▶ knowledge_graphs ──▶ question_decks
     │                                    │
     └────────▶ interview_sessions ◀──────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
  transcripts     card_events     scorecards ──▶ reports
```

핵심 테이블: `candidates`, `job_descriptions`, `knowledge_graphs`, `question_decks`, `question_cards`, `interview_sessions`, `transcripts`, `card_events`, `scorecards`, `scorecard_competencies`, `reports`, `promo_codes`, `user_credits`, `credit_transactions`

---

## 21. 면접 결과물 전체 맵

> **sabyun**: 우리가 면접으로 최종적으로 얻을 수 있는 결과물은 뭐야?

### 3단계에서 쌓이는 데이터

```
[v5.0 사전 분석]          [Live 면접]              [사후 종합]
"이 사람이 뭘 했는가"    "이 사람이 뭘 아는가"    "이 사람을 뽑을 것인가"
```

### 1단계: v5.0 사전 분석 수치

- JD 매칭률, 코드 품질 점수, AI 코드 비율, 표절 의심도, 기여 진정성, 스킬별 증거 강도, 모순점 목록, 경력 일관성

### 2단계: Live 면접 수치

- 역량별 커버리지, 토픽별 검증 상태, 답변 깊이 지표, 모순 검증 결과, 질문 사용 통계, 면접 시간 배분, 발화 비율, 응답 시간 패턴

### 3단계: 최종 산출물

- **종합 스코어카드**: 역량별 1.0-5.0 점수 + 신뢰도(🟢/🟡/🔴) + 권장 액션(HIRE/NEXT_ROUND/REJECT)
- **증거 기반 평가**: 코드 + 면접 발화 교차 검증
- **D3.js 시각화**: Radar Chart(역량 비교), Heatmap(시간대별 답변 품질), Treemap(스킬 분포)
- **전체 전사본**: 타임스탬프 + 화자 태그 + AI 주석

---

## 22. Phase 로드맵 & Linear 티켓

### 전체 로드맵 (14주, 69개 티켓)

```
Phase 0(1주) → Phase 1(1.5주) → Phase 2(2.5주) → Phase 3(2주) → Phase 4(2주) → Phase 5(2.5주) → Phase 6(2주)
스캐폴딩       도메인 계층       인프라-분석       인프라-Live      애플리케이션       데스크탑앱        웹+통합
```

| Phase | 핵심 산출물 | 티켓 수 |
|-------|-----------|---------|
| **Phase 0** | 모노레포 구조, Docker, DB, CI, Sentry, Infisical | 8개 |
| **Phase 1** | 에러 코드, Port 전체 정의, KG 모델, DI 컨테이너 | 10개 |
| **Phase 2** | Git/GitHub 어댑터, AST, 복잡도, 표절, LLM, pgvector | 8개 |
| **Phase 3** | 오디오 캡처, VAD, STT, LanceDB, graphology, Groq | 12개 |
| **Phase 4** | LangGraph HMAS, DeckGenerator, LiveSession, WebSocket | 10개 |
| **Phase 5** | Electron 앱, 대시보드 UI, 스코어카드, 설정 | 11개 |
| **Phase 6** | 웹 결과 페이지, D3.js 차트, E2E 테스트, 통합 | 10개 |

---

## 23. 프로모 코드 + 결제 준비

> **sabyun**: 추후 결제를 넣을수도 있고 프로모 코드같은걸로 몇회 무료사용 이런거 추가할 수 있도록 하면 좋을것같아.

### 아키텍처

```
PromoCode System (지금 구현) + UsageCredit System (지금 구현) + Payment System (추후)
                                       │
                             BillingPort (인터페이스)
                                       │
                       ┌───────────────┴───────────────┐
                       ▼                               ▼
                FreeTierAdapter                  StripeAdapter
                (지금 — 프로모 코드만)            (추후 — 결제 연동)
```

### 프로모 코드 도메인 모델

```python
class PromoCode:
    code: str                      # "JITTDA-BETA-2026"
    credit_type: CreditType        # ANALYSIS | INTERVIEW | BOTH
    credits_granted: int           # 부여 크레딧 수
    max_redemptions: int | None    # 전체 최대 사용 횟수
    max_per_user: int              # 유저당 최대 사용 횟수
    valid_from: datetime
    valid_until: datetime | None
```

---

## 24. 최종 산출물

### 생성된 파일

| 파일 | 내용 | 크기 |
|------|------|------|
| `docs/plans/2026-02-17-jittda-live-design.md` | 전체 시스템 설계서 | ~900줄, 13개 섹션 |
| `docs/plans/2026-02-17-jittda-live-mvp-prd.md` | MVP 최소 요구사항 정의서 | ~1,310줄, 10개 섹션 + 부록 4개 |
| `docs/plans/2026-02-17-jittda-live-wireframes.md` | 페이지별 와이어프레임 | ~900줄, 13개 페이지 |

### Linear 프로젝트

- **프로젝트**: Jittda Live
- **마일스톤**: Phase 0 ~ Phase 6 (7개)
- **이슈**: JIT-141 ~ JIT-209 (69개, 99개 의존성 관계)
- **기존 이슈**: JIT-128 ~ JIT-140 (13개, Cancelled 처리)

### Git

- **브랜치**: `docs/jittda-live-design`
- **커밋**: 3파일, 2,740 insertions
- **PR**: #341 → main 머지 완료

---

## 핵심 설계 결정 요약

| # | 결정 | 근거 | sabyun 피드백 |
|---|------|------|--------------|
| 1 | 통합 Monorepo | v5.0 미구현 + 1인 개발 → MSA 과잉 | "v5.0은 아직 구현 안 했어" |
| 2 | KG 하이브리드 | PostgreSQL만으로 다중 관계 추론 불가 | "postgres만으로는 힘들것같아" |
| 3 | Graph-First 파이프라인 | 분석하면서 동시에 KG 구축 → 일석이조 | "분석할때 바로바로 그래프에 주입하면 되지않나?" |
| 4 | Agentic Graph RAG | LLM이 도구로 그래프 직접 탐색 → 토큰 69% 절감 | "그래프 노드 탐색 툴로 호출해서 작업" |
| 5 | 디자인 패턴 최대 활용 | 6계층 추상화 + 7개 패턴 | "디자인패턴 최대한 이용하고 추상화를 최대화" |
| 6 | SOLID 원칙 적용 | ISP로 LLM 인터페이스 분리, LSP 런타임 검증 | "SOLID 원칙도 추가" |
| 7 | 2계층 질문 시스템 | Deck(사전) + Real-time(보조) | "미리 주제별로 질문 만들어놓고" |
| 8 | 자기 설명적 에러 코드 | RFC 9457 + Stripe + ErrorPrism | "에러코드만으로 어떤에러인지 찾을수 있도록" |
| 9 | Sentry + Infisical | 셀프호스팅 관측성 + 시크릿 관리 | "센트리도 적용, Infisical도" |
| 10 | 프로모 코드 선행 | BillingPort 추상화 → 추후 Stripe 교체 | "결제는 추후, 프로모 코드는 지금" |
