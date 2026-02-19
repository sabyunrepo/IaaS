import { useRef, useEffect } from 'react';
import * as d3 from 'd3';

export interface TreemapNode {
  name: string;
  size: number;
  maintainability: number;
}

export interface ComplexityTreemapProps {
  data: TreemapNode[];
  width?: number;
  height?: number;
}

function maintainabilityColor(value: number): string {
  // 0 (red) → 50 (yellow) → 100 (green)
  const clamped = Math.max(0, Math.min(100, value));
  const scale = d3
    .scaleLinear<string>()
    .domain([0, 50, 100])
    .range(['#ef4444', '#eab308', '#22c55e']);
  return scale(clamped);
}

export function ComplexityTreemap({
  data,
  width = 500,
  height = 300,
}: ComplexityTreemapProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (data.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    svg.attr('width', width).attr('height', height);

    const hierarchy = d3
      .hierarchy<{ children: TreemapNode[] }>({
        children: data,
      } as { children: TreemapNode[] })
      .sum((d) => ('size' in d ? (d as unknown as TreemapNode).size : 0));

    const treemapLayout = d3
      .treemap<{ children: TreemapNode[] }>()
      .size([width, height])
      .padding(2)
      .round(true);

    const root = treemapLayout(hierarchy);

    const tooltip = d3
      .select('body')
      .append('div')
      .attr('class', 'jittda-treemap-tooltip')
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

    const leaves = root.leaves();

    const cells = svg
      .selectAll('g')
      .data(leaves)
      .join('g')
      .attr('transform', (d) => `translate(${d.x0},${d.y0})`);

    cells
      .append('rect')
      .attr('width', (d) => Math.max(0, d.x1 - d.x0))
      .attr('height', (d) => Math.max(0, d.y1 - d.y0))
      .attr('fill', (d) => {
        const node = d.data as unknown as TreemapNode;
        return maintainabilityColor(node.maintainability);
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .attr('rx', 2)
      .style('cursor', 'pointer')
      .on('mouseover', (_event, d) => {
        const node = d.data as unknown as TreemapNode;
        tooltip
          .style('visibility', 'visible')
          .html(
            `<strong>${node.name}</strong><br/>복잡도: ${node.size}<br/>유지보수성: ${node.maintainability}`,
          );
      })
      .on('mousemove', (event) => {
        tooltip
          .style('top', `${event.pageY - 10}px`)
          .style('left', `${event.pageX + 12}px`);
      })
      .on('mouseout', () => {
        tooltip.style('visibility', 'hidden');
      });

    // File name labels (only if cell is large enough)
    cells
      .append('text')
      .attr('x', 4)
      .attr('y', 14)
      .attr('font-size', 11)
      .attr('font-weight', 500)
      .attr('fill', '#fff')
      .attr('pointer-events', 'none')
      .text((d) => {
        const node = d.data as unknown as TreemapNode;
        const cellWidth = d.x1 - d.x0;
        const cellHeight = d.y1 - d.y0;
        if (cellWidth < 40 || cellHeight < 20) return '';
        const maxChars = Math.floor(cellWidth / 7);
        return node.name.length > maxChars
          ? node.name.slice(0, maxChars - 1) + '\u2026'
          : node.name;
      });

    return () => {
      tooltip.remove();
    };
  }, [data, width, height]);

  return (
    <div className="inline-block overflow-hidden rounded-lg">
      <svg ref={svgRef} />
    </div>
  );
}
