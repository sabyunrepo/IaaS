---
title: "Complexity Treemap"
type: component
layer: interface
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[interface/d3-charts/MOC]]"
depends-on:
  - "[[infrastructure/complexity-analysis/radon]]"
  - "[[infrastructure/complexity-analysis/lizard]]"
affects: []
linear: JIT-114
tags: [d3, treemap, complexity, visualization]
---

# ComplexityTreemap.tsx -- 파일별 복잡도 드릴다운

> Radon/Lizard Worker (W7) 결과를 D3 Treemap으로 시각화.
> 파일 크기 = LOC, 색상 = Cyclomatic Complexity.
> Tab 3 (Code Deep Dive)에 배치.

## 시각화 개념

```
┌─────────────────────────────────────────┐
│  main.py (CC:12)  │  utils.py (CC:3)   │
│  ██████████████████│  ████              │
│  ██████████████████│                    │
├───────────┬───────┤────────────────────│
│ service/  │cache/ │  tests/            │
│ api.py    │redis  │  test_main.py      │
│ (CC:8)    │(CC:5) │  (CC:2)            │
│ █████████ │██████ │  ██                │
└───────────┴───────┴────────────────────┘

색상: 빨강(CC>10) / 노랑(CC 5-10) / 초록(CC<5)
면적: LOC (Lines of Code) 비례
```

## Props 인터페이스

```typescript
// frontend/src/components/charts/ComplexityTreemap.tsx
interface TreemapNode {
  name: string;          // 파일명 (e.g. "main.py")
  path: string;          // 전체 경로 (e.g. "src/main.py")
  loc: number;           // Lines of Code
  cyclomatic: number;    // Cyclomatic Complexity 평균
  halstead: number;      // Halstead Difficulty
  maintainability: number; // Maintainability Index
  functions: FunctionDetail[];  // 함수별 상세 (클릭 시 팝업)
}

interface FunctionDetail {
  name: string;
  start_line: number;
  end_line: number;
  cyclomatic: number;
  parameters: number;
  nloc: number;
}

interface ComplexityTreemapProps {
  data: TreemapNode[];
  width?: number;
  height?: number;
  onFileClick?: (node: TreemapNode) => void;  // 상세 팝업
}
```

## D3.js 구현 핵심

```typescript
import * as d3 from 'd3';

export function ComplexityTreemap({ data, width = 800, height = 500, onFileClick }: ComplexityTreemapProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // 계층 구조 생성 (디렉토리 기반)
    const root = d3.hierarchy(buildHierarchy(data))
      .sum(d => d.loc || 0)
      .sort((a, b) => (b.value || 0) - (a.value || 0));

    d3.treemap<TreemapNode>()
      .size([width, height])
      .padding(2)
      .round(true)(root);

    // 색상 스케일 (CC 기반)
    const colorScale = d3.scaleLinear<string>()
      .domain([0, 5, 10, 20])
      .range(['#22c55e', '#eab308', '#f97316', '#ef4444']);

    // 셀 렌더링
    const cell = svg.selectAll('g')
      .data(root.leaves())
      .join('g')
      .attr('transform', d => `translate(${d.x0},${d.y0})`);

    // 배경 사각형
    cell.append('rect')
      .attr('width', d => d.x1 - d.x0)
      .attr('height', d => d.y1 - d.y0)
      .attr('fill', d => colorScale(d.data.cyclomatic || 0))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .attr('cursor', 'pointer')
      .on('click', (_, d) => onFileClick?.(d.data));

    // 파일명 텍스트
    cell.append('text')
      .attr('x', 4)
      .attr('y', 14)
      .attr('class', 'text-xs fill-white')
      .text(d => {
        const w = d.x1 - d.x0;
        return w > 40 ? d.data.name : '';
      });

    // CC 값 표시
    cell.append('text')
      .attr('x', 4)
      .attr('y', 28)
      .attr('class', 'text-xs fill-white/70')
      .text(d => {
        const w = d.x1 - d.x0;
        return w > 60 ? `CC:${d.data.cyclomatic}` : '';
      });
  }, [data, width, height]);

  return <svg ref={svgRef} width={width} height={height} />;
}
```

## 드릴다운 팝업

파일 클릭 시 함수별 상세 복잡도를 팝업으로 표시:

```
┌─────────────────────────────────────┐
│  main.py                            │
│  총 LOC: 245 | 평균 CC: 12         │
│                                     │
│  함수별 복잡도:                      │
│  ├── process_request()  CC:18  ⚠️   │
│  ├── validate_input()   CC:8        │
│  ├── handle_error()     CC:6        │
│  └── init_service()     CC:3   ✅   │
│                                     │
│  Halstead Difficulty: 42.3          │
│  Maintainability Index: 58          │
└─────────────────────────────────────┘
```

## 데이터 소스

- **Worker**: W7 (ComplexityMeterWorker)
- **도구**: Radon (Python) / Lizard (Multi-lang)
- **DB 테이블**: `analysis_results` (worker_name='complexity_meter')
- **API**: `GET /api/v1/jobs/{job_id}/analysis/complexity_meter`

## 관련 문서

- [[infrastructure/complexity-analysis/radon]] -- Radon CC/Halstead/MI
- [[infrastructure/complexity-analysis/lizard]] -- Lizard 멀티 언어 복잡도
- [[interface/d3-charts/MOC]] -- D3 차트 전체 목록
