import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useJob } from '../hooks/useJob'
import { useAuth } from '../hooks/useAuth'
import { getToken } from '../lib/api'
import { SectionCard } from '../components/SectionCard'
import { FileUploadField, type FileUpload } from '../components/FileUploadField'
import { EmailNotificationModal } from '../components/EmailNotificationModal'
import { ActionButton, Divider, TextFieldRoot, TextFieldInput, TextFieldTextarea, TextFieldPrefixIcon } from '../../seed-design/ui'


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

export function CreateJobPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { createJob } = useJob()
  const { user, updateNotification } = useAuth()

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
  const [gitUrl, setGitUrl] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showNotificationModal, setShowNotificationModal] = useState(false)
  const [pendingSubmit, setPendingSubmit] = useState(false)

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
      const response = await fetch(`/api/v1/upload/${fileType}`, {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!jdText.trim()) return

    // 알림 미설정 시 모달 표시
    if (user?.email_notification_enabled === null || user?.email_notification_enabled === undefined) {
      setPendingSubmit(true)
      setShowNotificationModal(true)
      return
    }

    await submitJob()
  }

  const submitJob = async () => {
    setSubmitting(true)
    setError(null)

    try {
      // Build input data
      const inputData: Record<string, unknown> = {
        jd_text: jdText,
        experience_level: experienceLevel,
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

      if (gitUrl.trim()) {
        inputData.git_url = gitUrl.trim()
      }

      const job = await createJob(inputData)
      navigate(`/interview/${job.job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  }

  const handleNotificationAccept = async () => {
    await updateNotification(true)
    setShowNotificationModal(false)
    if (pendingSubmit) {
      setPendingSubmit(false)
      await submitJob()
    }
  }

  const handleNotificationDecline = async () => {
    await updateNotification(false)
    setShowNotificationModal(false)
    if (pendingSubmit) {
      setPendingSubmit(false)
      await submitJob()
    }
  }

  const isUploading = resume.uploading || portfolio.uploading || coverLetter.uploading
  const canSubmit = jdText.length >= 50 && !submitting && !isUploading

  return (
    <div className="mx-auto max-w-3xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-em-500 to-teal-500">
            <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[--color-text-primary]">{t('create_interview_script')}</h1>
            <p className="mt-0.5 text-sm text-[--color-text-tertiary]">{t('create_subtitle')}</p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* JD Text */}
        <SectionCard
          title={t('jd_section_title')}
          description={t('jd_section_desc')}
          required
        >
          <TextFieldRoot>
            <TextFieldTextarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder={t('jd_placeholder')}
              className="min-h-[200px]"
              required
              minLength={50}
            />
          </TextFieldRoot>
          <div className="mt-2 flex items-center justify-between text-sm">
            <span className={`${jdText.length >= 50 ? 'text-green-600' : 'text-[--color-text-tertiary]'}`}>
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

        {/* 파일 업로드 섹션 */}
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

        {/* 후보자 정보 섹션 */}
        <SectionCard title={t('candidate_info')}>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[--color-text-secondary]">
                {t('experience_level')} <span className="text-red-500">*</span>
              </label>
              <select
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                className="w-full rounded-lg border border-[--color-border-default] px-3 py-2.5 text-[--color-text-primary] transition-colors focus:border-[--color-border-accent] focus:outline-none focus:ring-2 focus:ring-em-500/20"
              >
                <option value="신입">{t('level_entry')}</option>
                <option value="주니어">{t('level_junior')}</option>
                <option value="미들">{t('level_mid')}</option>
                <option value="시니어">{t('level_senior')}</option>
                <option value="CTO/VP">{t('level_executive')}</option>
              </select>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-[--color-text-secondary]">
                {t('output_language')} <span className="text-red-500">*</span>
              </label>
              <select
                value={outputLanguage}
                onChange={(e) => setOutputLanguage(e.target.value)}
                className="w-full rounded-lg border border-[--color-border-default] px-3 py-2.5 text-[--color-text-primary] transition-colors focus:border-[--color-border-accent] focus:outline-none focus:ring-2 focus:ring-em-500/20"
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
            <label className="mb-1.5 block text-sm font-medium text-[--color-text-secondary]">
              {t('linkedin_url')}
            </label>
            <TextFieldRoot>
              <TextFieldPrefixIcon svg={
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                </svg>
              } />
              <TextFieldInput
                type="url"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                placeholder="https://linkedin.com/in/username"
              />
            </TextFieldRoot>
            <p className="mt-1.5 text-sm text-[--color-text-tertiary]">{t('linkedin_hint')}</p>
          </div>
        </SectionCard>

        {/* Git URL */}
        <SectionCard title={t('git_url')} description={t('git_url_hint')}>
          <TextFieldRoot>
            <TextFieldPrefixIcon svg={
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd"/>
              </svg>
            } />
            <TextFieldInput
              type="url"
              value={gitUrl}
              onChange={(e) => setGitUrl(e.target.value)}
              placeholder="https://github.com/username"
            />
          </TextFieldRoot>
        </SectionCard>

        {/* Error Display */}
        {error && (
          <div className="flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
            <svg className="h-5 w-5 flex-shrink-0 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="text-sm font-medium text-red-700">{error}</span>
          </div>
        )}

        {/* Submit Buttons */}
        <Divider className="mb-6" />
        <div className="flex items-center justify-end gap-3">
          <ActionButton
            variant="neutralOutline"
            size="medium"
            type="button"
            onClick={() => navigate('/interview')}
          >
            {t('cancel')}
          </ActionButton>
          <ActionButton
            variant="brandSolid"
            size="medium"
            type="submit"
            loading={submitting}
            disabled={!canSubmit}
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {t('create_interview_script')}
          </ActionButton>
        </div>
      </form>

      {showNotificationModal && (
        <EmailNotificationModal
          onAccept={handleNotificationAccept}
          onDecline={handleNotificationDecline}
        />
      )}
    </div>
  )
}
