import { useRef, useEffect } from 'react';
import * as d3 from 'd3';

type Signal = 'green' | 'yellow' | 'red';

export interface AuthenticityGaugeProps {
  score: number;
  signal: Signal;
  aiSuspicionPct: number;
}

const SIGNAL_COLORS: Record<Signal, string> = {
  green: '#22c55e',
  yellow: '#eab308',
  red: '#ef4444',
};

const SIGNAL_LABELS: Record<Signal, string> = {
  green: '양호',
  yellow: '주의',
  red: '위험',
};

export function AuthenticityGauge({
  score,
  signal,
  aiSuspicionPct,
}: AuthenticityGaugeProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 220;
    const height = 150;
    const cx = width / 2;
    const cy = height - 30;
    const outerRadius = 80;
    const innerRadius = 55;
    const startAngle = -Math.PI / 2;
    const endAngle = Math.PI / 2;

    svg.attr('width', width).attr('height', height);

    const g = svg.append('g').attr('transform', `translate(${cx},${cy})`);

    // Background arc (full semicircle)
    const bgArc = d3
      .arc()
      .innerRadius(innerRadius)
      .outerRadius(outerRadius)
      .startAngle(startAngle)
      .endAngle(endAngle)
      .cornerRadius(3);

    g.append('path')
      .attr('d', bgArc({} as d3.DefaultArcObject) as string)
      .attr('fill', '#e5e7eb');

    // Value arc
    const clampedScore = Math.max(0, Math.min(100, score));
    const valueEndAngle =
      startAngle + (clampedScore / 100) * (endAngle - startAngle);

    const valueArc = d3
      .arc()
      .innerRadius(innerRadius)
      .outerRadius(outerRadius)
      .startAngle(startAngle)
      .endAngle(valueEndAngle)
      .cornerRadius(3);

    g.append('path')
      .attr('d', valueArc({} as d3.DefaultArcObject) as string)
      .attr('fill', SIGNAL_COLORS[signal]);

    // Tick marks at 0, 25, 50, 75, 100
    const ticks = [0, 25, 50, 75, 100];
    for (const tick of ticks) {
      const tickAngle =
        startAngle + (tick / 100) * (endAngle - startAngle) - Math.PI;
      const x1 = Math.cos(tickAngle) * (outerRadius + 2);
      const y1 = Math.sin(tickAngle) * (outerRadius + 2);
      const x2 = Math.cos(tickAngle) * (outerRadius + 8);
      const y2 = Math.sin(tickAngle) * (outerRadius + 8);

      g.append('line')
        .attr('x1', x1)
        .attr('y1', y1)
        .attr('x2', x2)
        .attr('y2', y2)
        .attr('stroke', '#9ca3af')
        .attr('stroke-width', 1.5);

      const lx = Math.cos(tickAngle) * (outerRadius + 16);
      const ly = Math.sin(tickAngle) * (outerRadius + 16);

      g.append('text')
        .attr('x', lx)
        .attr('y', ly)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('font-size', 9)
        .attr('fill', '#9ca3af')
        .text(tick);
    }

    // Center score text
    g.append('text')
      .attr('x', 0)
      .attr('y', -12)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', 28)
      .attr('font-weight', 700)
      .attr('fill', SIGNAL_COLORS[signal])
      .text(clampedScore);

    // Signal label
    g.append('text')
      .attr('x', 0)
      .attr('y', 10)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', 12)
      .attr('font-weight', 600)
      .attr('fill', SIGNAL_COLORS[signal])
      .text(SIGNAL_LABELS[signal]);

    // AI suspicion text below gauge
    g.append('text')
      .attr('x', 0)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', 11)
      .attr('fill', '#6b7280')
      .text(`AI 의심률: ${Math.max(0, Math.min(100, aiSuspicionPct)).toFixed(1)}%`);
  }, [score, signal, aiSuspicionPct]);

  return (
    <div className="inline-block">
      <svg ref={svgRef} />
    </div>
  );
}
