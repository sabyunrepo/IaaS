/**
 * WebSocket stream types for LangGraph HMAS real-time updates.
 *
 * Message flow: Backend (FastAPI WebSocket) -> Frontend (useLangGraphStream hook)
 * Each message carries a `type` discriminator used for dispatch in the hook.
 */

// ---------------------------------------------------------------------------
// Agent state (tracked per worker/supervisor)
// ---------------------------------------------------------------------------

export type AgentStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface AgentState {
  name: string;
  status: AgentStatus;
  result?: Record<string, unknown>;
  error?: string;
}

// ---------------------------------------------------------------------------
// Metric update (individual scoring metric pushed during analysis)
// ---------------------------------------------------------------------------

export interface MetricUpdate {
  metric: string;
  value: number;
}

// ---------------------------------------------------------------------------
// Stream message (union discriminated by `type`)
// ---------------------------------------------------------------------------

export type StreamMessageType =
  | 'agent_started'
  | 'agent_completed'
  | 'progress'
  | 'metric_update'
  | 'error'
  | 'completed';

export interface StreamMessage {
  type: StreamMessageType;
  agent?: string;
  result?: Record<string, unknown>;
  progress?: number;
  metric?: string;
  value?: number;
  message?: string;
  job_id?: string;
}

// ---------------------------------------------------------------------------
// Aggregate hook state returned by useLangGraphStream
// ---------------------------------------------------------------------------

export interface LangGraphStreamState {
  agentStates: AgentState[];
  progress: number;
  metrics: Record<string, number>;
  isConnected: boolean;
  isCompleted: boolean;
  error: string | null;
}
