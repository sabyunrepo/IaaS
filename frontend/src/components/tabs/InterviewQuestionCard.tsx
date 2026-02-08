/**
 * InterviewQuestionCard - Individual question card with scenario scoring and follow-ups
 * Extracted from LiveInterviewTab.tsx for SRP compliance
 */
import { useTranslation } from 'react-i18next'
import type {
  InterviewQuestion,
  ScenarioLevelType,
  QuestionScoreState
} from '../../types/interview'

interface InterviewQuestionCardProps {
  question: InterviewQuestion
  questionIndex: number
  score: QuestionScoreState | undefined
  onScenarioSelect: (questionId: string, level: ScenarioLevelType, score: number) => void
  onFollowUpScore: (questionId: string, followUpId: string, score: number) => void
}

export function InterviewQuestionCard({
  question,
  questionIndex,
  score,
  onScenarioSelect,
  onFollowUpScore
}: InterviewQuestionCardProps) {
  const { t } = useTranslation()

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      {/* Question Header */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 font-semibold">
            {questionIndex + 1}
          </span>
          {question.title && (
            <span className="font-semibold text-gray-900">{question.title}</span>
          )}
          {question.is_risk && (
            <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">{t('live_risk_verify')}</span>
          )}
          {question.time_allocation_minutes && (
            <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
              {question.time_allocation_minutes}{t('live_minutes')}
            </span>
          )}
        </div>
        <p className="text-lg text-gray-900">{question.question_text}</p>
      </div>

      {/* Why Matters & Listen For */}
      <div className="grid sm:grid-cols-2 gap-4 mb-6">
        {question.why_matters && (
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <h5 className="text-xs font-semibold text-blue-700 uppercase mb-1">{t('live_why_matters')}</h5>
            <p className="text-sm text-blue-800">{question.why_matters}</p>
          </div>
        )}
        {question.listen_for && (
          <div className="p-3 bg-green-50 rounded-lg border border-green-200">
            <h5 className="text-xs font-semibold text-green-700 uppercase mb-1">{t('live_listen_for')}</h5>
            <p className="text-sm text-green-800">{question.listen_for}</p>
          </div>
        )}
      </div>

      {/* Answer Keywords */}
      {question.answer_keywords && question.answer_keywords.length > 0 && (
        <div className="mb-6">
          <h5 className="text-sm font-semibold text-gray-700 mb-2">{t('live_keywords')}</h5>
          <div className="flex flex-wrap gap-2">
            {question.answer_keywords.map((kw, i) => (
              <span
                key={i}
                className={`px-2 py-1 rounded-full text-xs font-medium ${
                  kw.importance === 'must'
                    ? 'bg-red-100 text-red-700 border border-red-200'
                    : 'bg-gray-100 text-gray-700 border border-gray-200'
                }`}
                title={kw.explanation}
              >
                {kw.keyword}
                {kw.importance === 'must' && ' *'}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Scenario Selection */}
      <div className="mb-6">
        <h5 className="text-sm font-semibold text-gray-700 mb-3">{t('live_scenario_eval')}</h5>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {question.scenarios.map((scenario) => (
            <button
              key={scenario.level}
              onClick={() => onScenarioSelect(question.id, scenario.level, scenario.score)}
              className={`card-hover p-4 rounded-xl border-2 text-left transition-all ${
                score?.selectedLevel === scenario.level
                  ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-200'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`font-semibold ${
                  scenario.level === 'Expert' ? 'text-emerald-700' :
                  scenario.level === 'Mid' ? 'text-amber-700' :
                  'text-red-700'
                }`}>
                  {scenario.level === 'Expert' ? `🌟 ${t('scenario_expert')}` :
                   scenario.level === 'Mid' ? `📊 ${t('scenario_mid')}` : `📉 ${t('scenario_low')}`}
                </span>
                <span className="text-lg font-bold text-indigo-600">{t('live_points', { score: scenario.score })}</span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{scenario.text}</p>
              <p className="text-xs text-gray-500">{scenario.depth_expectations}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Follow-up Questions (shown after scenario selection) */}
      {score?.selectedLevel && question.follow_ups && question.follow_ups.length > 0 && (
        <div className="border-t border-gray-200 pt-6">
          <h5 className="text-sm font-semibold text-gray-700 mb-3">{t('live_follow_ups')}</h5>
          <div className="space-y-4">
            {question.follow_ups
              .filter(fu => fu.trigger === 'any' || fu.trigger === score.selectedLevel)
              .map((followUp) => (
                <div key={followUp.id} className="card-hover p-4 bg-gray-50 rounded-xl border border-gray-200">
                  <p className="font-medium text-gray-900 mb-2">{followUp.question_text}</p>
                  <div className="grid sm:grid-cols-2 gap-3 mb-3">
                    <div className="p-2 bg-green-50 rounded-lg border border-green-200">
                      <span className="text-xs font-semibold text-green-700">Good ({followUp.good.score}pts)</span>
                      <p className="text-sm text-green-800 mt-1">{followUp.good.text}</p>
                    </div>
                    <div className="p-2 bg-red-50 rounded-lg border border-red-200">
                      <span className="text-xs font-semibold text-red-700">Poor ({followUp.poor.score}pts)</span>
                      <p className="text-sm text-red-800 mt-1">{followUp.poor.text}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => onFollowUpScore(question.id, followUp.id, followUp.good.score)}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                        score.followUpScores[followUp.id] === followUp.good.score
                          ? 'bg-green-600 text-white'
                          : 'bg-green-100 text-green-700 hover:bg-green-200'
                      }`}
                    >
                      Good +{followUp.good.score}
                    </button>
                    <button
                      onClick={() => onFollowUpScore(question.id, followUp.id, followUp.poor.score)}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                        score.followUpScores[followUp.id] === followUp.poor.score
                          ? 'bg-red-600 text-white'
                          : 'bg-red-100 text-red-700 hover:bg-red-200'
                      }`}
                    >
                      Poor +{followUp.poor.score}
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Interviewer Note */}
      {question.interviewer_note && (
        <div className="mt-6 p-4 bg-indigo-50 rounded-xl border border-indigo-200">
          <h5 className="text-xs font-semibold text-indigo-700 uppercase mb-2">{t('live_interviewer_note')}</h5>
          {question.interviewer_note.business_interpretation && (
            <p className="text-sm text-indigo-800 mb-2">
              <strong>{t('live_business_interpretation')}</strong> {question.interviewer_note.business_interpretation}
            </p>
          )}
          {question.interviewer_note.daily_analogy && (
            <p className="text-sm text-indigo-800 mb-2">
              <strong>{t('live_daily_analogy')}</strong> {question.interviewer_note.daily_analogy}
            </p>
          )}
          {question.interviewer_note.level_expectation && (
            <p className="text-sm text-indigo-800">
              <strong>{t('live_level_expectation')}</strong> {question.interviewer_note.level_expectation}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
