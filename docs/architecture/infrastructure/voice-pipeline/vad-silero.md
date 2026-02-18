---
title: "VAD Silero"
type: component
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [vad, silero, wasm, onnx, electron, turn-taking]
parent: "[[voice-pipeline/MOC]]"
linear: []
---

# VAD Silero

## 개요

> Silero VAD (ONNX Runtime Web)를 Electron Renderer 프로세스에서 구동하여
> OS 오디오 스트림에서 발화 구간을 실시간으로 감지한다.
> 무음 1.5초 지속 시 발화 완료로 판정하여 STT 파이프라인을 가동한다.

## 상세 설계

### 핵심 개념

**Silero VAD 선택 이유**:
- `@ricky0123/vad` npm 패키지로 Electron 환경에서 즉시 사용 가능
- ONNX Runtime Web 기반 WASM 실행 — 메인 스레드 차단 없음
- TPR(True Positive Rate) 87.7% @ 5% FPR — WebRTC VAD(50%) 대비 4배 정확
- 6000+ 언어 학습 데이터 — 한국어 환경 안정 동작
- MIT 라이선스 (무료 상용 사용)

**발화 완료 판정 규칙**:
- 무음 1.5초 이상 지속 → 발화 완료 → STT 청크 생성
- 1.5초 미만 무음 → 발화 중 → 버퍼 유지

**멀티채널 오디오 처리**:
- 채널 0 (좌): 마이크 입력 (면접관)
- 채널 1 (우): 시스템 오디오 (지원자)
- VAD는 각 채널을 독립적으로 처리 → 화자별 발화 구간 분리

### 의존성

```json
// desktop/package.json
{
  "dependencies": {
    "@ricky0123/vad-web": "^0.0.22",
    "onnxruntime-web": "^1.20.0"
  }
}
```

### 코드 예시

#### Silero VAD 초기화 (Electron Renderer)

```typescript
// desktop/src/services/vad-engine.ts
import { MicVAD, utils } from "@ricky0123/vad-web";

export interface VADCallbacks {
  onSpeechStart: (channel: "mic" | "system") => void;
  onSpeechEnd: (audioChunk: Float32Array, channel: "mic" | "system") => void;
  onMisfire: () => void;
}

export class SileroVADEngine {
  private micVAD: MicVAD | null = null;
  private systemVAD: MicVAD | null = null;

  /**
   * VAD 초기화 — 마이크(좌채널)와 시스템 오디오(우채널) 별도 처리
   * @param sampleRate 오디오 샘플링 레이트 (권장: 16000Hz for Whisper)
   * @param silenceMs 발화 완료 판정 무음 지속 시간 (기본: 1500ms)
   */
  async init(callbacks: VADCallbacks, sampleRate = 16000, silenceMs = 1500): Promise<void> {
    const baseConfig = {
      positiveSpeechThreshold: 0.5,  // 발화 감지 임계값
      negativeSpeechThreshold: 0.35, // 발화 종료 임계값
      minSpeechFrames: 3,            // 최소 발화 프레임 수
      preSpeechPadFrames: 10,        // 발화 시작 전 패딩
      redemptionFrames: Math.ceil(silenceMs / 96), // 1.5초 → 프레임 수 변환
      frameSamples: 1536,            // 96ms per frame at 16kHz
    };

    // 마이크 채널 VAD
    this.micVAD = await MicVAD.new({
      ...baseConfig,
      model: "v5",
      workletURL: "/vad.worklet.bundle.min.js",
      modelURL: "/silero_vad_v5.onnx",
      onSpeechStart: () => callbacks.onSpeechStart("mic"),
      onSpeechEnd: (audio) => callbacks.onSpeechEnd(audio, "mic"),
      onVADMisfire: callbacks.onMisfire,
    });
  }

  /**
   * 스테레오 스트림에서 단일 채널 분리
   * @param stereoBuffer 스테레오 PCM 버퍼
   * @param channel 0 = 좌(마이크), 1 = 우(시스템)
   */
  extractChannel(stereoBuffer: Float32Array, channel: 0 | 1): Float32Array {
    const monoBuffer = new Float32Array(stereoBuffer.length / 2);
    for (let i = 0; i < monoBuffer.length; i++) {
      monoBuffer[i] = stereoBuffer[i * 2 + channel];
    }
    return monoBuffer;
  }

  /**
   * 실시간 오디오 청크 처리 (Electron Main Process IPC에서 수신)
   */
  async processAudioChunk(stereoChunk: Float32Array): Promise<void> {
    if (!this.micVAD) throw new Error("VAD not initialized");

    const micChannel = this.extractChannel(stereoChunk, 0);
    const systemChannel = this.extractChannel(stereoChunk, 1);

    // 각 채널 독립적으로 처리
    await this.micVAD.processAudio(micChannel);
    // system channel: 별도 VAD 인스턴스 또는 동일 인스턴스 순차 처리
  }

  start(): void {
    this.micVAD?.start();
  }

  pause(): void {
    this.micVAD?.pause();
  }

  destroy(): void {
    this.micVAD?.destroy();
    this.systemVAD?.destroy();
  }
}
```

