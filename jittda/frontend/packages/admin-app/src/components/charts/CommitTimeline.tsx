import { useRef, useEffect } from 'react';
import * as d3 from 'd3';

export interface CommitTimelineEntry {
  date: string;
  count: number;
  ai_suspected?: boolean;
}

export interface CommitTimelineProps {
  commits: CommitTimelineEntry[];
  width?: number;
  height?: number;
}

const MARGIN = { top: 20, right: 20, bottom: 40, left: 40 };

export function CommitTimeline({
  commits,
  width = 600,
  height = 200,
}: CommitTimelineProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (commits.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    svg.attr('width', width).attr('height', height);

    const innerWidth = width - MARGIN.left - MARGIN.right;
    const innerHeight = height - MARGIN.top - MARGIN.bottom;

    const g = svg
      .append('g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    // Parse dates
    const parsedData = commits.map((d) => ({
      ...d,
      parsedDate: new Date(d.date),
    }));

    // Scales
    const xExtent = d3.extent(parsedData, (d) => d.parsedDate) as [Date, Date];
    const xScale = d3
      .scaleTime()
      .domain(xExtent)
      .range([0, innerWidth]);

    const maxCount = d3.max(parsedData, (d) => d.count) ?? 1;
    const yScale = d3
      .scaleLinear()
      .domain([0, maxCount * 1.1])
      .range([innerHeight, 0]);

    // X axis
    const xAxis = d3
      .axisBottom(xScale)
      .ticks(Math.min(parsedData.length, 8))
      .tickFormat((d) => d3.timeFormat('%m/%d')(d as Date));

    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis)
      .selectAll('text')
      .attr('font-size', 10)
      .attr('fill', '#6b7280');

    g.selectAll('.domain').attr('stroke', '#d1d5db');
    g.selectAll('.tick line').attr('stroke', '#e5e7eb');

    // Y axis
    const yAxis = d3.axisLeft(yScale).ticks(5).tickSize(-innerWidth);

    const yAxisGroup = g.append('g').call(yAxis);
    yAxisGroup.selectAll('text').attr('font-size', 10).attr('fill', '#6b7280');
    yAxisGroup.selectAll('.domain').remove();
    yAxisGroup
      .selectAll('.tick line')
      .attr('stroke', '#f3f4f6')
      .attr('stroke-dasharray', '3,3');

    // Area fill for normal commits
    const area = d3
      .area<(typeof parsedData)[number]>()
      .x((d) => xScale(d.parsedDate))
      .y0(innerHeight)
      .y1((d) => yScale(d.count))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(parsedData)
      .attr('d', area)
      .attr('fill', '#3b82f6')
      .attr('fill-opacity', 0.08);

    // Line
    const line = d3
      .line<(typeof parsedData)[number]>()
      .x((d) => xScale(d.parsedDate))
      .y((d) => yScale(d.count))
      .curve(d3.curveMonotoneX);

    g.append('path')
      .datum(parsedData)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', '#3b82f6')
      .attr('stroke-width', 2);

    // Tooltip
    const tooltip = d3
      .select('body')
      .append('div')
      .attr('class', 'jittda-commit-tooltip')
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

    // Data points
    g.selectAll('circle')
      .data(parsedData)
      .join('circle')
      .attr('cx', (d) => xScale(d.parsedDate))
      .attr('cy', (d) => yScale(d.count))
      .attr('r', 4)
      .attr('fill', (d) => (d.ai_suspected ? '#ef4444' : '#3b82f6'))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('mouseover', (_event, d) => {
        const dateStr = d3.timeFormat('%Y-%m-%d')(d.parsedDate);
        const aiLabel = d.ai_suspected ? '<br/><span style="color:#fca5a5">AI 의심</span>' : '';
        tooltip
          .style('visibility', 'visible')
          .html(`<strong>${dateStr}</strong><br/>커밋: ${d.count}건${aiLabel}`);
      })
      .on('mousemove', (event: MouseEvent) => {
        tooltip
          .style('top', `${event.pageY - 10}px`)
          .style('left', `${event.pageX + 12}px`);
      })
      .on('mouseout', () => {
        tooltip.style('visibility', 'hidden');
      });

    // Legend
    const legendData = [
      { label: '일반 커밋', color: '#3b82f6' },
      { label: 'AI 의심', color: '#ef4444' },
    ];

    const legend = svg
      .append('g')
      .attr('transform', `translate(${width - 160},${8})`);

    legendData.forEach((item, i) => {
      const lg = legend
        .append('g')
        .attr('transform', `translate(${i * 80},0)`);

      lg.append('circle')
        .attr('cx', 0)
        .attr('cy', 0)
        .attr('r', 4)
        .attr('fill', item.color);

      lg.append('text')
        .attr('x', 8)
        .attr('y', 0)
        .attr('dominant-baseline', 'central')
        .attr('font-size', 10)
        .attr('fill', '#6b7280')
        .text(item.label);
    });

    return () => {
      tooltip.remove();
    };
  }, [commits, width, height]);

  return (
    <div className="inline-block overflow-x-auto">
      <svg ref={svgRef} />
    </div>
  );
}
