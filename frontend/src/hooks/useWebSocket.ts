import { useEffect, useRef, useState, useCallback } from 'react'
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

export function useWebSocket(jobId: string | undefined): UseWebSocketReturn {
  const [progress, setProgress] = useState<WSProgress | null>(null)
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const connect = useCallback(() => {
    if (!jobId) return

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
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSProgress
          setProgress(data)

          // Terminal states — close connection
          if (data.event === 'done' || data.status === 'completed' || data.status === 'failed') {
            ws.close()
          }
        } catch {
          // ignore parse errors
        }
      }

      ws.onclose = () => {
        setConnected(false)
        wsRef.current = null
      }

      ws.onerror = () => {
        setError('WebSocket 연결 실패')
        setConnected(false)
      }
    } catch {
      setError('WebSocket 연결 실패')
    }
  }, [jobId])

  useEffect(() => {
    connect()

    return () => {
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
