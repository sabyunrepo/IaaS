---
title: "D3 Charts"
type: moc
layer: interface
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[interface/MOC]]"
tags: [d3, visualization, chart, frontend]
---

# D3 Charts

> D3.js v7 기반 데이터 시각화 컴포넌트.
> 4대 지표(논리력/전문성/안정성/진정성)와 코드 분석 결과를 비개발자도 이해할 수 있게 시각화한다.

## 차트 목록

| 차트 | 컴포넌트 | 데이터 소스 | 탭 |
|------|---------|-----------|-----|
| [[d3-charts/four-axis-radar\|4축 레이더]] | `FourAxisRadar.tsx` | 4대 지표 | Tab 1: Overview |
| [[d3-charts/complexity-treemap\|복잡도 트리맵]] | `ComplexityTreemap.tsx` | W7 (Radon/Lizard) | Tab 3: Code Deep Dive |
| [[d3-charts/ai-code-heatmap\|AI 코드 히트맵]] | `AICodeHeatmap.tsx` | W3 (Vibector) | Tab 3: Code Deep Dive |
| [[d3-charts/skill-heatmap\|기술 히트맵]] | `SkillHeatmap.tsx` | W9 (SkillExtractor) | Tab 3: Code Deep Dive |

## ResultPage 탭 구조

```
ResultPage:
├── Tab 1: Overview (3초 요약)
│   ├── 신호등 카드 (Green/Yellow/Red) + 종합 등급
│   ├── FourAxisRadar.tsx (4대 지표)
│   └── AI 코드 의심 비율 경고
│
├── Tab 2: Intel Brief (기존 + 진정성 검증)
│
├── Tab 3: Code Deep Dive (신규)
│   ├── ComplexityTreemap.tsx (파일별 복잡도)
│   ├── AICodeHeatmap.tsx (Human vs AI)
│   └── SkillHeatmap.tsx (JD 매칭)
│
├── Tab 4: Interview (3전략 그룹핑 + 카드형 UI)
│
└── Tab 5: Decision (4대 지표 기반 종합 판단)
```

## 기술 의존성

```json
{
  "dependencies": {
    "d3": "^7.9.0",
    "@types/d3": "^7.4.3",
    "react": "^19.0.0",
    "@tanstack/react-query": "^5.0.0"
  }
}
```

## 문서 목록 (자동)

```dataview
TABLE status, updated, tags
FROM "docs/architecture/interface/d3-charts"
WHERE file.name != "MOC"
SORT file.name ASC
```

## 관련 문서

- [[domain/scoring-system/four-metrics]] -- 4대 지표 산출 로직
- [[interface/websocket/realtime-protocol]] -- `metric_update` 실시간 렌더링