#### VAD 이벤트 버스 통합 (Pub/Sub 패턴)

```typescript
// desktop/src/stores/audio-store.ts
import { create } from "zustand";
import { SileroVADEngine } from "../services/vad-engine";
import type { STTClient } from "../services/stt-client";

interface AudioState {
  isListening: boolean;
  currentSpeaker: "mic" | "system" | null;
  lastTranscript: string;

  startSession: (sttClient: STTClient) => Promise<void>;
  stopSession: () => void;
}

export const useAudioStore = create<AudioState>((set, get) => {
  const vad = new SileroVADEngine();

  return {
    isListening: false,
    currentSpeaker: null,
    lastTranscript: "",

    startSession: async (sttClient: STTClient) => {
      await vad.init({
        onSpeechStart: (channel) => {
          set({ currentSpeaker: channel });
        },
        onSpeechEnd: async (audioChunk, channel) => {
          // Float32Array → WAV 변환 후 STT 전송
          const wavBuffer = utils.encodeWAV(audioChunk);
          const transcript = await sttClient.transcribe(wavBuffer, "ko");
          set({ lastTranscript: transcript, currentSpeaker: null });
        },
        onMisfire: () => {
          set({ currentSpeaker: null });
        },
      });

      vad.start();
      set({ isListening: true });
    },

    stopSession: () => {
      vad.destroy();
      set({ isListening: false, currentSpeaker: null });
    },
  };
});
```

#### Float32Array → WAV 변환 유틸리티

```typescript
// desktop/src/utils/audio-utils.ts
export function float32ToWav(
  audioData: Float32Array,
  sampleRate = 16000,
): ArrayBuffer {
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = (sampleRate * numChannels * bitsPerSample) / 8;
  const blockAlign = (numChannels * bitsPerSample) / 8;
  const dataSize = audioData.length * blockAlign;
  const bufferSize = 44 + dataSize;

  const buffer = new ArrayBuffer(bufferSize);
  const view = new DataView(buffer);

  // WAV 헤더 작성
  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, bufferSize - 8, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);           // PCM 포맷
  view.setUint16(20, 1, true);            // PCM = 1
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  writeString(36, "data");
  view.setUint32(40, dataSize, true);

  // PCM 데이터 변환 (Float32 → Int16)
  const pcmData = new Int16Array(buffer, 44);
  for (let i = 0; i < audioData.length; i++) {
    const clipped = Math.max(-1, Math.min(1, audioData[i]));
    pcmData[i] = clipped < 0 ? clipped * 0x8000 : clipped * 0x7fff;
  }

  return buffer;
}
```

### VAD 파라미터 튜닝 가이드

| 파라미터 | 기본값 | 설명 | 조정 방향 |
|---------|-------|------|---------|
| `positiveSpeechThreshold` | 0.5 | 발화 감지 신뢰도 임계값 | 높이면 민감도↓, 낮추면 오감지↑ |
| `negativeSpeechThreshold` | 0.35 | 발화 종료 신뢰도 임계값 | 너무 낮으면 발화 중간 분절 발생 |
| `redemptionFrames` | ~16 (1.5s) | 발화 완료 판정 무음 프레임 수 | 면접에서는 1.5~2초 권장 |
| `preSpeechPadFrames` | 10 | 발화 시작 전 패딩 | 첫 단어 잘림 방지 |
| `minSpeechFrames` | 3 | 최소 발화 프레임 (약 0.3초) | 짧은 감탄사 필터링 |

## 관련 문서

- 상위: [[voice-pipeline/MOC]]
- 연관: [[voice-pipeline/stt-provider]]
- 연관: [[interface/electron-app/MOC]]
