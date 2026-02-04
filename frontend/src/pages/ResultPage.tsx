import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiFetch } from '../lib/api'
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

const CATEGORY_KEYS = [
  { key: 'all', i18n: 'cat_all', color: 'bg-gray-100 text-gray-700 hover:bg-gray-200' },
  { key: 'role_fit', i18n: 'cat_role_fit', color: 'bg-blue-100 text-blue-700 hover:bg-blue-200' },
  { key: 'technical_depth', i18n: 'cat_technical_depth', color: 'bg-purple-100 text-purple-700 hover:bg-purple-200' },
  { key: 'execution_ownership', i18n: 'cat_execution_ownership', color: 'bg-amber-100 text-amber-700 hover:bg-amber-200' },
  { key: 'communication', i18n: 'cat_communication', color: 'bg-green-100 text-green-700 hover:bg-green-200' },
  { key: 'risk_flags', i18n: 'cat_risk_flags', color: 'bg-red-100 text-red-700 hover:bg-red-200' },
]

interface InterviewScript {
  candidate_summary: string | Record<string, unknown> | null
  questions: Question[]
  interviewer_guide: string | Record<string, unknown> | null
  full_glossary: Array<Record<string, string>>
  metadata: Record<string, unknown>
}

export function ResultPage() {
  const { t } = useTranslation()
  const { jobId } = useParams<{ jobId: string }>()
  const [script, setScript] = useState<InterviewScript | null>(null)
  const [activeCategory, setActiveCategory] = useState('all')
  const [scores, setScores] = useState<Record<number, number>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return
    apiFetch(`/jobs/${jobId}/result`)
      .then(setScript)
      .catch((err) => {
        setError(String(err))
      })
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative">
          <div className="h-16 w-16 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600"></div>
          </div>
        </div>
        <p className="mt-4 text-sm font-medium text-gray-500">{t('loading')}</p>
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

  const questions = script.questions || []
  const filtered = activeCategory === 'all'
    ? questions
    : questions.filter((q) => q.category === activeCategory)

  const handleScoreChange = (index: number, score: number) => {
    setScores((prev) => ({ ...prev, [index]: score }))
  }

  const totalScore = Object.values(scores).reduce((sum, s) => sum + s, 0)
  const maxScore = Object.keys(scores).length * 5
  const scorePercent = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('interview_script')}</h1>
            <p className="text-sm text-gray-500">#{jobId?.slice(0, 8)} · {questions.length}개 질문</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Score display */}
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

          {/* Action buttons */}
          <div className="flex gap-2 no-print">
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

      {/* Candidate Summary */}
      {script.candidate_summary && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-3 flex items-center gap-2">
            <svg className="h-5 w-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <h2 className="text-lg font-semibold text-gray-900">{t('candidate_summary')}</h2>
          </div>
          <p className="text-sm leading-relaxed text-gray-600">
            {typeof script.candidate_summary === 'string'
              ? script.candidate_summary
              : JSON.stringify(script.candidate_summary, null, 2)}
          </p>
        </div>
      )}

      {/* Category tabs */}
      <div className="flex flex-wrap gap-2 no-print">
        {CATEGORY_KEYS.map((cat) => {
          const count = cat.key === 'all'
            ? questions.length
            : questions.filter((q) => q.category === cat.key).length
          const isActive = activeCategory === cat.key

          return (
            <button
              key={cat.key}
              onClick={() => setActiveCategory(cat.key)}
              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-md'
                  : cat.color
              }`}
            >
              {t(cat.i18n)}
              <span className={`rounded-full px-1.5 py-0.5 text-xs ${
                isActive ? 'bg-white/20' : 'bg-black/5'
              }`}>
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Questions */}
      <div className="space-y-4">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-gray-50 py-12">
            <svg className="h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="mt-3 text-sm text-gray-500">이 카테고리에 해당하는 질문이 없습니다</p>
          </div>
        ) : (
          filtered.map((q, i) => (
            <QuestionCard
              key={i}
              question={q}
              index={i}
              onScoreChange={handleScoreChange}
            />
          ))
        )}
      </div>

      {/* Glossary */}
      {script.full_glossary && script.full_glossary.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <svg className="h-5 w-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <h2 className="text-lg font-semibold text-gray-900">{t('glossary')}</h2>
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
              {script.full_glossary.length}개 용어
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {script.full_glossary.map((term, i) => (
              <div key={i} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                <dt className="text-sm font-semibold text-gray-900">{term.term}</dt>
                <dd className="mt-1 text-sm text-gray-600">
                  {term.plain_language_explanation || term.definition}
                </dd>
              </div>
            ))}
          </div>
        </div>
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
          목록으로 돌아가기
        </Link>
      </div>
    </div>
  )
}
