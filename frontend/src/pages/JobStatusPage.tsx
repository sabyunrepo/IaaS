import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useJob } from '../hooks/useJob'
import { useWebSocket } from '../hooks/useWebSocket'

const PHASE_KEYS: Record<string, string> = {
  pending: 'phase_pending',
  enriching: 'phase_enriching',
  planning: 'phase_planning',
  analyzing: 'phase_analyzing',
  generating: 'phase_generating',
  reviewing: 'phase_reviewing',
  completed: 'phase_completed',
  failed: 'phase_failed',
}

// Phase configuration with colors and icons
const PHASE_CONFIG: Record<string, { color: string; bgColor: string; icon: string }> = {
  pending: { color: 'text-gray-600', bgColor: 'bg-gray-100', icon: 'clock' },
  enriching: { color: 'text-blue-600', bgColor: 'bg-blue-100', icon: 'search' },
  planning: { color: 'text-brand-600', bgColor: 'bg-brand-100', icon: 'clipboard' },
  analyzing: { color: 'text-navy-700', bgColor: 'bg-navy-100', icon: 'chart' },
  generating: { color: 'text-brand-600', bgColor: 'bg-brand-100', icon: 'sparkles' },
  reviewing: { color: 'text-cyan-600', bgColor: 'bg-cyan-100', icon: 'check' },
  completed: { color: 'text-green-600', bgColor: 'bg-green-100', icon: 'done' },
  failed: { color: 'text-red-600', bgColor: 'bg-red-100', icon: 'error' },
}

