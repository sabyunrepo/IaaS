import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../lib/api'

interface Job {
  id: string
  status: string
  progress: number
  input_data: {
    github_urls?: string[]
    candidate_username?: string
    jd_text?: string
  }
}

const STATUS_BADGE: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
}

export function JobListPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    apiFetch('/api/jobs')
      .then((res) => res.json())
      .then(setJobs)
      .catch(() => setJobs([]))
      .finally(() => setIsLoading(false))
  }, [])

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">채용 공고</h1>
        <Link
          to="/jobs/new"
          className="px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
        >
          새 분석 시작
        </Link>
      </div>

      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[--color-border-default]">
              <th className="text-left px-4 py-3 text-xs font-medium text-[--color-text-tertiary] uppercase">
                ID
              </th>
              <th className="text-left px-4 py-3 text-xs font-medium text-[--color-text-tertiary] uppercase">
                후보자
              </th>
              <th className="text-left px-4 py-3 text-xs font-medium text-[--color-text-tertiary] uppercase">
                상태
              </th>
              <th className="text-left px-4 py-3 text-xs font-medium text-[--color-text-tertiary] uppercase">
                진행률
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              [...Array(3)].map((_, i) => (
                <tr key={i} className="border-b border-[--color-border-default]">
                  {[...Array(4)].map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-[--color-bg-neutral] rounded animate-pulse w-24" />
                    </td>
                  ))}
                </tr>
              ))
            ) : jobs.length === 0 ? (
              <tr>
                <td
                  colSpan={4}
                  className="text-center py-12 text-[--color-text-secondary]"
                >
                  분석 기록이 없습니다.{' '}
                  <Link to="/jobs/new" className="text-[--color-text-accent] hover:underline">
                    새 분석을 시작하세요
                  </Link>
                </td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr
                  key={job.id}
                  className="border-b border-[--color-border-default] hover:bg-[--color-bg-neutral] transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link
                      to={`/jobs/${job.id}`}
                      className="text-sm font-mono text-[--color-text-accent] hover:underline"
                    >
                      {job.id.slice(0, 8)}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-[--color-text-primary]">
                    {job.input_data?.candidate_username || job.input_data?.github_urls?.[0] || '-'}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                        STATUS_BADGE[job.status] || 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {job.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-[--color-bg-neutral] rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[--color-bg-accent] rounded-full transition-all"
                          style={{ width: `${(job.progress || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-[--color-text-tertiary]">
                        {Math.round((job.progress || 0) * 100)}%
                      </span>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
