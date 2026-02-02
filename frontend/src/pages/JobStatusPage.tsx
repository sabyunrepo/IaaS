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

  if (error) return <p className="text-red-600 p-4">{error}</p>
  if (!job) {
    return (
      <div className="max-w-2xl mx-auto flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        <span className="ml-3 text-gray-500">{t('loading')}</span>
      </div>
    )
  }

  // Prefer WebSocket progress over polled status
  const status = wsProgress?.status || String(job.status || 'pending')
  const progressPercent = wsProgress?.progress ?? getProgressPercent(status)
  const phaseKey = PHASE_KEYS[status]
  const phaseLabel = wsProgress?.phase || (phaseKey ? t(phaseKey) : status)

  const isTerminal = status === 'completed' || status === 'failed'

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Job: {jobId?.slice(0, 8)}...</h1>

      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">{t('status')}</span>
          <div className="flex items-center gap-2">
            {!isTerminal && (
              <span className={`inline-block h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-yellow-500'} animate-pulse`} />
            )}
            <span className={`font-medium ${status === 'completed' ? 'text-green-600' : status === 'failed' ? 'text-red-600' : 'text-blue-600'}`}>
              {phaseLabel}
            </span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${status === 'failed' ? 'bg-red-500' : 'bg-blue-600'}`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="text-right text-xs text-gray-400">{progressPercent}%</div>

        <div className="text-sm text-gray-500">
          {t('created_at')}: {job.created_at ? new Date(String(job.created_at)).toLocaleString() : '-'}
        </div>

        {status === 'completed' && (
          <div className="mt-4 p-4 bg-green-50 rounded-lg flex items-center justify-between">
            <p className="text-green-800 font-medium">{t('script_complete')}</p>
            <Link
              to={`/jobs/${jobId}/result`}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              {t('view_result')}
            </Link>
          </div>
        )}

        {status === 'failed' && (
          <div className="mt-4 p-4 bg-red-50 rounded-lg">
            <p className="text-red-800 font-medium">{t('generation_failed')}</p>
            <p className="text-red-600 text-sm mt-1">
              {String((job as Record<string, unknown>).error_message || t('unknown_error'))}
            </p>
          </div>
        )}
      </div>
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
