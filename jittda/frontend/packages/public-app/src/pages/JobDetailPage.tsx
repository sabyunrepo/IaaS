import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { API_BASE } from '../lib/api'

interface JobDetail {
  id: string
  title: string
  department?: string
  location?: string
  type?: string
  description?: string
  requirements?: string[]
  tech_stack?: string[]
}

export function JobDetailPage() {
  const { slug, jobId } = useParams<{ slug: string; jobId: string }>()
  const [job, setJob] = useState<JobDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/careers/${slug}/${jobId}`)
      .then((res) => {
        if (!res.ok) throw new Error('공고를 찾을 수 없습니다.')
        return res.json()
      })
      .then(setJob)
      .catch((err) => setError(err.message))
      .finally(() => setIsLoading(false))
  }, [slug, jobId])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
        <p className="text-[--color-text-secondary]">로딩 중...</p>
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
        <div className="text-center">
          <p className="text-[--color-text-danger]">{error || '공고를 찾을 수 없습니다.'}</p>
          <Link to={`/careers/${slug}`} className="text-sm text-[--color-text-accent] hover:underline mt-2 inline-block">
            목록으로 돌아가기
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[--color-bg-primary]">
      <header className="bg-[--color-bg-surface] border-b border-[--color-border-default]">
        <div className="max-w-3xl mx-auto px-4 py-8">
          <Link
            to={`/careers/${slug}`}
            className="text-sm text-[--color-text-accent] hover:underline mb-4 inline-block"
          >
            &larr; 전체 포지션
          </Link>
          <h1 className="text-2xl font-bold text-[--color-text-primary]">{job.title}</h1>
          <div className="flex gap-3 mt-2 text-sm text-[--color-text-secondary]">
            {job.department && <span>{job.department}</span>}
            {job.location && <span>{job.location}</span>}
            {job.type && <span>{job.type}</span>}
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {job.description && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-[--color-text-primary] mb-3">소개</h2>
            <p className="text-[--color-text-secondary] whitespace-pre-line">{job.description}</p>
          </section>
        )}

        {job.requirements && job.requirements.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-[--color-text-primary] mb-3">자격 요건</h2>
            <ul className="list-disc list-inside space-y-1 text-[--color-text-secondary]">
              {job.requirements.map((req, i) => (
                <li key={i}>{req}</li>
              ))}
            </ul>
          </section>
        )}

        {job.tech_stack && job.tech_stack.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-[--color-text-primary] mb-3">기술 스택</h2>
            <div className="flex flex-wrap gap-2">
              {job.tech_stack.map((tech) => (
                <span
                  key={tech}
                  className="px-2.5 py-1 bg-[--color-bg-neutral] text-[--color-text-primary] rounded-md text-sm"
                >
                  {tech}
                </span>
              ))}
            </div>
          </section>
        )}

        <Link
          to={`/careers/${slug}/${jobId}/apply`}
          className="inline-block px-6 py-3 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg font-medium hover:opacity-90 transition-opacity"
        >
          지원하기
        </Link>
      </main>
    </div>
  )
}
