---
title: "STT Provider"
type: component
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [stt, whisper, groq-whisper, faster-whisper, korean, provider-pattern]
parent: "[[voice-pipeline/MOC]]"
depends-on:
  - "[[decisions/0008-stt-korean-alternative]]"
linear: []
---

# STT Provider

## 개요

> 한국어 + 영어 STT(Speech-to-Text) 처리를 위한 Provider 추상화 계층.
> Primary: Groq Whisper large-v3 (가속 추론, ~200ms),
> Fallback: faster-whisper 로컬 실행 (~500ms).
> VAD가 분리한 발화 청크(WAV)를 텍스트로 변환한다.

## 상세 설계

### 핵심 개념

**STT 전략 (ADR-0008)**:
- Deepgram Nova-3는 한국어 WER가 높아(7~16%) 한국어 면접에 부적합 판정
- Whisper large-v3는 한국어 WER 5~8% — 99+ 언어 지원
- Groq LPU 가속으로 동일 모델 가중치에서 ~200ms 응답 (로컬 CPU 대비 5~10x)
- 장애 시 faster-whisper 로컬으로 자동 Fallback

**Provider 패턴**:
- `STTProvider` 추상 인터페이스로 Groq/로컬 구현체를 교체 가능하게 설계
- `create_stt_provider()` 팩토리로 환경에 따라 적절한 Provider 선택
- Groq API 장애 감지 시 자동 Fallback 전환

**발화 청크 처리**:
- VAD가 생성한 Float32Array → WAV 버퍼로 변환 후 전달
- Groq API: `audio/wav` 멀티파트 업로드
- faster-whisper: bytes 직접 처리

### 의존성

```toml
# pyproject.toml (데스크탑 앱 Python 백엔드 또는 Electron Node.js 사이드카)
faster-whisper = ">=1.0.3"  # 로컬 fallback (CTranslate2 최적화)
groq = ">=0.35.0"           # Primary STT + LLM

# Electron TypeScript 환경의 경우 Groq 호출은 서버로 프록시
```

### 코드 예시

#### STTProvider 추상 인터페이스

```python
# infrastructure/voice_pipeline/stt_provider.py
from abc import ABC, abstractmethod

class STTProvider(ABC):
    """STT 제공자 추상 인터페이스"""

    @abstractmethod
    async def transcribe_chunk(
        self,
        audio_chunk: bytes,      # WAV 포맷 바이트
        language: str = "ko",   # BCP-47 언어 코드
    ) -> str:
        """발화 청크 → 텍스트 변환"""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """제공자 사용 가능 여부 확인"""
        ...
```

#### Groq Whisper Provider (Primary)

```python
# infrastructure/voice_pipeline/groq_whisper_provider.py
from groq import AsyncGroq
from infrastructure.voice_pipeline.stt_provider import STTProvider
from core.config import settings
import structlog

logger = structlog.get_logger(__name__)

class GroqWhisperProvider(STTProvider):
    """Primary: Groq Whisper large-v3 가속 추론 (~200ms)"""

    MODEL = "whisper-large-v3"

    def __init__(self, api_key: str = settings.GROQ_API_KEY):
        self._client = AsyncGroq(api_key=api_key)
        self._available = True

    def is_available(self) -> bool:
        return self._available

    async def transcribe_chunk(
        self,
        audio_chunk: bytes,
        language: str = "ko",
    ) -> str:
        try:
            response = await self._client.audio.transcriptions.create(
                model=self.MODEL,
                file=("audio.wav", audio_chunk, "audio/wav"),
                language=language,
                response_format="text",
                temperature=0.0,  # 결정론적 전사
            )
            return response.strip()

        except Exception as e:
            logger.warning("Groq STT 실패 — Fallback 필요", error=str(e))
            self._available = False
            raise
```

#### faster-whisper Provider (Fallback)

