---
title: "ADR-0008: Jittda Live STT 한국어 지원"
type: adr
status: proposed
date: 2026-02-19
decision-makers: ["@sabyun"]
related-adrs: []
impacts: ["[[infrastructure/voice-pipeline/MOC]]", "[[application/live-session/MOC]]"]
tags: [stt, korean, whisper, deepgram]
---

# ADR-0008: Jittda Live STT 한국어 지원

## 상태

proposed

---

## 컨텍스트

Jittda Live는 실시간 면접 가이드 데스크톱 앱이다.
면접 오디오(마이크 + 시스템 사운드)를 실시간으로 STT(Speech-to-Text) 처리하여
면접관 어시스턴트 대시보드에 텍스트와 AI 질문 카드를 제공한다.

한국 채용 시장을 1차 타겟으로 하므로 **한국어 인식 정확도**가 핵심 요구사항이다.

### STT 파이프라인 구조

```
오디오 캡처 (OS Native)
  → VAD (Silero WASM, 1ms 이하)
  → STT 엔진
  → 텍스트
  → LanceDB 로컬 검색 (20ms)
  → Groq API 꼬리 질문 생성 (~0.8s)
```

전체 파이프라인 레이턴시 목표: **0.8~1.0초** 이내.
STT 단계에 허용되는 레이턴시: **~300ms** 이내.

### 초기 설계 선택: Deepgram Nova-3

`jittda_doc/jittda_live_brainstorm_curated.md` STT 리서치 결과 및
`jittda_doc/jittda_reveiw.md`의 시스템 아키텍처 검토에서
초기 후보로 Deepgram Nova-3가 언급되었다:

| 항목 | Deepgram Nova-3 |
|------|-----------------|
| 실시간 스트리밍 | WebSocket |
| 레이턴시 | <300ms |
| 화자 분리 | 내장 |
| 가격 | $0.0077/분 |

그러나 `docs/plans/2026-02-19-architecture-documentation-design.md` §6.1에서
핵심 문제가 확인되었다:

> **STT: Deepgram Nova-3 → Whisper large-v3 (한국어 미지원)**

Deepgram Nova-3는 2026년 2월 기준 **한국어를 정식 지원하지 않는다**.
`jittda_doc/jittda_live_brainstorm_curated.md` STT 비교표에서도
"Reddit 커뮤니티 피드백: Deepgram/AssemblyAI는 영어에선 훌륭하지만
아시아 언어 정확도와 구두점은 크게 떨어진다"가 확인되었다.

### 추가 검토된 STT 서비스 (리서치 결과)

| 서비스 | 한국어 | 레이턴시 | 실시간 | 화자분리 |
|--------|--------|----------|--------|----------|
| Deepgram Nova-3 | 미지원 | <300ms | WebSocket | 내장 |
| ElevenLabs Scribe v2 RT | 미확인 | ~150ms | WebSocket | 미확인 |
| AssemblyAI Universal | 제한적 | ~300ms | WebSocket | 내장 |
| Soniox | 60+언어 | 미공개 | WebSocket | 실시간 |
| OpenAI Whisper large-v3 | 지원 | 모델 의존 | 배치/스트림 | 별도 |

---

## 검토한 옵션

### 옵션 A: Deepgram Nova-3 유지 (영어 전용)

**설명**: 한국어 지원을 포기하고 Deepgram을 유지하거나,
서비스가 한국어를 지원할 때까지 대기한다.

**장점**:
- WebSocket 기반 실시간 스트리밍 API가 완성도 높음
- <300ms 저지연
- 내장 화자 분리

**단점**:
- 한국어 WER(단어 오류율)이 높아 면접 컨텍스트 분석 품질 저하
- 한국어 구두점/어미 처리 미흡 — 텍스트 기반 RAG 검색 품질에 직접 영향
- 1차 타겟인 한국 시장에서 사실상 사용 불가

**결론**: 채택 불가.

---

### 옵션 B: OpenAI Whisper large-v3 (로컬 또는 API)

**설명**: OpenAI의 Whisper large-v3 모델을 로컬 서버 또는
OpenAI API로 실행하여 한국어 STT를 처리한다.

**장점**:
- 한국어를 포함한 99개 언어 지원
- large-v3 기준 한국어 WER 5~8% (고정밀)
- 오픈소스 — 로컬 self-hosted 가능 (데이터 보안)
- faster-whisper 등 최적화 구현체로 속도 개선 가능

**단점**:
- 실시간 스트리밍: 배치 처리 기반이라 VAD와 조합 필요
- large-v3 로컬 실행: GPU 없으면 지연 증가 (CPU: ~2-5초/발화)
- OpenAI API 사용 시: 네트워크 레이턴시 추가 (~200-500ms)

---

### 옵션 C: Groq Whisper (Groq 가속 추론) — 선택

