# Jittda Live — 실시간 AI 면접 가이드 시스템 설계서

> 작성일: 2026-02-17 | 상태: 설계 완료
> 기반: Jittda Sniper v5.0 Clean Slate Reconstruction 확장
> 원칙: "면접관의 인지 부하 최소화 + 객관적 평가 보조"

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [시스템 아키텍처](#2-시스템-아키텍처)
3. [설계 패턴 & 추상화 전략](#3-설계-패턴--추상화-전략)
4. [실시간 면접 데이터 플로우](#4-실시간-면접-데이터-플로우)
5. [Knowledge Graph & Agentic Graph RAG](#5-knowledge-graph--agentic-graph-rag)
6. [2-Layer 질문 시스템](#6-2-layer-질문-시스템)
7. [면접관 대시보드 UI/UX](#7-면접관-대시보드-uiux)
8. [백엔드 확장 설계](#8-백엔드-확장-설계)
9. [에러 처리 시스템](#9-에러-처리-시스템)
10. [데이터 모델 / DB 스키마](#10-데이터-모델--db-스키마)
11. [면접 결과 산출물](#11-면접-결과-산출물)
12. [프로모 코드 & 결제 준비](#12-프로모-코드--결제-준비)
13. [Phase 로드맵](#13-phase-로드맵)

---

## 1. Executive Summary

기존 Jittda Sniper v5.0(웹 기반 면접 질문 생성기)을 확장하여 **실시간 AI 면접 가이드 데스크탑 앱**을 추가한다.

### 핵심 가치
- **2-Layer 질문 시스템**: Pre-generated Deck(0ms) + Real-time Probing(trigger-based)
- **AI 면접 참모**: 면접관이 대화에 집중하면서도 객관적 평가 데이터를 축적
- **Local-First**: 면접 중 네트워크 불안정해도 Deck 질문과 벡터 검색은 로컬에서 동작
- **Evidence-based Scoring**: 모든 점수에 코드/면접 발언 근거 첨부

### 통합 모노레포 구조

```
jittda/
├── backend/          # FastAPI + LangGraph (기존 v5.0 확장)
│   └── src/
│       ├── domain/           # 비즈니스 로직 (순수 Python)
│       ├── infrastructure/   # 외부 연동 (Adapter)
│       ├── application/      # LangGraph, 서비스
│       └── interface/        # FastAPI, WebSocket
├── desktop/          # Electron 33+ 데스크탑 앱
│   ├── main/         # Main Process (Node.js)
│   ├── renderer/     # Renderer Process (React)
│   ├── preload/      # Preload Scripts (IPC)
│   └── native/       # OS별 네이티브 오디오 바이너리
├── frontend/         # Vite + React 19 (웹)
├── shared/           # 공유 타입, 유틸, 프로토콜
└── infra/            # Docker Compose, init.sql, Makefile
```

---

## 2. 시스템 아키텍처

### 2.1 Electron 프로세스 모델

```
┌─────────────────────────────────────────────────────────┐
│                    Electron App                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Child Process (Native Audio)                      │   │
│  │ - macOS: ScreenCaptureKit / CoreAudio             │   │
│  │ - Windows: WASAPI Loopback                        │   │
│  │ - Output: Stereo PCM (Mic=L, System=R)           │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │ Raw PCM Stream                     │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │ Main Process (Node.js)                            │   │
│  │ - OS 판별 (process.platform)                      │   │
│  │ - Child Process 생명주기 관리                      │   │
│  │ - IPC → Renderer 스트림 전달                       │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │ IPC Channel                        │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │ Renderer Process (React + Zustand)                │   │
│  │ ┌─────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐ │   │
│  │ │Silero   │ │Deepgram  │ │LanceDB │ │Groq LLM │ │   │
│  │ │VAD(WASM)│ │Nova-3 STT│ │Local DB│ │API      │ │   │
│  │ └─────────┘ └──────────┘ └────────┘ └─────────┘ │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 2.2 기술 스택

| 계층 | 기술 | 버전 | 역할 |
|------|------|------|------|
| Desktop Shell | Electron | 33+ | 크로스플랫폼 데스크탑 |
| Audio Capture | electron-audio-loopback | latest | OS 네이티브 오디오 |
| VAD | Silero VAD (@ricky0123/vad) | WASM | 음성 감지 <1ms |
| STT | Deepgram Nova-3 | Streaming | 한국어 WER 7-16% |
| Local Vector DB | LanceDB | 0.26+ | 임베딩 검색 <100ms |
| KG Client | graphology | 0.25+ | 인메모리 그래프 <5ms |
| KG Server | NetworkX | 3.4+ | 그래프 구축/분석 |
| Real-time LLM | Groq (Llama 3.3 70B) | API | TTFT ~0.14s |
| Server LLM | Kimi K2.5 | Instructor | 분석/Deck 생성 |
| State | Zustand | 5+ | 전역 상태 관리 |
| Event Bus | mitt | 3+ | Pub/Sub 이벤트 |
| Backend | FastAPI | 0.115+ | REST + WebSocket |
| Orchestration | LangGraph | 1.0.8+ | HMAS 에이전트 |
| DB | PostgreSQL 16 + pgvector | — | 영구 저장소 |
| Cache | Redis 7 | — | 세션, 캐시 |
| Error Monitor | Sentry (self-hosted) | — | 에러 추적 |
| Secrets | Infisical (self-hosted) | — | 환경변수 관리 |

### 2.3 클라이언트 설계 패턴 3원칙

1. **Local-First (오프라인 퍼스트)**: 서버는 동기화 노드. KG/Deck/벡터 데이터를 로컬에 캐시하여 네트워크 불안정 시에도 동작
2. **멀티채널 오디오 파이프라이닝 (Channel Muxing)**: 마이크=Ch0(L), 시스템=Ch1(R) 물리적 분리로 화자 인식률 100%
3. **Pub/Sub (Observer) 이벤트 버스**: 오디오/VAD/STT/LLM 이벤트를 전역 버스에 발행, UI가 필요한 이벤트만 구독

---

## 3. 설계 패턴 & 추상화 전략

### 3.1 7대 설계 패턴

#### 1) Port/Adapter (Hexagonal Architecture)
모든 외부 의존성을 Port(Protocol) 인터페이스로 추상화. 변경 영향 반경: 최대 1파일.

```python
# Port 정의 (domain 계층)
class STTProvider(Protocol):
    async def connect(self, config: STTConfig) -> None: ...
    async def stream(self, audio: AsyncIterator[AudioChunk]) -> AsyncIterator[TranscriptSegment]: ...
    async def disconnect(self) -> None: ...

# Adapter 구현 (infrastructure 계층)
class DeepgramSTTAdapter:
    async def connect(self, config: STTConfig) -> None:
        self._client = DeepgramClient(config.api_key)
```

#### 2) Strategy Pattern
알고리즘 교체 필요한 곳: QuestionStrategy, ScoringStrategy, AudioCaptureStrategy

```python
class QuestionStrategy(Protocol):
    def generate(self, context: InterviewContext) -> list[Question]: ...

class DeepTechnicalStrategy:
    def generate(self, context: InterviewContext) -> list[Question]: ...

class BehavioralStrategy:
    def generate(self, context: InterviewContext) -> list[Question]: ...
```

#### 3) Observer + EventBus (Pub/Sub)
비동기 이벤트 기반 아키텍처로 UI 렌더링 지연 방지.

```typescript
type Events = {
  'vad:speech-start': { channel: 'mic' | 'system'; timestamp: number };
  'vad:speech-end': { channel: 'mic' | 'system'; duration: number };
  'stt:transcript': { text: string; speaker: 'interviewer' | 'candidate'; isFinal: boolean };
  'llm:question-ready': { questions: ProbingQuestion[]; trigger: string };
  'coverage:updated': { topicId: string; percentage: number };
};
```

#### 4) Pipeline Pattern (Chain of Responsibility)
오디오→VAD→STT→분석→LLM 파이프라인을 단계별 프로세서 체인으로 구현.

```
AudioCapture → VADFilter → STTProcessor → AnalysisEngine → LLMGenerator
```

#### 5) Factory + Registry
런타임에 Adapter를 동적으로 생성/교체.

```python
@AdapterRegistry.register(STTProvider, "deepgram")
class DeepgramSTTAdapter: ...

@AdapterRegistry.register(STTProvider, "whisper")
class WhisperSTTAdapter: ...

# 사용
stt = AdapterRegistry.create(STTProvider, config.stt_provider)
```

#### 6) Template Method
면접 세션 생명주기의 골격 정의.

```python
class InterviewSession(ABC):
    async def run(self):
        await self.prepare()      # 추상
        await self.start()        # 추상
        await self._monitor()     # 공통 로직
        await self.finalize()     # 추상

class OnlineInterviewSession(InterviewSession):
    async def prepare(self):
        # 채널 분리 설정 (L=mic, R=system)

class OfflineInterviewSession(InterviewSession):
    async def prepare(self):
        # 마이크만 + 화자 분리 모드
```

#### 7) Command Pattern
면접관 액션을 Command 객체로 캡슐화 (Undo/Redo, 로깅).

```python
class RequestNewQuestionCommand(Command):
    async def execute(self):
        questions = await self.llm.generate_probing(self.context)
        self.event_bus.emit('llm:question-ready', questions)
```

### 3.2 SOLID 원칙 매핑

| 원칙 | 적용 | 예시 |
|------|------|------|
| **SRP** | 각 Adapter는 하나의 외부 시스템만 | DeepgramSTTAdapter = STT만 |
| **OCP** | 새 기능은 Adapter 추가로 확장 | WhisperAdapter 추가 시 기존 코드 변경 0 |
| **LSP** | 모든 Adapter는 Port Protocol 100% 준수 | 런타임 Protocol 검증 |
| **ISP** | LLM 인터페이스 분리 | Completable, Streamable, ToolCallable, Embeddable |
| **DIP** | 상위 모듈은 Port에만 의존 | FastAPI Depends() 의존성 주입 |

#### ISP — LLM 인터페이스 분리 상세

```python
class Completable(Protocol):
    async def complete(self, prompt: str) -> str: ...

class Streamable(Protocol):
    async def stream(self, prompt: str) -> AsyncIterator[str]: ...

class ToolCallable(Protocol):
    async def call_with_tools(self, prompt: str, tools: list[Tool]) -> ToolCallResult: ...

class Embeddable(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

# Groq: Completable + Streamable (실시간 질문 생성)
# Kimi K2.5: 4개 모두 구현 (분석/Deck 생성)
```

---

## 4. 실시간 면접 데이터 플로우

7단계 파이프라인, **E2E 레이턴시 < 700ms**:

```
Stage 1: Audio Capture (OS Native)
  └→ macOS: ScreenCaptureKit, Windows: WASAPI
  └→ Stereo PCM (48kHz, 16bit)
  └→ Channel Muxing: Mic=L(Ch0), System=R(Ch1)

Stage 2: VAD Filtering (Silero WASM, <1ms)
  └→ 무음 1.5초 이상 → 발화 종료 인식
  └→ 발화 구간만 다음 단계 전달

Stage 3: STT (Deepgram Nova-3 Streaming)
  └→ 채널별 독립 전사: Ch0=면접관, Ch1=지원자
  └→ Interim + Final 결과 스트리밍
  └→ 한국어 WER: 7-16%

Stage 4: Real-time Analysis
  └→ 키워드 추출 → LanceDB 벡터 검색 (<100ms)
  └→ graphology 그래프 탐색 (<5ms)
  └→ 토픽 커버리지 업데이트

Stage 5: Trigger Evaluation
  └→ 트리거 조건 평가:
     - 이력서 모순 감지
     - 모호한 답변 감지
     - 면접관 수동 요청
     - 토픽 미커버 경고

Stage 6: LLM Question Generation (Groq, ~300ms)
  └→ 트리거 발동 시에만 실행
  └→ 그래프 컨텍스트 + 프롬프트 → 꼬리 질문 ≤3개
  └→ 각 질문에 목적(왜 물어야 하는지) 간략 표시

Stage 7: UI Update (EventBus → React)
  └→ 카드 형태 우측 팝업
  └→ 토픽 커버리지 바 업데이트
  └→ 스코어카드 자동 기록
```

### 레이턴시 버짓

| 단계 | 목표 | 누적 |
|------|------|------|
| Audio → VAD | <1ms | 1ms |
| VAD → STT 전송 | ~10ms | 11ms |
| STT 처리 (Final) | ~300ms | 311ms |
| 분석 + 벡터 검색 | ~100ms | 411ms |
| 트리거 평가 | ~5ms | 416ms |
| LLM 생성 (Groq) | ~280ms | 696ms |

---

## 5. Knowledge Graph & Agentic Graph RAG

### 5.1 KG 노드/엣지 스키마

v5.0 분석 파이프라인의 각 Worker가 KG에 노드/엣지를 추가:

```
노드 타입:
  - Candidate: 지원자 기본 정보
  - Skill: 기술 스택 (canonical name)
  - Project: GitHub 프로젝트
  - Experience: 경력 사항
  - CodePattern: AST 분석 결과 (패턴, 복잡도)
  - Claim: 이력서/커버레터 주장
  - Evidence: 코드/커밋 근거

엣지 타입:
  - HAS_SKILL: Candidate → Skill (proficiency, source)
  - WORKED_ON: Candidate → Project (role, duration)
  - DEMONSTRATES: Project → CodePattern (frequency, quality)
  - SUPPORTS: Evidence → Claim (strength: strong/weak/contradicts)
  - REQUIRES: JD → Skill (priority: must/nice)
```

### 5.2 KG 구축 (서버 — NetworkX)

서버에서 v5.0 분석 완료 시 NetworkX로 KG 구축 → JSON 직렬화 → DB 저장.

### 5.3 Agentic Graph RAG (클라이언트 — graphology)

KG JSON을 Electron에 동기화 → graphology 인메모리 탐색.
LLM이 사용 가능한 **7개 그래프 탐색 도구**:

| # | 도구 | 설명 |
|---|------|------|
| 1 | `find_skill_evidence(skill)` | 특정 기술의 코드 근거 탐색 |
| 2 | `find_claim_contradictions(claim_id)` | 이력서 주장 모순 증거 |
| 3 | `find_uncovered_topics(jd_id)` | JD 미검증 항목 |
| 4 | `find_related_questions(topic_id)` | 토픽 관련 질문 후보 |
| 5 | `get_candidate_strength_weakness()` | 강점/약점 요약 |
| 6 | `find_project_depth(project_id)` | 프로젝트 기여도 심층 |
| 7 | `get_coverage_status()` | 현재 토픽 커버리지 |

→ 고정 컨텍스트 대신 LLM이 필요한 정보만 도구로 조회 **(69% 토큰 절감)**

---

## 6. 2-Layer 질문 시스템

### Layer 1: Pre-generated Question Deck

- v5.0 분석 완료 시 서버에서 자동 생성
- **Kimi K2.5 + KG** 기반 심층 분석
- 카테고리별 질문 묶음 (기술 / 행동 / 상황 / 프로젝트)
- 각 질문 포함: 텍스트, 의도, 예상 답변, 검증 포인트, 꼬리 질문 후보
- Electron 앱에 동기화 시 Deck 미리 로드 → **면접 중 0ms 지연**

### Layer 2: Real-time Probing (트리거 기반)

Deck에 없는 상황에서만 실행:

| 트리거 | 예시 |
|--------|------|
| 이력서 모순 감지 | 이력서="팀 프로젝트" ↔ 답변="혼자 구축" |
| 모호한 답변 | "Redis로 성능 높였다" → 구체적 수치 미제시 |
| 면접관 수동 요청 | "다른 질문 보여줘" 버튼 클릭 |
| 토픽 미커버 경고 | 시간 대비 미검증 역량 있음 |

- **Groq Llama 3.3 70B**로 ~300ms 이내 생성
- 최대 3개 bullet + 각 질문의 목적 1줄 표시

---

## 7. 면접관 대시보드 UI/UX

### 3-Stage View

1. **Pre-Interview (면접 대기)**: 지원자 요약, KG 시각화, Deck 미리보기, 모드 선택
2. **Live Interview (실시간)**: 3-Zone 레이아웃
3. **Post-Interview (면접 종료)**: 스코어카드, 타임라인, 증거 매핑

### Live Dashboard 3-Zone (420×900px)

```
┌──────────────────────────────────────┐
│ Zone A (상단 40px): 상태바            │
│ ⏱ 타이머 │ 🎙 오디오 │ ■■ 종료가능   │
├──────────────────────────────────────┤
│ Zone B (중앙 65%): 질문 카드          │
│                                      │
│ 🔴 모순 발견 [NOW]                   │
│ ┌────────────────────────────────┐   │
│ │ 이력서 "팀 프로젝트"             │   │
│ │ ↔ 면접 "혼자서 다 구축"          │   │
│ │ 추천: "캐시 무효화 전략은?"      │   │
│ │ [사용함 ✓] [다른 질문 ↻]        │   │
│ └────────────────────────────────┘   │
│                                      │
│ 📂 MSA 분산 환경 [미검증]            │
│ ┌────────────────────────────────┐   │
│ │ Q1. "서비스 분리 기준?"         │   │
│ │ 의도: MSA 설계 원칙 검증        │   │
│ └────────────────────────────────┘   │
├──────────────────────────────────────┤
│ Zone C (하단 25%): 커버리지+컨트롤   │
│ 기술 ■■■■■■■■□□ 78%               │
│ 소프트 ■■■■□□□□□□ 40%             │
│ [💬 질문 요청]      [⏹ 면접 종료]   │
└──────────────────────────────────────┘
```

### 카드 우선순위 색상

| 색상 | 의미 | 트리거 |
|------|------|--------|
| 🔴 긴급 | 이력서 모순 발견 | 이력서 vs 답변 불일치 |
| 🟡 주의 | 모호한 답변 | 구체적 수치/사례 부재 |
| 🟢 참고 | 심화 기회 | 흥미로운 답변, 추가 탐색 |

### 카드 상태 관리

| 상태 | 시각적 표현 |
|------|------------|
| 새 카드 (NOW) | 상단 삽입 + 슬라이드 + 펄스 애니메이션 |
| 활성 | 불투명, 풀 하이트 |
| 사용됨 (✓) | 반투명 50%, 높이 축소 |
| 3분 경과 | 자동 반투명 30% |
| 스와이프 | 슬라이드 아웃 제거 |

### 인터랙션 패턴

- "다른 질문 요청" → 팝업: [꼬리 질문] [주제 전환] [심화] 또는 직접 입력
- 카드 클릭 → 상세 근거 표시
- 토픽 항목 클릭 → 해당 토픽 Deck 질문으로 이동
- 면접 종료 확인 → 미검증 역량 경고 + [계속 진행] / [종료 및 분석]

---

## 8. 백엔드 확장 설계

### 8.1 REST API

```
POST   /api/v1/interviews/sessions              # 세션 생성
GET    /api/v1/interviews/sessions/{id}          # 세션 조회
PATCH  /api/v1/interviews/sessions/{id}          # 상태 변경
DELETE /api/v1/interviews/sessions/{id}          # 삭제

POST   /api/v1/interviews/sessions/{id}/deck     # Deck 생성
GET    /api/v1/interviews/sessions/{id}/deck     # Deck 조회

GET    /api/v1/interviews/sessions/{id}/scorecard    # 스코어카드 조회
PUT    /api/v1/interviews/sessions/{id}/scorecard    # 승인/수정

POST   /api/v1/promo-codes/validate              # 프로모 코드 검증
POST   /api/v1/promo-codes/redeem                # 사용

GET    /api/v1/credits/balance                   # 잔액
GET    /api/v1/credits/transactions              # 내역

GET    /api/v1/candidates/{id}/knowledge-graph   # KG JSON
```

### 8.2 WebSocket

```
WS  /ws/interview/{session_id}
  → Events:
    - session:started
    - stt:transcript          # 실시간 전사
    - analysis:trigger        # 트리거 발동
    - question:generated      # 새 질문
    - coverage:updated        # 토픽 업데이트
    - score:updated           # 점수 업데이트
    - session:ended
```

### 8.3 세션 생명주기

```
CREATED → PREPARING → READY → LIVE → ENDING → COMPLETED → ARCHIVED
```

---

## 9. 에러 처리 시스템

### 9.1 자기 설명적 에러 코드

형식: `{Domain}-{Severity}-{Layer}-{Sequence}`

```
JL = Jittda Live
Severity: 1=Critical, 2=Error, 3=Warning, 4=Info
Layer: F=Frontend, B=Backend, D=Desktop, I=Integration, A=Audio, S=STT
Sequence: 4자리

예시:
JL-1-A-0001  Critical, Audio     "마이크 접근 권한 거부"
JL-2-S-0010  Error, STT          "Deepgram 연결 타임아웃"
JL-3-B-0020  Warning, Backend    "KG 노드 수 제한 초과"
JL-2-I-0030  Error, Integration  "Groq API 응답 실패"
```

### 9.2 Error Chain (ErrorPrism)

```python
class BaseError(Exception):
    def __init__(self, error_code: str, message: str, **context):
        self.error_code = error_code
        self.message = message
        self.context = context
        self.correlation_id = context.get('correlation_id', str(uuid7()))
        self._chain: list[ErrorChainLink] = []

    def wrap(self, component: str, operation: str, context: str) -> "BaseError":
        self._chain.append(ErrorChainLink(
            component=component,
            operation=operation,
            context=context,
            timestamp=datetime.utcnow()
        ))
        return self
```

### 9.3 RFC 9457 Problem Details

```python
class ProblemDetail(BaseModel):
    type: str             # "https://jittda.io/errors/JL-2-S-0010"
    title: str            # "STT 연결 실패"
    status: int           # 503
    detail: str           # "Deepgram 응답 시간 초과 (5000ms)"
    instance: str         # "/interviews/sessions/abc-123"
    error_code: str       # "JL-2-S-0010"
    correlation_id: str   # UUID v7
    chain: list[dict]     # Error Chain
```

### 9.4 Sentry 통합 (Self-hosted)

```python
import sentry_sdk

def enrich_with_error_code(event, hint):
    exc = hint.get("exc_info", [None, None, None])[1]
    if isinstance(exc, BaseError):
        event["tags"]["error_code"] = exc.error_code
        event["tags"]["severity"] = exc.error_code.split("-")[1]
        event["tags"]["layer"] = exc.error_code.split("-")[2]
        event["fingerprint"] = [exc.error_code]
        event["contexts"]["error_chain"] = {
            "chain": [link.to_dict() for link in exc._chain]
        }
    return event

sentry_sdk.init(
    dsn=secrets.get("SENTRY_DSN"),
    before_send=enrich_with_error_code,
    traces_sample_rate=0.2,
    profiles_sample_rate=0.1,
)
```

### 9.5 Infisical 통합 (Self-hosted)

```python
from infisical_sdk import InfisicalSDKClient

class SecretsManager:
    def __init__(self):
        self._client = InfisicalSDKClient(host=os.environ["INFISICAL_HOST"])
        self._client.auth.universal_auth.login(
            client_id=os.environ["INFISICAL_CLIENT_ID"],
            client_secret=os.environ["INFISICAL_CLIENT_SECRET"]
        )
        self._cache: dict[str, str] = {}

    async def load_all(self, environment: str, path: str = "/backend") -> dict:
        secrets = self._client.secrets.list(
            project_id=os.environ["INFISICAL_PROJECT_ID"],
            environment=environment,
            secret_path=path
        )
        self._cache = {s.secret_key: s.secret_value for s in secrets}
        return self._cache

    def get(self, key: str) -> str:
        return self._cache[key]
```

`.env`는 3개만:
```
INFISICAL_HOST=https://secrets.jittda.io
INFISICAL_CLIENT_ID=...
INFISICAL_CLIENT_SECRET=...
```

---

## 10. 데이터 모델 / DB 스키마

### PostgreSQL 16 + pgvector

```sql
-- 면접 세션
CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    interviewer_id UUID NOT NULL REFERENCES users(id),
    jd_id UUID REFERENCES job_descriptions(id),
    mode VARCHAR(20) NOT NULL CHECK (mode IN ('online', 'offline')),
    status VARCHAR(20) NOT NULL DEFAULT 'created',
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    audio_config JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 면접 전사
CREATE TABLE interview_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id),
    speaker VARCHAR(20) NOT NULL CHECK (speaker IN ('interviewer', 'candidate')),
    text TEXT NOT NULL,
    start_time_ms INTEGER NOT NULL,
    end_time_ms INTEGER NOT NULL,
    confidence FLOAT,
    is_final BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 질문 Deck
CREATE TABLE question_decks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id),
    category VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    intent TEXT,
    expected_answer TEXT,
    verification_points JSONB,
    follow_up_candidates JSONB,
    priority INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    asked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 실시간 생성 질문
CREATE TABLE realtime_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id),
    trigger_type VARCHAR(50) NOT NULL,
    trigger_context TEXT,
    questions JSONB NOT NULL,
    displayed_at TIMESTAMPTZ,
    selected_question_index INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 토픽 커버리지
CREATE TABLE topic_coverage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id),
    topic_name VARCHAR(200) NOT NULL,
    topic_category VARCHAR(50),
    coverage_percentage FLOAT DEFAULT 0,
    evidence_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'uncovered',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 스코어카드
CREATE TABLE scorecards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES interview_sessions(id),
    overall_score FLOAT,
    recommendation VARCHAR(30),
    competency_scores JSONB NOT NULL,
    evidence_map JSONB NOT NULL,
    strengths JSONB,
    concerns JSONB,
    interviewer_notes TEXT,
    approved_at TIMESTAMPTZ,
    approved_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Knowledge Graph 스냅샷
CREATE TABLE knowledge_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    graph_data JSONB NOT NULL,
    node_count INTEGER,
    edge_count INTEGER,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 프로모 코드
CREATE TABLE promo_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    credit_type VARCHAR(20) NOT NULL CHECK (credit_type IN ('analysis', 'interview', 'both')),
    credits_granted INTEGER NOT NULL,
    max_redemptions INTEGER,
    current_redemptions INTEGER DEFAULT 0,
    max_per_user INTEGER DEFAULT 1,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 프로모 사용 기록
CREATE TABLE promo_redemptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promo_code_id UUID NOT NULL REFERENCES promo_codes(id),
    user_id UUID NOT NULL REFERENCES users(id),
    credits_granted INTEGER NOT NULL,
    redeemed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(promo_code_id, user_id)
);

-- 크레딧 계좌
CREATE TABLE credit_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id),
    analysis_credits INTEGER DEFAULT 0,
    interview_credits INTEGER DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 크레딧 트랜잭션
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES credit_accounts(id),
    type VARCHAR(20) NOT NULL CHECK (type IN ('grant', 'consume', 'refund', 'expire')),
    credit_type VARCHAR(20) NOT NULL CHECK (credit_type IN ('analysis', 'interview')),
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    source VARCHAR(50),
    reference_id UUID,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 11. 면접 결과 산출물

면접 종료 후 면접관이 받는 최종 결과물:

### 7대 산출물

| # | 산출물 | 설명 |
|---|--------|------|
| 1 | **종합 스코어카드** | 6대 역량별 점수 + 종합 추천 (강력추천/추천/보류/부적합) |
| 2 | **증거 기반 평가** | 각 점수에 실제 발언 인용 + KG 코드 근거 |
| 3 | **토픽 커버리지** | 검증된 역량 vs 미검증 역량 |
| 4 | **면접 타임라인** | 시간순 대화 흐름 + 핵심 포인트 하이라이트 |
| 5 | **D3.js 시각화** | Radar(역량), Heatmap(시간대별 품질), Bar(커버리지) |
| 6 | **전사본** | 화자 분리된 면접 전문 |
| 7 | **AI 분석 요약** | 강점, 우려사항, 특이사항, 면접관 메모 |

### 20+ 수치 지표

- 역량별 점수 (6대 역량 × 1-5점)
- JD 매칭률 (%)
- 답변 구체성 지수
- 이력서-답변 일치율
- 커뮤니케이션 스코어
- 기술 깊이 지수
- 프로젝트 기여도 점수
- 문제해결 접근 점수
- 코드 품질 상관 점수
- 토픽 커버리지율

---

## 12. 프로모 코드 & 결제 준비

### 12.1 프로모 코드 시스템

```python
class CreditType(str, Enum):
    ANALYSIS = "analysis"
    INTERVIEW = "interview"
    BOTH = "both"

class PromoCode(BaseModel):
    code: str                      # "JITTDA-BETA-26"
    credit_type: CreditType        # ANALYSIS | INTERVIEW | BOTH
    credits_granted: int           # 5
    max_redemptions: int | None    # None = 무제한
    max_per_user: int              # 1
    valid_from: datetime
    valid_until: datetime | None   # None = 만료 없음
```

### 12.2 결제 준비 (BillingProvider Port)

```python
class BillingProvider(Protocol):
    async def create_checkout(self, plan: Plan) -> CheckoutSession: ...
    async def get_subscription(self, user_id: str) -> Subscription | None: ...
    async def cancel_subscription(self, subscription_id: str) -> None: ...

# 현재: 무료 + 프로모 코드
class FreeTierAdapter:
    async def create_checkout(self, plan: Plan) -> CheckoutSession:
        raise NotImplementedError("프로모 코드로만 가능")

# 미래: Stripe (Port 교체만으로 전환)
# class StripeAdapter(BillingProvider): ...
```

---

## 13. Phase 로드맵

총 **69 티켓, 14주**:

| Phase | 기간 | 핵심 산출물 | 티켓 |
|-------|------|------------|------|
| 0 | 1주 | Monorepo 스캐폴딩, Docker, DB | 8 |
| 1 | 2주 | Electron Shell + 네이티브 오디오 | 10 |
| 2 | 2주 | VAD + STT + 채널 분리 | 8 |
| 3 | 3주 | KG 구축 + Deck 생성 + Local-First | 12 |
| 4 | 2주 | 실시간 파이프라인 + LLM 통합 | 10 |
| 5 | 2주 | 면접관 대시보드 UI + 스코어카드 | 11 |
| 6 | 2주 | 에러 처리 + Sentry + Infisical + 테스트 | 10 |

### Phase 0: Monorepo 스캐폴딩 (Week 1)
- jittda/ 디렉토리 구조 생성
- desktop/ Electron 프로젝트 초기화
- Docker Compose 확장 (기존 + desktop 빌드)
- init.sql에 Live 관련 테이블 추가
- shared/ 패키지 설정 (공유 타입)

### Phase 1: Electron + 네이티브 오디오 (Week 2-3)
- Electron 33+ 앱 셸 (BrowserWindow, IPC)
- macOS ScreenCaptureKit 바이너리
- Windows WASAPI 바이너리
- Main Process: OS 판별 + Child Process 관리
- Channel Muxing (스테레오 PCM)

### Phase 2: VAD + STT (Week 4-5)
- Silero VAD WASM 통합 (@ricky0123/vad)
- Deepgram Nova-3 스트리밍 클라이언트
- 채널별 독립 전사
- EventBus (mitt) 설정

### Phase 3: KG + Deck + Local-First (Week 6-8)
- NetworkX KG 구축 (v5.0 Worker 확장)
- KG → JSON 직렬화 + API
- graphology 클라이언트 통합
- LanceDB 인프로세스 설정
- Deck 생성 파이프라인 (Kimi K2.5)
- Local-First 동기화 프로토콜

### Phase 4: 실시간 파이프라인 (Week 9-10)
- 7단계 파이프라인 연결
- 트리거 평가 엔진
- Groq LLM 통합 (실시간 질문 생성)
- Agentic Graph RAG (7개 도구)
- WebSocket 서버

### Phase 5: 대시보드 UI (Week 11-12)
- 3-Zone 라이브 대시보드
- QuestionCard 컴포넌트 (애니메이션)
- 토픽 커버리지 바
- 자동 스코어카드 생성
- D3.js 차트 (Radar, Timeline)
- 면접 전/후 화면

### Phase 6: 품질 + 인프라 (Week 13-14)
- 에러 코드 체계 + Error Chain
- Sentry self-hosted 연동
- Infisical self-hosted 연동
- 프로모 코드 시스템
- 크레딧 시스템
- E2E 테스트 (Playwright)
- 성능 벤치마크

---

## 관련 문서

| 문서 | 경로 |
|------|------|
| 와이어프레임 | `docs/plans/2026-02-17-jittda-live-wireframes.md` |
| MVP PRD | `docs/plans/2026-02-17-jittda-live-mvp-prd.md` |
| v5.0 원본 설계 | `plan/2026-02-15-v5-final-design.md` |
| Linear 프로젝트 | Jittda Live (JIT-128 ~ JIT-140) |
