import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../hooks/useAuth'
import { useCandidate, type JD } from '../hooks/useCandidate'
import { SectionCard } from '../components/SectionCard'

interface RankedCandidate {
  rank: number
  candidate: {
    id: string
    name: string
    email: string | null
    experience_level: string | null
    skills: string[]
    github_username: string | null
  }
  overall_match_score: number
  skill_match_score: number
}

export function FindCEOPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const { createJD, fetchJDs, getJDRanking } = useCandidate()

  const isCEO = user?.role === 'ceo' || user?.role === 'both'
  const isCandidate = user?.role === 'candidate' || user?.role === 'both'

  // Tab state
  const [activeTab, setActiveTab] = useState<'browse' | 'register'>(isCandidate ? 'browse' : 'register')

  // JD list
  const [jds, setJDs] = useState<JD[]>([])
  const [jdsLoading, setJDsLoading] = useState(true)

  // JD detail / ranking
  const [selectedJD, setSelectedJD] = useState<JD | null>(null)
  const [ranking, setRanking] = useState<RankedCandidate[]>([])
  const [rankingLoading, setRankingLoading] = useState(false)

  // Register form
  const [title, setTitle] = useState('')
  const [serviceDesc, setServiceDesc] = useState('')
  const [companySize, setCompanySize] = useState('1-10')
  const [workEnv, setWorkEnv] = useState('remote')
  const [positionType, setPositionType] = useState('fullstack')
  const [experienceLevel, setExperienceLevel] = useState('미들')
  const [requiredSkillInput, setRequiredSkillInput] = useState('')
  const [requiredSkills, setRequiredSkills] = useState<string[]>([])
  const [preferredSkillInput, setPreferredSkillInput] = useState('')
  const [preferredSkills, setPreferredSkills] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState(false)

  const loadJDs = useCallback(async () => {
    setJDsLoading(true)
    try {
      const data = await fetchJDs()
      setJDs(data)
    } catch {
      // silent
    } finally {
      setJDsLoading(false)
    }
  }, [fetchJDs])

  useEffect(() => {
    loadJDs()
  }, [loadJDs])

  const handleViewRanking = async (jd: JD) => {
    setSelectedJD(jd)
    setRankingLoading(true)
    try {
      const result = await getJDRanking(jd.id, 20)
      setRanking(result.ranking as RankedCandidate[])
    } catch {
      setRanking([])
    } finally {
      setRankingLoading(false)
    }
  }

  const addSkill = (
    input: string,
    setInput: (v: string) => void,
    skills: string[],
    setSkills: (v: string[]) => void
  ) => {
    const trimmed = input.trim()
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed])
      setInput('')
    }
  }

  const removeSkill = (skill: string, skills: string[], setSkills: (v: string[]) => void) => {
    setSkills(skills.filter(s => s !== skill))
  }

  const handleSubmitJD = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !serviceDesc.trim()) return

    setSubmitting(true)
    setFormError(null)
    setFormSuccess(false)

    try {
      // Build JD text from service description + metadata
      const jdText = [
        `[${t('ceo_position_type')}: ${t(`position_${positionType}`)}]`,
        `[${t('ceo_company_size')}: ${companySize}${t('ceo_people')}]`,
        `[${t('ceo_work_env')}: ${t(`env_${workEnv}`)}]`,
        `[${t('experience_level')}: ${experienceLevel}]`,
        '',
        serviceDesc,
      ].join('\n')

      await createJD({
        title: title.trim(),
        jd_text: jdText,
        required_skills: requiredSkills.length > 0 ? requiredSkills : undefined,
        preferred_skills: preferredSkills.length > 0 ? preferredSkills : undefined,
      })

      setFormSuccess(true)
      // Reset form
      setTitle('')
      setServiceDesc('')
      setRequiredSkills([])
      setPreferredSkills([])
      // Refresh JD list
      loadJDs()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('ceo_page_title')}</h1>
            <p className="mt-0.5 text-sm text-gray-500">{t('ceo_page_desc')}</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-1 rounded-lg bg-gray-100 p-1">
        <button
          onClick={() => setActiveTab('browse')}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'browse'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          {t('ceo_browse_jds')}
        </button>
        {isCEO && (
          <button
            onClick={() => setActiveTab('register')}
            className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === 'register'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {t('ceo_register_service')}
          </button>
        )}
      </div>

      {/* Browse JDs Tab */}
      {activeTab === 'browse' && (
        <div className="space-y-4">
          {selectedJD ? (
            // JD Detail + Ranking
            <div className="space-y-4">
              <button
                onClick={() => { setSelectedJD(null); setRanking([]) }}
                className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                {t('ceo_back_to_list')}
              </button>

              <SectionCard title={selectedJD.title}>
                <div className="space-y-3">
                  {selectedJD.jd_text && (
                    <p className="whitespace-pre-wrap text-sm text-gray-700">{selectedJD.jd_text}</p>
                  )}
                  <div className="flex flex-wrap gap-2">
                    {selectedJD.required_skills.map(skill => (
                      <span key={skill} className="rounded-md bg-navy-50 px-2 py-0.5 text-xs font-medium text-navy-800">
                        {skill}
                      </span>
                    ))}
                    {selectedJD.preferred_skills.map(skill => (
                      <span key={skill} className="rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </SectionCard>

              {/* Matching Candidates */}
              <SectionCard title={t('ceo_matching_candidates')}>
                {rankingLoading ? (
                  <div className="space-y-2">
                    {[1, 2, 3].map(i => (
                      <div key={i} className="animate-pulse rounded-lg border border-gray-200 p-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-gray-200" />
                          <div className="flex-1">
                            <div className="h-4 w-24 rounded bg-gray-200" />
                            <div className="mt-1 h-3 w-32 rounded bg-gray-100" />
                          </div>
                          <div className="h-6 w-16 rounded bg-gray-200" />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : ranking.length === 0 ? (
                  <p className="py-8 text-center text-sm text-gray-400">{t('ceo_no_matching')}</p>
                ) : (
                  <div className="space-y-2">
                    {ranking.map(item => (
                      <div
                        key={item.candidate.id}
                        className="flex items-center gap-4 rounded-lg border border-gray-200 p-4 transition-colors hover:bg-gray-50"
                      >
                        {/* Rank */}
                        <div className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                          item.rank <= 3
                            ? 'bg-gradient-to-br from-brand-400 to-orange-500 text-white'
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {item.rank}
                        </div>

                        {/* Info */}
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="truncate text-sm font-medium text-gray-900">
                              {item.candidate.name}
                            </span>
                            {item.candidate.experience_level && (
                              <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500">
                                {item.candidate.experience_level}
                              </span>
                            )}
                          </div>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {item.candidate.skills.slice(0, 5).map(skill => (
                              <span key={skill} className="rounded bg-navy-50 px-1.5 py-0.5 text-[10px] text-navy-700">
                                {skill}
                              </span>
                            ))}
                            {item.candidate.skills.length > 5 && (
                              <span className="text-[10px] text-gray-400">
                                +{item.candidate.skills.length - 5}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Scores */}
                        <div className="flex flex-shrink-0 items-center gap-3">
                          <div className="text-right">
                            <div className={`text-lg font-bold ${
                              item.overall_match_score >= 70 ? 'text-emerald-600'
                              : item.overall_match_score >= 50 ? 'text-brand-600'
                              : 'text-gray-500'
                            }`}>
                              {Math.round(item.overall_match_score)}%
                            </div>
                            <div className="text-[10px] text-gray-400">{t('ceo_match_rate')}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>
            </div>
          ) : (
            // JD List
            <>
              {jdsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="animate-pulse rounded-lg border border-gray-200 p-4">
                      <div className="h-5 w-40 rounded bg-gray-200" />
                      <div className="mt-2 h-4 w-full rounded bg-gray-100" />
                      <div className="mt-1 h-4 w-3/4 rounded bg-gray-100" />
                    </div>
                  ))}
                </div>
              ) : jds.length === 0 ? (
                <div className="rounded-xl border-2 border-dashed border-gray-300 py-16 text-center">
                  <svg className="mx-auto h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <h3 className="mt-4 text-sm font-medium text-gray-900">{t('ceo_no_jds_title')}</h3>
                  <p className="mt-1 text-sm text-gray-500">{t('ceo_no_jds_desc')}</p>
                  {isCEO && (
                    <button
                      onClick={() => setActiveTab('register')}
                      className="mt-4 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
                    >
                      {t('ceo_register_service')}
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  {jds.map(jd => (
                    <div
                      key={jd.id}
                      className="cursor-pointer rounded-lg border border-gray-200 p-4 transition-colors hover:border-emerald-300 hover:bg-emerald-50/50"
                      onClick={() => handleViewRanking(jd)}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0 flex-1">
                          <h3 className="truncate text-sm font-medium text-gray-900">{jd.title}</h3>
                          {jd.jd_text && (
                            <p className="mt-1 line-clamp-2 text-xs text-gray-500">{jd.jd_text}</p>
                          )}
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {jd.required_skills.slice(0, 6).map(skill => (
                              <span key={skill} className="rounded bg-navy-50 px-1.5 py-0.5 text-[10px] font-medium text-navy-700">
                                {skill}
                              </span>
                            ))}
                            {jd.required_skills.length > 6 && (
                              <span className="text-[10px] text-gray-400">+{jd.required_skills.length - 6}</span>
                            )}
                          </div>
                        </div>
                        <div className="flex flex-shrink-0 items-center gap-1 text-sm text-emerald-600">
                          <span>{t('ceo_view_matches')}</span>
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Register Service Tab */}
      {activeTab === 'register' && isCEO && (
        <form onSubmit={handleSubmitJD} className="space-y-6">
          <SectionCard title={t('ceo_service_info')} required>
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  {t('ceo_position_title')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder={t('ceo_position_title_placeholder')}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                  required
                />
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  {t('ceo_service_desc')} <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={serviceDesc}
                  onChange={(e) => setServiceDesc(e.target.value)}
                  placeholder={t('ceo_service_desc_placeholder')}
                  rows={5}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                  required
                  minLength={30}
                />
                <p className="mt-1 text-xs text-gray-400">{t('min_chars')}: 30</p>
              </div>
            </div>
          </SectionCard>

          <SectionCard title={t('ceo_company_details')}>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">{t('ceo_company_size')}</label>
                <select
                  value={companySize}
                  onChange={(e) => setCompanySize(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                >
                  <option value="1-10">1-10{t('ceo_people')}</option>
                  <option value="11-50">11-50{t('ceo_people')}</option>
                  <option value="51-200">51-200{t('ceo_people')}</option>
                  <option value="200+">200+{t('ceo_people')}</option>
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">{t('ceo_work_env')}</label>
                <select
                  value={workEnv}
                  onChange={(e) => setWorkEnv(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                >
                  <option value="remote">{t('env_remote')}</option>
                  <option value="hybrid">{t('env_hybrid')}</option>
                  <option value="office">{t('env_office')}</option>
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">{t('ceo_position_type')}</label>
                <select
                  value={positionType}
                  onChange={(e) => setPositionType(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                >
                  <option value="cto">{t('position_cto')}</option>
                  <option value="backend">{t('position_backend')}</option>
                  <option value="frontend">{t('position_frontend')}</option>
                  <option value="fullstack">{t('position_fullstack')}</option>
                  <option value="devops">{t('position_devops')}</option>
                  <option value="mobile">{t('position_mobile')}</option>
                  <option value="data">{t('position_data')}</option>
                </select>
              </div>
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">{t('experience_level')}</label>
                <select
                  value={experienceLevel}
                  onChange={(e) => setExperienceLevel(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                >
                  <option value="신입">{t('level_entry')}</option>
                  <option value="주니어">{t('level_junior')}</option>
                  <option value="미들">{t('level_mid')}</option>
                  <option value="시니어">{t('level_senior')}</option>
                  <option value="CTO/VP">{t('level_executive')}</option>
                </select>
              </div>
            </div>
          </SectionCard>

          <SectionCard title={t('ceo_required_skills')}>
            <div className="space-y-4">
              {/* Required Skills */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">{t('ceo_required_skills_label')}</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={requiredSkillInput}
                    onChange={(e) => setRequiredSkillInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addSkill(requiredSkillInput, setRequiredSkillInput, requiredSkills, setRequiredSkills) } }}
                    placeholder={t('candidate_skill_placeholder')}
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                  />
                  <button
                    type="button"
                    onClick={() => addSkill(requiredSkillInput, setRequiredSkillInput, requiredSkills, setRequiredSkills)}
                    className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    {t('candidate_add_skill')}
                  </button>
                </div>
                {requiredSkills.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {requiredSkills.map(skill => (
                      <span key={skill} className="inline-flex items-center gap-1 rounded-md bg-navy-50 px-2 py-0.5 text-sm font-medium text-navy-800">
                        {skill}
                        <button type="button" onClick={() => removeSkill(skill, requiredSkills, setRequiredSkills)} className="text-navy-600 hover:text-navy-700">
                          <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Preferred Skills */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">{t('ceo_preferred_skills_label')}</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={preferredSkillInput}
                    onChange={(e) => setPreferredSkillInput(e.target.value)}
                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addSkill(preferredSkillInput, setPreferredSkillInput, preferredSkills, setPreferredSkills) } }}
                    placeholder={t('candidate_skill_placeholder')}
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm transition-colors focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                  />
                  <button
                    type="button"
                    onClick={() => addSkill(preferredSkillInput, setPreferredSkillInput, preferredSkills, setPreferredSkills)}
                    className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    {t('candidate_add_skill')}
                  </button>
                </div>
                {preferredSkills.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {preferredSkills.map(skill => (
                      <span key={skill} className="inline-flex items-center gap-1 rounded-md bg-gray-100 px-2 py-0.5 text-sm font-medium text-gray-600">
                        {skill}
                        <button type="button" onClick={() => removeSkill(skill, preferredSkills, setPreferredSkills)} className="text-gray-400 hover:text-gray-600">
                          <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </SectionCard>

          {/* Error */}
          {formError && (
            <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
              <svg className="h-5 w-5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span className="text-sm font-medium text-red-700">{formError}</span>
            </div>
          )}

          {/* Success */}
          {formSuccess && (
            <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
              <svg className="h-5 w-5 flex-shrink-0 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span className="text-sm font-medium text-emerald-700">{t('ceo_jd_created')}</span>
            </div>
          )}

          {/* Submit */}
          <div className="flex items-center justify-end gap-3 border-t border-gray-200 pt-6">
            <button
              type="button"
              onClick={() => setActiveTab('browse')}
              className="rounded-lg border border-gray-300 bg-white px-5 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              {t('cancel')}
            </button>
            <button
              type="submit"
              disabled={!title.trim() || !serviceDesc.trim() || submitting}
              className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:from-emerald-700 hover:to-teal-700 hover:shadow-md disabled:cursor-not-allowed disabled:from-gray-400 disabled:to-gray-400 disabled:shadow-none"
            >
              {submitting ? (
                <>
                  <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  {t('loading')}
                </>
              ) : (
                t('ceo_create_jd')
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
