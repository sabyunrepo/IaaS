import { useCallback, useEffect, useRef, useState } from 'react';
import { WS_BASE } from '../lib/api';
import type {
  AgentState,
  LangGraphStreamState,
  StreamMessage,
} from '../types/stream';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Maximum automatic reconnection attempts before giving up. */
const MAX_RECONNECT_ATTEMPTS = 3;

/** Delay between reconnection attempts in milliseconds. */
const RECONNECT_DELAY_MS = 2_000;

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * Manages a WebSocket connection to the LangGraph HMAS analysis pipeline
 * and exposes real-time agent states, progress, and metrics.
 *
 * Usage:
 * ```tsx
 * const { agentStates, progress, metrics, isConnected, isCompleted, error } =
 *   useLangGraphStream(jobId);
 * ```
 *
 * The hook automatically connects on mount and cleans up on unmount.
 * It will retry up to {@link MAX_RECONNECT_ATTEMPTS} times on unexpected
 * disconnections before surfacing an error.
 */
export function useLangGraphStream(jobId: string): LangGraphStreamState {
  // -- State ----------------------------------------------------------------
  const [agentStates, setAgentStates] = useState<AgentState[]>([]);
  const [progress, setProgress] = useState(0);
  const [metrics, setMetrics] = useState<Record<string, number>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // -- Refs (survive across renders without triggering re-renders) ----------
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);
  const isCompletedRef = useRef(false);

  // -- Helpers --------------------------------------------------------------

  /** Update a single agent entry inside the `agentStates` array. */
  const upsertAgent = useCallback(
    (name: string, patch: Partial<AgentState>) => {
      setAgentStates((prev) => {
        const idx = prev.findIndex((a) => a.name === name);
        if (idx === -1) {
          return [...prev, { name, status: 'pending', ...patch }];
        }
        const next = [...prev];
        next[idx] = { ...next[idx], ...patch };
        return next;
      });
    },
    [],
  );

  // -- Message handler (stable ref via useCallback) -------------------------

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      let data: StreamMessage;
      try {
        data = JSON.parse(event.data as string) as StreamMessage;
      } catch {
        // Ignore malformed payloads — do not crash the UI.
        return;
      }

      switch (data.type) {
        case 'agent_started': {
          if (data.agent) {
            upsertAgent(data.agent, { status: 'running' });
          }
          break;
        }

        case 'agent_completed': {
          if (data.agent) {
            upsertAgent(data.agent, {
              status: 'completed',
              result: data.result,
            });
          }
          break;
        }

        case 'progress': {
          if (data.progress != null) {
            setProgress(data.progress);
          }
          break;
        }

        case 'metric_update': {
          if (data.metric != null && data.value != null) {
            setMetrics((prev) => ({ ...prev, [data.metric!]: data.value! }));
          }
          break;
        }

        case 'error': {
          if (data.agent) {
            upsertAgent(data.agent, {
              status: 'failed',
              error: data.message,
            });
          }
          setError(data.message ?? 'Unknown error');
          break;
        }

        case 'completed': {
          setIsCompleted(true);
          isCompletedRef.current = true;
          setProgress(1);
          break;
        }
      }
    },
    [upsertAgent],
  );

  // -- Connection logic -----------------------------------------------------

  const connect = useCallback(() => {
    // Guard: don't connect without a jobId or after unmount.
    if (!jobId || !mountedRef.current) return;

    // Close any existing socket first.
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const url = `${WS_BASE}/ws/jobs/${jobId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.addEventListener('open', () => {
      if (!mountedRef.current) return;
      setIsConnected(true);
      setError(null);
      reconnectAttemptsRef.current = 0;
    });

    ws.addEventListener('message', handleMessage);

    ws.addEventListener('close', (event) => {
      if (!mountedRef.current) return;
      setIsConnected(false);

      // Normal closure or analysis completed — no reconnect needed.
      if (event.code === 1000 || isCompletedRef.current) return;

      // Attempt automatic reconnection.
      if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttemptsRef.current += 1;
        reconnectTimerRef.current = setTimeout(() => {
          if (mountedRef.current) {
            connect();
          }
        }, RECONNECT_DELAY_MS);
      } else {
        setError(
          `Connection lost after ${MAX_RECONNECT_ATTEMPTS} reconnection attempts.`,
        );
      }
    });

    ws.addEventListener('error', () => {
      if (!mountedRef.current) return;
      // The `close` handler will fire next and manage reconnection.
      setIsConnected(false);
    });
  }, [jobId, handleMessage]);

  // -- Lifecycle ------------------------------------------------------------

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;

      // Clear pending reconnect timer.
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }

      // Close the WebSocket cleanly.
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
    };
  }, [connect]);

  // -- Return ---------------------------------------------------------------

  return { agentStates, progress, metrics, isConnected, isCompleted, error };
}
