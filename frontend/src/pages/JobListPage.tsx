import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useJob } from '../hooks/useJob'

export function JobListPage() {
  const { t } = useTranslation()
  const { jobs, loading, fetchJobs, deleteJob } = useJob()

  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  if (loading) return <p>{t('loading')}</p>

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
        <div className="space-y-3">
          {jobs.map((job) => (
            <div key={job.id} className="bg-white rounded-lg shadow p-4 flex items-center justify-between">
              <div>
                <Link to={`/jobs/${job.id}`} className="text-blue-600 hover:underline font-medium">
                  {job.id.slice(0, 8)}...
                </Link>
                <span className="ml-3 text-sm text-gray-500">{job.status}</span>
                <span className="ml-3 text-sm text-gray-400">
                  {new Date(job.created_at).toLocaleString()}
                </span>
              </div>
              <button
                onClick={() => deleteJob(job.id)}
                className="text-sm text-red-500 hover:text-red-700"
              >
                삭제
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
