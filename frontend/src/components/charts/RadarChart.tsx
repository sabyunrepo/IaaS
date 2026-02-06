/**
 * RadarChart - 5-axis radar chart for candidate vs required comparison
 *
 * Uses pure SVG for rendering without external dependencies.
 */
import { useTranslation } from 'react-i18next'

interface RadarChartProps {
  /** Candidate scores (5 values, 0-100) */
  candidateData: number[]
  /** Required scores (5 values, 0-100) */
  requiredData: number[]
  /** Labels for each axis */
  labels?: string[]
  /** Chart size in pixels */
  size?: number
}

export function RadarChart({
  candidateData,
  requiredData,
  labels,
  size = 300
}: RadarChartProps) {
  const { t } = useTranslation()
  const resolvedLabels = labels ?? [
    t('deep_role_fit'),
    t('deep_technical'),
    t('deep_execution'),
    t('deep_communication'),
    t('deep_code_quality'),
  ]
  const center = size / 2
  const maxRadius = size * 0.4
  const numAxes = 5
  const angleStep = (2 * Math.PI) / numAxes
  const startAngle = -Math.PI / 2 // Start from top

  // Calculate point position on radar
  const getPoint = (value: number, axisIndex: number): { x: number; y: number } => {
    const angle = startAngle + axisIndex * angleStep
    const radius = (value / 100) * maxRadius
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle)
    }
  }

  // Generate polygon points string
  const getPolygonPoints = (data: number[]): string => {
    return data
      .map((value, i) => {
        const point = getPoint(value, i)
        return `${point.x},${point.y}`
      })
      .join(' ')
  }

  // Generate grid lines
  const gridLevels = [20, 40, 60, 80, 100]

  return (
    <div className="relative w-full max-w-[320px] mx-auto">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-auto">
        {/* Background grid circles */}
        {gridLevels.map((level) => {
          const radius = (level / 100) * maxRadius
          const points = Array.from({ length: numAxes }, (_, i) => {
            const angle = startAngle + i * angleStep
            return `${center + radius * Math.cos(angle)},${center + radius * Math.sin(angle)}`
          }).join(' ')
          return (
            <polygon
              key={level}
              points={points}
              fill="none"
              stroke="#e5e7eb"
              strokeWidth={1}
            />
          )
        })}

        {/* Axis lines */}
        {Array.from({ length: numAxes }, (_, i) => {
          const angle = startAngle + i * angleStep
          const endX = center + maxRadius * Math.cos(angle)
          const endY = center + maxRadius * Math.sin(angle)
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={endX}
              y2={endY}
              stroke="#d1d5db"
              strokeWidth={1}
            />
          )
        })}

        {/* Required polygon (background) */}
        <polygon
          points={getPolygonPoints(requiredData)}
          fill="rgba(99, 102, 241, 0.2)"
          stroke="#6366f1"
          strokeWidth={2}
          strokeDasharray="4 2"
          style={{ transition: 'all 0.4s ease' }}
        />

        {/* Candidate polygon (foreground) */}
        <polygon
          points={getPolygonPoints(candidateData)}
          fill="rgba(16, 185, 129, 0.3)"
          stroke="#10b981"
          strokeWidth={2}
          style={{ transition: 'all 0.4s ease' }}
        />

        {/* Data points with hover tooltip */}
        {candidateData.map((value, i) => {
          const point = getPoint(value, i)
          return (
            <g key={i}>
              {/* Larger invisible hit area for hover */}
              <circle
                cx={point.x}
                cy={point.y}
                r={10}
                fill="transparent"
                style={{ cursor: 'pointer' }}
              >
                <title>{resolvedLabels[i]}: {value} ({t('radar_required')}: {requiredData[i]})</title>
              </circle>
              <circle
                cx={point.x}
                cy={point.y}
                r={4}
                fill="#10b981"
                stroke="white"
                strokeWidth={2}
                style={{ transition: 'r 0.2s ease' }}
                className="hover:r-6"
              >
                <title>{resolvedLabels[i]}: {value} ({t('radar_required')}: {requiredData[i]})</title>
              </circle>
            </g>
          )
        })}

        {/* Labels */}
        {resolvedLabels.map((label, i) => {
          const angle = startAngle + i * angleStep
          const labelRadius = maxRadius + 25
          const x = center + labelRadius * Math.cos(angle)
          const y = center + labelRadius * Math.sin(angle)

          // Adjust text anchor based on position
          let textAnchor: 'start' | 'middle' | 'end' = 'middle'
          if (Math.cos(angle) > 0.3) textAnchor = 'start'
          else if (Math.cos(angle) < -0.3) textAnchor = 'end'

          return (
            <text
              key={i}
              x={x}
              y={y}
              textAnchor={textAnchor}
              dominantBaseline="middle"
              className="fill-gray-600 text-xs font-medium"
            >
              {label}
            </text>
          )
        })}
      </svg>

      {/* Legend */}
      <div className="flex justify-center gap-6 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-emerald-500"></div>
          <span className="text-xs text-gray-600">{t('radar_candidate_legend')}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-indigo-500" style={{ borderStyle: 'dashed' }}></div>
          <span className="text-xs text-gray-600">{t('radar_required_legend')}</span>
        </div>
      </div>
    </div>
  )
}