```python
# infrastructure/voice_pipeline/local_whisper_provider.py
import io
import asyncio
from concurrent.futures import ThreadPoolExecutor
from infrastructure.voice_pipeline.stt_provider import STTProvider
import structlog

logger = structlog.get_logger(__name__)

class LocalWhisperProvider(STTProvider):
    """Fallback: faster-whisper 로컬 실행 (~500ms CPU)"""

    MODEL_SIZE = "large-v3"
    _executor = ThreadPoolExecutor(max_workers=2)  # CPU 바운드 작업

    def __init__(self):
        from faster_whisper import WhisperModel
        logger.info("faster-whisper 로컬 모델 로딩 중...", model=self.MODEL_SIZE)
        self._model = WhisperModel(
            self.MODEL_SIZE,
            device="cpu",
            compute_type="int8",     # CPU 최적화 (양자화)
            num_workers=2,
        )
        logger.info("faster-whisper 로드 완료")

    def is_available(self) -> bool:
        return True  # 로컬 모델은 항상 사용 가능

    async def transcribe_chunk(
        self,
        audio_chunk: bytes,
        language: str = "ko",
    ) -> str:
        """CPU 바운드 작업 — executor에서 비동기 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._sync_transcribe,
            audio_chunk,
            language,
        )

    def _sync_transcribe(self, audio_chunk: bytes, language: str) -> str:
        audio_io = io.BytesIO(audio_chunk)
        segments, info = self._model.transcribe(
            audio_io,
            language=language,
            beam_size=5,
            vad_filter=False,       # VAD는 Silero에서 이미 처리
            condition_on_previous_text=False,
        )
        return " ".join(seg.text.strip() for seg in segments)
```

#### STT Provider 팩토리

```python
# infrastructure/voice_pipeline/stt_factory.py
import asyncio
from infrastructure.voice_pipeline.stt_provider import STTProvider
from infrastructure.voice_pipeline.groq_whisper_provider import GroqWhisperProvider
from infrastructure.voice_pipeline.local_whisper_provider import LocalWhisperProvider
import structlog

logger = structlog.get_logger(__name__)

class FallbackSTTProvider(STTProvider):
    """Primary 실패 시 Fallback STTProvider로 자동 전환"""

    def __init__(self, primary: STTProvider, fallback: STTProvider):
        self._primary = primary
        self._fallback = fallback

    def is_available(self) -> bool:
        return self._primary.is_available() or self._fallback.is_available()

    async def transcribe_chunk(self, audio_chunk: bytes, language: str = "ko") -> str:
        if self._primary.is_available():
            try:
                return await self._primary.transcribe_chunk(audio_chunk, language)
            except Exception as e:
                logger.warning("Primary STT 실패, Fallback 전환", error=str(e))

        logger.info("Fallback STT 사용 중")
        return await self._fallback.transcribe_chunk(audio_chunk, language)

def create_stt_provider(prefer_groq: bool = True) -> STTProvider:
    """환경에 따라 적절한 STT 제공자 선택"""
    if prefer_groq:
        groq_provider = GroqWhisperProvider()
        local_provider = LocalWhisperProvider()
        return FallbackSTTProvider(primary=groq_provider, fallback=local_provider)
    return LocalWhisperProvider()
```

#### STT 파이프라인 사용 예시

```typescript
// desktop/src/services/stt-client.ts (Electron Renderer → Python 사이드카)
export class STTClient {
  private apiBase: string;

  constructor(apiBase = "http://localhost:8001") {
    this.apiBase = apiBase;  // 로컬 Python 사이드카 서버
  }

  async transcribe(wavBuffer: ArrayBuffer, language = "ko"): Promise<string> {
    const formData = new FormData();
    formData.append("audio", new Blob([wavBuffer], { type: "audio/wav" }), "chunk.wav");
    formData.append("language", language);

    const response = await fetch(`${this.apiBase}/stt/transcribe`, {
      method: "POST",
      body: formData,
    });

    const { text } = await response.json();
    return text;
  }
}
```

### 레이턴시 비교

| Provider | STT 레이턴시 | 전체 파이프라인 | 비고 |
|----------|------------|----------------|------|
| Groq Whisper (Primary) | ~200ms | ~0.8s | GPU 가속, API 의존 |
| faster-whisper CPU (Fallback) | ~500ms | ~1.2s | 오프라인 동작 |
| faster-whisper GPU | ~100ms | ~0.6s | GPU 있는 경우 |

### 한국어 WER 비교

| 서비스 | 한국어 WER | 판단 |
|--------|-----------|------|
| Whisper large-v3 (Groq) | 5~8% | 채택 |
| Deepgram Nova-3 | 7~16% | Tier 2 — 불채택 |
| AssemblyAI Universal | 균일 지원 (미측정) | 대안 |

## 관련 문서

- 상위: [[voice-pipeline/MOC]]
- 의존: [[decisions/0008-stt-korean-alternative]]
- 연관: [[voice-pipeline/vad-silero]], [[voice-pipeline/groq-realtime]]
