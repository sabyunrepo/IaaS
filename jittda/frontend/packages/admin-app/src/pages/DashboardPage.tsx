import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../lib/api'

interface DashboardStats {
  total_jobs: number
  active_jobs: number
  completed_analyses: number
  pending_analyses: number
}

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    apiFetch('/api/jobs?limit=100')
      .then((res) => res.json())
      .then((jobs: Array<{ status: string }>) => {
        setStats({
          total_jobs: jobs.length,
          active_jobs: jobs.filter((j) => j.status === 'running').length,
          completed_analyses: jobs.filter((j) => j.status === 'completed').length,
          pending_analyses: jobs.filter((j) => j.status === 'pending').length,
        })
      })
      .catch(() => {
        setStats({ total_jobs: 0, active_jobs: 0, completed_analyses: 0, pending_analyses: 0 })
      })
      .finally(() => setIsLoading(false))
  }, [])

  const cards = stats
    ? [
        { label: '전체 공고', value: stats.total_jobs, color: 'text-[--color-text-primary]' },
        { label: '진행 중', value: stats.active_jobs, color: 'text-[--color-text-accent]' },
        { label: '분석 완료', value: stats.completed_analyses, color: 'text-[--color-text-success]' },
        { label: '대기 중', value: stats.pending_analyses, color: 'text-[--color-text-secondary]' },
      ]
    : []

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">대시보드</h1>
        <Link
          to="/jobs/new"
          className="px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
        >
          새 분석 시작
        </Link>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl p-6 animate-pulse"
            >
              <div className="h-4 bg-[--color-bg-neutral] rounded w-20 mb-3" />
              <div className="h-8 bg-[--color-bg-neutral] rounded w-16" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-4 gap-4">
          {cards.map((card) => (
            <div
              key={card.label}
              className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6"
            >
              <p className="text-sm text-[--color-text-secondary]">{card.label}</p>
              <p className={`text-3xl font-bold mt-1 ${card.color}`}>{card.value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
