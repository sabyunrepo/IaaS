---
title: "Electron App"
type: moc
layer: interface
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[interface/MOC]]"
tags: [electron, desktop, live, interview, realtime]
---

# Electron App (Jittda Live)

> Jittda Live 실시간 AI 면접 가이드 데스크톱 클라이언트.
> Electron v33+ 기반, Main/Renderer/Child Process 3계층 아키텍처.
> 면접관이 화상회의 옆에 띄워두고 사용하는 비침해적(Non-intrusive) 어시스턴트.

## 기술 스택

| 항목 | 선택 | 근거 |
|------|------|------|
| 프레임워크 | Electron v33+ | 네이티브 오디오 접근, npm 생태계 |
| 오디오 캡처 | electron-audio-loopback | 가상 드라이버 불필요, OS 네이티브 |
| VAD | Silero VAD (WASM) | Renderer에서 1ms 이하 무음 감지 |
| 로컬 DB | LanceDB v0.26 | In-process 벡터 검색 <60ms |
| 그래프 탐색 | graphology | In-memory 그래프 탐색 <5ms |
| STT | Deepgram Nova-3 | 한/영 WER 7-16%, WebSocket 스트리밍 |
| 실시간 LLM | Groq (Llama 3.3 70B) | TTFT 0.14s, 꼬리 질문 생성 |
| UI | React 19 + Tailwind 4 | 기존 웹 기술 재사용 |
| 빌드 | Electron Forge | 크로스 플랫폼 패키징 |

## 문서 목록

| 문서 | 내용 |
|------|------|
| [[electron-app/architecture\|Architecture]] | Main/Renderer/Child Process 3계층 |
| [[electron-app/audio-capture\|Audio Capture]] | OS별 오디오 캡처 구현 |
| [[electron-app/lancedb-local\|LanceDB Local]] | Read-Heavy 전략, Local-First RAG |
| [[electron-app/tauri-migration\|Tauri Migration]] | Electron -> Tauri 2.x 마이그레이션 로드맵 |

## 전체 파이프라인

```
OS Audio (마이크 + 시스템) → Child Process (네이티브 바이너리)
    → Main Process (IPC) → Renderer Process
        → Silero VAD → Deepgram STT → LanceDB + graphology
            → Groq LLM → 면접관 대시보드 UI
```

## 문서 목록 (자동)

```dataview
TABLE status, updated, tags
FROM "docs/architecture/interface/electron-app"
WHERE file.name != "MOC"
SORT file.name ASC
```

## 관련 ADR

- [[decisions/0009-electron-vs-tauri]] -- Electron v33 선택 + Tauri 마이그레이션 로드맵

```dataview
LIST
FROM "docs/architecture/decisions"
WHERE contains(impacts, this.file.link)
SORT date DESC
```
