# Jittda Live 실시간 AI 면접 가이드 설계 브레인스토밍 세션 추출

세션 ID: `9210bbe5-3255-4100-ba32-5a0c5a43c12c`

---

## Phase 1: 초기 요청 및 컨텍스트 수집

### [사용자 초기 요청] (Line 9)

> <command-message>superpowers:brainstorming</command-message>
> <command-name>/superpowers:brainstorming</command-name>
> <command-args> /brainstorming plan/2026-02-15-v5-final-design.md 을 가지고 리니어프로젝트 Jittda Sniper v5.0 —
>   Clean Slate Reconstruction 을 설계했는데 해당 설계를 바꾸는게 필요할것 같아. 지금은 웹에서로만 질문
>   만들어주고 정보보여주고 하는건데 이걸 개선해서 실시간 면접 ai 가이드 기능을 지원하도록 할거야 일단
>   ai 면접 가이드 기능의 최소 기능요구서는 [Pasted text #1 +87 lines] 와 같아 먼저 면접자데이터
>   분석을 끝내고 데스크탑 프로그램에서 접속해서 해당 면접자 를 선택하고 면접을 진행하면 os 마이크와
>   시스템 사운드 캡쳐를 오프라인인지, 온라인 면접인지에 따라 동적으로 챕켜하고 면접자 화자분리가
>   필요한(오프라인) 에서 화자분리를 하고 stt화 해서 실시간으로 ai 가 상황을 인식하고 우리가 미리
>   면접자 정보를 백터나 그래프 같은 곳에 저장한 정보를 실시간으로 파악해서 면접에 필요한 질문생성을
>   해주고 카테고리별로 변접자 분석에 필요한 데이터가 추가될때마다 실시간으로 퍼센테이지 프로그레스바로
>   표시하고 면접 분석할만한 데이터가 쌓이면 면접종료해도 된다는 안내를 내고 면접이 종료되면 ai 가
>   종합적으로 분석해서 면접자를 분석한 데이터를 시작화해서 면접관이 보기좋게 보여주는 게 목표야,
> 
>  1. 클라이언트 시스템 아키텍처 설계도 (Electron 기반)
> Electron의 아키텍처는 브라우저와 동일하게 다중 프로세스(Multi-Process) 모델을 따릅니다 ``. 무거운 작업은 분리하고 UI 스레드(Renderer)의 병목을 막는 것이 핵심입니다.
> │ ├─ macOS (ScreenCaptureKit / CoreAudio) └─ Windows (WASAPI Loopback) │ [ 1. Child Process (Native Audio Module) ] │ - 역할: OS별 C++/Swift 바이너리가 백그라운드에서 실행 │ - 마이크(면접관) = Left 채널, 시스템 소리(지원자) = Right 채널 │ - 출력: 원시 PCM 스테레오 오디오 스트림 ▼ [ 2. Electron Main Process (Node.js) ] │ - 역할: OS 환경 판별(process.platform), Child Process 생명주기 관리 │ - IPC(Inter-Process Communication)를 통해 Renderer로 스트림 전달 ▼
>   │
>   ├─ 
>   │     - 1ms 이하 속도로 무음 감지, 발화 교대(Turn-taking) 제어
>   │
>   ├─
>   │     - VAD가 열어준 구간의 오디오만 전송, 채널 기반 화자 분리 텍스트 수신
>   │
>   ├─
>   │     - 서버와 Local-First 동기화된 지원자 데이터 보관
>   │     - STT 텍스트 수신 즉시 20ms 이내로 연관 데이터 검색
>   │
>   └─ [ Groq LLM API ]
>         - 검색된 컨텍스트 + 시스템 프롬프트를 결합해 꼬리 질문 동적 생성
> 2. 클라이언트 디자인 패턴
> 개발팀에 다음 세 가지 아키텍처 패턴을 반드시 적용하도록 지시하십시오.
> 1. Local-First (오프라인 퍼스트) 패턴: 서버는 단순한 '동기화 노드' 역할만 수행합니다. 앱 구동 시 서버에서 이력서 및 직무 기술서(JD) 벡터 데이터를 다운로드하여 로컬 파일 시스템의 LanceDB에 적재합니다 [1]. 면접 도중 네트워크가 불안정해도 데이터 조회는 클라이언트 내부에서 처리되므로 지연이 없습니다 ``, [2].
> 2. 멀티채널 오디오 파이프라이닝 (Channel Muxing): 소프트웨어적인 화자 분리에 의존하지 않습니다. 마이크 입력은 채널 0(좌측), 시스템 오디오는 채널 1(우측)로 물리적으로 분리된 스테레오 스트림을 생성하여 STT 엔진에 전송합니다 ``. 이를 통해 화자 인식률을 100%로 보장합니다.
> 3. Pub/Sub (Observer) 이벤트 버스: 오디오 스트림, VAD 상태, STT 텍스트 반환, LLM 질문 생성 등은 모두 비동기적으로 발생합니다. React 컴포넌트가 이 상태들을 직접 관리하면 렌더링 지연이 발생하므로, 전역 이벤트 버스를 통해 UI 요소들이 필요한 이벤트만 구독(Subscribe)하도록 결합도를 낮춰야 합니다.
> 
> 3. 클라이언트 최소 기능 요구서 (MVP PRD)
> 이 요구서를 바탕으로 스프린트를 쪼개시면 됩니다. 첫 번째 마일스톤은 무조건 'OS 네이티브 오디오 캡처'여야 합니다.
> 요구사항 1: 운영체제 네이티브 오디오 캡처 모듈
> * 기능 명세: 서드파티 가상 드라이버 설치 없이 시스템 오디오와 마이크 오디오를 캡처한다.
> * 세부 조건:
>     * macOS (13.0 이상): ScreenCaptureKit 또는 CoreAudio 기반 네이티브 바이너리 실행.
>     * Windows (10 이상): WASAPI 기반 루프백 캡처 바이너리 실행 [3].
>     * Main Process는 OS를 판별하여 적절한 바이너리를 자식 프로세스로 실행하고 에러 생명주기를 관리한다.
> 요구사항 2: 엣지 기반 VAD 및 오디오 스트림 제어
> * 기능 명세: 클라이언트 내부에서 음성과 무음을 판별하여 불필요한 API 호출을 막는다.
> * 세부 조건:
>     * WebAssembly 컴파일된 Silero VAD를 Renderer 프로세스에서 구동한다 [4].
>     * 무음이 1.5초 이상 지속될 때만 발화의 완전한 종료로 인식하고 LLM 파이프라인을 가동한다 [5].
> 요구사항 3: 초저지연 RAG 데이터 파이프라인 (LanceDB)
> * 기능 명세: 지원자 이력서 및 평가 기준(Rubric)을 로컬 환경에서 0.1초 이내에 검색한다.
> * 세부 조건:
>     * Electron 앱 내부에 LanceDB를 인프로세스(In-process)로 구동한다 [1].
>     * 지원자의 발화(STT 결과)에서 핵심 키워드를 추출해 로컬 데이터베이스를 쿼리한다.
> 요구사항 4: 면접관 보조 UI/UX 대시보드
> * 기능 명세: 화상회의 창 옆에 띄워두는 비침해적(Non-intrusive) 인터페이스를 제공한다.
> * 세부 조건:
>     * 토픽 커버리지 바 (Topic Coverage): 직무 평가 요소(예: MSA 경험, 트러블슈팅)가 대화 중 언급되었는지 실시간으로 체크박스 상태를 업데이트한다 [6].
>     * 동적 질문 카드 (Probing Cards): 지원자 답변에 허점이 있거나 이력서와 다른 부분이 발견되면, Groq API를 통해 3개 이내의 짧은 꼬리 질문(Bullet point)을 팝업 형태로 화면 우측에 제시한다.
>     * 자동 스코어카드 (Automated Scorecard): 면접이 종료되면 실시간으로 수집된 증거 데이터를 사전에 정의된 역량 평가 루브릭에 매핑하여 평가서 초안을 제공한다 ``.
> 
> 
> 본 시스템의 사용자는 다수의 지원자를 연속으로 평가해야 하는 면접관이다. 따라서 디자인의 핵심은 '인지 부하 최소화'와 '객관적 평가 보조'에 있다. 화상 회의 화면과 병렬로 띄워놓고 사용할 수 있는 대시보드 형태로 설계된다.
> 8.1. 실시간 면접관 어시스턴트 대시보드 (Interviewer Dashboard)
> 면접관이 대화의 흐름을 놓치지 않으면서도, 시스템이 제공하는 정보를 즉각적으로 소화할 수 있도록 미니멀리즘 기반의 다크/라이트 테마를 지원하는 독립된 데스크탑 윈도우(BrowserWindow)로 구현된다.
> 8.2. 핵심 UI 컴포넌트 및 기능 명세
> 화면 레이아웃은 진행 상황을 추적하는 [토픽 커버리지 바], 실시간으로 생성되는 [동적 검증 질문 카드], 그리고 자동화된 **[역량 스코어카드]**로 구성된다.
> A. 역량 평가 및 토픽 커버리지 바 (Topic Coverage Checklist)
> 면접관이 해당 포지션에서 반드시 확인해야 할 필수 질문과 역량들이 얼마나 논의되었는지 추적한다. AI가 실시간 대화 내용을 분석하여 특정 역량(예: 트러블슈팅, 커뮤니케이션)에 대한 충분한 데이터가 확보되었다고 판단하면 체크리스트를 자동으로 완료(✔) 처리한다.
> UI 와이어프레임 명세: 화면 상단 배치
> [ 📊 직무 역량 검증 진행도 ]
> ⏱️ 진행 시간: 24:15 | 현재 대화 주제: 시스템 아키텍처 설계 경험
> ------------------------------------------------------------
> ☑ MSA 분산 환경 이해도 (충분함) | ☐ 대용량 트래픽 최적화 경험 (미검증) | ☐ 팀 내 갈등 해결 사례 (미검증)
> B. 실시간 동적 검증 질문 카드 (Dynamic Probing Cards)
> 지원자의 답변이 모호하거나 이력서의 내용과 충돌할 때, 또는 더 깊이 파고들어야 할 기술적 포인트가 포착되면 즉시 팝업되는 카드다. 면접관이 화면을 슬쩍 보는 것만으로도 핵심을 찌르는 후속 질문(Follow-up)을 던질 수 있도록 짧은 개조식(Bullet Point) 형태로 제공된다.
> UI 와이어프레임 명세: 화면 우측 메인 영역
> 🎙️ [지원자 답변 실시간 분석 중...]
> "Redis를 써서 속도를 많이 높였고, 혼자서 캐싱 레이어를 다 구축했습니다."
> ------------------------------------------------------------
> 💡 [AI 참모의 실시간 검증 가이드]
> ⚠️ 검증 포인트: 지원서에는 '팀 프로젝트'로 기재되어 있으나 단독 구축을 주장함. 캐시 정합성에 대한 깊이 있는 이해 확인 필요.
> [추천 꼬리 질문]
> - "혼자 구축하셨다니 대단하네요. 당시 캐시 무효화(Cache Invalidation) 전략은 어떻게 가져가셨나요?"
> - "데이터베이스 업데이트 시 캐시와 DB 간의 데이터 정합성이 깨지는 문제는 겪지 않으셨나요?"
> C. 실시간 자동화 스코어카드 (Automated Scorecard)
> 면접이 끝난 후 면접관이 기억을 더듬어 평가표를 작성하는 수고를 덜어준다. 면접 중 지원자의 답변에서 특정 역량에 부합하는 명확한 증거(Evidence)가 나오면, 사전에 정의된 평가 루브릭(Rubric)에 맞춰 자동으로 내용을 분류하고 기록한다. 면접관은 제안된 스코어카드를 확인하고 승인(Approve)하거나 가볍게 수정하기만 하면 된다.
> 
> 
> 1. 상훈 님이 구현하려는 핵심 기능: "자동화된 면접 참모(Strategist)"
> 면접관이 면접장에 들어가기 전, 유능한 참모가 미리 지원자를 뒷조사해서 **"이것만 물어보시면 됩니다"**라고 정리된 파일을 책상 위에 올려두는 상황을 상상하세요.
> 상훈 님이 구현하려는 시스템은 바로 그 **'참모'**와 **'보고서'**입니다.
> A. 질문 덱(Deck) 생성 = "면접 시나리오 집필"
> * 의미: AI가 지원자의 이력서와 코드를 미리 읽고, **'검증해야 할 의혹'**들을 찾아내는 과정입니다.
> * 결과물: 단순한 질문 목록이 아니라, 상황별 대처가 담긴 카드 묶음입니다.
>     * 카드 1: "이 지원자는 보안 경험이 약해 보입니다. 이 질문으로 찔러보세요."
>     * 카드 2: "협업 경험이 훌륭하다고 썼는데, 진짜인지 구체적 사례를 요구해보세요."
>     * 체크리스트: "답변에서 '구체적 수치(%)'가 나오는지 확인하세요."
> B. 클라이언트 동기화 = "작전 지도 배포"
> * 의미: 면접관이 사용할 도구(앱)에 방금 만든 '시나리오'를 장전하는 과정입니다.
> * 목적:
>     * 면접 도중에는 인터넷이 끊겨도, AI가 느려져도 상관없게 만듭니다.
>     * 이미 모든 질문과 전략이 **면접관의 손 안(앱)**에 들어와 있기 때문에, 버튼만 누르면(혹은 대화 흐름에 따라) 즉시 튀어나옵니다.
> 
> 2. 전체 흐름 요약 (Non-Technical)
> 상훈 님이 만들고자 하는 서비스의 본질은 이렇습니다.
> 1. 탐정 (Server): 면접 전에 지원자의 서류를 샅샅이 뒤져서 약점과 강점을 파악하고, **맞춤형 질문 리스트(공략집)**를 만듭니다.
> 2. 전달자 (Sync): 이 공략집을 면접관이 들고 들어갈 태블릿(앱)에 몰래 넣어줍니다.
> 3. 가이드 (App): 실시간 면접 현장에서 지원자가 무슨 말을 하면, 태블릿이 공략집을 뒤져서 **"지금은 3번 카드를 쓰세요!"**라고 알려줍니다.
> 
>  확인해봐 면접관은 실시간으로 다른 질문을 요청할수 있고
>   ai 에게 ai는 대화 상황에 맞는 다른 질문은 생성하여 제공해야해 대화에따라 꼬리질문이 필요한경우
>   꼬리잘문을 만들어서 면접관에게 보여줘야해 상황에 따라 해당질문이 뭘 위한건지를 간략하게 알려주면
>   좋을것도 같아. 면접관은 면접+ ai가이드 읽기 + 판단 등 동시에 여러가지 일을 해야해서 멀티테스킹이
>   힘드니 최대한 간략하고 불필요한 정보는 빼고 필요한 정보만 출력하는 방식으로 해야해 해당 방법으로
>   프로젝트 재설계 하는데 같이 처음부터 하나한 설계해보자 적절한 프렘임워크 라이브러리, api ,프로그램,
>   등 최신기술(여기에 필요한) 을 인터넷으로 충분히 찾아서 분석해보고 설계해보자, 일단 최소기능
>   요구서부터 같이 만들어 보면서 단계적으로 뭐부터 설계를 해놓고 뭐부터 세부적으로 설계를 할지
>   순차적으로 하나씩 진행해보자, 새롭게 리니어 프로젝트 생성해서 하나하나씩 채워나가 보자 프로젝트 이름은 jittda live 로 하자</command-args>

### [어시스턴트] 프로젝트 컨텍스트 요약 (Line 132)

## 프로젝트 컨텍스트 요약

기존 **Jittda Sniper v5.0**은:
- **서버 사이드** 분석 시스템 (LangGraph HMAS + DDD)
- GitHub 코드 + LinkedIn + 이력서를 분석하여 **면접 질문 덱** 생성
- **웹 기반** 결과 시각화 (D3.js + React 19)
- 42개 티켓, 42일 로드맵

새로운 **Jittda Live**는 이 위에:
- **데스크탑 앱**으로 실시간 면접 가이드
- OS 네이티브 오디오 캡처 + STT + VAD
- 로컬 벡터 DB + 실시간 LLM 질문 생성
- 면접관 인지 부하 최소화 대시보드

---

이제 설계 방향을 확정하기 위해 핵심 질문을 하나씩 드리겠습니다. 첫 번째 질문입니다:

---
## Phase 2: 설계 명확화 질문 (Q&A)

### [Q1: 기존 웹서비스와 데스크탑의 관계] (Line 132)

## 프로젝트 컨텍스트 요약

기존 **Jittda Sniper v5.0**은:
- **서버 사이드** 분석 시스템 (LangGraph HMAS + DDD)
- GitHub 코드 + LinkedIn + 이력서를 분석하여 **면접 질문 덱** 생성
- **웹 기반** 결과 시각화 (D3.js + React 19)
- 42개 티켓, 42일 로드맵

새로운 **Jittda Live**는 이 위에:
- **데스크탑 앱**으로 실시간 면접 가이드
- OS 네이티브 오디오 캡처 + STT + VAD
- 로컬 벡터 DB + 실시간 LLM 질문 생성
- 면접관 인지 부하 최소화 대시보드

---

이제 설계 방향을 확정하기 위해 핵심 질문을 하나씩 드리겠습니다. 첫 번째 질문입니다:

### [사용자 답변 + 어시스턴트 정리] (Line 139)

이해했습니다. 정리하면:
- **웹**: 유저 데이터 분석 + 결과 열람 (기존 유지)
- **데스크탑 앱**: 라이브 면접 서비스 (기존 질문 생성을 실시간으로 전환)
- **공유**: 분석 데이터와 면접 결과는 웹/앱 양쪽에서 확인 가능

다음 질문입니다:

### [Q2: 타겟 플랫폼] (Line 146)

좋습니다. macOS 우선 개발, OS별 바이너리 분리 + 인터페이스 추상화로 Windows 확장성 확보. 다음 질문입니다:

### [Q3: 온라인/오프라인 면접] (Line 152)

둘 다 지원. 온라인(채널 분리) + 오프라인(AI 화자분리) 모두 MVP에 포함. 다음 질문입니다:

### [Q4: STT 서비스 리서치 시작] (Line 158)

최신 실시간 STT 서비스들을 리서치하겠습니다. 한국어+영어 지원 + 성능을 중점으로 찾아보겠습니다.

### [STT 리서치 결과] (Line 197)

리서치 결과를 종합했습니다. 실시간 STT 서비스 비교표입니다:

### 실시간 STT 서비스 비교 (한국어+영어 기준)

| 서비스 | 실시간 스트리밍 | 한국어 정확도 | 레이턴시 | 화자분리 | 가격 |
|--------|:---:|---|---|:---:|---|
| **Deepgram Nova-3** | WebSocket | Tier 2 (WER 7-16%) | <300ms | 내장 | $0.0077/분 |
| **ElevenLabs Scribe v2 RT** | WebSocket | "Good" (WER 10-20%) | **~150ms** | 미확인 | 별도 확인 필요 |
| **AssemblyAI Universal** | WebSocket | 제한적 (영어 중심) | ~300ms | 내장 | $0.0025/분 |
| **Soniox** | WebSocket | 60+언어 지원 | 미공개 | **실시간 지원** | Speechmatics 대비 2-3x 저렴 |
| **Speechmatics** | WebSocket | 55+언어 지원 | <1s | 지원 | 프리미엄 |

**핵심 발견:**
- Reddit 커뮤니티 피드백: "Deepgram/AssemblyAI는 영어에선 훌륭하지만 **아시아 언어 정확도와 구두점은 크게 떨어진다**"
- ElevenLabs가 가장 빠르지만(150ms), 한국어 WER이 Deepgram보다 높음(덜 정확)
- Soniox가 실시간 화자분리를 기본 내장하면서 가격 경쟁력 있음

Sources:
- [Deepgram Nova-3 Korean](https://deepgram.com/learn/deepgram-expands-nova-3-with-11-new-languages-across-europe-and-asia)
- [ElevenLabs Scribe v2 Realtime](https://elevenlabs.io/blog/introducing-scribe-v2-realtime)
- [Reddit STT 비교](https://www.reddit.com/r/speechtech/comments/1m1l0zu/comparative_review_of_speechtotext_apis_2025/)

---
### [서브에이전트] v5 설계 문서 구조 파악 (Line 201)

완벽합니다. 이제 종합 요약을 작성하겠습니다.

---

## Jittda Sniper v5.0 최종 설계서 종합 요약 (2026-02-15)

### 1. 전체 아키텍처 개요

**Jittda v5.0**은 기존 Vantict Sniper v4.0(Temporal.io 기반)의 "마이그레이션"이 아닌 **완전한 "재건축"(Clean Slate Reconstruction)**이다. `jittda/` 새로운 프로젝트 디렉토리에서 처음부터 설계하며, DDD 4계층 아키텍처와 LangGraph 1.0 기반 3계층 HMAS(Heterogeneous Multi-Agent System)를 중심으로 구성된다.

**핵심 철학:** AI의 할루시네이션을 원천 차단하기 위해 "확률적 AI(LLM)와 결정론적 알고리즘(정적 분석)의 하이브리드 결합"을 추구한다. 모든 LLM 판단은 수학적으로 계산된 정량적 데이터(Fact)에 기반해야 한다.

---

### 2. 주요 설계 원칙 (8가지)

| 원칙 | 설명 |
|------|------|
| **Noise-Free** | Fork, 라이브러리, AI 생성/Boilerplate 코드를 완벽히 제거한 순수 기여분만 분석 |
| **Semantic Analysis** | 텍스트 기반이 아닌 AST(추상 구문 트리) 기반의 논리적 분석 |
| **Identity-First** | "이 코드를 정말 지원자가 짰는가?" 검증이 분석보다 선행 |
| **JD-Relevance** | JD 기반 Funnel Selection으로 상위 3-5개 프로젝트만 심층 분석 |
| **Reference Passing** | LangGraph State에는 'DB ID'만, Raw Data는 DB에 저장 (State Checkpoint 최적화) |
| **Fact-Grounded** | 모든 LLM 판단에 정량적 분석 데이터 근거 필수 |
| **Parallel Execution** | Fan-out/Fan-in 패턴으로 분석 속도 극대화 |
| **Clean Separation** | DDD 4계층 엄격 준수, domain → infrastructure import 금지 |

---

### 3. 전체 Phase 및 Scope

총 **6개 Phase, 42개 Linear 티켓, 42일 일정**

| Phase | 기간 | 티켓 | 핵심 산출물 |
|-------|------|------|-----------|
| **Phase 0: Scaffolding** | 3일 | 4개 | 프로젝트 구조, Docker, Fresh init.sql |
| **Phase 1: Domain Layer** | 5일 | 6개 | Identity Resolution, Funnel Selection, Scoring Calculator |
| **Phase 2: Infrastructure** | 7일 | 8개 | Git, GitHub GraphQL, Tree-sitter, Radon/Lizard, SonarQube, Datasketch, Instructor, pgvector 어댑터 |
| **Phase 3: Application - Graphs** | 7일 | 6개 | MetaState, Forensic/Logic/Stack Supervisor Graph, FastAPI + WebSocket 통합 |
| **Phase 4: 질문 생성** | 5일 | 5개 | TopicSelector, 3전략 QuestionCrafter, Enhancement Agents, QualityGate |
| **Phase 5: 출력 + 프론트엔드** | 10일 | 9개 | OutputAssembler, 4대 지표, D3.js 차트 (Radar, Treemap, Heatmap), 5개 탭 UI |
| **Phase 6: 테스트 + 정리** | 5일 | 4개 | Domain/E2E/Playwright 테스트, 성능 벤치마크, 문서화 |

---

### 4. 기술 스택 (2026-02 최신화)

#### 백엔드 (Python)
- **Orchestration:** LangGraph 1.0.8+ (StateGraph + HMAS)
- **Checkpointer:** langgraph-checkpoint-postgres 3.0.4+ (PostgreSQL 기반)
- **Structured Output:** Instructor 1.7.0+ (Pydantic v2 네이티브 + 자동 재시도)
- **AST Parsing:** Tree-sitter 0.24.7+ (Python 패키지 네이티브 바인딩, .so 빌드 폐기)
- **복잡도 분석:** Radon 6.0.1+, Lizard 1.17.10+
- **품질 게이트:** SonarQube Community (On-Demand Docker Profile)
- **표절 탐지:** Datasketch 1.6.5+ (MinHash/LSH)
- **DB:** PostgreSQL 16 + pgvector 0.3.6+ (벡터 검색)
- **캐시:** Redis 7
- **LLM:** Kimi K2.5 (Langfuse 기반)
- **Tracing:** Langfuse 2.57.0+ (프롬프트 버전 관리 + 분석)

#### 프론트엔드
- **Framework:** React 19 + Vite (HMR 최적화)
- **Styling:** Tailwind CSS 4
- **Visualization:** D3.js v7 (Radar, Treemap, Heatmap 등 복잡 데이터 시각화)
- **State:** TanStack Query 5.0+ (실시간 데이터 페칭)
- **Streaming:** WebSocket (LangGraph 실행 상태 실시간 전송)

#### 인프라
- **Container:** Docker Compose (개발 환경 통일)
- **Tunnel:** Cloudflare Tunnel (cloudflared) - Zero Trust, 포트 포워딩 불필요
- **CI/CD:** GitHub Actions

---

### 5. DDD 4계층 아키텍처 및 디렉토리 구조

```
jittda/
├── backend/src/
│   ├── interface/          # [Layer 1] FastAPI Routes + WebSocket + Middleware
│   ├── application/        # [Layer 2] LangGraph StateGraph + 노드
│   │   ├── graphs/         # MetaGraph, ForensicGraph, LogicGraph, StackGraph, QuestionGraph
│   │   ├── nodes/          # Thin Wrapper (Load→Process→Save→Ref 패턴)
│   │   ├── states/         # TypedDict State (Reference Passing)
│   │   └── use_cases/
│   ├── domain/             # [Layer 3] 순수 비즈니스 로직 (외부 의존성 0)
│   │   ├── identity/       # Identity Resolution (mailmap_builder, blame_filter, semantic_pruner)
│   │   ├── scoring/        # 4대 지표 계산기
│   │   ├── matching/       # JD-기반 Funnel Selection
│   │   ├── question/       # 질문 생성 규칙
│   │   └── analysis/       # 분석 도메인 모델
│   └── infrastructure/     # [Layer 4] 외부 서비스 어댑터
│       ├── git/            # blame_runner, clone_manager, mailmap_writer
│       ├── github/         # GraphQL + REST API 클라이언트
│       ├── analysis/       # Tree-sitter, Radon, Lizard, SonarQube, Datasketch
│       ├── llm/            # Instructor + Langfuse 통합
│       ├── linkedin/       # BrightData 스크래핑 (LinkedIn)
│       ├── embedding/      # pgvector 벡터 저장소
│       └── persistence/    # Repository 패턴 (Job, Analysis)
├── frontend/
│   ├── src/components/charts/
│   │   ├── FourAxisRadar.tsx        # 4대 지표 레이더
│   │   ├── ComplexityTreemap.tsx    # 파일별 복잡도 드릴다운
│   │   ├── AICodeHeatmap.tsx        # Human vs AI 비율
│   │   ├── SkillHeatmap.tsx         # 기술 매칭 히트맵
│   │   └── CommitTimeline.tsx
│   └── src/hooks/useLangGraphStream.ts  # WebSocket 실시간 스트리밍
└── infra/
    ├── postgres/init.sql   # Fresh DB 스키마 (Alembic 없음)
    ├── sonarqube/          # SonarQube 설정
    └── nginx/              # Production 리버스 프록시
```

**의존성 규칙:**
- `domain/` → 외부 패키지 import 불가 (순수 Python + Pydantic)
- `infrastructure/` → `domain/` 모델을 리턴하도록 설계
- `application/` → `domain/` + `infrastructure/` 조합
- `interface/` → `application/` 유스케이스만 호출

---

### 6. 3계층 HMAS 아키텍처 (LangGraph)

#### Level 1: MetaAgent (전체 오케스트레이터)
```
Phase 0: InputRouter → 입력 파싱 + 소스 라우팅
Phase 1: PlanGenerator → LLM 기반 실행 계획 동적 생성
Phase 2: AnalysisDispatcher (Fan-out)
  ├─ Level 2: ForensicSupervisor (수집/정제/진정성 검증)
  ├─ Level 2: LogicSupervisor (복잡도/품질 분석)
  └─ Level 2: StackSupervisor (전문성/스택 분석) — LogicSupervisor 완료 후 실행
Phase 2.5: ProfileSynthesizer (Fan-in) → UnifiedCandidateProfile + 4대 지표 산출
Phase 3: QuestionOrchestrator (3전략 병렬 생성)
Phase 4: QualityGate (검증 + 조건부 재생성 루프, 최대 2회)
Phase 5: OutputAssembler (최종 스크립트 조립)
```

#### Level 2-3: Worker 기반 Supervisor (11개 Worker)

| # | Worker | Supervisor | 도구 | 설명 |
|---|--------|------------|------|------|
| W1 | CollectorWorker | Forensic | GraphQL, PyDriller | 코드 수집 + Identity Resolution |
| W2 | CleanerWorker | Forensic | git blame -w -M -C | 노이즈 제거 (Fork, Boilerplate 등) |
| W3 | VibectorWorker | Forensic | WPM 계산 | AI 코드 의심 구간 탐지 (타이핑 속도) |
| W4 | CLAVEWorker | Forensic | 스타일로메트리 | 저자 지문 생성 |
| W5 | DatasketchWorker | Forensic | MinHash/LSH | 표절 탐지 |
| W6 | ASTAnalyzerWorker | Logic | Tree-sitter | 의미론적 코드 분석 |
| W7 | ComplexityMeterWorker | Logic | Radon/Lizard | CC, Halstead, MI 산출 |
| W8 | QualityScannerWorker | Logic | SonarQube | 부채, 스멜, 취약점 |
| W9 | SkillExtractorWorker | Stack | AST + LLM | JD 기반 기술 매핑 |
| W10 | APIDepthAnalyzerWorker | Stack | AST Call Graph | API 활용 깊이 분석 |
| W11 | ArchitectureEvaluatorWorker | Stack | AST 패턴 | SOLID/설계 패턴 평가 |

**의존성:**
- ForensicSupervisor ∥ LogicSupervisor (병렬)
- StackSupervisor는 LogicSupervisor 완료 후 실행 (AST 결과 의존)

---

### 7. 핵심 데이터 흐름

#### 7.1 Identity Resolution Pipeline (3단계)
1. **Step 1: GitHub Node ID** - 이메일 변경에도 불변인 GitHub 고유 ID(databaseId) 조회
2. **Step 2: 동적 .mailmap 생성** - Git 히스토리 기반 동일인 클러스터링
   - noreply.github.com 패턴 (확정)
   - GitHub profile 교차 매칭 (확정)
   - Levenshtein distance < threshold (휴리스틱)
   - 동일 커스텀 도메인 (약한 신호)
3. **Step 3: 3단계 포렌식 쿼리**
   - Level 1: `git blame -w -M -C -C` (공백, 파일 이동, 복사 제외)
   - Level 2: Tree-sitter AST 의미론적 제거 (import, 주석, config, 자동 생성 코드)
   - Level 3: Authenticity Check (Vibector + CLAVE + Datasketch)

#### 7.2 JD 기반 Funnel Selection (3단계)
```
전체 레포 → Stage 1: Hard Filter (Fork, 최근 push, 언어 교집합)
         → Stage 2: Relevance Scoring (JD tech_stack 매칭 + LLM)
         → Stage 3: Vector Similarity (JD ↔ README/Description)
         → 상위 3-5개 심층 분석
```

#### 7.3 Reference Passing 패턴 (State 최적화)
모든 노드는 **Load → Process → Save → Return Ref** 4단계를 따른다:
```python
# 1. Load: DB에서 데이터 조회 (ref 기반)
repo_files = await repo_repository.get_files(job_id)

# 2. Process: 분석 수행
ast_result = await ast_analyzer.analyze(repo_files)

# 3. Save: 결과를 DB에 저장
result_id = await analysis_repository.save_result(job_id, "logic_supervisor", ast_result)

# 4. Return Ref: ID만 리턴 (State에는 ID만 기록, Checkpoint 최적화)
return {"logic_result_ref": result_id}
```

---

### 8. 4대 핵심 지표 체계

#### 지표 구성
```
최종 점수 = 0.30 × 논리력 + 0.30 × 전문성 + 0.20 × 안정성 + 0.20 × 진정성
```

| 주지표 | 세부 지표 | 산출 도구 | 가중치 |
|--------|----------|----------|--------|
| **논리력 (30%)** | | | 

---
### [서브에이전트] 최신 기술 스택 리서치 (Line 209)

Now I have comprehensive data. Let me compile the full research report.

---

# 실시간 AI 면접 어시스턴트 데스크탑 애플리케이션 기술 리서치 (2026년 2월 기준)

---

## 1. 데스크탑 프레임워크: Electron vs Tauri v2 vs Neutralino

### 비교 요약표

| 항목 | Electron (v33+) | Tauri v2 (v2.2+) | Neutralino (v5.x) |
|------|----------------|-------------------|---------------------|
| **번들 크기** | ~100MB+ | ~2-10MB | ~2-5MB |
| **메모리 사용** | ~200-400MB | ~30-40MB | ~30-50MB |
| **시작 시간** | 1-2초 | 0.5초 이하 | 0.5초 이하 |
| **네이티브 오디오** | desktopCapturer + electron-audio-loopback | tauri-plugin-mic-recorder, 커스텀 Rust 플러그인 | 지원 없음 (OS API 직접 불가) |
| **크로스 플랫폼** | macOS, Windows, Linux | macOS, Windows, Linux, iOS, Android | macOS, Windows, Linux |
| **생태계** | 매우 성숙 (npm 전체 생태계) | 빠르게 성장 중 (공식 플러그인 다수) | 미성숙 (npm 생태계 없음) |
| **렌더링 엔진** | Chromium 내장 | OS WebView (macOS: WebKit, Win: WebView2) | OS WebView |
| **백엔드 언어** | Node.js | Rust | C/C++ |

### 네이티브 오디오 캡처 상세

**Electron:**
- **macOS**: `desktopCapturer` API로 ScreenCaptureKit 또는 CoreAudio Taps 활용 가능. macOS 13.2+ 필요. Chromium 플래그(`MacLoopbackAudioForScreenShare`, `MacSckSystemAudioLoopbackOverride`)를 통해 외부 의존성 없이 시스템 오디오 캡처 가능
- **Windows**: Chromium 내장 WASAPI 루프백 캡처 지원
- `electron-audio-loopback` npm 패키지(v1.0.6): macOS 12.3+, Windows 10+, Linux에서 서드파티 루프백 드라이버 없이 시스템 오디오 캡처
- 마이크: `navigator.mediaDevices.getUserMedia()` 기본 지원

**Tauri v2:**
- `tauri-plugin-mic-recorder` (v2.0.0): cpal + hound 기반 마이크 녹음, WAV 파일 생성
- `tauri-plugin-audio-recorder`: 크로스 플랫폼(Windows/macOS/Linux/iOS/Android), WAV 16-bit PCM 출력, 품질 프리셋(Low 16kHz mono, Medium 44.1kHz mono, High 48kHz stereo)
- 시스템 오디오 루프백 캡처: 공식 플러그인 없음. Rust로 직접 CoreAudio(macOS) / WASAPI(Windows) 래핑 필요
- 장점: Rust 네이티브 코드로 레이턴시 300-400ms 절감 가능 (getUserMedia 대비)

**Neutralino:**
- 네이티브 오디오 API 접근 불가. 시스템 오디오 캡처 사실상 불가능
- **면접 어시스턴트 용도로 부적합**

### 추천

**Electron을 추천**. 이유:
1. 시스템 오디오 루프백 캡처가 `electron-audio-loopback` 패키지로 즉시 사용 가능
2. macOS ScreenCaptureKit 통합이 Chromium 레벨에서 지원됨
3. npm 생태계 전체 활용 가능 (오디오 처리, VAD, 벡터 DB 등)
4. 메모리 사용량이 높지만, 면접 어시스턴트는 단일 앱으로 장시간 구동하므로 번들 크기/시작 시간보다 기능 완성도가 중요

Tauri v2는 시스템 오디오 루프백 캡처를 위한 Rust 플러그인 직접 개발이 필요하여 개발 비용이 높음.

---

## 2. 실시간 STT API 비교

### 비교 요약표

| 항목 | Deepgram Nova-3 | AssemblyAI Universal-2 | Groq Whisper Large v3 | OpenAI Whisper API |
|------|----------------|----------------------|---------------------|-------------------|
| **실시간 스트리밍** | WebSocket 스트리밍 지원 | WebSocket 스트리밍 지원 | 스트리밍 미지원 (배치 전송) | 스트리밍 미지원 |
| **레이턴시** | ~300ms 이하 | ~300ms (P50) | 164x 실시간 속도 (배치) | Realtime API: ~232ms |
| **영어 WER** | ~8.1% (AssemblyAI 벤치) / ~6.84% (자체) | ~5.9% / ~6.68% | ~8.4% | 비공개 |
| **한국어 지원** | Tier 2 (WER 7-16%) | 99+ 언어, 한국어 포함 | Whisper v3: 99+ 언어 | 99+ 언어 |
| **화자 분리** | 지원 (추가 비용 없음 또는 ~$0.001-0.002/분) | 지원 ($0.02/시간 추가) | 미지원 | Realtime API에서 미지원 |
| **가격** | $0.0077/분 (스트리밍) | $0.0025/분 ($0.15/시간) | STT: $0.006/분 | Whisper: $0.006/분, Realtime: ~$0.50/콜 |

### 상세 분석

**Deepgram Nova-3:**
- WebSocket 기반 실시간 스트리밍의 업계 표준
- 도메인 특화 엔진 (의료용 Nova-3 Medical: WER 1-10%)
- 한국어는 Tier 2로 중간 수준 지원 (WER 7-16%)
- 스마트 포매팅, 자동 언어 감지, 키워드 부스팅 지원
- 멀티채널 지원으로 마이크/시스템 오디오 별도 처리 가능

**AssemblyAI Universal-2 / Universal-Streaming:**
- Universal-Streaming: 음성 에이전트용 초저지연 모델
- 99개 언어 동일 요금($0.27/시간)으로 다국어 지원이 가장 균일
- 무제한 동시 스트림, 자동 스케일링
- 화자 분리 95개 언어 지원 + 노이즈 환경 30% 정확도 향상 (2025 업데이트)

**Groq Whisper Large v3:**
- **실시간 스트리밍 미지원** -- 오디오 세그먼트를 버퍼링 후 배치 전송
- 262x 실시간 속도로 배치 처리 시 극도로 빠름
- 중간 결과(interim results) 미제공, 최종 전사만 반환
- 한국어 포함 99+ 언어 지원 (Whisper v3 기반)
- 면접 어시스턴트의 실시간 요구사항에는 부적합

**OpenAI Whisper API / Realtime API:**
- Whisper API: 배치 전용, 25MB 파일 크기 제한 (~30분), 스트리밍 미지원
- Realtime API: 232ms 레이턴시로 실시간 대화 지원하나 STT+LLM+TTS 통합 가격 체계로 비쌈 (~$0.50/콜)
- 면접 어시스턴트에서 STT만 분리 사용 시 비효율적

### 추천

**Deepgram Nova-3** 또는 **AssemblyAI Universal-Streaming** 추천.
- 실시간 스트리밍 필수이므로 Groq Whisper와 OpenAI Whisper는 탈락
- 한국어 면접 지원 시: AssemblyAI가 다국어 균일 지원으로 유리
- 가격 최적화 시: AssemblyAI ($0.15/시간)가 Deepgram ($0.46/시간)보다 저렴
- 화자 분리(면접관 vs 후보자 구분) 시: 둘 다 지원, AssemblyAI가 95개 언어에서 화자 분리 지원

---

## 3. Voice Activity Detection (VAD)

### 비교 요약표

| 항목 | Silero VAD | WebRTC VAD | Picovoice Cobra v2.1 | TEN-VAD |
|------|-----------|------------|---------------------|---------|
| **정확도 (TPR @5% FPR)** | 87.7% | 50% | 98.9% | 신규, 벤치마크 부족 |
| **WASM/브라우저 지원** | ONNX Runtime Web 지원 | 네이티브 지원 | 미지원 (네이티브 SDK) | 미확인 |
| **Electron 호환** | @ricky0123/vad npm 패키지 | 내장 | 별도 네이티브 바인딩 필요 | 미확인 |
| **레이턴시** | RTF 0.004 (1시간 오디오 15.4초) | 극도로 낮음 | 낮음 | 미확인 |
| **라이선스** | MIT (오픈소스) | BSD (오픈소스) | 상용 라이선스 | 오픈소스 |
| **학습 데이터** | 6000+ 언어 | 범용 | 수천 시간 다양한 환경 | 미확인 |
| **샘플링 레이트** | 8kHz, 16kHz | 8kHz, 16kHz, 32kHz, 48kHz | 다양 | 미확인 |

### 상세 분석

**Silero VAD:**
- ONNX Runtime Web/Node.js를 통해 브라우저/Electron에서 실행 가능
- `@ricky0123/vad` npm 패키지: 브라우저 및 Electron용 간단한 API 제공
- `koizuka/silero-vad-test`: Node.js + Electron 전용 통합 예제
- WebRTC VAD 대비 4배 적은 오류
- MIT 라이선스로 상용 사용 무료
- 6000+ 언어 학습 데이터로 한국어 환경에서도 안정적

**WebRTC VAD:**
- GMM 기반 전통적 신호 처리 방식
- Chromium/Electron에 이미 내장되어 별도 설치 불필요
- 정확도가 가장 낮음 (TPR 50% @5% FPR) -- 음성 2프레임 중 1프레임 누락
- 통합 복잡도 최소

**Picovoice Cobra v2.1:**
- 최고 정확도 (TPR 98.9%) -- Silero 대비 12배, WebRTC 대비 50배 적은 오류
- WASM/브라우저 네이티브 지원 없음 -- 네이티브 SDK만 제공
- **상용 라이선스 필요** (무료 tier 제한적)
- Electron에서 사용하려면 네이티브 노드 애드온 래핑 필요

**TEN-VAD (TEN Framework):**
- HuggingFace에 공개된 신규 VAD 모델 (`TEN-framework/ten-vad`)
- 아직 생태계 미성숙, 벤치마크 데이터 부족

### 추천

**Silero VAD + @ricky0123/vad** 조합 추천.
- Electron 환경에서 즉시 사용 가능한 npm 패키지 존재
- 정확도-통합 복잡도-비용 밸런스 최적
- ONNX Runtime Web으로 메인 스레드 차단 없이 실행 가능
- 무료 오픈소스

---

## 4. 로컬 벡터 데이터베이스

### 비교 요약표

| 항목 | LanceDB (@lancedb/lancedb v0.26.2) | ChromaDB (chromadb v3.3.0) | Qdrant (@qdrant/qdrant-js v1.16.2) |
|------|------------------------------------|--------------------------|------------------------------------|
| **임베디드 모드** | 네이티브 임베디드 (SQLite 스타일) | 임베디드 가능 (in-memory/persistent) | Python만 임베디드, Node.js는 서버 필요 |
| **Node.js/Electron 호환** | `@lancedb/lancedb` npm 네이티브 지원 | `chromadb` npm 지원 (Rust 코어 리라이트 2025) | REST API 클라이언트만 (외부 서버 필요) |
| **쿼리 레이턴시** | 40-60ms (IVF_PQ) | 미공개 (2025 Rust 리라이트로 4x 개선) | 20-30ms (HNSW) |
| **Recall@1** | ~88% | 미공개 | ~95% |
| **인덱싱 알고리즘** | IVF_PQ (클러스터링 + 양자화) | 미공개 | HNSW (그래프 기반) |
| **저장 효율** | 높음 (Lance 컬럼 포맷, 압축 우수) | 보통 | 높음 (24x 비대칭 양자화 2025) |
| **멀티모달 지원** | 벡터 + 메타데이터 + 이미지/텍스트 | 벡터 + 메타데이터 | 벡터 + 페이로드 필터링 |
| **디스크 스토리지** | 로컬 디스크 네이티브 | 지원 | 서버 모드에서만 |

### 상세 분석

**LanceDB (v0.26.2):**
- **Electron 최적 선택**: 서버 없이 앱 프로세스 내에서 직접 실행
- TypeScript/Node.js 네이티브 라이브러리 제공 (`npm i @lancedb/lancedb`)
- Lance 컬럼 포맷: 벡터 + 구조화 데이터 통합 저장, 제로 카피 읽기
- Continue.dev (VS Code AI 확장)에서 로컬 코드 임베딩용으로 채택
- 수십억 벡터 밀리초 단위 검색 가능
- 풀텍스트 검색 + SQL + 벡터 유사도 검색 통합
- 오브젝트 스토리지(S3 등) 네이티브 연동, 비활성 시 제로 스케일링

**ChromaDB (v3.3.0):**
- 2025년 Rust 코어 리라이트: 쓰기/쿼리 4x 속도 향상, 멀티스레딩 지원 (GIL 병목 제거)
- JavaScript SDK 제공, 로컬 서버 없이 사용 가능
- 개발자 편의성 최우선 설계
- 단, Electron 환경에서의 임베디드 모드 안정성 검증 사례가 LanceDB보다 적음

**Qdrant (v1.16.2 JS 클라이언트):**
- Node.js 클라이언트는 REST API 방식 -- **별도 Qdrant 서버 프로세스 필요**
- 임베디드 모드는 Python 클라이언트에서만 지원
- 최고 쿼리 성능 (20-30ms, Recall 95%) 이지만 Electron 앱에 서버를 번들링해야 함
- 2025 업데이트: 비대칭 양자화 24x 압축, Hybrid Cloud, RBAC
- 면접 어시스턴트의 로컬 앱 구조에는 과잉 설계

### 추천

**LanceDB** 추천.
1. Electron 프로세스 내 임베디드 실행 가능 (외부 서버 불필요)
2. TypeScript/Node.js 퍼스트 클래스 지원
3. 로컬 디스크 저장으로 앱 종료 후에도 데이터 영속
4. 벡터 + SQL + 풀텍스트 하이브리드 검색
5. Continue.dev 사례로 Electron 환경 검증됨

---

## 5. 초저지연 LLM API

### 비교 요약표

| 항목 | Groq | Cerebras | SambaNova | Together AI |
|------|------|----------|-----------|-------------|
| **TTFT (Time to First Token)** | ~0.14초 (Llama 70B) | ~0.24초 (Llama 405B), ~0.35초 (70B) | 미공개 | 미공개 |
| **출력 속도 (Llama 8B)** | ~600.9 t/s | ~1,999.2 t/s | ~906.4 t/s | 미공개 |
| **출력 속도 (Llama 70B)** | ~750 t/s | ~445 t/s | ~580 t/s | 미공개 |
| **출력 속도 (Llama 405B)** | 미공개 | ~969 t/s | 미공개 | 미공개 |
| **가격 (Llama 70B)** | $0.64/M tokens | $0.60/M tokens | 미공개 (AWS Outposts) | GPT-4o 대비 11x 저렴 |
| **스트리밍** | 지원 | 지원 | 지원 | 지원 |
| **한국어 품질** | Llama 모델 의존 (중간) | Llama 모델 의존 (중간) | Llama 모델 의존 (중간) | 200+ 모델 선택 가능 |
| **무료 tier

---
### [어시스턴트] STT 종합 비교 (Line 218)

### 실시간 STT 서비스 종합 비교 (한국어+영어, 2026년 2월 기준)

| 서비스 | 실시간 스트리밍 | 한국어 WER | 레이턴시 | 화자분리 | 가격 |
|--------|:---:|---|---|:---:|---|
| **Deepgram Nova-3** | WebSocket | Tier 2 (7-16%) | <300ms | 내장 | $0.0077/분 ($0.46/hr) |
| **ElevenLabs Scribe v2 RT** | WebSocket | "Good" (10-20%) | **~150ms** | 미확인 | 별도 확인 필요 |
| **AssemblyAI Universal-Streaming** | WebSocket | 99+ 언어 균일 지원 | ~300ms | 내장 (95개 언어) | **$0.0025/분 ($0.15/hr)** |
| **Soniox** | WebSocket | 60+ 언어 | 미공개 | **실시간 내장** | Speechmatics 대비 2-3x 저렴 |
| **Speechmatics** | WebSocket | 55+ 언어 | <1s | 내장 | 프리미엄 |
| **Groq Whisper v3** | **배치만** | 99+ 언어 | 배치 164x속도 | 미지원 | $0.006/분 |
| **OpenAI Whisper** | **배치만** | 99+ 언어 | - | 미지원 | $0.006/분 |

**핵심 판단 기준:**
1. **실시간 스트리밍 필수** → Groq Whisper, OpenAI Whisper 탈락
2. **한국어 정확도** → Reddit 피드백: "아시아 언어에서 Deepgram/AssemblyAI 정확도 급락" 경고
3. **화자분리 필요** (오프라인 면접) → ElevenLabs는 화자분리 미확인
4. **가격** → AssemblyAI가 3x 저렴

**추천 (수정):**

| 순위 | 서비스 | 이유 |
|------|--------|------|
| 1 | **Deepgram Nova-3** | 한국어 WER 최저(7-16%), 멀티채널 지원, 화자분리 내장 |
| 2 | **AssemblyAI Universal-Streaming** | 가격 최저($0.15/hr), 95개 언어 화자분리, 노이즈 환경 30% 정확도 향상 |
| 3 | **ElevenLabs Scribe v2 RT** | 레이턴시 최저(150ms), 한국어 정확도는 약간 떨어짐 |

**설계 방향**: STT 인터페이스 추상화 후, MVP에서 Deepgram으로 시작하고 한국어 실제 테스트 결과에 따라 교체 가능하게 설계.

### [어시스턴트] 종합 기술 스택 추천 (Line 225)

좋습니다! STT는 **Deepgram Nova-3** + 인터페이스 추상화로 확정. 사용자가 전체 최신 기술 선택지를 다시 보고 싶다고 하셨으니, 종합 기술 스택 추천표를 정리합니다.

---

## Jittda Live — 종합 기술 스택 추천 (2026년 2월 기준)

### 1. 데스크탑 프레임워크

| 항목 | Electron (v33+) | Tauri v2 (v2.2+) | Neutralino |
|------|:---:|:---:|:---:|
| **번들 크기** | ~100MB+ | ~2-10MB | ~2-5MB |
| **메모리** | ~200-400MB | ~30-40MB | ~30-50MB |
| **시스템 오디오 캡처** | `electron-audio-loopback` 즉시 사용 | Rust 직접 래핑 필요 | 불가 |
| **npm 생태계** | 전체 사용 가능 | 제한적 | 없음 |
| **추천** | **MVP 추천** | 향후 마이그레이션 고려 | 탈락 |

### 2. 오디오 캡처

| 항목 | 기술 | 비고 |
|------|------|------|
| **macOS 시스템 오디오** | `electron-audio-loopback` (ScreenCaptureKit) | macOS 12.3+ |
| **Windows 시스템 오디오** | `electron-audio-loopback` (WASAPI Loopback) | Windows 10+ |
| **마이크** | `navigator.mediaDevices.getUserMedia()` | Chromium 내장 |

### 3. VAD (Voice Activity Detection)

| 항목 | Silero VAD | WebRTC VAD | Picovoice Cobra |
|------|:---:|:---:|:---:|
| **정확도 (TPR@5%FPR)** | **87.7%** | 50% | 98.9% |
| **Electron WASM** | `@ricky0123/vad` npm | 내장 | 네이티브만 |
| **라이선스** | MIT (무료) | BSD (무료) | 상용 |
| **추천** | **MVP 추천** | 백업 | 과잉 |

### 4. STT (Speech-to-Text)

| 항목 | Deepgram Nova-3 | AssemblyAI | ElevenLabs Scribe v2 |
|------|:---:|:---:|:---:|
| **한국어 WER** | **7-16%** | 균일 지원 | 10-20% |
| **레이턴시** | <300ms | ~300ms | ~150ms |
| **화자분리** | 내장 | 내장 (95개 언어) | 미확인 |
| **멀티채널** | 지원 | 지원 | 미확인 |
| **가격** | $0.46/hr | **$0.15/hr** | 별도 확인 |
| **추천** | **MVP 추천** | 대안 | 레이턴시 우선 시 |

### 5. 로컬 벡터 DB

| 항목 | LanceDB (v0.26) | ChromaDB (v3.3) | Qdrant |
|------|:---:|:---:|:---:|
| **임베디드 모드** | **네이티브** | 가능 | Python만 |
| **Node.js/Electron** | `@lancedb/lancedb` npm | `chromadb` npm | REST API만 |
| **쿼리 레이턴시** | 40-60ms | 미공개 | 20-30ms |
| **서버 불필요** | **예** | 예 | 아니오 |
| **추천** | **MVP 추천** | 대안 | 탈락 (서버 필요) |

### 6. 초저지연 LLM (실시간 질문 생성)

| 항목 | Groq | Cerebras | Together AI | SambaNova |
|------|:---:|:---:|:---:|:---:|
| **TTFT** | **~0.14초** | ~0.24초 | 미공개 | 미공개 |
| **출력 속도 (70B)** | ~750 t/s | ~445 t/s | 미공개 | ~580 t/s |
| **한국어 품질** | Llama 의존 (중간) | Llama 의존 (중간) | **Qwen/SOLAR 선택 가능** | 미공개 |
| **가격 (70B)** | $0.64/M tokens | $0.60/M tokens | GPT-4o 대비 11x 저렴 | 미공개 |
| **무료 tier** | 제한적 | 30 RPM/1M tok/day | 제한적 | 없음 |
| **추천** | **MVP 추천 (TTFT)** | 대안 | 한국어 품질 보완 | 탈락 |

### 7. 확정 추천 스택 요약

| 계층 | 선택 | 이유 |
|------|------|------|
| **데스크탑** | Electron v33+ | 시스템 오디오 캡처 생태계 최성숙 |
| **오디오 캡처** | electron-audio-loopback | macOS/Windows, 외부 드라이버 불필요 |
| **VAD** | Silero VAD + @ricky0123/vad | WASM, 87.7% TPR, MIT, Electron 즉시 통합 |
| **STT** | Deepgram Nova-3 | 한국어 WER 최저, 멀티채널, 화자분리 |
| **로컬 벡터 DB** | LanceDB v0.26 | 서버 없는 임베디드, TS 네이티브 |
| **실시간 LLM** | Groq (TTFT 0.14초) | 실시간 질문 생성 최적 |
| **한국어 보완** | Together AI (Qwen-2.5/SOLAR) | 한국어 특화 모델 선택지 |

---

다음 설계 명확화 질문으로 넘어가겠습니다.

### [어시스턴트] 리포트/스코어카드 확정 (Line 240)

전체 리포트 확정 — 스코어카드 + 대화 타임라인 + 심층 분석 + 시각화 + v5.0 결과 페이지 통합. 마지막 핵심 질문입니다:

### [어시스턴트] 요구사항 확정 요약 (Line 255)

## 확정된 요구사항 요약

| 항목 | 결정 |
|------|------|
| **프로젝트 관계** | 웹 유지 + 질문 생성을 라이브로 이동 + 데이터/결과 양쪽 공유 |
| **타겟 OS** | macOS 우선 + 인터페이스 추상화 (Windows 확장성) |
| **면접 유형** | 온라인 (채널 분리) + 오프라인 (AI 화자분리) 둘 다 |
| **STT** | Deepgram Nova-3 + 인터페이스 추상화 |
| **서버 통신** | REST (전/후) + WebSocket (면접 중) |
| **질문 생성** | 하이브리드 (AI 자동 추천 + 면접관 수동 요청) |
| **결과 분석** | 전체 리포트 (스코어카드 + 타임라인 + 시각화 + v5.0 통합) |
| **사전 분석** | v5.0 분석 필수 선행 → Live에 동기화 |
| **기술 스택** | Electron + Silero VAD + Deepgram + LanceDB + Groq LLM |

---

## 아키텍처 접근법 3가지 제안

이제 전체 시스템 아키텍처를 어떻게 구성할지 3가지 접근법을 비교합니다.

### 접근법 A: Monorepo 확장 (추천)

```
jittda/                          # 기존 v5.0 Monorepo 확장
├── backend/                     # 기존 v5.0 서버 (FastAPI + LangGraph)
│   └── src/interface/api/
│       └── routes/live.py       # 🆕 Live 면접용 REST + WebSocket 엔드포인트
├── frontend/                    # 기존 웹 프론트엔드 (React 19)
│   └── src/pages/LiveResult/    # 🆕 라이브 면접 결과 페이지
├── desktop/                     # 🆕 Electron 데스크탑 앱
│   ├── package.json
│   ├── electron/
│   │   ├── main.ts              # Main Process (오디오 캡처, IPC)
│   │   ├── preload.ts
│   │   └── audio/               # OS별 오디오 캡처 모듈
│   ├── src/                     # Renderer (React, 면접관 대시보드)
│   │   ├── components/
│   │   ├── services/
│   │   │   ├── stt-client.ts    # Deepgram WebSocket
│   │   │   ├── vad-engine.ts    # Silero VAD (WASM)
│   │   │   ├── lance-store.ts   # LanceDB 로컬 벡터 검색
│   │   │   └── llm-client.ts    # Groq LLM 질문 생성
│   │   └── stores/              # Zustand 이벤트 버스
│   └── forge.config.ts          # Electron Forge 빌드
└── shared/                      # 🆕 공유 타입/모델
    └── types/
```

**장점:** 공유 타입/모델, 단일 CI/CD, 백엔드 변경 즉시 반영
**단점:** 레포가 커짐, 빌드 복잡도 증가

---

### 접근법 B: 독립 레포 + API 연동

```
jittda/                          # 기존 v5.0 (변경 최소)
├── backend/                     # REST API + WebSocket 엔드포인트 추가만
└── frontend/

jittda-live/                     # 🆕 완전 독립 레포
├── package.json
├── electron/
├── src/
└── shared/                      # npm 패키지로 공유 타입 발행
```

**장점:** 완전 독립 개발/배포, v5.0 영향 최소
**단점:** 타입 동기화 부담, 별도 CI/CD, API 계약 관리 필요

---

### 접근법 C: Turborepo 기반 워크스페이스

```
jittda-platform/                 # Turborepo 루트
├── turbo.json
├── apps/
│   ├── backend/                 # 기존 v5.0 서버
│   ├── web/                     # 기존 웹 프론트엔드
│   └── desktop/                 # 🆕 Electron 앱
└── packages/
    ├── shared-types/            # 공유 TypeScript 타입
    ├── api-client/              # 서버 API 클라이언트 (web + desktop 공유)
    └── ui-components/           # 공유 UI 컴포넌트
```

**장점:** 패키지 공유 체계적, 빌드 캐시, 의존성 명확
**단점:** 기존 프로젝트 구조 대폭 변경 필요, Turborepo 학습 비용

---

### 비교 요약

| 기준 | A: Monorepo 확장 | B: 독립 레포 | C: Turborepo |
|------|:---:|:---:|:---:|
| **v5.0 영향** | 중간 (디렉토리 추가) | 최소 | 대폭 (구조 변경) |
| **타입 공유** | 직접 import | npm 패키지 | 워크스페이스 패키지 |
| **개발 속도** | **빠름** | 보통 | 초기 느림 → 이후 빠름 |
| **배포 독립성** | 가능 | **완전 독립** | 가능 |
| **MVP 적합성** | **높음** | 높음 | 낮음 |

**추천: 접근법 A (Monorepo 확장)**
- v5.0과 데이터 모델/타입을 직접 공유하므로 개발 속도가 가장 빠름
- `desktop/`만 추가하면 되므로 기존 코드 변경 최소
- 백엔드에 Live 엔드포인트만 추가하는 수준

---
## Phase 3: 아키텍처 접근법 제안

### [어시스턴트] (Line 255)

## 확정된 요구사항 요약

| 항목 | 결정 |
|------|------|
| **프로젝트 관계** | 웹 유지 + 질문 생성을 라이브로 이동 + 데이터/결과 양쪽 공유 |
| **타겟 OS** | macOS 우선 + 인터페이스 추상화 (Windows 확장성) |
| **면접 유형** | 온라인 (채널 분리) + 오프라인 (AI 화자분리) 둘 다 |
| **STT** | Deepgram Nova-3 + 인터페이스 추상화 |
| **서버 통신** | REST (전/후) + WebSocket (면접 중) |
| **질문 생성** | 하이브리드 (AI 자동 추천 + 면접관 수동 요청) |
| **결과 분석** | 전체 리포트 (스코어카드 + 타임라인 + 시각화 + v5.0 통합) |
| **사전 분석** | v5.0 분석 필수 선행 → Live에 동기화 |
| **기술 스택** | Electron + Silero VAD + Deepgram + LanceDB + Groq LLM |

---

## 아키텍처 접근법 3가지 제안

이제 전체 시스템 아키텍처를 어떻게 구성할지 3가지 접근법을 비교합니다.

### 접근법 A: Monorepo 확장 (추천)

```
jittda/                          # 기존 v5.0 Monorepo 확장
├── backend/                     # 기존 v5.0 서버 (FastAPI + LangGraph)
│   └── src/interface/api/
│       └── routes/live.py       # 🆕 Live 면접용 REST + WebSocket 엔드포인트
├── frontend/                    # 기존 웹 프론트엔드 (React 19)
│   └── src/pages/LiveResult/    # 🆕 라이브 면접 결과 페이지
├── desktop/                     # 🆕 Electron 데스크탑 앱
│   ├── package.json
│   ├── electron/
│   │   ├── main.ts              # Main Process (오디오 캡처, IPC)
│   │   ├── preload.ts
│   │   └── audio/               # OS별 오디오 캡처 모듈
│   ├── src/                     # Renderer (React, 면접관 대시보드)
│   │   ├── components/
│   │   ├── services/
│   │   │   ├── stt-client.ts    # Deepgram WebSocket
│   │   │   ├── vad-engine.ts    # Silero VAD (WASM)
│   │   │   ├── lance-store.ts   # LanceDB 로컬 벡터 검색
│   │   │   └── llm-client.ts    # Groq LLM 질문 생성
│   │   └── stores/              # Zustand 이벤트 버스
│   └── forge.config.ts          # Electron Forge 빌드
└── shared/                      # 🆕 공유 타입/모델
    └── types/
```

**장점:** 공유 타입/모델, 단일 CI/CD, 백엔드 변경 즉시 반영
**단점:** 레포가 커짐, 빌드 복잡도 증가

---

### 접근법 B: 독립 레포 + API 연동

```
jittda/                          # 기존 v5.0 (변경 최소)
├── backend/                     # REST API + WebSocket 엔드포인트 추가만
└── frontend/

jittda-live/                     # 🆕 완전 독립 레포
├── package.json
├── electron/
├── src/
└── shared/                      # npm 패키지로 공유 타입 발행
```

**장점:** 완전 독립 개발/배포, v5.0 영향 최소
**단점:** 타입 동기화 부담, 별도 CI/CD, API 계약 관리 필요

---

### 접근법 C: Turborepo 기반 워크스페이스

```
jittda-platform/                 # Turborepo 루트
├── turbo.json
├── apps/
│   ├── backend/                 # 기존 v5.0 서버
│   ├── web/                     # 기존 웹 프론트엔드
│   └── desktop/                 # 🆕 Electron 앱
└── packages/
    ├── shared-types/            # 공유 TypeScript 타입
    ├── api-client/              # 서버 API 클라이언트 (web + desktop 공유)
    └── ui-components/           # 공유 UI 컴포넌트
```

**장점:** 패키지 공유 체계적, 빌드 캐시, 의존성 명확
**단점:** 기존 프로젝트 구조 대폭 변경 필요, Turborepo 학습 비용

---

### 비교 요약

| 기준 | A: Monorepo 확장 | B: 독립 레포 | C: Turborepo |
|------|:---:|:---:|:---:|
| **v5.0 영향** | 중간 (디렉토리 추가) | 최소 | 대폭 (구조 변경) |
| **타입 공유** | 직접 import | npm 패키지 | 워크스페이스 패키지 |
| **개발 속도** | **빠름** | 보통 | 초기 느림 → 이후 빠름 |
| **배포 독립성** | 가능 | **완전 독립** | 가능 |
| **MVP 적합성** | **높음** | 높음 | 낮음 |

**추천: 접근법 A (Monorepo 확장)**
- v5.0과 데이터 모델/타입을 직접 공유하므로 개발 속도가 가장 빠름
- `desktop/`만 추가하면 되므로 기존 코드 변경 최소
- 백엔드에 Live 엔드포인트만 추가하는 수준

### [어시스턴트] (Line 261)

아, v5.0이 아직 미구현 상태군요! 그러면 설계 관점이 완전히 달라집니다. **처음부터 통합 설계**가 가능합니다.

v5.0(분석 엔진)과 Jittda Live(실시간 면접)를 처음부터 하나의 시스템으로 설계하면:

### 통합 vs MSA 비교

| 기준 | 통합 (Recommended) | MSA (분리) |
|------|:---:|:---:|
| **v5.0 미구현 상태에서** | 처음부터 일관된 구조 | 경계 정의가 어려움 (아직 뭘 분리할지 모름) |
| **데이터 공유** | DB 직접 공유 | API 통신 필요 (오버헤드) |
| **개발 인원** | 1명 (상훈님) | MSA는 팀 규모에 적합 |
| **배포 복잡도** | Docker Compose 하나 | 서비스별 배포 관리 |
| **코드 중복** | 없음 | 모델/타입 중복 가능 |

**1인 개발에서 MSA는 과잉 설계입니다.** 처음부터 통합 Monorepo로 가는 것이 맞습니다.

### 수정된 아키텍처: 통합 Monorepo (v5.0 + Live 일체형)

```
jittda/                              # 통합 프로젝트
├── backend/                         # 단일 백엔드 (분석 + 라이브)
│   └── src/
│       ├── interface/api/routes/
│       │   ├── jobs.py              # 분석 Job CRUD + WebSocket
│       │   ├── live.py              # 🆕 라이브 면접 세션 API
│       │   └── auth.py
│       ├── application/
│       │   ├── graphs/              # LangGraph HMAS (코드 분석)
│       │   └── live/                # 🆕 라이브 면접 서비스
│       │       ├── session_manager.py
│       │       ├── realtime_analyzer.py
│       │       └── scorecard_generator.py
│       ├── domain/                  # 분석 + 라이브 공용 도메인
│       └── infrastructure/          # 외부 서비스 어댑터
│
├── frontend/                        # 웹 (분석 결과 + 라이브 결과 열람)
│
├── desktop/                         # 🆕 Electron (실시간 면접 가이드)
│   ├── electron/                    # Main Process
│   └── src/                         # Renderer (면접관 대시보드)
│
├── shared/                          # 웹 + 데스크탑 공유 타입
│
└── infra/                           # Docker, DB, Tunnel
```

**핵심:** 백엔드가 하나이므로 분석 결과와 라이브 면접 데이터가 같은 DB에 존재하고, 웹과 데스크탑 모두 같은 API를 통해 접근합니다.

### [어시스턴트] (Line 276)

---

## 설계 섹션 1: 전체 시스템 아키텍처

### 1.1 서비스 구성

```
┌─────────────────────────────────────────────────────────────────┐
│                     jittda/ (통합 Monorepo)                      │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  backend/         │  │  frontend/        │  │  desktop/      │  │
│  │  (Python/FastAPI) │  │  (React 19/Vite) │  │  (Electron)    │  │
│  │                   │  │                   │  │                │  │
│  │  - 코드 분석      │  │  - 분석 결과 열람  │  │  - 실시간 면접  │  │
│  │  - 라이브 세션 관리│  │  - 라이브 결과 열람│  │  - 오디오 캡처  │  │
│  │  - 면접 후 분석   │  │  - Job 관리       │  │  - STT/VAD     │  │
│  │                   │  │                   │  │  - 로컬 RAG    │  │
│  │  REST + WebSocket │  │  REST 호출        │  │  - LLM 질문    │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬───────┘  │
│           │                      │                      │          │
│  ┌────────┴──────────────────────┴──────────────────────┴───────┐  │
│  │                    shared/ (TypeScript 타입)                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  infra/ (PostgreSQL 16 + pgvector, Redis 7, Cloudflare)      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 1.2 면접 전체 플로우

```
[Phase 1: 사전 분석] (서버)
    JD + GitHub + 이력서 + LinkedIn 입력
         ↓
    v5.0 LangGraph HMAS 분석 (코드 분석, Identity Resolution, 4대 지표)
         ↓
    분석 결과 DB 저장 + 벡터 임베딩 생성

[Phase 2: 면접 준비] (데스크탑 앱)
    면접관이 앱 실행 → 지원자 선택
         ↓
    서버에서 분석 결과 + 벡터 데이터 다운로드 → LanceDB 로컬 적재
         ↓
    면접 세션 생성 (온라인/오프라인 선택)

[Phase 3: 실시간 면접] (데스크탑 앱, Local-First)
    오디오 캡처 → VAD → STT → 실시간 전사
         ↓
    대화 분석 → 로컬 RAG 검색 → LLM 질문 생성
         ↓
    토픽 커버리지 추적 → 동적 카드 표시 → 데이터 충분 시 종료 안내

[Phase 4: 면접 후 분석] (서버)
    전체 전사 + 면접 데이터 서버 업로드
         ↓
    AI 종합 분석 → 스코어카드 + 리포트 생성
         ↓
    웹 + 앱 양쪽에서 결과 열람 가능
```

### 1.3 기술 스택 (확정)

| 계층 | 기술 | 용도 |
|------|------|------|
| **백엔드** | Python 3.11 + FastAPI + LangGraph 1.0+ | 분석 + 라이브 세션 관리 |
| **웹 프론트엔드** | React 19 + Vite + Tailwind 4 + D3.js | 결과 시각화 |
| **데스크탑** | Electron v33+ | 실시간 면접 가이드 |
| **오디오 캡처** | electron-audio-loopback (macOS 우선) | OS 네이티브 |
| **VAD** | Silero VAD + @ricky0123/vad (WASM) | 엣지 음성 감지 |
| **STT** | Deepgram Nova-3 (WebSocket) | 실시간 전사 |
| **로컬 벡터 DB** | LanceDB v0.26 (임베디드) | Local-First RAG |
| **실시간 LLM** | Groq (TTFT 0.14초) | 질문 동적 생성 |
| **서버 LLM** | Kimi K2.5 + Instructor + Langfuse | 분석 + 질문 품질 |
| **DB** | PostgreSQL 16 + pgvector | 통합 데이터 저장 |
| **캐시** | Redis 7 | LLM 캐시, Rate Limit |
| **인프라** | Docker Compose + Cloudflare Tunnel | 배포 |

---

이 전체 아키텍처 구조가 괜찮으신가요? 수정할 부분이 있으면 말씀해주세요, 다음 섹션(데스크탑 앱 상세 아키텍처)으로 넘어가겠습니다.

---
## Phase 4: 상세 설계 (섹션별)

### [사용자] PostgreSQL 한계 지적 (Line 283)

> 면접자의 깃 분석데이터나 레주메 커버레터 포트폴리오 링크드인 정보들에서 가져온것들을 postgres 만으로 효율적으로 정보 추출하기 힘들것같은데 실시간으로 해당정보 바탕으로 질문을 생성해야하는데 말이 안되는것같아 그래프 나 rag를 사용해서 하ㄷㄴ가 해야할것같은데 그래프rag 기술도 있는데 뭐가 가종좋을지랑 해당 기술을 우리 에게 적용하는것에 대해 어떻게 생각해?

### [어시스턴트] Knowledge Graph 분석 (Line 286)

핵심적인 지적입니다. 실시간 면접에서 PostgreSQL만으로는 **"지원자가 Redis 캐싱을 언급했을 때 → 이력서에는 팀 프로젝트라고 적혀 있고 → 코드에서는 단독 구현 흔적 → 모순점 발견 → 꼬리질문 생성"** 같은 **다중 관계 추론**이 불가능합니다.

이 부분을 깊이 분석해보겠습니다.

### [어시스턴트] 하이브리드 KG + Vector 접근법 (Line 333)

분석이 완료되었습니다. 상훈님 말씀이 정확합니다 — PostgreSQL만으로는 면접 중 실시간 다중 관계 추론이 불가능합니다.

---

## 왜 PostgreSQL만으로는 안 되는가?

면접 중 실제로 필요한 질의 유형:

| 질의 유형 | 예시 | PostgreSQL | 벡터 DB | Knowledge Graph |
|-----------|------|:---:|:---:|:---:|
| **의미 검색** | "캐시"와 관련된 모든 정보 찾기 | SQL LIKE (부정확) | **벡터 유사도** | - |
| **관계 탐색** | Redis 경험의 출처 추적 (이력서→코드→LinkedIn) | JOIN 가능하지만 느림 | 불가 | **그래프 탐색** |
| **모순 탐지** | "이력서: 팀 프로젝트" vs "발화: 혼자 구축" vs "blame: 95%" | 불가 | 불가 | **삼각 검증** |
| **다중 홉 추론** | "JD 요구 스킬 중 미검증 항목은?" | 복잡한 서브쿼리 | 불가 | **1-2홉 탐색** |
| **실시간 갱신** | 면접 중 발화 추가 → 교차 참조 | 가능하지만 서버 왕복 | 로컬 가능 | 로컬 가능 |

---

## 3가지 접근법 비교

### 접근법 A: 순수 GraphRAG (Microsoft 방식)
- 모든 텍스트(이력서, LinkedIn, 코드 분석)를 LLM으로 엔티티/관계 자동 추출 → 그래프 구축
- Community Detection으로 계층적 요약 생성
- **단점:** 구축 비용 3-5x (모든 텍스트를 LLM 처리). 우리는 이미 v5.0에서 구조화된 분석 결과를 갖고 있으므로 LLM으로 다시 그래프를 만들 이유가 없음

### 접근법 B: 서버 Neo4j + 클라이언트 REST
- 서버에 Neo4j 배포, 면접 중 Cypher 쿼리로 관계 탐색
- **단점:** Local-First 위반. 네트워크 지연. 면접 중 서버 의존

### 접근법 C: 하이브리드 — 서버 Knowledge Graph + 클라이언트 로컬 검색 (추천)

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

---

## 추천: 접근법 C — 하이브리드 로컬 Knowledge Graph + Vector

### 실제 면접 시뮬레이션

**지원자 발화:** "Redis를 써서 속도를 많이 높였고, 혼자서 캐싱 레이어를 다 구축했습니다"

```
Step 1: STT 수신 (300ms)

Step 2: LanceDB 벡터 검색 (20ms)
  → 이력서 청크: "ABC 회사 팀 프로젝트로 Redis 캐시 구현"
  → 코드 분석: "redis_cache.py — CC:8, 순수 기여도 95%"
  → LinkedIn: "ABC Corp — Backend Developer"

Step 3: graphology 그래프 탐색 (5ms)
  → (Candidate)─[HAS_SKILL]→(Redis)─[EVIDENCE]→(GitCommit{blame: 95%})
  → (Candidate)─[CLAIMED]→(Claim{"팀 프로젝트", src: resume})
  → (Claim{"팀 프로젝트"})─[CONTRADICTS]→(발화{"혼자 구축"})
  → (Redis)─[REQUIRED_BY]→(JD{priority: high})

Step 4: 하이브리드 컨텍스트 → Groq LLM (640ms)
  → 모순 정보 + 코드 증거 → 꼬리질문 생성

전체: ~670ms (발화 종료 → 질문 카드 표시)
```

### Knowledge Graph 스키마

```
(Candidate) ─[HAS_SKILL]──────→ (Skill)
             ─[WORKED_AT]──────→ (Company) ─[ROLE]→ (Position)
             ─[CONTRIBUTED_TO]─→ (Repo) ─[USED_TECH]→ (Tech)
             ─[CLAIMED]────────→ (Claim) ─[SOURCE]→ (Resume|LinkedIn|CoverLetter)
             ─[SCORED]─────────→ (Score) ─[IN_CATEGORY]→ (Category)

(Skill)      ─[EVIDENCE]──────→ (Evidence{type: git|resume|linkedin})
(Evidence)   ─[SUPPORTS|CONTRADICTS]→ (Claim)
(Repo)       ─[HAS_FILE]──────→ (File) ─[COMPLEXITY]→ (Metric)
(JD)         ─[REQUIRES]──────→ (Skill{priority: high|medium|low})
```

### 기술 스택

| 위치 | 기술 | 역할 |
|------|------|------|
| **서버** | NetworkX (Python) | 분석 결과 → Knowledge Graph 구축 |
| **서버** | PostgreSQL + pgvector | 원본 데이터 영속 저장 |
| **동기화** | JSON 직렬화 + LanceDB export | 그래프 + 벡터를 클라이언트로 전송 |
| **클라이언트** | [graphology](https://graphology.github.io/) (JS) | 인메모리 그래프 탐색 (<5ms) |
| **클라이언트** | LanceDB (임베디드) | 벡터 의미 검색 (<60ms) |
| **클라이언트** | HybridQueryEngine (자체) | 벡터 + 그래프 결합 쿼리 |

### 왜 GraphRAG(Microsoft)가 아닌가?

| 기준 | Microsoft GraphRAG | 우리 방식 (하이브리드) |
|------|:---:|:---:|
| **그래프 구축** | LLM으로 자동 추출 (비쌈) | v5.0 분석 결과로 직접 구축 (무료) |
| **구축 비용** | 3-5x (LLM 토큰) | 0 (이미 구조화된 데이터) |
| **실시간 갱신** | 어려움 | graphology 인메모리 즉시 추가 |
| **Local-First** | 서버 필요 | 완전 로컬 |
| **도메인 특화** | 범용 | 면접 도메인 최적화 |

> v5.0이 이미 코드 분석, Identity Resolution, 스킬 추출, 복잡도 측정 등을 수행하므로, **그 결과를 그래프 노드/엣지로 직접 매핑**하는 것이 GraphRAG보다 정확하고 저렴합니다. GraphRAG의 Community Detection 아이디어만 차용하여 역량별 클러스터링 + 요약에 활용합니다.

Sources:
- [GraphRAG & Knowledge Graphs 2026](https://flur.ee/fluree-blog/graphrag-knowledge-graphs-making-your-data-ai-ready-for-2026/)
- [Knowledge Graphs vs RAG 비교](https://atlan.com/know/knowledge-graphs-vs-rag-for-ai/)
- [graphology - JS 그래프 라이브러리](https://graphology.github.io/)

---

이 하이브리드 Knowledge Graph + Vector 접근법에 대해 어떻게 생각하시나요? 동의하시면 수정된 아키텍처에 반영하고 다음 설계 섹션으로 넘어가겠습니다.

### [사용자] 분석 시 그래프 구축 제안 (Line 340)

> v5.0 으로 분석할떄 바로바로 그래프 래그에 해당 데이터를 주입하고 통합하면 되지않나? 그렇게 하면 한번에 될것같은데 분석결과를 낼때도 효율성이 증되될 수 있을것 같은데 이건 어떻게 생각해?

### [어시스턴트] 분석-그래프 동시 구축 확정 (Line 349)

완전히 맞는 말입니다. **분석하면서 동시에 그래프를 구축**하면 일석이조입니다.

## Graph-First 분석 파이프라인

기존 v5.0 설계에서 각 Worker가 독립적으로 결과를 DB에 저장했다면, 이제는 **Knowledge Graph가 분석의 중심축**이 됩니다.

### 기존 설계 (분석 결과 분산)

```
CollectorWorker → analysis_results 테이블에 JSON 저장
CleanerWorker   → analysis_results 테이블에 JSON 저장
SkillExtractor  → analysis_results 테이블에 JSON 저장
  ...각자 따로 저장, 나중에 ProfileSynthesizer가 전부 불러서 합침
```

**문제:** Worker 간 교차 참조 불가. ProfileSynthesizer가 모든 JSON을 합치는 병목.

### 개선 설계 (그래프 중심)

```
CollectorWorker → 그래프에 노드/엣지 추가 (Repo, Tech, Company...)
                     ↓ 그래프가 점점 성장
CleanerWorker   → 기존 노드에 blame 속성 추가, 새 엣지 연결
                     ↓
SkillExtractor  → 그래프 쿼리로 선행 결과 활용 → 스킬 노드 + EVIDENCE 엣지
                     ↓
ComplexityMeter → 파일 노드에 복잡도 속성 추가
                     ↓
VibectorWorker  → AI 의심 구간 엣지 추가
                     ↓
ProfileSynthesizer → 그래프 순회 한 번으로 통합 프로필 완성!
```

### 구체적 Worker별 그래프 주입 흐름

```python
# Worker 1: CollectorWorker
graph.add_node("candidate:kim", type="Candidate", name="김개발")
graph.add_node("repo:abc-api", type="Repo", url="github.com/kim/abc-api")
graph.add_node("tech:redis", type="Tech")
graph.add_node("company:abc", type="Company")
graph.add_edge("candidate:kim", "repo:abc-api", rel="CONTRIBUTED_TO")
graph.add_edge("repo:abc-api", "tech:redis", rel="USED_TECH")
graph.add_edge("candidate:kim", "company:abc", rel="WORKED_AT", 
               role="Backend Dev", source="linkedin")

# Worker 2: CleanerWorker (선행 그래프 활용!)
graph.add_edge("candidate:kim", "repo:abc-api", rel="BLAME_RATIO", 
               ratio=0.95)  # 이미 있는 노드에 속성 추가

# Worker 3: SkillExtractor (그래프 쿼리로 교차 검증!)
# "이 지원자의 모든 Repo에서 사용된 기술 + blame 비율은?"
for tech in graph.neighbors("candidate:kim", filter=rel="USED_TECH"):
    evidence = graph.get_edge_data("candidate:kim", tech)
    graph.add_node(f"skill:{tech}", type="Skill", proficiency="advanced",
                   evidence_count=3, evidence_sources=["git", "resume"])
    graph.add_edge(f"skill:{tech}", "repo:abc-api", rel="EVIDENCE",
                   strength="strong")

# Worker 4: 이력서 분석
graph.add_node("claim:team-project", type="Claim", 
               text="팀 프로젝트로 Redis 캐시 구현", source="resume")
graph.add_edge("candidate:kim", "claim:team-project", rel="CLAIMED")

# 자동 모순 탐지: blame 95% + "팀 프로젝트" claim
if blame_ratio > 0.9 and claim.text contains "팀":
    graph.add_edge("claim:team-project", "blame:abc-api", 
                   rel="POTENTIALLY_CONTRADICTS",
                   reason="blame 95%인데 팀 프로젝트 주장")
```

### 분석 효율성 증대 포인트

| 단계 | 기존 (분산) | 개선 (그래프 중심) |
|------|-----------|-----------------|
| **SkillExtractor** | 코드만 보고 스킬 추출 | 그래프에서 이력서+LinkedIn+코드 교차 확인 → 더 정확한 스킬 레벨 판정 |
| **ProfileSynthesizer** | 5개 Worker JSON 전부 로드 → 수동 합침 | 그래프 순회 한 번 → O(N) |
| **QualityGate** | 질문 하나씩 검증 | 그래프에서 "미검증 스킬" 즉시 쿼리 → 빠진 토픽 탐지 |
| **QuestionCrafter** | 컨텍스트를 수동 조립 | 그래프에서 모순/약점 엣지 직접 추출 → 질문 품질 향상 |
| **모순 탐지** | 불가능 (별도 로직 필요) | 분석 과정에서 **자동으로** CONTRADICTS 엣지 생성 |

### 기술 구현

```
[서버 - v5.0 분석 중]
NetworkX (Python 인메모리)
  └─ 각 Worker가 노드/엣지 추가
  └─ Reference Passing: state["kg_ref"] = DB에 저장된 그래프 ID
  └─ 분석 완료 → JSONB로 PostgreSQL 영속화

[서버 → 클라이언트 동기화]
PostgreSQL JSONB → JSON export → 클라이언트 다운로드

[클라이언트 - Electron 실시간]
graphology (JS 인메모리) ← JSON import
LanceDB (벡터 검색)
  └─ 하이브리드: 벡터(의미) + 그래프(관계) 결합 쿼리
  └─ 면접 중 새 발화 → 그래프에 실시간 노드 추가
```

### LangGraph 통합 (Reference Passing 패턴 유지)

```python
# application/states/meta_state.py
class MetaState(TypedDict):
    job_id: str
    knowledge_graph_ref: Optional[str]  # 🆕 KG 테이블 ID
    # ... 기존 필드들

# application/nodes/base_worker.py  
async def run(self, state: dict) -> dict:
    # 1. Load: DB에서 Knowledge Graph 로드
    kg = await kg_repository.load(state["knowledge_graph_ref"])
    
    # 2. Process: 분석 + 그래프에 결과 주입
    result = await self.execute(input_data, kg)  # kg를 받아서 활용
    
    # 3. Save: 갱신된 그래프를 DB에 저장
    await kg_repository.save(state["knowledge_graph_ref"], kg)
    
    # 4. Return Ref: 동일한 ref 반환 (그래프는 누적)
    return {"knowledge_graph_ref": state["knowledge_graph_ref"]}
```

### 왜 Neo4j/Apache AGE가 아닌 NetworkX + JSONB인가?

| 기준 | NetworkX + JSONB | Neo4j | Apache AGE |
|------|:---:|:---:|:---:|
| **추가 인프라** | 없음 (Python + PostgreSQL) | Docker 서비스 추가 | PostgreSQL 확장 설치 |
| **1인 개발** | 최적 | 과잉 | 중간 |
| **지원자 1명 그래프 크기** | ~수백 노드/엣지 | 수십억 지원 (과잉) | 중간 |
| **Python 통합** | 네이티브 | py2neo 필요 | psycopg2 |
| **LangGraph 호환** | 직접 조작 | API 호출 | SQL 쿼리 |
| **클라이언트 export** | JSON 직접 | Cypher → JSON 변환 | SQL → JSON 변환 |

지원자 1명당 그래프는 **수백 노드** 수준이므로 NetworkX 인메모리로 충분합니다.

---

정리하면: **"분석하면서 그래프 구축 → 분석 품질 향상 → 그래프 완성 → Live에 동기화"** 이 플로우가 가장 효율적입니다. 이 방향으로 아키텍처를 반영할까요?

### [사용자] LLM 그래프 도구 호출 제안 (Line 356)

> 기존 v5.0 을 지금 추가되는 기능들로 최적화 더 할수 잇는방법 찾아봐 툴도 그래프 노드 탐색툴로 호출해서 작업한다면 불필요한 input 토큰 많이 사용할 필요없이 필요한거 알아서 가져가서 쓸수있을것같은데

### [어시스턴트] Agentic Graph RAG 설계 (Line 365-370)

완벽한 통찰입니다. LLM이 **도구로 그래프를 직접 탐색**하면 v5.0 전체 파이프라인이 혁신적으로 최적화됩니다.

## Knowledge Graph 중심 v5.0 최적화 — "Agentic Graph RAG"

### 핵심 변경: 고정 컨텍스트 → 도구 기반 동적 탐색

```
[기존 v5.0 방식 — 수동 컨텍스트 조립]
각 Worker 결과 JSON → 수동으로 8000토큰 맞춰 잘라 붙이기 → LLM에 전달

[개선 방식 — LLM이 그래프 도구로 직접 탐색]
LLM에게 그래프 탐색 도구 세트 제공 → LLM이 필요한 정보만 선택적 조회
```

### 토큰 절감 효과

| 단계 | 기존 (고정 컨텍스트) | 개선 (도구 호출) | 절감 |
|------|---|---|---|
| QuestionCrafter (질문 1개당) | ~8,000 토큰 | ~2,500 토큰 | **-69%** |
| ProfileSynthesizer | ~12,000 토큰 (5개 Worker JSON) | ~4,000 토큰 (그래프 순회) | **-67%** |
| QualityGate | ~6,000 토큰 | ~1,500 토큰 (gap 쿼리) | **-75%** |
| **25개 질문 생성 전체** | **~200,000 input 토큰** | **~62,500 input 토큰** | **-69%** |

### 그래프 탐색 도구 세트 설계

LangGraph의 [ToolNode](https://docs.langchain.com/oss/python/langgraph/agentic-rag)와 통합하여, LLM이 자율적으로 호출할 수 있는 도구:

```python
# infrastructure/kg/graph_tools.py

@tool
def get_candidate_overview(candidate_id: str) -> dict:
    """지원자 전체 요약: 스킬 수, 레포 수, 4대 지표, 신뢰도"""
    # 그래프에서 1홉 탐색으로 즉시 반환 (~50 토큰)

@tool
def get_skill_evidence(candidate_id: str, skill_name: str) -> dict:
    """특정 스킬의 모든 증거: 코드, 이력서, LinkedIn 출처별"""
    # (Skill)-[EVIDENCE]->(Source) 탐색 (~200 토큰)

@tool
def find_contradictions(candidate_id: str) -> list[dict]:
    """이력서/LinkedIn 주장 vs 코드/Git 증거 간 모순점 목록"""
    # (Claim)-[CONTRADICTS]->(Evidence) 엣지 수집 (~150 토큰)

@tool
def get_jd_coverage(candidate_id: str, jd_id: str) -> dict:
    """JD 요구 스킬 중 검증된/미검증/약한 항목 분류"""
    # (JD)-[REQUIRES]->(Skill) where verified/unverified (~200 토큰)

@tool
def get_code_deep_dive(file_path: str) -> dict:
    """특정 파일의 상세: 복잡도, blame 비율, AI 의심도, 패턴"""
    # (File)-[COMPLEXITY|BLAME|AI_SUSPICION] 속성 (~300 토큰)

@tool
def get_unverified_topics(candidate_id: str) -> list[str]:
    """아직 면접에서 검증되지 않은 토픽/역량 목록"""
    # (Skill)-[VERIFIED:false] 필터 (~100 토큰)

@tool
def traverse_context(node_id: str, depth: int = 2) -> dict:
    """특정 노드 주변 N홉 탐색 — 범용 그래프 탐색"""
    # graphology/NetworkX 이웃 탐색 (~100-500 토큰)
```

### v5.0 파이프라인 최적화 — Before vs After

#### 1. QuestionCrafter (질문 생성)

```
[Before — 8000토큰 고정 컨텍스트]
system_prompt + jd_context + code_chunks + candidate_profile + topic_context
→ "이 컨텍스트를 바탕으로 질문을 만들어라"

[After — 도구 기반]
system_prompt + "그래프 도구를 사용하여 질문을 만들어라"
→ LLM이 자율 판단:
  1) get_jd_coverage() → "아, MSA 경험이 미검증이네"
  2) get_skill_evidence("msa") → "이력서에는 MSA 3년이라고 했고..."
  3) find_contradictions() → "모순점: 이력서는 마이크로서비스인데 코드는 모놀리스"
  4) 질문 생성: "MSA 경험 3년이시라고 했는데, 코드에서는 모놀리스 구조가..."
