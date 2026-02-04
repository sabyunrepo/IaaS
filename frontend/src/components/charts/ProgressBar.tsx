/**
 * ProgressBar - Animated progress bar for Engineering DNA display
 */

interface ProgressBarProps {
  /** Label text */
  label: string
  /** Value (0-100) */
  value: number
  /** Display text (e.g., "82%", "우수", "미확인") */
  display: string
  /** Color variant */
  color: 'emerald' | 'blue' | 'amber' | 'red' | 'gray'
  /** Optional note text */
  note?: string
  /** Optional tooltip text */
  tooltip?: string
}

const colorMap = {
  emerald: {
    bg: 'bg-emerald-100',
    fill: 'bg-emerald-500',
    text: 'text-emerald-700',
    border: 'border-emerald-200'
  },
  blue: {
    bg: 'bg-blue-100',
    fill: 'bg-blue-500',
    text: 'text-blue-700',
    border: 'border-blue-200'
  },
  amber: {
    bg: 'bg-amber-100',
    fill: 'bg-amber-500',
    text: 'text-amber-700',
    border: 'border-amber-200'
  },
  red: {
    bg: 'bg-red-100',
    fill: 'bg-red-500',
    text: 'text-red-700',
    border: 'border-red-200'
  },
  gray: {
    bg: 'bg-gray-100',
    fill: 'bg-gray-400',
    text: 'text-gray-600',
    border: 'border-gray-200'
  }
}

export function ProgressBar({
  label,
  value,
  display,
  color,
  note,
  tooltip
}: ProgressBarProps) {
  const colors = colorMap[color]

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          {tooltip && (
            <span className="group relative">
              <svg
                className="w-4 h-4 text-gray-400 cursor-help"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="invisible group-hover:visible absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-48 p-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg z-10">
                {tooltip}
              </span>
            </span>
          )}
        </div>
        <span className={`text-sm font-semibold ${colors.text}`}>{display}</span>
      </div>

      <div className={`h-2.5 rounded-full ${colors.bg} overflow-hidden`}>
        <div
          className={`h-full rounded-full ${colors.fill} transition-all duration-500 ease-out`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>

      {note && (
        <p className={`text-xs ${colors.text} ${colors.bg} ${colors.border} border rounded-md px-2 py-1`}>
          ℹ️ {note}
        </p>
      )}
    </div>
  )
}

/**
 * ProgressBarGroup - Multiple progress bars in a card
 */
interface ProgressBarGroupProps {
  title: string
  items: Array<{
    label: string
    value: number
    display: string
    color: 'emerald' | 'blue' | 'amber' | 'red' | 'gray'
    note?: string
    tooltip?: string
  }>
}

export function ProgressBarGroup({ title, items }: ProgressBarGroupProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <svg
          className="w-5 h-5 text-indigo-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
        {title}
      </h3>
      <div className="space-y-4">
        {items.map((item, index) => (
          <ProgressBar key={index} {...item} />
        ))}
      </div>
    </div>
  )
}
