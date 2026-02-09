import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiFetch } from '../lib/api'
import type { InterviewScript, ResultTab, InterviewQuestion } from '../types/interview'
import { IntelBriefTab, DeepAnalysisTab, LiveInterviewTab, DecisionTab, V1SummaryTab, V1GuideTab } from '../components/tabs'
import { QuestionCard, type Question } from '../components/QuestionCard'
import { GlossarySection } from '../components/GlossarySection'

function downloadJSON(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
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

  // Tab keyboard navigation (WCAG 2.1)
  // IMPORTANT: useCallback must be called before any early returns
  // to maintain consistent hook call order (React Rules of Hooks).
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
          to="/interview"
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
              to={`/interview/${jobId}/logs`}
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
            {t('result_tab_intel_brief')}
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
            {t('result_tab_analysis')}
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
            {t('result_tab_interview')} ({questions.length})
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
            {t('result_tab_decision')}
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
              linkedinProfile={script.linkedin_profile}
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
              dataConfidence={script.analysis?.data_confidence}
              dataConfidenceScore={script.analysis?.data_confidence_score}
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
            <V1SummaryTab summary={summary} />
          )}

          {/* Interviewer Guide Tab */}
          {activeTab === 'guide' && guide && (
            <V1GuideTab guide={guide} />
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
          to="/interview"
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
