import { useRef, useEffect } from 'react';
import * as d3 from 'd3';

export interface HeatmapCell {
  filename: string;
  ai_suspicion: number;
}

export interface AICodeHeatmapProps {
  data: HeatmapCell[];
  width?: number;
  height?: number;
}

const CELL_SIZE = 40;
const CELL_GAP = 3;
const LABEL_HEIGHT = 16;

export function AICodeHeatmap({
  data,
  width = 500,
  height = 300,
}: AICodeHeatmapProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const colorScale = d3
      .scaleLinear<string>()
      .domain([0, 0.5, 1])
      .range(['#3b82f6', '#a78bfa', '#ef4444']);

    // Compute grid layout
    const cols = Math.max(
      1,
      Math.floor((width - CELL_GAP) / (CELL_SIZE + CELL_GAP)),
    );
    const rows = Math.ceil(data.length / cols);
    const computedHeight = Math.max(
      height,
      rows * (CELL_SIZE + CELL_GAP + LABEL_HEIGHT) + CELL_GAP + 40,
    );

    svg.attr('width', width).attr('height', computedHeight);

    // Legend
    const legendWidth = 200;
    const legendHeight = 12;
    const legendX = width - legendWidth - 10;
    const legendY = 8;

    const defs = svg.append('defs');
    const gradient = defs
      .append('linearGradient')
      .attr('id', 'ai-heatmap-gradient');

    gradient
      .append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#3b82f6');
    gradient
      .append('stop')
      .attr('offset', '50%')
      .attr('stop-color', '#a78bfa');
    gradient
      .append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#ef4444');

    svg
      .append('rect')
      .attr('x', legendX)
      .attr('y', legendY)
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .attr('rx', 3)
      .attr('fill', 'url(#ai-heatmap-gradient)');

    svg
      .append('text')
      .attr('x', legendX - 4)
      .attr('y', legendY + legendHeight / 2)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'central')
      .attr('font-size', 10)
      .attr('fill', '#6b7280')
      .text('Human');

    svg
      .append('text')
      .attr('x', legendX + legendWidth + 4)
      .attr('y', legendY + legendHeight / 2)
      .attr('text-anchor', 'start')
      .attr('dominant-baseline', 'central')
      .attr('font-size', 10)
      .attr('fill', '#6b7280')
      .text('AI');

    const gridOffsetY = legendY + legendHeight + 16;

    // Tooltip
    const tooltip = d3
      .select('body')
      .append('div')
      .attr('class', 'jittda-heatmap-tooltip')
      .style('position', 'absolute')
      .style('visibility', 'hidden')
      .style('background', '#1f2937')
      .style('color', '#f9fafb')
      .style('padding', '6px 10px')
      .style('border-radius', '6px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', '9999')
      .style('white-space', 'nowrap');

    // Grid cells
    const g = svg.append('g').attr('transform', `translate(0,${gridOffsetY})`);

    const cellGroups = g
      .selectAll('g')
      .data(data)
      .join('g')
      .attr('transform', (_d, i) => {
        const col = i % cols;
        const row = Math.floor(i / cols);
        const x = col * (CELL_SIZE + CELL_GAP) + CELL_GAP;
        const y = row * (CELL_SIZE + CELL_GAP + LABEL_HEIGHT) + CELL_GAP;
        return `translate(${x},${y})`;
      });

    cellGroups
      .append('rect')
      .attr('width', CELL_SIZE)
      .attr('height', CELL_SIZE)
      .attr('rx', 4)
      .attr('fill', (d) => colorScale(Math.max(0, Math.min(1, d.ai_suspicion))))
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseover', (_event, d) => {
        const pct = (d.ai_suspicion * 100).toFixed(1);
        tooltip
          .style('visibility', 'visible')
          .html(`<strong>${d.filename}</strong><br/>AI 의심률: ${pct}%`);
      })
      .on('mousemove', (event) => {
        tooltip
          .style('top', `${event.pageY - 10}px`)
          .style('left', `${event.pageX + 12}px`);
      })
      .on('mouseout', () => {
        tooltip.style('visibility', 'hidden');
      });

    // Percentage text inside cell
    cellGroups
      .append('text')
      .attr('x', CELL_SIZE / 2)
      .attr('y', CELL_SIZE / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', 10)
      .attr('font-weight', 600)
      .attr('fill', '#fff')
      .attr('pointer-events', 'none')
      .text((d) => `${Math.round(d.ai_suspicion * 100)}%`);

    // Filename label below cell
    cellGroups
      .append('text')
      .attr('x', CELL_SIZE / 2)
      .attr('y', CELL_SIZE + 12)
      .attr('text-anchor', 'middle')
      .attr('font-size', 9)
      .attr('fill', '#6b7280')
      .attr('pointer-events', 'none')
      .text((d) => {
        const maxChars = Math.floor(CELL_SIZE / 5.5);
        return d.filename.length > maxChars
          ? d.filename.slice(0, maxChars - 1) + '\u2026'
          : d.filename;
      });

    return () => {
      tooltip.remove();
    };
  }, [data, width, height]);

  return (
    <div className="inline-block overflow-hidden">
      <svg ref={svgRef} />
    </div>
  );
}
