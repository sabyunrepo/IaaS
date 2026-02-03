import { useState } from 'react'
import { useTranslation } from 'react-i18next'

export interface Question {
  question_text: string
  category: string
  difficulty: string
  alternative_phrasings?: string[]
  expected_answer?: Record<string, unknown>
  evaluation_scenarios?: Array<Record<string, unknown>>
  follow_up_questions?: Array<Record<string, unknown>>
  terminology?: Array<Record<string, string>>
  interviewer_note?: string | Record<string, unknown>
  time_allocation_minutes?: number
  code_reference?: Record<string, unknown>
}

interface QuestionCardProps {
  question: Question
  index: number
  onScoreChange?: (index: number, score: number) => void
}

export function QuestionCard({ question, index, onScoreChange }: QuestionCardProps) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const [score, setScore] = useState<number | null>(null)

  const difficultyColor =
    question.difficulty === 'Hard' ? 'text-red-600' :
    question.difficulty === 'Medium' ? 'text-yellow-600' : 'text-green-600'

  const handleScore = (s: number) => {
    setScore(s)
    onScoreChange?.(index, s)
  }

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
      <button
        type="button"
        className="w-full p-4 cursor-pointer flex items-center justify-between hover:bg-gray-50 text-left"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        aria-controls={`question-${index}-details`}
      >
        <div className="flex-1">
          <span className="text-sm text-gray-500 mr-2">Q{index + 1}</span>
          <span className={`text-xs font-medium mr-2 ${difficultyColor}`}>
            {question.difficulty}
          </span>
          <span className="text-gray-900">{question.question_text}</span>
        </div>
        <div className="flex items-center gap-2">
          {question.time_allocation_minutes && (
            <span className="text-xs text-gray-400">{question.time_allocation_minutes}{t('minutes')}</span>
          )}
          <span className="text-gray-400" aria-hidden="true">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {expanded && (
        <div id={`question-${index}-details`} className="px-4 pb-4 space-y-3 border-t border-gray-100" role="region" aria-label={`Q${index + 1} ${t('expected_answer')}`}>
          {question.expected_answer && (
            <div className="mt-3">
              <h4 className="text-sm font-semibold text-gray-700 mb-1">{t('expected_answer')}</h4>
              {Object.entries(question.expected_answer).map(([level, answer]) => (
                <div key={level} className={`text-sm p-2 rounded mb-1 ${
                  level === 'expert' ? 'bg-green-50 text-green-800' :
                  level === 'mid_level' ? 'bg-yellow-50 text-yellow-800' :
                  'bg-red-50 text-red-800'
                }`}>
                  <strong>{level}:</strong> {String(answer)}
                </div>
              ))}
            </div>
          )}

          {question.follow_up_questions && question.follow_up_questions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-1">{t('follow_up')}</h4>
              {question.follow_up_questions.map((fq, i) => (
                <p key={i} className="text-sm text-gray-600 ml-2">
                  → {typeof fq === 'string' ? fq : String((fq as Record<string, unknown>).question || JSON.stringify(fq))}
                </p>
              ))}
            </div>
          )}

          {question.terminology && question.terminology.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-1">{t('terminology')}</h4>
              {question.terminology.map((term, i) => (
                <div key={i} className="text-sm text-gray-600 ml-2">
                  <strong>{term.term}</strong>: {term.plain_language_explanation || term.definition}
                </div>
              ))}
            </div>
          )}

          {question.interviewer_note && (
            <div className="bg-blue-50 p-2 rounded text-sm text-blue-800">
              <strong>{t('interviewer_note')}:</strong>{' '}
              {typeof question.interviewer_note === 'string'
                ? question.interviewer_note
                : JSON.stringify(question.interviewer_note)}
            </div>
          )}

          <div className="flex items-center gap-2 pt-2 no-print">
            <span className="text-sm text-gray-600">{t('scoring')}:</span>
            {[1, 2, 3, 4, 5].map((s) => (
              <button
                key={s}
                onClick={() => handleScore(s)}
                aria-label={`${t('scoring')} ${s}/5`}
                aria-pressed={score === s}
                className={`w-8 h-8 rounded-full text-sm font-medium border ${
                  score === s
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
