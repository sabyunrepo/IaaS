---
title: "ADR-0009: Jittda Live 데스크톱 프레임워크"
type: adr
status: proposed
date: 2026-02-19
decision-makers: ["@sabyun"]
related-adrs: []
impacts: ["[[interface/electron-app/MOC]]"]
tags: [electron, tauri, desktop, live]
---

# ADR-0009: Jittda Live 데스크톱 프레임워크

## 상태

proposed

---

## 컨텍스트

Jittda Live는 면접관이 사용하는 실시간 AI 면접 가이드 데스크톱 앱이다.
핵심 기능:

- **OS 네이티브 오디오 캡처**: 서드파티 드라이버 없이 마이크 + 시스템 사운드 캡처
  - macOS: ScreenCaptureKit / CoreAudio
  - Windows: WASAPI 루프백
- **VAD (Voice Activity Detection)**: Silero WebAssembly 실행
- **로컬 벡터 DB**: LanceDB 인프로세스(In-process) 실행
- **IPC**: Main Process ↔ Renderer 간 오디오 스트림 + 이벤트 전달
- **UI**: React 기반 면접관 어시스턴트 대시보드

### 기술적 제약 조건

`jittda_doc/jittda_live_brainstorm_curated.md` 초기 설계에서 확인된 아키텍처:

```
[ Child Process (Native Audio Module) ]  ← macOS/Windows 네이티브 바이너리
  │  PCM 스테레오 스트림
  ▼
[ Electron Main Process (Node.js) ]
  │  IPC
  ▼
[ Renderer Process ]
  ├─ VAD (Silero WASM, <1ms)
  ├─ STT Client
  ├─ LanceDB (In-process)
  └─ Groq LLM API
```

`docs/plans/2026-02-19-architecture-documentation-design.md` §6.1에서:
- v5 설계서 채택: Electron v33
- 최종 결정: **Electron v33 / Tauri 2.x (ADR 결정)**
- 변경 사유: Tauri 96% 번들 감소

`jittda_doc/jittda_reveiw.md`에서 Electron vs Tauri 비교:

| 항목 | Electron v33 | Tauri 2.x |
|------|-------------|-----------|
| 번들 크기 | 100MB+ | 2-10MB |
| 메모리 사용 | 200-400MB | 30-40MB |
| 내장 런타임 | Chromium + Node.js | 네이티브 WebView + Rust |
| 보안 | 상대적으로 취약 | Rust 기반 강화 |
| 생태계 성숙도 | 매우 성숙 | 빠르게 성장 중 |
| 네이티브 통합 | Node.js 네이티브 모듈 | Rust Tauri 플러그인 |
| `electron-audio-loopback` 등 | 기존 라이브러리 다수 | 별도 플러그인 개발 필요 |

---

## 검토한 옵션

### 옵션 A: Electron v33 (선택)

**설명**: 현재 가장 널리 사용되는 데스크톱 앱 프레임워크.
Chromium + Node.js 번들 포함.

**장점**:
- VS Code, Slack, Discord 등 대규모 프로덕션 검증
- OS 네이티브 오디오 캡처 라이브러리(`electron-audio-loopback`, `naudiodon`) 다수 존재
- Node.js 생태계 직접 활용 — LanceDB Node.js 바인딩, faster-whisper Node.js 래퍼
- React 19 UI 그대로 사용 (Chromium 내장)
- Child Process 기반 네이티브 바이너리 실행 패턴 검증됨
- 빠른 MVP 개발 가능 — 기존 웹 개발자 지식 재사용
- macOS ScreenCaptureKit / Windows WASAPI 통합 예시 레퍼런스 풍부

**단점**:
- 번들 크기 100MB+: 설치 경험 저하
- 메모리 사용 200-400MB: LanceDB + 로컬 Whisper 동시 실행 시 경합 우려
- Chromium 내장 → 불필요한 리소스 사용 (WebRTC, V8 GC 등)
- 보안 모델이 Tauri 대비 약함 (Node.js 전체 접근 허용)

---

### 옵션 B: Tauri 2.x

**설명**: Rust 기반 데스크톱 앱 프레임워크.
OS 네이티브 WebView(macOS: WKWebView, Windows: WebView2) 사용.

**장점**:
- 번들 크기 2-10MB (Electron 대비 ~96% 감소)
- 메모리 사용 30-40MB
- Rust 기반 → 메모리 안전성 + 성능
- OS 네이티브 WebView → Chromium 불필요
- 보안 모델 우수 (Capability 기반 API 허용)

