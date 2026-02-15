/**
 * LiveInterviewTab - Question Selection → Interactive Scoring → Follow-up Branching
 */
import { memo, useState, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import type {
  InterviewQuestion,
  ScenarioLevelType,
  ScoresState
} from '../../types/interview'
import { InterviewQuestionCard } from './InterviewQuestionCard'

interface LiveInterviewTabProps {
  questions: InterviewQuestion[]
}

export const LiveInterviewTab = memo(function LiveInterviewTab({ questions }: LiveInterviewTabProps) {
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

  const [phase, setPhase] = useState<'select' | 'interview' | 'summary'>('select')
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
                className="px-3 py-1.5 text-sm font-medium text-navy-700 hover:bg-navy-50 rounded-lg transition-colors"
              >
                {t('live_select_all')}
              </button>
              <button
                onClick={startInterview}
                disabled={selectedQuestions.size === 0}
                className="px-4 py-1.5 text-sm font-medium text-white bg-navy-700 hover:bg-navy-800 disabled:bg-gray-300 rounded-lg transition-colors"
              >
                {t('live_start_interview')}
              </button>
            </div>
          </div>

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
                    ? 'bg-navy-50 border-navy-300 ring-1 ring-navy-200'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center ${
                    selectedQuestions.has(q.id)
                      ? 'bg-navy-700 border-navy-700'
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
                        q.difficulty === 'Medium' ? 'bg-brand-100 text-brand-700' :
                        'bg-green-100 text-green-700'
                      }`}>
                        {q.difficulty}
                      </span>
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

  // Summary Phase — 면접 완료 후 결과 요약
  if (phase === 'summary') {
    const scorePercent = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0
    const scoredCount = Object.keys(scores).length

    // 카테고리별 점수 집계
    const categoryScores: Record<string, { total: number; max: number; count: number }> = {}
    interviewQuestions.forEach(q => {
      const cat = q.category || t('live_other')
      if (!categoryScores[cat]) categoryScores[cat] = { total: 0, max: 0, count: 0 }
      categoryScores[cat].count++
      const s = scores[q.id]
      if (s) {
        categoryScores[cat].total += s.totalScore
        categoryScores[cat].max += s.maxPossibleScore
      }
    })

    return (
      <div className="space-y-6">
        {/* 총점 헤더 */}
        <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-sm text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-1">{t('live_interview_complete')}</h3>
          <p className="text-sm text-gray-500 mb-6">
            {t('live_scored_count', { scored: scoredCount, total: interviewQuestions.length })}
          </p>
          <div className="text-5xl font-bold text-navy-700 mb-2">
            {scorePercent}%
          </div>
          <p className="text-sm text-gray-500">
            {totalScore} / {maxScore} {t('live_points_unit')}
          </p>
        </div>

        {/* 카테고리별 점수 */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h4 className="text-base font-semibold text-gray-900 mb-4">{t('live_category_scores')}</h4>
          <div className="space-y-3">
            {Object.entries(categoryScores).map(([cat, data]) => {
              const pct = data.max > 0 ? Math.round((data.total / data.max) * 100) : 0
              return (
                <div key={cat}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="font-medium text-gray-700">{cat}</span>
                    <span className="text-gray-500">{data.total}/{data.max} ({pct}%)</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-brand-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* 액션 버튼 */}
        <div className="flex justify-center gap-3">
          <button
            onClick={() => { setPhase('interview'); setCurrentIndex(0) }}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            {t('live_review_questions')}
          </button>
          <button
            onClick={() => { setPhase('select'); setCurrentIndex(0); setScores({}); setSelectedQuestions(new Set()) }}
            className="px-4 py-2 text-sm font-medium text-white bg-navy-700 rounded-lg hover:bg-navy-800"
          >
            {t('live_new_interview')}
          </button>
        </div>
      </div>
    )
  }

  // Interview Phase
  const currentQuestion = interviewQuestions[currentIndex]
  const currentScore = scores[currentQuestion?.id]
  const isLastQuestion = currentIndex === interviewQuestions.length - 1

  if (!currentQuestion) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">{t('live_no_questions')}</p>
        <button
          onClick={() => setPhase('select')}
          className="mt-4 px-4 py-2 text-navy-700 hover:bg-navy-50 rounded-lg"
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
            <span className="text-lg font-bold text-navy-700">{totalScore}</span>
            {maxScore > 0 && (
              <span className="text-sm text-gray-400">/ {maxScore}</span>
            )}
          </div>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-navy-500 transition-all"
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
        {isLastQuestion ? (
          <button
            onClick={() => setPhase('summary')}
            className="px-6 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700"
          >
            {t('live_finish_interview')}
          </button>
        ) : (
          <button
            onClick={() => setCurrentIndex(currentIndex + 1)}
            className="px-4 py-2 text-sm font-medium text-white bg-navy-700 rounded-lg hover:bg-navy-800"
          >
            {t('live_next_question')}
          </button>
        )}
      </div>
    </div>
  )
})
