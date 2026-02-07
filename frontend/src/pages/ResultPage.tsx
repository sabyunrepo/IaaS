import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiFetch } from '../lib/api'
import type { InterviewScript, ResultTab, InterviewQuestion } from '../types/interview'
import { IntelBriefTab, DeepAnalysisTab, LiveInterviewTab, DecisionTab } from '../components/tabs'
import { QuestionCard, type Question } from '../components/QuestionCard'

function downloadJSON(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function GlossarySection({ glossary }: { glossary: InterviewScript['full_glossary'] }) {
  const { t } = useTranslation()
  const [expandedTerms, setExpandedTerms] = useState<Set<number>>(new Set())
  const [glossaryExpanded, setGlossaryExpanded] = useState(false)

  const toggleTerm = useCallback((idx: number) => {
    setExpandedTerms(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }, [])

  if (!glossary || glossary.length === 0) return null

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <button
        onClick={() => setGlossaryExpanded(!glossaryExpanded)}
        className="w-full p-6 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <svg className="h-5 w-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h2 className="text-lg font-semibold text-gray-900">{t('glossary')}</h2>
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
            {t('result_terms_count', { count: glossary.length })}
          </span>
        </div>
        <svg className={`w-5 h-5 text-gray-400 transition-transform ${glossaryExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {glossaryExpanded && (
        <div className="px-6 pb-6 animate-fadeIn">
          <div className="grid gap-2 sm:grid-cols-2">
            {glossary.map((term, i) => (
              <button
                key={i}
                onClick={() => toggleTerm(i)}
                className="w-full text-left rounded-lg border border-gray-100 bg-gray-50 p-3 hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-semibold text-gray-900">{term.term}</dt>
                  <svg className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${expandedTerms.has(i) ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
                {expandedTerms.has(i) && (
                  <dd className="mt-2 text-sm text-gray-600 animate-fadeIn">
                    {term.plain_language_explanation || term.definition}
                    {term.business_context && (
                      <p className="mt-1 text-xs text-indigo-600">{term.business_context}</p>
                    )}
                  </dd>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export function ResultPage() {
  const { t } = useTranslation()
  const { jobId } = useParams<{ jobId: string }>()
  const [script, setScript] = useState<InterviewScript | null>(null)
  const [activeTab, setActiveTab] = useState<ResultTab | 'questions' | 'summary' | 'guide'>('intel')
  const [scores, setScores] = useState<Record<number, number>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Determine if we have v2 data
  const hasV2Data = script?.intel || script?.analysis || script?.decision
  const questions = script?.questions || []

  // Fallback to v1 tabs if no v2 data
  useEffect(() => {
    if (script && !hasV2Data) {
      setActiveTab('questions')
    }
  }, [script, hasV2Data])

  useEffect(() => {
    if (!jobId) return
    // Request v2 format by default
    apiFetch(`/jobs/${jobId}/result?version=v2`)
      .then(setScript)
      .catch((err) => {
        setError(String(err))
      })
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) {
    return (
      <div className="space-y-6 py-6">
        <div className="flex items-center gap-4">
          <div className="skeleton h-14 w-14 rounded-2xl" />
          <div className="space-y-2">
            <div className="skeleton h-6 w-48" />
            <div className="skeleton h-4 w-32" />
          </div>
        </div>
        <div className="skeleton h-12 w-full" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="skeleton h-40" />
          <div className="skeleton h-40" />
        </div>
        <div className="skeleton h-60 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50 px-6 py-12">
        <svg className="h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p className="mt-3 text-sm font-medium text-red-800">{t('result_error')}: {error}</p>
        <Link
          to="/jobs"
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          {t('go_home')}
        </Link>
      </div>
    )
  }

  if (!script) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-gray-50 px-6 py-12">
        <svg className="h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="mt-3 text-sm font-medium text-gray-800">{t('result_error')}</p>
      </div>
    )
  }

  const handleScoreChange = (index: number, score: number) => {
    setScores((prev) => ({ ...prev, [index]: score }))
  }

  // Tab keyboard navigation (WCAG 2.1)
  const v2TabIds = ['intel', 'analysis', 'interview', 'decision'] as const
  const v1TabIds = ['questions', 'summary', 'guide'] as const

  const handleTabKeyDown = useCallback((e: React.KeyboardEvent, tabs: readonly string[]) => {
    const currentIndex = tabs.indexOf(activeTab)
    if (currentIndex === -1) return
    let newIndex = currentIndex
    if (e.key === 'ArrowRight') newIndex = (currentIndex + 1) % tabs.length
    else if (e.key === 'ArrowLeft') newIndex = (currentIndex - 1 + tabs.length) % tabs.length
    else if (e.key === 'Home') newIndex = 0
    else if (e.key === 'End') newIndex = tabs.length - 1
    else return
    e.preventDefault()
    setActiveTab(tabs[newIndex] as typeof activeTab)
    document.getElementById(`tab-${tabs[newIndex]}`)?.focus()
  }, [activeTab])

  const totalScore = Object.values(scores).reduce((sum, s) => sum + s, 0)
  const maxScore = Object.keys(scores).length * 5
  const scorePercent = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0

  // Legacy data for fallback
  const summary = script.candidate_summary
  const guide = script.interviewer_guide

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
            <svg className="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('interview_script')}</h1>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span>#{jobId?.slice(0, 8)}</span>
              <span>·</span>
              <span>{t('result_question_count', { count: questions.length })}</span>
              {script.metadata?.experience_level && (
                <>
                  <span>·</span>
                  <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-medium">
                    {script.metadata.experience_level}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {maxScore > 0 && (
            <div className="flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2">
              <svg className="h-5 w-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span className="text-sm font-semibold text-indigo-700">
                {totalScore}/{maxScore} ({scorePercent}%)
              </span>
            </div>
          )}

          <div className="flex gap-2 no-print">
            <Link
              to={`/jobs/${jobId}/logs`}
              className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-300 bg-indigo-50 px-3 py-2 text-sm font-medium text-indigo-700 transition-colors hover:bg-indigo-100"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {t('result_analysis_logs')}
            </Link>
            <button
              onClick={() => downloadJSON(script, `interview-${jobId?.slice(0, 8)}.json`)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {t('export_json')}
            </button>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              {t('print_pdf')}
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      {hasV2Data ? (
        // v2 4-tab navigation (underline style)
        <div role="tablist" aria-label={t('interview_script')} className="flex border-b border-gray-200 no-print overflow-x-auto scrollbar-hide">
          <button
            role="tab"
            id="tab-intel"
            aria-selected={activeTab === 'intel'}
            aria-controls="tabpanel-intel"
            tabIndex={activeTab === 'intel' ? 0 : -1}
            onClick={() => setActiveTab('intel')}
            onKeyDown={(e) => handleTabKeyDown(e, v2TabIds)}
            className={`tab-underline flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors whitespace-nowrap shrink-0 ${
              activeTab === 'intel' ? 'active text-indigo-700' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Intel Brief
          </button>
          <button
            role="tab"
            id="tab-analysis"
            aria-selected={activeTab === 'analysis'}
            aria-controls="tabpanel-analysis"
            tabIndex={activeTab === 'analysis' ? 0 : -1}
            onClick={() => setActiveTab('analysis')}
            onKeyDown={(e) => handleTabKeyDown(e, v2TabIds)}
            className={`tab-underline flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors whitespace-nowrap shrink-0 ${
              activeTab === 'analysis' ? 'active text-indigo-700' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Deep Analysis
          </button>
          <button
            role="tab"
            id="tab-interview"
            aria-selected={activeTab === 'interview'}
            aria-controls="tabpanel-interview"
            tabIndex={activeTab === 'interview' ? 0 : -1}
            onClick={() => setActiveTab('interview')}
            onKeyDown={(e) => handleTabKeyDown(e, v2TabIds)}
            className={`tab-underline flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors whitespace-nowrap shrink-0 ${
              activeTab === 'interview' ? 'active text-indigo-700' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
            Live Interview ({questions.length})
          </button>
          <button
            role="tab"
            id="tab-decision"
            aria-selected={activeTab === 'decision'}
            aria-controls="tabpanel-decision"
            tabIndex={activeTab === 'decision' ? 0 : -1}
            onClick={() => setActiveTab('decision')}
            onKeyDown={(e) => handleTabKeyDown(e, v2TabIds)}
            className={`tab-underline flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors whitespace-nowrap shrink-0 ${
              activeTab === 'decision' ? 'active text-indigo-700' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Decision
          </button>
        </div>
      ) : (
        // v1 3-tab navigation (underline style)
        <div role="tablist" aria-label={t('interview_script')} className="flex border-b border-gray-200 no-print overflow-x-auto scrollbar-hide">
          <button
            role="tab"
            id="tab-questions"
            aria-selected={activeTab === 'questions'}
            aria-controls="tabpanel-questions"
            tabIndex={activeTab === 'questions' ? 0 : -1}
            onClick={() => setActiveTab('questions')}
            onKeyDown={(e) => handleTabKeyDown(e, v1TabIds)}
            className={`tab-underline flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors whitespace-nowrap shrink-0 ${
              activeTab === 'questions' ? 'active text-indigo-700' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t('result_tab_questions')} ({questions.length})
          </button>
          <button
            role="tab"
            id="tab-summary"
            aria-selected={activeTab === 'summary'}
            aria-controls="tabpanel-summary"
            tabIndex={activeTab === 'summary' ? 0 : -1}
            onClick={() => setActiveTab('summary')}
            onKeyDown={(e) => handleTabKeyDown(e, v1TabIds)}
            className={`tab-underline flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors whitespace-nowrap shrink-0 ${
              activeTab === 'summary' ? 'active text-indigo-700' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t('result_tab_summary')}
          </button>
          <button
            role="tab"
            id="tab-guide"
            aria-selected={activeTab === 'guide'}
            aria-controls="tabpanel-guide"
            tabIndex={activeTab === 'guide' ? 0 : -1}
            onClick={() => setActiveTab('guide')}
            onKeyDown={(e) => handleTabKeyDown(e, v1TabIds)}
            className={`tab-underline flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors whitespace-nowrap shrink-0 ${
              activeTab === 'guide' ? 'active text-indigo-700' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t('result_tab_guide')}
          </button>
        </div>
      )}

      {/* V2 Tabs */}
      {hasV2Data && (
        <div key={activeTab} id={`tabpanel-${activeTab}`} role="tabpanel" aria-labelledby={`tab-${activeTab}`} className="animate-fadeIn">
          {activeTab === 'intel' && script.intel && (
            <IntelBriefTab
              intel={script.intel}
              candidate={script.candidate}
              techStack={script.metadata?.code_analysis_tech_stack}
            />
          )}

          {activeTab === 'analysis' && script.analysis && (
            <DeepAnalysisTab analysis={script.analysis} />
          )}

          {activeTab === 'interview' && (
            <LiveInterviewTab
              questions={questions as InterviewQuestion[]}
              categoryWeights={script.category_weights}
            />
          )}

          {activeTab === 'decision' && script.decision && (
            <DecisionTab
              decision={script.decision}
              candidate={script.candidate}
              categoryWeights={script.category_weights}
              totalScore={hasV2Data && script?.analysis?.overall_match != null ? script.analysis.overall_match : totalScore}
              maxScore={hasV2Data && script?.analysis?.overall_match != null ? 100 : (maxScore || 100)}
              riskFlags={script.analysis?.risk_flags}
            />
          )}
        </div>
      )}

      {/* V1 Tabs (Fallback) */}
      {!hasV2Data && (
        <>
          {/* Questions Tab */}
          {activeTab === 'questions' && (
            <div className="space-y-4">
              {questions.length === 0 ? (
                <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-gray-50 py-12">
                  <svg className="h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="mt-3 text-sm text-gray-500">{t('result_no_questions')}</p>
                </div>
              ) : (
                questions.map((q, i) => (
                  <QuestionCard
                    key={i}
                    question={q as Question}
                    index={i}
                    onScoreChange={handleScoreChange}
                  />
                ))
              )}
            </div>
          )}

          {/* Candidate Summary Tab */}
          {activeTab === 'summary' && summary && (
            <div className="space-y-6">
              {/* Candidate Overview */}
              {summary.candidate_overview && (
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <svg className="h-5 w-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    {t('result_candidate_overview')}
                  </h2>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {summary.candidate_overview.name && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('result_name')}</dt>
                        <dd className="mt-1 text-lg font-semibold text-gray-900">{summary.candidate_overview.name}</dd>
                      </div>
                    )}
                    {summary.candidate_overview.current_position && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('result_current_position')}</dt>
                        <dd className="mt-1 text-gray-900">{summary.candidate_overview.current_position}</dd>
                      </div>
                    )}
                    {summary.candidate_overview.primary_domain && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('result_primary_domain')}</dt>
                        <dd className="mt-1 text-gray-900">{summary.candidate_overview.primary_domain}</dd>
                      </div>
                    )}
                    {summary.candidate_overview.experience_years && (
                      <div>
                        <dt className="text-sm font-medium text-gray-500">{t('result_v1_experience')}</dt>
                        <dd className="mt-1 text-gray-900">{summary.candidate_overview.experience_years}</dd>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Key Strengths */}
              {summary.key_strengths && summary.key_strengths.length > 0 && (
                <div className="rounded-xl border border-green-200 bg-green-50 p-6">
                  <h2 className="text-lg font-semibold text-green-900 mb-4 flex items-center gap-2">
                    <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {t('result_key_strengths')}
                  </h2>
                  <div className="space-y-3">
                    {summary.key_strengths.map((item, i) => (
                      <div key={i} className="bg-white rounded-lg p-4 border border-green-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-green-900">{item.strength}</span>
                          <span className="text-sm text-green-600">{t('result_confidence', { value: Math.round(item.confidence * 100) })}</span>
                        </div>
                        {item.evidence && (
                          <div className="text-sm text-green-700 space-y-1">
                            {item.evidence.resume && <p>📄 {t('result_source_resume')}: {item.evidence.resume}</p>}
                            {item.evidence.linkedin && <p>💼 LinkedIn: {item.evidence.linkedin}</p>}
                            {item.evidence.github && <p>🔗 GitHub: {item.evidence.github}</p>}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Risk Flags */}
              {summary.risk_flags && summary.risk_flags.length > 0 && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-6">
                  <h2 className="text-lg font-semibold text-red-900 mb-4 flex items-center gap-2">
                    <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    {t('result_risk_factors')}
                  </h2>
                  <div className="space-y-3">
                    {summary.risk_flags.map((item, i) => (
                      <div key={i} className="bg-white rounded-lg p-4 border border-red-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-red-900">{item.concern}</span>
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            item.severity === 'high' ? 'bg-red-200 text-red-800' :
                            item.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                            'bg-gray-200 text-gray-800'
                          }`}>
                            {item.severity}
                          </span>
                        </div>
                        {item.evidence && <p className="text-sm text-red-700 mb-2">{item.evidence}</p>}
                        {item.mitigation_question && (
                          <p className="text-sm text-red-800 bg-red-100 p-2 rounded">
                            💡 {t('result_verify_question')}: {item.mitigation_question}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Technical Expertise */}
              {summary.technical_expertise && (
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                    </svg>
                    {t('result_technical_expertise')}
                  </h2>
                  <div className="space-y-4">
                    {summary.technical_expertise.languages && summary.technical_expertise.languages.length > 0 && (
                      <div>
                        <h3 className="text-sm font-medium text-gray-500 mb-2">{t('result_languages')}</h3>
                        <div className="flex flex-wrap gap-2">
                          {summary.technical_expertise.languages.map((lang, i) => (
                            <span key={i} className="px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-sm">
                              {lang.skill} ({lang.proficiency})
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {summary.technical_expertise.frameworks && summary.technical_expertise.frameworks.length > 0 && (
                      <div>
                        <h3 className="text-sm font-medium text-gray-500 mb-2">{t('result_frameworks')}</h3>
                        <div className="flex flex-wrap gap-2">
                          {summary.technical_expertise.frameworks.map((fw, i) => (
                            <span key={i} className="px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm">
                              {fw.skill} ({fw.proficiency})
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {summary.technical_expertise.tools && summary.technical_expertise.tools.length > 0 && (
                      <div>
                        <h3 className="text-sm font-medium text-gray-500 mb-2">{t('result_tools')}</h3>
                        <div className="flex flex-wrap gap-2">
                          {summary.technical_expertise.tools.map((tool, i) => (
                            <span key={i} className="px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-sm">
                              {tool.tool} ({tool.proficiency})
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Data Quality Assessment */}
              {summary.data_quality_assessment && (
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('result_data_quality')}</h2>
                  <div className="grid gap-4 sm:grid-cols-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-indigo-600">
                        {Math.round(summary.data_quality_assessment.overall_confidence * 100)}%
                      </div>
                      <div className="text-sm text-gray-500">{t('result_overall_confidence')}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {Math.round(summary.data_quality_assessment.document_quality * 100)}%
                      </div>
                      <div className="text-sm text-gray-500">{t('result_document_quality')}</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {Math.round(summary.data_quality_assessment.linkedin_quality * 100)}%
                      </div>
                      <div className="text-sm text-gray-500">LinkedIn</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {Math.round(summary.data_quality_assessment.github_quality * 100)}%
                      </div>
                      <div className="text-sm text-gray-500">GitHub</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Interviewer Guide Tab */}
          {activeTab === 'guide' && guide && (
            <div className="space-y-6">
              {/* Interview Overview */}
              {guide.interview_overview && (
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('result_interview_overview')}</h2>
                  <div className="grid gap-4 sm:grid-cols-4">
                    <div className="text-center p-3 bg-indigo-50 rounded-lg">
                      <div className="text-2xl font-bold text-indigo-600">
                        {t('result_duration', { min: guide.interview_overview.total_duration_minutes })}
                      </div>
                      <div className="text-sm text-gray-500">{t('result_total_duration')}</div>
                    </div>
                    <div className="text-center p-3 bg-indigo-50 rounded-lg">
                      <div className="text-2xl font-bold text-indigo-600">
                        {t('result_count_unit', { count: guide.interview_overview.question_count })}
                      </div>
                      <div className="text-sm text-gray-500">{t('result_question_count_label')}</div>
                    </div>
                    <div className="text-center p-3 bg-indigo-50 rounded-lg">
                      <div className="text-lg font-bold text-indigo-600">
                        {guide.interview_overview.experience_level}
                      </div>
                      <div className="text-sm text-gray-500">{t('result_experience_level_label')}</div>
                    </div>
                    <div className="text-center p-3 bg-indigo-50 rounded-lg">
                      <div className="text-lg font-bold text-indigo-600">
                        {guide.interview_overview.interview_style}
                      </div>
                      <div className="text-sm text-gray-500">{t('result_interview_style')}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Interview Flow */}
              {guide.interview_flow && (
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('result_interview_flow_order')}</h2>
                  <div className="space-y-4">
                    {guide.interview_flow.opening && (
                      <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                        <h3 className="font-medium text-green-900 mb-2">
                          🎬 {t('result_opening')} ({t('result_duration', { min: guide.interview_flow.opening.duration_minutes })})
                        </h3>
                        <p className="text-sm text-green-800">{guide.interview_flow.opening.script}</p>
                      </div>
                    )}
                    {guide.interview_flow.main_body && (
                      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <h3 className="font-medium text-blue-900 mb-2">📋 {t('result_main_interview')}</h3>
                        <p className="text-sm text-blue-800 mb-2">
                          {t('result_flow_order')}: {guide.interview_flow.main_body.recommended_order?.join(' → ')}
                        </p>
                        {guide.interview_flow.main_body.transition_phrases && (
                          <div className="text-sm text-blue-700">
                            <p className="font-medium mb-1">{t('result_transition_phrases')}:</p>
                            <ul className="list-disc list-inside">
                              {guide.interview_flow.main_body.transition_phrases.map((phrase, i) => (
                                <li key={i}>{phrase}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                    {guide.interview_flow.closing && (
                      <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                        <h3 className="font-medium text-amber-900 mb-2">
                          🏁 {t('result_closing')} ({t('result_duration', { min: guide.interview_flow.closing.duration_minutes })})
                        </h3>
                        <p className="text-sm text-amber-800">{guide.interview_flow.closing.script}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Evaluation Matrix */}
              {guide.evaluation_matrix && (
                <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('result_evaluation_criteria')}</h2>
                  <div className="grid gap-4 sm:grid-cols-3 mb-4">
                    <div className="text-center p-3 bg-gray-50 rounded-lg">
                      <div className="text-lg font-bold text-gray-900">
                        {guide.evaluation_matrix.scoring_scale}
                      </div>
                      <div className="text-sm text-gray-500">{t('result_scoring_scale')}</div>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-lg font-bold text-green-600">
                        ≥ {guide.evaluation_matrix.passing_threshold}
                      </div>
                      <div className="text-sm text-gray-500">{t('result_passing_threshold')}</div>
                    </div>
                    <div className="text-center p-3 bg-indigo-50 rounded-lg">
                      <div className="text-lg font-bold text-indigo-600">
                        ≥ {guide.evaluation_matrix.strong_hire_threshold}
                      </div>
                      <div className="text-sm text-gray-500">Strong Hire</div>
                    </div>
                  </div>
                  {guide.evaluation_matrix.category_weights && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-2">{t('result_v1_category_weights')}</h3>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(guide.evaluation_matrix.category_weights).map(([cat, weight]) => (
                          <span key={cat} className="px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-sm">
                            {cat}: {Math.round(Number(weight) * 100)}%
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Red/Green Flags */}
              <div className="grid gap-6 sm:grid-cols-2">
                {guide.green_flags_summary && guide.green_flags_summary.length > 0 && (
                  <div className="rounded-xl border border-green-200 bg-green-50 p-6">
                    <h2 className="text-lg font-semibold text-green-900 mb-3">✅ Green Flags</h2>
                    <ul className="space-y-2">
                      {guide.green_flags_summary.map((flag, i) => (
                        <li key={i} className="text-sm text-green-800 flex items-start gap-2">
                          <span className="text-green-500">•</span>
                          {flag}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {guide.red_flags_summary && guide.red_flags_summary.length > 0 && (
                  <div className="rounded-xl border border-red-200 bg-red-50 p-6">
                    <h2 className="text-lg font-semibold text-red-900 mb-3">🚩 Red Flags</h2>
                    <ul className="space-y-2">
                      {guide.red_flags_summary.map((flag, i) => (
                        <li key={i} className="text-sm text-red-800 flex items-start gap-2">
                          <span className="text-red-500">•</span>
                          {flag}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* Glossary (shown on all tabs) */}
      {script.full_glossary && script.full_glossary.length > 0 && (
        <GlossarySection glossary={script.full_glossary} />
      )}

      {/* Back to list link */}
      <div className="flex justify-center pt-4 no-print">
        <Link
          to="/jobs"
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-gray-700"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          {t('result_back_to_list')}
        </Link>
      </div>
    </div>
  )
}
