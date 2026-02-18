---
title: "AI Code Heatmap"
type: component
layer: interface
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[interface/d3-charts/MOC]]"
depends-on:
  - "[[domain/scoring-system/authenticity-metric]]"
affects: []
linear: JIT-115
tags: [d3, heatmap, ai-detection, vibector, visualization]
---

# AICodeHeatmap.tsx -- Human vs AI 생성 비율 히트맵

> Vibector Worker (W3) 결과를 D3 Heatmap으로 시각화.
> 파일별 Human vs AI 코드 생성 비율을 색상 그라데이션으로 표시.
> Tab 3 (Code Deep Dive)에 배치.

## 시각화 개념

```
파일명              Human ◀─────────────▶ AI
─────────────────────────────────────────────
main.py            ████████████████░░░░  82%
utils/helpers.py   ████████████████████  100%
service/api.py     ██████████░░░░░░░░░░  52%  ⚠️
tests/test_main.py ████████████████████  100%
config/settings.py ████░░░░░░░░░░░░░░░░  20%  ⚠️
─────────────────────────────────────────────

색상: 짙은 파랑(Human 100%) → 빨강(AI 의심 높음)
```

## Props 인터페이스

```typescript
// frontend/src/components/charts/AICodeHeatmap.tsx
interface AICodeFile {
  path: string;               // 파일 경로
  human_ratio: number;        // Human 작성 비율 (0-1)
  ai_suspicion: number;       // AI 생성 의심 비율 (0-1)
  wpm_score: number;          // Words Per Minute 기반 점수
  total_lines: number;        // 전체 라인 수
  flagged_functions: string[]; // AI 의심 함수 목록
}

interface AICodeHeatmapProps {
  data: AICodeFile[];
  width?: number;
  height?: number;
  threshold?: number;         // AI 의심 경고 임계값 (default: 0.3)
}
```

## D3.js 구현 핵심

```typescript
import * as d3 from 'd3';

export function AICodeHeatmap({ data, width = 700, height, threshold = 0.3 }: AICodeHeatmapProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const rowHeight = 32;
  const computedHeight = height || data.length * rowHeight + 60;

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 30, right: 40, left: 200, bottom: 30 };
    const chartWidth = width - margin.left - margin.right;

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // X축: Human(0) -> AI(1)
    const xScale = d3.scaleLinear()
      .domain([0, 1])
      .range([0, chartWidth]);

    // 색상: 파랑(Human) -> 빨강(AI)
    const colorScale = d3.scaleLinear<string>()
      .domain([0, 0.3, 0.7, 1.0])
      .range(['#3b82f6', '#22c55e', '#eab308', '#ef4444']);

    // 행별 렌더링
    data.forEach((file, i) => {
      const y = i * rowHeight;

      // 파일명
      g.append('text')
        .attr('x', -10)
        .attr('y', y + rowHeight / 2)
        .attr('text-anchor', 'end')
        .attr('dominant-baseline', 'middle')
        .attr('class', 'text-xs')
        .text(file.path.split('/').pop() || file.path);

      // Human 비율 바
      g.append('rect')
        .attr('x', 0)
        .attr('y', y + 4)
        .attr('width', xScale(file.human_ratio))
        .attr('height', rowHeight - 8)
        .attr('fill', colorScale(file.ai_suspicion))
        .attr('rx', 2);

      // 비율 텍스트
      g.append('text')
        .attr('x', chartWidth + 5)
        .attr('y', y + rowHeight / 2)
        .attr('dominant-baseline', 'middle')
        .attr('class', 'text-xs font-mono')
        .text(`${Math.round(file.human_ratio * 100)}%`);

      // AI 의심 경고
      if (file.ai_suspicion > threshold) {
        g.append('text')
          .attr('x', chartWidth + 35)
          .attr('y', y + rowHeight / 2)
          .attr('dominant-baseline', 'middle')
          .text('!!');
      }
    });

    // 범례
    const legend = svg.append('g')
      .attr('transform', `translate(${margin.left}, ${computedHeight - 20})`);

    legend.append('text')
      .attr('class', 'text-xs')
      .text('Human 100%');
    legend.append('rect')
      .attr('x', 70).attr('y', -10)
      .attr('width', 100).attr('height', 10)
      .style('fill', 'url(#gradient)');
    legend.append('text')
      .attr('x', 175)
      .attr('class', 'text-xs')
      .text('AI 의심');
  }, [data, width, threshold]);

  return <svg ref={svgRef} width={width} height={computedHeight} />;
}
```

## Vibector WPM 분석 원리

Vibector Worker는 **Words Per Minute (WPM)** 패턴으로 AI 생성 코드를 탐지:

| 지표 | Human 코드 | AI 생성 코드 |
|------|----------|------------|
| WPM 패턴 | 불규칙, 멈춤 있음 | 균일, 연속적 |
| 변수 명명 | 개인 스타일 | 패턴화된 명명 |
| 주석 비율 | 불규칙 | 일정 비율 |
| 함수 길이 | 다양 | 표준화됨 |

## CEO 경고 표시

Overview 탭의 3초 요약 카드에서 AI 코드 의심 비율을 별도 경고로 표시:

```
+------------------------------------------+
|  종합 등급: B+ (상위 15%)                 |
|  ...                                     |
|  AI 코드 의심: 12%                        |
+------------------------------------------+
```

## 데이터 소스

- **Worker**: W3 (VibectorWorker)
- **Supervisor**: ForensicSupervisor
- **DB 테이블**: `analysis_results` (worker_name='vibector')
- **API**: `GET /api/v1/jobs/{job_id}/analysis/vibector`

## 관련 문서

- [[domain/scoring-system/authenticity-metric]] -- 진정성 지표 산출
- [[interface/d3-charts/MOC]] -- D3 차트 전체 목록
- [[interface/d3-charts/four-axis-radar]] -- 4축 레이더 (진정성 축)