// Phase icon component
function PhaseIcon({ phase, className }: { phase: string; className?: string }) {
  const icons: Record<string, React.ReactNode> = {
    clock: (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    search: (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    clipboard: (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
    chart: (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    sparkles: (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
      </svg>
    ),
    check: (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    done: (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    error: (
      <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  }
  const config = PHASE_CONFIG[phase] || PHASE_CONFIG.pending
  return <>{icons[config.icon]}</>
}

// Timeline step component
function TimelineStep({
  phase,
  label,
  isActive,
  isCompleted,
  isFailed,
}: {
  phase: string
  label: string
  isActive: boolean
  isCompleted: boolean
  isFailed: boolean
}) {
  const config = PHASE_CONFIG[phase] || PHASE_CONFIG.pending

  return (
    <div className={`flex items-center gap-3 ${isActive ? 'opacity-100' : isCompleted ? 'opacity-70' : 'opacity-40'}`}>
      <div
        className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full ${
          isActive
            ? isFailed
              ? 'bg-red-100 text-red-600'
              : 'bg-navy-100 text-navy-700 ring-4 ring-navy-50'
            : isCompleted
            ? 'bg-green-100 text-green-600'
            : 'bg-gray-100 text-gray-400'
        }`}
      >
        {isCompleted && !isActive ? (
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <PhaseIcon phase={phase} className="h-5 w-5" />
        )}
      </div>
      <span className={`text-sm font-medium ${isActive ? config.color : isCompleted ? 'text-green-600' : 'text-gray-400'}`}>
        {label}
      </span>
      {isActive && !isFailed && phase !== 'completed' && (
        <span className="ml-auto">
          <svg className="h-4 w-4 animate-spin text-navy-700" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </span>
      )}
    </div>
  )
}

export function JobStatusPage() {
  const { t } = useTranslation()
  const { jobId } = useParams<{ jobId: string }>()
  const { getJob } = useJob()
  const { progress: wsProgress, connected } = useWebSocket(jobId)
  const [job, setJob] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState('')

  // Initial fetch + polling fallback (when WS not connected)
  useEffect(() => {
    if (!jobId) return
    const fetchStatus = async () => {
      try {
        const data = await getJob(jobId)
        setJob(data)
      } catch (e) {
        setError(String(e))
      }
    }
    fetchStatus()

    // Poll only if WebSocket is not connected
    if (!connected) {
      const interval = setInterval(fetchStatus, 3000)
      return () => clearInterval(interval)
    }
  }, [jobId, getJob, connected])

  if (error) {
    return (
      <div className="mx-auto max-w-2xl">
        <div className="flex flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50 px-6 py-12">
          <svg className="h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="mt-3 text-sm font-medium text-red-800">{error}</p>
          <Link
            to="/interview"
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            {t('go_home')}
          </Link>
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="mx-auto max-w-2xl">
        <div className="flex flex-col items-center justify-center py-20">
          <div className="relative">
            <div className="h-16 w-16 animate-spin rounded-full border-4 border-navy-200 border-t-navy-700"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-navy-700 to-navy-600"></div>
            </div>
          </div>
          <p className="mt-4 text-sm font-medium text-gray-500">{t('loading')}</p>
        </div>
      </div>
    )
  }

  // Prefer WebSocket progress over polled status
  const status = wsProgress?.status || String(job.status || 'pending')
  const progressPercent = wsProgress?.progress ?? getProgressPercent(status)
  const phaseKey = PHASE_KEYS[status]
  const phaseLabel = wsProgress?.phase || (phaseKey ? t(phaseKey) : status)

  const isTerminal = status === 'completed' || status === 'failed'
  const config = PHASE_CONFIG[status] || PHASE_CONFIG.pending

  // Define all phases for timeline
  const phases = ['pending', 'enriching', 'planning', 'analyzing', 'generating', 'reviewing', 'completed']
  const currentPhaseIndex = phases.indexOf(status)

  return (
    <div className="mx-auto max-w-2xl">
      {/* Header Card */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className={`flex h-14 w-14 items-center justify-center rounded-xl ${config.bgColor}`}>
              <PhaseIcon phase={status} className={`h-7 w-7 ${config.color}`} />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">{t('status_title', { id: jobId?.slice(0, 8) })}</h1>
              <div className="mt-1 flex items-center gap-2">
                <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${config.bgColor} ${config.color}`}>
                  {!isTerminal && (
                    <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse`} />
                  )}
                  {phaseLabel}
                </span>
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-400">{t('created_at')}</p>
            <p className="text-sm font-medium text-gray-600">
              {job.created_at ? new Date(String(job.created_at)).toLocaleDateString() : '-'}
            </p>
            <p className="text-xs text-gray-400">
              {job.created_at ? new Date(String(job.created_at)).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
            </p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-medium text-gray-700">{t('progress_label')}</span>
            <span className={`font-semibold ${config.color}`}>{progressPercent}%</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              className={`h-2.5 rounded-full transition-all duration-700 ease-out ${
                status === 'failed' ? 'bg-red-500' : 'bg-gradient-to-r from-navy-700 to-navy-600'
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>


      {/* Timeline */}
      <div className="mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold text-gray-900">{t('processing_steps')}</h2>
        <div className="space-y-4">
          {phases.map((phase, index) => {
            const isActive = phase === status
            const isCompleted = index < currentPhaseIndex || status === 'completed'
            const isFailed = status === 'failed' && index === currentPhaseIndex

            return (
              <div key={phase} className="relative">
                {index < phases.length - 1 && (
                  <div
                    className={`absolute left-5 top-10 h-4 w-0.5 ${
                      isCompleted ? 'bg-green-300' : 'bg-gray-200'
                    }`}
                  />
                )}
                <TimelineStep
                  phase={phase}
                  label={t(PHASE_KEYS[phase])}
                  isActive={isActive}
                  isCompleted={isCompleted}
                  isFailed={isFailed}
                />
              </div>
            )
          })}
        </div>
      </div>

      {/* Success State */}
      {status === 'completed' && (
        <div className="rounded-xl border border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 p-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
              <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-green-800">{t('script_complete')}</h3>
              <p className="text-sm text-green-600">{t('script_generated_desc')}</p>
            </div>
            <Link
              to={`/interview/${jobId}/result`}
              className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-green-700 hover:shadow-md"
            >
              {t('view_result')}
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </div>
      )}

      {/* Failed State */}
      {status === 'failed' && (
        <div className="rounded-xl border border-red-200 bg-gradient-to-br from-red-50 to-orange-50 p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-red-100">
              <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-red-800">{t('generation_failed')}</h3>
              <p className="mt-1 text-sm text-red-600">
                {String((job as Record<string, unknown>).error_message || t('unknown_error'))}
              </p>
              <Link
                to="/interview/new"
                className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-red-700 hover:text-red-800"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                {t('create_new_script')}
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function getProgressPercent(status: string): number {
  const map: Record<string, number> = {
    pending: 0, enriching: 10, planning: 20,
    analyzing: 40, generating: 65, reviewing: 85,
    completed: 100, failed: 100,
  }
  return map[status] ?? 0
}
