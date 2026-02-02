import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiFetch } from '../lib/api'
import { QuestionCard } from '../components/QuestionCard'

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
  { key: 'all', i18n: 'cat_all' },
  { key: 'role_fit', i18n: 'cat_role_fit' },
  { key: 'technical_depth', i18n: 'cat_technical_depth' },
  { key: 'execution_ownership', i18n: 'cat_execution_ownership' },
  { key: 'communication', i18n: 'cat_communication' },
  { key: 'risk_flags', i18n: 'cat_risk_flags' },
]

interface InterviewScript {
  candidate_summary: string | Record<string, unknown> | null
  questions: Array<Record<string, unknown>>
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

  useEffect(() => {
    if (!jobId) return
    apiFetch(`/jobs/${jobId}/result`)
      .then(setScript)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) return <p>{t('loading')}</p>
  if (!script) return <p className="text-red-600">{t('result_error')}</p>

  const questions = script.questions || []
  const filtered = activeCategory === 'all'
    ? questions
    : questions.filter((q) => q.category === activeCategory)

  const handleScoreChange = (index: number, score: number) => {
    setScores((prev) => ({ ...prev, [index]: score }))
  }

  const totalScore = Object.values(scores).reduce((sum, s) => sum + s, 0)
  const maxScore = Object.keys(scores).length * 5

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">{t('interview_script')}</h1>
        <div className="flex items-center gap-3">
          {maxScore > 0 && (
            <div className="text-lg font-semibold text-gray-700">
              {t('score_label')}: {totalScore}/{maxScore} ({Math.round((totalScore / maxScore) * 100)}%)
            </div>
          )}
          <button
            onClick={() => downloadJSON(script, `interview-${jobId?.slice(0, 8)}.json`)}
            className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 no-print"
          >
            {t('export_json')}
          </button>
          <button
            onClick={() => window.print()}
            className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 no-print"
          >
            {t('print_pdf')}
          </button>
        </div>
      </div>

      {/* Candidate Summary */}
      {script.candidate_summary && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">{t('candidate_summary')}</h2>
          <p className="text-sm text-gray-600">
            {typeof script.candidate_summary === 'string'
              ? script.candidate_summary
              : JSON.stringify(script.candidate_summary, null, 2)}
          </p>
        </div>
      )}

      {/* Category tabs */}
      <div className="flex gap-2 flex-wrap no-print">
        {CATEGORY_KEYS.map((cat) => (
          <button
            key={cat.key}
            onClick={() => setActiveCategory(cat.key)}
            className={`px-3 py-1 rounded-full text-sm font-medium ${
              activeCategory === cat.key
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {t(cat.i18n)}
            <span className="ml-1 text-xs">
              ({cat.key === 'all'
                ? questions.length
                : questions.filter((q) => q.category === cat.key).length})
            </span>
          </button>
        ))}
      </div>

      {/* Questions */}
      <div className="space-y-3">
        {filtered.map((q, i) => (
          <QuestionCard
            key={i}
            question={q as any}
            index={i}
            onScoreChange={handleScoreChange}
          />
        ))}
      </div>

      {/* Glossary */}
      {script.full_glossary && script.full_glossary.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-2">{t('glossary')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {script.full_glossary.map((term, i) => (
              <div key={i} className="text-sm">
                <strong className="text-gray-800">{term.term}</strong>:{' '}
                <span className="text-gray-600">{term.plain_language_explanation || term.definition}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
