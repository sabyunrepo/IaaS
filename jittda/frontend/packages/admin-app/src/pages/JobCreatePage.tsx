import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../lib/api'

export function JobCreatePage() {
  const navigate = useNavigate()
  const [githubUrls, setGithubUrls] = useState('')
  const [candidateUsername, setCandidateUsername] = useState('')
  const [jdText, setJdText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    const urls = githubUrls
      .split('\n')
      .map((u) => u.trim())
      .filter(Boolean)

    if (!urls.length && !candidateUsername) {
      setError('GitHub URL 또는 후보자 사용자명을 입력해주세요.')
      setIsSubmitting(false)
      return
    }

    try {
      const res = await apiFetch('/api/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          github_urls: urls.length ? urls : undefined,
          candidate_username: candidateUsername || undefined,
          jd_text: jdText || undefined,
        }),
      })

      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.detail || `요청 실패 (${res.status})`)
      }

      const job = await res.json()
      navigate(`/jobs/${job.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-[--color-text-primary] mb-6">새 분석 시작</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
            GitHub 저장소 URL
          </label>
          <textarea
            value={githubUrls}
            onChange={(e) => setGithubUrls(e.target.value)}
            placeholder="https://github.com/user/repo&#10;한 줄에 하나씩 입력"
            rows={3}
            className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
            후보자 GitHub 사용자명
          </label>
          <input
            type="text"
            value={candidateUsername}
            onChange={(e) => setCandidateUsername(e.target.value)}
            placeholder="github-username"
            className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
            채용 공고 (JD)
          </label>
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="채용 공고 내용을 붙여넣기 (선택사항)"
            rows={6}
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
          {isSubmitting ? '분석 시작 중...' : '분석 시작'}
        </button>
      </form>
    </div>
  )
}
