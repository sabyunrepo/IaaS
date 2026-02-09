import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAnalysisLogs, type AnalysisLog } from '../hooks/useAnalysisLogs'

// Phase configuration
const PHASE_CONFIG: Record<string, { color: string; bgColor: string; label: string }> = {
  enriching: { color: 'text-blue-700', bgColor: 'bg-blue-100', label: '입력 보강' },
  planning: { color: 'text-purple-700', bgColor: 'bg-purple-100', label: '계획 수립' },
  analyzing: { color: 'text-indigo-700', bgColor: 'bg-indigo-100', label: '분석' },
  generating: { color: 'text-amber-700', bgColor: 'bg-amber-100', label: '질문 생성' },
  reviewing: { color: 'text-cyan-700', bgColor: 'bg-cyan-100', label: '품질 검토' },
}

// Log type icons
const LOG_TYPE_CONFIG: Record<string, { icon: string; color: string }> = {
  start: { icon: '▶️', color: 'text-blue-600' },
  progress: { icon: '🔄', color: 'text-amber-600' },
  result: { icon: '✅', color: 'text-green-600' },
  error: { icon: '❌', color: 'text-red-600' },
}

// Activity display names
const ACTIVITY_NAMES: Record<string, string> = {
  document_analysis: '문서 분석',
  code_analysis: '코드 분석',
  jd_analysis: 'JD 분석',
  planning: '계획 수립',
  input_enrichment: '입력 보강',
  question_generation: '질문 생성',
  quality_review: '품질 검토',
  finalization: '최종 처리',
}

