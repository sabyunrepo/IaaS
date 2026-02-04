/**
 * DecisionTab - JD Competency Achievement + Hiring Recommendation
 */
import type { DecisionSupport, Candidate, CategoryWeights } from '../../types/interview'

interface DecisionTabProps {
  decision: DecisionSupport
  candidate?: Candidate
  categoryWeights?: CategoryWeights
  totalScore?: number
  maxScore?: number
}

export function DecisionTab({
  decision,
  candidate,
  categoryWeights,
  totalScore = 0,
  maxScore = 100
}: DecisionTabProps) {
  const { summary, interviewer_guide, jd_competency_map } = decision
  const scorePercent = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0

  // Determine recommendation based on score
  const getRecommendation = () => {
    if (scorePercent >= 80) return { label: 'Strong Hire', color: 'emerald', icon: '🌟' }
    if (scorePercent >= 60) return { label: 'Hire', color: 'green', icon: '✅' }
    if (scorePercent >= 40) return { label: 'Leaning No', color: 'amber', icon: '⚠️' }
    return { label: 'No Hire', color: 'red', icon: '❌' }
  }

  const recommendation = getRecommendation()

  return (
    <div className="space-y-6">
      {/* Score Summary Card */}
      <div className={`bg-gradient-to-r ${
        recommendation.color === 'emerald' ? 'from-emerald-500 to-teal-600' :
        recommendation.color === 'green' ? 'from-green-500 to-emerald-600' :
        recommendation.color === 'amber' ? 'from-amber-500 to-orange-600' :
        'from-red-500 to-rose-600'
      } rounded-xl p-6 text-white shadow-lg`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium opacity-90">채용 추천</h3>
            <p className="text-4xl font-bold mt-1">{recommendation.icon} {recommendation.label}</p>
            {candidate && (
              <p className="text-sm opacity-80 mt-2">{candidate.name} · {candidate.role || candidate.current_title}</p>
            )}
          </div>
          <div className="text-right">
            <div className="text-5xl font-bold">{scorePercent}%</div>
            <div className="text-sm opacity-80">{totalScore} / {maxScore} 점</div>
          </div>
        </div>
      </div>

      {/* Decision Summary */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          후보자 요약
        </h3>

        <div className="grid sm:grid-cols-3 gap-4 mb-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">경력</div>
            <div className="font-semibold text-gray-900">{summary.experience}</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">JD 매칭</div>
            <div className="font-semibold text-gray-900">{summary.jd_match}</div>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-500">레벨</div>
            <div className="font-semibold text-gray-900">{summary.level}</div>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-6">
          {/* Strengths */}
          <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
            <h4 className="font-semibold text-emerald-900 mb-3 flex items-center gap-2">
              <span>✅</span> 강점
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
          <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
            <h4 className="font-semibold text-amber-900 mb-3 flex items-center gap-2">
              <span>⚠️</span> 우려 사항
            </h4>
            <ul className="space-y-2">
              {summary.concerns.map((concern, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-amber-800">
                  <span className="text-amber-500 mt-0.5">•</span>
                  {concern}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* JD Competency Map */}
      {jd_competency_map && jd_competency_map.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            JD 역량 달성도
          </h3>

          <div className="space-y-4">
            {jd_competency_map.map((comp, i) => (
              <div key={i} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900">{comp.competency}</span>
                  <span className="text-sm text-indigo-600 font-semibold">
                    가중치: {Math.round(comp.weight * 100)}%
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
                  <div
                    className="h-full bg-indigo-500 rounded-full"
                    style={{ width: `${comp.weight * 100}%` }}
                  />
                </div>
                {comp.related_questions.length > 0 && (
                  <p className="text-xs text-gray-500">
                    관련 질문: Q{comp.related_questions.join(', Q')}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Category Weights (if provided separately) */}
      {categoryWeights && Object.keys(categoryWeights).length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">카테고리별 가중치</h3>
          <div className="space-y-3">
            {Object.entries(categoryWeights).map(([cat, weight]) => (
              <div key={cat} className="flex items-center gap-4">
                <span className="w-32 text-sm text-gray-600">{cat}</span>
                <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full"
                    style={{ width: `${weight * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-700 w-12 text-right">
                  {Math.round(weight * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interviewer Guide Tips */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          면접관 가이드
        </h3>

        {/* Interview Flow */}
        {interviewer_guide.interview_flow && (
          <div className="mb-6 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
            <h4 className="text-sm font-semibold text-indigo-900 mb-2">면접 진행</h4>
            <p className="text-sm text-indigo-800">{interviewer_guide.interview_flow}</p>
          </div>
        )}

        {/* Time Allocation */}
        {interviewer_guide.time_allocation && Object.keys(interviewer_guide.time_allocation).length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">시간 배분</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(interviewer_guide.time_allocation).map(([phase, time]) => (
                <span key={phase} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                  {phase}: {time}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Resume Tips */}
        {interviewer_guide.resume_based_tips && interviewer_guide.resume_based_tips.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">이력서 기반 팁</h4>
            <div className="space-y-2">
              {interviewer_guide.resume_based_tips.map((tip, i) => (
                <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <span className="text-xs font-semibold text-gray-500 uppercase">{tip.section}</span>
                  <p className="text-sm text-gray-700 mt-1">{tip.insight}</p>
                  {tip.question_link && (
                    <p className="text-xs text-indigo-600 mt-1">→ {tip.question_link}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cover Letter Insights */}
        {interviewer_guide.cover_letter_insights && interviewer_guide.cover_letter_insights.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">자기소개서 인사이트</h4>
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

        {/* Red/Green Flags */}
        <div className="grid sm:grid-cols-2 gap-4">
          {interviewer_guide.positive_signals && interviewer_guide.positive_signals.length > 0 && (
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <h4 className="text-sm font-semibold text-green-900 mb-2">✅ 긍정 신호</h4>
              <ul className="space-y-1">
                {interviewer_guide.positive_signals.map((signal, i) => (
                  <li key={i} className="text-sm text-green-800 flex items-start gap-2">
                    <span className="text-green-500">•</span>
                    {signal}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {interviewer_guide.red_flags_to_watch && interviewer_guide.red_flags_to_watch.length > 0 && (
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <h4 className="text-sm font-semibold text-red-900 mb-2">🚩 주의 사항</h4>
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
      </div>
    </div>
  )
}
