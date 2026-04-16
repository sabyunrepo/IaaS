import { useRef, useEffect } from 'react';
import * as d3 from 'd3';

export interface SkillHeatmapItem {
  name: string;
  level: number;
  jd_match?: boolean;
}

export interface SkillHeatmapProps {
  skills: SkillHeatmapItem[];
  width?: number;
  height?: number;
}

const LEVEL_LABELS = ['초급', '중급', '고급', '전문가'];
const CELL_SIZE = 36;
const CELL_GAP = 3;
const LABEL_MARGIN_LEFT = 60;
const LABEL_MARGIN_TOP = 30;

export function SkillHeatmap({
  skills,
  width = 600,
  height = 300,
}: SkillHeatmapProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (skills.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const cols = skills.length;
    const rows = LEVEL_LABELS.length;
    const computedWidth = Math.max(
      width,
      LABEL_MARGIN_LEFT + cols * (CELL_SIZE + CELL_GAP) + CELL_GAP + 10,
    );
    const computedHeight = Math.max(
      height,
      LABEL_MARGIN_TOP + rows * (CELL_SIZE + CELL_GAP) + CELL_GAP + 10,
    );

    svg.attr('width', computedWidth).attr('height', computedHeight);

    // Color scales
    const normalColor = d3
      .scaleLinear<string>()
      .domain([0, 1])
      .range(['#e0e7ff', '#3b82f6']);

    const matchColor = d3
      .scaleLinear<string>()
      .domain([0, 1])
      .range(['#d1fae5', '#059669']);

    const g = svg
      .append('g')
      .attr('transform', `translate(${LABEL_MARGIN_LEFT},${LABEL_MARGIN_TOP})`);

    // Y-axis labels (proficiency levels — top is highest)
    const reversedLabels = [...LEVEL_LABELS].reverse();
    for (let row = 0; row < rows; row++) {
      svg
        .append('text')
        .attr('x', LABEL_MARGIN_LEFT - 8)
        .attr(
          'y',
          LABEL_MARGIN_TOP + row * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2,
        )
        .attr('text-anchor', 'end')
        .attr('dominant-baseline', 'central')
        .attr('font-size', 10)
        .attr('fill', '#6b7280')
        .text(reversedLabels[row]);
    }

    // X-axis labels (skill names)
    for (let col = 0; col < cols; col++) {
      const skill = skills[col];
      svg
        .append('text')
        .attr(
          'x',
          LABEL_MARGIN_LEFT + col * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2,
        )
        .attr('y', LABEL_MARGIN_TOP - 8)
        .attr('text-anchor', 'middle')
        .attr('font-size', 10)
        .attr('font-weight', skill.jd_match ? 700 : 400)
        .attr('fill', skill.jd_match ? '#059669' : '#6b7280')
        .text(() => {
          const maxChars = Math.floor(CELL_SIZE / 5.5);
          return skill.name.length > maxChars
            ? skill.name.slice(0, maxChars - 1) + '\u2026'
            : skill.name;
        });
    }

    // Tooltip
    const tooltip = d3
      .select('body')
      .append('div')
      .attr('class', 'jittda-skill-tooltip')
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

    // Draw cells
    for (let col = 0; col < cols; col++) {
      const skill = skills[col];
      // Normalize level: assume 1-4 scale (or 0-100)
      const normalizedLevel =
        skill.level > 4 ? skill.level / 100 : skill.level / 4;
      const isMatch = skill.jd_match ?? false;
      const colorFn = isMatch ? matchColor : normalColor;

      for (let row = 0; row < rows; row++) {
        // Row 0 = top = level 4, Row 3 = bottom = level 1
        const levelThreshold = (rows - row) / rows;
        const isFilled = normalizedLevel >= levelThreshold;
        const intensity = isFilled ? normalizedLevel : 0;

        const x = col * (CELL_SIZE + CELL_GAP);
        const y = row * (CELL_SIZE + CELL_GAP);

        g.append('rect')
          .attr('x', x)
          .attr('y', y)
          .attr('width', CELL_SIZE)
          .attr('height', CELL_SIZE)
          .attr('rx', 4)
          .attr('fill', isFilled ? colorFn(intensity) : '#f3f4f6')
          .attr('stroke', isMatch && isFilled ? '#059669' : '#e5e7eb')
          .attr('stroke-width', isMatch && isFilled ? 1.5 : 1)
          .style('cursor', 'pointer')
          .on('mouseover', () => {
            const matchLabel = isMatch ? ' [JD 매칭]' : '';
            const levelLabel = LEVEL_LABELS[rows - row - 1];
            tooltip
              .style('visibility', 'visible')
              .html(
                `<strong>${skill.name}</strong>${matchLabel}<br/>` +
                  `${levelLabel}: ${isFilled ? '충족' : '미달'}<br/>` +
                  `숙련도: ${skill.level > 4 ? skill.level : Math.round(normalizedLevel * 100)}`,
              );
          })
          .on('mousemove', (event: MouseEvent) => {
            tooltip
              .style('top', `${event.pageY - 10}px`)
              .style('left', `${event.pageX + 12}px`);
          })
          .on('mouseout', () => {
            tooltip.style('visibility', 'hidden');
          });
      }
    }

    // Legend
    const legendY = computedHeight - 20;
    const legendItems = [
      { label: '일반 스킬', color: '#3b82f6' },
      { label: 'JD 매칭', color: '#059669' },
    ];

    for (let i = 0; i < legendItems.length; i++) {
      const lx = LABEL_MARGIN_LEFT + i * 100;
      svg
        .append('rect')
        .attr('x', lx)
        .attr('y', legendY)
        .attr('width', 12)
        .attr('height', 12)
        .attr('rx', 2)
        .attr('fill', legendItems[i].color);

      svg
        .append('text')
        .attr('x', lx + 16)
        .attr('y', legendY + 6)
        .attr('dominant-baseline', 'central')
        .attr('font-size', 10)
        .attr('fill', '#6b7280')
        .text(legendItems[i].label);
    }

    return () => {
      tooltip.remove();
    };
  }, [skills, width, height]);

  return (
    <div className="inline-block overflow-x-auto">
      <svg ref={svgRef} />
    </div>
  );
}