```

#### 2. ProfileSynthesizer (프로필 통합)

```
[Before — 5개 Worker JSON 전체 로드]
forensic_result (3000토큰) + logic_result (3000토큰) + stack_result (3000토큰)
+ resume (2000토큰) + linkedin (1000토큰) = 12,000 입력 토큰

[After — 그래프 순회]
get_candidate_overview() → 50 토큰
get_jd_coverage() → 200 토큰  
find_contradictions() → 150 토큰
→ LLM이 필요 시 추가 도구 호출: get_skill_evidence("redis") → 200 토큰
= ~2,000-4,000 입력 토큰
```

#### 3. QualityGate (질문 품질 검증)

```
[Before — 질문 목록 + 전체 컨텍스트 재로드]
25개 질문 + 8000토큰 컨텍스트 = ~15,000 토큰

[After — 도구 기반 검증]
25개 질문 + get_unverified_topics() → "아직 '트러블슈팅'이 안 다뤄졌네"
= ~5,000 토큰
```

#### 4. Worker 간 중복 제거

```
[Before]
CollectorWorker: "이 레포에서 Redis 사용" → JSON 저장
SkillExtractor: 같은 레포를 다시 분석하여 "Redis 사용" → 중복 JSON 저장

[After]
CollectorWorker: graph.add_edge(repo, "redis", rel="USED_TECH")
SkillExtractor: graph.has_edge(repo, "redis")? → 이미 있음, 스킵!
               → 대신 깊이 분석만 추가: skill.proficiency = "advanced"
