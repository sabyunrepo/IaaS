import { useTranslation } from 'react-i18next'
import type { InterviewerGuide } from '../../types/interview'

interface V1GuideTabProps {
  guide: InterviewerGuide
}

export function V1GuideTab({ guide }: V1GuideTabProps) {
  const { t } = useTranslation()

  return (
    <div className="space-y-6">
      {/* Interview Overview */}
      {guide.interview_overview && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('result_interview_overview')}</h2>
          <div className="grid gap-4 sm:grid-cols-4">
            <div className="text-center p-3 bg-em-50 rounded-lg">
              <div className="text-2xl font-bold text-em-700">
                {t('result_duration', { min: guide.interview_overview.total_duration_minutes })}
              </div>
              <div className="text-sm text-gray-500">{t('result_total_duration')}</div>
            </div>
            <div className="text-center p-3 bg-em-50 rounded-lg">
              <div className="text-2xl font-bold text-em-700">
                {t('result_count_unit', { count: guide.interview_overview.question_count })}
              </div>
              <div className="text-sm text-gray-500">{t('result_question_count_label')}</div>
            </div>
            <div className="text-center p-3 bg-em-50 rounded-lg">
              <div className="text-lg font-bold text-em-700">
                {guide.interview_overview.experience_level}
              </div>
              <div className="text-sm text-gray-500">{t('result_experience_level_label')}</div>
            </div>
            <div className="text-center p-3 bg-em-50 rounded-lg">
              <div className="text-lg font-bold text-em-700">
                {guide.interview_overview.interview_style}
              </div>
              <div className="text-sm text-gray-500">{t('result_interview_style')}</div>
            </div>
          </div>
        </div>
      )}

      {/* Interview Flow */}
      {guide.interview_flow && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('result_interview_flow_order')}</h2>
          <div className="space-y-4">
            {guide.interview_flow.opening && (
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <h3 className="font-medium text-green-900 mb-2">
                  🎬 {t('result_opening')} ({t('result_duration', { min: guide.interview_flow.opening.duration_minutes })})
                </h3>
                <p className="text-sm text-green-800">{guide.interview_flow.opening.script}</p>
              </div>
            )}
            {guide.interview_flow.main_body && (
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h3 className="font-medium text-blue-900 mb-2">📋 {t('result_main_interview')}</h3>
                <p className="text-sm text-blue-800 mb-2">
                  {t('result_flow_order')}: {guide.interview_flow.main_body.recommended_order?.join(' → ')}
                </p>
                {guide.interview_flow.main_body.transition_phrases && (
                  <div className="text-sm text-blue-700">
                    <p className="font-medium mb-1">{t('result_transition_phrases')}:</p>
                    <ul className="list-disc list-inside">
                      {guide.interview_flow.main_body.transition_phrases.map((phrase, i) => (
                        <li key={i}>{phrase}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            {guide.interview_flow.closing && (
              <div className="p-4 bg-em-50 rounded-lg border border-em-200">
                <h3 className="font-medium text-em-900 mb-2">
                  🏁 {t('result_closing')} ({t('result_duration', { min: guide.interview_flow.closing.duration_minutes })})
                </h3>
                <p className="text-sm text-em-800">{guide.interview_flow.closing.script}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Evaluation Matrix */}
      {guide.evaluation_matrix && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('result_evaluation_criteria')}</h2>
          <div className="grid gap-4 sm:grid-cols-3 mb-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-lg font-bold text-gray-900">
                {guide.evaluation_matrix.scoring_scale}
              </div>
              <div className="text-sm text-gray-500">{t('result_scoring_scale')}</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-lg font-bold text-green-600">
                ≥ {guide.evaluation_matrix.passing_threshold}
              </div>
              <div className="text-sm text-gray-500">{t('result_passing_threshold')}</div>
            </div>
            <div className="text-center p-3 bg-em-50 rounded-lg">
              <div className="text-lg font-bold text-em-700">
                ≥ {guide.evaluation_matrix.strong_hire_threshold}
              </div>
              <div className="text-sm text-gray-500">{t('result_strong_hire')}</div>
            </div>
          </div>
          {guide.evaluation_matrix.category_weights && (
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">{t('result_v1_category_weights')}</h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(guide.evaluation_matrix.category_weights).map(([cat, weight]) => (
                  <span key={cat} className="px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-sm">
                    {cat}: {Math.round(Number(weight) * 100)}%
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Red/Green Flags */}
      <div className="grid gap-6 sm:grid-cols-2">
        {guide.green_flags_summary && guide.green_flags_summary.length > 0 && (
          <div className="rounded-xl border border-green-200 bg-green-50 p-6">
            <h2 className="text-lg font-semibold text-green-900 mb-3">✅ {t('result_green_flags')}</h2>
            <ul className="space-y-2">
              {guide.green_flags_summary.map((flag, i) => (
                <li key={i} className="text-sm text-green-800 flex items-start gap-2">
                  <span className="text-green-500">•</span>
                  {flag}
                </li>
              ))}
            </ul>
          </div>
        )}
        {guide.red_flags_summary && guide.red_flags_summary.length > 0 && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6">
            <h2 className="text-lg font-semibold text-red-900 mb-3">🚩 {t('result_red_flags')}</h2>
            <ul className="space-y-2">
              {guide.red_flags_summary.map((flag, i) => (
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
  )
}
