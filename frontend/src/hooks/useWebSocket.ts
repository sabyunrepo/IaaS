import { useEffect, useRef, useState, useCallback } from 'react'
import i18next from 'i18next'
import { getToken } from '../lib/api'

interface WSProgress {
  status: string
  phase: string
  progress: number
  event?: string
}

interface UseWebSocketReturn {
  progress: WSProgress | null
  connected: boolean
  error: string | null
}

const MAX_RECONNECT_ATTEMPTS = 5
const BASE_DELAY_MS = 1000

export function useWebSocket(jobId: string | undefined): UseWebSocketReturn {
  const [progress, setProgress] = useState<WSProgress | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const attemptRef = useRef(0)
  const terminalRef = useRef(false)

  const connect = useCallback(() => {
    if (!jobId || terminalRef.current) return

    const token = getToken()
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/api/v1/jobs/${jobId}/ws?token=${encodeURIComponent(token)}`

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        setError(null)
        attemptRef.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSProgress
          setProgress(data)

          if (data.event === 'done' || data.status === 'completed' || data.status === 'failed') {
            terminalRef.current = true
            ws.close()
          }
        } catch {
          // ignore parse errors
        }
      }

      ws.onclose = () => {
        setConnected(false)
        wsRef.current = null

        // Auto-reconnect with exponential backoff if not terminal
        if (!terminalRef.current && attemptRef.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = BASE_DELAY_MS * Math.pow(2, attemptRef.current)
          attemptRef.current += 1
          reconnectRef.current = setTimeout(connect, delay)
        }
      }

      ws.onerror = () => {
        setError(i18next.t('websocket_error'))
        setConnected(false)
      }
    } catch {
      setError(i18next.t('websocket_error'))
    }
  }, [jobId])

  useEffect(() => {
    terminalRef.current = false
    attemptRef.current = 0
    connect()

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
  }, [connect])

  return { progress, connected, error }
}