```

#### 5. OutputAssembler (최종 리포트)

```
[Before — 여러 테이블에서 JOIN]
SELECT * FROM analysis_results WHERE job_id = ...  (5개 Worker 결과)
+ SELECT * FROM candidate_scores WHERE job_id = ...
→ Python에서 수동 조립

[After — 그래프 순회 한 번]
그래프 전체 직렬화 → 구조가 곧 리포트
→ (Candidate)-[HAS_SKILL]→(Skill)-[EVIDENCE]→(Source) 체인이 
   자동으로 "증거 기반 역량 평가" 구조를 형성
```

### Live 면접에서의 동일 패턴

클라이언트(Electron)에서도 **동일한 도구 세트**를 Groq LLM에 제공:

```
면접관이 "다른 질문 줘" 버튼 클릭
→ Groq LLM 호출 (도구 세트 포함)
→ LLM: get_unverified_topics() → "팀 협업 미검증"
→ LLM: get_skill_evidence("teamwork") → "LinkedIn: 팀 리드 2년"
→ LLM: 질문 생성 + [의도: 팀 협업 역량 검증]

전체: ~140ms(TTFT) + ~500ms(생성) = ~640ms
입력 토큰: ~1,500 (도구 결과만)
```

### 수정된 아키텍처 요약

```
Knowledge Graph = 분석의 중심축 + LLM의 도구 인터페이스

