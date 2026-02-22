import { Link } from 'react-router-dom'
import { Plus, FileText, Users, Trash2 } from 'lucide-react'
import { usePostings, useDeletePosting } from '../hooks/usePostings'
import type { Posting } from '../types/posting'

const STATUS_BADGE: Record<Posting['status'], { text: string; style: string }> = {
  draft: { text: '초안', style: 'bg-gray-100 text-gray-800' },
  active: { text: '진행 중', style: 'bg-green-100 text-green-800' },
  closed: { text: '마감', style: 'bg-red-100 text-red-800' },
}

export function PostingListPage() {
  const { data: postings, isLoading } = usePostings()
  const deletePosting = useDeletePosting()

  const handleDelete = (id: string, title: string) => {
    if (!window.confirm(`"${title}" 공고를 삭제하시겠습니까?`)) return
    deletePosting.mutate(id)
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">채용 공고</h1>
        <Link
          to="/postings/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" />
          새 공고
        </Link>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6 animate-pulse"
            >
              <div className="h-5 bg-[--color-bg-neutral] rounded w-3/4 mb-3" />
              <div className="h-4 bg-[--color-bg-neutral] rounded w-1/2 mb-4" />
              <div className="flex gap-2 mb-4">
                <div className="h-5 bg-[--color-bg-neutral] rounded w-16" />
                <div className="h-5 bg-[--color-bg-neutral] rounded w-16" />
              </div>
              <div className="h-4 bg-[--color-bg-neutral] rounded w-24" />
            </div>
          ))}
        </div>
      ) : !postings || postings.length === 0 ? (
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-12 text-center">
          <FileText className="w-12 h-12 text-[--color-text-tertiary] mx-auto mb-4" />
          <p className="text-[--color-text-secondary] text-lg mb-2">등록된 공고가 없습니다</p>
          <p className="text-[--color-text-tertiary] text-sm mb-6">
            새 채용 공고를 등록하고 지원자를 관리하세요.
          </p>
          <Link
            to="/postings/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
          >
            <Plus className="w-4 h-4" />
            새 공고 등록
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {postings.map((posting) => {
            const statusInfo = STATUS_BADGE[posting.status] || {
              text: posting.status,
              style: 'bg-gray-100 text-gray-800',
            }

            return (
              <div
                key={posting.id}
                className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6 hover:border-[--color-border-hover] transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <Link
                    to={`/postings/${posting.id}`}
                    className="text-base font-semibold text-[--color-text-primary] hover:text-[--color-text-accent] transition-colors line-clamp-2"
                  >
                    {posting.title}
                  </Link>
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap ml-2 ${statusInfo.style}`}
                  >
                    {statusInfo.text}
                  </span>
                </div>

                {posting.department && (
                  <p className="text-sm text-[--color-text-secondary] mb-3">
                    {posting.department}
                  </p>
                )}

                {posting.jd_tech_stack.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {posting.jd_tech_stack.slice(0, 5).map((tech) => (
                      <span
                        key={tech}
                        className="inline-block px-2 py-0.5 bg-[--color-bg-neutral] text-[--color-text-secondary] rounded text-xs"
                      >
                        {tech}
                      </span>
                    ))}
                    {posting.jd_tech_stack.length > 5 && (
                      <span className="inline-block px-2 py-0.5 text-[--color-text-tertiary] text-xs">
                        +{posting.jd_tech_stack.length - 5}
                      </span>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between pt-3 border-t border-[--color-border-default]">
                  <div className="flex items-center gap-1.5 text-sm text-[--color-text-secondary]">
                    <Users className="w-4 h-4" />
                    <span>지원자 {posting.application_count}명</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Link
                      to={`/postings/${posting.id}`}
                      className="p-1.5 text-[--color-text-tertiary] hover:text-[--color-text-primary] rounded transition-colors"
                      title="상세 보기"
                    >
                      <FileText className="w-4 h-4" />
                    </Link>
                    <button
                      onClick={() => handleDelete(posting.id, posting.title)}
                      disabled={deletePosting.isPending}
                      className="p-1.5 text-[--color-text-tertiary] hover:text-[--color-text-danger] rounded transition-colors disabled:opacity-50"
                      title="삭제"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