**단점**:
- Node.js 생태계 미사용 → LanceDB, 오디오 라이브러리를 Rust 플러그인으로 구현 필요
- OS 네이티브 오디오 캡처(ScreenCaptureKit/WASAPI) Tauri 플러그인 미성숙
- macOS WebView 버전 간 렌더링 차이 — React UI 호환성 검증 필요
- 팀 내 Rust 경험 필요
- 2026.02 기준 MVP 단계에서 기술 위험 높음
- `jittda_doc/jittda_reveiw.md` 제안: "단계적 마이그레이션 권장"

---

## 결정

**Electron v33으로 시작, Tauri 2.x 마이그레이션 로드맵 유지**

구체적 접근:

1. **Phase 1 (MVP)**: Electron v33으로 개발
   - Child Process 기반 OS 네이티브 오디오 캡처
   - React 19 + Tailwind 4 대시보드 UI
   - LanceDB Node.js 바인딩 인프로세스 실행
   - Groq API 통합 (STT + LLM)

2. **Phase 2 (안정화 후 검토)**: Tauri 2.x 마이그레이션 평가
   - Jittda Live MVP 기능 안정화 이후
   - Tauri 플러그인 생태계 성숙도 재평가
   - 번들 크기 / 메모리 개선 필요성 사용자 피드백 기반 판단

이 결정의 근거:
- MVP 우선 원칙: 기술 위험보다 빠른 검증이 중요
- `jittda_doc/jittda_reveiw.md`에서 명시된 "Electron의 electron-audio-loopback 같은
  특정 라이브러리 의존성이 있다면 단계적 마이그레이션을 권장"
- OS 네이티브 오디오 캡처는 Jittda Live의 핵심 MVP 기능 — 이 부분의 기술 리스크를 최소화해야 함
- `docs/plans/2026-02-19-architecture-documentation-design.md`에서도
  `interface/electron-app/tauri-migration.md` 문서를 별도로 계획 — Tauri 전환이 후속 로드맵임을 명시

---

## 결과

### 초기 Electron 아키텍처

```
Electron Main Process (Node.js)
├─ Child Process: OS Audio Capture
│   ├─ macOS: ScreenCaptureKit Swift 바이너리
│   └─ Windows: WASAPI C++ 바이너리
│       → PCM 스테레오 스트림 출력
├─ IPC Bridge (ipcMain/ipcRenderer)
└─ BrowserWindow (Renderer Process)
    ├─ React 19 + Tailwind 4 (UI)
    ├─ Silero VAD (WASM, <1ms)
    ├─ LanceDB Node.js (In-process)
    └─ Groq API Client (STT + LLM)
```

### 디렉토리 구조

```
desktop/
├── src/
│   ├── main/           # Electron Main Process
│   │   ├── index.ts    # 앱 진입점
│   │   ├── audio.ts    # Child Process 관리
│   │   └── ipc.ts      # IPC 핸들러
│   ├── renderer/       # Renderer Process (React)
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── TopicCoverage.tsx    # 토픽 커버리지 바
│   │   │   ├── ProbingCards.tsx     # 동적 질문 카드
│   │   │   └── Scorecard.tsx        # 자동화 스코어카드
│   │   ├── hooks/
│   │   │   ├── useVAD.ts            # Silero VAD
│   │   │   ├── useSTT.ts            # Groq Whisper / faster-whisper
│   │   │   └── useLanceDB.ts        # 로컬 벡터 검색
│   │   └── store/
│   │       └── liveStore.ts         # Pub/Sub 이벤트 버스
│   └── native/         # C++/Swift 네이티브 오디오 모듈
│       ├── macos/      # ScreenCaptureKit
│       └── windows/    # WASAPI 루프백
├── package.json
└── electron-builder.yml
```

### Tauri 마이그레이션 전제 조건 (체크리스트)

Tauri 전환을 검토할 때 다음이 충족되어야 한다:

- [ ] Tauri 공식 오디오 캡처 플러그인 안정화 (macOS ScreenCaptureKit + Windows WASAPI)
- [ ] LanceDB Rust 바인딩 안정화 (`lancedb` crate)
- [ ] 팀 내 Rust 역량 확보 (Tauri 플러그인 개발 가능 수준)
- [ ] Electron MVP 사용자 테스트 완료 후 번들 크기 개선 필요성 확인

### 적용 대상 Linear 티켓

- Jittda Live 데스크탑 앱 개발 전 범위

### 참조

- `jittda_doc/jittda_live_brainstorm_curated.md` — Electron 아키텍처 상세 설계
- `jittda_doc/jittda_reveiw.md` — Electron vs Tauri 비교, 단계적 마이그레이션 권장
- `docs/plans/2026-02-19-architecture-documentation-design.md` §5.3, §6.1
- `[[interface/electron-app/architecture]]`
- `[[interface/electron-app/audio-capture]]`
- `[[interface/electron-app/tauri-migration]]`
