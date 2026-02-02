import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useJob } from '../hooks/useJob'

const PHASE_LABELS: Record<string, string> = {
  pending: '대기 중',
  enriching: 'Phase 0: 입력 분석',
  planning: 'Phase 1: 실행 계획',
  analyzing: 'Phase 2: 분석',
  generating: 'Phase 3: 질문 생성',
  reviewing: 'Phase 4: 품질 검토',
  completed: '완료',
  failed: '실패',
}

export function JobStatusPage() {
  const { t } = useTranslation()
  const { jobId } = useParams<{ jobId: string }>()
  const { getJob } = useJob()
  const [job, setJob] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState('')

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
    const interval = setInterval(fetchStatus, 3000)
    return () => clearInterval(interval)
  }, [jobId, getJob])

  if (error) return <p className="text-red-600">{error}</p>
  if (!job) return <p>{t('loading')}</p>

  const status = String(job.status || 'pending')
  const phaseLabel = PHASE_LABELS[status] || status

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Job: {jobId?.slice(0, 8)}...</h1>

      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div className="flex justify-between">
          <span className="text-gray-600">{t('status')}</span>
          <span className={`font-medium ${status === 'completed' ? 'text-green-600' : status === 'failed' ? 'text-red-600' : 'text-blue-600'}`}>
            {phaseLabel}
          </span>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-blue-600 h-3 rounded-full transition-all duration-500"
            style={{ width: `${getProgressPercent(status)}%` }}
          />
        </div>

        <div className="text-sm text-gray-500">
          생성일: {job.created_at ? new Date(String(job.created_at)).toLocaleString() : '-'}
        </div>

        {status === 'completed' && (
          <div className="mt-4 p-4 bg-green-50 rounded-lg flex items-center justify-between">
            <p className="text-green-800 font-medium">면접 스크립트 생성 완료!</p>
            <Link
              to={`/jobs/${jobId}/result`}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              결과 보기
            </Link>
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