**설명**: Groq의 LPU(Language Processing Unit)를 활용한 Whisper 추론.
이미 Dynamic Probing(Layer 2)에서 Groq API를 사용하므로 인프라 통합이 자연스럽다.

**장점**:
- Whisper large-v3와 동일한 한국어 정확도 (같은 모델 가중치)
- Groq LPU 가속으로 ~300ms 이하 응답 (Whisper 대비 ~5-10x 빠름)
- 별도 GPU 인프라 불필요
- 이미 사용 중인 Groq API 통합 — 단일 인증/청구
- `jittda_doc/jittda_reveiw.md`에서 확인: Groq TTFT 0.14s (메인 LLM)

**단점**:
- Groq API 의존성 — 장애 시 STT + 질문 생성 동시 불가
- Groq Whisper는 스트리밍 방식이 아닌 발화 단위 배치 — VAD 필수
- API 비용 (vs 로컬 Whisper)

---

## 결정

**옵션 B + 옵션 C 병행 채택: Whisper large-v3 기본 + Groq Whisper 가속 옵션**

구체적인 전략:
1. **기본(Fallback)**: `faster-whisper`(CTranslate2 최적화) 로컬 실행 — 인터넷 불안정 시에도 동작
2. **권장(Primary)**: Groq Whisper API — 정확도 동일 + 저지연 + 인프라 단순화
3. **전환 조건**: Groq API 장애 감지 시 로컬 faster-whisper로 자동 fallback

이 결정의 근거:
- Jittda Live의 1차 타겟은 한국 시장이므로 한국어 지원은 비협상 요소
- Groq Whisper는 기존 Groq API 인프라 재사용 — 운영 복잡도 최소화
- faster-whisper 로컬 실행은 서버가 없거나 오프라인 면접 환경의 안전망

---

## 결과

### STT 제공자 추상화 레이어

```python
# infrastructure/voice_pipeline/stt_provider.py
from abc import ABC, abstractmethod

class STTProvider(ABC):
    @abstractmethod
    async def transcribe_chunk(
        self, audio_chunk: bytes, language: str = "ko"
    ) -> str: ...

class GroqWhisperProvider(STTProvider):
    """Primary: Groq Whisper large-v3 가속 추론"""
    async def transcribe_chunk(self, audio_chunk: bytes, language: str = "ko") -> str:
        response = await groq_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=("audio.wav", audio_chunk, "audio/wav"),
            language=language,
            response_format="text",
        )
        return response

class LocalWhisperProvider(STTProvider):
    """Fallback: faster-whisper 로컬 실행"""
    def __init__(self):
        from faster_whisper import WhisperModel
        self.model = WhisperModel("large-v3", device="cpu", compute_type="int8")

    async def transcribe_chunk(self, audio_chunk: bytes, language: str = "ko") -> str:
        # VAD로 분리된 발화 청크를 배치 처리
        segments, _ = self.model.transcribe(audio_chunk, language=language)
        return " ".join(seg.text for seg in segments)

def create_stt_provider(prefer_groq: bool = True) -> STTProvider:
    """환경에 따라 적절한 STT 제공자 선택"""
    if prefer_groq and is_groq_available():
        return GroqWhisperProvider()
    return LocalWhisperProvider()
```

### 오디오 파이프라인 통합

```
OS Audio (마이크 + 시스템)
  → VAD (Silero WASM, 무음 1.5초 감지)
  → 발화 구간 청크 추출 (PCM → WAV)
  → STTProvider.transcribe_chunk(chunk, language="ko")
  → 텍스트 → LanceDB 로컬 검색
  → Layer 2 꼬리 질문 생성 (Groq LLM)
```

### 의존성 추가

```toml
# pyproject.toml (데스크탑 앱)
faster-whisper = ">=1.0.3"      # 로컬 fallback
groq = ">=0.35.0"               # Primary STT + LLM
```

### 레이턴시 예상치

| 경로 | STT 레이턴시 | 전체 파이프라인 |
|------|-------------|----------------|
| Groq Whisper (Primary) | ~200ms | ~0.8s |
| faster-whisper CPU (Fallback) | ~500ms | ~1.2s |

### 적용 대상 Linear 티켓

- Jittda Live 음성 파이프라인 구현 (voice-pipeline 관련)

### 참조

- `jittda_doc/jittda_live_brainstorm_curated.md` — STT 리서치 결과
- `jittda_doc/jittda_reveiw.md` — Groq TTFT 0.14s, 실시간 아키텍처 검토
- `docs/plans/2026-02-19-architecture-documentation-design.md` §6.1
- `[[infrastructure/voice-pipeline/stt-provider]]`
- `[[infrastructure/voice-pipeline/groq-realtime]]`
- `[[application/live-session/live-engine]]`
