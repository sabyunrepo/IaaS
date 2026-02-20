import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { API_BASE } from '../lib/api'

export function ApplyPage() {
  const { slug, jobId } = useParams<{ slug: string; jobId: string }>()
  const navigate = useNavigate()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [githubUrl, setGithubUrl] = useState('')
  const [coverLetter, setCoverLetter] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim() || !email.trim() || !githubUrl.trim()) {
      setError('이름, 이메일, GitHub URL은 필수입니다.')
      return
    }

    setIsSubmitting(true)
    try {
      const res = await fetch(`${API_BASE}/api/careers/${slug}/${jobId}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          github_url: githubUrl.trim(),
          cover_letter: coverLetter.trim() || undefined,
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.detail || `요청 실패 (${res.status})`)
      }

      navigate('/apply/confirm', { state: { name, email } })
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.')
    } finally {
      setIsSubmitting(false)
    }
  }

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
          <div>
            <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
              이름 <span className="text-[--color-text-danger]">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
              이메일 <span className="text-[--color-text-danger]">*</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
              GitHub 프로필 URL <span className="text-[--color-text-danger]">*</span>
            </label>
            <input
              type="url"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              placeholder="https://github.com/username"
              required
              className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
              커버 레터 (선택)
            </label>
            <textarea
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              rows={5}
              placeholder="자기소개 또는 지원 동기를 작성해주세요."
              className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
            />
          </div>

          {error && (
            <p className="text-sm text-[--color-text-danger] bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full px-4 py-2.5 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {isSubmitting ? '제출 중...' : '지원서 제출'}
          </button>
        </form>
      </main>
    </div>
  )
}
