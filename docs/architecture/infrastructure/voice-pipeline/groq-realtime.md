---
title: "Groq Realtime"
type: component
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [groq, realtime, ttft, llm, follow-up-question, lpu]
parent: "[[voice-pipeline/MOC]]"
linear: []
---

# Groq Realtime

## 개요

> Groq LPU(Language Processing Unit) 기반 실시간 API로
> STT 텍스트 + LanceDB 검색 결과를 기반으로 꼬리 질문을 생성한다.
> TTFT(Time to First Token) 0.14초로 면접관이 즉시 참고할 수 있는 질문 카드를 제공한다.

## 상세 설계

### 핵심 개념

**Groq 선택 이유**:
- TTFT 0.14초 (Llama 70B 기준) — 면접 실시간 응답에 최적
- 출력 속도 750 t/s (Llama 70B) — 짧은 질문 카드 생성에 충분
- Groq Whisper도 사용하므로 단일 API 키/청구 통합
- 가격: $0.64/M tokens (Llama 3.3 70B)

**Groq 실시간 활용 범위**:
- Layer 1: 발화에서 토픽 감지 → 준비된 질문 덱 검색 (로컬 LanceDB, 20ms)
- Layer 2: 발화 내용에서 의혹/검증 포인트 발견 → Groq로 꼬리 질문 동적 생성 (~0.8s)
- Layer 3: 면접관이 수동으로 새 질문 요청 → Groq로 즉시 생성

**스트리밍 응답**:
- Groq API는 SSE(Server-Sent Events) 스트리밍 지원
- 첫 토큰이 0.14초 내에 도착하여 면접관 대시보드에 점진적으로 렌더링
- 3개 이내의 짧은 Bullet point 형태로 출력

### 의존성

```toml
# pyproject.toml
groq = ">=0.35.0"
```

```bash
# .env
GROQ_API_KEY=gsk_...
```

### 코드 예시

#### Groq 실시간 클라이언트

```python
# infrastructure/voice_pipeline/groq_realtime_client.py
from groq import AsyncGroq
from core.config import settings
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class ProbingQuestion:
    """꼬리 질문 카드"""
    questions: list[str]          # 추천 꼬리 질문 (최대 3개)
    verification_point: str       # 검증 포인트 (면접관에게 짧은 컨텍스트)
    urgency: str                  # 'high' | 'medium' | 'low'
    evidence_from_speech: str     # 발화에서 발견된 의혹 근거

class GroqRealtimeClient:
    """Groq LPU 기반 실시간 꼬리 질문 생성"""

    MODEL = "llama-3.3-70b-versatile"
    MAX_TOKENS = 400  # 3개 짧은 질문 카드 — 빠른 생성 우선

    SYSTEM_PROMPT = """당신은 면접관의 실시간 AI 참모입니다.
지원자의 발화 내용에서 검증이 필요한 포인트를 찾아,
면접관이 즉시 사용할 수 있는 짧고 날카로운 꼬리 질문을 3개 이내로 생성합니다.

출력 형식 (JSON):
{
  "verification_point": "한 문장으로 요약한 검증 포인트",
  "questions": ["질문1", "질문2", "질문3"],
  "urgency": "high|medium|low",
  "evidence_from_speech": "발화에서 발견된 의혹 구절"
}

규칙:
- 질문은 30자 이내로 짧고 구체적으로
- 비개발자 면접관도 이해하고 바로 사용 가능한 표현
- 기술 용어 사용 시 괄호로 간단 설명 추가
- 지원자 이력서/코드와 발화 내용의 불일치에 집중"""

    def __init__(self, api_key: str = settings.GROQ_API_KEY):
        self._client = AsyncGroq(api_key=api_key)

    async def generate_probing_questions(
        self,
        speech_text: str,
        candidate_context: dict,     # LanceDB 검색 결과 (이력서, 코드 요약)
        interview_history: list[str], # 이전 발화 요약 (최근 3개)
    ) -> ProbingQuestion:
        """발화 분석 → 꼬리 질문 생성 (스트리밍 아님 — JSON 응답 필요)"""

        user_message = self._build_user_message(
            speech_text, candidate_context, interview_history
        )

        try:
            response = await self._client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=self.MAX_TOKENS,
                temperature=0.3,         # 일관성 있는 질문 생성
                response_format={"type": "json_object"},
            )

            import json
            result = json.loads(response.choices[0].message.content)
            return ProbingQuestion(
                questions=result.get("questions", [])[:3],
                verification_point=result.get("verification_point", ""),
                urgency=result.get("urgency", "medium"),
                evidence_from_speech=result.get("evidence_from_speech", ""),
            )

        except Exception as e:
            logger.error("Groq 꼬리 질문 생성 실패", error=str(e))
            raise

    async def generate_probing_questions_stream(
        self,
        speech_text: str,
        candidate_context: dict,
        interview_history: list[str],
    ):
        """스트리밍 응답 — 첫 토큰 0.14초에 대시보드 즉시 렌더링 시작"""
        user_message = self._build_user_message(
            speech_text, candidate_context, interview_history
        )

        stream = await self._client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=self.MAX_TOKENS,
            temperature=0.3,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta  # 청크 단위로 Electron IPC로 전송

    def _build_user_message(
        self,
        speech_text: str,
        candidate_context: dict,
        interview_history: list[str],
    ) -> str:
        resume_summary = candidate_context.get("resume_summary", "정보 없음")
        code_highlights = candidate_context.get("code_highlights", "정보 없음")
        history = "\n".join(f"- {h}" for h in interview_history[-3:])

        return f"""## 지원자 발화 (방금 전)
{speech_text}

## 이전 대화 맥락 (최근 3개)
{history}

## 이력서 핵심 요약
{resume_summary}

## 관련 코드 특징 (RAG 검색)
{code_highlights}

위 정보를 바탕으로 검증 포인트와 꼬리 질문을 생성하세요."""
```

