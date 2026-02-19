/**
 * InterviewQuestionCard - Individual question card with scenario scoring and follow-ups
 * Extracted from LiveInterviewTab.tsx for SRP compliance
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type {
  InterviewQuestion,
  ScenarioLevelType,
  QuestionScoreState,
  EvaluationScenarioDetail,
  FollowUpQuestionExtra
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
  const [expandedKeyword, setExpandedKeyword] = useState<number | null>(null)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      {/* Question Header */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-em-100 text-em-800 font-semibold">
            {questionIndex + 1}
          </span>
          {question.title && (
            <span className="font-semibold text-gray-900">{question.title}</span>
          )}
          {question.is_risk && (
            <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">{t('live_risk_verify')}</span>
          )}
          {question.evidence_quality && (
            <span className={`px-2 py-0.5 text-xs rounded-full ${
              question.evidence_quality === 'high' ? 'bg-emerald-100 text-emerald-700' :
              question.evidence_quality === 'medium' ? 'bg-blue-100 text-blue-700' :
              'bg-gray-100 text-gray-500'
            }`}>
              {t(`evidence_${question.evidence_quality}`)}
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

      {/* Answer Keywords — tap to expand explanation */}
      {question.answer_keywords && question.answer_keywords.length > 0 && (
        <div className="mb-6">
          <h5 className="text-sm font-semibold text-gray-700 mb-2">{t('live_keywords')}</h5>
          <div className="flex flex-wrap gap-2">
            {question.answer_keywords.map((kw, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setExpandedKeyword(expandedKeyword === i ? null : i)}
                className={`px-2 py-1 rounded-full text-xs font-medium transition-colors ${
                  kw.importance === 'must'
                    ? 'bg-red-100 text-red-700 border border-red-200 hover:bg-red-200'
                    : 'bg-gray-100 text-gray-700 border border-gray-200 hover:bg-gray-200'
                } ${expandedKeyword === i ? 'ring-2 ring-em-300' : ''}`}
              >
                {kw.keyword}
                <span className="ml-1 text-[10px] opacity-60">
                  {kw.importance === 'must' ? t('live_keyword_must') : t('live_keyword_nice')}
                </span>
              </button>
            ))}
          </div>
          {expandedKeyword !== null && question.answer_keywords[expandedKeyword]?.explanation && (
            <div className="mt-2 p-3 bg-em-50 rounded-lg border border-em-200 text-sm text-em-800 animate-fadeIn">
              <strong>{question.answer_keywords[expandedKeyword].keyword}:</strong>{' '}
              {question.answer_keywords[expandedKeyword].explanation}
            </div>
          )}
        </div>
      )}

      {/* Terminology — plain language explanations for non-developers */}
      {question.terminology && question.terminology.length > 0 && (
        <div className="mb-6">
          <h5 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-1.5">
            <svg className="w-4 h-4 text-em-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            {t('live_terminology')}
          </h5>
          <div className="space-y-2">
            {question.terminology.map((term, i) => (
              <div key={i} className="p-3 bg-em-50 rounded-lg border border-em-200">
                <div className="font-medium text-sm text-em-900">{term.term}</div>
                <div className="text-sm text-em-800 mt-1">
                  {term.plain_language_explanation || term.definition}
                </div>
                {(term.business_context || term.business_relevance) && (
                  <div className="text-xs text-em-700 mt-1">
                    <strong>{t('live_term_business')}</strong> {term.business_context || term.business_relevance}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Code Reference — shows which code file this question is based on */}
      {question.code_reference && (question.code_reference.file || question.code_reference.snippet) && (
        <div className="mb-6 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <h5 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-1.5">
            <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
            {t('live_code_reference')}
          </h5>
          {question.code_reference.file && (
            <div className="text-xs font-mono text-gray-600 mb-1">
              {question.code_reference.file}
              {question.code_reference.lines && `:${question.code_reference.lines}`}
            </div>
          )}
          {question.code_reference.snippet && (
            <pre className="text-xs font-mono bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto max-h-32">
              <code>{question.code_reference.snippet}</code>
            </pre>
          )}
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
                  ? 'border-em-600 bg-em-50 ring-2 ring-em-200'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`font-semibold ${
                  scenario.level === 'Expert' ? 'text-emerald-700' :
                  scenario.level === 'Mid' ? 'text-em-700' :
                  'text-red-700'
                }`}>
                  {scenario.level === 'Expert' ? `🌟 ${t('scenario_expert')}` :
                   scenario.level === 'Mid' ? `📊 ${t('scenario_mid')}` : `📉 ${t('scenario_low')}`}
                </span>
                <span className="text-lg font-bold text-em-700">{t('live_points', { score: scenario.score })}</span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{scenario.text}</p>
              <p className="text-xs text-gray-500">{scenario.depth_expectations}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Evaluation Guidance (shown after scenario selection) */}
      {score?.selectedLevel && question.evaluation_scenarios && (() => {
        const levelMap: Record<ScenarioLevelType, EvaluationScenarioDetail | undefined> = {
          Expert: question.evaluation_scenarios?.expert,
          Mid: question.evaluation_scenarios?.mid_level,
          Low: question.evaluation_scenarios?.low_level,
        }
        const detail = levelMap[score.selectedLevel]
        if (!detail) return null
        return (
          <div className="mb-6 p-4 bg-violet-50 rounded-xl border border-violet-200 animate-fadeIn">
            <h5 className="text-xs font-semibold text-violet-700 uppercase mb-3">{t('live_eval_guidance')}</h5>
            {detail.description && (
              <p className="text-sm text-violet-900 mb-3">{detail.description}</p>
            )}
            {detail.trigger_keywords && detail.trigger_keywords.length > 0 && (
              <div className="mb-3">
                <span className="text-xs font-semibold text-violet-700">{t('live_trigger_keywords')}</span>
                <div className="flex flex-wrap gap-1.5 mt-1">
                  {detail.trigger_keywords.map((kw, i) => (
                    <span key={i} className="px-2 py-0.5 bg-violet-100 text-violet-800 text-xs rounded-full border border-violet-200">
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {detail.behavioral_indicators && detail.behavioral_indicators.length > 0 && (
              <div className="mb-3">
                <span className="text-xs font-semibold text-violet-700">{t('live_behavioral_indicators')}</span>
                <ul className="mt-1 space-y-1">
                  {detail.behavioral_indicators.map((ind, i) => (
                    <li key={i} className="text-sm text-violet-800 flex items-start gap-1.5">
                      <span className="mt-0.5 shrink-0">•</span> {ind}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {detail.coaching_tip && (
              <div className="p-2 bg-em-50 rounded-lg border border-em-200 text-sm text-em-800">
                <strong>{t('live_coaching_tip')}</strong> {detail.coaching_tip}
              </div>
            )}
            {detail.recovery_question && (
              <div className="p-2 bg-blue-50 rounded-lg border border-blue-200 text-sm text-blue-800 mt-2">
                <strong>{t('live_recovery_question')}</strong> {detail.recovery_question}
              </div>
            )}
            {detail.follow_up_direction && (
              <div className="p-2 bg-green-50 rounded-lg border border-green-200 text-sm text-green-800 mt-2">
                <strong>{t('live_follow_up_direction')}</strong> {detail.follow_up_direction}
              </div>
            )}
          </div>
        )
      })()}

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
                      <span className="text-xs font-semibold text-green-700">{t('live_followup_good')} ({followUp.good.score}{t('live_followup_pts')})</span>
                      <p className="text-sm text-green-800 mt-1">{followUp.good.text}</p>
                    </div>
                    <div className="p-2 bg-red-50 rounded-lg border border-red-200">
                      <span className="text-xs font-semibold text-red-700">{t('live_followup_poor')} ({followUp.poor.score}{t('live_followup_pts')})</span>
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

      {/* Additional Follow-up Questions (purpose + expected insight) */}
      {score?.selectedLevel && question.follow_up_questions && question.follow_up_questions.length > 0 && (() => {
        const filtered = question.follow_up_questions.filter(
          (fq: FollowUpQuestionExtra) => !fq.trigger || fq.trigger.toLowerCase() === 'any' || fq.trigger.toLowerCase() === score.selectedLevel?.toLowerCase()
        )
        if (filtered.length === 0) return null
        return (
          <div className="border-t border-gray-200 pt-6 mb-6">
            <h5 className="text-sm font-semibold text-gray-700 mb-3">{t('live_extra_follow_ups')}</h5>
            <div className="space-y-3">
              {filtered.map((fq: FollowUpQuestionExtra, i: number) => (
                <div key={i} className="p-4 bg-teal-50 rounded-xl border border-teal-200">
                  <p className="font-medium text-gray-900 mb-2">{fq.question_text}</p>
                  {fq.purpose && (
                    <p className="text-sm text-teal-800 mb-1">
                      <strong>{t('live_fuq_purpose')}</strong> {fq.purpose}
                    </p>
                  )}
                  {fq.expected_insight && (
                    <p className="text-sm text-teal-700">
                      <strong>{t('live_fuq_expected')}</strong> {fq.expected_insight}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )
      })()}

      {/* Interviewer Note */}
      {question.interviewer_note && (
        <div className="mt-6 p-4 bg-em-50 rounded-xl border border-em-200">
          <h5 className="text-xs font-semibold text-em-800 uppercase mb-2">{t('live_interviewer_note')}</h5>
          {question.interviewer_note.business_interpretation && (
            <p className="text-sm text-em-800 mb-2">
              <strong>{t('live_business_interpretation')}</strong> {question.interviewer_note.business_interpretation}
            </p>
          )}
          {question.interviewer_note.daily_analogy && (
            <p className="text-sm text-em-800 mb-2">
              <strong>{t('live_daily_analogy')}</strong> {question.interviewer_note.daily_analogy}
            </p>
          )}
          {question.interviewer_note.level_expectation && (
            <p className="text-sm text-em-800 mb-2">
              <strong>{t('live_level_expectation')}</strong> {question.interviewer_note.level_expectation}
            </p>
          )}
          {question.interviewer_note.what_to_listen_for && (
            <p className="text-sm text-em-800 mb-2">
              <strong>{t('live_listen_for')}</strong> {question.interviewer_note.what_to_listen_for}
            </p>
          )}
          {question.interviewer_note.green_flags && question.interviewer_note.green_flags.length > 0 && (
            <div className="mt-2">
              <strong className="text-xs text-emerald-700">{t('live_green_flags')}</strong>
              <ul className="mt-1 space-y-1">
                {question.interviewer_note.green_flags.map((flag, i) => (
                  <li key={i} className="text-sm text-emerald-700 flex items-start gap-1.5">
                    <span className="mt-0.5 shrink-0">✅</span> {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {question.interviewer_note.red_flags && question.interviewer_note.red_flags.length > 0 && (
            <div className="mt-2">
              <strong className="text-xs text-red-700">{t('live_red_flags')}</strong>
              <ul className="mt-1 space-y-1">
                {question.interviewer_note.red_flags.map((flag, i) => (
                  <li key={i} className="text-sm text-red-700 flex items-start gap-1.5">
                    <span className="mt-0.5 shrink-0">⚠️</span> {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {question.interviewer_note.time_guidance && (
            <p className="text-xs text-em-700 mt-2 italic">
              {question.interviewer_note.time_guidance}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
