/**
 * ContributionChart - Line chart for GitHub contribution data
 *
 * Shows 12-month contribution history with area fill.
 */

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

export function ContributionChart({
  data,
  labels = DEFAULT_LABELS,
  width = 400,
  height = 150,
  color = '#6366f1'
}: ContributionChartProps) {
  const padding = { top: 20, right: 20, bottom: 30, left: 40 }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  const maxValue = Math.max(...data, 10)
  const minValue = 0

  // Calculate point positions
  const points = data.map((value, index) => ({
    x: padding.left + (index / (data.length - 1)) * chartWidth,
    y: padding.top + chartHeight - ((value - minValue) / (maxValue - minValue)) * chartHeight
  }))

  // Generate path for line
  const linePath = points
    .map((p, i) => (i === 0 ? `M ${p.x} ${p.y}` : `L ${p.x} ${p.y}`))
    .join(' ')

  // Generate path for area fill
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${points[0].x} ${padding.top + chartHeight} Z`

  // Y-axis ticks
  const yTicks = [0, Math.round(maxValue / 2), maxValue]

  return (
    <svg width={width} height={height} className="overflow-visible">
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
              stroke="#e5e7eb"
              strokeWidth={1}
            />
            <text
              x={padding.left - 8}
              y={y}
              textAnchor="end"
              dominantBaseline="middle"
              className="fill-gray-400 text-xs"
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
            className="fill-gray-500 text-xs"
          >
            {label}
          </text>
        )
      })}
    </svg>
  )
}
