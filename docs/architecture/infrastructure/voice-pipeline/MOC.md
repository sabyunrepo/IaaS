---
title: "Voice Pipeline"
type: moc
layer: infrastructure
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[infrastructure/MOC]]"
tags: [voice, vad, stt, tts, silero, whisper, groq, realtime]
---

# Voice Pipeline

> Jittda Live 실시간 면접 가이드의 음성 입출력 파이프라인.
> OS 네이티브 오디오 캡처 → VAD → STT → 텍스트 → LLM 질문 생성
> 전체 레이턴시 목표: 0.8~1.0초 이내.

## 역할

- OS 네이티브 오디오 캡처 (macOS: ScreenCaptureKit/CoreAudio, Windows: WASAPI)
- Silero VAD로 발화 구간 감지 (무음 1.5초 → LLM 파이프라인 가동)
- STT: Groq Whisper large-v3 (Primary) + faster-whisper (Fallback)
- TTS: 면접관 대시보드 오디오 피드백 (선택적)
- Groq 실시간 API로 꼬리 질문 생성 (TTFT 0.14초)

## 문서 목록

| 문서 | 내용 |
|------|------|
| [[voice-pipeline/vad-silero\|VAD Silero]] | Silero VAD, WebAssembly, 발화 감지 |
| [[voice-pipeline/stt-provider\|STT Provider]] | Whisper large-v3, Groq Whisper, Provider 추상화 |
| [[voice-pipeline/tts-provider\|TTS Provider]] | TTS 서비스 연동, 면접관 피드백 오디오 |
| [[voice-pipeline/groq-realtime\|Groq Realtime]] | Groq 실시간 API, TTFT 최적화, 꼬리 질문 생성 |

## 전체 파이프라인

```
OS Audio (마이크 L채널 + 시스템 R채널)
      │
      ▼ (멀티채널 스테레오 스트림)
Silero VAD (WASM, 1ms 이하)
      │  ← 무음 1.5초 → 발화 완료 판정
      ▼
VAD 게이트 오픈 → 발화 청크 추출 (PCM → WAV)
      │
      ▼
STTProvider.transcribe_chunk(chunk, language="ko")
      │  ← Primary: Groq Whisper (~200ms)
      │  ← Fallback: faster-whisper CPU (~500ms)
      ▼
텍스트 → LanceDB 로컬 검색 (20ms)
      │
      ▼
Groq LLM 꼬리 질문 생성 (TTFT ~0.14s)
      │
      ▼
면접관 대시보드 표시
```

## 화자 분리 전략

| 면접 유형 | 전략 |
|----------|------|
| 온라인 면접 | 멀티채널 분리 (마이크 L, 시스템 R) — 화자 인식률 100% |
| 오프라인 면접 | AI 소프트웨어 화자 분리 (diarization) |

## 레이턴시 예산

| 단계 | 목표 |
|------|------|
| VAD 감지 | <1ms |
| STT (Groq Whisper) | ~200ms |
| LanceDB 로컬 검색 | ~20ms |
| Groq LLM TTFT | ~140ms |
| 전체 파이프라인 | **~0.8s** |

## 관련 ADR

- [[decisions/0008-stt-korean-alternative|ADR-0008: Jittda Live STT 한국어 지원]]
- [[decisions/0009-electron-vs-tauri|ADR-0009: Electron vs Tauri]]

## 관련 문서

```dataview
TABLE status, updated, tags
FROM "docs/architecture/infrastructure/voice-pipeline"
WHERE file.name != "MOC"
SORT file.name ASC
```
