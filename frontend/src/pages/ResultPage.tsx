import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiFetch } from '../lib/api'
import type { InterviewScript, ResultTab, InterviewQuestion } from '../types/interview'
import { IntelBriefTab, DeepAnalysisTab, LiveInterviewTab, DecisionTab, V1SummaryTab, V1GuideTab } from '../components/tabs'
import { QuestionCard, type Question } from '../components/QuestionCard'
import { ActionButton, Badge, Skeleton, TabsRoot, TabsList, TabsTrigger, TabsContent, TabsIndicator } from '../../seed-design/ui'


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

  if (loading) {
    return (
      <div className="space-y-6 py-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-14 w-14 rounded-2xl" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <Skeleton className="h-12 w-full" />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
        <Skeleton className="h-60 w-full" />
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
      <div className="flex flex-col items-center justify-center rounded-xl border border-[--color-border-default] bg-[--color-bg-page] px-6 py-12">
        <svg className="h-12 w-12 text-[--color-text-tertiary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="mt-3 text-sm font-medium text-[--color-text-primary]">{t('result_error')}</p>
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
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-em-500 to-teal-500 shadow-lg">
            <svg className="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[--color-text-primary]">{t('interview_script')}</h1>
            <div className="flex items-center gap-2 text-sm text-[--color-text-tertiary]">
              <span>#{jobId?.slice(0, 8)}</span>
              <span>·</span>
              <span>{t('result_question_count', { count: questions.length })}</span>
              {script.metadata?.experience_level && (
                <>
                  <span>·</span>
                  <Badge tone="brand" variant="weak">
                    {script.metadata.experience_level}
                  </Badge>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {maxScore > 0 && (
            <div className="flex items-center gap-2 rounded-lg border border-em-200 bg-em-50 px-3 py-2">
              <svg className="h-5 w-5 text-em-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span className="text-sm font-semibold text-em-800">
                {totalScore}/{maxScore} ({scorePercent}%)
              </span>
            </div>
          )}

          <div className="flex gap-2 no-print">
            <ActionButton
              variant="neutralOutline"
              size="small"
              onClick={() => downloadJSON(script, `interview-${jobId?.slice(0, 8)}.json`)}
              className="inline-flex items-center gap-1.5"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {t('export_json')}
            </ActionButton>
            <ActionButton
              variant="neutralOutline"
              size="small"
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              {t('print_pdf')}
            </ActionButton>
          </div>
        </div>
      </div>

      {/* Tabs */}
      {hasV2Data ? (
        <TabsRoot
          value={activeTab}
          onValueChange={(v) => setActiveTab(v as ResultTab | 'questions' | 'summary' | 'guide')}
        >
          <TabsList className="no-print overflow-x-auto scrollbar-hide">
            <TabsTrigger value="intel" className="flex items-center gap-2 whitespace-nowrap">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {t('result_tab_intel_brief')}
            </TabsTrigger>
            <TabsTrigger value="analysis" className="flex items-center gap-2 whitespace-nowrap">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              {t('result_tab_analysis')}
            </TabsTrigger>
            <TabsTrigger value="interview" className="flex items-center gap-2 whitespace-nowrap">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
              </svg>
              {t('result_tab_interview')} ({questions.length})
            </TabsTrigger>
            <TabsTrigger value="decision" className="flex items-center gap-2 whitespace-nowrap">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {t('result_tab_decision')}
            </TabsTrigger>
            <TabsIndicator />
          </TabsList>

          <TabsContent value="intel">
            {script.intel && (
              <IntelBriefTab
                intel={script.intel}
                candidate={script.candidate}
                techStack={script.metadata?.code_analysis_tech_stack}
                linkedinProfile={script.linkedin_profile}
              />
            )}
          </TabsContent>
          <TabsContent value="analysis">
            {script.analysis && (
              <DeepAnalysisTab analysis={script.analysis} />
            )}
          </TabsContent>
          <TabsContent value="interview">
            <LiveInterviewTab
              questions={questions as InterviewQuestion[]}
            />
          </TabsContent>
          <TabsContent value="decision">
            {script.decision && (
              <DecisionTab
                decision={script.decision}
                overallMatch={script.analysis?.overall_match}
              />
            )}
          </TabsContent>
        </TabsRoot>
      ) : (
        <TabsRoot
          value={activeTab}
          onValueChange={(v) => setActiveTab(v as ResultTab | 'questions' | 'summary' | 'guide')}
        >
          <TabsList className="no-print overflow-x-auto scrollbar-hide">
            <TabsTrigger value="questions">
              {t('result_tab_questions')} ({questions.length})
            </TabsTrigger>
            <TabsTrigger value="summary">
              {t('result_tab_summary')}
            </TabsTrigger>
            <TabsTrigger value="guide">
              {t('result_tab_guide')}
            </TabsTrigger>
            <TabsIndicator />
          </TabsList>

          <TabsContent value="questions">
            <div className="space-y-4">
              {questions.length === 0 ? (
                <div className="flex flex-col items-center justify-center rounded-xl border border-[--color-border-default] bg-[--color-bg-page] py-12">
                  <svg className="h-12 w-12 text-ink-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="mt-3 text-sm text-[--color-text-tertiary]">{t('result_no_questions')}</p>
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
          </TabsContent>
          <TabsContent value="summary">
            {summary && <V1SummaryTab summary={summary} />}
          </TabsContent>
          <TabsContent value="guide">
            {guide && <V1GuideTab guide={guide} />}
          </TabsContent>
        </TabsRoot>
      )}

      {/* Back to list link */}
      <div className="flex justify-center pt-4 no-print">
        <Link
          to="/interview"
          className="inline-flex items-center gap-2 text-sm font-medium text-[--color-text-tertiary] hover:text-[--color-text-secondary]"
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
