import { useEffect, useRef, useState, useCallback } from 'react'
import { apiFetch, getToken } from '../lib/api'

export interface AnalysisLog {
  id: string
  job_id: string
  activity_name: string
  phase: string
  log_type: 'start' | 'progress' | 'result' | 'error'
  message: string | null
  data: Record<string, unknown>
  duration_ms: number | null
  created_at: string
}

export interface AnalysisSummary {
  job_id: string
  total_logs: number
  completed_activities: number
  errors: number
  total_duration_ms: number
  total_duration_sec: number
  phase_stats: Record<string, number>
  activity_stats: Record<string, number>
}

interface UseAnalysisLogsReturn {
  logs: AnalysisLog[]
  summary: AnalysisSummary | null
  loading: boolean
  error: string | null
  streaming: boolean
  fetchLogs: (filters?: {
    phase?: string
    activity_name?: string
    log_type?: string
  }) => Promise<void>
  fetchSummary: () => Promise<void>
}

const MAX_RECONNECT_ATTEMPTS = 5
const BASE_DELAY_MS = 1000

export function useAnalysisLogs(jobId: string | undefined): UseAnalysisLogsReturn {
  const [logs, setLogs] = useState<AnalysisLog[]>([])
  const [summary, setSummary] = useState<AnalysisSummary | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [streaming, setStreaming] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const attemptRef = useRef(0)
  const terminalRef = useRef(false)

  const fetchLogs = useCallback(async (filters?: {
    phase?: string
    activity_name?: string
    log_type?: string
  }) => {
    if (!jobId) return

    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      if (filters?.phase) params.append('phase', filters.phase)
      if (filters?.activity_name) params.append('activity_name', filters.activity_name)
      if (filters?.log_type) params.append('log_type', filters.log_type)

      const queryString = params.toString()
      const path = `/jobs/${jobId}/analysis-logs${queryString ? `?${queryString}` : ''}`
      const data = await apiFetch(path)
      setLogs(data || [])
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [jobId])

  const fetchSummary = useCallback(async () => {
    if (!jobId) return

    try {
      const data = await apiFetch(`/jobs/${jobId}/analysis-summary`)
      setSummary(data)
    } catch (e) {
      console.error('Failed to fetch summary:', e)
    }
  }, [jobId])

  // WebSocket streaming connection
  const connectWebSocket = useCallback(() => {
    if (!jobId || terminalRef.current) return

    const token = getToken()
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/api/v1/jobs/${jobId}/logs/ws?token=${encodeURIComponent(token)}`

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setStreaming(true)
        setError(null)
        attemptRef.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.event === 'summary') {
            setSummary(data.data)
          } else if (data.event === 'log') {
            setLogs((prev) => {
              // Check for duplicate
              const exists = prev.some((log) => log.id === data.data.id)
              if (exists) return prev
              return [...prev, data.data]
            })
          } else if (data.event === 'done') {
            terminalRef.current = true
            if (data.summary) setSummary(data.summary)
            ws.close()
          } else if (data.event === 'error') {
            setError(data.message)
          }
        } catch {
          // ignore parse errors
        }
      }

      ws.onclose = () => {
        setStreaming(false)
        wsRef.current = null

        // Auto-reconnect with exponential backoff if not terminal
        if (!terminalRef.current && attemptRef.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = BASE_DELAY_MS * Math.pow(2, attemptRef.current)
          attemptRef.current += 1
          reconnectRef.current = setTimeout(connectWebSocket, delay)
        }
      }

      ws.onerror = () => {
        setError('WebSocket 연결 실패')
        setStreaming(false)
      }
    } catch {
      setError('WebSocket 연결 실패')
    }
  }, [jobId])

  // Initial fetch and WebSocket connection
  useEffect(() => {
    if (!jobId) return

    terminalRef.current = false
    attemptRef.current = 0

    // Fetch initial data
    fetchLogs()
    fetchSummary()

    // Connect WebSocket for streaming
    connectWebSocket()

    return () => {
      terminalRef.current = true
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current)
      }
    }
  }, [jobId, fetchLogs, fetchSummary, connectWebSocket])

  return {
    logs,
    summary,
    loading,
    error,
    streaming,
    fetchLogs,
    fetchSummary,
  }
}