[서버 — v5.0 분석]
Worker → NetworkX 그래프에 노드/엣지 주입 (분석하면서 구축)
LLM (Instructor) → 그래프 도구로 필요한 정보만 조회 (토큰 69% 절감)
완료 → PostgreSQL JSONB 영속화

[클라이언트 — Live 면접]  
graphology 그래프 (인메모리) ← 서버에서 동기화
LanceDB 벡터 (임베디드) ← 서버에서 동기화
Groq LLM → 동일한 그래프 도구 세트로 실시간 질문 생성
```

Sources:
- [LangGraph Agentic RAG](https://docs.langchain.com/oss/python/langgraph/agentic-rag)
- [Agent-as-a-Graph 논문](https://www.arxiv.org/pdf/2511.18194)
- [GraphRAG + Agentic Architecture](https://neo4j.com/blog/developer/graphrag-and-agentic-architecture-with-neoconverse/)

---

이렇게 하면 **v5.0 분석 품질 향상 + 토큰 69% 절감 + Live 면접 동일 인터페이스**를 한 번에 달성합니다. 이 방향으로 전체 설계에 반영할까요?

---
### [컨텍스트 연속] (Line 379)

This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.
Analysis:
Let me chronologically analyze the entire conversation:
1. **User's initial request**: The user invoked the brainstorming skill to redesign the Jittda Sniper v5.0 project. They want to transform it from a web-only interview question generator into a real-time AI interview guide system called "Jittda Live". They provided extensive requirements including:
   - Electron-based desktop app
   - OS native audio capture (mic + system sound)
   - VAD (Voice Activity Detection)
   - Real-time STT with speaker diarization
   - Local-first RAG with LanceDB
   - Real-time AI question generation
   - Topic coverage tracking
   - Dynamic probing cards
   - Automated scorecard
   - Minimal cognitive load for interviewer
2. **My approach**: I followed the brainstorming skill process:
   - Created 6 tasks for tracking
   - Explored project context (read v5.0 design doc extensively)
   - Launched background agents for v5 summary and tech research
   - Asked clarifying questions one at a time
   - Proposed architecture approaches
   - Began presenting design sections
3. **Clarifying questions and answers**:
   - Project relationship: Web features maintained + interview question generation moves to desktop Live + data/results shared between web and app
   - Target OS: macOS first, with interface abstraction for Windows expansion
   - Interview type: Both online (channel separation) + offline (AI speaker diarization)
   - STT: Deepgram Nova-3 with interface abstraction
   - Communication: REST (before/after) + WebSocket (during interview)
   - Question generation: Hybrid (AI auto-recommend + interviewer manual request)
   - Result analysis: Full report (scorecard + timeline + deep analysis + D3.js visualization + v5.0 integration)
   - Pre-analysis: v5.0 analysis required before live interview, results synced to Live
   - Architecture: Integrated Monorepo (since v5.0 isn't built yet)
4. **Critical user feedback on Knowledge Graph**:
   - User pointed out that PostgreSQL alone can't efficiently extract information from candidate data for real-time question generation
   - Suggested using Graph or RAG or GraphRAG
   - I analyzed and proposed hybrid approach: Server-side Knowledge Graph (NetworkX) + Client-side local search (graphology + LanceDB)
5. **User's second insight**: Why not inject data into the graph during v5.0 analysis instead of building it separately?
   - I agreed and designed "Graph-First Analysis Pipeline" where each Worker adds nodes/edges to the KG during analysis
   - This optimizes both analysis quality and Live interview data
6. **User's third insight**: LLM should use graph traversal tools instead of receiving large context dumps
   - I designed a graph tool set for LLM tool calling
   - Estimated 69% token savings
   - Same tool interface works for both v5.0 analysis and Live interview
7. **Final request**: "해당 내용 설계에 반영해" (Reflect this in the design) + compact summary request
Key technology decisions:
- Electron v33+ for desktop
- electron-audio-loopback for audio capture
- Silero VAD + @ricky0123/vad for VAD
- Deepgram Nova-3 for STT
- LanceDB v0.26 for local vector DB
- Groq for real-time LLM (TTFT 0.14s)
- NetworkX (server) + graphology (client) for Knowledge Graph
- PostgreSQL JSONB for graph persistence
- Kimi K2.5 + Instructor + Langfuse for server-side LLM
Files read:
- /Users/sabyun/goinfre/IaaS/plan/2026-02-15-v5-final-design.md (extensively, lines 1-2198+)
- Phase design files listed via Glob
The conversation was interrupted during design section presentation (Section 1: Overall System Architecture was presented), and the user provided three critical design feedback items that need to be reflected in the full design document.
Tasks status:
- #1 completed: Project context exploration
- #2 completed: Latest tech research
- #3 completed: Clarifying questions
- #4 completed: Architecture approach proposals
- #5 in_progress: Design document writing and approval
- #6 pending: Implementation plan transition (writing-plans)
Summary:
1. Primary Request and Intent:
   The user wants to redesign the Jittda Sniper v5.0 project (currently unbuilt) to include a real-time AI interview guide feature called "Jittda Live". The system should:
   - Maintain web functionality for candidate data analysis and results viewing
   - Add an Electron desktop app for real-time live interview assistance
   - Support OS native audio capture (mic + system sound) for both online and offline interviews
   - Provide real-time STT, AI-powered question generation, topic coverage tracking, dynamic probing cards
   - Generate comprehensive post-interview reports with D3.js visualization
   - Use a Knowledge Graph as the central data structure for both analysis and real-time interview
   - LLM should use graph traversal tools instead of large context dumps (69% token savings)
   - Create a new Linear project called "Jittda Live"
   - Design step by step, starting with MVP requirements, using latest technologies researched from the internet
2. Key Technical Concepts:
   - **Integrated Monorepo**: jittda/ with backend/ + frontend/ + desktop/ + shared/ + infra/ (since v5.0 is not yet built)
   - **Electron v33+**: Desktop framework with native audio capture via electron-audio-loopback
   - **Silero VAD + @ricky0123/vad**: WASM-based Voice Activity Detection in Electron renderer

### [어시스턴트] 섹션 2: 데스크탑 앱 상세 아키텍처 (Line 418)

이전 대화에서 확정된 모든 설계 결정사항을 반영한 전체 설계 문서를 작성하겠습니다. 먼저 남은 섹션들을 순차적으로 제시하겠습니다.

---

## 섹션 2: 데스크탑 앱 상세 아키텍처 (Electron)

이전에 확정된 사항을 바탕으로 Electron 프로세스 모델과 오디오 파이프라인입니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    Electron v33+ App                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Renderer Process (React + Vite)           │    │
│  │                                                     │    │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐    │    │
│  │  │ Silero   │  │ grapho-  │  │  Interviewer   │    │    │
│  │  │ VAD      │  │ logy     │  │  Dashboard UI  │    │    │
│  │  │ (WASM)   │  │ (Graph)  │  │  (React)       │    │    │
│  │  └────┬─────┘  └────┬─────┘  └───────┬────────┘    │    │
│  │       │              │                │             │    │
│  │       └──────────────┴────────────────┘             │    │
│  │                    EventBus                         │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │ IPC                                │
│  ┌─────────────────────┴───────────────────────────────┐    │
│  │              Main Process (Node.js)                 │    │
│  │                                                     │    │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────┐    │    │
│  │  │ Audio    │  │ LanceDB  │  │  Deepgram WS   │    │    │
│  │  │ Manager  │  │ v0.26    │  │  Client        │    │    │
│  │  │          │  │ (Vector) │  │  (STT)         │    │    │
│  │  └────┬─────┘  └──────────┘  └────────────────┘    │    │
│  └───────┼─────────────────────────────────────────────┘    │
│          │ stdio pipe                                       │
│  ┌───────┴─────────────────────────────────────────────┐    │
│  │        Child Process (Native Audio Binary)          │    │
│  │  macOS: ScreenCaptureKit / CoreAudio                │    │
│  │  Windows: WASAPI Loopback (추후)                     │    │
│  │  출력: PCM Stereo (L=Mic, R=System)                 │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**핵심 결정사항:**

| 항목 | 선택 | 근거 |
|------|------|------|
| 프레임워크 | Electron v33+ | 네이티브 오디오 접근, 크로스 플랫폼 |
| 오디오 캡처 | electron-audio-loopback | 가상 드라이버 불필요, OS 네이티브 |
| 타겟 OS | macOS 우선 | 인터페이스 추상화로 Windows 확장 가능 |
| VAD | Silero VAD (WASM) | Renderer에서 1ms 이하 무음 감지 |
| 로컬 DB | LanceDB v0.26 (Main) | In-process 벡터 검색 <60ms |
| 그래프 | graphology (Renderer) | In-memory 그래프 탐색 <5ms |
| STT | Deepgram Nova-3 | 한/영 WER 7-16%, 스트리밍 지원 |
| 실시간 LLM | Groq (Llama 3.3 70B) | TTFT 0.14s, 면접 중 질문 생성 |

**온라인 vs 오프라인 면접 처리:**

| 모드 | 화자 분리 방식 | 오디오 소스 |
|------|---------------|------------|
| 온라인 (화상) | Channel Muxing (L=Mic, R=System) | 마이크 + 시스템 사운드 |
| 오프라인 (대면) | Deepgram AI Diarization | 마이크만 (양자 음성 모두 캡처) |

이 섹션에 대해 피드백이 있으신가요? 괜찮으면 다음 섹션으로 넘어가겠습니다.

### [사용자] 디자인 패턴 + 추상화 요청 (Line 425)

> 아키텍쳐 설계할때 디자인패턴 최대한 이용하고 추상화를 최대화로 해서(효율적인) 로직이 바뀌거나 추가되거나 할때 많은 로드가 걸리지 않고록 설계단에서 부터 해당 염두해두고 설계하면 좋을것같아

### [어시스턴트] 디자인 패턴 & 추상화 전략 (Line 428)

좋은 포인트입니다. 변경 내성(Change Tolerance)을 설계 단계부터 확보하는 것이 핵심이죠. 전체 아키텍처에 걸쳐 적용할 디자인 패턴과 추상화 전략을 체계적으로 설계하겠습니다.

---

## 섹션 2-1: 디자인 패턴 & 추상화 전략 (변경 내성 아키텍처)

전체 시스템을 **6개 추상화 레이어**로 나누고, 각 레이어에 핵심 패턴을 배치합니다. 목표는 **어떤 구성요소든 교체/추가 시 영향 반경을 해당 Adapter 1개 파일로 한정**하는 것입니다.

```
┌────────────────────────────────────────────────────────┐
│              Layer 6: UI (Presenter)                   │
│  Observer 패턴 — EventBus 구독만, 직접 의존 없음         │
├────────────────────────────────────────────────────────┤
│              Layer 5: Application (Orchestrator)       │
│  Mediator 패턴 — 파이프라인 조율, 컴포넌트 간 직접 참조 금지│
├────────────────────────────────────────────────────────┤
│              Layer 4: Domain (Business Logic)          │
│  Strategy 패턴 — 면접 모드별/분석 전략별 교체 가능        │
├────────────────────────────────────────────────────────┤
│              Layer 3: Service (Use Cases)              │
│  Template Method — 공통 흐름 고정, 세부 단계만 Override   │
├────────────────────────────────────────────────────────┤
│              Layer 2: Port (Interface Contracts)       │
│  Port/Adapter — 모든 외부 의존을 Interface로 차단        │
├────────────────────────────────────────────────────────┤
│              Layer 1: Adapter (Infrastructure)         │
│  Adapter 패턴 — 실제 구현체, 교체 시 여기만 수정          │
└────────────────────────────────────────────────────────┘
```

### 1. Port/Adapter (Hexagonal Architecture) — 외부 의존 완전 격리

모든 외부 서비스를 **Port(인터페이스)**로 정의하고, 실제 구현은 **Adapter**로 분리합니다. 교체 시 Adapter 파일 1개만 추가하면 됩니다.

```
shared/ports/           ← 인터페이스 정의 (Python: Protocol, TS: interface)
├── stt.py/ts           ← STTProvider Protocol
├── llm.py/ts           ← LLMProvider Protocol  
├── vad.py/ts           ← VADEngine Protocol
├── audio_capture.py/ts ← AudioCapturer Protocol
├── vector_store.py/ts  ← VectorStore Protocol
├── graph_store.py/ts   ← GraphStore Protocol
├── graph_query.py/ts   ← GraphQueryEngine Protocol
└── notification.py/ts  ← NotificationSender Protocol
```

```python
# shared/ports/stt.py — Port 예시
from typing import Protocol, AsyncIterator
from shared.models.audio import AudioChunk, TranscriptSegment

class STTProvider(Protocol):
    """STT 제공자 인터페이스. 구현체 교체 시 이 계약만 충족하면 됨."""
    
    async def connect(self, config: STTConfig) -> None: ...
    async def stream(self, audio: AsyncIterator[AudioChunk]) -> AsyncIterator[TranscriptSegment]: ...
    async def disconnect(self) -> None: ...
    
    @property
    def supports_diarization(self) -> bool: ...
    @property
    def supported_languages(self) -> list[str]: ...
```

```python
# backend/adapters/stt/deepgram.py — Adapter 예시
class DeepgramSTTAdapter:
    """Deepgram Nova-3 구현체. 교체 대상은 이 파일뿐."""
    
    def __init__(self, api_key: str):
        self._client = DeepgramClient(api_key)
    
    async def stream(self, audio: AsyncIterator[AudioChunk]) -> AsyncIterator[TranscriptSegment]:
        # Deepgram 고유 로직
        ...
```

**현재 교체 가능성이 있는 Adapter 목록:**

| Port | 현재 Adapter | 교체 후보 | 영향 범위 |
|------|-------------|----------|----------|
| STTProvider | DeepgramAdapter | WhisperAdapter, AssemblyAIAdapter | 1 파일 |
| LLMProvider (실시간) | GroqAdapter | TogetherAIAdapter, OllamaAdapter | 1 파일 |
| LLMProvider (분석) | KimiK2Adapter | ClaudeAdapter, GPT4Adapter | 1 파일 |
| VADEngine | SileroWASMAdapter | WebRTCVADAdapter | 1 파일 |
| AudioCapturer | ScreenCaptureKitAdapter | WASAPIAdapter (Windows) | 1 파일 |
| VectorStore | LanceDBAdapter | ChromaAdapter, QdrantAdapter | 1 파일 |
| GraphStore | NetworkXAdapter (서버) | Neo4jAdapter | 1 파일 |
| GraphQuery | GraphologyAdapter (클라이언트) | - | 1 파일 |

### 2. Strategy 패턴 — 면접 모드/분석 전략 동적 교체

런타임에 면접 모드나 분석 전략이 바뀌어도 로직 수정 없이 Strategy만 교체합니다.

```python
# shared/ports/interview_strategy.py
class InterviewStrategy(Protocol):
    """면접 모드별 전략. 온라인/오프라인/하이브리드 등 추가 시 이것만 구현."""
    
    def get_audio_sources(self) -> list[AudioSourceConfig]: ...
    def get_diarization_mode(self) -> DiarizationMode: ...
    def create_audio_pipeline(self, capturer: AudioCapturer) -> AudioPipeline: ...

# domain/strategies/online_interview.py
class OnlineInterviewStrategy:
    """온라인 면접: Channel Muxing (L=Mic, R=System)"""
    def get_diarization_mode(self) -> DiarizationMode:
        return DiarizationMode.CHANNEL_BASED

# domain/strategies/offline_interview.py
class OfflineInterviewStrategy:
    """오프라인 면접: AI Speaker Diarization"""
    def get_diarization_mode(self) -> DiarizationMode:
        return DiarizationMode.AI_DIARIZATION
```

```python
# 질문 생성 전략도 동일
class QuestionStrategy(Protocol):
    async def generate(self, context: InterviewContext, graph_tools: GraphToolSet) -> list[ProbingCard]: ...

class FollowUpStrategy:       # 꼬리 질문
class ContradictionStrategy:  # 모순 검증 질문  
class CoverageGapStrategy:    # 미검증 영역 질문
class InterviewerRequestStrategy:  # 면접관 수동 요청
```

### 3. Observer + EventBus — 컴포넌트 간 결합도 제로

모든 실시간 이벤트(오디오, VAD, STT, LLM)를 EventBus를 통해 전달합니다. UI 컴포넌트는 필요한 이벤트만 구독하고, 생산자는 소비자를 모릅니다.

```typescript
// shared/events/event-bus.ts
interface EventMap {
  'audio:chunk':        AudioChunkEvent;
  'vad:speech-start':   SpeechStartEvent;
  'vad:speech-end':     SpeechEndEvent;
  'stt:partial':        PartialTranscriptEvent;
  'stt:final':          FinalTranscriptEvent;
  'rag:context-found':  ContextFoundEvent;
  'llm:probing-cards':  ProbingCardsEvent;
  'coverage:updated':   CoverageUpdateEvent;
  'score:updated':      ScoreUpdateEvent;
  'interview:command':  InterviewerCommandEvent;  // 면접관 수동 요청
}

// 타입 안전한 EventBus — 이벤트 추가 시 EventMap에 타입만 추가
class TypedEventBus {
  on<K extends keyof EventMap>(event: K, handler: (data: EventMap[K]) => void): void;
  emit<K extends keyof EventMap>(event: K, data: EventMap[K]): void;
  off<K extends keyof EventMap>(event: K, handler: Function): void;
}
```

```
새 이벤트 추가 시:
1. EventMap에 타입 1줄 추가
2. 생산자에서 emit() 1줄 추가
3. 소비자에서 on() 1줄 추가
→ 기존 코드 수정 없음
```

### 4. Pipeline (Chain of Responsibility) — 처리 단계 동적 조합

오디오→분석 파이프라인을 체인으로 구성하여, 단계 추가/제거/순서 변경을 설정만으로 처리합니다.

```python
# domain/pipeline/base.py
class PipelineStage(Protocol[TIn, TOut]):
    async def process(self, input: TIn) -> TOut | None:
        """None 반환 시 파이프라인 중단 (예: VAD가 무음 판정)"""
        ...

class Pipeline:
    def __init__(self, stages: list[PipelineStage]):
        self._stages = stages
    
    async def execute(self, input: Any) -> Any:
        result = input
        for stage in self._stages:
            result = await stage.process(result)
            if result is None:
                return None  # 단계에서 중단 결정
        return result
```

```python
# 파이프라인 조립 — 설정 기반, 코드 변경 없이 단계 추가/제거
def build_realtime_pipeline(config: InterviewConfig) -> Pipeline:
    stages = [
        AudioNormalizerStage(),
        VADGateStage(threshold=config.vad_threshold),       # 무음이면 중단
        ChannelSplitterStage() if config.is_online else NoOpStage(),
        STTStreamStage(stt_adapter),
        KeywordExtractorStage(),
        GraphRAGStage(graph_query, vector_store),            # Hybrid RAG
        LLMQuestionGeneratorStage(llm_adapter, graph_tools), # Agentic Graph RAG
    ]
    return Pipeline(stages)
```

### 5. Factory + Registry — 구현체 자동 등록/해석

DI(Dependency Injection) 컨테이너로 Adapter를 자동 등록하여, 설정 파일 1줄로 구현체를 교체합니다.

```python
# shared/di/registry.py
class AdapterRegistry:
    _registry: dict[type, dict[str, type]] = {}
    
    @classmethod
    def register(cls, port: type, name: str):
        """데코레이터로 Adapter 자동 등록"""
        def decorator(adapter_cls):
            cls._registry.setdefault(port, {})[name] = adapter_cls
            return adapter_cls
        return decorator
    
    @classmethod
    def resolve(cls, port: type, name: str, **kwargs):
        return cls._registry[port][name](**kwargs)

# 사용
@AdapterRegistry.register(STTProvider, "deepgram")
class DeepgramSTTAdapter: ...

@AdapterRegistry.register(STTProvider, "whisper")
class WhisperSTTAdapter: ...
```

```yaml
# config/live.yaml — 설정 파일만 바꾸면 구현체 교체
stt:
  provider: "deepgram"    # → "whisper"로 바꾸면 끝
  config:
    model: "nova-3"
    language: ["ko", "en"]

llm:
  realtime_provider: "groq"
  analysis_provider: "kimi-k2"

audio:
  capturer: "screencapturekit"  # macOS
  # capturer: "wasapi"          # Windows
```

### 6. Template Method — Worker 공통 흐름 고정

v5.0 BaseWorker 패턴을 확장하여 KG 통합 흐름을 고정합니다. 각 Worker는 `execute()`만 구현하면 됩니다.

```python
# domain/workers/base.py
class BaseWorker(ABC):
    """Load → Execute → Save → Ref 흐름 고정. 서브클래스는 execute()만 구현."""
    
    async def run(self, state: WorkflowState) -> WorkflowState:
        # 고정 흐름 — 수정 불필요
        kg = await self.kg_repo.load(state.knowledge_graph_ref)
        input_data = await self.load_input(state)
        
        result = await self.execute(input_data, kg)  # ← 여기만 구현
        
        await self.kg_repo.save(state.knowledge_graph_ref, kg)
        return state.with_update(self.output_key, result.ref_id)
    
    @abstractmethod
    async def execute(self, input: Any, kg: KnowledgeGraph) -> WorkerResult:
        """각 Worker의 고유 로직. KG에 노드/엣지 주입 포함."""
        ...
```

### 7. Command 패턴 — 면접관 액션 확장성

면접관의 모든 조작을 Command 객체로 캡슐화하여, 새 액션 추가 시 Command 1개만 구현합니다.

```typescript
// domain/commands/types.ts
interface InterviewCommand {
  readonly type: string;
  execute(context: InterviewContext): Promise<CommandResult>;
}

