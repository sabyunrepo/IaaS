---
title: "Relation Map"
type: crosscutting
status: draft
created: 2026-02-19
updated: 2026-02-19
---

# Relation Map

> 전체 아키텍처 컴포넌트 간 의존성 시각화.

## 의존성 그래프

```mermaid
graph TB
    subgraph Domain["🟦 Domain Layer"]
        IR[Identity Resolution]
        SC[Scoring System]
        FS[Funnel Selection]
        QG[Question Generation]
        LP[LinkedIn Profile]
    end

    subgraph Application["🟩 Application Layer"]
        MA[MetaAgent Graph]
        LS[Live Session Engine]
        SM[State Management]
        QA[Quality Gate]
    end

    subgraph Infrastructure["🟧 Infrastructure Layer"]
        GA[Git Adapter]
        GH[GitHub Client]
        TS[Tree-sitter AST]
        CA[Complexity Analysis]
        PD[Plagiarism Detection]
        LI[LLM Instructor]
        VS[Vector Search]
        LA[LinkedIn Adapter]
        VP[Voice Pipeline]
    end

    subgraph Interface["🟪 Interface Layer"]
        RA[REST API]
        WS[WebSocket]
        EA[Electron App]
        D3[D3 Charts]
        WF[Web Frontend]
    end

    %% Domain → Infrastructure 의존
    IR -->|uses| GA
    IR -->|uses| GH
    SC -->|uses| CA
    SC -->|uses| PD
    FS -->|uses| VS
    QG -->|uses| LI
    QG -->|uses| TS
    LP -->|uses| LA

    %% Application → Domain 의존
    MA -->|orchestrates| IR
    MA -->|orchestrates| SC
    MA -->|orchestrates| FS
    MA -->|orchestrates| QG
    LS -->|uses| QG
    LS -->|uses| VP
    QA -->|validates| QG

    %% Application → Infrastructure 의존
    MA -->|uses| LI
    SM -->|uses| VS

    %% Interface → Application 의존
    RA -->|calls| MA
    WS -->|streams| MA
    EA -->|hosts| LS
    D3 -->|renders| SC
    WF --> RA
    WF --> WS
    WF --> D3
```

## 범례

| 색상 | 계층 | 의존 방향 |
|------|------|----------|
| 🟦 파랑 | Domain | Infrastructure를 사용 (Port/Adapter) |
| 🟩 초록 | Application | Domain + Infrastructure 오케스트레이션 |
| 🟧 주황 | Infrastructure | 외부 서비스 어댑터 (의존 받기만) |
| 🟪 보라 | Interface | Application 호출 (진입점) |

## Dataview: 관계 밀도

```dataview
TABLE length(depends-on) as "의존", length(affects) as "영향"
FROM "docs/architecture"
WHERE type != "moc" AND type != "adr"
SORT length(depends-on) + length(affects) DESC
LIMIT 20
```
