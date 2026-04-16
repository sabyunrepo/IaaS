import { Link } from 'react-router-dom'
import { Plus, FileText, Users, CheckCircle, Clock } from 'lucide-react'
import { usePostings } from '../hooks/usePostings'

export function DashboardPage() {
  const { data: postings, isLoading } = usePostings()

  const stats = postings
    ? {
        total: postings.length,
        active: postings.filter((p) => p.status === 'active').length,
        totalApplicants: postings.reduce((sum, p) => sum + (p.application_count ?? 0), 0),
        draft: postings.filter((p) => p.status === 'draft').length,
      }
    : null

  const cards = stats
    ? [
        { label: '전체 공고', value: stats.total, icon: FileText, color: 'text-[--color-text-primary]' },
        { label: '활성 공고', value: stats.active, icon: CheckCircle, color: 'text-[--color-text-accent]' },
        { label: '전체 지원자', value: stats.totalApplicants, icon: Users, color: 'text-[--color-text-success]' },
        { label: '초안', value: stats.draft, icon: Clock, color: 'text-[--color-text-secondary]' },
      ]
    : []

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">대시보드</h1>
        <Link
          to="/postings/new"
          className="flex items-center gap-1.5 px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
        >
          <Plus size={16} />
          새 공고
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
        <>
          <div className="grid grid-cols-4 gap-4 mb-8">
            {cards.map((card) => {
              const Icon = card.icon
              return (
                <div
                  key={card.label}
                  className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Icon size={14} className="text-[--color-text-tertiary]" />
                    <p className="text-sm text-[--color-text-secondary]">{card.label}</p>
                  </div>
                  <p className={`text-3xl font-bold ${card.color}`}>{card.value}</p>
                </div>
              )
            })}
          </div>

          {/* Recent postings */}
          {postings && postings.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold text-[--color-text-primary] mb-4">최근 공고</h2>
              <div className="space-y-2">
                {postings.slice(0, 5).map((p) => (
                  <Link
                    key={p.id}
                    to={`/postings/${p.id}`}
                    className="flex items-center justify-between bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg px-4 py-3 hover:bg-[--color-bg-neutral] transition-colors"
                  >
                    <div>
                      <span className="text-sm font-medium text-[--color-text-primary]">{p.title}</span>
                      {p.department && (
                        <span className="ml-2 text-xs text-[--color-text-tertiary]">{p.department}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1 text-xs text-[--color-text-secondary]">
                        <Users size={12} />
                        {p.application_count}
                      </span>
                      <StatusBadge status={p.status} />
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-600',
    active: 'bg-green-100 text-green-700',
    closed: 'bg-red-100 text-red-600',
  }
  const labels: Record<string, string> = {
    draft: '초안',
    active: '활성',
    closed: '마감',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] ?? styles.draft}`}>
      {labels[status] ?? status}
    </span>
  )
}