// domain/commands/
class RequestFollowUpCommand implements InterviewCommand { ... }
class RequestTopicChangeCommand implements InterviewCommand { ... }
class MarkTopicVerifiedCommand implements InterviewCommand { ... }
class RequestDeepDiveCommand implements InterviewCommand { ... }
class EndInterviewCommand implements InterviewCommand { ... }
// 새 액션 추가 → Command 파일 1개 추가, 기존 코드 수정 없음
```

---

### 패턴 적용 종합 맵

```
┌──────────────────────────────────────────────────────────────┐
│                    변경 시나리오별 영향 범위                     │
├──────────────────────────┬────────────────┬──────────────────┤
│ 변경 사항                 │ 수정 파일 수    │ 적용 패턴         │
├──────────────────────────┼────────────────┼──────────────────┤
│ STT 엔진 교체             │ 1 (Ad

### [사용자] SOLID 원칙 추가 요청 (Line 435)

> solid 원칙도 추가해서 해당방향으로 진행하자

### [어시스턴트] SOLID + 디자인패턴 매핑 (Line 438)

SOLID 원칙을 디자인 패턴과 매핑하여 아키텍처 전체에 적용합니다.

### SOLID × 패턴 매핑 (설계에 추가)

| 원칙 | 적용 | 구체적 규칙 |
|------|------|------------|
| **S** — Single Responsibility | Adapter 1개 = 외부 서비스 1개, Worker 1개 = 분석 도메인 1개 | `DeepgramAdapter`가 VAD까지 담당 금지 |
| **O** — Open/Closed | Port 인터페이스 수정 금지, 새 Adapter/Strategy 파일 추가만 | `STTProvider` Protocol 확정 후 시그니처 변경 금지 |
| **L** — Liskov Substitution | 모든 Adapter는 Port 계약을 100% 충족 | `WhisperAdapter`가 `stream()` 미구현이면 배포 불가 — 추상 메서드 강제 |
| **I** — Interface Segregation | 큰 인터페이스 금지, 역할별 분리 | `LLMProvider`를 `Streamable`, `ToolCallable`, `Embeddable`로 분리 |
| **D** — Dependency Inversion | 모든 상위 레이어는 Port에만 의존 | `Pipeline`이 `DeepgramAdapter` 직접 import 금지 → `STTProvider`만 참조 |

**ISP 적용 예시 — LLM 인터페이스 분리:**

```python
# 하나의 거대 인터페이스 대신 역할별 분리
class Completable(Protocol):
    """단순 텍스트 생성"""
    async def complete(self, prompt: str) -> str: ...

class Streamable(Protocol):
    """스트리밍 생성 (실시간 UI용)"""
    async def stream(self, prompt: str) -> AsyncIterator[str]: ...

class ToolCallable(Protocol):
    """도구 호출 지원 (Agentic Graph RAG용)"""
    async def call_with_tools(self, prompt: str, tools: list[Tool]) -> ToolCallResult: ...

class Embeddable(Protocol):
    """임베딩 생성 (벡터 검색용)"""
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

# Groq: Completable + Streamable + ToolCallable (임베딩 미지원)
# Kimi K2.5: Completable + ToolCallable + Embeddable (스트리밍 불필요)
# 각 Adapter는 필요한 Protocol만 구현
```

**LSP 보장 — 런타임 검증:**

```python
# shared/di/registry.py 에서 등록 시 자동 검증
@classmethod
def register(cls, port: type, name: str):
    def decorator(adapter_cls):
        # LSP 위반 시 앱 시작 단계에서 즉시 실패
        assert runtime_checkable(port)
        if not issubclass(adapter_cls, port):
            raise LSPViolationError(
                f"{adapter_cls.__name__}이 {port.__name__} 계약을 충족하지 않음"
            )
        cls._registry.setdefault(port, {})[name] = adapter_cls
        return adapter_cls
    return decorator
```

---

확정된 방향입니다. 다음 섹션으로 넘어가겠습니다.

## 섹션 3: 실시간 면접 데이터 플로우

면접 시작부터 질문 생성까지의 전체 데이터 흐름입니다. Pipeline 패턴으로 각 단계가 독립적으로 교체 가능합니다.

```
[면접 시작]
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 1: Audio Capture (Child Process)                          │
│ AudioCapturer Port → ScreenCaptureKitAdapter                    │
│ 출력: PCM Stereo Stream (48kHz, 16bit)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ IPC (stdio pipe)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 2: Audio Normalization (Main Process)                     │
│ 리샘플링(16kHz) + 노이즈 게이트 + 볼륨 정규화                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ IPC → Renderer
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ Stage 3: VAD Gate (Renderer — WASM)                             │
│ VADEngine Port → SileroWASMAdapter                              │
│ 무음 1.5s 이상 → speech-end 이벤트 emit                          │
│ 발화 중 → 오디오 버퍼에 계속 축적                                  │
│ ⚡ 판정 지연: <1ms                                               │
└──────────┬─────────────────────────────┬────────────────────────┘
           │ speech-end                  │ speech (ongoing)
           ▼                             │ (버퍼링만, STT 미전송)
┌──────────────────────────────┐         │
│ Stage 4: STT Stream          │         │
│ STTProvider Port              │         │
│ → DeepgramAdapter            │         │
│                              │         │
│ 온라인: Channel별 분리 전송    │         │
│   L(Mic) → 면접관 발화        │         │
│   R(Sys) → 지원자 발화        │         │
│                              │         │
│ 오프라인: 모노 + AI Diarize   │         │
│   Speaker 0 → 면접관          │         │
│   Speaker 1 → 지원자          │         │
│                              │         │
│ 출력: TranscriptSegment      │         │
│  { speaker, text, timestamp, │         │
│    confidence, is_final }    │         │
└──────────┬───────────────────┘         │
           │ stt:final (지원자 발화 완료)  │
           ▼                             │
┌──────────────────────────────────────────────────────────────┐
│ Stage 5: Hybrid RAG Query (<100ms)                           │
│                                                              │
│  ┌─────────────────────┐    ┌─────────────────────┐          │
│  │ 5a. Semantic Search  │    │ 5b. Graph Traversal │          │
│  │ VectorStore Port     │    │ GraphQuery Port     │          │
│  │ → LanceDBAdapter     │    │ → GraphologyAdapter │          │
│  │                      │    │                     │          │
│  │ 지원자 발화 임베딩 →  │    │ 발화 키워드 →        │          │
│  │ 유사 이력서/JD 청크   │    │ 관련 노드 2-hop 탐색 │          │
│  │ ⚡ <60ms             │    │ ⚡ <5ms              │          │
│  └──────────┬──────────┘    └──────────┬──────────┘          │
│             └──────────┬───────────────┘                     │
│                        ▼                                     │
│              Context Merger                                  │
│              벡터 유사도 + 그래프 관계 교차 랭킹                 │
│              중복 제거, 상위 5개 컨텍스트 선택                   │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 6: Agentic Graph RAG — LLM Question Generation         │
│ ToolCallable Port → GroqAdapter (TTFT ~0.14s)                │
│                                                              │
│ LLM이 직접 Graph Tool 호출하여 필요한 정보만 탐색:              │
│                                                              │
│  시스템 프롬프트                                               │
│  + Stage 5 컨텍스트 (압축)                                    │
│  + 대화 히스토리 (최근 3턴)                                    │
│  + 사용 가능 도구:                                             │
│    ├── get_skill_evidence(skill)                              │
│    ├── find_contradictions()                                  │
│    ├── get_jd_coverage(jd_id)                                │
│    ├── get_unverified_topics()                                │
│    └── traverse_context(node, depth)                          │
│                                                              │
│ 출력: ProbingCard[]                                           │
│  { question, intent, evidence_summary, priority }            │
└──────────────────────────┬───────────────────────────────────┘
                           │ EventBus emit
                           ▼
┌──────────────────────────────────────────────────────────────┐
│ Stage 7: UI Update (Renderer — React)                        │
│ Observer 패턴으로 각 컴포넌트가 필요 이벤트만 구독              │
│                                                              │
│  📊 TopicCoverageBar  ← coverage:updated 구독                │
│  💡 ProbingCards      ← llm:probing-cards 구독               │
│  📝 TranscriptView   ← stt:final 구독                       │
│  📈 ScoreTracker     ← score:updated 구독                    │
└──────────────────────────────────────────────────────────────┘
```

### 전체 지연 시간 목표 (End-to-End)

| 구간 | 목표 지연 | 병목 대응 |
|------|----------|----------|
| Audio → VAD 판정 | <1ms | WASM, Renderer 내 처리 |
| VAD → STT 전송 | <50ms | WebSocket 스트리밍 |
| STT 처리 | <300ms | Deepgram 서버 처리 |
| Hybrid RAG 쿼리 | <100ms | 로컬 LanceDB + graphology |
| LLM 질문 생성 (TTFT) | <200ms | Groq 추론 |
| **합계** | **<700ms** | 지원자 발화 종료 → 질문 카드 표시 |

### 면접관 수동 요청 흐름 (Command 패턴)

```
면접관 버튼 클릭 ("다른 질문 요청" / "이 주제 더 깊게")
    │
    ▼ InterviewerCommandEvent
┌──────────────────────────────────────┐
│ CommandDispatcher (Mediator)         │
│ Command 타입별 적절한 Strategy 선택   │
│                                     │
│ "follow-up" → FollowUpStrategy      │
│ "topic-change" → CoverageGapStrategy│
│ "deep-dive" → DeepDiveStrategy      │
└──────────┬────

### [사용자] 면접관 화면 구성 요청 (Line 445)

> 면접관이 보는 화면구성은 어떻게 돼? 보여지는 방법과 어떤식으로 어떤정보가 보여지는지도 확인해보자

### [어시스턴트] 면접관 대시보드 UI 설계 (Line 448)

좋은 질문입니다. 면접관의 인지 부하를 최소화하면서 필요한 정보만 정확히 전달하는 UI를 설계하겠습니다.

## 섹션: 면접관 대시보드 UI/UX 설계

### 1. 윈도우 구성 전략

면접관은 화상회의(Zoom/Meet) 또는 대면 면접을 하면서 이 앱을 **옆에 띄워놓는** 상황입니다.

```
┌──────────────────────────────────┬──────────────────┐
│                                  │                  │
│                                  │   Jittda Live    │
│     화상회의 / 메모 등            │   Dashboard      │
│     (면접관 기존 작업 영역)        │                  │
│                                  │   420px 폭       │
│                                  │   항상 위 (옵션)  │
│                                  │                  │
└──────────────────────────────────┴──────────────────┘
```

| 항목 | 설정 |
|------|------|
| 기본 크기 | **420×900px** (좁고 긴 사이드바형) |
| 최소 크기 | 380×700px |
| 위치 | 화면 우측 고정 (드래그 이동 가능) |
| Always on Top | 토글 가능 (기본 ON) |
| 테마 | 다크/라이트 (기본 다크 — 시선 부담 감소) |
| 폰트 | 본문 14px, 질문 카드 15px (빠른 스캔 가능) |

---

### 2. 면접 3단계별 화면 전환

면접 진행 단계에 따라 화면이 자동 전환됩니다.

```
[대기] ──시작──▶ [라이브] ──종료──▶ [리포트]
 준비 화면          실시간 면접         결과 분석
```

---

### 3. 대기 화면 (Pre-Interview)

면접 시작 전, 지원자 요약 정보를 빠르게 훑는 화면입니다.

```
┌──────────────────────────────────────┐
│  ◀ 지원자 목록            ⚙ 설정    │
├──────────────────────────────────────┤
│                                      │
│  👤 김민수                           │
│  Backend Engineer · 경력 4년          │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 📋 v5.0 분석 요약                 │ │
│ │                                  │ │
│ │ 강점                             │ │
│ │  ● Spring Boot 실무 경험 풍부     │ │
│ │  ● 테스트 커버리지 82% (상위)     │ │
│ │                                  │ │
│ │ 주의 포인트                       │ │
│ │  ⚠ 이력서 "MSA 설계" ↔ Git에     │ │
│ │    모놀리식 코드만 존재            │ │
│ │  ⚠ AI 코드 비율 34% (높음)       │ │
│ │                                  │ │
│ │ JD 매칭                          │ │
│ │  ■■■■■■■□□□  68%               │ │
│ │  미검증: K8s, 대용량 트래픽       │ │
│ └──────────────────────────────────┘ │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ 면접 모드 선택                    │ │
│ │                                  │ │
│ │  (●) 온라인 (화상 면접)           │ │
│ │  ( ) 오프라인 (대면 면접)         │ │
│ └──────────────────────────────────┘ │
│                                      │
│  ┌──────────────────────────────┐    │
│  │      ▶  면접 시작             │    │
│  └──────────────────────────────┘    │
│                                      │
└──────────────────────────────────────┘
```

**핵심:** v5.0 사전 분석 결과에서 **면접관이 꼭 알아야 할 것만** 3가지로 압축 — 강점, 주의 포인트, JD 매칭률

---

### 4. 라이브 면접 화면 (핵심)

면접 중 면접관이 실제로 보는 화면입니다. **3개 존**으로 나뉩니다.

```
┌──────────────────────────────────────┐
│ Zone A: 상태 바 (고정, 40px)          │
├──────────────────────────────────────┤
│                                      │
│                                      │
│ Zone B: 메인 — 질문 카드 영역         │
│ (스크롤 가능, 전체의 ~65%)            │
│                                      │
│                                      │
├──────────────────────────────────────┤
│ Zone C: 하단 — 커버리지 + 컨트롤      │
│ (고정, ~25%)                         │
└──────────────────────────────────────┘
```

#### Zone A: 상태 바 (항상 고정)

면접 진행 시간, 현재 감지된 대화 주제, 마이크 상태를 한 줄로 보여줍니다.

```
┌──────────────────────────────────────┐
│ ⏱ 24:15  │ 🎙 수신중  │ ■■ 종료가능  │
└──────────────────────────────────────┘
```

| 요소 | 설명 |
|------|------|
| ⏱ 24:15 | 경과 시간 |
| 🎙 수신중 | 오디오 캡처 상태 (수신중/무음/오류) |
| ■■ 종료가능 | 데이터 충분도 — 아래 커버리지 기반 (회색→주황→초록) |

**종료 가능 표시 로직:**
- 커버리지 <50% → `□□ 계속 필요` (회색)
- 커버리지 50-80% → `■□ 종료가능` (주황)
- 커버리지 >80% → `■■ 충분` (초록, 면접 종료 권장 알림 1회)

---

#### Zone B: 메인 질문 카드 영역

면접관이 가장 많이 보는 영역입니다. AI가 생성한 검증 질문이 카드 형태로 쌓입니다.

```
┌──────────────────────────────────────┐
│                                      │
│  🔴 모순 발견                    NOW  │
│ ┌──────────────────────────────────┐ │
│ │                                  │ │
│ │ 이력서: "팀 프로젝트로 캐싱 구축" │ │
│ │ 발화: "혼자서 다 구축했다"        │ │
│ │                                  │ │
│ │ 추천 질문:                       │ │
│ │ "캐시 무효화 전략은 어떻게        │ │
│ │  가져가셨나요?"                   │ │
│ │                                  │ │
│ │  [사용함 ✓]  [다른 질문 ↻]       │ │
│ └──────────────────────────────────┘ │
│                                      │
│  🟡 심화 검증                   1분전 │
│ ┌──────────────────────────────────┐ │
│ │                                  │ │
│ │ Redis 경험 언급 — 깊이 확인 필요  │ │
│ │                                  │ │
│ │ 추천 질문:                       │ │
│ │ "Redis Cluster 환경에서 핫키      │ │
│ │  문제를 겪은 적 있으신가요?"      │ │
│ │                                  │ │
│ │  [사용함 ✓]  [다른 질문 ↻]       │ │
│ └──────────────────────────────────┘ │
│                                      │
│  🟢 역량 확인                   3분전 │
│ ┌──────────────────────────────────┐ │
│ │                                  │ │
│ │ JD 요구: "트러블슈팅 경험"       │ │
│ │ 아직 미검증 상태                  │ │
│ │                                  │ │
│ │ 추천 질문:                       │ │
│ │ "서비스 장애 대응 경험 중 가장    │ │
│ │  기억에 남는 사례가 있으신가요?"  │ │
│ │                                  │ │
│ │  [사용함 ✓]  [다른 질문 ↻]       │ │
│ └──────────────────────────────────┘ │
│                                      │
└──────────────────────────────────────┘
```

**카드 우선순위 색상 체계:**

| 색상 | 의미 | 발생 조건 |
|------|------|----------|
| 🔴 빨강 | 모순 발견 | 이력서/LinkedIn 주장 ↔ 발화/코드 불일치 |
| 🟡 노랑 | 심화 검증 | 기술 언급은 했으나 깊이 부족 |
| 🟢 초록 | 역량 확인 | JD 미검증 항목 커버 유도 |
| 🔵 파랑 | 면접관 요청 | 면접관이 직접 요청한 질문 |

**카드 구성 요소 (최소 정보만):**

```
┌──────────────────────────────────┐
│ [색상 태그] [의도 한줄]     [시간] │ ← 왜 이 질문이 나왔는지
│                                  │
│ 근거 1줄                         │ ← 어떤 증거 기반인지
│                                  │
│ 추천 질문 (1개, 최대 2줄)         │ ← 면접관이 바로 읽을 수 있게
│                                  │
│ [사용함 ✓]  [다른 질문 ↻]        │ ← 2개 버튼만
└──────────────────────────────────┘
```

**카드 인터랙션:**

| 버튼 | 동작 |
|------|------|
| `사용함 ✓` | 해당 질문을 물어봤다고 기록 → 커버리지 반영 → 카드 반투명 처리 |
| `다른 질문 ↻` | 같은 의도의 다른 표현/각도 질문 재생성 (Command 패턴) |
| 카드 스와이프 좌 | 무시/숨기기 |

**자동 행동:**
- 새 카드 생성 시 **상단에 삽입** + 부드러운 슬라이드 애니메이션
- 🔴 카드는 **진동/펄스 효과**로 시선 유도 (선택적)
- 3분 이상 된 카드는 **자동 반투명** (맥락 지남)

---

#### Zone C: 하단 — 커버리지 트래커 + 컨트롤

```
┌──────────────────────────────────────┐
│  📊 역량 검증 진행도                  │
│                                      │
│  기술                                │
│  ■■■■■■■■□□  78%                   │
│  MSA ✓  Redis ✓  K8s ✗  CI/CD ✗    │
│                                      │
│  소프트                              │
│  ■■■■□□□□□□  40%                   │
│  커뮤니케이션 ✗  리더십 ✗  문제해결 ✓ │
│                                      │
├──────────────────────────────────────┤
│                                      │
│  [💬 질문 요청]      [⏹ 면접 종료]   │
│                                      │
└──────────────────────────────────────┘
```

**커버리지 바 동작:**
- ✓ = AI가 충분한 발화 증거를 확보했다고 판단
- ✗ = 아직 미검증
- 항목을 **탭하면** 해당 역량 관련 질문 카드를 즉시 생성 (Command 패턴)

**`💬 질문 요청` 버튼:**

```
┌──────────────────────────────────────┐
│  어떤 질문이 필요하신가요?            │
│                                      │
│  [꼬리 질문]  [주제 전환]  [심화]     │
│                                      │
│  또는 직접 입력:                      │
│  ┌──────────────────────────────┐    │
│  │ "보안 관련해서 물어봐줘"       │    │
│  └──────────────────────────────┘    │
│              [생성 ▶]                │
└──────────────────────────────────────┘
```

3개 프리셋 + 자유 입력으로 **최소 탭**으로 질문 요청 가능합니다.

---

### 5. 면접 종료 화면 (Post-Interview)

면접 종료 후 AI가 종합 분석하여 스코어카드를 보여줍니다.

```
┌──────────────────────────────────────┐
│  📋 면접 결과 — 김민수                │
│  Backend Engineer · 2026.02.17       │
│  면접 시간: 42분 · 질문 18개 사용     │
├──────────────────────────────────────┤
│                                      │
│  종합 점수                           │
│  ┌──────────────────────────────┐    │
│  │        ★ 3.8 / 5.0          │    │
│  │       권장: 2차 면접 진행     │    │
│  └──────────────────────────────┘    │
│                                      │
│  역량별 평가                         │
│  ┌──────────────────────────────┐    │
│  │ 기술 역량      ■■■■□  4.0   │    │
│  │  근거: Redis 캐싱 설계를      │    │
│  │  구체적으로 설명, 단 K8s 경험 │    │
│  │  은 간접적 수준               │    │
│  │                              │    │
│  │ 문제 해결      ■■■■□  3.5   │    │
│  │  근거: 장애 대응 사례 구체적, │    │
│  │  근본 원인 분석 접근법 보유    │    │
│  │                              │    │
│  │ 커뮤니케이션   ■■■□□  3.0   │    │
│  │  근거: 답변이 장황한 경향,    │    │
│  │  핵심 전달력 보통             │    │
│  │                              │    │
│  │ 문화 적합성    ■■■■■  4.5   │    │
│  │  근거: 팀 협업 사례 풍부,     │    │
│  │  성장 의지 높음               │    │
│  └──────────────────────────────┘    │
│                                      │
│  ⚠ 주의 사항                        │
│  ┌──────────────────────────────┐    │
│  │ • 이력서 "팀 프로젝트" 기재   │    │
│  │   ↔ 면접 중 "혼자 구축" 발언  │    │
│  │   → 추가 확인 권장            │    │
│  │                              │    │
│  │ • AI 코드 비율 34% —         │    │
│  │   면접 중 코드 이해도 확인됨   │    │
│  └──────────────────────────────┘    │
│                                      │
│  [✏ 수정하기]    [✅ 승인 및 저장]   │
│  [🌐 웹에서 상세 보기]               │
│                                      │
└──────────────────────────────────────┘
```

**`웹에서 상세 보기`** → 브라우저에서 D3.js 시각화 포함 전체 리포트 확인 (v5.0 분석 + Live 면접 결과 통합)

---

### 6. 정보 표시 원칙 (인지 부하 최소화)

| 원칙 | 적용 |
|------|------|
| **3초 룰** | 모든 카드는 3초 이내에 핵심 파악 가능 |
| **1질문 1카드** | 카드당 추천 질문 1개만 (선택 부담 제거) |
| **근거 1줄** | 왜 이 질문인지 1줄로 압축 |
| **색상 우선순위** | 🔴→🟡→🟢→🔵 순서로 시각적 중요도 구분 |
| **자동 정리** | 오래된 카드 자동 페이드, 사용한 카드 반투명 |
| **소음 제거** | 확신도 낮은 분석은 표시 안 함 (threshold 이상만) |
| **능동 요청** | 면접관이 원할 때만 추가 정보 요청 (정보 폭탄 방지) |

---

이 면접관 대시보드 UI 구성에 대해 어떻게 생각하시나요? 수정하거나 추가하고 싶은 부분이 있으시면 말씀해주세요. 괜찮으면 다음 섹션(Knowledge Graph 스키마 & Graph-First 분석 파이프라인)으로 넘어가겠습니다.

### [어시스턴트] KG 스키마 & Graph-First 파이프라인 (Line 458)

좋습니다. 핵심 섹션입니다.

## 섹션 4: Knowledge Graph 스키마 & Graph-First 분석 파이프라인

### 1. Knowledge Graph 스키마

지원자의 모든 데이터를 **노드(Entity)**와 **엣지(Relationship)**로 표현합니다. LLM이 그래프 도구로 탐색하는 대상입니다.

```
                        ┌───────────┐
                        │ Candidate │
                        └─────┬─────┘
            ┌─────────────┬───┴───┬──────────────┐
            ▼             ▼       ▼              ▼
      ┌──────────┐  ┌─────────┐ ┌──────┐  ┌──────────┐
      │ Skill    │  │ Company │ │ Repo │  │  Claim   │
      └────┬─────┘  └────┬────┘ └──┬───┘  └────┬─────┘
           │              │         │            │
           ▼              ▼         ▼            ▼
      ┌──────────┐  ┌─────────┐ ┌──────┐  ┌──────────┐
      │ Evidence │  │ Position│ │ Tech │  │  Source  │
      └──────────┘  └─────────┘ └──────┘  └──────────┘
                                                │
                                    ┌───────────┼───────────┐
                                    ▼           ▼           ▼
                              ┌────────┐ ┌──────────┐ ┌─────────┐
                              │ Resume │ │ LinkedIn │ │ GitHub  │
                              └────────┘ └──────────┘ └─────────┘
```

#### 노드 타입

| 노드 | 속성 | 생성 시점 |
|------|------|----------|
| **Candidate** | name, email, identity_hash | Identity Resolution Worker |
| **Skill** | name, canonical_name, category(기술/소프트) | Resume + LinkedIn + Code 분석 시 |
| **Company** | name, industry, size | Resume/LinkedIn 파싱 시 |
| **Position** | title, period, description | Resume/LinkedIn 파싱 시 |
| **Repo** | name, url, language, stars, commits | GitHub 수집 시 |
| **Tech** | name, version, category | AST + dependency 분석 시 |
| **Claim** | content, confidence | 이력서/LinkedIn/CoverLetter에서 추출 |
| **Evidence** | type, content, file_path, line_range, metric | 코드/Git/정적분석에서 추출 |
| **JD** | title, requirements, company | 입력 시 |
| **JDRequirement** | skill_name, priority(high/mid/low), description | JD 파싱 시 |
| **InterviewSegment** | speaker, text, timestamp | Live 면접 STT 시 (Live 전용) |

#### 엣지 타입

| 엣지 | From → To | 속성 | 의미 |
|------|-----------|------|------|
| **HAS_SKILL** | Candidate → Skill | proficiency, years | 보유 스킬 |
| **EVIDENCED_BY** | Skill → Evidence | strength(strong/weak/indirect) | 스킬 증거 연결 |
| **WORKED_AT** | Candidate → Company | — | 근무 이력 |
| **HELD_ROLE** | Company → Position | period | 직무 수행 |
| **CONTRIBUTED_TO** | Candidate → Repo | commits, role(owner/contributor) | 기여 레포 |
| **USES_TECH** | Repo → Tech | usage_count, files | 레포 내 기술 사용 |
| **CLAIMED** | Candidate → Claim | — | 주장/기재 사항 |
| **SOURCED_FROM** | Claim → Source | page, section | 출처 |
| **SUPPORTS** | Evidence → Claim | confidence | 증거가 주장을 뒷받침 |
| **CONTRADICTS** | Evidence → Claim | severity, detail | 증거가 주장과 모순 |
| **REQUIRES** | JD → JDRequirement | — | JD 요구사항 |
| **MATCHES** | Skill → JDRequirement | match_score | 스킬-JD 매칭 |
| **VERIFIED_BY** | JDRequirement → InterviewSegment | — | 면접 중 검증됨 (Live) |

---

### 2. Graph-First 분석 파이프라인

v5.0 분석 시 **각 Worker가 분석과 동시에 그래프에 노드/엣지를 주입**합니다. 분석 후 별도로 그래프를 구축하는 것이 아니라, 분석 자체가 그래프를 만드는 행위입니다.

```
┌─────────────────────────────────────────────────────────────┐
│                   MetaAgent (LangGraph HMAS)                │
│                                                             │
│  State: { knowledge_graph_ref: "kg_abc123", ... }           │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Forensic Supervisor                      │  │
│  │                                                       │  │
│  │  IdentityWorker ──▶ Candidate, Company, Position 노드 │  │
│  │  GitBlameWorker ──▶ Repo, Evidence(커밋 패턴) 엣지     │  │
│  │  ASTWorker ──────▶ Tech, Evidence(코드 구조) 노드/엣지 │  │
│  │  ComplexityWorker ▶ Evidence(복잡도 메트릭) 노드        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Logic Supervisor                         │  │
│  │                                                       │  │
│  │  ResumeWorker ───▶ Claim, Skill 노드 + SOURCED_FROM   │  │
│  │  LinkedInWorker ─▶ Claim, Skill 노드 + 교차 검증 엣지  │  │
│  │  CoverLetterWorker▶ Claim 노드 + 동기/포부 추출        │  │
│  │  CrossRefWorker ─▶ SUPPORTS / CONTRADICTS 엣지 생성    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Stack Supervisor                         │  │
│  │                                                       │  │
│  │  PlagiarismWorker ▶ Evidence(표절 의심) 노드           │  │
│  │  AIDetectWorker ──▶ Evidence(AI 코드 비율) 노드        │  │
│  │  JDMatchWorker ───▶ JDRequirement + MATCHES 엣지      │  │
│  │  ScoringWorker ───▶ 최종 점수 산출 (그래프 집계)        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  결과: 완성된 Knowledge Graph (노드 50-200개, 엣지 100-500개) │
└─────────────────────────────────────────────────────────────┘
```

#### Worker의 KG 주입 패턴 (Template Method)

```python
# 예시: ResumeWorker
class ResumeWorker(BaseWorker):
    async def execute(self, input: ResumeData, kg: KnowledgeGraph) -> WorkerResult:
        # 1. 이력서 파싱
        parsed = await self.llm.extract(input.text, ResumeSchema)
        
        # 2. 그래프에 노드 주입
        for skill in parsed.skills:
            skill_node = kg.add_node("Skill", name=skill.name, 
                                     canonical_name=skill.canonical)
            kg.add_edge(input.candidate_ref, skill_node, "HAS_SKILL",
                       proficiency=skill.level, years=skill.years)
            
            # 주장(Claim) 노드 생성
            claim = kg.add_node("Claim", content=f"{skill.name} {skill.level}급")
            kg.add_edge(input.candidate_ref, claim, "CLAIMED")
            kg.add_edge(claim, "resume", "SOURCED_FROM", section=skill.source_section)
        
        for exp in parsed.experiences:
            company = kg.add_node("Company", name=exp.company)
            position = kg.add_node("Position", title=exp.title)
            kg.add_edge(input.candidate_ref, company, "WORKED_AT")
            kg.add_edge(company, position, "HELD_ROLE", period=exp.period)
        
        # 3. 결과 반환 (Reference만)
        return WorkerResult(ref_id=parsed.db_ref)
```

```python
# 예시: CrossRefWorker — 교차 검증으로 SUPPORTS/CONTRADICTS 생성
class CrossRefWorker(BaseWorker):
    async def execute(self, input: CrossRefInput, kg: KnowledgeGraph) -> WorkerResult:
        claims = kg.get_nodes_by_type("Claim")
        evidences = kg.get_nodes_by_type("Evidence")
        
        for claim in claims:
            related = kg.find_related_evidence(claim, max_hops=2)
            for evidence in related:
                # LLM이 그래프 도구로 판단
                verdict = await self.llm.call_with_tools(
                    prompt=f"이 증거가 주장을 뒷받침하는가 모순되는가?",
                    tools=[self.graph_tools.get_skill_evidence,
                           self.graph_tools.traverse_context]
                )
                if verdict.supports:
                    kg.add_edge(evidence, claim, "SUPPORTS", 
                               confidence=verdict.confidence)
                elif verdict.contradicts:
                    kg.add_edge(evidence, claim, "CONTRADICTS",
                               severity=verdict.severity, detail=verdict.reason)
        
        return WorkerResult(ref_id="crossref_complete")
```

---

### 3. 그래프 저장 & 클라이언트 동기화

```
┌──────────────────────┐     동기화      ┌──────────────────────┐
│   Server (Python)    │ ──────────────▶ │  Client (Electron)   │
│                      │                 │                      │
│  NetworkX            │  REST API       │  graphology          │
│  (In-memory 분석)    │  JSON export    

### [사용자] 사전 질문 Deck 제안 (Line 465)

> 면접 라이브때 실시간으로 만드는것보다 미리 주제별로 몇개 질문한거 질문 만들어놓고 그 기반 및 실시간으로 질문 생성하는게 좋지않을가?

### [어시스턴트] 2계층 질문 시스템 (Line 468)

맞습니다. 훨씬 합리적인 접근입니다. 사전 질문 덱(Deck)이 베이스라인이 되고, 실시간 생성은 그 위에 보조하는 **2계층 질문 시스템**으로 설계하겠습니다.

## 질문 생성 전략 수정: 2계층 시스템

### 왜 이게 더 좋은가

| | 실시간 단독 | 사전 Deck + 실시간 보조 |
|---|---|---|
| 면접 시작 즉시 | 질문 없음 (발화 대기) | 주제별 질문 이미 준비됨 |
| 네트워크 장애 시 | 질문 생성 불가 | Deck으로 면접 진행 가능 |
| 질문 품질 | 실시간 압박 → 깊이 제한 | 사전 분석 기반 → 깊이 있음 |
| 지연 시간 | ~700ms | 0ms (즉시) + 보조만 700ms |
| LLM 토큰 | 매 발화마다 호출 | 사전 1회 + 필요 시만 호출 |

---

### 계층 구조

```
┌─────────────────────────────────────────────────────────┐
│           Layer 1: Question Deck (사전 생성)              │
│                                                         │
│  면접 시작 전, v5.0 KG 분석 결과 기반으로                  │
│  주제별 질문 카드 미리 생성 (서버, Kimi K2.5)              │
│  → 클라이언트에 동기화 → 즉시 사용 가능                    │
│                                                         │
│  특징: 깊이 있는 분석, 모순점 사전 발굴, 0ms 지연          │
├─────────────────────────────────────────────────────────┤
│           Layer 2: Real-time Probing (실시간 보조)        │
│                                                         │
│  면접 대화 흐름에 따라 동적 생성 (클라이언트, Groq)         │
│  → Deck에 없는 꼬리질문, 새로운 모순점, 맥락 기반 심화     │
│                                                         │
│  특징: 대화 맥락 반영, 예측 불가 상황 대응                  │
└─────────────────────────────────────────────────────────┘
```

---

### Layer 1: Question Deck — 사전 생성

v5.0 분석 완료 시점에 KG를 탐색하여 주제별 질문 카드를 미리 만듭니다.

#### Deck 구조

```python
# domain/models/question_deck.py

class QuestionCard:
    question: str           # 질문 본문
    intent: str             # 이 질문의 목적 (1줄)
    evidence_summary: str   # 근거 요약 (1줄)
    priority: Priority      # HIGH / MEDIUM / LOW
    category: str           # 연결된 JD 요구사항 or 역량

class TopicGroup:
    topic: str              # "MSA 경험", "트러블슈팅", "리더십" 등
    jd_requirement_ref: str # JD 요구사항 노드 ID
    cards: list[QuestionCard]  # 주제별 2-3개 질문
    status: TopicStatus     # PENDING / PARTIAL / VERIFIED

class QuestionDeck:
    candidate_id: str
    groups: list[TopicGroup]   # 주제별 그룹 (5-8개)
    red_flags: list[QuestionCard]  # 모순/위험 신호 (별도 분리)
    ice_breakers: list[QuestionCard]  # 오프닝 질문 (1-2개)
```

#### Deck 생성 프로세스 (v5.0 분석 완료 후)

```
v5.0 분석 완료 → KG 완성
        │
        ▼
┌────────────────────────────────────────────────┐
│  DeckGenerator (서버, Kimi K2.5 + Graph Tools) │
│                                                │
│  1. get_jd_coverage() → 미검증 역량 목록        │
│  2. find_contradictions() → 모순점 목록         │
│  3. get_unverified_topics() → 미확인 주장 목록  │
│                                                │
│  주제별로 그래프 도구 호출하며 질문 생성:         │
│                                                │
│  for topic in jd_requirements:                 │
│    evidence = get_skill_evidence(topic.skill)   │
│    cards = llm.generate_questions(              │
│      topic=topic,                              │
│      evidence=evidence,                        │
│      depth="deep"  # 시간 여유 → 깊이 있게     │
│    )                                           │
│    deck.add_group(topic, cards)                 │
│                                                │
│  모순점 → red_flags 카드 별도 생성              │
│  오프닝 → ice_breakers 생성 (경력 기반 가벼운)  │
└────────────────────────────┬───────────────────┘
                             │
                             ▼
                    DB 저장 + 클라이언트 동기화
```

#### Deck 예시

```
📋 Question Deck — 김민수 (Backend Engineer)

🔓 오프닝 (Ice Breaker)
┌──────────────────────────────────────┐
│ "GitHub에서 spring-commerce 프로젝트 │
│  를 꽤 활발히 하신 것 같은데, 최근에 │
│  가장 집중하고 계신 기술이 뭔가요?"   │
│                                      │
│  의도: 자연스러운 대화 시작 + 관심사  │
└──────────────────────────────────────┘

📂 주제 1: MSA 분산 환경 [미검증]  ── 질문 3개
┌──────────────────────────────────────┐
│ Q1. "이력서에 MSA 전환 경험을        │
│ 적으셨는데, 서비스를 어떤 기준으로    │
│ 분리하셨나요?"                       │
│ 의도: MSA 설계 원칙 이해도           │
│ 근거: 이력서 기재, Git에 모놀리식만   │
├──────────────────────────────────────┤
│ Q2. "서비스 간 통신은 어떤 방식을     │
│ 사용하셨나요? gRPC, REST, 메시지큐?" │
│ 의도: 실무 수준 검증                 │
├──────────────────────────────────────┤
│ Q3. "분산 트랜잭션 이슈를 겪으신 적   │
│ 있나요? 어떻게 해결하셨나요?"        │
│ 의도: 실전 경험 깊이                 │
└──────────────────────────────────────┘

📂 주제 2: 캐싱 / Redis [약한 증거]  ── 질문 2개
  ...

📂 주제 3: 트러블슈팅 [미검증]  ── 질문 2개
  ...

🔴 Red Flags ── 모순/위험 신호
┌──────────────────────────────────────┐
│ ⚠ 이력서: "팀 프로젝트로 캐싱 구축"  │
│   Git: 해당 레포 커밋 1인 = 본인만    │
│                                      │
│ Q. "캐싱 레이어를 구축할 때 팀 내     │
│ 역할 분담은 어떻게 하셨나요?"        │
│ 의도: 팀 vs 개인 기여도 명확화       │
└──────────────────────────────────────┘
```

---

### Layer 2: Real-time Probing — 실시간 보조

Deck이 커버하지 못하는 **대화 맥락 기반** 질문만 실시간으로 생성합니다.

#### 실시간 생성이 발동하는 3가지 트리거

| 트리거 | 상황 | 예시 |
|--------|------|------|
| **모순 감지** | 지원자 발화가 Deck/KG와 충돌 | "혼자 다 했다" ↔ 이력서 "팀 프로젝트" |
| **예상 외 주제** | Deck에 없는 기술/경험 언급 | Deck에 없는 "Kafka" 언급 → 심화 질문 |
| **꼬리 질문** | Deck 질문 사용 후 답변이 불충분 | 답변이 모호 → 구체적 수치 요구 |

```
지원자 발화 완료 (stt:final)
        │
        ▼
┌───────────────────────────────────┐
│  RealTimeAnalyzer                 │
│                                   │
│  1. 발화 내용 vs Deck 주제 매칭    │
│     → 매칭되면 Deck 카드 자동 활성│
│                                   │
│  2. 트리거 조건 체크               │
│     → 모순 감지? 예상 외 주제?     │
│     → 트리거 없으면 → 생성 안 함   │
│                                   │
│  3. 트리거 있을 때만               │
│     → Groq LLM 호출 (실시간)      │
│     → 새 카드 생성 → UI 푸시      │
└───────────────────────────────────┘
```

**핵심: 매 발화마다 LLM을 호출하지 않습니다.** 트리거 조건 충족 시에만 호출하므로 비용과 노이즈를 대폭 줄입니다.

---

### UI에서의 2계층 표현

```
┌──────────────────────────────────────┐
│ Zone B: 질문 카드 영역               │
│                                      │
│  🔴 실시간 — 모순 발견          NOW  │
│ ┌──────────────────────────────────┐ │
│ │ "혼자 구축" 발언 ↔ 팀 프로젝트   │ │
│ │ Q. "캐시 무효화 전략은?"         │ │
│ │ [사용함 ✓]  [다른 질문 ↻]       │ │
│ └──────────────────────────────────┘ │
│                      ↑ Layer 2       │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│                      ↓ Layer 1       │
│  📂 MSA 분산 환경           [미검증] │
│ ┌──────────────────────────────────┐ │
│ │ Q1. "서비스 분리 기준이           │ │
│ │  어떻게 되나요?"                  │ │
│ │ 의도: MSA 설계 원칙              │ │
│ │ [사용함 ✓]  [다음 질문 ▶]       │ │
│ ├──────────────────────────────────┤ │
│ │ Q2. "서비스 간 통신 방식은?"      │ │
│ │ 의도: 실무 수준 검증              │ │
│ │ [사용함 ✓]  [다음 질문 ▶]       │ │
│ └──────────────────────────────────┘ │
│                                      │
│  📂 캐싱 / Redis             [약함] │
│ ┌──────────────────────────────────┐ │
│ │ Q1. "캐싱 도입 전후 성능 차이는?" │ │
│ │ 의도: 정량적 결과 확인            │ │
│ │ [사용함 ✓]  [다음 질문 ▶]       │ │
│ └──────────────────────────────────┘ │
│                                      │
│  📂 트러블슈팅               [미검증]│
│  ...                                 │
│                                      │
└──────────────────────────────────────┘
```

**UI 동작 규칙:**

| 규칙 | 설명 |
|------|------|
| Layer 2(실시간)는 항상 **최상단** | 긴급도가 높으므로 시선 우선 |
| Layer 1(Deck)은 **주제별 접이식** | 현재 대화 주제와 매칭되는 그룹 자동 펼침 |
| `사용함` 누르면 | 해당 카드 반투명 + 커버리지 반영 |
| `다음 질문 ▶` | 같은 주제의 다음 Deck 질문으로 이동 |
| `다른 질문 ↻` | Layer 2 실시간 재생성 (같은 의도, 다른 각도) |
| 대화 주제 변경 감지 시 | 해당 주제 그룹 자동 펼침 + 스크롤 |

---

### Deck 생성 타이밍과 흐름 (전체)

```
v5.0 분석 요청
    │
    ▼
Worker들이 KG 구축 (Graph-First)
    │
    ▼
분석 완료 → DeckGenerator 실행 (서버)
    │
    ├── KG 그래프 도구로 주제별 질문 생성
    ├── Red Flags 카드 생성
    ├── Ice Breaker 생성
    │
    ▼
Question Deck DB 저장
    │
    ▼ (면접 시작 전)
클라이언트 동기화: KG + Deck + Embeddings 다운로드
    │
    ▼ (면접 시작)
Layer 1: Deck 카드 즉시 표시 (0ms)
Layer 2: 대화 흐름에 따라 트리거 시에만 실시간 생성
    │
    ▼ (면접 종료)
사용된 카드 + 실시간 생성 카드 → 스코어카드 집계
```

---

이 2계층 질문 시스템 방향이 맞는지요? 괜찮으면 **섹션 5: 백엔드 확장 설계**로 넘어가겠습니다.

### [어시스턴트] 섹션 5: 백엔드 확장 설계 (Line 478)

## 섹션 5: 백엔드 확장 설계 (v5.0 + Live 통합)

### 1. 모노레포 디렉토리 구조

v5.0 분석 백엔드와 Live 면접 백엔드가 **하나의 FastAPI 앱** 안에 DDD 계층으로 공존합니다.

```
jittda/
├── backend/
│   └── src/
│       ├── domain/                    # 순수 비즈니스 로직 (외부 의존 없음)
│       │   ├── models/
│       │   │   ├── candidate.py       # 지원자 도메인 모델
│       │   │   ├── knowledge_graph.py # KG 도메인 모델
│       │   │   ├── question_deck.py   # Deck 도메인 모델
│       │   │   ├── interview_session.py # Live 세션 모델
│       │   │   ├── scorecard.py       # 스코어카드 모델
│       │   │   └── transcript.py      # STT 트랜스크립트 모델
│       │   ├── strategies/
│       │   │   ├── question/          # 질문 생성 Strategy들
│       │   │   │   ├── follow_up.py
│       │   │   │   ├── contradiction.py
│       │   │   │   ├── coverage_gap.py
│       │   │   │   └── deep_dive.py
│       │   │   └── scoring/           # 평가 Strategy들
│       │   ├── workers/               # v5.0 분석 Worker들
│       │   │   ├── base.py            # BaseWorker (Template Method)
│       │   │   ├── identity_worker.py
│       │   │   ├── resume_worker.py
│       │   │   ├── crossref_worker.py
│       │   │   └── ...
│       │   └── services/
│       │       ├── deck_generator.py  # Deck 생성 도메인 서비스
│       │       ├── live_analyzer.py   # 실시간 분석 도메인 서비스
│       │       └── report_builder.py  # 리포트 생성 도메인 서비스
│       │
│       ├── application/               # 유스케이스 오케스트레이션
│       │   ├── commands/              # Command 핸들러 (CQS)
│       │   │   ├── start_analysis.py
│       │   │   ├── generate_deck.py
│       │   │   ├── start_interview.py
│       │   │   ├── end_interview.py
│       │   │   └── approve_scorecard.py
│       │   ├── queries/               # Query 핸들러
│       │   │   ├── get_candidate.py
│       │   │   ├── get_deck.py
│       │   │   ├── get_scorecard.py
│       │   │   └── get_report.py
│       │   └── graphs/                # LangGraph StateGraph 정의
│       │       ├── meta_agent.py      # v5.0 HMAS 그래프
│       │       └── live_agent.py      # Live 실시간 분석 그래프
│       │
│       ├── infrastructure/            # 외부 시스템 Adapter
│       │   ├── adapters/
│       │   │   ├── stt/
│       │   │   │   └── deepgram.py
│       │   │   ├── llm/
│       │   │   │   ├── kimi_k2.py     # 분석용
│       │   │   │   └── groq.py        # 실시간용
│       │   │   ├── graph/
│       │   │   │   └── networkx_adapter.py
│       │   │   ├── vector/
│       │   │   │   └── pgvector.py
│       │   │   └── external/
│       │   │       ├── github.py
│       │   │       └── linkedin.py
│       │   └── persistence/           # Repository 구현
│       │       ├── pg_candidate_repo.py
│       │       ├── pg_kg_repo.py
│       │       ├── pg_session_repo.py
│       │       └── pg_deck_repo.py
│       │
│       └── interface/                 # 진입점 (API, WebSocket)
│           ├── api/
│           │   ├── v1/
│           │   │   ├── candidates.py  # 지원자 CRUD
│           │   │   ├── analysis.py    # v5.0 분석 시작/상태
│           │   │   ├── decks.py       # Deck 조회
│           │   │   ├── interviews.py  # 세션 생성/조회
│           │   │   ├── reports.py     # 리포트 조회
│           │   │   └── sync.py        # 클라이언트 동기화
│           │   └── deps.py            # DI 컨테이너
│           └── ws/
│               └── live_interview.py  # WebSocket 실시간 통신
│
├── desktop/                           # Electron 앱
├── frontend/                          # 웹 프론트엔드
├── shared/                            # 공용 Port, 모델, 도구
│   ├── ports/                         # 인터페이스 정의
│   ├── models/                        # 공유 DTO
│   ├── tools/                         # Graph Tool Set
│   └── events/                        # EventBus 타입
└── infra/                             # Docker, DB, 배포
```

---

### 2. REST API 설계

면접 전/후 데이터 교환은 REST로 처리합니다.

#### 분석 관련

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/analysis/start` | v5.0 분석 시작 (KG 구축 + Deck 생성) |
| GET | `/api/v1/analysis/{id}/status` | 분석 진행 상태 |
| GET | `/api/v1/candidates/{id}/knowledge-graph` | KG JSON export (클라이언트 동기화) |
| GET | `/api/v1/candidates/{id}/embeddings` | 벡터 데이터 다운로드 (LanceDB용) |
| GET | `/api/v1/candidates/{id}/deck` | Question Deck 조회 |

#### Live 면접 관련

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/interviews` | 세션 생성 (candidate_id, mode) |
| GET | `/api/v1/interviews/{id}` | 세션 정보 조회 |
| PATCH | `/api/v1/interviews/{id}/end` | 면접 종료 → 리포트 생성 트리거 |
| GET | `/api/v1/interviews/{id}/report` | 면접 결과 리포트 |
| PATCH | `/api/v1/interviews/{id}/scorecard` | 스코어카드 수정/승인 |

#### 동기화

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/sync/{candidate_id}/bundle` | KG + Deck + Embeddings 번들 다운로드 |
| POST | `/api/v1/sync/{session_id}/upload` | 면접 종료 후 트랜스크립트 + 카드 사용 이력 업로드 |

---

### 3. WebSocket 설계 (Live 면접 실시간 통신)

면접 중 클라이언트↔서버 실시간 이벤트는 WebSocket으로 처리합니다.

```
Client (Electron)                    Server (FastAPI)
      │                                    │
      │── ws://api/v1/ws/interview/{id} ──▶│
      │                                    │
      │  ┌─────────────────────────┐       │
      │  │ Client → Server 이벤트   │       │
      │  │                         │       │
      │  │ transcript.segment      │──────▶│  트랜스크립트 저장
      │  │ { speaker, text, ts }   │       │
      │  │                         │       │
      │  │ card.used               │──────▶│  카드 사용 기록
      │  │ { card_id }             │       │
      │  │                         │       │
      │  │ card.dismissed          │──────▶│  카드 무시 기록
      │  │ { card_id }             │       │
      │  │                         │       │
      │  │ coverage.manual_verify  │──────▶│  수동 검증 완료 기록
      │  │ { topic_id }            │       │
      │  │                         │       │
      │  │ interview.end           │──────▶│  면접 종료 트리거
      │  └─────────────────────────┘       │
      │                                    │
      │  ┌─────────────────────────┐       │
      │  │ Server → Client 이벤트   │       │
      │  │                         │       │
      │◀─│ coverage.updated        │───────│  커버리지 재계산 결과
      │  │ { topics: [...] }       │       │
      │  │                         │       │
      │◀─│ report.ready            │───────│  리포트 생성 완료 알림
      │  │ { report_url }          │       │
      │  └─────────────────────────┘       │
      │                                    │
```

**핵심: 실시간 질문 생성은 클라이언트에서 직접 처리** (Groq API 호출). 서버는 데이터 저장과 커버리지 재계산만 담당합니다. 서버 의존을 최소화하여 Local-First 원칙을 지킵니다.

```python
# interface/ws/live_interview.py

@router.websocket("/ws/interview/{session_id}")
async def interview_websocket(ws: WebSocket, session_id: str):
    session = await session_repo.get(session_id)
    await ws.accept()
    
    try:
        while True:
            message = await ws.receive_json()
            event_type = message["type"]
            
            handler = event_handlers.get(event_type)  # Registry 패턴
            if handler:
                result = await handler.handle(session, message["data"])
                if result.broadcast:
                    await ws.send_json(result.to_dict())
    except WebSocketDisconnect:
        await session_repo.mark_disconnected(session_id)
```

---

### 4. 면접 세션 생명주기

```
 [생성]            [동기화]          [진행중]         [분석중]        [완료]
CREATED ──────▶ SYNCING ──────▶ IN_PROGRESS ──────▶ ANALYZING ──────▶ COMPLETED
   │               │                │                  │               │
   │  POST /       │  GET /sync/    │  WebSocket       │  리포트 생성   │  GET /report
   │  interviews   │  bundle       │  연결             │  (서버)       │
   │               │               │                   │               │
   │               │               ├─ transcript 저장  │               │
   │               │               ├─ card 사용 기록   │               │
   │               │               └─ coverage 갱신   │               │
```

```python
# domain/models/interview_session.py

class InterviewSession:
    id: str
    candidate_id: str
    mode: InterviewMode          # O

### [사용자] 에러 처리 체계화 요청 (Line 485)

> 좋은데 에러 처리로직을 확실히 구조화하고 로그도 확실하게 뭐가 문제인지 하나의 잡이나 요청마다 uuid를 부여 어디에서 어떻게 문제가 발생했는지 어느 깊이에서 발생했는지 등의 확실한 에러처리로직이 있으면 좋겠어 프론트와 백엔드도 프론트도 기본 베이스 스키마를 기준으로 해당 에러를 상속해서 구체화한후 반환되도록 (구글에서 예외처리 하는방식일텐데 확인해보고)

### [어시스턴트] 에러 처리 체계 설계 (Line 488-499)

좋은 포인트입니다. Google의 AIP-193 에러 모델을 기반으로 우리 시스템에 맞는 구조화된 에러 처리 체계를 설계하겠습니다.

Google AIP-193 모델을 확인했습니다. 이를 기반으로 우리 시스템에 맞게 설계합니다.

## 섹션 5-1: 구조화된 에러 처리 & 관측성(Observability) 체계

### 1. 핵심 원칙 (Google AIP-193 기반)

| 원칙 | 적용 |
|------|------|
| **모든 요청에 Correlation ID** | UUID v7 (시간순 정렬 가능) — 요청 시작부터 응답까지 추적 |
| **에러 계층 상속** | BaseError → DomainError → 구체 에러 (어느 깊이든 동일 스키마) |
| **에러 = 값 객체** | 예외를 throw하되, 응답은 항상 구조화된 JSON |
| **Partial Error 금지** | Google AIP-193: 부분 에러 반환 금지, 성공 or 실패 명확 |
| **reason + domain 쌍 불변** | 같은 에러는 항상 같은 (reason, domain) → 모니터링/알림 가능 |

---

### 2. Correlation ID 전파 체계

모든 요청/잡에 UUID가 부여되고, 시스템 전 계층을 관통합니다.

```
Client (Electron/Web)              Server (FastAPI)
      │                                 │
      │  X-Correlation-ID: {uuid}  ────▶│  미들웨어가 추출 or 생성
      │                                 │
      │                           ┌─────┴─────────────────────────┐
      │                           │ ContextVar("correlation_id")  │
      │                           │                               │
      │                           │  API Layer     [uuid]         │
      │                           │    ▼                          │
      │                           │  Application   [uuid]         │
      │                           │    ▼                          │
      │                           │  Domain        [uuid]         │
      │                           │    ▼                          │
      │                           │  Infrastructure [uuid]        │
      │                           │    ▼                          │
      │                           │  External API   [uuid]        │
      │                           └───────────────────────────────┘
      │                                 │
      │◀── Response + X-Correlation-ID ─┤
      │    + 에러 시 error.correlation_id│
```

```python
# infrastructure/middleware/correlation.py

import uuid
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

class CorrelationMiddleware:
    async def __call__(self, request, call_next):
        # 클라이언트가 보낸 ID 사용, 없으면 생성 (UUID v7 — 시간순)
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid7())
        correlation_id_var.set(corr_id)
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = corr_id
        return response
```

```python
# Job/분석 작업에도 동일하게 적용
class AnalysisJob:
    job_id: str          # 분석 잡 고유 ID
    correlation_id: str  # 요청 추적 ID
    # Worker 실행 시에도 이 correlation_id가 전파됨
```

---

### 3. 공용 에러 스키마 (shared/ — 프론트 + 백엔드 공유)

Google AIP-193의 `Status` + `ErrorInfo`를 Python/TypeScript 양쪽에 정의합니다.

```python
# shared/errors/base.py — Python (Backend)

class ErrorDetail:
    """추가 에러 상세 (Google AIP-193 details)"""
    type: str              # "ErrorInfo" | "ValidationError" | "RetryInfo"
    reason: str            # UPPER_SNAKE_CASE — "KG_NOT_FOUND"
    domain: str            # "jittda.analysis" | "jittda.live" | "jittda.sync"
    metadata: dict[str, str]  # 에러 관련 키-값 (요청 파라미터 등)

class ErrorResponse:
    """모든 에러 응답의 최종 형태 (AIP-193 기반)"""
    code: int              # HTTP 상태 코드 (404, 500 등)
    status: str            # "NOT_FOUND", "INTERNAL" 등
    message: str           # 개발자용 디버그 메시지 (영어)
    localized_message: str # 사용자 표시용 메시지 (한글)
    correlation_id: str    # 요청 추적 UUID
    timestamp: str         # ISO 8601
    details: list[ErrorDetail]
    
    # 에러 발생 위치 추적
    origin: ErrorOrigin

class ErrorOrigin:
    """에러가 어디서, 어느 깊이에서 발생했는지"""
    layer: str             # "interface" | "application" | "domain" | "infrastructure"
    component: str         # "DeepgramAdapter" | "ResumeWorker" | "KGRepository"
    operation: str         # "stream_audio" | "parse_resume" | "save_graph"
    trace: list[str]       # 호출 스택 요약 ["API→StartInterview→SessionRepo→PostgreSQL"]
```

```typescript
// shared/errors/base.ts — TypeScript (Frontend + Desktop)

interface ErrorDetail {
  type: string;
  reason: string;         // "KG_NOT_FOUND"
  domain: string;         // "jittda.live"
  metadata: Record<string, string>;
}

interface ErrorOrigin {
  layer: string;
  component: string;
  operation: string;
  trace: string[];
}

interface ErrorResponse {
  code: number;
  status: string;
  message: string;
  localized_message: string;
  correlation_id: string;
  timestamp: string;
  details: ErrorDetail[];
  origin: ErrorOrigin;
}
```

**실제 에러 응답 예시:**

```json
{
  "code": 404,
  "status": "NOT_FOUND",
  "message": "Knowledge graph not found for candidate c8a2f..., analysis may not be completed",
  "localized_message": "지원자 분석이 아직 완료되지 않았습니다. 분석 완료 후 면접을 시작해주세요.",
  "correlation_id": "019505e8-7c3a-7b8e-9a1f-3e4b5c6d7e8f",
  "timestamp": "2026-02-17T10:23:45.123Z",
  "details": [
    {
      "type": "ErrorInfo",
      "reason": "KG_NOT_FOUND",
      "domain": "jittda.live",
      "metadata": {
        "candidate_id": "c8a2f...",
        "expected_status": "ANALYSIS_COMPLETED"
      }
    }
  ],
  "origin": {
    "layer": "application",
    "component": "StartInterviewHandler",
    "operation": "handle",
    "trace": ["API:POST /interviews", "StartInterviewHandler", "KGRepository.get_by_candidate"]
  }
}
```

---

### 4. 에러 계층 구조 (상속 체계)

```
BaseError (shared/)
├── DomainError                     # domain 계층 비즈니스 규칙 위반
│   ├── AnalysisError               # v5.0 분석 관련
│   │   ├── IdentityResolutionFailed
│   │   ├── KGConstructionFailed
│   │   └── DeckGenerationFailed
│   ├── InterviewError              # Live 면접 관련
│   │   ├── SessionNotFound
│   │   ├── SessionAlreadyActive
│   │   ├── AnalysisNotCompleted
│   │   └── InterviewAlreadyEnded
│   └── ScorecardError              # 평가 관련
│       ├── ScorecardNotReady
│       └── ScorecardAlreadyApproved
│
├── InfrastructureError             # infrastructure 계층 외부 시스템 장애
│   ├── AdapterError                # 외부 서비스 연동 실패
│   │   ├── STTConnectionFailed
│   │   ├── STTStreamInterrupted
│   │   ├── LLMRateLimited
│   │   ├── LLMTimeoutError
│   │   └── GitHubAPIFailed
│   ├── PersistenceError            # DB/저장소 장애
│   │   ├── KGSaveFailed
│   │   ├── TranscriptSaveFailed
│   │   └── ConnectionPoolExhausted
│   └── SyncError                   # 동기화 실패
│       ├── BundleDownloadFailed
│       └── TranscriptUploadFailed
│
└── InterfaceError                  # interface 계층 입력 검증
    ├── ValidationError             # 요청 데이터 검증 실패
    ├── AuthenticationError         # 인증 실패
    └── RateLimitExceeded           # 요청 제한 초과
```

```python
# shared/errors/base.py

class BaseError(Exception):
    """모든 에러의 루트. 발생 시점에 자동으로 correlation_id, origin 주입."""
    
    def __init__(
        self,
        reason: str,            # "KG_NOT_FOUND"
        domain: str,            # "jittda.analysis"
        message: str,           # 개발자용 영어
        localized_message: str, # 사용자용 한글
        http_code: int = 500,
        metadata: dict[str, str] | None = None,
    ):
        self.reason = reason
        self.domain = domain
        self.message = message
        self.localized_message = localized_message
        self.http_code = http_code
        self.metadata = metadata or {}
        
        # 자동 주입
        self.correlation_id = correlation_id_var.get("")
        self.origin = self._capture_origin()
        self.timestamp = datetime.now(UTC).isoformat()
    
    def _capture_origin(self) -> ErrorOrigin:
        """호출 스택에서 layer/component/operation 자동 추출"""
        frame = inspect.currentframe().f_back.f_back
        module = frame.f_globals.get("__name__", "")
        
        layer = self._detect_layer(module)  # 모듈 경로로 계층 판별
        component = frame.f_locals.get("self", None).__class__.__name__
        operation = frame.f_code.co_name
        
        return ErrorOrigin(layer=layer, component=component, operation=operation)
    
    def to_response(self) -> ErrorResponse:
        """FastAPI 응답용 직렬화"""
        return ErrorResponse(
            code=self.http_code,
            status=HTTP_CODE_TO_STATUS[self.http_code],
            message=self.message,
        

### [사용자] 에러 코드 체계 요청 (Line 506)

> 각 에러를 구체화한 에러코드를 임의로 구현해서 지금은 나혼자 하지만 에러코드만으로 찾아보면 어떤에러인지 어디서 나는 에러인지를 찾을수 있도록 하면 좋을것같은데 좀더 최신 에러처리기법과 구조와 없나?

### [어시스턴트] RFC 9457 + ErrorPrism 에러 코드 체계 (Line 540)

좋습니다. 3가지 최신 접근법을 종합하여 **자기 설명적(Self-Describing) 에러 코드 체계**를 설계합니다.

## 섹션 5-1 개선: 자기 설명적 에러 코드 + Error Chain + RFC 9457

### 조사 결과 — 최신 기법 3가지 종합

| 출처 | 기법 | 적용 |
|------|------|------|
| **RFC 9457** (2024 IETF 표준) | Problem Details — `type` URI + 확장 필드 | 에러 응답 포맷 표준 |
| **Stripe** | 계층적 snake_case 코드 (`card_declined`) + `doc_url` | 에러 코드 네이밍 |
| **ErrorPrism** (ByteDance 2025) | Error Wrapping Chain — 에러 전파 경로 추적 | 근본 원인 체인 |

---

### 1. 에러 코드 형식: `{도메인}.{계층}.{구분코드}`

에러 코드만 보면 **어디서(도메인)**, **어느 깊이에서(계층)**, **무엇이(구체 에러)** 발생했는지 즉시 파악됩니다.

```
에러 코드 구조:

  JL - 1 - A - 0001
  │    │   │    │
  │    │   │    └── 순번 (4자리, 도메인 내 고유)
  │    │   └─────── 계층 코드 (어디서 터졌는지)
  │    └─────────── 심각도 (1=Critical, 2=High, 3=Medium, 4=Low)
  └──────────────── 도메인 접두사 (2자리)
```

#### 도메인 접두사

| 코드 | 도메인 | 설명 |
|------|--------|------|
| `JA` | jittda.analysis | v5.0 분석 파이프라인 |
| `JL` | jittda.live | Live 면접 세션 |
| `JR` | jittda.report | 리포트/스코어카드 |
| `JS` | jittda.sync | 클라이언트 동기화 |
| `JC` | jittda.common | 공용 (인증, 검증 등) |

#### 계층 코드

| 코드 | 계층 | 설명 |
|------|------|------|
| `I` | Interface | API 입력 검증, 인증 |
| `A` | Application | 유스케이스 오케스트레이션 |
| `D` | Domain | 비즈니스 규칙 위반 |
| `F` | inFrastructure | 외부 서비스, DB |
| `C` | Client | 프론트/데스크탑 내부 |

#### 심각도

| 코드 | 레벨 | 면접 중 대응 |
|------|------|-------------|
| `1` | Critical | 면접 중단 위험 — 데이터 보존 후 종료 안내 |
| `2` | High | 폴백 모드 전환 — Deck 전용 진행 |
| `3` | Medium | 자동 재시도 + 토스트 알림 |
| `4` | Low | 자동 재시도, 사용자 표시 안 함 |

#### 전체 에러 코드 레지스트리

```
┌────────────┬────────────────────────────────────┬──────────────────────────────┐
│ 코드       │ 이름                                │ 설명                         │
├────────────┼────────────────────────────────────┼──────────────────────────────┤
│            │ ═══ v5.0 분석 (JA) ═══             │                              │
│ JA-3-D-0001│ IDENTITY_RESOLUTION_FAILED         │ 지원자 Identity 통합 실패      │
│ JA-2-F-0002│ GITHUB_CLONE_FAILED                │ 레포 클론 실패                │
│ JA-2-F-0003│ GITHUB_RATE_LIMITED                 │ GitHub API 제한 초과          │
│ JA-3-D-0004│ AST_PARSE_UNSUPPORTED_LANG         │ 미지원 언어 파일               │
│ JA-2-F-0005│ KG_CONSTRUCTION_FAILED             │ Knowledge Graph 구축 실패      │
│ JA-3-F-0006│ LLM_ANALYSIS_TIMEOUT               │ 분석용 LLM 응답 시간 초과      │
│ JA-2-D-0007│ DECK_GENERATION_FAILED             │ Question Deck 생성 실패       │
│ JA-4-F-0008│ SONARQUBE_UNAVAILABLE              │ SonarQube 컨테이너 미기동      │
│ JA-3-D-0009│ PLAGIARISM_CHECK_FAILED            │ 표절 탐지 모듈 실패            │
│ JA-2-F-0010│ VECTOR_EMBEDDING_FAILED            │ 임베딩 생성 실패               │
│            │                                    │                              │
│            │ ═══ Live 면접 (JL) ═══             │                              │
│ JL-3-D-0001│ ANALYSIS_NOT_COMPLETED             │ 사전 분석 미완료               │
│ JL-3-D-0002│ SESSION_NOT_FOUND                  │ 세션 ID 없음                  │
│ JL-3-D-0003│ SESSION_ALREADY_ACTIVE             │ 이미 진행 중인 면접            │
│ JL-3-D-0004│ INTERVIEW_ALREADY_ENDED            │ 이미 종료된 면접               │
│ JL-1-C-0010│ AUDIO_CAPTURE_FAILED               │ OS 오디오 캡처 실패            │
│ JL-1-C-0011│ AUDIO_PERMISSION_DENIED            │ 마이크 권한 거부               │
│ JL-2-F-0020│ STT_CONNECTION_FAILED              │ STT WebSocket 연결 실패       │
│ JL-3-F-0021│ STT_STREAM_INTERRUPTED             │ STT 스트림 일시 중단           │
│ JL-4-F-0022│ STT_PARTIAL_TIMEOUT                │ STT 부분 결과 지연             │
│ JL-2-F-0030│ LLM_REALTIME_TIMEOUT               │ 실시간 LLM 응답 시간 초과      │
│ JL-3-F-0031│ LLM_RATE_LIMITED                   │ LLM API 호출 제한             │
│ JL-4-F-0032│ LLM_LOW_CONFIDENCE                 │ LLM 응답 신뢰도 낮음           │
│ JL-3-C-0040│ LOCAL_DB_CORRUPTED                 │ LanceDB 로컬 데이터 손상       │
│ JL-3-C-0041│ GRAPH_QUERY_FAILED                 │ graphology 쿼리 실패           │
│ JL-2-F-0050│ WEBSOCKET_DISCONNECTED             │ 서버 WS 연결 끊김              │
│            │                                    │                              │
│            │ ═══ 리포트 (JR) ═══                │                              │
│ JR-3-A-0001│ SCORECARD_GENERATION_FAILED        │ 스코어카드 생성 실패            │
│ JR-3-D-0002│ SCORECARD_ALREADY_APPROVED         │ 이미 승인된 스코어카드          │
│ JR-3-A-0003│ REPORT_NOT_READY                   │ 리포트 생성 미완료              │
│ JR-3-D-0004│ INSUFFICIENT_DATA                  │ 분석 데이터 부족               │
│            │                                    │                              │
│            │ ═══ 동기화 (JS) ═══                │                              │
│ JS-2-F-0001│ BUNDLE_DOWNLOAD_FAILED             │ 동기화 번들 다운로드 실패       │
│ JS-3-F-0002│ VERSION_MISMATCH                   │ 클라이언트/서버 버전 불일치     │
│ JS-2-F-0003│ TRANSCRIPT_UPLOAD_FAILED           │ 트랜스크립트 업로드 실패        │
│ JS-3-F-0004│ KG_SYNC_CONFLICT                   │ KG 동기화 충돌                │
│            │                                    │                              │
│            │ ═══ 공용 (JC) ═══                  │                              │
│ JC-3-I-0001│ VALIDATION_FAILED                  │ 요청 데이터 검증 실패          │
│ JC-2-I-0002│ AUTHENTICATION_FAILED              │ 인증 실패                     │
│ JC-3-I-0003│ RATE_LIMIT_EXCEEDED                │ 요청 제한 초과                 │
│ JC-1-F-0004│ DATABASE_CONNECTION_FAILED         │ DB 연결 실패                  │
│ JC-2-F-0005│ CONNECTION_POOL_EXHAUSTED           │ 커넥션 풀 고갈                │
└────────────┴────────────────────────────────────┴──────────────────────────────┘
```

**에러 코드만 보고 즉시 파악 가능:**

```
JL-2-F-0020
│  │  │  │
│  │  │  └── STT_CONNECTION_FAILED (20번)
│  │  └───── inFrastructure 계층 (외부 서비스 문제)
│  └──────── High 심각도 (폴백 모드 필요)
└─────────── Live 면접 도메인
```

---

### 2. RFC 9457 Problem Details 응답 포맷

Google AIP-193 대신 **IETF 표준 RFC 9457**을 적용합니다. 더 최신이고 업계 표준입니다.

```python
# shared/errors/problem_detail.py

class ProblemDetail:
    """RFC 9457 Problem Details + 확장 필드"""
    
    # ─── RFC 9457 표준 필드 ───
    type: str              # 에러 문서 URI: "https://docs.jittda.io/errors/JL-2-F-0020"
    title: str             # 짧은 에러 제목 (불변): "STT Connection Failed"
    status: int            # HTTP 상태 코드: 502
    detail: str            # 이번 발생의 구체 설명: "Deepgram WebSocket timed out after 5s"
    instance: str          # 이 발생의 고유 URI: "/errors/019505e8-7c3a..."
    
    # ─── Jittda 확장 필드 ───
    error_code: str        # 자기 설명적 코드: "JL-2-F-0020"
    correlation_id: str    # 요청 추적 UUID
    timestamp: str         # ISO 8601
    localized: str         # 사용자용 한글 메시지
    severity: int          # 1-4
    
    # Error Chain (ErrorPrism 기법)
    chain: list[ErrorChainLink] | None
    
    # 메타데이터 (AIP-193 계승)
    metadata: dict[str, str]
```

**Content-Type: `application/problem+json`** (RFC 9457 표준)

**응답 예시:**

```json
{
  "type": "https://docs.jittda.io/errors/JL-2-F-0020",
  "title": "STT Connection Failed",
  "status": 502,
  "detail": "Deepgram WebSocket connection timed out after 5000ms on attempt 3/3",
  "instance": "/errors/019505e8-7c3a-7b8e-9a1f-3e4b5c6d7e8f",
  
  "error_code": "JL-2-F-0020",
  "correlation_id": "019505e8-7c3a-7b8e-9a1f-3e4b5c6d7e8f",
  "timestamp": "2026-02-17T10:23:45.123Z",
  "localized": "음성 인식 연결에 실패했습니다. 자동 재연결을 시도합니다.",
  "severity": 2,
  
  "chain": [
    {
      "depth": 0,
      "layer": "interface",
      "component": "LiveInterviewWS",
      "operation": "handle_audio_stream",
      "message": "STT stream setup failed for session s-abc123"
    },
    {
      "depth": 1,
      "layer": "application",
      "component": "AudioPipeline",
      "operation": "connect_stt",
      "message": "STTProvider.connect() failed after 3 retries"
    },
    {
      "depth": 2,
      "layer": "infrastructure",
      "component": "DeepgramAdapter",
      "operation": "connect",
      "message": "WebSocket handshake timeout: wss://api.deepgram.com/v1/listen"
    }
  ],
  
  "metadata": {
    "session_id": "s-abc123",
    "stt_provider": "deepgram",
    "retry_count": "3",
    "timeout_ms": "5000"
  }
}
```

---

### 3. Error Chain (ErrorPrism 방식) — 에러 전파 경로 추적

ByteDance의 ErrorPrism 논문에서 제안한 **Error Wrapping Chain**을 적용합니다. 에러가 하위 계층에서 상위로 전파될 때, 각 계층이 맥락을 추가합니다.

```python
# shared/errors/chain.py

@dataclass
class ErrorChainLink:
    """에러 체인의 한 링크 — 에러가 지나간 각 계층의 흔적"""
    depth: int          # 0 = 최상위 (API), 숫자 클수록 근본 원인에 가까움
    layer: str          # interface | application | domain | infrastructure | client
    component: str      # 클래스명
    operation: str      # 메서드명
    message: str        # 이 계층에서 추가한 맥락

class BaseError(Exception):
    _chain: list[ErrorChainLink]
    
    def __init__(self, error_code: str, detail: str, **kwargs):
        self.error_code = error_code
        self.detail = detail
        self._chain = []
        self._severity = int(error_code.split("-")[1])
        # ... 나머지 초기화
    
    def wrap(self, component: str, operation: str, context: str) -> "BaseError":
        """상위 계층이 에러를 감싸면서 맥락 추가 (ErrorPrism 패턴)"""
        self._chain.append(ErrorChainLink(
            depth=len(self._chain),
            layer=self._detect_layer(),
            component=component,
            operation=operation,
            message=context,
        ))
        return self  # 체이닝 가능
```

**사용 — 각 계층이 맥락을 추가하며 전파:**

```python
# infrastructure/adapters/stt/deepgram.py (depth 2 — 근본 원인)
class DeepgramAdapter:
    async def connect(self, config):
        try:
            await self._ws.connect(config.url, timeout=5.0)
        except TimeoutError:
            raise STTConnectionFailed(
                provider="deepgram", 
                cause="WebSocket handshake timeout"
            )

# application/pipelines/audio_pipeline.py (depth 1 — 중간 계층)
class AudioPipeline:
    async def connect_stt(self):
        try:
            await self.stt_provider.connect(self.config)
        except STTConnectionFailed as e:
            raise e.wrap(
                "AudioPipeline", "connect_stt",
                f"STTProvider.connect() failed after 

### [사용자] Sentry + Infisical 추가 요청 (Line 547)

> 좋아 그리고 추가적으로 센트리도 적용할수 있도록 해줘 센트리는 다른곳에서 셀프호스팅할거야 infisical 환경변수 관리도 다른곳에서 셀프호스팅하는거 사용해서 환경변수 관리할수 있도록 추가해줘

### [어시스턴트] Sentry + Infisical 통합 설계 (Line 583)

조사 완료. Sentry + Infisical을 에러 처리 체계와 통합하여 설계합니다.

## 섹션 5-2: Sentry (셀프호스팅) + Infisical (셀프호스팅) 통합

### 1. 관측성 스택 전체 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                    외부 셀프호스팅 서버                           │
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────────────┐     │
│  │  Sentry Self-Hosted │    │  Infisical Self-Hosted      │     │
│  │  (에러/성능 모니터링) │    │  (시크릿/환경변수 관리)       │     │
│  │                     │    │                             │     │
│  │  DSN: https://      │    │  API: https://              │     │
│  │  sentry.jittda.io   │    │  secrets.jittda.io          │     │
│  └──────────┬──────────┘    └──────────────┬──────────────┘     │
│             │                              │                    │
└─────────────┼──────────────────────────────┼────────────────────┘
              │                              │
    ┌─────────┴──────────┐     ┌─────────────┴─────────────┐
    │ 에러/트랜잭션 전송    │     │ 시크릿 주입 (앱 시작 시)    │
    │ (sentry-sdk)        │     │ (infisical-sdk)           │
    │                     │     │                           │
    ▼                     ▼     ▼                           ▼
┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────────┐
│ Backend │  │ Desktop  │  │ Backend │  │ Desktop          │
│ FastAPI │  │ Electron │  │ Python  │  │ Node.js          │
│         │  │          │  │ SDK     │  │ SDK              │
└─────────┘  └──────────┘  └─────────┘  └──────────────────┘
```

---

### 2. Sentry 통합 — 에러 코드 체계와 연동

#### 백엔드 (FastAPI + sentry-sdk)

```python
# infrastructure/observability/sentry.py

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration

def init_sentry(config: AppConfig):
    sentry_sdk.init(
        dsn=config.sentry_dsn,  # Infisical에서 주입
        environment=config.environment,  # "production" | "staging" | "development"
        release=f"jittda-backend@{config.version}",
        
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(
                failed_request_status_codes=[range(400, 599)]
            ),
            SqlAlchemyIntegration(),
            HttpxIntegration(),  # Deepgram, Groq 등 외부 API 호출 추적
        ],
        
        traces_sample_rate=0.3,       # 성능 트레이싱 30%
        profiles_sample_rate=0.1,     # 프로파일링 10%
        
        # 에러 코드 체계와 연동
        before_send=enrich_with_error_code,
        before_send_transaction=attach_correlation_id,
    )
```

#### Sentry ↔ 에러 코드 연동 (핵심)

```python
# infrastructure/observability/sentry_hooks.py

def enrich_with_error_code(event: dict, hint: dict) -> dict:
    """BaseError 발생 시 Sentry 이벤트에 에러 코드 메타데이터 자동 주입"""
    
    exc = hint.get("exc_info", [None, None, None])[1]
    
    if isinstance(exc, BaseError):
        # ─── 에러 코드로 Sentry 태그 설정 (검색/필터링용) ───
        event["tags"] = event.get("tags", {}) | {
            "error_code": exc.error_code,              # "JL-2-F-0020"
            "error_domain": exc.error_code[:2],        # "JL"
            "error_severity": exc.severity,             # 2
            "error_layer": exc.parsed_layer,            # "infrastructure"
            "correlation_id": exc.correlation_id,
        }
        
        # ─── Sentry fingerprint → 같은 에러 코드끼리 그룹핑 ───
        event["fingerprint"] = [exc.error_code]
        
        # ─── Error Chain을 Sentry context로 첨부 ───
        event["contexts"] = event.get("contexts", {}) | {
            "error_chain": {
                "chain": [
                    {
                        "depth": link.depth,
                        "layer": link.layer,
                        "component": link.component,
                        "operation": link.operation,
                        "message": link.message,
                    }
                    for link in exc.chain
                ],
                "root_cause_depth": len(exc.chain) - 1,
                "root_cause_component": exc.chain[-1].component if exc.chain else "unknown",
            },
            "error_metadata": exc.metadata,
        }
    
    # ─── Correlation ID를 모든 이벤트에 주입 ───
    corr_id = correlation_id_var.get("")
    if corr_id:
        event.setdefault("tags", {})["correlation_id"] = corr_id
    
    return event


def attach_correlation_id(event: dict, hint: dict) -> dict:
    """트랜잭션(성능 추적)에도 correlation_id 태그 추가"""
    corr_id = correlation_id_var.get("")
    if corr_id:
        event.setdefault("tags", {})["correlation_id"] = corr_id
    return event
```

#### Sentry 미들웨어 — 요청별 컨텍스트 자동 설정

```python
# infrastructure/middleware/sentry_context.py

class SentryContextMiddleware:
    async def __call__(self, request: Request, call_next):
        corr_id = correlation_id_var.get("")
        
        # Sentry 스코프에 요청 정보 설정
        with sentry_sdk.new_scope() as scope:
            scope.set_tag("correlation_id", corr_id)
            scope.set_tag("api_version", "v1")
            scope.set_context("request_info", {
                "correlation_id": corr_id,
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host,
            })
            
            # 면접 세션 관련 요청이면 세션 컨텍스트 추가
            session_id = request.path_params.get("session_id")
            if session_id:
                scope.set_tag("session_id", session_id)
                scope.set_context("interview_session", {
                    "session_id": session_id,
                })
            
            response = await call_next(request)
            return response
```

#### 데스크탑 (Electron + @sentry/electron)

```typescript
// desktop/services/sentry.ts

import * as Sentry from "@sentry/electron/main";  // Main Process
import { init as rendererInit } from "@sentry/electron/renderer";  // Renderer

// Main Process 초기화
export function initSentryMain(config: AppConfig) {
  Sentry.init({
    dsn: config.sentryDsn,  // Infisical에서 주입
    environment: config.environment,
    release: `jittda-desktop@${config.version}`,
    
    // 에러 코드 연동
    beforeSend(event, hint) {
      const error = hint.originalException;
      
      if (error instanceof AppError) {
        event.tags = {
          ...event.tags,
          error_code: error.errorCode,
          error_domain: error.errorCode.slice(0, 2),
          error_severity: String(error.severity),
          correlation_id: error.correlationId,
        };
        event.fingerprint = [error.errorCode];
        event.contexts = {
          ...event.contexts,
          error_chain: { chain: error.chain },
        };
      }
      
      return event;
    },
  });
}

// Renderer Process 초기화
export function initSentryRenderer() {
  rendererInit({
    // Main과 동일 DSN — Sentry가 프로세스별로 구분
  });
}
```

#### Sentry에서 보이는 화면 (결과)

```
Sentry Dashboard
├── Issues (에러 그룹)
│   ├── JL-2-F-0020: STT_CONNECTION_FAILED (14건, 이번 주)
│   │   Tags: error_domain=JL, error_severity=2, error_layer=infrastructure
│   │   Context: error_chain → 3단계 전파 경로
│   │   
│   ├── JL-1-C-0010: AUDIO_CAPTURE_FAILED (3건)
│   └── JA-2-F-0003: GITHUB_RATE_LIMITED (7건)
│
├── Performance (트랜잭션)
│   ├── POST /api/v1/interviews → p95: 230ms
│   ├── POST /api/v1/analysis/start → p95: 1.2s
│   └── WS /ws/interview/{id} → 평균 세션: 38분
│
└── 필터링 예시
    ├── error_code:JL-* → Live 면접 에러만
    ├── error_severity:1 → Critical만
    ├── correlation_id:019505e8-... → 특정 요청 추적
    └── session_id:s-abc123 → 특정 면접 세션
```

---

### 3. Infisical 통합 — 환경변수/시크릿 관리

#### 시크릿 구조 (Infisical 프로젝트)

```
Infisical Project: "Jittda Live"
│
├── /backend                    # 백엔드 시크릿
│   ├── DATABASE_URL            # PostgreSQL 연결 문자열
│   ├── REDIS_URL               # Redis 연결 문자열
│   ├── 

### [어시스턴트] 섹션 6: DB 스키마 (Line 593)

## 섹션 6: 데이터 모델 / DB 스키마

### 1. 전체 ERD 개요

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
│  candidates  │────▶│ knowledge_    │────▶│ question_decks   │
│              │     │ graphs        │     │                  │
└──────┬───────┘     └───────────────┘     └────────┬─────────┘
       │                                            │
       │             ┌───────────────┐              │
       └────────────▶│ interview_    │◀─────────────┘
                     │ sessions      │
                     └───────┬───────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      ┌──────────────┐ ┌──────────┐ ┌────────────┐
      │ transcripts  │ │ card_    │ │ scorecards │
      │              │ │ events   │ │            │
      └──────────────┘ └──────────┘ └────────────┘
                                          │
                                          ▼
                                    ┌────────────┐
                                    │ reports    │
                                    └────────────┘
```

---

### 2. 코어 테이블

```sql
-- ============================================================
-- 0. 확장 모듈
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";        -- pgvector
CREATE EXTENSION IF NOT EXISTS "pg_trgm";       -- 트라이그램 텍스트 검색

-- ============================================================
-- 1. 지원자 (Candidate)
-- ============================================================
CREATE TABLE candidates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 기본 정보
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(255),
    identity_hash   VARCHAR(64) UNIQUE,          -- Identity Resolution 결과
    
    -- 소스 데이터 참조 (원본은 별도 저장, Reference Passing)
    resume_ref      UUID,                        -- 이력서 저장 ID
    linkedin_ref    UUID,                        -- LinkedIn 프로필 저장 ID
    portfolio_ref   UUID,                        -- 포트폴리오 저장 ID
    cover_letter_ref UUID,                       -- 커버레터 저장 ID
    
    -- 상태
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    -- PENDING → ANALYZING → ANALYZED → DECK_READY → INTERVIEW_READY
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_candidates_identity ON candidates(identity_hash);

-- ============================================================
-- 2. 채용 공고 (Job Description)
-- ============================================================
CREATE TABLE job_descriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    title           VARCHAR(200) NOT NULL,
    company         VARCHAR(100),
    department      VARCHAR(100),
    
    -- JD 내용
    raw_text        TEXT NOT NULL,
    parsed_requirements JSONB NOT NULL DEFAULT '[]',
    -- [{skill, priority: "high"|"medium"|"low", description}]
    
    -- 평가 루브릭
    rubric          JSONB NOT NULL DEFAULT '{}',
    -- {competencies: [{name, weight, criteria: [...]}]}
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 3. 지원자-JD 매핑
-- ============================================================
CREATE TABLE candidate_applications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    UUID NOT NULL REFERENCES candidates(id),
    jd_id           UUID NOT NULL REFERENCES job_descriptions(id),
    
    -- v5.0 분석 결과 참조
    analysis_job_id UUID REFERENCES analysis_jobs(id),
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (candidate_id, jd_id)
);
```

---

### 3. v5.0 분석 테이블

```sql
-- ============================================================
-- 4. 분석 잡 (Analysis Job)
-- ============================================================
CREATE TABLE analysis_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    UUID NOT NULL REFERENCES candidates(id),
    jd_id           UUID NOT NULL REFERENCES job_descriptions(id),
    correlation_id  UUID NOT NULL,               -- 요청 추적 ID
    
    -- 상태
    status          VARCHAR(20) NOT NULL DEFAULT 'QUEUED',
                    -- QUEUED → RUNNING → COMPLETED → FAILED
    
    -- LangGraph 실행 참조
    langgraph_thread_id VARCHAR(100),
    
    -- 진행도
    total_workers   INT NOT NULL DEFAULT 0,
    completed_workers INT NOT NULL DEFAULT 0,
    
    -- 결과 참조 (Reference Passing)
    kg_id           UUID REFERENCES knowledge_graphs(id),
    deck_id         UUID REFERENCES question_decks(id),
    
    -- 에러 (실패 시)
    error_code      VARCHAR(20),                 -- "JA-2-F-0005"
    error_detail    JSONB,                       -- ProblemDetail JSON
    
    -- 시간
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX idx_analysis_jobs_candidate ON analysis_jobs(candidate_id);
CREATE INDEX idx_analysis_jobs_correlation ON analysis_jobs(correlation_id);

