import { useState, useCallback } from 'react'
import { apiFetch } from '../lib/api'

interface Job {
  job_id: string
  status: string
  created_at: string
  completed_at?: string
}

export function useJob() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiFetch('/jobs')
      setJobs(data)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [])

  const createJob = useCallback(async (inputData: Record<string, unknown>) => {
    return apiFetch('/jobs', {
      method: 'POST',
      body: JSON.stringify({ input_data: inputData }),
    })
  }, [])

  const getJob = useCallback(async (jobId: string) => {
    return apiFetch(`/jobs/${jobId}`)
  }, [])

  const deleteJob = useCallback(async (jobId: string) => {
    await apiFetch(`/jobs/${jobId}`, { method: 'DELETE' })
    setJobs((prev) => prev.filter((j) => j.job_id !== jobId))
  }, [])

  return { jobs, loading, error, fetchJobs, createJob, getJob, deleteJob }
}
