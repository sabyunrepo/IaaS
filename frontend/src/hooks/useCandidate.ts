import { useState, useCallback } from 'react'
import { apiFetch } from '../lib/api'

export interface Candidate {
  id: string
  name: string
  email: string | null
  experience_years: number | null
  experience_level: string | null
  skills: string[]
  github_username: string | null
  linkedin_url: string | null
  data_completeness: number
  created_at: string | null
  updated_at: string | null
  profile_data?: Record<string, unknown>
}

export interface JD {
  id: string
  title: string
  required_skills: string[]
  preferred_skills: string[]
  is_active: boolean
  created_at: string | null
  jd_text?: string
  jd_analysis?: Record<string, unknown>
}

export interface MatchResult {
  candidate_id: string
  jd_id: string
  overall_match_score: number
  skill_match_score: number
  skill_matches: {
    matched: Array<{ skill: string; matched: boolean; match_score: number; source: string }>
    gaps: Array<{ skill: string; importance: string }>
    overlap_score: number
    total_jd_skills: number
    matched_count: number
    gap_count: number
  }
  radar_scores: {
    candidate: number[]
    required: number[]
    sources: string[]
    human_sources: string[]
  }
  gaps: Array<{ skill: string; importance: string }>
  match_explanation: string
  hiring_recommendation: string
  confidence_level: string
}

export interface CompareResult {
  jd_id: string
  candidates: Array<{
    candidate: Candidate
    match: MatchResult | null
  }>
  total: number
}

export function useCandidate() {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchCandidates = useCallback(async (params?: {
    limit?: number; offset?: number; skill?: string[]; level?: string
  }) => {
    setLoading(true)
    setError(null)
    try {
      const query = new URLSearchParams()
      if (params?.limit) query.set('limit', String(params.limit))
      if (params?.offset) query.set('offset', String(params.offset))
      if (params?.skill) params.skill.forEach(s => query.append('skill', s))
      if (params?.level) query.set('level', params.level)
      const qs = query.toString()
      const data = await apiFetch(`/candidates${qs ? '?' + qs : ''}`)
      setCandidates(data)
      return data as Candidate[]
    } catch (e) {
      setError(String(e))
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  const getCandidate = useCallback(async (id: string): Promise<Candidate> => {
    return apiFetch(`/candidates/${id}`)
  }, [])

  const createCandidate = useCallback(async (data: {
    name: string
    email?: string
    experience_years?: number
    experience_level?: string
    skills?: string[]
    github_username?: string
    linkedin_url?: string
    profile_data?: Record<string, unknown>
  }): Promise<Candidate> => {
    return apiFetch('/candidates', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }, [])

  const updateCandidate = useCallback(async (id: string, data: Partial<{
    name: string; email: string; experience_years: number
    experience_level: string; skills: string[]
    github_username: string; linkedin_url: string
  }>): Promise<Candidate> => {
    return apiFetch(`/candidates/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }, [])

  const deleteCandidate = useCallback(async (id: string) => {
    await apiFetch(`/candidates/${id}`, { method: 'DELETE' })
    setCandidates(prev => prev.filter(c => c.id !== id))
  }, [])

  // JD operations
  const createJD = useCallback(async (data: {
    title: string; jd_text?: string
    required_skills?: string[]; preferred_skills?: string[]
  }): Promise<JD> => {
    return apiFetch('/candidates/jd', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }, [])

  const fetchJDs = useCallback(async (): Promise<JD[]> => {
    return apiFetch('/candidates/jd')
  }, [])

  const getJD = useCallback(async (id: string): Promise<JD> => {
    return apiFetch(`/candidates/jd/${id}`)
  }, [])

  // Matching
  const matchCandidateToJD = useCallback(async (
    candidateId: string, jdId: string,
    options?: { experience_level?: string; output_language?: string }
  ): Promise<MatchResult> => {
    return apiFetch(`/candidates/${candidateId}/match/${jdId}`, {
      method: 'POST',
      body: JSON.stringify(options || {}),
    })
  }, [])

  const compareCandidates = useCallback(async (
    jdId: string, candidateIds: string[]
  ): Promise<CompareResult> => {
    return apiFetch(`/candidates/compare?jd_id=${jdId}&ids=${candidateIds.join(',')}`)
  }, [])

  const getJDRanking = useCallback(async (
    jdId: string, limit = 20
  ): Promise<{ jd_id: string; ranking: Array<{
    rank: number; candidate: Candidate
    overall_match_score: number; skill_match_score: number
  }>; total: number }> => {
    return apiFetch(`/candidates/jd/${jdId}/ranking?limit=${limit}`)
  }, [])

  const updateJD = useCallback(async (id: string, data: { jd_text?: string }): Promise<JD> => {
    return apiFetch(`/candidates/jd/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }, [])

  const deleteJD = useCallback(async (id: string) => {
    await apiFetch(`/candidates/jd/${id}`, { method: 'DELETE' })
  }, [])

  const fetchMyProfile = useCallback(async (): Promise<Candidate> => {
    return apiFetch('/candidates/my-profile')
  }, [])

  return {
    candidates, loading, error,
    fetchCandidates, getCandidate, createCandidate, updateCandidate, deleteCandidate,
    createJD, fetchJDs, getJD, updateJD, deleteJD,
    matchCandidateToJD, compareCandidates, getJDRanking,
    fetchMyProfile,
  }
}