-- ============================================================
-- 5. Worker 실행 결과 (Worker Results)
-- ============================================================
CREATE TABLE worker_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id          UUID NOT NULL REFERENCES analysis_jobs(id),
    
    worker_name     VARCHAR(50) NOT NULL,        -- "ResumeWorker", "ASTWorker"
    supervisor      VARCHAR(50) NOT NULL,        -- "forensic", "logic", "stack"
    
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    -- PENDING → RUNNING → COMPLETED → FAILED
    
    -- 결과 (Reference Passing — 원본 데이터는 별도)
    result_ref      UUID,                        -- 결과 저장 ID
    
    -- KG 기여도
    nodes_added     INT NOT NULL DEFAULT 0,
    edges_added     INT NOT NULL DEFAULT 0,
    
    -- 성능
    duration_ms     INT,
    llm_tokens_used INT DEFAULT 0,
    
    -- 에러
    error_code      VARCHAR(20),
    error_detail    JSONB,
    
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_worker_results_job ON worker_results(job_id);
```

---

### 4. Knowledge Graph 테이블

```sql
-- ============================================================
-- 6. Knowledge Graph (핵심)
-- ============================================================
CREATE TABLE knowledge_graphs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id    UUID NOT NULL REFERENCES candidates(id),
    jd_id           UUID REFERENCES job_descriptions(id),
    
    -- 그래프 데이터 (NetworkX JSON 호환)
    nodes           JSONB NOT NULL DEFAULT '[]',
    -- [{id, type, attrs: {name, canonical_name, ...}}]
    
    edges           JSONB NOT NULL DEFAULT '[]',
    -- [{source, target, type, attrs: {strength, confidence, ...}}]
    
    -- 통계 (Generated Column)
    node_count      INT GENERATED ALWAYS AS (jsonb_array_length(nodes)) STORED,
    edge_count      INT GENERATED ALWAYS AS (jsonb_array_length(edges)) STORED,
    
    -- 버전 관리 (Optimistic Locking)
    version         INT NOT NULL DEFAULT 1,
    
    -- 동기화 추적
    last_synced_at  TIMESTAMPTZ,                 -- 마지막 클라이언트 동기화 시각
    sync_checksum   VARCHAR(64),                 -- 변경 감지용 해시
    
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_kg_candidate ON knowledge_graphs(candidate_id);
-- JSONB 내부 노드 타입별 검색
CREATE INDEX idx_kg_nodes_gin ON knowledge_graphs USING GIN (nodes jsonb_path_ops);

