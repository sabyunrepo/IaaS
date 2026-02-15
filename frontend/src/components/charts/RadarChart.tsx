/**
 * RadarChart - 5-axis radar chart for candidate vs required comparison
 *
 * Uses pure SVG for rendering without external dependencies.
 */
import { memo, useMemo } from 'react'
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

export const RadarChart = memo(function RadarChart({
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

  // Memoize expensive geometry calculations
  const geometry = useMemo(() => {
    const getPoint = (value: number, axisIndex: number) => {
      const angle = startAngle + axisIndex * angleStep
      const radius = (value / 100) * maxRadius
      return {
        x: center + radius * Math.cos(angle),
        y: center + radius * Math.sin(angle)
      }
    }

    const getPolygonPoints = (data: number[]): string =>
      data.map((value, i) => {
        const point = getPoint(value, i)
        return `${point.x},${point.y}`
      }).join(' ')

    const gridLevels = [20, 40, 60, 80, 100]
    const gridPolygons = gridLevels.map((level) => {
      const radius = (level / 100) * maxRadius
      const points = Array.from({ length: numAxes }, (_, i) => {
        const angle = startAngle + i * angleStep
        return `${center + radius * Math.cos(angle)},${center + radius * Math.sin(angle)}`
      }).join(' ')
      return { level, points }
    })

    const axisLines = Array.from({ length: numAxes }, (_, i) => {
      const angle = startAngle + i * angleStep
      return {
        index: i,
        endX: center + maxRadius * Math.cos(angle),
        endY: center + maxRadius * Math.sin(angle),
      }
    })

    const candidatePoints = candidateData.map((value, i) => ({
      ...getPoint(value, i),
      value,
      index: i,
    }))

    const labelPositions = Array.from({ length: numAxes }, (_, i) => {
      const angle = startAngle + i * angleStep
      const labelRadius = maxRadius + 25
      let textAnchor: 'start' | 'middle' | 'end' = 'middle'
      if (Math.cos(angle) > 0.3) textAnchor = 'start'
      else if (Math.cos(angle) < -0.3) textAnchor = 'end'
      return {
        x: center + labelRadius * Math.cos(angle),
        y: center + labelRadius * Math.sin(angle),
        textAnchor,
      }
    })

    return {
      gridPolygons,
      axisLines,
      requiredPolygon: getPolygonPoints(requiredData),
      candidatePolygon: getPolygonPoints(candidateData),
      candidatePoints,
      labelPositions,
    }
  }, [candidateData, requiredData, size, center, maxRadius, angleStep, startAngle])

  return (
    <div className="relative w-full max-w-[320px] mx-auto">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-auto">
        {/* Background grid circles */}
        {geometry.gridPolygons.map(({ level, points }) => (
          <polygon
            key={level}
            points={points}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={1}
          />
        ))}

        {/* Axis lines */}
        {geometry.axisLines.map(({ index, endX, endY }) => (
          <line
            key={index}
            x1={center}
            y1={center}
            x2={endX}
            y2={endY}
            stroke="#d1d5db"
            strokeWidth={1}
          />
        ))}

        {/* Required polygon (background) */}
        <polygon
          points={geometry.requiredPolygon}
          fill="rgba(27, 58, 92, 0.2)"
          stroke="#1B3A5C"
          strokeWidth={2}
          strokeDasharray="4 2"
          style={{ transition: 'all 0.4s ease' }}
        />

        {/* Candidate polygon (foreground) */}
        <polygon
          points={geometry.candidatePolygon}
          fill="rgba(16, 185, 129, 0.3)"
          stroke="#10b981"
          strokeWidth={2}
          style={{ transition: 'all 0.4s ease' }}
        />

        {/* Data points with hover tooltip */}
        {geometry.candidatePoints.map(({ x, y, value, index: i }) => (
          <g key={i}>
            <circle
              cx={x}
              cy={y}
              r={10}
              fill="transparent"
              style={{ cursor: 'pointer' }}
            >
              <title>{resolvedLabels[i]}: {value} ({t('radar_required')}: {requiredData[i]})</title>
            </circle>
            <circle
              cx={x}
              cy={y}
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
        ))}

        {/* Labels */}
        {resolvedLabels.map((label, i) => (
          <text
            key={i}
            x={geometry.labelPositions[i].x}
            y={geometry.labelPositions[i].y}
            textAnchor={geometry.labelPositions[i].textAnchor}
            dominantBaseline="middle"
            className="fill-gray-600 text-xs font-medium"
          >
            {label}
          </text>
        ))}
      </svg>

      {/* Legend */}
      <div className="flex justify-center gap-6 mt-4">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-emerald-500"></div>
          <span className="text-xs text-gray-600">{t('radar_candidate_legend')}</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-navy-700" style={{ borderStyle: 'dashed' }}></div>
          <span className="text-xs text-gray-600">{t('radar_required_legend')}</span>
        </div>
      </div>
    </div>
  )
})
