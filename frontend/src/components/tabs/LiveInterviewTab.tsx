/**
 * LiveInterviewTab - Question Selection → Interactive Scoring → Follow-up Branching
 */
import { memo, useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import type {
  InterviewQuestion,
  ScenarioLevelType,
  ScoresState,
  CategoryWeights
} from '../../types/interview'
import { InterviewQuestionCard } from './InterviewQuestionCard'

interface LiveInterviewTabProps {
  questions: InterviewQuestion[]
  categoryWeights?: CategoryWeights
}

export const LiveInterviewTab = memo(function LiveInterviewTab({ questions, categoryWeights }: LiveInterviewTabProps) {
  const { t } = useTranslation()

  // Deduplicate questions by ID — backend generates UUID-based IDs,
  // but this safety net prevents selection bugs if duplicates slip through
  const uniqueQuestions = useMemo(() => {
    const seen = new Set<string>()
    return questions.filter(q => {
      if (seen.has(q.id)) return false
      seen.add(q.id)
      return true
    })
  }, [questions])

  const [phase, setPhase] = useState<'select' | 'interview'>('select')
  const [selectedQuestions, setSelectedQuestions] = useState<Set<string>>(new Set())
  const [currentIndex, setCurrentIndex] = useState(0)
  const [scores, setScores] = useState<ScoresState>({})

  // Get selected questions in order
  const interviewQuestions = uniqueQuestions.filter(q => selectedQuestions.has(q.id))

  // Toggle question selection
  const toggleQuestion = (id: string) => {
    const newSet = new Set(selectedQuestions)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    setSelectedQuestions(newSet)
  }

  // Select all questions
  const selectAll = () => {
    setSelectedQuestions(new Set(uniqueQuestions.map(q => q.id)))
  }

  // Start interview
  const startInterview = () => {
    if (selectedQuestions.size > 0) {
      setPhase('interview')
      setCurrentIndex(0)
    }
  }

  // Handle scenario selection
  const handleScenarioSelect = (questionId: string, level: ScenarioLevelType, score: number) => {
    setScores(prev => ({
      ...prev,
      [questionId]: {
        ...prev[questionId],
        selectedLevel: level,
        followUpScores: prev[questionId]?.followUpScores || {},
        totalScore: score + Object.values(prev[questionId]?.followUpScores || {}).reduce((a, b) => a + b, 0),
        maxPossibleScore: 20 + (questions.find(q => q.id === questionId)?.follow_ups?.length || 0) * 10
      }
    }))
  }

  // Handle follow-up scoring
  const handleFollowUpScore = (questionId: string, followUpId: string, score: number) => {
    setScores(prev => {
      const current = prev[questionId] || { selectedLevel: undefined, followUpScores: {}, totalScore: 0, maxPossibleScore: 20 }
      const newFollowUpScores = { ...current.followUpScores, [followUpId]: score }
      const scenarioScore = current.selectedLevel
        ? questions.find(q => q.id === questionId)?.scenarios.find(s => s.level === current.selectedLevel)?.score || 0
        : 0
      return {
        ...prev,
        [questionId]: {
          ...current,
          followUpScores: newFollowUpScores,
          totalScore: scenarioScore + Object.values(newFollowUpScores).reduce((a, b) => a + b, 0)
        }
      }
    })
  }

  // Calculate total score
  const totalScore = Object.values(scores).reduce((sum, s) => sum + s.totalScore, 0)
  const maxScore = Object.values(scores).reduce((sum, s) => sum + s.maxPossibleScore, 0)

  // Selection Phase
  if (phase === 'select') {
    // Group questions by category
    const questionsByCategory = uniqueQuestions.reduce((acc, q) => {
      const cat = q.category || t('live_other')
      if (!acc[cat]) acc[cat] = []
      acc[cat].push(q)
      return acc
    }, {} as Record<string, InterviewQuestion[]>)

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{t('live_select_questions')}</h3>
              <p className="text-sm text-gray-500 mt-1">
                {t('live_select_desc', { count: selectedQuestions.size })}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={selectAll}
                className="px-3 py-1.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
              >
                {t('live_select_all')}
              </button>
              <button
                onClick={startInterview}
                disabled={selectedQuestions.size === 0}
                className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 rounded-lg transition-colors"
              >
                {t('live_start_interview')}
              </button>
            </div>
          </div>

          {/* Category Weights */}
          {categoryWeights && (
            <div className="flex flex-wrap gap-2">
              {Object.entries(categoryWeights).map(([cat, weight]) => (
                <span key={cat} className="px-2 py-1 bg-indigo-50 text-indigo-700 text-xs rounded-full">
                  {cat}: {Math.round(weight * 100)}%
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Questions by Category */}
        {Object.entries(questionsByCategory).map(([category, categoryQuestions]) => (
          <div key={category} className="space-y-3">
            <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wide flex items-center gap-2">
              {category}
              <span className="text-xs font-normal text-gray-400">
                ({categoryQuestions.filter(q => selectedQuestions.has(q.id)).length}/{categoryQuestions.length})
              </span>
            </h4>
            {categoryQuestions.map((q) => (
              <button
                key={q.id}
                onClick={() => toggleQuestion(q.id)}
                className={`card-hover w-full text-left p-4 rounded-xl border transition-all ${
                  selectedQuestions.has(q.id)
                    ? 'bg-indigo-50 border-indigo-300 ring-1 ring-indigo-200'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center ${
                    selectedQuestions.has(q.id)
                      ? 'bg-indigo-600 border-indigo-600'
                      : 'border-gray-300'
                  }`}>
                    {selectedQuestions.has(q.id) && (
                      <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {q.title && (
                        <span className="font-semibold text-gray-900">{q.title}</span>
                      )}
                      {q.is_risk && (
                        <span className="px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded">{t('live_risk')}</span>
                      )}
                      <span className={`px-1.5 py-0.5 text-xs rounded ${
                        q.difficulty === 'Hard' ? 'bg-red-100 text-red-700' :
                        q.difficulty === 'Medium' ? 'bg-amber-100 text-amber-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {q.difficulty}
                      </span>
                      {q.time_allocation_minutes && (
                        <span className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                          {q.time_allocation_minutes} {t('live_minutes')}
                        </span>
                      )}
                      {q.evidence_quality && (
                        <span className={`px-1.5 py-0.5 text-xs rounded ${
                          q.evidence_quality === 'high' ? 'bg-emerald-100 text-emerald-700' :
                          q.evidence_quality === 'medium' ? 'bg-blue-100 text-blue-700' :
                          'bg-orange-100 text-orange-700'
                        }`}>
                          {t(`evidence_${q.evidence_quality}`)}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-2">{q.question_text}</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        ))}
      </div>
    )
  }

  // Interview Phase
  const currentQuestion = interviewQuestions[currentIndex]
  const currentScore = scores[currentQuestion?.id]

  if (!currentQuestion) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">{t('live_no_questions')}</p>
        <button
          onClick={() => setPhase('select')}
          className="mt-4 px-4 py-2 text-indigo-600 hover:bg-indigo-50 rounded-lg"
        >
          {t('live_back_to_select')}
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPhase('select')}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              {t('live_go_select')}
            </button>
            <span className="text-gray-300">|</span>
            <span className="text-sm font-medium text-gray-900">
              {t('live_question_progress', { current: currentIndex + 1, total: interviewQuestions.length })}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500">{t('live_total_score')}</span>
            <span className="text-lg font-bold text-indigo-600">{totalScore}</span>
            {maxScore > 0 && (
              <span className="text-sm text-gray-400">/ {maxScore}</span>
            )}
          </div>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-500 transition-all"
            style={{ width: `${((currentIndex + 1) / interviewQuestions.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Question Card */}
      <InterviewQuestionCard
        question={currentQuestion}
        questionIndex={currentIndex}
        score={currentScore}
        onScenarioSelect={handleScenarioSelect}
        onFollowUpScore={handleFollowUpScore}
      />

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
          disabled={currentIndex === 0}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {t('live_prev_question')}
        </button>
        <button
          onClick={() => setCurrentIndex(Math.min(interviewQuestions.length - 1, currentIndex + 1))}
          disabled={currentIndex === interviewQuestions.length - 1}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {t('live_next_question')}
        </button>
      </div>
    </div>
  )
})