-- ============================================================
-- 7. 벡터 임베딩 (pgvector)
-- ===========================

### [사용자] 최종 결과물/수치 질문 (Line 600)

> 우리가 면접으로 최종적으로 얻을수 있는 결과물은 뭐야? 어떤 수치들을 면접을 통해서 얻을수 있어?

### [어시스턴트] 면접 최종 산출물 정의 (Line 603)

좋은 질문입니다. 면접 전체 프로세스를 통해 최종적으로 얻는 결과물과 수치를 정리해보겠습니다.

## 면접 결과물 전체 맵

### 3단계에서 쌓이는 데이터

```
[v5.0 사전 분석]          [Live 면접]              [사후 종합]
코드/이력서/LinkedIn       실시간 대화               AI 통합 분석
정적 데이터               동적 데이터               교차 검증
━━━━━━━━━━━━━━━━━       ━━━━━━━━━━━━━━━━━━      ━━━━━━━━━━━━━━━
        │                       │                       │
        ▼                       ▼                       ▼
   "이 사람이 뭘 했는가"    "이 사람이 뭘 아는가"    "이 사람을 뽑을 것인가"
```

---

### 1단계: v5.0 사전 분석에서 얻는 수치

| 수치 | 설명 | 예시 |
|------|------|------|
| **JD 매칭률** | JD 요구 스킬 vs 지원자 보유 스킬 매칭 비율 | 68% (10개 중 7개 보유, 2개 약함) |
| **코드 품질 점수** | AST + Radon/Lizard 복잡도 + 패턴 분석 | B+ (상위 30%) |
| **AI 코드 비율** | GitHub 코드 중 AI 생성 추정 비율 | 34% |
| **표절 의심도** | Datasketch 기반 코드 유사도 | Low (3%) |
| **기여 진정성** | Git Blame + 커밋 패턴 분석 | 실질 기여자 확인됨 |
| **스킬별 증거 강도** | 코드/이력서/LinkedIn 교차 검증 | Spring: Strong, K8s: Weak, Redis: Indirect |
| **모순점 목록** | 이력서 주장 vs 실제 증거 불일치 | 3건 발견 (1건 심각) |
| **경력 일관성** | LinkedIn + 이력서 경력 교차 검증 | 일치 (경력 4.2년) |

---

### 2단계: Live 면접에서 얻는 수치

| 수치 | 설명 | 예시 |
|------|------|------|
| **역량별 커버리지** | JD 요구 역량 중 면접에서 검증된 비율 | 기술 78%, 소프트스킬 40% |
| **토픽별 검증 상태** | 각 주제가 충분히 다뤄졌는지 | MSA ✓, K8s ✗, 트러블슈팅 ✓ |
| **답변 깊이 지표** | 지원자 답변의 구체성 수준 | 구체적 수치 포함 4회, 모호한 답변 2회 |
| **모순 검증 결과** | 사전 발견 모순점의 면접 중 해소 여부 | 3건 중 1건 해소, 2건 미해소 |
| **실시간 모순 발견** | 면접 중 새로 발견된 모순 | 1건 ("혼자 구축" ↔ "팀 프로젝트") |
| **질문 사용 통계** | Deck vs 실시간 질문 사용량 | Deck 12개, 실시간 6개, 총 18개 |
| **면접 시간 배분** | 주제별 소요 시간 | 기술 25분, 소프트 10분, 오프닝 5분 |
| **발화 비율** | 면접관 vs 지원자 말하기 비율 | 면접관 30%, 지원자 70% (적절) |
| **응답 시간 패턴** | 질문-답변 간 평균 응답 시간 | 평균 2.3초, 기술 질문 시 4.1초 |

---

### 3단계: 사후 종합 분석 (최종 결과물)

여기가 면접관과 채용팀이 실제로 보는 **최종 산출물**입니다.

#### A. 종합 스코어카드

```
┌──────────────────────────────────────────────────────┐
│  종합 점수: ★ 3.8 / 5.0                              │
│  권장 액션: 2차 면접 진행                              │
│  근거: 기술 역량 우수하나 MSA 실무 경험 미검증          │
├──────────────────────────────────────────────────────┤
│                                                      │
│  역량별 점수 (루브릭 기반)                             │
│                                                      │
│  기술 역량          ■■■■□  4.0 / 5.0  (🟢 높은 확신) │
│  문제 해결력        ■■■■□  3.5 / 5.0  (🟢 높은 확신) │
│  커뮤니케이션       ■■■□□  3.0 / 5.0  (🟡 중간 확신) │
│  문화 적합성        ■■■■■  4.5 / 5.0  (🟢 높은 확신) │
│  리더십/협업        ■■■■□  3.5 / 5.0  (🟡 중간 확신) │
│  성장 가능성        ■■■■□  4.0 / 5.0  (🟢 높은 확신) │
│                                                      │
└──────────────────────────────────────────────────────┘
```

| 수치 | 설명 |
|------|------|
| **종합 점수** (1.0-5.0) | 전체 역량 가중 평균 |
| **역량별 점수** (1.0-5.0 × N개) | JD 루브릭에 정의된 역량별 점수 |
| **신뢰도** (🟢/🟡/🔴) | 해당 점수의 증거 충분도 |
| **권장 액션** | HIRE / NEXT_ROUND / REJECT |

#### B. 증거 기반 평가 (수치 + 근거)

```
┌──────────────────────────────────────────────────────┐
│  📊 기술 역량: 4.0 / 5.0                             │
│                                                      │
│  증거 (코드):                                         │
│  • Spring Boot 프로젝트 3개, 커밋 342회               │
│  • 테스트 커버리지 82% (상위 15%)                     │
│  • 코드 복잡도 평균 Cyclomatic 4.2 (양호)             │
│                                                      │
│  증거 (면접):                                         │
│  • Redis 캐싱 설계 질문 — 구체적 수치 포함 답변       │
│  • Cache Invalidation 전략 정확하게 설명              │
│  • 장애 대응 사례 — 근본 원인 분석 접근법 보유        │
│                                                      │
│  미검증:                                              │
│  • K8s 운영 경험 (이력서 기재, 면접 미확인)           │
│  • 대용량 트래픽 최적화 (시간 부족으로 미진행)        │
└──────────────────────────────────────────────────────┘
```

#### C. 위험 신호 리포트

