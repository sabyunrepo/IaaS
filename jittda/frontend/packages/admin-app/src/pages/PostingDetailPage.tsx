import { useState, type FormEvent } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Plus, Trash2, Play, FileText, ExternalLink } from 'lucide-react'
import { usePosting } from '../hooks/usePostings'
import {
  useApplications,
  useCreateApplication,
  useDeleteApplication,
} from '../hooks/useApplications'
import type { Posting } from '../types/posting'
import type { Application, ApplicationCreateInput } from '../types/application'

const POSTING_STATUS_BADGE: Record<Posting['status'], { text: string; style: string }> = {
  draft: { text: '초안', style: 'bg-gray-100 text-gray-800' },
  active: { text: '진행 중', style: 'bg-green-100 text-green-800' },
  closed: { text: '마감', style: 'bg-red-100 text-red-800' },
}

const APP_STATUS_BADGE: Record<Application['status'], { text: string; style: string }> = {
  pending: { text: '대기', style: 'bg-yellow-100 text-yellow-800' },
  analyzing: { text: '분석 중', style: 'bg-blue-100 text-blue-800' },
  completed: { text: '완료', style: 'bg-green-100 text-green-800' },
  failed: { text: '실패', style: 'bg-red-100 text-red-800' },
}

export function PostingDetailPage() {
  const { postingId } = useParams<{ postingId: string }>()
  const { data: posting, isLoading: postingLoading } = usePosting(postingId || '')
  const { data: applications, isLoading: appsLoading } = useApplications(postingId || '')
  const createApplication = useCreateApplication(postingId || '')
  const deleteApplication = useDeleteApplication(postingId || '')

  const [showAddForm, setShowAddForm] = useState(false)
  const [formName, setFormName] = useState('')
  const [formEmail, setFormEmail] = useState('')
  const [formGithub, setFormGithub] = useState('')
  const [formLinkedin, setFormLinkedin] = useState('')
  const [formMemo, setFormMemo] = useState('')

  const handleAddApplication = (e: FormEvent) => {
    e.preventDefault()

    const input: ApplicationCreateInput = {
      candidate_name: formName.trim() || undefined,
      candidate_email: formEmail.trim() || undefined,
      github_username: formGithub.trim() || undefined,
      linkedin_url: formLinkedin.trim() || undefined,
      memo: formMemo.trim() || undefined,
    }

    createApplication.mutate(input, {
      onSuccess: () => {
        setShowAddForm(false)
        setFormName('')
        setFormEmail('')
        setFormGithub('')
        setFormLinkedin('')
        setFormMemo('')
      },
    })
  }

  const handleDeleteApplication = (appId: string, name: string | null) => {
    if (!window.confirm(`"${name || '이름 없음'}" 지원자를 삭제하시겠습니까?`)) return
    deleteApplication.mutate(appId)
  }

  if (postingLoading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-[--color-bg-neutral] rounded w-32" />
          <div className="h-8 bg-[--color-bg-neutral] rounded w-64" />
          <div className="h-4 bg-[--color-bg-neutral] rounded w-48" />
          <div className="h-40 bg-[--color-bg-neutral] rounded w-full mt-6" />
        </div>
      </div>
    )
  }

  if (!posting) {
    return (
      <div className="p-8">
        <p className="text-[--color-text-danger]">공고를 찾을 수 없습니다.</p>
        <Link
          to="/postings"
          className="text-sm text-[--color-text-accent] hover:underline mt-2 inline-block"
        >
          목록으로 돌아가기
        </Link>
      </div>
    )
  }

  const postingStatus = POSTING_STATUS_BADGE[posting.status] || {
    text: posting.status,
    style: 'bg-gray-100 text-gray-800',
  }

  return (
    <div className="p-8">
      {/* Back link */}
      <Link
        to="/postings"
        className="inline-flex items-center gap-1.5 text-sm text-[--color-text-accent] hover:underline mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        공고 목록으로
      </Link>

      {/* Posting info */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-[--color-text-primary]">
                {posting.title}
              </h1>
              <span
                className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${postingStatus.style}`}
              >
                {postingStatus.text}
              </span>
            </div>
            {posting.department && (
              <p className="text-sm text-[--color-text-secondary]">
                {posting.department}
              </p>
            )}
          </div>
          <Link
            to={`/postings/${posting.id}/edit`}
            className="px-3 py-1.5 border border-[--color-border-default] rounded-lg text-sm text-[--color-text-secondary] hover:bg-[--color-bg-neutral] transition-colors"
          >
            편집
          </Link>
        </div>

        {posting.jd_tech_stack.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {posting.jd_tech_stack.map((tech) => (
              <span
                key={tech}
                className="inline-block px-2 py-0.5 bg-[--color-bg-neutral] text-[--color-text-secondary] rounded text-xs"
              >
                {tech}
              </span>
            ))}
          </div>
        )}

        {posting.jd_languages.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-[--color-text-tertiary] uppercase mb-1">
              요구 언어
            </p>
            <div className="flex flex-wrap gap-1.5">
              {posting.jd_languages.map((lang) => (
                <span
                  key={lang}
                  className="inline-block px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs"
                >
                  {lang}
                </span>
              ))}
            </div>
          </div>
        )}

        {posting.jd_experience_years !== null && (
          <p className="text-sm text-[--color-text-secondary] mb-4">
            요구 경력: {posting.jd_experience_years}년 이상
          </p>
        )}

        {posting.jd_description && (
          <div>
            <p className="text-xs text-[--color-text-tertiary] uppercase mb-1">
              공고 설명
            </p>
            <p className="text-sm text-[--color-text-secondary] whitespace-pre-line max-h-60 overflow-auto">
              {posting.jd_description}
            </p>
          </div>
        )}
      </div>

      {/* Applications section */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[--color-border-default]">
          <h2 className="text-lg font-semibold text-[--color-text-primary]">
            지원자 ({applications?.length || 0})
          </h2>
          <button
            onClick={() => setShowAddForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
          >
            <Plus className="w-4 h-4" />
            지원자 추가
          </button>
        </div>

        {/* Add application modal */}
        {showAddForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6 w-full max-w-md mx-4">
              <h3 className="text-lg font-semibold text-[--color-text-primary] mb-4">
                지원자 추가
              </h3>
              <form onSubmit={handleAddApplication} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
                    이름
                  </label>
                  <input
                    type="text"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    placeholder="홍길동"
                    className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
                    이메일
                  </label>
                  <input
                    type="email"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    placeholder="email@example.com"
                    className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
                    GitHub 사용자명
                  </label>
                  <input
                    type="text"
                    value={formGithub}
                    onChange={(e) => setFormGithub(e.target.value)}
                    placeholder="github-username"
                    className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
                    LinkedIn URL
                  </label>
                  <input
                    type="url"
                    value={formLinkedin}
                    onChange={(e) => setFormLinkedin(e.target.value)}
                    placeholder="https://linkedin.com/in/username"
                    className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
                    메모
                  </label>
                  <textarea
                    value={formMemo}
                    onChange={(e) => setFormMemo(e.target.value)}
                    placeholder="추가 메모"
                    rows={2}
                    className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
                  />
                </div>

                {createApplication.isError && (
                  <p className="text-sm text-[--color-text-danger] bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                    {createApplication.error instanceof Error
                      ? createApplication.error.message
                      : '지원자 추가에 실패했습니다.'}
                  </p>
                )}

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="px-4 py-2 border border-[--color-border-default] rounded-lg text-sm text-[--color-text-secondary] hover:bg-[--color-bg-neutral] transition-colors"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    disabled={createApplication.isPending}
                    className="px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                  >
                    {createApplication.isPending ? '추가 중...' : '추가'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Applications table */}
        {appsLoading ? (
          <div className="p-6">
            {[...Array(3)].map((_, i) => (
              <div
                key={i}
                className="flex items-center gap-4 py-3 animate-pulse"
              >
                <div className="h-4 bg-[--color-bg-neutral] rounded w-24" />
                <div className="h-4 bg-[--color-bg-neutral] rounded w-40" />
                <div className="h-4 bg-[--color-bg-neutral] rounded w-28" />
                <div className="h-4 bg-[--color-bg-neutral] rounded w-16" />
              </div>
            ))}
          </div>
        ) : !applications || applications.length === 0 ? (
          <div className="py-12 text-center">
            <FileText className="w-10 h-10 text-[--color-text-tertiary] mx-auto mb-3" />
            <p className="text-[--color-text-secondary]">
              등록된 지원자가 없습니다.
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-[--color-border-default]">
                <th className="text-left px-4 py-3 text-xs font-medium text-[--color-text-tertiary] uppercase">
                  이름
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-[--color-text-tertiary] uppercase">
                  이메일
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-[--color-text-tertiary] uppercase">
                  GitHub
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-[--color-text-tertiary] uppercase">
                  상태
                </th>
                <th className="text-right px-4 py-3 text-xs font-medium text-[--color-text-tertiary] uppercase">
                  작업
                </th>
              </tr>
            </thead>
            <tbody>
              {applications.map((app) => {
                const appStatus = APP_STATUS_BADGE[app.status] || {
                  text: app.status,
                  style: 'bg-gray-100 text-gray-800',
                }

                return (
                  <tr
                    key={app.id}
                    className="border-b border-[--color-border-default] hover:bg-[--color-bg-neutral] transition-colors"
                  >
                    <td className="px-4 py-3 text-sm text-[--color-text-primary]">
                      {app.candidate_name || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-[--color-text-secondary]">
                      {app.candidate_email || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {app.github_username ? (
                        <a
                          href={`https://github.com/${app.github_username}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[--color-text-accent] hover:underline inline-flex items-center gap-1"
                        >
                          {app.github_username}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span className="text-[--color-text-tertiary]">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${appStatus.style}`}
                      >
                        {appStatus.text}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <Link
                          to={`/postings/${postingId}/applications/${app.id}`}
                          className="p-1.5 text-[--color-text-tertiary] hover:text-[--color-text-primary] rounded transition-colors"
                          title="상세 보기"
                        >
                          <FileText className="w-4 h-4" />
                        </Link>
                        {app.status === 'pending' && (
                          <Link
                            to={`/postings/${postingId}/applications/${app.id}`}
                            className="p-1.5 text-[--color-text-tertiary] hover:text-[--color-text-accent] rounded transition-colors"
                            title="분석 시작"
                          >
                            <Play className="w-4 h-4" />
                          </Link>
                        )}
                        <button
                          onClick={() =>
                            handleDeleteApplication(app.id, app.candidate_name)
                          }
                          disabled={deleteApplication.isPending}
                          className="p-1.5 text-[--color-text-tertiary] hover:text-[--color-text-danger] rounded transition-colors disabled:opacity-50"
                          title="삭제"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
