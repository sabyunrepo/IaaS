import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useJob } from '../hooks/useJob'
import { ActionButton } from '../../seed-design/ui'

const PAGE_SIZE = 10

// Status badge component
function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation()

  const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
    pending: { bg: 'bg-[--color-bg-neutral]', text: 'text-[--color-text-secondary]', label: t('phase_pending') },
    enriching: { bg: 'bg-blue-100', text: 'text-blue-700', label: t('phase_enriching') },
    planning: { bg: 'bg-em-100', text: 'text-em-700', label: t('phase_planning') },
    analyzing: { bg: 'bg-em-100', text: 'text-em-800', label: t('phase_analyzing') },
    generating: { bg: 'bg-em-100', text: 'text-em-700', label: t('phase_generating') },
    reviewing: { bg: 'bg-cyan-100', text: 'text-cyan-700', label: t('phase_reviewing') },
    completed: { bg: 'bg-green-100', text: 'text-green-700', label: t('phase_completed') },
    failed: { bg: 'bg-red-100', text: 'text-red-700', label: t('phase_failed') },
  }

  const config = statusConfig[status] || { bg: 'bg-[--color-bg-neutral]', text: 'text-[--color-text-secondary]', label: status }

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  )
}

// Empty state component
function EmptyState() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[--color-border-default] bg-[--color-bg-page] px-6 py-16">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-em-500 to-teal-500">
        <svg
          className="h-8 w-8 text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      </div>
      <h3 className="mt-4 text-lg font-semibold text-[--color-text-primary]">{t('script_list_empty_title')}</h3>
      <p className="mt-1 text-sm text-[--color-text-tertiary]">{t('script_list_empty_desc')}</p>
      <Link
        to="/interview/new"
        className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[--color-bg-accent] px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-[--color-bg-accent-hover] hover:shadow-md"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        {t('new_script')}
      </Link>
    </div>
  )
}

// Loading skeleton
function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="animate-pulse rounded-xl border border-[--color-border-default] bg-[--color-bg-surface] p-5">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="h-4 w-32 rounded bg-ink-200"></div>
              <div className="h-3 w-48 rounded bg-[--color-bg-neutral]"></div>
            </div>
            <div className="h-6 w-16 rounded-full bg-ink-200"></div>
          </div>
        </div>
      ))}
    </div>
  )
}

export function JobListPage() {
  const { t } = useTranslation()
  const { jobs, loading, error, fetchJobs, deleteJob } = useJob()
  const [page, setPage] = useState(1)

  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  if (loading) {
    return (
      <div>
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-[--color-text-primary]">{t('script_list_title')}</h1>
        </div>
        <LoadingSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50 px-6 py-12">
        <svg className="h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p className="mt-3 text-sm font-medium text-red-800">{t('fetch_error')}</p>
        <ActionButton variant="criticalSolid" size="small" onClick={() => fetchJobs()} className="mt-4">
          {t('retry')}
        </ActionButton>
      </div>
    )
  }

  const totalPages = Math.max(1, Math.ceil(jobs.length / PAGE_SIZE))
  const paginated = jobs.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleDelete = (jobId: string) => {
    if (window.confirm(t('delete_confirm'))) {
      deleteJob(jobId)
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[--color-text-primary]">{t('script_list_title')}</h1>
          {jobs.length > 0 && (
            <p className="mt-1 text-sm text-[--color-text-tertiary]">
              {t('script_count', { count: jobs.length })}
            </p>
          )}
        </div>
        {jobs.length > 0 && (
          <Link
            to="/interview/new"
            className="inline-flex items-center gap-2 rounded-lg bg-[--color-bg-accent] px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-[--color-bg-accent-hover] hover:shadow-md"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {t('new_script')}
          </Link>
        )}
      </div>

      {jobs.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          {/* Script List */}
          <div className="space-y-3">
            {paginated.map((job) => (
              <div
                key={job.job_id}
                className="group rounded-xl border border-[--color-border-default] bg-[--color-bg-surface] p-5 transition-all hover:border-ink-300 hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <Link
                        to={`/interview/${job.job_id}`}
                        className="text-base font-medium text-[--color-text-primary] hover:text-[--color-text-accent]"
                      >
                        #{job.job_id.slice(0, 8)}
                      </Link>
                      <StatusBadge status={job.status} />
                    </div>
                    <div className="mt-1.5 flex items-center gap-4 text-sm text-[--color-text-tertiary]">
                      <span className="flex items-center gap-1">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {new Date(job.created_at).toLocaleDateString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {new Date(job.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Link
                      to={`/interview/${job.job_id}`}
                      className="rounded-lg bg-em-50 px-3 py-1.5 text-sm font-medium text-em-800 hover:bg-em-100"
                    >
                      {t('view_job_status')}
                    </Link>
                    {job.status === 'completed' && (
                      <Link
                        to={`/interview/${job.job_id}/result`}
                        className="rounded-lg bg-green-50 px-3 py-1.5 text-sm font-medium text-green-700 hover:bg-green-100"
                      >
                        {t('view_result')}
                      </Link>
                    )}
                    <button
                      onClick={() => handleDelete(job.job_id)}
                      className="rounded-lg p-2 text-[--color-text-tertiary] opacity-0 transition-all hover:bg-red-50 hover:text-red-500 group-hover:opacity-100 focus-visible:opacity-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[--color-border-accent]"
                      aria-label={t('delete')}
                    >
                      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-8 flex items-center justify-center gap-2">
              <ActionButton
                variant="neutralOutline"
                size="small"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                {t('prev')}
              </ActionButton>
              <span className="px-4 text-sm text-[--color-text-secondary]">
                {page} / {totalPages}
              </span>
              <ActionButton
                variant="neutralOutline"
                size="small"
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                {t('next')}
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </ActionButton>
            </div>
          )}
        </>
      )}
    </div>
  )
}