#### FastAPI WebSocket 엔드포인트

```python
# interface/api/routes/live.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from infrastructure.voice_pipeline.groq_realtime_client import GroqRealtimeClient
from infrastructure.embedding.pgvector_store import PgVectorStore
import json

router = APIRouter(prefix="/live", tags=["live"])
groq_client = GroqRealtimeClient()

@router.websocket("/ws/{job_id}")
async def live_interview_ws(websocket: WebSocket, job_id: str):
    """실시간 면접 WebSocket 엔드포인트"""
    await websocket.accept()

    try:
        while True:
            # Electron 앱에서 STT 텍스트 수신
            data = await websocket.receive_json()
            speech_text = data.get("speech_text", "")
            channel = data.get("channel", "mic")  # 'mic' | 'system'

            if not speech_text.strip():
                continue

            # LanceDB 로컬 검색 결과를 클라이언트에서 전달받거나
            # 서버에서 pgvector 검색
            candidate_context = data.get("context", {})

            # 스트리밍으로 꼬리 질문 전송
            await websocket.send_json({
                "type": "probing_start",
                "channel": channel,
            })

            accumulated = ""
            async for chunk in groq_client.generate_probing_questions_stream(
                speech_text=speech_text,
                candidate_context=candidate_context,
                interview_history=data.get("history", []),
            ):
                accumulated += chunk
                await websocket.send_json({
                    "type": "probing_chunk",
                    "delta": chunk,
                })

            await websocket.send_json({
                "type": "probing_done",
                "full_response": accumulated,
            })

    except WebSocketDisconnect:
        pass
```

#### Electron 클라이언트 통합

```typescript
// desktop/src/services/live-session.ts
import { useAudioStore } from "../stores/audio-store";
import { TTSClient } from "./tts-client";

export class LiveSession {
  private ws: WebSocket | null = null;
  private ttsClient = new TTSClient();

  connect(jobId: string, serverUrl = "ws://localhost:8000"): void {
    this.ws = new WebSocket(`${serverUrl}/live/ws/${jobId}`);

    this.ws.onmessage = async (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case "probing_start":
          // 대시보드에 로딩 인디케이터 표시
          useDashboardStore.getState().setGenerating(true);
          break;

        case "probing_chunk":
          // 스트리밍 텍스트 점진적 렌더링
          useDashboardStore.getState().appendProbingText(data.delta);
          break;

        case "probing_done":
          // 완성된 카드 파싱 + 표시
          useDashboardStore.getState().setGenerating(false);
          try {
            const parsed = JSON.parse(data.full_response);
            useDashboardStore.getState().addProbingCard(parsed);
          } catch {
            // JSON 파싱 실패 시 raw 텍스트 표시
          }
          break;
      }
    };
  }

  /**
   * STT 결과를 서버로 전송 (VAD onSpeechEnd 콜백에서 호출)
   */
  sendSpeech(speechText: string, channel: "mic" | "system"): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    this.ws.send(JSON.stringify({
      speech_text: speechText,
      channel,
      history: useDashboardStore.getState().getRecentHistory(3),
      context: useLanceStore.getState().search(speechText),  // 로컬 검색
    }));
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }
}
```

### 레이턴시 분석

```
VAD 발화 완료 감지 (1.5s 무음)
      │
      ▼ (0ms)
STT 전송 (Groq Whisper)
      │
      ▼ (~200ms)
텍스트 수신
      │
      ├──→ LanceDB 로컬 검색 (20ms) → Layer 1 질문 카드 즉시 표시
      │
      └──→ Groq LLM 꼬리 질문 생성
                │
                ▼ (TTFT ~140ms)
           첫 토큰 대시보드 렌더링 시작
                │
                ▼ (~400ms 총 생성)
           꼬리 질문 카드 완성

전체: ~0.8초 (발화 완료 → 카드 표시)
```

### Groq 모델 선택

| 모델 | TTFT | 한국어 | 가격 | 용도 |
|------|------|--------|------|------|
| `llama-3.3-70b-versatile` | ~0.14s | 중간 | $0.64/M | 꼬리 질문 생성 (기본) |
| `llama-3.1-8b-instant` | ~0.07s | 낮음 | $0.05/M | 초저지연 필요 시 |
| `gemma2-9b-it` | ~0.10s | 중간 | $0.20/M | 경량 대안 |

**한국어 품질 보완**: 면접 컨텍스트 + 시스템 프롬프트 최적화로 한국어 품질 향상 가능.
한국어 특화가 필요하다면 Together AI의 `SOLAR-10.7B-v1.0`을 Fallback으로 구성.

## 관련 문서

- 상위: [[voice-pipeline/MOC]]
- 연관: [[voice-pipeline/stt-provider]], [[voice-pipeline/vad-silero]], [[voice-pipeline/tts-provider]]
- 연관: [[interface/websocket/MOC]]
