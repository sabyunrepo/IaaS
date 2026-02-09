import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useCandidate, type MatchResult, type Candidate } from '../hooks/useCandidate'
import { SectionCard } from '../components/SectionCard'

interface RankedCandidate {
  rank: number
  candidate: Candidate
  overall_match_score: number
  skill_match_score: number
}

interface MatchDetail {
  candidate: Candidate
  match: MatchResult
}

function RecommendationBadge({ score }: { score: number }) {
  const { t } = useTranslation()
  if (score >= 80) return <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-bold text-green-800">{t('rec_strong_hire')}</span>
  if (score >= 65) return <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-bold text-blue-800">{t('rec_hire')}</span>
  if (score >= 45) return <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-bold text-amber-800">{t('rec_leaning_no')}</span>
  return <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-bold text-red-800">{t('rec_no_hire')}</span>
}

function SkillMatchBar({ matched, total }: { matched: number; total: number }) {
  const pct = total > 0 ? Math.round((matched / total) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-indigo-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500">{matched}/{total}</span>
    </div>
  )
}

function MatchCard({ detail, onToggle, expanded }: {
  detail: MatchDetail
  onToggle: () => void
  expanded: boolean
}) {
  const { t } = useTranslation()
  const { candidate, match } = detail

  return (
    <div className="rounded-xl border border-gray-200 bg-white transition-all hover:border-gray-300 hover:shadow-md">
      <div className="flex items-start gap-4 p-5">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3">
            <span className="text-base font-medium text-gray-900">{candidate.name}</span>
            {candidate.experience_level && (
              <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                {candidate.experience_level}
              </span>
            )}
            <RecommendationBadge score={match.overall_match_score} />
          </div>
          {/* Score row */}
          <div className="mt-2 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">{t('deep_overall_match')}:</span>
              <span className="text-lg font-bold text-indigo-600">{Math.round(match.overall_match_score)}%</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">{t('search_skill_match')}:</span>
              <SkillMatchBar
                matched={match.skill_matches?.matched_count ?? 0}
                total={match.skill_matches?.total_jd_skills ?? 0}
              />
            </div>
          </div>
          {/* Skills */}
          {candidate.skills.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {candidate.skills.slice(0, 6).map((skill) => (
                <span key={skill} className="rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
                  {skill}
                </span>
              ))}
              {candidate.skills.length > 6 && (
                <span className="text-xs text-gray-400">+{candidate.skills.length - 6}</span>
              )}
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm font-medium text-gray-600 transition-colors hover:border-indigo-300 hover:bg-indigo-50 hover:text-indigo-700"
        >
          {expanded ? t('search_collapse') : t('search_detail')}
        </button>
      </div>

      {/* Expanded Detail */}
      {expanded && (
        <div className="border-t border-gray-100 bg-gray-50/50 p-5 space-y-4">
          {/* Skill matches */}
          {match.skill_matches?.matched && match.skill_matches.matched.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-semibold text-gray-700">{t('deep_skill_matching')}</h4>
              <div className="grid gap-2 sm:grid-cols-2">
                {match.skill_matches.matched.map((sm, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-white px-3 py-2 text-sm">
                    <span className="text-gray-700">{sm.skill}</span>
                    <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                      sm.matched ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'
                    }`}>
                      {sm.matched ? t('deep_match_exact') : t('deep_match_none')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gaps */}
          {match.gaps && match.gaps.length > 0 && (
            <div>
              <h4 className="mb-2 text-sm font-semibold text-gray-700">{t('search_gaps')}</h4>
              <div className="flex flex-wrap gap-2">
                {match.gaps.map((gap, i) => (
                  <span key={i} className="rounded-md bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700">
                    {gap.skill} ({gap.importance})
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Explanation */}
          {match.match_explanation && (
            <div>
              <h4 className="mb-2 text-sm font-semibold text-gray-700">{t('search_explanation')}</h4>
              <p className="text-sm text-gray-600 whitespace-pre-line">{match.match_explanation}</p>
            </div>
          )}

          {/* Recommendation */}
          {match.hiring_recommendation && (
            <div>
              <h4 className="mb-2 text-sm font-semibold text-gray-700">{t('decision_recommendation')}</h4>
              <p className="text-sm text-gray-600">{match.hiring_recommendation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function CandidateSearchPage() {
  const { t } = useTranslation()
  const { createJD, fetchCandidates, matchCandidateToJD, getJDRanking } = useCandidate()

  // Step 1: JD Input
  const [jdText, setJdText] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('미들')
  const [outputLanguage, setOutputLanguage] = useState('ko')

  // Step 2: Results
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [rankings, setRankings] = useState<RankedCandidate[]>([])
  const [matchDetails, setMatchDetails] = useState<Map<string, MatchResult>>(new Map())
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (jdText.length < 50) return

    setSearching(true)
    setSearchError(null)
    setRankings([])
    setMatchDetails(new Map())
    setExpandedId(null)

    try {
      // 1. Create JD
      const jd = await createJD({
        title: jdText.slice(0, 100),
        jd_text: jdText,
      })

      // 2. Fetch all candidates
      const candidates = await fetchCandidates({ limit: 200 })
      if (!candidates || candidates.length === 0) {
        setRankings([])
        setHasSearched(true)
        return
      }

      // 3. Match each candidate to JD
      const results: { candidate: Candidate; match: MatchResult }[] = []
      for (const candidate of candidates) {
        try {
          const match = await matchCandidateToJD(candidate.id, jd.id, {
            experience_level: experienceLevel,
            output_language: outputLanguage,
          })
          results.push({ candidate, match })
        } catch {
          // Skip candidates that fail matching
        }
      }

      // 4. Sort by score and build rankings
      results.sort((a, b) => b.match.overall_match_score - a.match.overall_match_score)

      const rankedList: RankedCandidate[] = results.map((r, i) => ({
        rank: i + 1,
        candidate: r.candidate,
        overall_match_score: r.match.overall_match_score,
        skill_match_score: r.match.skill_match_score,
      }))

      const detailMap = new Map<string, MatchResult>()
      results.forEach(r => detailMap.set(r.candidate.id, r.match))

      setRankings(rankedList)
      setMatchDetails(detailMap)
      setHasSearched(true)

      // Try to also get server-side ranking if available
      try {
        const serverRanking = await getJDRanking(jd.id, 20)
        if (serverRanking.ranking.length > 0) {
          setRankings(serverRanking.ranking)
        }
      } catch {
        // Use client-side ranking as fallback
      }
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : String(err))
    } finally {
      setSearching(false)
    }
  }

  const SUPPORTED_LANGUAGES = [
    { code: 'ko', name: '한국어' },
    { code: 'en', name: 'English' },
    { code: 'ja', name: '日本語' },
    { code: 'zh-CN', name: '简体中文' },
  ]

  return (
    <div className="mx-auto max-w-4xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('search_candidates_title')}</h1>
            <p className="mt-0.5 text-sm text-gray-500">{t('search_candidates_desc')}</p>
          </div>
        </div>
      </div>

      {/* Step 1: JD Input */}
      <form onSubmit={handleSearch} className="space-y-6">
        <SectionCard
          title={t('jd_section_title')}
          description={t('search_jd_input_desc')}
          required
        >
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder={t('jd_placeholder')}
            rows={6}
            className="w-full rounded-lg border border-gray-300 p-4 text-gray-900 placeholder-gray-400 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            required
            minLength={50}
          />
          <div className="mt-2 text-sm">
            <span className={jdText.length >= 50 ? 'text-green-600' : 'text-gray-500'}>
              {jdText.length >= 50 ? (
                <span className="flex items-center gap-1">
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {t('jd_length_ok')}
                </span>
              ) : (
                `${jdText.length}/50 ${t('min_chars')}`
              )}
            </span>
          </div>
        </SectionCard>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              {t('experience_level')}
            </label>
            <select
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="신입">{t('level_entry')}</option>
              <option value="주니어">{t('level_junior')}</option>
              <option value="미들">{t('level_mid')}</option>
              <option value="시니어">{t('level_senior')}</option>
              <option value="CTO/VP">{t('level_executive')}</option>
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">
              {t('output_language')}
            </label>
            <select
              value={outputLanguage}
              onChange={(e) => setOutputLanguage(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>{lang.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Search Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={jdText.length < 50 || searching}
            className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:from-indigo-700 hover:to-purple-700 hover:shadow-md disabled:cursor-not-allowed disabled:from-gray-400 disabled:to-gray-400 disabled:shadow-none"
          >
            {searching ? (
              <>
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                {t('search_matching')}
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                {t('search_candidates_btn')}
              </>
            )}
          </button>
        </div>
      </form>

      {/* Error */}
      {searchError && (
        <div className="mt-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
          <svg className="h-5 w-5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span className="text-sm font-medium text-red-700">{searchError}</span>
        </div>
      )}

      {/* Step 2: Results */}
      {hasSearched && !searching && (
        <div className="mt-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">{t('search_results_title')}</h2>
            <span className="text-sm text-gray-500">
              {t('candidate_count', { count: rankings.length })}
            </span>
          </div>

          {rankings.length === 0 ? (
            <div className="rounded-xl border-2 border-dashed border-gray-200 bg-gray-50/50 px-6 py-12 text-center">
              <p className="text-sm text-gray-500">{t('search_no_results')}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {rankings.map((rc) => {
                const match = matchDetails.get(rc.candidate.id)
                if (!match) return null
                return (
                  <MatchCard
                    key={rc.candidate.id}
                    detail={{ candidate: rc.candidate, match }}
                    expanded={expandedId === rc.candidate.id}
                    onToggle={() => setExpandedId(prev => prev === rc.candidate.id ? null : rc.candidate.id)}
                  />
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
