/**
 * DecisionTab - Hiring Recommendation + Interviewer Guide
 *
 * 중복 데이터 정리 (GitHub #270):
 * - candidate 기본정보 → IntelBriefTab에서만 표시
 * - riskFlags → DeepAnalysisTab에서만 표시
 * - categoryWeights → LiveInterviewTab에서만 표시
 * - dataConfidence → DeepAnalysisTab에서만 표시
 * - experience/jd_match/level → IntelBriefTab candidate에서만 표시
 */
import { memo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { DecisionSupport } from '../../types/interview'

interface DecisionTabProps {
  decision: DecisionSupport
  overallMatch?: number
}

export const DecisionTab = memo(function DecisionTab({
  decision,
  overallMatch = 0,
}: DecisionTabProps) {
  const { t } = useTranslation()
  const { summary, interviewer_guide } = decision
  const scorePercent = Math.round(Math.min(Math.max(overallMatch, 0), 100))

  // Determine recommendation based on score
  const getRecommendation = () => {
    if (scorePercent >= 80) return { label: t('rec_strong_hire'), desc: t('rec_strong_hire_desc'), color: 'emerald', icon: '🌟' }
    if (scorePercent >= 60) return { label: t('rec_hire'), desc: t('rec_hire_desc'), color: 'green', icon: '✅' }
    if (scorePercent >= 40) return { label: t('rec_leaning_no'), desc: t('rec_leaning_no_desc'), color: 'amber', icon: '⚠️' }
    return { label: t('rec_no_hire'), desc: t('rec_no_hire_desc'), color: 'red', icon: '❌' }
  }

  const recommendation = getRecommendation()
  const [guideExpanded, setGuideExpanded] = useState(true)

  return (
    <div className="space-y-6">
      {/* Score Summary Card */}
      <div className={`bg-gradient-to-r ${
        recommendation.color === 'emerald' ? 'from-emerald-500 to-teal-600' :
        recommendation.color === 'green' ? 'from-green-500 to-emerald-600' :
        recommendation.color === 'amber' ? 'from-brand-500 to-orange-600' :
        'from-red-500 to-rose-600'
      } rounded-xl p-6 text-white shadow-lg`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium opacity-90">{t('decision_recommendation')}</h3>
            <p className="text-2xl sm:text-4xl font-bold mt-1">{recommendation.icon} {recommendation.label}</p>
            <p className="text-sm opacity-70 mt-1">{recommendation.desc}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl sm:text-5xl font-bold">{scorePercent}%</div>
            <div className="text-sm opacity-80">{t('decision_overall_match')}</div>
          </div>
        </div>
      </div>

      {/* Score Threshold Guide - shows how score maps to recommendation */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {t('decision_score_guide')}
        </h4>
        <div className="relative h-3 rounded-full overflow-hidden flex">
          <div className="h-full bg-red-400" style={{ width: '40%' }} />
          <div className="h-full bg-brand-400" style={{ width: '20%' }} />
          <div className="h-full bg-green-400" style={{ width: '20%' }} />
          <div className="h-full bg-emerald-400" style={{ width: '20%' }} />
          {/* Score indicator */}
          <div
            className="absolute top-0 h-full w-0.5 bg-gray-900"
            style={{ left: `${Math.min(scorePercent, 100)}%` }}
          />
        </div>
        <div className="flex text-[10px] text-gray-500 mt-1.5">
          <div className="w-[40%] text-center">
            <span className="text-red-600 font-medium">{t('rec_no_hire')}</span>
            <span className="text-gray-400 ml-1">0-39%</span>
          </div>
          <div className="w-[20%] text-center">
            <span className="text-brand-600 font-medium">{t('rec_leaning_no')}</span>
            <span className="text-gray-400 ml-1">40-59%</span>
          </div>
          <div className="w-[20%] text-center">
            <span className="text-green-600 font-medium">{t('rec_hire')}</span>
            <span className="text-gray-400 ml-1">60-79%</span>
          </div>
          <div className="w-[20%] text-center">
            <span className="text-emerald-600 font-medium">{t('rec_strong_hire')}</span>
            <span className="text-gray-400 ml-1">80%+</span>
          </div>
        </div>
      </div>

      {/* Decision Summary */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-navy-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {t('decision_candidate_summary')}
        </h3>

        {/* Level Evidence */}
        {summary.level_evidence && (
          <div className="p-4 bg-navy-50 rounded-lg border border-navy-200 mb-6">
            <div className="text-sm font-medium text-navy-900">{t('decision_level_evidence')}</div>
            <div className="text-sm text-navy-800 mt-1">{summary.level_evidence}</div>
          </div>
        )}

        <div className="grid sm:grid-cols-2 gap-6">
          {/* Strengths */}
          <div className="card-hover p-4 bg-emerald-50 rounded-xl border border-emerald-200">
            <h4 className="font-semibold text-emerald-900 mb-3 flex items-center gap-2">
              <span>✅</span> {t('decision_strengths')}
            </h4>
            <ul className="space-y-2">
              {summary.strengths.map((strength, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-emerald-800">
                  <span className="text-emerald-500 mt-0.5">•</span>
                  {strength}
                </li>
              ))}
            </ul>
          </div>

          {/* Concerns */}
          <div className="card-hover p-4 bg-brand-50 rounded-xl border border-brand-200">
            <h4 className="font-semibold text-brand-900 mb-3 flex items-center gap-2">
              <span>⚠️</span> {t('decision_concerns')}
            </h4>
            <ul className="space-y-2">
              {summary.concerns.map((concern, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-brand-800">
                  <span className="text-brand-500 mt-0.5">•</span>
                  {concern}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Interviewer Guide Tips */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <button
          onClick={() => setGuideExpanded(!guideExpanded)}
          className="w-full p-6 flex items-center justify-between text-left"
        >
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <svg className="w-5 h-5 text-navy-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {t('decision_interviewer_guide')}
          </h3>
          <svg className={`w-5 h-5 text-gray-400 transition-transform ${guideExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {guideExpanded && (
        <div className="px-6 pb-6 space-y-6 animate-fadeIn">
        {/* Resume Tips */}
        {interviewer_guide.resume_based_tips && interviewer_guide.resume_based_tips.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">{t('decision_resume_tips')}</h4>
            <div className="space-y-2">
              {interviewer_guide.resume_based_tips.map((tip, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <span className="text-xs font-semibold text-gray-500 uppercase">{tip.section}</span>
                  <p className="text-sm text-gray-700 mt-1">{tip.insight}</p>
                  {tip.question_link && (
                    <p className="text-xs text-navy-700 mt-1">→ {tip.question_link}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cover Letter Insights */}
        {interviewer_guide.cover_letter_insights && interviewer_guide.cover_letter_insights.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">{t('decision_cover_letter_insights')}</h4>
            <div className="space-y-2">
              {interviewer_guide.cover_letter_insights.map((insight, i) => (
                <div key={i} className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm font-medium text-blue-900">{insight.highlight}</p>
                  <p className="text-sm text-blue-700 mt-1">{insight.interpretation}</p>
                  {insight.follow_up_opportunity && (
                    <p className="text-xs text-blue-600 mt-1">💡 {insight.follow_up_opportunity}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Red Flags */}
        {interviewer_guide.red_flags_to_watch && interviewer_guide.red_flags_to_watch.length > 0 && (
          <div className="p-4 bg-red-50 rounded-lg border border-red-200">
            <h4 className="text-sm font-semibold text-red-900 mb-2">🚩 {t('decision_red_flags')}</h4>
            <ul className="space-y-1">
              {interviewer_guide.red_flags_to_watch.map((flag, i) => (
                <li key={i} className="text-sm text-red-800 flex items-start gap-2">
                  <span className="text-red-500">•</span>
                  {flag}
                </li>
              ))}
            </ul>
          </div>
        )}
        </div>
        )}
      </div>

    </div>
  )
})
