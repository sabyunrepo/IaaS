import { useState, useCallback } from 'react'
import { apiFetch } from '../lib/api'

interface Job {
  id: string
  status: string
  input_data: Record<string, unknown>
  created_at: string
  completed_at?: string
}

export function useJob() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(false)

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch('/jobs')
      setJobs(data)
    } catch (e) {
      console.error('Failed to fetch jobs:', e)
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
    setJobs((prev) => prev.filter((j) => j.id !== jobId))
  }, [])

  return { jobs, loading, fetchJobs, createJob, getJob, deleteJob }
}
