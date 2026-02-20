---
title: "TTS Provider"
type: component
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [tts, text-to-speech, voice, audio, elevenlabs, openai-tts]
parent: "[[voice-pipeline/MOC]]"
linear: []
---

# TTS Provider

## 개요

> 면접 가이드 텍스트를 음성으로 변환하여 면접관에게 오디오 피드백을 제공한다.
> Jittda Live MVP에서 TTS는 선택적 기능이며, 면접관 요청 시 질문 카드를 음성으로 읽어주는 용도로 사용된다.
> STT와 동일한 Provider 추상화 패턴을 적용한다.

## 상세 설계

### 핵심 개념

**TTS 적용 시나리오**:
- 면접관이 화면을 보기 어려운 상황에서 AI 추천 질문을 음성으로 읽어줌
- 기본 비활성화 — 면접관이 설정에서 활성화할 수 있음
- 레이턴시 요구사항: STT+LLM 파이프라인과 독립적, 비실시간 허용

**Provider 옵션**:
1. **OpenAI TTS** (`tts-1-hd`): 자연스러운 음성, 한국어 지원, $0.03/1K chars
2. **ElevenLabs**: 감정 표현 풍부, 한국어 지원, 더 자연스러운 억양
3. **Edge TTS (Microsoft)**: 무료, 한국어 지원, 낮은 품질
4. **Kokoro TTS**: 오픈소스 로컬 실행 가능, 경량 모델

**MVP 선택**: OpenAI TTS — 이미 사용 중인 OpenAI 인프라 재사용, 별도 API 키 불필요.

### 의존성

```toml
# pyproject.toml
openai = ">=1.40.0"  # TTS API 포함
```

### 코드 예시

#### TTS Provider 인터페이스

```python
# infrastructure/voice_pipeline/tts_provider.py
from abc import ABC, abstractmethod

class TTSProvider(ABC):
    """TTS 제공자 추상 인터페이스"""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str = "nova",       # 음성 캐릭터
        language: str = "ko",
        speed: float = 1.0,
    ) -> bytes:
        """텍스트 → WAV/MP3 오디오 바이트"""
        ...
```

#### OpenAI TTS Provider

```python
# infrastructure/voice_pipeline/openai_tts_provider.py
from openai import AsyncOpenAI
from infrastructure.voice_pipeline.tts_provider import TTSProvider
from core.config import settings
import structlog

logger = structlog.get_logger(__name__)

class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS API — tts-1-hd 모델"""

    MODEL = "tts-1-hd"   # 고품질 (latency 약간 높음, 면접 가이드 비실시간 용도에 적합)
    # tts-1은 저품질이지만 latency 낮음 — 실시간 필요 시 대안

    # 한국어에 최적화된 음성: nova(여성, 자연스러움) 또는 echo(남성, 명확함)
    DEFAULT_VOICE = "nova"

    def __init__(self, api_key: str = settings.OPENAI_API_KEY):
        self._client = AsyncOpenAI(api_key=api_key)

    async def synthesize(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        language: str = "ko",
        speed: float = 1.0,
    ) -> bytes:
        """텍스트 → MP3 오디오 바이트"""
        if not text.strip():
            return b""

        response = await self._client.audio.speech.create(
            model=self.MODEL,
            voice=voice,
            input=text,
            response_format="mp3",
            speed=speed,
        )
        return response.content
```

#### Edge TTS Provider (무료 대안)

```python
# infrastructure/voice_pipeline/edge_tts_provider.py
# pip install edge-tts
import edge_tts
import io
from infrastructure.voice_pipeline.tts_provider import TTSProvider

class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS — 무료, 한국어 지원 (품질은 낮음)"""

    # 한국어 음성 목록
    VOICES = {
        "ko": "ko-KR-SunHiNeural",     # 여성, 자연스러운 발화
        "ko-male": "ko-KR-InJoonNeural", # 남성
    }

    async def synthesize(
        self,
        text: str,
        voice: str = "ko",
        language: str = "ko",
        speed: float = 1.0,
    ) -> bytes:
        voice_name = self.VOICES.get(voice, self.VOICES["ko"])
        rate = f"+{int((speed - 1.0) * 100)}%" if speed != 1.0 else "+0%"

        communicate = edge_tts.Communicate(text, voice_name, rate=rate)
        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        return audio_buffer.getvalue()
```

#### Electron에서 오디오 재생

```typescript
// desktop/src/services/tts-client.ts
export class TTSClient {
  private apiBase: string;
  private enabled = false;

  constructor(apiBase = "http://localhost:8001") {
    this.apiBase = apiBase;
  }

  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  async speakText(text: string, language = "ko"): Promise<void> {
    if (!this.enabled) return;

    const response = await fetch(`${this.apiBase}/tts/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, language }),
    });

    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);

    await audio.play();
    audio.onended = () => URL.revokeObjectURL(audioUrl);
  }

  /**
   * 면접관 대시보드 — AI 추천 질문 카드를 읽어줌
   */
  async readQuestionCard(question: string): Promise<void> {
    // 너무 긴 질문은 첫 문장만 읽기
    const shortText = question.split(".")[0].trim();
    await this.speakText(shortText);
  }
}
```

#### FastAPI TTS 엔드포인트

```python
# interface/api/routes/tts.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from infrastructure.voice_pipeline.openai_tts_provider import OpenAITTSProvider

router = APIRouter(prefix="/tts", tags=["tts"])
tts_provider = OpenAITTSProvider()

class TTSRequest(BaseModel):
    text: str
    language: str = "ko"
    voice: str = "nova"
    speed: float = 1.0

@router.post("/synthesize")
async def synthesize_text(request: TTSRequest) -> Response:
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="text는 비어있을 수 없습니다")

    audio_bytes = await tts_provider.synthesize(
        text=request.text,
        voice=request.voice,
        language=request.language,
        speed=request.speed,
    )
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="speech.mp3"'},
    )
```

### TTS 서비스 비교

| 서비스 | 한국어 품질 | 레이턴시 | 가격 | Electron 통합 |
|--------|-----------|---------|------|------------|
| OpenAI TTS (`tts-1-hd`) | 높음 | ~1~2s | $0.03/1K chars | API 호출 |
| OpenAI TTS (`tts-1`) | 중간 | ~0.5s | $0.015/1K chars | API 호출 |
| ElevenLabs | 매우 높음 | ~1s | $0.30/1K chars | API 호출 |
| Edge TTS | 보통 | <0.5s | 무료 | Python 로컬 |
| Kokoro TTS | 보통 | ~0.3s (CPU) | 무료 | Python 로컬 |

**MVP 권장**: OpenAI TTS `tts-1` — 낮은 레이턴시 + OpenAI 인프라 통합 + 무난한 한국어 품질.

## 관련 문서

- 상위: [[voice-pipeline/MOC]]
- 연관: [[voice-pipeline/stt-provider]], [[voice-pipeline/groq-realtime]]
