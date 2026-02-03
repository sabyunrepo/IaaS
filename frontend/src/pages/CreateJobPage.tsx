import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useJob } from '../hooks/useJob'
import { getToken } from '../lib/api'

const BACKEND = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

// 지원 언어 목록
const SUPPORTED_LANGUAGES = [
  { code: 'ko', name: '한국어' },
  { code: 'en', name: 'English' },
  { code: 'ja', name: '日本語' },
  { code: 'zh-CN', name: '简体中文' },
  { code: 'zh-TW', name: '繁體中文' },
  { code: 'es', name: 'Español' },
  { code: 'de', name: 'Deutsch' },
  { code: 'fr', name: 'Français' },
  { code: 'pt', name: 'Português' },
  { code: 'vi', name: 'Tiếng Việt' },
  { code: 'th', name: 'ไทย' },
  { code: 'id', name: 'Bahasa Indonesia' },
]

interface FileUpload {
  file: File | null
  path: string | null
  uploading: boolean
  error: string | null
}

export function CreateJobPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { createJob } = useJob()

  // 필수 필드
  const [jdText, setJdText] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('미들')
  const [outputLanguage, setOutputLanguage] = useState('ko')

  // 파일 업로드
  const [resume, setResume] = useState<FileUpload>({ file: null, path: null, uploading: false, error: null })
  const [portfolio, setPortfolio] = useState<FileUpload>({ file: null, path: null, uploading: false, error: null })
  const [coverLetter, setCoverLetter] = useState<FileUpload>({ file: null, path: null, uploading: false, error: null })

  // 선택 필드
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [githubUrls, setGithubUrls] = useState<string[]>([''])
  const [maxQuestions, setMaxQuestions] = useState(25)
  const [focusAreas, setFocusAreas] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 파일 업로드 핸들러
  const uploadFile = async (
    file: File,
    fileType: 'resume' | 'portfolio' | 'cover_letter',
    setFileState: React.Dispatch<React.SetStateAction<FileUpload>>
  ) => {
    setFileState(prev => ({ ...prev, uploading: true, error: null }))

    try {
      const formData = new FormData()
      formData.append('file', file)

      const token = getToken()
      const response = await fetch(`${BACKEND}/api/v1/upload/${fileType}`, {
        method: 'POST',
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      })

      if (!response.ok) {
        const errData = await response.json()
        throw new Error(errData.detail || 'Upload failed')
      }

      const data = await response.json()
      setFileState({ file, path: data.file_path, uploading: false, error: null })
    } catch (err) {
      setFileState(prev => ({
        ...prev,
        uploading: false,
        error: err instanceof Error ? err.message : 'Upload failed',
      }))
    }
  }

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    fileType: 'resume' | 'portfolio' | 'cover_letter',
    setFileState: React.Dispatch<React.SetStateAction<FileUpload>>
  ) => {
    const file = e.target.files?.[0]
    if (file) {
      uploadFile(file, fileType, setFileState)
    }
  }

  const removeFile = (setFileState: React.Dispatch<React.SetStateAction<FileUpload>>) => {
    setFileState({ file: null, path: null, uploading: false, error: null })
  }

  // GitHub URL 핸들러
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
        language_config: {
          output_language: outputLanguage,
          terminology_languages: ['ko', 'en'],
        },
      }

      // 파일 경로 추가
      if (resume.path) {
        inputData.resume_path = resume.path
      }
      if (portfolio.path) {
        inputData.portfolio_path = portfolio.path
      }
      if (coverLetter.path) {
        inputData.cover_letter_path = coverLetter.path
      }

      // 선택 필드 추가
      if (linkedinUrl.trim()) {
        inputData.linkedin_url = linkedinUrl.trim()
      }

      const validGithubUrls = githubUrls.filter(url => url.trim())
      if (validGithubUrls.length > 0) {
        inputData.github_urls = validGithubUrls
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

  const isUploading = resume.uploading || portfolio.uploading || coverLetter.uploading

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('create_job')}</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* JD Text - Required */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            {t('jd_section_title')} <span className="text-red-500">*</span>
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
            {jdText.length}/50 {t('min_chars')}
          </p>
        </div>

        {/* 파일 업로드 섹션 */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            {t('document_upload')}
          </h2>
          <p className="text-sm text-gray-500 mb-4">{t('document_upload_hint')}</p>

          <div className="space-y-4">
            {/* 이력서 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('resume')} (PDF)
              </label>
              {resume.path ? (
                <div className="flex items-center gap-2 p-2 bg-green-50 border border-green-200 rounded-lg">
                  <span className="text-green-700 text-sm flex-1 truncate">{resume.file?.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(setResume)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    {t('remove')}
                  </button>
                </div>
              ) : (
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleFileChange(e, 'resume', setResume)}
                  disabled={resume.uploading}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              )}
              {resume.uploading && <p className="text-sm text-blue-600 mt-1">{t('uploading')}</p>}
              {resume.error && <p className="text-sm text-red-600 mt-1">{resume.error}</p>}
            </div>

            {/* 포트폴리오 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('portfolio')} (PDF, DOCX)
              </label>
              {portfolio.path ? (
                <div className="flex items-center gap-2 p-2 bg-green-50 border border-green-200 rounded-lg">
                  <span className="text-green-700 text-sm flex-1 truncate">{portfolio.file?.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(setPortfolio)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    {t('remove')}
                  </button>
                </div>
              ) : (
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={(e) => handleFileChange(e, 'portfolio', setPortfolio)}
                  disabled={portfolio.uploading}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              )}
              {portfolio.uploading && <p className="text-sm text-blue-600 mt-1">{t('uploading')}</p>}
              {portfolio.error && <p className="text-sm text-red-600 mt-1">{portfolio.error}</p>}
            </div>

            {/* 커버레터 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('cover_letter')} (PDF, DOCX)
              </label>
              {coverLetter.path ? (
                <div className="flex items-center gap-2 p-2 bg-green-50 border border-green-200 rounded-lg">
                  <span className="text-green-700 text-sm flex-1 truncate">{coverLetter.file?.name}</span>
                  <button
                    type="button"
                    onClick={() => removeFile(setCoverLetter)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    {t('remove')}
                  </button>
                </div>
              ) : (
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={(e) => handleFileChange(e, 'cover_letter', setCoverLetter)}
                  disabled={coverLetter.uploading}
                  className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              )}
              {coverLetter.uploading && <p className="text-sm text-blue-600 mt-1">{t('uploading')}</p>}
              {coverLetter.error && <p className="text-sm text-red-600 mt-1">{coverLetter.error}</p>}
            </div>
          </div>
        </div>

        {/* 후보자 정보 섹션 */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            {t('candidate_info')}
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
                {t('output_language')} <span className="text-red-500">*</span>
              </label>
              <select
                value={outputLanguage}
                onChange={(e) => setOutputLanguage(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500"
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* LinkedIn URL */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('linkedin_url')}
            </label>
            <input
              type="url"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              placeholder="https://linkedin.com/in/username"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-sm text-gray-500 mt-1">{t('linkedin_hint')}</p>
          </div>
        </div>

        {/* GitHub Repos */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-lg font-semibold text-gray-900">
              {t('github_repos')}
            </h2>
            {githubUrls.length < 5 && (
              <button
                type="button"
                onClick={addGithubUrl}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                + {t('add_repo')}
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
                    aria-label={t('remove')}
                  >
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-2">
            {t('github_repos_hint')}
          </p>
        </div>

        {/* Options */}
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            {t('options')}
          </h2>

          <div className="space-y-4">
            {/* Max Questions */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('max_questions')}: <span className="font-semibold">{maxQuestions}</span>
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
                {t('focus_areas')}
              </label>
              <input
                type="text"
                value={focusAreas}
                onChange={(e) => setFocusAreas(e.target.value)}
                placeholder="e.g. React, TypeScript, System Design"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-sm text-gray-500 mt-1">
                {t('focus_areas_hint')}
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
            {t('cancel')}
          </button>
          <button
            type="submit"
            disabled={submitting || jdText.length < 50 || isUploading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? t('loading') : t('create_interview_script')}
          </button>
        </div>
      </form>
    </div>
  )
}