| 수치 | 설명 | 예시 |
|------|------|------|
| **미해소 모순 수** | 면접으로도 해소되지 않은 모순점 | 2건 |
| **모순 심각도** | HIGH/MEDIUM/LOW | 1 HIGH, 1 MEDIUM |
| **미검증 역량 수** | 면접에서 확인하지 못한 JD 요구 역량 | 2개 (K8s, 대용량 트래픽) |
| **AI 코드 이해도** | AI 코드 34% 중 면접에서 이해도 확인 여부 | 확인됨 (코드 설명 가능) |

#### D. 면접 타임라인 데이터 (D3.js 시각화용)

| 수치 | 설명 |
|------|------|
| **분 단위 주제 전환** | 시간 흐름에 따른 대화 주제 변화 그래프 |
| **핵심 순간 마커** | 모순 발견, 강한 답변, 약한 답변 시점 |
| **커버리지 곡선** | 시간에 따른 커버리지 % 변화 (언제 충분해졌는지) |
| **질문 카드 사용 시점** | 어떤 질문이 언제 사용/무시되었는지 |

#### E. 비교 데이터 (같은 JD 지원자 간)

| 수치 | 설명 | 예시 |
|------|------|------|
| **순위** | 같은 포지션 지원자 중 순위 | 3명 중 1위 |
| **역량별 비교** | 같은 역량의 지원자 간 비교 | 기술: 상위, 소프트: 중위 |
| **강점/약점 차별점** | 다른 지원자 대비 뚜렷한 차이 | "유일하게 트러블슈팅 실전 사례 보유" |

---

### 최종 산출물 요약

```
면접 1건 완료 시 생성되는 결과물:

1. 📋 스코어카드
   ├── 종합 점수 (1.0-5.0)
   ├── 권장 액션 (HIRE / NEXT_ROUND / REJECT)
   ├── 역량별 점수 × N개 (각각 신뢰도 포함)
   └── 면접관 승인/수정 이력

2. 📊 수치 지표 (총 20+ 메트릭)
   ├── 사전 분석: JD 매칭률, 코드 품질, AI 비율, 표절도, 모순 수
   ├── 면접 중: 커버리지%, 답변 깊이, 발화 비율, 응답 시간
   └── 사후: 종합 점수, 역량별 점수, 미해소 모순 수, 미검증 역량 수

3. 📝 증거 기반 평가서
   ├── 역량별 (코드 증거 + 면접 증거) 매핑
   ├── 위험 신호 리포트 (모순 + 미검증)
   └── 강점/약점 요약

4. 📈 시각화 데이터 (D3.js)
   ├── 역량 레이더 차트
   ├── 면접 타임라인
   ├── 커버리지 곡선
   ├── 스킬-증거 트리맵
   └── 지원자 비교 차트

5. 📄 전체 트랜스크립트
   ├── 화자 분리된 전문
   ├── 핵심 순간 하이라이트
   └── AI 분석 주석
```

---

이 결과물들이 충분한지, 혹시 빠진 수치나 추가하고 싶은 결과물이 있으신가요? 이 결과물 정의를 확정하면 스코어카드와 리포트 설계를 더 구체화하고, **섹션 7: Phase 로드맵**으로 넘어가겠습니다.

### [어시스턴트] 섹션 7: Phase 로드맵 (Line 613)

## 섹션 7: Phase 로드맵 & Linear 티켓 구조

### 전체 로드맵 개요

```
Phase 0    Phase 1      Phase 2        Phase 3       Phase 4       Phase 5      Phase 6
스캐폴딩 → 도메인 계층 → 인프라-분석 → 인프라-Live → 애플리케이션 → 데스크탑앱 → 웹+통합
 1주       1.5주        2.5주          2주           2주           2.5주        2주
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                                                          총 14주
```

### 의존성 그래프

```
Phase 0 ──▶ Phase 1 ──┬──▶ Phase 2 ──┬──▶ Phase 4 ──▶ Phase 6
                       │              │        │
                       └──▶ Phase 3 ──┘        │
                                               ▼
                                           Phase 5
                                        (Phase 3 완료 후)
```

---

### Phase 0: 프로젝트 스캐폴딩 (1주)

모노레포 구조, Docker, DB, CI 기반을 세운다.

| 티켓 ID | 제목 | 설명 | 예상 |
|---------|------|------|------|
| JTL-1 | 모노레포 초기 구조 생성 | `jittda/` 하위 backend, desktop, frontend, shared, infra 디렉토리 + pyproject.toml + package.json + Makefile | 0.5d |
| JTL-2 | Shared 계층 기반 구조 | shared/ports, shared/models, shared/errors, shared/events, shared/tools 디렉토리 + 빈 __init__.py/index.ts | 0.5d |
| JTL-3 | Docker Compose 기본 구성 | PostgreSQL 16 + pgvector, Redis 7, backend, frontend 서비스 정의. Profile 기반 SonarQube | 0.5d |
| JTL-4 | Fresh init.sql 작성 | 섹션 6 전체 DB 스키마. 확장 모듈, 코어 테이블, 인덱스 포함 | 1d |
| JTL-5 | Infisical 통합 기반 | SecretsManager (Python + Node.js), AppConfig.from_infisical(), .env에 접속 정보 3개만 | 0.5d |
| JTL-6 | Sentry 초기화 기반 | init_sentry() + before_send hook + CorrelationMiddleware + SentryContextMiddleware | 0.5d |
| JTL-7 | 구조화 로깅 설정 | structlog JSON 출력, correlation_id 자동 주입, layer/component 자동 감지 | 0.5d |
| JTL-8 | CI 파이프라인 (GitHub Actions) | lint + type-check + test 기본 파이프라인. backend/desktop/frontend 매트릭스 | 0.5d |

---

### Phase 1: 도메인 계층 (1.5주)

순수 비즈니스 로직. 외부 의존 없음. 모든 Port 인터페이스 정의.

| 티켓 ID | 제목 | 설명 | 예상 |
|---------|------|------|------|
| JTL-10 | 에러 코드 체계 구현 | BaseError, ErrorChainLink, ProblemDetail, 에러 코드 레지스트리 (JA/JL/JR/JS/JC), RFC 9457 직렬화 | 1d |
| JTL-11 | Port 인터페이스 전체 정의 | STTProvider, LLMProvider (Completable/Streamable/ToolCallable/Embeddable), VADEngine, AudioCapturer, VectorStore, GraphStore, GraphQuery | 1d |
| JTL-12 | AdapterRegistry + DI 컨테이너 | Factory + Registry 패턴 구현, LSP 런타임 검증, config YAML 기반 Adapter 해석 | 0.5d |
| JTL-13 | KG 도메인 모델 | KnowledgeGraph 클래스 (add_node, add_edge, find_related, export_json), 노드/엣지 타입 정의 | 1d |
| JTL-14 | Question Deck 도메인 모델 | QuestionCard, TopicGroup, QuestionDeck, Priority, TopicStatus | 0.5d |
| JTL-15 | Interview Session 도메인 모델 | InterviewSession, SessionStatus, TranscriptSegment, InterviewMode | 0.5d |
| JTL-16 | Scorecard + Report 도메인 모델 | Scorecard, CompetencyScore, RedFlag, Recommendation, Report | 0.5d |
| JTL-17 | Graph Tool Set 인터페이스 | get_candidate_overview, get_skill_evidence, find_contradictions, get_jd_coverage, get_unverified_topics, get_code_deep_dive, traverse_context — Port 정의 | 1d |
| JTL-18 | Question Strategy 인터페이스 | QuestionStrategy Protocol + FollowUp, Contradiction, CoverageGap, DeepDive, InterviewerRequest Strategy 스켈레톤 | 0.5d |
| JTL-19 | EventBus 타입 정의 (TypeScript) | TypedEventBus + EventMap (audio:chunk, vad:*, stt:*, llm:*, coverage:*, score:*, interview:*) | 0.5d |
| JTL-20 | Pipeline 프레임워크 | PipelineStage Protocol, Pipeline 체이너, build_realtime_pipeline() 팩토리 | 0.5d |
| JTL-21 | Command 패턴 기반 | InterviewCommand 인터페이스 + CommandDispatcher + 기본 Command들 (RequestFollowUp, EndInterview 등) | 0.5d |

---

### Phase 2: 인프라 — v5.0 분석 (2.5주)

외부 서비스 Adapter + v5.0 분석 Worker + KG 구축 파이프라인.

| 티켓 ID | 제목 | 설명 | 예상 |
|---------|------|------|------|
| JTL-30 | PostgreSQL Repository 구현 | PGCandidateRepo, PGKGRepo, PGSessionRepo, PGDeckRepo — SQLAlchemy AsyncSession | 1d |
| JTL-31 | NetworkX GraphStore Adapter | NetworkX 기반 KG 저장/로드/쿼리, PostgreSQL JSONB import/export | 1d |
| JTL-32 | Graph Tool Set 서버 구현 | NetworkX 기반 7개 그래프 도구 구현 (Python, 서버용) | 1.5d |
| JTL-33 | pgvector 벡터 검색 Adapter | 임베딩 저장/검색, IVFFlat 인덱스, cosine similarity | 0.5d |
| JTL-34 | Kimi K2.5 LLM Adapter | Completable + ToolCallable 구현, Instructor 1.7+ 통합, Langfuse 추적 | 1d |
| JTL-35 | GitHub GraphQL Adapter | 레포 목록, 커밋 이력, Blame 데이터, 파일 트리 수집 | 1d |
| JTL-36 | Tree-sitter AST Adapter | Python 패키지 네이티브 바인딩 0.24+, 다중 언어 파싱 | 1d |
| JTL-37 | BaseWorker Template Method | Load→Execute→Save→Ref 패턴, KG 자동 주입, 에러 래핑 | 0.5d |
| JTL-38 | Identity Resolution Worker | GitHub Node ID + 동적 .mailmap + 3단계 포렌식 | 1d |
| JTL-39 | Resume/LinkedIn/CoverLetter Worker | 파싱 + Claim/Skill 노드 KG 주입 + SOURCED_FROM 엣지 | 1.5d |
| JTL-40 | Git Blame + AST Worker | 커밋 패턴 분석 + 코드 구조 분석 + Evidence 노드 주입 | 1.5d |
| JTL-41 | CrossRef Worker | 교차 검증 — SUPPORTS/CONTRADICTS 엣지 생성, LLM 도구 호출 | 1d |
| JTL-42 | JD Match + Scoring Worker | JDRequirement 매칭 + MATCHES 엣지 + 4대 지표 산출 | 1d |

---

### Phase 3: 인프라 — Live 면접 (2주)

오디오, STT, 실시간 LLM, 로컬 DB Adapter.

| 티켓 ID | 제목 | 설명 | 예상 |
|---------|------|------|------|
| JTL-50 | macOS 네이티브 오디오 캡처 모듈 | ScreenCaptureKit/CoreAudio 기반 Swift 바이너리, PCM Stereo 출력, Electron Child Process 연동 | 2d |
| JTL-51 | AudioCapturer Adapter (macOS) | Port 구현, Main Process에서 Child Process 생명주기 관리, IPC 스트림 전달 | 1d |
| JTL-52 | Silero VAD WASM Adapter | @ricky0123/vad 기반 Renderer 내 VAD, speech-start/speech-end 이벤트 발생, 무음 1.5s 임계값 | 1d |
| JTL-53 | Deepgram STT Adapter | Nova-3 WebSocket 스트리밍, 한/영 지원, 채널 기반 화자 분리 (온라인), AI Diarization (오프라인) | 1.5d |
| JTL-54 | Groq LLM Adapter | Llama 3.3 70B, Streamable + ToolCallable 구현, TTFT 최적화 | 1d |
| JTL-55 | LanceDB 로컬 Adapter | v0.26 In-process 벡터 검색, 테이블 생성/쿼리, 서버 데이터 import | 1d |
| JTL-56 | graphology Graph Adapter | In-memory 그래프 import(JSON), 노드/엣지 탐색, 7개 그래프 도구 클라이언트 구현 | 1d |
| JTL-57 | Live 에러 복구 모듈 | LiveErrorRecovery — 심각도별 복구 전략, 폴백 모드 전환, 긴급 데이터 보존 | 1d |

---

### Phase 4: 애플리케이션 계층 (2주)

LangGraph 그래프 조립, Deck 생성, API/WebSocket 엔드포인트.

| 티켓 ID | 제목 | 설명 | 예상 |
|---------|------|------|------|
| JTL-60 | LangGraph MetaAgent 그래프 | 3-tier HMAS (Forensic/Logic/Stack Supervisor), Worker 연결, StateGraph 정의 | 1.5d |
| JTL-61 | DeckGenerator 서비스 | 분석 완료 후 KG 기반 Question Deck 생성, 주제별 2-3 질문 + Red Flags + Ice Breakers | 1.5d |
| JTL-62 | 실시간 분석 파이프라인 | RealTimeAnalyzer — 발화 vs Deck 매칭, 트리거 조건 체크 (모순/예상외/꼬리), 조건부 LLM 호출 | 1.5d |
| JTL-63 | PostInterview 분석 파이프라인 | 데이터 수집 → KG 확장 → 역량 평가 → 스코어카드 생성 → 리포트 조립 | 1.5d |
| JTL-64 | REST API 엔드포인트 | candidates, analysis, decks, interviews, reports, sync — CQS 핸들러 연결 | 1d |
| JTL-65 | WebSocket 엔드포인트 | live_interview WS — transcript.segment, card.used, card.dismissed, coverage.updated, report.ready | 1d |
| JTL-66 | 클라이언트 동기화 API | GET /sync/{id}/bundle (KG + Deck + Embeddings), POST /sync/{id}/upload (트랜스크립트 + 카드 이력) | 1d |

---

### Phase 5: 데스크탑 앱 — Electron (2.5주)

Electron 셸, 오디오 파이프라인, 면접관 대시보드 UI.

| 티켓 ID | 제목 | 설명 | 예상 |
|---------|------|------|------|
| JTL-70 | Electron 앱 셸 | Electron v33+ 초기화, Main/Renderer 프로세스 구조, Vite + React 빌드 설정 | 1d |
| JTL-71 | Sentry + Infisical 데스크탑 통합 | @sentry/electron 초기화, Infisical Node.js SDK, 시크릿 로드 | 0.5d |
| JTL-72 | 오디오 파이프라인 통합 | Child Process(오디오) → Main(관리) → Renderer(VAD) 연결, IPC 스트림, 온라인/오프라인 모드 분기 | 1.5d |
| JTL-73 | STT + RAG + LLM 파이프라인 통합 | VAD → STT → Hybrid RAG (LanceDB + graphology) → Groq 질문 생성, Pipeline 패턴으로 조립 | 1.5d |
| JTL-74 | 동기화 서비스 | 면접 시작 전 번들 다운로드 (KG → graphology, Embeddings → LanceDB, Deck → 로컬), 종료 후 업로드 | 1d |
| JTL-75 | 대기 화면 (Pre-Interview) | 지원자 목록, v5.0 분석 요약, 면접 모드 선택, 면접 시작 버튼 | 1d |
| JTL-76 | 라이브 대시보드 — Zone A 상태바 | 경과 시간, 오디오 상태, 종료 가능 표시 (커버리지 기반 색상) | 0.5d |
| JTL-77 | 라이브 대시보드 — Zone B 질문 카드 | Layer 1 (Deck 주제별 접이식) + Layer 2 (실시간 최상단), 카드 사용/무시/재생성, 우선순위 색상 | 1.5d |
| JTL-78 | 라이브 대시보드 — Zone C 커버리지 | 커버리지 프로그레스 바 (기술/소프트), 토픽 체크리스트 탭→질문 생성, 질문 요청 버튼 + 프리셋 | 1d |
| JTL-79 | 면접 종료 화면 (Post-Interview) | 스코어카드 요약 표시, 수정/승인 기능, "웹에서 상세 보기" 링크 | 1d |
| JTL-80 | 다크/라이트 테마 + Always on Top | 테마 토글, 420×900 기본 크기, 드래그 이동, Always on Top 토글 | 0.5d |

---

### Phase 6: 웹 프론트엔드 + 통합 테스트 (2주)

웹 리포트 뷰어, D3.js 시각화, E2E 테스트.

| 티켓 ID | 제목 | 설명 | 예상 |
|---------|------|------|------|
| JTL-90 | 웹 지원자 관리 페이지 | 지원자 목록, 상태별 필터, JD 매핑, 분석 시작 트리거 | 1d |
| JTL-91 | 웹 리포트 뷰어 — 스코어카드 탭 | 종합 점수, 역량별 점수+근거, 위험 신호, 권장 액션 | 1d |
| JTL-92 | D3.js 역량 레이더 차트 | 역량별 점수 레이더, 인터랙티브 드릴다운 | 1d |
| JTL-93 | D3.js 면접 타임라인 | 시간별 주제 전환, 핵심 순간 마커, 커버리지 곡선 오버레이 | 1d |
| JTL-94 | D3.js 스킬 증거 트리맵 | 스킬별 증거 매핑, 코드/이력서/면접 소스별 색상 | 1d |
| JTL-95 | 지원자 비교 뷰 | 같은 JD 지원자 간 역량 비교 차트, 순위 테이블 | 1d |
| JTL-96 | 단위 테스트 (Domain + Application) | 도메인 모델, KG 조작, Deck 생성, 스코어카드 산출 로직 테스트 | 1d |
| JTL-97 | 통합 테스트 (API + WebSocket) | REST 엔드포인트 + WS 이벤트 흐름, 동기화 번들 검증 | 1d |
| JTL-98 | E2E 테스트 (Playwright) | 웹: 분석 시작 → 결과 확인 흐름, 데스크탑: 면접 시작 → 종료 시뮬레이션 | 1.5d |
| JTL-99 | 성능 벤치마크 | Hybrid RAG <100ms, LLM TTFT <200ms, 동기화 번들 <5s, KG 쿼리 <5ms 검증 | 0.5d |

---

### 전체 티켓 요약

| Phase | 티켓 수 | 기간 | 핵심 산출물 |
|-------|--------|------|------------|
| 0. 스캐폴딩 | 8개 (JTL-1~8) | 1주 | 모노레포, Docker, DB, Sentry, Infisical |
| 1. 도메인 | 12개 (JTL-10~21) | 1.5주 | Port, 에러 체계, 도메인 모델, EventBus |
| 2. 인프라-분석 | 13개 (JTL-30~42) | 2.5주 | v5.0 Worker, KG 구축, Graph Tool |
| 3. 인프라-Live | 8개 (JTL-50~57) | 2주 | 오디오, STT, VAD, 로컬 DB |
| 4. 애플리케이션 | 7개 (JTL-60~66) | 2주 | HMAS, Deck 생성, API, WebSocket |
| 5. 데스크탑 | 11개 (JTL-70~80) | 2.5주 | Electron 앱, 대시보드 UI |
| 6. 웹+통합 | 10개 (JTL-90~99) | 2주 | 리포트 뷰어, D3.js, 테스트 |
| **합계** | **69개** | **14주** | |

---

### 마일스톤 체크포인트

```
Week 1  ▶ M0: 프로젝트 빌드/실행 가능 (Docker 기동, DB 접속)
Week 2.5 ▶ M1: 모든 Port 정의 완료, 에러 체계 작동
Week 5  ▶ M2: v5.0 분석 → KG 구축 → Deck 생성 E2E 작동
Week 7  ▶ M3: macOS 오디오 캡처 → STT 텍스트 변환 작동
Week 9  ▶ M4: 전체 파이프라인 연결 (분석 → Deck → Live → 스코어카드)
Week 11.5 ▶ M5: 데스크탑 앱으로 면접 진행 가능 (MVP)
Week 14 ▶ M6: 웹 리포트 + 테스트 완료 (출시 가능)
```

---

이것이 설계 문서의 마지막 섹션입니다. 전체 설계에 대해 수정하거나 추가할 부분이 있으신가요? 괜찮으시면 전체 설계 문서를 `docs/plans/2026-02-17-jittda-live-design.md`에 작성하고, 이후 writing-plans 스킬로 구현 계획을 세우겠습니다.

---
## Phase 5: 문서 작성 및 Linear 프로젝트 구성

### [사용자] 산출물 요청 (Line 620)

> 시작전에 논의한 전체적인 설계도 파일로 남기고, 최소요구사항적의서 작성과 와이어프레임 작성(penceil mcp로) 각각의 페이지들을 작성하고 (페이지별 구체적으로 이슈 만들어서 작성) 해줘 , 그리고 추후 결제를 넣을수도 있고 프로모 코드같은걸로 몇회 무료사용 이런거 추가할수 잇도록 하면 좋을것같아 결제는 추후 할건데 추가하기 쉽도록 미리 준비하면 좋을것같고 프로모 코드는 지금 설계부터 들어가면 좋을것같아 생성과 기한 몇번 무료로 사용가능한지, 등

### [어시스턴트] 프로모 코드 + 결제 설계 (Line 644)

먼저 프로모 코드 + 결제 준비 설계를 추가한 후, 전체를 파일로 작성하겠습니다.

Pencil MCP는 현재 연결된 MCP 서버에 없습니다. 와이어프레임은 **상세 ASCII + 컴포넌트 명세**로 작성하고, 필요하면 추후 Magic MCP로 실제 React 컴포넌트를 생성하는 방식으로 진행하겠습니다.

---

## 섹션 8: 프로모 코드 + 결제 준비 설계

### 1. 사용량/크레딧 기반 모델 설계

```
┌─────────────────────────────────────────────────────┐
│                Usage & Billing Layer                 │
│                                                     │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ PromoCode     │  │ UsageCredit  │  │ Payment  │ │
│  │ System        │  │ System       │  │ System   │ │
│  │ (지금 구현)    │  │ (지금 구현)   │  │ (추후)   │ │
│  └───────┬───────┘  └──────┬───────┘  └────┬─────┘ │
│          │                 │               │       │
│          └─────────────────┴───────────────┘       │
│                        │                           │
│              BillingPort (인터페이스)                │
│                        │                           │
│          ┌─────────────┴─────────────┐             │
│          ▼                           ▼             │
│   FreeTierAdapter              StripeAdapter       │
│   (지금 — 프로모 코드만)       (추후 — 결제 연동)    │
└─────────────────────────────────────────────────────┘
```

### 2. 프로모 코드 시스템

#### 도메인 모델

```python
# domain/models/billing.py

class PromoCode:
    id: UUID
    code: str                      # "JITTDA-BETA-2026" (대소문자 무시)
    
    # 혜택
    credit_type: CreditType        # ANALYSIS | INTERVIEW | BOTH
    credits_granted: int           # 부여 크레딧 수 (예: 면접 5회)
    
    # 제한
    max_redemptions: int | None    # 전체 최대 사용 횟수 (None=무제한)
    max_per_user: int              # 유저당 최대 사용 횟수 (기본 1)
    
    # 기한
    valid_from: datetime
    valid_until: datetime | None   # None=무기한
    
    # 상태
    is_active: bool
    current_redemptions: int       # 현재 사용 횟수
    
    # 메타
    description: str               # 관리자 메모
    created_by: str                # 생성자
    created_at: datetime


class CreditType(Enum):
    ANALYSIS = "analysis"          # v5.0 분석 크레딧
    INTERVIEW = "interview"        # Live 면접 크레딧
    BOTH = "both"                  # 분석 + 면접 모두


class UserCredit:
    id: UUID
    user_id: UUID
    
    # 잔여 크레딧
    analysis_credits: int          # 남은 분석 횟수
    interview_credits: int         # 남은 면접 횟수
    
    # 이력
    total_analysis_used: int
    total_interviews_used: int
    
    # 구독 (추후)
    subscription_tier: str | None  # None | "pro" | "enterprise"
    subscription_ref: str | None   # 결제 시스템 참조 ID
    
    updated_at: datetime


class CreditTransaction:
    id: UUID
    user_id: UUID
    
    # 트랜잭션 정보
    type: TransactionType          # PROMO_REDEEM | USAGE | PURCHASE | REFUND | ADMIN_GRANT
    credit_type: CreditType
    amount: int                    # +5 (충전) or -1 (사용)
    
    # 참조
    promo_code_id: UUID | None     # 프로모 사용 시
    session_id: UUID | None        # 면접 사용 시
    job_id: UUID | None            # 분석 사용 시
    payment_ref: str | None        # 결제 시 (추후)
    
    # 잔액 스냅샷
    balance_after: int
    
    created_at: datetime
```

#### DB 스키마

```sql
-- ============================================================
-- 프로모 코드
-- ============================================================
CREATE TABLE promo_codes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code                VARCHAR(50) NOT NULL UNIQUE,
    
    credit_type         VARCHAR(15) NOT NULL DEFAULT 'both',
    credits_granted     INT NOT NULL,
    
    max_redemptions     INT,                    -- NULL = 무제한
    max_per_user        INT NOT NULL DEFAULT 1,
    
    valid_from          TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_until         TIMESTAMPTZ,            -- NULL = 무기한
    
    is_active           BOOLEAN NOT NULL DEFAULT true,
    current_redemptions INT NOT NULL DEFAULT 0,
    
    description         TEXT,
    created_by          VARCHAR(100),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_promo_code_upper ON promo_codes(UPPER(code));

-- ============================================================
-- 사용자 크레딧
-- ============================================================
CREATE TABLE user_credits (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL UNIQUE,
    
    analysis_credits        INT NOT NULL DEFAULT 0,
    interview_credits       INT NOT NULL DEFAULT 0,
    
    total_analysis_used     INT NOT NULL DEFAULT 0,
    total_interviews_used   INT NOT NULL DEFAULT 0,
    
    -- 추후 결제 연동용
    subscription_tier       VARCHAR(20),
    subscription_ref        VARCHAR(200),
    
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- 크레딧 트랜잭션 (감사 로그 겸용)
-- ============================================================
CREATE TABLE credit_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    
    type            VARCHAR(2

### [어시스턴트] 설계 산출물 완료 (Line 878)

모든 산출물이 완성되었습니다. 최종 결과를 정리합니다.

---

## Jittda Live — 설계 산출물 완료 현황

### 생성된 파일

| 파일 | 내용 |
|------|------|
| `docs/plans/2026-02-17-jittda-live-design.md` | 전체 시스템 설계서 (13개 섹션) |
| `docs/plans/2026-02-17-jittda-live-mvp-prd.md` | MVP 최소 요구사항 정의서 (P0 14개 기능) |
| `docs/plans/2026-02-17-jittda-live-wireframes.md` | 페이지별 와이어프레임 (13개 페이지) |

### Linear 프로젝트 & 이슈

**프로젝트**: [Jittda Live](https://linear.app/jittda) (ID: `be788790-...`)

**데스크탑 (7개)**:
| 이슈 | 페이지 | 우선순위 |
|------|--------|---------|
| JIT-128 | [WF-D1] 로그인 | High |
| JIT-129 | [WF-D2] 지원자 목록 | High |
| JIT-130 | [WF-D3] 면접 대기 | Urgent |
| JIT-131 | [WF-D4] 라이브 대시보드 (핵심) | Urgent |
| JIT-132 | [WF-D5] 면접 종료/스코어카드 | High |
| JIT-133 | [WF-D6] 설정 | Medium |
| JIT-134 | [WF-D7] 크레딧 & 프로모 | Medium |

**웹 (6개)**:
| 이슈 | 페이지 | 우선순위 |
|------|--------|---------|
| JIT-135 | [WF-W1] 대시보드 (홈) | High |
| JIT-136 | [WF-W2] 지원자 관리 | High |
| JIT-137 | [WF-W3] 지원자 상세 | High |
| JIT-138 | [WF-W4] 면접 리포트 | High |
| JIT-139 | [WF-W5] 지원자 비교 | Medium |
| JIT-140 | [WF-W6] 설정 & 빌링 | Medium |

### 다음 단계

brainstorming 스킬 워크플로우에 따라 **writing-plans 스킬을 호출**하여 구현 계획을 작성할 차례입니다. 진행할까요?

### [사용자] Linear 이슈 상세화 요청 (Line 973)

> 리니어 이슈 생성및 프로젝트 생성한게 너무 간략하게 작성되어있어 프로젝트 세부적으로 상세내용및 계획 세우고 각각의 마일스톤 생성하고 이슈도 세부적으로 다 작성해줘 테스트 방법도 각각의 이슈및 마일스톤은 어디가 어디로 연결되어있는지 명시해서 구현중에 뭐가 바뀔때 뒤에 어떻게 영향이 가는지, 이전에 어떻게 바뀌어서 어떻게 바꿔야하는지 잘 알수 있도록 상세하게 작성해줘 기존에 작성된것들 모두 정리하고(참고해야하면 작업이 다끝나면 정리)

### [어시스턴트] 69개 이슈 생성 완료 (Line 1444)

**69개 이슈 모두 생성 완료!** (JIT-141 ~ JIT-209)

이제 이슈 간 의존성(blocks/blockedBy) 관계를 설정하고, 기존 간략 이슈(JIT-128~140)를 취소하겠습니다.

### [어시스턴트] Linear 프로젝트 최종 현황 (Line 1544)

## Jittda Live Linear 프로젝트 재구성 완료

### 생성 결과 요약

| Phase | 기간 | 이슈 범위 | 티켓 수 |
|-------|------|-----------|---------|
| **Phase 0** | Week 1 | JIT-141 ~ JIT-148 | 8개 |
| **Phase 1** | Week 2-3 | JIT-149 ~ JIT-158 | 10개 |
| **Phase 2** | Week 4-5 | JIT-159 ~ JIT-166 | 8개 |
| **Phase 3** | Week 6-8 | JIT-167 ~ JIT-178 | 12개 |
| **Phase 4** | Week 9-10 | JIT-179 ~ JIT-188 | 10개 |
| **Phase 5** | Week 11-12 | JIT-189 ~ JIT-199 | 11개 |
| **Phase 6** | Week 13-14 | JIT-200 ~ JIT-209 | 10개 |
| **합계** | **14주** | **JIT-141 ~ JIT-209** | **69개** |

### 완료 항목
- **69개 상세 이슈 생성**: 각 이슈에 개요, 기술 스펙, 수용 기준, 의존성, PRD 참조 포함
- **99개 의존성 관계 설정**: blocks/blockedBy로 이슈 간 영향 경로 명시
- **7개 마일스톤 연결**: Phase 0~6 각각 projectMilestoneId 배정
- **7개 Phase 라벨 배정**: 색상 코딩된 라벨로 Phase 구분
- **기존 간략 이슈 정리**: JIT-128~140 (13개) 모두 Cancelled 처리