function LogCard({ log, isExpanded, onToggle }: { log: AnalysisLog; isExpanded: boolean; onToggle: () => void }) {
  const typeConfig = LOG_TYPE_CONFIG[log.log_type] || LOG_TYPE_CONFIG.progress
  const phaseConfig = PHASE_CONFIG[log.phase] || { color: 'text-gray-700', bgColor: 'bg-gray-100', label: log.phase }
  const activityName = ACTIVITY_NAMES[log.activity_name] || log.activity_name
  const hasData = log.data && Object.keys(log.data).length > 0

  return (
    <div className={`rounded-lg border bg-white transition-all ${
      log.log_type === 'error' ? 'border-red-200' : 'border-gray-200'
    }`}>
      <div
        className="flex cursor-pointer items-center gap-3 p-4 hover:bg-gray-50"
        onClick={onToggle}
      >
        {/* Type Icon */}
        <span className="text-lg" title={log.log_type}>{typeConfig.icon}</span>

        {/* Phase Badge */}
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${phaseConfig.bgColor} ${phaseConfig.color}`}>
          {phaseConfig.label}
        </span>

        {/* Activity Name */}
        <span className="font-medium text-gray-900">{activityName}</span>

        {/* Duration */}
        {log.duration_ms !== null && (
          <span className="text-sm text-gray-500">
            {(log.duration_ms / 1000).toFixed(1)}s
          </span>
        )}

        {/* Timestamp */}
        <span className="ml-auto text-xs text-gray-400">
          {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </span>

        {/* Expand Arrow */}
        {hasData && (
          <svg
            className={`h-4 w-4 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </div>

      {/* Message */}
      {log.message && (
        <div className={`border-t px-4 py-2 text-sm ${log.log_type === 'error' ? 'bg-red-50 text-red-700' : 'text-gray-600'}`}>
          {log.message}
        </div>
      )}

      {/* Expanded Data */}
      {isExpanded && hasData && (
        <div className="border-t bg-gray-50 p-4">
          <pre className="max-h-64 overflow-auto rounded-lg bg-gray-900 p-3 text-xs text-gray-100">
            {JSON.stringify(log.data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

function SummaryCard({ summary }: { summary: { total_logs: number; completed_activities: number; errors: number; total_duration_sec: number } }) {
  return (
    <div className="mb-6 grid grid-cols-4 gap-4">
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="text-2xl font-bold text-gray-900">{summary.total_logs}</div>
        <div className="text-sm text-gray-500">총 로그</div>
      </div>
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="text-2xl font-bold text-green-600">{summary.completed_activities}</div>
        <div className="text-sm text-gray-500">완료</div>
      </div>
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="text-2xl font-bold text-red-600">{summary.errors}</div>
        <div className="text-sm text-gray-500">에러</div>
      </div>
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <div className="text-2xl font-bold text-indigo-600">{summary.total_duration_sec.toFixed(1)}s</div>
        <div className="text-sm text-gray-500">총 소요시간</div>
      </div>
    </div>
  )
}

export function AnalysisLogsPage() {
  const { t } = useTranslation()
  const { jobId } = useParams<{ jobId: string }>()
  const { logs, summary, loading, error, streaming, fetchLogs } = useAnalysisLogs(jobId)

  const [expandedLogId, setExpandedLogId] = useState<string | null>(null)
  const [phaseFilter, setPhaseFilter] = useState<string>('')
  const [activityFilter, setActivityFilter] = useState<string>('')

  // Get unique phases and activities for filters
  const phases = [...new Set(logs.map((log) => log.phase))]
  const activities = [...new Set(logs.map((log) => log.activity_name))]

  // Filter logs
  const filteredLogs = logs.filter((log) => {
    if (phaseFilter && log.phase !== phaseFilter) return false
    if (activityFilter && log.activity_name !== activityFilter) return false
    return true
  })

  const handleToggleExpand = (logId: string) => {
    setExpandedLogId((prev) => (prev === logId ? null : logId))
  }

  const handleRefresh = () => {
    fetchLogs({
      phase: phaseFilter || undefined,
      activity_name: activityFilter || undefined,
    })
  }

  if (error) {
    return (
      <div className="mx-auto max-w-4xl">
        <div className="flex flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50 px-6 py-12">
          <svg className="h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="mt-3 text-sm font-medium text-red-800">{error}</p>
          <Link
            to={`/interview/${jobId}`}
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
          >
            Job 상태로 돌아가기
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Link
              to={`/interview/${jobId}`}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <h1 className="text-xl font-bold text-gray-900">분석 로그</h1>
            <span className="text-sm text-gray-500">#{jobId?.slice(0, 8)}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Streaming indicator */}
          {streaming && (
            <span className="flex items-center gap-2 rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
              <span className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
              실시간 스트리밍
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            <svg className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            새로고침
          </button>
        </div>
      </div>

      {/* Summary */}
      {summary && <SummaryCard summary={summary} />}

      {/* Filters */}
      <div className="mb-4 flex items-center gap-3">
        <select
          value={phaseFilter}
          onChange={(e) => setPhaseFilter(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">모든 단계</option>
          {phases.map((phase) => (
            <option key={phase} value={phase}>
              {PHASE_CONFIG[phase]?.label || phase}
            </option>
          ))}
        </select>

        <select
          value={activityFilter}
          onChange={(e) => setActivityFilter(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">모든 Activity</option>
          {activities.map((activity) => (
            <option key={activity} value={activity}>
              {ACTIVITY_NAMES[activity] || activity}
            </option>
          ))}
        </select>

        {(phaseFilter || activityFilter) && (
          <button
            onClick={() => {
              setPhaseFilter('')
              setActivityFilter('')
            }}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            필터 초기화
          </button>
        )}
      </div>

      {/* Logs List */}
      {loading && logs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600"></div>
          <p className="mt-3 text-sm text-gray-500">{t('loading')}</p>
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-200 py-12">
          <svg className="h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="mt-3 text-sm text-gray-500">
            {phaseFilter || activityFilter ? '필터 조건에 맞는 로그가 없습니다' : '아직 분석 로그가 없습니다'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filteredLogs.map((log) => (
            <LogCard
              key={log.id}
              log={log}
              isExpanded={expandedLogId === log.id}
              onToggle={() => handleToggleExpand(log.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
