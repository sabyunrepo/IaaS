import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useCandidate } from '../hooks/useCandidate'
import { useAuth } from '../hooks/useAuth'
import { SectionCard } from '../components/SectionCard'
import { FileUploadField, type FileUpload } from '../components/FileUploadField'
import { GitHubRepoSelector } from '../components/GitHubRepoSelector'
import { getToken } from '../lib/api'

export function CandidateRegisterPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { createCandidate } = useCandidate()
  const { user } = useAuth()

  // Basic info — auto-fill from authenticated user
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('미들')
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [githubUsername, setGithubUsername] = useState('')
  const [skillInput, setSkillInput] = useState('')
  const [skills, setSkills] = useState<string[]>([])
  const [selectedRepos, setSelectedRepos] = useState<string[]>([])

  // Auto-fill from auth user data
  useEffect(() => {
    if (!user) return
    if (!name && user.display_name) setName(user.display_name)
    if (!email && user.email) setEmail(user.email)
    if (!githubUsername && user.github_username) setGithubUsername(user.github_username)
  }, [user]) // eslint-disable-line react-hooks/exhaustive-deps

  // File uploads
  const [resume, setResume] = useState<FileUpload>({ file: null, path: null, uploading: false, error: null })
  const [portfolio, setPortfolio] = useState<FileUpload>({ file: null, path: null, uploading: false, error: null })
  const [coverLetter, setCoverLetter] = useState<FileUpload>({ file: null, path: null, uploading: false, error: null })

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Skill management
  const addSkill = () => {
    const trimmed = skillInput.trim()
    if (trimmed && !skills.includes(trimmed)) {
      setSkills(prev => [...prev, trimmed])
      setSkillInput('')
    }
  }

  const removeSkill = (skill: string) => {
    setSkills(prev => prev.filter(s => s !== skill))
  }

  const handleSkillKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addSkill()
    }
  }

  // File upload handler (reuse CreateJobPage pattern)
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
      const response = await fetch(`/api/v1/upload/${fileType}`, {
        method: 'POST',
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
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
    if (file) uploadFile(file, fileType, setFileState)
  }

  const removeFile = (setFileState: React.Dispatch<React.SetStateAction<FileUpload>>) => {
    setFileState({ file: null, path: null, uploading: false, error: null })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    setSubmitting(true)
    setError(null)

    try {
      const profileData: Record<string, unknown> = {}
      if (resume.path) profileData.resume_path = resume.path
      if (portfolio.path) profileData.portfolio_path = portfolio.path
      if (coverLetter.path) profileData.cover_letter_path = coverLetter.path

      if (selectedRepos.length > 0) profileData.selected_repos = selectedRepos

      await createCandidate({
        name: name.trim(),
        email: email.trim() || undefined,
        experience_level: experienceLevel,
        skills: skills.length > 0 ? skills : undefined,
        github_username: githubUsername.trim() || undefined,
        linkedin_url: linkedinUrl.trim() || undefined,
        profile_data: Object.keys(profileData).length > 0 ? profileData : undefined,
      })

      navigate('/find-cto')
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  }

  const isUploading = resume.uploading || portfolio.uploading || coverLetter.uploading
  const canSubmit = name.trim().length > 0 && !submitting && !isUploading

  return (
    <div className="mx-auto max-w-3xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('register_candidate')}</h1>
            <p className="mt-0.5 text-sm text-gray-500">{t('register_candidate_desc')}</p>
          </div>
        </div>
      </div>

      {/* Auto-fill info banner */}
      {user && (user.display_name || user.email || user.github_username) && (
        <div className="mb-6 rounded-lg border border-indigo-200 bg-indigo-50 p-4">
          <div className="flex items-center gap-3">
            <svg className="h-5 w-5 flex-shrink-0 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-indigo-800">{t('auto_filled_info')}</p>
              <p className="mt-0.5 text-xs text-indigo-600">{t('auto_filled_hint')}</p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <SectionCard title={t('candidate_basic_info')} required>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                {t('candidate_name')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t('candidate_name_placeholder')}
                className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                required
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                {t('candidate_email')}
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="email@example.com"
                className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              />
            </div>
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
          </div>
        </SectionCard>

        {/* Skills */}
        <SectionCard title={t('candidate_skills')}>
          <div>
            <div className="flex gap-2">
              <input
                type="text"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={handleSkillKeyDown}
                placeholder={t('candidate_skill_placeholder')}
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2.5 text-gray-900 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              />
              <button
                type="button"
                onClick={addSkill}
                className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
              >
                {t('candidate_add_skill')}
              </button>
            </div>
            {skills.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {skills.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1 rounded-md bg-indigo-50 px-2.5 py-1 text-sm font-medium text-indigo-700"
                  >
                    {skill}
                    <button
                      type="button"
                      onClick={() => removeSkill(skill)}
                      className="ml-0.5 text-indigo-400 hover:text-indigo-600"
                    >
                      <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </SectionCard>

        {/* External Profiles */}
        <SectionCard title={t('candidate_external_profiles')}>
          <div className="grid gap-4 sm:grid-cols-2">
            {/* GitHub */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                GitHub
              </label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                  </svg>
                </div>
                <input
                  type="text"
                  value={githubUsername}
                  onChange={(e) => setGithubUsername(e.target.value)}
                  placeholder="username"
                  className="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-3 text-gray-900 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
            </div>
            {/* LinkedIn */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">
                LinkedIn
              </label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
                  </svg>
                </div>
                <input
                  type="url"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://linkedin.com/in/username"
                  className="w-full rounded-lg border border-gray-300 py-2.5 pl-10 pr-3 text-gray-900 transition-colors focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
            </div>
          </div>
        </SectionCard>

        {/* GitHub Repository Selection */}
        <SectionCard
          title={t('github_repos')}
          description={t('github_repos_desc')}
        >
          <GitHubRepoSelector
            selectedRepos={selectedRepos}
            onSelectionChange={setSelectedRepos}
            maxSelection={10}
            githubConnected={!!(user?.providers?.includes('github'))}
          />
        </SectionCard>

        {/* Document Upload */}
        <SectionCard
          title={t('document_upload')}
          description={t('document_upload_hint')}
        >
          <div className="grid gap-4 sm:grid-cols-3">
            <FileUploadField
              label={`${t('resume')} (PDF)`}
              accept=".pdf"
              fileState={resume}
              onFileChange={(e) => handleFileChange(e, 'resume', setResume)}
              onRemove={() => removeFile(setResume)}
              t={t}
            />
            <FileUploadField
              label={`${t('portfolio')} (PDF, DOCX)`}
              accept=".pdf,.docx"
              fileState={portfolio}
              onFileChange={(e) => handleFileChange(e, 'portfolio', setPortfolio)}
              onRemove={() => removeFile(setPortfolio)}
              t={t}
            />
            <FileUploadField
              label={`${t('cover_letter')} (PDF, DOCX)`}
              accept=".pdf,.docx"
              fileState={coverLetter}
              onFileChange={(e) => handleFileChange(e, 'cover_letter', setCoverLetter)}
              onRemove={() => removeFile(setCoverLetter)}
              t={t}
            />
          </div>
        </SectionCard>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
            <svg className="h-5 w-5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="text-sm font-medium text-red-700">{error}</span>
          </div>
        )}

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 border-t border-gray-200 pt-6">
          <button
            type="button"
            onClick={() => navigate('/find-cto')}
            className="rounded-lg border border-gray-300 bg-white px-5 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
          >
            {t('cancel')}
          </button>
          <button
            type="submit"
            disabled={!canSubmit}
            className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-6 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:from-indigo-700 hover:to-purple-700 hover:shadow-md disabled:cursor-not-allowed disabled:from-gray-400 disabled:to-gray-400 disabled:shadow-none"
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
              <>
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                </svg>
                {t('register_candidate')}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
