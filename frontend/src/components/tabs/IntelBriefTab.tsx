/**
 * IntelBriefTab - JD Analysis + GitHub Chart + LinkedIn Timeline + Competency Matching
 */
import { memo } from 'react'
import { useTranslation } from 'react-i18next'
import type { IntelBrief, Candidate } from '../../types/interview'
import { ContributionChart } from '../charts'

interface IntelBriefTabProps {
  intel: IntelBrief
  candidate?: Candidate
  techStack?: string[]
}

export const IntelBriefTab = memo(function IntelBriefTab({ intel, candidate, techStack }: IntelBriefTabProps) {
  const { t } = useTranslation()
  const { jd_summary, competencies, github, linkedin, linkedin_warning } = intel

  return (
    <div className="space-y-6">
      {/* Candidate Header */}
      {candidate && (
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center gap-4">
            {candidate.avatar_url ? (
              <img
                src={candidate.avatar_url}
                alt={candidate.name}
                className="h-16 w-16 rounded-full object-cover border-2 border-white/30"
                onError={(e) => {
                  const target = e.currentTarget
                  target.style.display = 'none'
                  target.nextElementSibling?.classList.remove('hidden')
                }}
              />
            ) : null}
            <div className={`flex h-16 w-16 items-center justify-center rounded-full bg-white/20 text-2xl font-bold ${candidate.avatar_url ? 'hidden' : ''}`}>
              {candidate.initials || candidate.name?.charAt(0) || '?'}
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-bold">{candidate.name}</h2>
              <p className="text-indigo-100">{candidate.role || candidate.current_title}</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
            {candidate.experience && (
              <div className="bg-white/10 rounded-lg px-4 py-2">
                <div className="text-sm text-indigo-100">{t('intel_experience')}</div>
                <div className="text-lg font-semibold">{candidate.experience}</div>
              </div>
            )}
            {candidate.jd_match && (
              <div className="bg-white/10 rounded-lg px-4 py-2">
                <div className="text-sm text-indigo-100">{t('intel_jd_match')}</div>
                <div className="text-lg font-semibold">{candidate.jd_match}</div>
              </div>
            )}
            {candidate.level && (
              <div className="bg-white/10 rounded-lg px-4 py-2">
                <div className="text-sm text-indigo-100">{t('intel_level')}</div>
                <div className="text-lg font-semibold">{candidate.level}</div>
              </div>
            )}
            {candidate.company_context && (
              <div className="bg-white/10 rounded-lg px-4 py-2">
                <div className="text-sm text-indigo-100">{t('intel_target_company')}</div>
                <div className="text-lg font-semibold">{candidate.company_context}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* JD Summary */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm animate-fadeIn">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {t('intel_jd_summary')}
        </h3>

        <div className="mb-4">
          <h4 className="text-xl font-bold text-gray-900">{jd_summary.title}</h4>
          <p className="text-sm text-gray-500">{jd_summary.subtitle}</p>
        </div>

        {/* Requirements */}
        <div className="mb-4">
          <h5 className="text-sm font-semibold text-gray-700 mb-2">{t('intel_requirements')}</h5>
          {jd_summary.requirements.length > 0 ? (
            <div className="space-y-2">
              {jd_summary.requirements.map((req, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-3 p-3 rounded-lg ${
                    req.matched ? 'bg-emerald-50 border border-emerald-200' : 'bg-gray-50 border border-gray-200'
                  }`}
                >
                  <span className={req.matched ? 'text-emerald-600' : 'text-gray-400'}>
                    {req.matched ? '✓' : '○'}
                  </span>
                  <div>
                    <span className={`font-medium ${req.matched ? 'text-emerald-900' : 'text-gray-700'}`}>
                      {req.text}
                    </span>
                    <p className="text-sm text-gray-500 mt-0.5">{req.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 text-center">
              <p className="text-sm text-gray-500">{t('intel_no_requirements')}</p>
              <p className="text-xs text-gray-400 mt-1">{t('intel_no_requirements_hint')}</p>
            </div>
          )}
        </div>

        {/* Success Metrics */}
        {jd_summary.success_metrics.length > 0 && (
          <div>
            <h5 className="text-sm font-semibold text-gray-700 mb-2">{t('intel_success_metrics')}</h5>
            <ul className="space-y-1">
              {jd_summary.success_metrics.map((metric, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                  <span className="text-indigo-500">•</span>
                  {metric}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Competency Matching */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {t('intel_competency_matching')}
        </h3>

        {competencies.length > 0 ? (
          <div className="space-y-4">
            {competencies.map((comp, i) => (
              <div
                key={i}
                className={`card-hover p-4 rounded-lg border ${
                  comp.color === 'emerald' ? 'bg-emerald-50 border-emerald-200' :
                  comp.color === 'amber' ? 'bg-amber-50 border-amber-200' :
                  comp.color === 'red' ? 'bg-red-50 border-red-200' :
                  comp.color === 'slate' ? 'bg-slate-50 border-slate-200' :
                  'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{comp.icon}</span>
                    <span className="font-semibold text-gray-900">{comp.name}</span>
                  </div>
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    comp.color === 'emerald' ? 'bg-emerald-200 text-emerald-800' :
                    comp.color === 'amber' ? 'bg-amber-200 text-amber-800' :
                    comp.color === 'red' ? 'bg-red-200 text-red-800' :
                    comp.color === 'slate' ? 'bg-slate-200 text-slate-800' :
                    'bg-gray-200 text-gray-800'
                  }`}>
                    {comp.match_label}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{comp.desc}</p>
                <p className={`text-sm font-medium ${
                  comp.color === 'emerald' ? 'text-emerald-700' :
                  comp.color === 'amber' ? 'text-amber-700' :
                  comp.color === 'red' ? 'text-red-700' :
                  comp.color === 'slate' ? 'text-slate-700' :
                  'text-gray-700'
                }`}>
                  💡 {comp.why}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 text-center">
            <p className="text-sm text-gray-500">{t('intel_no_competency')}</p>
            <p className="text-xs text-gray-400 mt-1">{t('intel_no_competency_hint')}</p>
          </div>
        )}
      </div>

      {/* GitHub Summary */}
      {github && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-gray-700" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
            {t('intel_github_activity')}
          </h3>

          {github.contributions === 0 && github.repos === 0 && github.main_languages === 'N/A' ? (
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 text-center">
              <p className="text-sm text-gray-500">{t('intel_no_github_data')}</p>
              <p className="text-xs text-gray-400 mt-1">{t('intel_no_github_hint')}</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-indigo-600">{github.contributions}</div>
                  <div className="text-sm text-gray-500">{t('intel_contributions')}</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-indigo-600">{github.repos}</div>
                  <div className="text-sm text-gray-500">{t('intel_repos')}</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-sm font-semibold text-gray-900">{github.main_languages}</div>
                  <div className="text-sm text-gray-500">{t('intel_main_languages')}</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-sm font-semibold text-gray-900">{github.tenure_pattern}</div>
                  <div className="text-sm text-gray-500">{t('intel_avg_tenure')}</div>
                </div>
              </div>

              {/* Tech Match */}
              <div className="mb-4 p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-indigo-900">{t('intel_tech_match')} {github.tech_match}</span>
                  {github.tech_match_note && (
                    <span className="text-sm text-amber-600">⚠️ {github.tech_match_note}</span>
                  )}
                </div>
              </div>

              {/* Tech Stack Tags */}
              {techStack && techStack.length > 0 && (
                <div className="mt-3">
                  <h5 className="text-xs font-medium text-gray-500 mb-2">{t('intel_tech_stack')}</h5>
                  <div className="flex flex-wrap gap-1.5">
                    {techStack.map((tech) => (
                      <span key={tech} className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium">
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Contribution Chart */}
              {github.chart_data && github.chart_data.some(v => v > 0) && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">{t('intel_monthly_contributions')}</h4>
                  <ContributionChart data={github.chart_data} />
                </div>
              )}

              {/* Activity Gap Warning */}
              {github.activity_gap && (
                <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <span className="text-amber-800">⚠️ {t('intel_activity_gap')} {github.activity_gap}</span>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* LinkedIn Timeline */}
      {linkedin && linkedin.length > 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
            </svg>
            {t('intel_linkedin_career')}
          </h3>

          <div className="space-y-4">
            {linkedin.map((pos, i) => (
              <div key={i} className="flex items-start gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 font-semibold">
                  {pos.initial}
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">{pos.title}</div>
                  <div className="text-sm text-gray-600">{pos.company}</div>
                  <div className="text-sm text-gray-500">{pos.detail}</div>
                </div>
                {i < linkedin.length - 1 && (
                  <div className="absolute left-5 top-12 h-full w-0.5 bg-gray-200" style={{ transform: 'translateX(-50%)' }} />
                )}
              </div>
            ))}
          </div>

          {linkedin_warning && (
            <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <span className="text-amber-800">⚠️ {linkedin_warning}</span>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
            </svg>
            {t('intel_linkedin_career')}
          </h3>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 text-center">
            <p className="text-sm text-gray-500">{t('intel_no_linkedin')}</p>
            <p className="text-xs text-gray-400 mt-1">{t('intel_no_linkedin_hint')}</p>
          </div>
        </div>
      )}
    </div>
  )
})
