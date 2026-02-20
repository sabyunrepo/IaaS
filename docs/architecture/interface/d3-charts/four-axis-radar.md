---
title: "Four Axis Radar Chart"
type: component
layer: interface
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[interface/d3-charts/MOC]]"
depends-on:
  - "[[domain/scoring-system/four-metrics]]"
  - "[[interface/websocket/realtime-protocol]]"
affects: []
linear: JIT-113
tags: [d3, radar, chart, four-metrics, visualization]
---

# FourAxisRadar.tsx -- 4대 지표 레이더 차트

> 논리력 / 전문성 / 안정성 / 진정성 4개 축으로 후보자 역량을 한눈에 시각화.
> Tab 1 (Overview)에서 3초 요약 카드와 함께 표시된다.

## 시각화 예시

```
          논리력 (78)
             *
            / \
           /   \
          /     \
진정성 --*       *-- 전문성
  (45)    \     /    (65)
           \   /
            \ /
             *
          안정성 (72)

종합 등급: B+ (상위 15%)
```

## Props 인터페이스

```typescript
// frontend/src/components/charts/FourAxisRadar.tsx
interface FourAxisRadarProps {
  scores: {
    logic: number;       // 0-100, 논리력
    mastery: number;     // 0-100, 전문성
    stability: number;   // 0-100, 안정성
    authenticity: number; // 0-100, 진정성
  };
  confidence: 'high' | 'medium' | 'low';
  animated?: boolean;   // 점진적 렌더링 (WebSocket)
  size?: number;        // SVG 크기 (default: 400)
}
```

## D3.js 구현 핵심

```typescript
import * as d3 from 'd3';
import { useRef, useEffect } from 'react';

export function FourAxisRadar({ scores, confidence, animated, size = 400 }: FourAxisRadarProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = 60;
    const radius = (size - margin * 2) / 2;
    const center = size / 2;

    // 4축 정의
    const axes = [
      { key: 'logic', label: '논리력', angle: -Math.PI / 2 },
      { key: 'mastery', label: '전문성', angle: 0 },
      { key: 'stability', label: '안정성', angle: Math.PI / 2 },
      { key: 'authenticity', label: '진정성', angle: Math.PI },
    ];

    const scale = d3.scaleLinear().domain([0, 100]).range([0, radius]);

    // 배경 그리드 (20, 40, 60, 80, 100)
    const gridLevels = [20, 40, 60, 80, 100];
    const g = svg.append('g').attr('transform', `translate(${center},${center})`);

    gridLevels.forEach(level => {
      const points = axes.map(a => {
        const r = scale(level);
        return [r * Math.cos(a.angle), r * Math.sin(a.angle)];
      });
      g.append('polygon')
        .attr('points', points.map(p => p.join(',')).join(' '))
        .attr('fill', 'none')
        .attr('stroke', '#e5e7eb')
        .attr('stroke-width', 0.5);
    });

    // 축 라인
    axes.forEach(a => {
      g.append('line')
        .attr('x2', radius * Math.cos(a.angle))
        .attr('y2', radius * Math.sin(a.angle))
        .attr('stroke', '#d1d5db');
    });

    // 데이터 다각형
    const dataPoints = axes.map(a => {
      const value = scores[a.key as keyof typeof scores];
      const r = scale(value);
      return [r * Math.cos(a.angle), r * Math.sin(a.angle)];
    });

    const area = g.append('polygon')
      .attr('points', dataPoints.map(p => p.join(',')).join(' '))
      .attr('fill', getConfidenceColor(confidence))
      .attr('fill-opacity', 0.3)
      .attr('stroke', getConfidenceColor(confidence))
      .attr('stroke-width', 2);

    // 점진적 애니메이션 (WebSocket metric_update)
    if (animated) {
      area.attr('opacity', 0)
        .transition()
        .duration(800)
        .attr('opacity', 1);
    }

    // 축 레이블
    axes.forEach(a => {
      const value = scores[a.key as keyof typeof scores];
      const labelR = radius + 30;
      g.append('text')
        .attr('x', labelR * Math.cos(a.angle))
        .attr('y', labelR * Math.sin(a.angle))
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('class', 'text-sm font-medium')
        .text(`${a.label} (${value})`);
    });
  }, [scores, confidence, animated, size]);

  return <svg ref={svgRef} width={size} height={size} />;
}

function getConfidenceColor(confidence: string): string {
  switch (confidence) {
    case 'high': return '#22c55e';   // Green
    case 'medium': return '#eab308'; // Yellow
    case 'low': return '#ef4444';    // Red
    default: return '#6b7280';
  }
}
```

## WebSocket 점진적 렌더링

`metric_update` 메시지를 수신할 때마다 해당 축만 애니메이션으로 업데이트:

```typescript
// useLangGraphStream에서 metric_update 처리
case 'metric_update':
  setScores(prev => ({
    ...prev,
    [data.metric.replace('_score', '')]: data.value,
  }));
  break;
```

각 Worker 완료 시점에 해당 지표가 실시간으로 레이더 차트에 반영된다:
1. LogicSupervisor 완료 -> `logic_score` 축 렌더링
2. StackSupervisor 완료 -> `mastery_score` 축 렌더링
3. ForensicSupervisor 완료 -> `authenticity_score` 축 렌더링
4. ProfileSynthesizer 완료 -> `stability_score` + 최종 다각형

## 신호등 색상 체계

| 점수 범위 | 색상 | 의미 |
|----------|------|------|
| 70-100 | Green | 우수 |
| 40-69 | Yellow | 보통 |
| 0-39 | Red | 주의 |

## 관련 문서

- [[domain/scoring-system/four-metrics]] -- 4대 지표 산출 공식
- [[domain/scoring-system/confidence-levels]] -- 신뢰도 판정 기준
- [[interface/websocket/realtime-protocol]] -- `metric_update` 메시지 타입
- [[interface/d3-charts/MOC]] -- D3 차트 전체 목록
