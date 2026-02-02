import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useJob } from '../hooks/useJob'

const PAGE_SIZE = 10

export function JobListPage() {
  const { t } = useTranslation()
  const { jobs, loading, fetchJobs, deleteJob } = useJob()
  const [page, setPage] = useState(1)

  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  if (loading) return <p>{t('loading')}</p>

  const totalPages = Math.max(1, Math.ceil(jobs.length / PAGE_SIZE))
  const paginated = jobs.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleDelete = (jobId: string) => {
    if (window.confirm(t('delete_confirm'))) {
      deleteJob(jobId)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('jobs')}</h1>
        <Link
          to="/jobs/new"
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          {t('create_job')}
        </Link>
      </div>

      {jobs.length === 0 ? (
        <p className="text-gray-500">{t('no_jobs')}</p>
      ) : (
        <>
          <div className="space-y-3">
            {paginated.map((job) => (
              <div key={job.job_id} className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
                <div>
                  <Link to={`/jobs/${job.job_id}`} className="text-blue-600 hover:underline font-medium">
                    {job.job_id.slice(0, 8)}...
                  </Link>
                  <span className="ml-3 text-sm text-gray-500">{job.status}</span>
                  <span className="ml-3 text-sm text-gray-400">
                    {new Date(job.created_at).toLocaleString()}
                  </span>
                </div>
                <button
                  onClick={() => handleDelete(job.job_id)}
                  className="text-sm text-red-500 hover:text-red-700"
                >
                  {t('delete')}
                </button>
              </div>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-100"
              >
                {t('prev')}
              </button>
              <span className="text-sm text-gray-600">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 text-sm rounded border border-gray-300 disabled:opacity-40 hover:bg-gray-100"
              >
                {t('next')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
