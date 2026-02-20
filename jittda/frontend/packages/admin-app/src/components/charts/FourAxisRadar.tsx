import { useRef, useEffect } from 'react';
import * as d3 from 'd3';

type Signal = 'green' | 'yellow' | 'red';

interface AxisData {
  score: number;
  signal: Signal;
}

export interface FourAxisRadarProps {
  data: {
    logic: AxisData;
    mastery: AxisData;
    stability: AxisData;
    authenticity: AxisData;
  };
  size?: number;
}

const SIGNAL_COLORS: Record<Signal, string> = {
  green: '#22c55e',
  yellow: '#eab308',
  red: '#ef4444',
};

const AXES = [
  { key: 'logic' as const, label: '논리력' },
  { key: 'mastery' as const, label: '전문성' },
  { key: 'stability' as const, label: '안정성' },
  { key: 'authenticity' as const, label: '진정성' },
];

const GRID_LEVELS = [20, 40, 60, 80, 100];

export function FourAxisRadar({ data, size = 300 }: FourAxisRadarProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = 40;
    const radius = (size - margin * 2) / 2;
    const cx = size / 2;
    const cy = size / 2;
    const angleSlice = (Math.PI * 2) / AXES.length;

    const g = svg
      .attr('width', size)
      .attr('height', size)
      .append('g')
      .attr('transform', `translate(${cx},${cy})`);

    // Grid circles
    for (const level of GRID_LEVELS) {
      const r = (level / 100) * radius;
      g.append('circle')
        .attr('r', r)
        .attr('fill', 'none')
        .attr('stroke', '#e5e7eb')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', level < 100 ? '3,3' : 'none');
    }

    // Axis lines + labels
    for (let i = 0; i < AXES.length; i++) {
      const angle = angleSlice * i - Math.PI / 2;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius;

      g.append('line')
        .attr('x1', 0)
        .attr('y1', 0)
        .attr('x2', x)
        .attr('y2', y)
        .attr('stroke', '#d1d5db')
        .attr('stroke-width', 1);

      const labelOffset = 18;
      const lx = Math.cos(angle) * (radius + labelOffset);
      const ly = Math.sin(angle) * (radius + labelOffset);

      g.append('text')
        .attr('x', lx)
        .attr('y', ly)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('font-size', 12)
        .attr('font-weight', 600)
        .attr('fill', '#374151')
        .text(AXES[i].label);
    }

    // Data polygon
    const points: [number, number][] = AXES.map((axis, i) => {
      const angle = angleSlice * i - Math.PI / 2;
      const value = data[axis.key].score;
      const r = (Math.max(0, Math.min(100, value)) / 100) * radius;
      return [Math.cos(angle) * r, Math.sin(angle) * r];
    });

    const lineGenerator = d3
      .line<[number, number]>()
      .x((d) => d[0])
      .y((d) => d[1])
      .curve(d3.curveLinearClosed);

    g.append('path')
      .datum(points)
      .attr('d', lineGenerator)
      .attr('fill', '#3b82f6')
      .attr('fill-opacity', 0.15)
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 2);

    // Data points with signal colors + score labels
    for (let i = 0; i < AXES.length; i++) {
      const axis = AXES[i];
      const value = data[axis.key].score;
      const signal = data[axis.key].signal;
      const angle = angleSlice * i - Math.PI / 2;
      const r = (Math.max(0, Math.min(100, value)) / 100) * radius;
      const px = Math.cos(angle) * r;
      const py = Math.sin(angle) * r;

      g.append('circle')
        .attr('cx', px)
        .attr('cy', py)
        .attr('r', 5)
        .attr('fill', SIGNAL_COLORS[signal])
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);

      // Score label offset: push slightly outward from center
      const labelR = r + 14;
      const slx = Math.cos(angle) * labelR;
      const sly = Math.sin(angle) * labelR;

      g.append('text')
        .attr('x', slx)
        .attr('y', sly)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('font-size', 11)
        .attr('font-weight', 500)
        .attr('fill', SIGNAL_COLORS[signal])
        .text(value);
    }
  }, [data, size]);

  return (
    <div className="inline-block">
      <svg ref={svgRef} />
    </div>
  );
}
