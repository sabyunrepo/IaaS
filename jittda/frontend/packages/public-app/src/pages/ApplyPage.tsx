import { useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { API_BASE } from '../lib/api'

interface FileState {
  file: File | null
  path: string | null
  uploading: boolean
}

export function ApplyPage() {
  const { slug, jobId } = useParams<{ slug: string; jobId: string }>()
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [githubUsername, setGithubUsername] = useState('')
  const [githubUrls, setGithubUrls] = useState('')
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [resume, setResume] = useState<FileState>({ file: null, path: null, uploading: false })
  const [coverLetter, setCoverLetter] = useState<FileState>({ file: null, path: null, uploading: false })
  const [portfolio, setPortfolio] = useState<FileState>({ file: null, path: null, uploading: false })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const resumeRef = useRef<HTMLInputElement>(null)
  const coverLetterRef = useRef<HTMLInputElement>(null)
  const portfolioRef = useRef<HTMLInputElement>(null)

  const uploadFile = async (
    file: File,
    fileType: string,
    setter: React.Dispatch<React.SetStateAction<FileState>>,
  ) => {
    setter((s) => ({ ...s, file, uploading: true }))
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${API_BASE}/api/public/uploads/${fileType}`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.detail || `업로드 실패 (${res.status})`)
      }
      const data = await res.json()
      setter({ file, path: data.file_path, uploading: false })
    } catch (err) {
      setter({ file: null, path: null, uploading: false })
      setError(err instanceof Error ? err.message : '파일 업로드 실패')
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim() || !email.trim()) {
      setError('이름과 이메일은 필수입니다.')
      return
    }

    setIsSubmitting(true)
    try {
      const urls = githubUrls
        .split('\n')
        .map((u) => u.trim())
        .filter(Boolean)

      const res = await fetch(`${API_BASE}/api/careers/${slug}/${jobId}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_name: name.trim(),
          candidate_email: email.trim(),
          github_username: githubUsername.trim() || undefined,
          github_urls: urls.length > 0 ? urls : undefined,
          linkedin_url: linkedinUrl.trim() || undefined,
          resume_path: resume.path || undefined,
          cover_letter_path: coverLetter.path || undefined,
          portfolio_path: portfolio.path || undefined,
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.detail || `요청 실패 (${res.status})`)
      }

      const data = await res.json()
      navigate('/apply/confirm', {
        state: { name, email, applicationId: data.application_id },
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const inputClass =
    'w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]'

  return (
    <div className="min-h-screen bg-[--color-bg-primary]">
      <header className="bg-[--color-bg-surface] border-b border-[--color-border-default]">
        <div className="max-w-2xl mx-auto px-4 py-8">
          <Link
            to={`/careers/${slug}/${jobId}`}
            className="text-sm text-[--color-text-accent] hover:underline mb-4 inline-block"
          >
            &larr; 공고로 돌아가기
          </Link>
          <h1 className="text-2xl font-bold text-[--color-text-primary]">지원하기</h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* 이름 */}
          <div>
            <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
              이름 <span className="text-[--color-text-danger]">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          {/* 이메일 */}
          <div>
            <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
              이메일 <span className="text-[--color-text-danger]">*</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className={inputClass}
            />
          </div>

          {/* GitHub Username */}
          <div>
            <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
              GitHub Username
            </label>
            <input
              type="text"
              value={githubUsername}
              onChange={(e) => setGithubUsername(e.target.value)}
              placeholder="username"
              className={inputClass}
            />
          </div>

          {/* GitHub URLs */}
          <div>
            <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
              GitHub Repository URLs
            </label>
            <textarea
              value={githubUrls}
              onChange={(e) => setGithubUrls(e.target.value)}
              rows={3}
              placeholder="https://github.com/user/repo1&#10;https://github.com/user/repo2"
              className={inputClass}
            />
            <p className="text-xs text-[--color-text-tertiary] mt-1">
              분석할 레포지토리 URL을 한 줄에 하나씩 입력하세요.
            </p>
          </div>

          {/* LinkedIn */}
          <div>
            <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
              LinkedIn URL
            </label>
            <input
              type="url"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              placeholder="https://linkedin.com/in/username"
              className={inputClass}
            />
          </div>

          {/* 파일 업로드 */}
          <FileUploadField
            label="이력서 (PDF)"
            accept=".pdf"
            fileState={resume}
            inputRef={resumeRef}
            onSelect={(f) => uploadFile(f, 'resume', setResume)}
          />
          <FileUploadField
            label="커버레터 (PDF, DOCX)"
            accept=".pdf,.docx"
            fileState={coverLetter}
            inputRef={coverLetterRef}
            onSelect={(f) => uploadFile(f, 'cover_letter', setCoverLetter)}
          />
          <FileUploadField
            label="포트폴리오 (PDF, DOCX)"
            accept=".pdf,.docx"
            fileState={portfolio}
            inputRef={portfolioRef}
            onSelect={(f) => uploadFile(f, 'portfolio', setPortfolio)}
          />

          {error && (
            <p className="text-sm text-[--color-text-danger] bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting || resume.uploading || coverLetter.uploading || portfolio.uploading}
            className="w-full px-4 py-2.5 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {isSubmitting ? '제출 중...' : '지원서 제출'}
          </button>
        </form>
      </main>
    </div>
  )
}

function FileUploadField({
  label,
  accept,
  fileState,
  inputRef,
  onSelect,
}: {
  label: string
  accept: string
  fileState: FileState
  inputRef: React.RefObject<HTMLInputElement | null>
  onSelect: (file: File) => void
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
        {label}
      </label>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) onSelect(file)
        }}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={fileState.uploading}
        className="w-full px-3 py-3 border-2 border-dashed border-[--color-border-default] rounded-lg text-sm text-[--color-text-secondary] hover:border-[--color-text-accent] hover:text-[--color-text-accent] transition-colors disabled:opacity-50"
      >
        {fileState.uploading
          ? '업로드 중...'
          : fileState.file
            ? `${fileState.file.name} (업로드 완료)`
            : '클릭하여 파일 선택'}
      </button>
    </div>
  )
}
