import { useTranslation } from 'react-i18next'
import type { CandidateSummary } from '../../types/interview'

interface V1SummaryTabProps {
  summary: CandidateSummary
}

export function V1SummaryTab({ summary }: V1SummaryTabProps) {
  const { t } = useTranslation()

  return (
    <div className="space-y-6">
      {/* Candidate Overview */}
      {summary.candidate_overview && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="h-5 w-5 text-navy-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            {t('result_candidate_overview')}
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {summary.candidate_overview.name && (
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('result_name')}</dt>
                <dd className="mt-1 text-lg font-semibold text-gray-900">{summary.candidate_overview.name}</dd>
              </div>
            )}
            {summary.candidate_overview.current_position && (
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('result_current_position')}</dt>
                <dd className="mt-1 text-gray-900">{summary.candidate_overview.current_position}</dd>
              </div>
            )}
            {summary.candidate_overview.primary_domain && (
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('result_primary_domain')}</dt>
                <dd className="mt-1 text-gray-900">{summary.candidate_overview.primary_domain}</dd>
              </div>
            )}
            {summary.candidate_overview.experience_years && (
              <div>
                <dt className="text-sm font-medium text-gray-500">{t('result_v1_experience')}</dt>
                <dd className="mt-1 text-gray-900">{summary.candidate_overview.experience_years}</dd>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Key Strengths */}
      {summary.key_strengths && summary.key_strengths.length > 0 && (
        <div className="rounded-xl border border-green-200 bg-green-50 p-6">
          <h2 className="text-lg font-semibold text-green-900 mb-4 flex items-center gap-2">
            <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {t('result_key_strengths')}
          </h2>
          <div className="space-y-3">
            {summary.key_strengths.map((item, i) => (
              <div key={i} className="bg-white rounded-lg p-4 border border-green-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-green-900">{item.strength}</span>
                  <span className="text-sm text-green-600">{t('result_confidence', { value: Math.round(item.confidence * 100) })}</span>
                </div>
                {item.evidence && (
                  <div className="text-sm text-green-700 space-y-1">
                    {item.evidence.resume && <p>📄 {t('result_source_resume')}: {item.evidence.resume}</p>}
                    {item.evidence.linkedin && <p>💼 LinkedIn: {item.evidence.linkedin}</p>}
                    {item.evidence.github && <p>🔗 GitHub: {item.evidence.github}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Flags */}
      {summary.risk_flags && summary.risk_flags.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6">
          <h2 className="text-lg font-semibold text-red-900 mb-4 flex items-center gap-2">
            <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            {t('result_risk_factors')}
          </h2>
          <div className="space-y-3">
            {summary.risk_flags.map((item, i) => (
              <div key={i} className="bg-white rounded-lg p-4 border border-red-200">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-red-900">{item.concern}</span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    item.severity === 'high' ? 'bg-red-200 text-red-800' :
                    item.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                    'bg-gray-200 text-gray-800'
                  }`}>
                    {item.severity}
                  </span>
                </div>
                {item.evidence && <p className="text-sm text-red-700 mb-2">{item.evidence}</p>}
                {item.mitigation_question && (
                  <p className="text-sm text-red-800 bg-red-100 p-2 rounded">
                    💡 {t('result_verify_question')}: {item.mitigation_question}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Technical Expertise */}
      {summary.technical_expertise && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="h-5 w-5 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
            {t('result_technical_expertise')}
          </h2>
          <div className="space-y-4">
            {summary.technical_expertise.languages && summary.technical_expertise.languages.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">{t('result_languages')}</h3>
                <div className="flex flex-wrap gap-2">
                  {summary.technical_expertise.languages.map((lang, i) => (
                    <span key={i} className="px-3 py-1 rounded-full bg-brand-100 text-brand-700 text-sm">
                      {lang.skill} ({lang.proficiency})
                    </span>
                  ))}
                </div>
              </div>
            )}
            {summary.technical_expertise.frameworks && summary.technical_expertise.frameworks.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">{t('result_frameworks')}</h3>
                <div className="flex flex-wrap gap-2">
                  {summary.technical_expertise.frameworks.map((fw, i) => (
                    <span key={i} className="px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm">
                      {fw.skill} ({fw.proficiency})
                    </span>
                  ))}
                </div>
              </div>
            )}
            {summary.technical_expertise.tools && summary.technical_expertise.tools.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-2">{t('result_tools')}</h3>
                <div className="flex flex-wrap gap-2">
                  {summary.technical_expertise.tools.map((tool, i) => (
                    <span key={i} className="px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-sm">
                      {tool.tool} ({tool.proficiency})
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Data Quality Assessment */}
      {summary.data_quality_assessment && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('result_data_quality')}</h2>
          <div className="grid gap-4 sm:grid-cols-4">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-navy-700">
                {Math.round(summary.data_quality_assessment.overall_confidence * 100)}%
              </div>
              <div className="text-sm text-gray-500">{t('result_overall_confidence')}</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {Math.round(summary.data_quality_assessment.document_quality * 100)}%
              </div>
              <div className="text-sm text-gray-500">{t('result_document_quality')}</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {Math.round(summary.data_quality_assessment.linkedin_quality * 100)}%
              </div>
              <div className="text-sm text-gray-500">LinkedIn</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-brand-600">
                {Math.round(summary.data_quality_assessment.github_quality * 100)}%
              </div>
              <div className="text-sm text-gray-500">GitHub</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
