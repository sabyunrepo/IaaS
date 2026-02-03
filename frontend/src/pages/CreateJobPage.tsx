import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useJob } from '../hooks/useJob'

export function CreateJobPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { createJob } = useJob()

  // Required fields
  const [jdText, setJdText] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('미들')

  // Optional fields
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [githubUrls, setGithubUrls] = useState<string[]>([''])
  const [githubUsername, setGithubUsername] = useState('')
  const [maxQuestions, setMaxQuestions] = useState(25)
  const [focusAreas, setFocusAreas] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // GitHub URL handlers
  const addGithubUrl = () => {
    if (githubUrls.length < 5) {
      setGithubUrls([...githubUrls, ''])
    }
  }

  const removeGithubUrl = (index: number) => {
    setGithubUrls(githubUrls.filter((_, i) => i !== index))
  }

  const updateGithubUrl = (index: number, value: string) => {
    const updated = [...githubUrls]
    updated[index] = value
    setGithubUrls(updated)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!jdText.trim()) return

    setSubmitting(true)
    setError(null)

    try {
      // Build input data
      const inputData: Record<string, unknown> = {
        jd_text: jdText,
        experience_level: experienceLevel,
        max_questions: maxQuestions,
      }

      // Add optional fields if provided
      if (linkedinUrl.trim()) {
        inputData.linkedin_url = linkedinUrl.trim()
      }

      const validGithubUrls = githubUrls.filter(url => url.trim())
      if (validGithubUrls.length > 0) {
        inputData.github_urls = validGithubUrls
      }

      if (githubUsername.trim()) {
        inputData.candidate_github_username = githubUsername.trim()
      }

      if (focusAreas.trim()) {
        inputData.focus_areas = focusAreas.split(',').map(s => s.trim()).filter(Boolean)
      }

      const job = await createJob(inputData)
      navigate(`/jobs/${job.job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('create_job')}</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* JD Text - Required */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            {t('jd_section_title', '채용공고')} <span className="text-red-500">*</span>
          </h2>
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder={t('jd_placeholder')}
            rows={8}
            className="w-full border border-gray-300 rounded-lg p-3 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
            minLength={50}
          />
          <p className="text-sm text-gray-500 mt-1">
            {jdText.length}/50 {t('min_chars', '최소 글자')}
          </p>
        </div>

        {/* Experience Level */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            {t('candidate_info', '후보자 정보')}
          </h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('experience_level')} <span className="text-red-500">*</span>
              </label>
              <select
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500"
              >
                <option value="신입">{t('level_entry')}</option>
                <option value="주니어">{t('level_junior')}</option>
                <option value="미들">{t('level_mid')}</option>
                <option value="시니어">{t('level_senior')}</option>
                <option value="CTO/VP">{t('level_executive')}</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('github_username', 'GitHub 사용자명')}
              </label>
              <input
                type="text"
                value={githubUsername}
                onChange={(e) => setGithubUsername(e.target.value)}
                placeholder="e.g. octocat"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* LinkedIn URL */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('linkedin_url', 'LinkedIn 프로필 URL')}
            </label>
            <input
              type="url"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              placeholder="https://linkedin.com/in/username"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* GitHub Repos */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-semibold text-gray-900">
              {t('github_repos', 'GitHub 레포지토리')}
            </h2>
            {githubUrls.length < 5 && (
              <button
                type="button"
                onClick={addGithubUrl}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                + {t('add_repo', '레포 추가')}
              </button>
            )}
          </div>

          <div className="space-y-2">
            {githubUrls.map((url, index) => (
              <div key={index} className="flex gap-2">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => updateGithubUrl(index, e.target.value)}
                  placeholder="https://github.com/user/repo"
                  className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500"
                />
                {githubUrls.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeGithubUrl(index)}
                    className="px-3 py-2 text-red-600 hover:text-red-800"
                    aria-label={t('remove', '삭제')}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-2">
            {t('github_repos_hint', '분석할 GitHub 레포지토리 URL을 입력하세요 (최대 5개)')}
          </p>
        </div>

        {/* Options */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            {t('options', '옵션')}
          </h2>

          <div className="space-y-4">
            {/* Max Questions */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('max_questions', '생성할 질문 수')}: <span className="font-semibold">{maxQuestions}</span>
              </label>
              <input
                type="range"
                min={5}
                max={25}
                value={maxQuestions}
                onChange={(e) => setMaxQuestions(Number(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>5</span>
                <span>15</span>
                <span>25</span>
              </div>
            </div>

            {/* Focus Areas */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('focus_areas', '집중 기술 영역')}
              </label>
              <input
                type="text"
                value={focusAreas}
                onChange={(e) => setFocusAreas(e.target.value)}
                placeholder="e.g. React, TypeScript, System Design"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-sm text-gray-500 mt-1">
                {t('focus_areas_hint', '쉼표로 구분하여 입력 (선택사항)')}
              </p>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/jobs')}
            className="px-6 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            {t('cancel', '취소')}
          </button>
          <button
            type="submit"
            disabled={submitting || jdText.length < 50}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? t('loading') : t('create_interview_script', '면접 스크립트 생성')}
          </button>
        </div>
      </form>
    </div>
  )
}
