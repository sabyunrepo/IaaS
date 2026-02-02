import { useState } from 'react'

interface Question {
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
      <div
        className="p-4 cursor-pointer flex items-center justify-between hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
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
            <span className="text-xs text-gray-400">{question.time_allocation_minutes}분</span>
          )}
          <span className="text-gray-400">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-100">
          {/* Expected Answer */}
          {question.expected_answer && (
            <div className="mt-3">
              <h4 className="text-sm font-semibold text-gray-700 mb-1">예상 답변</h4>
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

          {/* Follow-up questions */}
          {question.follow_up_questions && question.follow_up_questions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-1">꼬리질문</h4>
              {question.follow_up_questions.map((fq, i) => (
                <p key={i} className="text-sm text-gray-600 ml-2">
                  → {typeof fq === 'string' ? fq : String((fq as Record<string, unknown>).question || JSON.stringify(fq))}
                </p>
              ))}
            </div>
          )}

          {/* Terminology */}
          {question.terminology && question.terminology.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 mb-1">용어 설명</h4>
              {question.terminology.map((term, i) => (
                <div key={i} className="text-sm text-gray-600 ml-2">
                  <strong>{term.term}</strong>: {term.plain_language_explanation || term.definition}
                </div>
              ))}
            </div>
          )}

          {/* Interviewer note */}
          {question.interviewer_note && (
            <div className="bg-blue-50 p-2 rounded text-sm text-blue-800">
              <strong>면접관 노트:</strong>{' '}
              {typeof question.interviewer_note === 'string'
                ? question.interviewer_note
                : JSON.stringify(question.interviewer_note)}
            </div>
          )}

          {/* Scoring */}
          <div className="flex items-center gap-2 pt-2">
            <span className="text-sm text-gray-600">평가:</span>
            {[1, 2, 3, 4, 5].map((s) => (
              <button
                key={s}
                onClick={() => handleScore(s)}
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
