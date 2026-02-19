/**
 * ContributionChart - Line chart for GitHub contribution data
 *
 * Shows 12-month contribution history with area fill.
 */
import { memo, useMemo } from 'react'

interface ContributionChartProps {
  /** Monthly contribution counts (12 values) */
  data: number[]
  /** Optional month labels */
  labels?: string[]
  /** Chart width */
  width?: number
  /** Chart height */
  height?: number
  /** Line color */
  color?: string
}

const DEFAULT_LABELS = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]

export const ContributionChart = memo(function ContributionChart({
  data,
  labels = DEFAULT_LABELS,
  width = 400,
  height = 150,
  color = '#2db882'
}: ContributionChartProps) {
  const padding = { top: 20, right: 20, bottom: 30, left: 40 }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  const { points, linePath, areaPath, yTicks, maxValue } = useMemo(() => {
    const max = Math.max(...data, 10)
    const min = 0

    const pts = data.map((value, index) => ({
      x: padding.left + (index / (data.length - 1)) * chartWidth,
      y: padding.top + chartHeight - ((value - min) / (max - min)) * chartHeight
    }))

    const line = pts
      .map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`))
      .join(' ')

    const area = `${line} L ${pts[pts.length - 1].x} ${padding.top + chartHeight} L ${pts[0].x} ${padding.top + chartHeight} Z`

    return {
      points: pts,
      linePath: line,
      areaPath: area,
      yTicks: [0, Math.round(max / 2), max],
      maxValue: max,
    }
  }, [data, padding.left, padding.top, chartWidth, chartHeight])

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto overflow-visible">
      {/* Grid lines */}
      {yTicks.map((tick) => {
        const y = padding.top + chartHeight - (tick / maxValue) * chartHeight
        return (
          <g key={tick}>
            <line
              x1={padding.left}
              y1={y}
              x2={width - padding.right}
              y2={y}
              stroke="#ccd4e0"
              strokeWidth={1}
            />
            <text
              x={padding.left - 8}
              y={y}
              textAnchor="end"
              dominantBaseline="middle"
              className="fill-ink-400 text-xs"
            >
              {tick}
            </text>
          </g>
        )
      })}

      {/* Area fill */}
      <path
        d={areaPath}
        fill={`${color}20`}
      />

      {/* Line */}
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Data points */}
      {points.map((point, index) => (
        <g key={index}>
          <circle
            cx={point.x}
            cy={point.y}
            r={4}
            fill="white"
            stroke={color}
            strokeWidth={2}
          />
          {/* Tooltip on hover - value */}
          <title>{`${labels[index]}: ${data[index]}`}</title>
        </g>
      ))}

      {/* X-axis labels (show every other month for space) */}
      {labels.map((label, index) => {
        if (index % 2 !== 0 && index !== labels.length - 1) return null
        const x = padding.left + (index / (data.length - 1)) * chartWidth
        return (
          <text
            key={index}
            x={x}
            y={height - 8}
            textAnchor="middle"
            className="fill-ink-500 text-xs"
          >
            {label}
          </text>
        )
      })}
    </svg>
  )
})
