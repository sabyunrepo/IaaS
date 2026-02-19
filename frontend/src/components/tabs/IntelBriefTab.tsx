/**
 * IntelBriefTab - JD Analysis + GitHub Chart + LinkedIn Timeline + Competency Matching
 */
import { memo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { IntelBrief, Candidate, LinkedInProfile } from '../../types/interview'
import { ContributionChart } from '../charts'
import { Badge } from '../../../seed-design/ui'

interface IntelBriefTabProps {
  intel: IntelBrief
  candidate?: Candidate
  techStack?: string[]
  linkedinProfile?: LinkedInProfile
}

export const IntelBriefTab = memo(function IntelBriefTab({ intel, candidate, techStack, linkedinProfile }: IntelBriefTabProps) {
  const { t } = useTranslation()
  const { jd_summary, jd_full, github, linkedin, linkedin_warning } = intel
  const [avatarError, setAvatarError] = useState(false)
  const [jdFullExpanded, setJdFullExpanded] = useState(false)

  return (
    <div className="space-y-6">
      {/* Candidate Header */}
      {candidate && (
        <div className="bg-gradient-to-r from-em-600 to-teal-500 rounded-xl p-6 text-white shadow-lg">
          <div className="flex items-center gap-4">
            {candidate.avatar_url && !avatarError ? (
              <img
                src={candidate.avatar_url}
                alt={candidate.name}
                className="h-16 w-16 rounded-full object-cover border-2 border-white/30"
                onError={() => setAvatarError(true)}
              />
            ) : (
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/20 text-2xl font-bold">
                {candidate.initials || candidate.name?.charAt(0) || '?'}
              </div>
            )}
            <div>
              <h2 className="text-xl sm:text-2xl font-bold">{candidate.name}</h2>
              <p className="text-em-100">{candidate.role || candidate.current_title}</p>
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
            {candidate.experience && (
              <div className="bg-white/10 rounded-lg px-4 py-2">
                <div className="text-sm text-em-100">{t('intel_experience')}</div>
                <div className="text-lg font-semibold">{candidate.experience}</div>
              </div>
            )}
            {candidate.jd_match && (
              <div className="bg-white/10 rounded-lg px-4 py-2">
                <div className="text-sm text-em-100">{t('intel_jd_match')}</div>
                <div className="text-lg font-semibold">{candidate.jd_match}</div>
              </div>
            )}
            {candidate.level && (
              <div className="bg-white/10 rounded-lg px-4 py-2">
                <div className="text-sm text-em-100">{t('intel_level')}</div>
                <div className="text-lg font-semibold">{candidate.level}</div>
              </div>
            )}
            {candidate.company_context && (
              <div className="bg-white/10 rounded-lg px-4 py-2">
                <div className="text-sm text-em-100">{t('intel_target_company')}</div>
                <div className="text-lg font-semibold">{candidate.company_context}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* JD Summary */}
      <div className="bg-[--color-bg-surface] rounded-xl border border-[--color-border-default] p-6 shadow-sm animate-fadeIn">
        <h3 className="text-lg font-semibold text-[--color-text-primary] mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-em-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {t('intel_jd_summary')}
        </h3>

        <div className="mb-4">
          <h4 className="text-xl font-bold text-[--color-text-primary]">{jd_summary.title}</h4>
          <p className="text-sm text-[--color-text-tertiary]">{jd_summary.subtitle}</p>
        </div>

        {/* Requirements */}
        <div className="mb-4">
          <h5 className="text-sm font-semibold text-[--color-text-secondary] mb-2">{t('intel_requirements')}</h5>
          {jd_summary.requirements.length > 0 ? (
            <div className="space-y-2">
              {jd_summary.requirements.map((req, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-3 p-3 rounded-lg ${
                    req.matched ? 'bg-emerald-50 border border-emerald-200' : 'bg-[--color-bg-page] border border-[--color-border-default]'
                  }`}
                >
                  <span className={req.matched ? 'text-emerald-600' : 'text-[--color-text-tertiary]'}>
                    {req.matched ? '✓' : '○'}
                  </span>
                  <div>
                    <span className={`font-medium ${req.matched ? 'text-emerald-900' : 'text-[--color-text-secondary]'}`}>
                      {req.text}
                    </span>
                    <p className="text-sm text-[--color-text-tertiary] mt-0.5">{req.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 bg-[--color-bg-page] rounded-lg border border-[--color-border-default] text-center">
              <p className="text-sm text-[--color-text-tertiary]">{t('intel_no_requirements')}</p>
              <p className="text-xs text-[--color-text-tertiary] mt-1">{t('intel_no_requirements_hint')}</p>
            </div>
          )}
        </div>

        {/* Success Metrics */}
        {jd_summary.success_metrics.length > 0 && (
          <div>
            <h5 className="text-sm font-semibold text-[--color-text-secondary] mb-2">{t('intel_success_metrics')}</h5>
            <ul className="space-y-1">
              {jd_summary.success_metrics.map((metric, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-[--color-text-secondary]">
                  <span className="text-em-700">•</span>
                  {metric}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Full JD Text (collapsible) */}
      {jd_full && (
        <div className="bg-[--color-bg-surface] rounded-xl border border-[--color-border-default] shadow-sm">
          <button
            onClick={() => setJdFullExpanded(!jdFullExpanded)}
            className="w-full px-6 py-4 flex items-center justify-between text-left"
          >
            <h3 className="text-sm font-semibold text-[--color-text-secondary] flex items-center gap-2">
              <svg className="w-4 h-4 text-[--color-text-tertiary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              {t('intel_jd_full_text')}
            </h3>
            <svg className={`w-4 h-4 text-[--color-text-tertiary] transition-transform ${jdFullExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          {jdFullExpanded && (
            <div className="px-6 pb-4">
              <pre className="text-sm text-[--color-text-secondary] whitespace-pre-wrap font-sans leading-relaxed bg-[--color-bg-page] rounded-lg p-4 border border-[--color-border-subtle]">
                {jd_full}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* GitHub Summary */}
      {github && (
        <div className="bg-[--color-bg-surface] rounded-xl border border-[--color-border-default] p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-[--color-text-primary] mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-[--color-text-secondary]" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
            {t('intel_github_activity')}
          </h3>

          {github.contributions === 0 && github.repos === 0 && github.main_languages === 'N/A' ? (
            <div className="p-4 bg-[--color-bg-page] rounded-lg border border-[--color-border-default] text-center">
              <p className="text-sm text-[--color-text-tertiary]">{t('intel_no_github_data')}</p>
              <p className="text-xs text-[--color-text-tertiary] mt-1">{t('intel_no_github_hint')}</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-3 bg-[--color-bg-page] rounded-lg">
                  <div className="text-2xl font-bold text-em-700">{github.contributions}</div>
                  <div className="text-sm text-[--color-text-tertiary]">{t('intel_contributions')}</div>
                </div>
                <div className="text-center p-3 bg-[--color-bg-page] rounded-lg">
                  <div className="text-2xl font-bold text-em-700">{github.repos}</div>
                  <div className="text-sm text-[--color-text-tertiary]">{t('intel_repos')}</div>
                </div>
                <div className="text-center p-3 bg-[--color-bg-page] rounded-lg">
                  <div className="text-sm font-semibold text-[--color-text-primary]">{github.main_languages}</div>
                  <div className="text-sm text-[--color-text-tertiary]">{t('intel_main_languages')}</div>
                </div>
                <div className="text-center p-3 bg-[--color-bg-page] rounded-lg">
                  <div className="text-sm font-semibold text-[--color-text-primary]">{github.tenure_pattern}</div>
                  <div className="text-sm text-[--color-text-tertiary]">{t('intel_avg_tenure')}</div>
                </div>
              </div>

              {/* Tech Match */}
              <div className="mb-4 p-3 bg-em-50 border border-em-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-em-900">{t('intel_tech_match')} {github.tech_match}</span>
                  {github.tech_match_note && (
                    <span className="text-sm text-[--color-text-accent]">⚠️ {github.tech_match_note}</span>
                  )}
                </div>
              </div>

              {/* Tech Stack Tags */}
              {techStack && techStack.length > 0 && (
                <div className="mt-3">
                  <h5 className="text-xs font-medium text-[--color-text-tertiary] mb-2">{t('intel_tech_stack')}</h5>
                  <div className="flex flex-wrap gap-1.5">
                    {techStack.map((tech) => (
                      <Badge key={tech} tone="brand" variant="weak">
                        {tech}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Contribution Chart */}
              {github.chart_data && github.chart_data.some(v => v > 0) && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-[--color-text-secondary] mb-2">{t('intel_monthly_contributions')}</h4>
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
        <div className="bg-[--color-bg-surface] rounded-xl border border-[--color-border-default] p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-[--color-text-primary] mb-4 flex items-center gap-2">
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
                  <div className="font-semibold text-[--color-text-primary]">{pos.title}</div>
                  <div className="text-sm text-[--color-text-secondary]">{pos.company}</div>
                  <div className="text-sm text-[--color-text-tertiary]">{pos.detail}</div>
                </div>
                {i < linkedin.length - 1 && (
                  <div className="absolute left-5 top-12 h-full w-0.5 bg-[--color-border-default]" style={{ transform: 'translateX(-50%)' }} />
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
        <div className="bg-[--color-bg-surface] rounded-xl border border-[--color-border-default] p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-[--color-text-primary] mb-4 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
            </svg>
            {t('intel_linkedin_career')}
          </h3>
          <div className="p-4 bg-[--color-bg-page] rounded-lg border border-[--color-border-default] text-center">
            <p className="text-sm text-[--color-text-tertiary]">{t('intel_no_linkedin')}</p>
            <p className="text-xs text-[--color-text-tertiary] mt-1">{t('intel_no_linkedin_hint')}</p>
          </div>
        </div>
      )}

      {/* LinkedIn Profile Details (Education, Skills, Certs, Projects, Honors, Languages) */}
      {linkedinProfile && (
        <div className="bg-[--color-bg-surface] rounded-xl border border-[--color-border-default] p-6 shadow-sm space-y-6">
          {/* Education */}
          {linkedinProfile.education && linkedinProfile.education.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[--color-text-secondary] mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                </svg>
                {t('intel_education')}
              </h4>
              <div className="space-y-3">
                {linkedinProfile.education.map((edu, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-sm font-semibold">
                      {edu.school?.charAt(0) || '?'}
                    </div>
                    <div>
                      <div className="font-medium text-[--color-text-primary]">{edu.school}</div>
                      {edu.degree && (
                        <div className="text-sm text-[--color-text-secondary]">
                          <span className="text-xs text-blue-600 font-medium">{t('intel_education_degree')}:</span> {edu.degree}
                        </div>
                      )}
                      {edu.field && (
                        <div className="text-sm text-[--color-text-secondary]">
                          <span className="text-xs text-blue-600 font-medium">{t('intel_education_field')}:</span> {edu.field}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skills */}
          {linkedinProfile.skills && linkedinProfile.skills.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[--color-text-secondary] mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-em-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                {t('intel_skills')}
              </h4>
              <div className="flex flex-wrap gap-2">
                {linkedinProfile.skills.map((skill, i) => {
                  const jdReqs = jd_summary?.requirements?.map(r => r.text?.toLowerCase()) || [];
                  const isJdMatch = jdReqs.some(r =>
                    r && (r.includes(skill.toLowerCase()) || skill.toLowerCase().includes(r))
                  );
                  return (
                    <Badge key={i} tone={isJdMatch ? "positive" : "neutral"} variant="weak">
                      {skill}
                    </Badge>
                  );
                })}
              </div>
            </div>
          )}

          {/* Certifications */}
          {linkedinProfile.certifications && linkedinProfile.certifications.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[--color-text-secondary] mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
                {t('intel_certifications')}
              </h4>
              <div className="space-y-2">
                {linkedinProfile.certifications.map((cert, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 bg-emerald-50 rounded-lg border border-emerald-200">
                    <span className="text-emerald-600">✓</span>
                    <div>
                      <span className="font-medium text-[--color-text-primary] text-sm">{cert.name}</span>
                      {cert.authority && (
                        <span className="text-xs text-[--color-text-tertiary] ml-2">— {cert.authority}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Projects */}
          {linkedinProfile.projects && linkedinProfile.projects.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[--color-text-secondary] mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-em-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                {t('intel_projects')}
              </h4>
              <div className="space-y-2">
                {linkedinProfile.projects.map((proj, i) => (
                  <div key={i} className="p-3 bg-em-50 rounded-lg border border-em-200">
                    <div className="font-medium text-[--color-text-primary] text-sm">{proj.title}</div>
                    {proj.description && (
                      <p className="text-xs text-[--color-text-secondary] mt-1">{proj.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Honors & Awards */}
          {linkedinProfile.honors_and_awards && linkedinProfile.honors_and_awards.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[--color-text-secondary] mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-em-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                </svg>
                {t('intel_honors')}
              </h4>
              <div className="space-y-2">
                {linkedinProfile.honors_and_awards.map((honor, i) => (
                  <div key={i} className="p-3 bg-em-50 rounded-lg border border-em-200">
                    <div className="font-medium text-[--color-text-primary] text-sm">{honor.title}</div>
                    {honor.issuer && (
                      <div className="text-xs text-em-700">{honor.issuer}</div>
                    )}
                    {honor.description && (
                      <p className="text-xs text-[--color-text-secondary] mt-1">{honor.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations Summary (JIT-52) */}
          {linkedinProfile?.recommendations_summary && (
            <div className="bg-em-50 rounded-lg p-4 border border-em-200">
              <h4 className="text-sm font-semibold text-em-800 flex items-center gap-2 mb-2">
                <svg className="w-4 h-4 text-em-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                {t('intel_recommendations')}
                {linkedinProfile.recommendations && (
                  <Badge tone="brand" variant="weak">
                    {linkedinProfile.recommendations.length}
                  </Badge>
                )}
              </h4>
              <p className="text-sm text-[--color-text-secondary]">{linkedinProfile.recommendations_summary}</p>
            </div>
          )}

          {/* Volunteer Summary (JIT-52) */}
          {linkedinProfile?.volunteer_summary && (
            <div className="bg-teal-50 rounded-lg p-4 border border-teal-200">
              <h4 className="text-sm font-semibold text-teal-800 flex items-center gap-2 mb-2">
                <svg className="w-4 h-4 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                {t('intel_volunteer')}
                {linkedinProfile.volunteer_experience && (
                  <Badge tone="brand" variant="weak">
                    {linkedinProfile.volunteer_experience.length}
                  </Badge>
                )}
              </h4>
              <p className="text-sm text-[--color-text-secondary]">{linkedinProfile.volunteer_summary}</p>
            </div>
          )}

          {/* Languages */}
          {linkedinProfile.languages && linkedinProfile.languages.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[--color-text-secondary] mb-3 flex items-center gap-2">
                <svg className="w-4 h-4 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                </svg>
                {t('intel_languages')}
              </h4>
              <div className="flex flex-wrap gap-2">
                {linkedinProfile.languages.map((lang, i) => (
                  <Badge key={i} tone="brand" variant="weak">
                    {lang}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Profile Link */}
          {linkedinProfile.profile_url && (
            <div className="pt-2 border-t border-[--color-border-default]">
              <a
                href={linkedinProfile.profile_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
                {t('intel_linkedin_profile')}
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  )
})
