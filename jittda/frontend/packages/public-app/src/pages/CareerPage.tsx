import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { API_BASE } from '../lib/api'

interface PostingListing {
  id: string
  title: string
  department?: string
  jd_languages: string[]
  jd_tech_stack: string[]
  jd_experience_years?: number
  created_at?: string
}

interface CompanyInfo {
  name: string
  slug?: string
  description?: string
  logo?: string
}

export function CareerPage() {
  const { slug } = useParams<{ slug: string }>()
  const [company, setCompany] = useState<CompanyInfo>({ name: slug || '' })
  const [postings, setPostings] = useState<PostingListing[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE}/api/careers/${slug}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.company) setCompany(data.company)
        setPostings(data.postings || [])
      })
      .catch(() => setPostings([]))
      .finally(() => setIsLoading(false))
  }, [slug])

  return (
    <div className="min-h-screen bg-[--color-bg-primary]">
      {/* Header */}
      <header className="bg-[--color-bg-surface] border-b border-[--color-border-default]">
        <div className="max-w-3xl mx-auto px-4 py-12 text-center">
          {company.logo && (
            <img
              src={company.logo}
              alt={company.name}
              className="w-16 h-16 mx-auto mb-4 rounded-xl object-contain"
            />
          )}
          <h1 className="text-3xl font-bold text-[--color-text-primary]">{company.name}</h1>
          {company.description && (
            <p className="text-[--color-text-secondary] mt-2 max-w-xl mx-auto">
              {company.description}
            </p>
          )}
        </div>
      </header>

      {/* Job listings */}
      <main className="max-w-3xl mx-auto px-4 py-8">
        <h2 className="text-lg font-semibold text-[--color-text-primary] mb-4">
          채용 중인 포지션
        </h2>

        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl p-5 animate-pulse"
              >
                <div className="h-5 bg-[--color-bg-neutral] rounded w-48 mb-2" />
                <div className="h-4 bg-[--color-bg-neutral] rounded w-32" />
              </div>
            ))}
          </div>
        ) : postings.length === 0 ? (
          <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl p-8 text-center">
            <p className="text-[--color-text-secondary]">
              현재 채용 중인 포지션이 없습니다.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {postings.map((posting) => (
              <Link
                key={posting.id}
                to={`/careers/${slug}/${posting.id}`}
                className="block bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl p-5 hover:shadow-card-hover transition-shadow"
              >
                <h3 className="font-medium text-[--color-text-primary]">{posting.title}</h3>
                <div className="flex items-center gap-3 mt-1 text-sm text-[--color-text-secondary]">
                  {posting.department && <span>{posting.department}</span>}
                  {posting.jd_experience_years != null && (
                    <span>{posting.jd_experience_years}+ years</span>
                  )}
                </div>
                {posting.jd_tech_stack.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {posting.jd_tech_stack.map((tech) => (
                      <span
                        key={tech}
                        className="px-2 py-0.5 text-xs rounded-full bg-[--color-bg-neutral] text-[--color-text-secondary]"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                )}
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
