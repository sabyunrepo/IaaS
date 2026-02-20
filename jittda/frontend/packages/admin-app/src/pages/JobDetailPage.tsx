import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiFetch } from '../lib/api'

interface JobDetail {
  id: string
  status: string
  progress: number
  input_data: {
    github_urls?: string[]
    candidate_username?: string
    jd_text?: string
  }
  result_data?: Record<string, unknown>
  error_message?: string
}

const STATUS_LABEL: Record<string, { text: string; style: string }> = {
  pending: { text: '대기 중', style: 'bg-yellow-100 text-yellow-800' },
  running: { text: '분석 중', style: 'bg-blue-100 text-blue-800' },
  completed: { text: '완료', style: 'bg-green-100 text-green-800' },
  failed: { text: '실패', style: 'bg-red-100 text-red-800' },
}

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const [job, setJob] = useState<JobDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!jobId) return
    apiFetch(`/api/jobs/${jobId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Not found')
        return res.json()
      })
      .then(setJob)
      .catch(() => setJob(null))
      .finally(() => setIsLoading(false))
  }, [jobId])

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-[--color-bg-neutral] rounded w-64" />
          <div className="h-4 bg-[--color-bg-neutral] rounded w-48" />
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="p-8">
        <p className="text-[--color-text-danger]">Job을 찾을 수 없습니다.</p>
        <Link to="/jobs" className="text-sm text-[--color-text-accent] hover:underline mt-2 inline-block">
          목록으로 돌아가기
        </Link>
      </div>
    )
  }

  const statusInfo = STATUS_LABEL[job.status] || { text: job.status, style: 'bg-gray-100 text-gray-800' }

  return (
    <div className="p-8">
      <Link to="/jobs" className="text-sm text-[--color-text-accent] hover:underline mb-4 inline-block">
        &larr; 목록으로
      </Link>

      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">
          Job {job.id.slice(0, 8)}
        </h1>
        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${statusInfo.style}`}>
          {statusInfo.text}
        </span>
      </div>

      {/* Progress */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-[--color-text-primary]">진행률</span>
          <span className="text-sm text-[--color-text-secondary]">
            {Math.round((job.progress || 0) * 100)}%
          </span>
        </div>
        <div className="h-2 bg-[--color-bg-neutral] rounded-full overflow-hidden">
          <div
            className="h-full bg-[--color-bg-accent] rounded-full transition-all"
            style={{ width: `${(job.progress || 0) * 100}%` }}
          />
        </div>
      </div>

      {/* Input data */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold text-[--color-text-primary] mb-4">입력 정보</h2>
        <dl className="space-y-3">
          {job.input_data.candidate_username && (
            <div>
              <dt className="text-xs text-[--color-text-tertiary] uppercase">후보자</dt>
              <dd className="text-sm text-[--color-text-primary]">{job.input_data.candidate_username}</dd>
            </div>
          )}
          {job.input_data.github_urls && job.input_data.github_urls.length > 0 && (
            <div>
              <dt className="text-xs text-[--color-text-tertiary] uppercase">GitHub URLs</dt>
              <dd className="space-y-1">
                {job.input_data.github_urls.map((url) => (
                  <a
                    key={url}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block text-sm text-[--color-text-accent] hover:underline"
                  >
                    {url}
                  </a>
                ))}
              </dd>
            </div>
          )}
          {job.input_data.jd_text && (
            <div>
              <dt className="text-xs text-[--color-text-tertiary] uppercase">JD</dt>
              <dd className="text-sm text-[--color-text-secondary] whitespace-pre-line max-h-40 overflow-auto">
                {job.input_data.jd_text}
              </dd>
            </div>
          )}
        </dl>
      </div>

      {/* Error */}
      {job.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-[--color-text-danger] mb-2">오류</h2>
          <p className="text-sm text-[--color-text-danger]">{job.error_message}</p>
        </div>
      )}

      {/* Actions */}
      {job.status === 'completed' && (
        <Link
          to={`/jobs/${job.id}/candidates/default/analysis`}
          className="inline-block px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
        >
          분석 결과 보기
        </Link>
      )}
    </div>
  )
}
