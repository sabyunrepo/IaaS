import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft,
  Play,
  ExternalLink,
  FileText,
  Github,
  Linkedin,
} from 'lucide-react'
import {
  useApplication,
  useAnalyzeApplication,
  useApplicationResult,
} from '../hooks/useApplications'
import type { Application } from '../types/application'

const APP_STATUS_BADGE: Record<
  Application['status'],
  { text: string; style: string }
> = {
  pending: { text: '대기', style: 'bg-yellow-100 text-yellow-800' },
  analyzing: { text: '분석 중', style: 'bg-blue-100 text-blue-800' },
  completed: { text: '완료', style: 'bg-green-100 text-green-800' },
  failed: { text: '실패', style: 'bg-red-100 text-red-800' },
}

export function ApplicationDetailPage() {
  const { postingId, applicationId } = useParams<{
    postingId: string
    applicationId: string
  }>()

  const { data: application, isLoading: appLoading } = useApplication(
    postingId || '',
    applicationId || '',
  )
  const analyzeApplication = useAnalyzeApplication(postingId || '')
  const { data: result, isLoading: resultLoading } = useApplicationResult(
    postingId || '',
    applicationId || '',
  )

  const handleAnalyze = () => {
    if (!applicationId) return
    analyzeApplication.mutate(applicationId)
  }

  if (appLoading) {
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

  if (!application) {
    return (
      <div className="p-8">
        <p className="text-[--color-text-danger]">지원자를 찾을 수 없습니다.</p>
        <Link
          to={`/postings/${postingId}`}
          className="text-sm text-[--color-text-accent] hover:underline mt-2 inline-block"
        >
          공고로 돌아가기
        </Link>
      </div>
    )
  }

  const statusInfo = APP_STATUS_BADGE[application.status] || {
    text: application.status,
    style: 'bg-gray-100 text-gray-800',
  }

  return (
    <div className="p-8 max-w-3xl">
      {/* Back link */}
      <Link
        to={`/postings/${postingId}`}
        className="inline-flex items-center gap-1.5 text-sm text-[--color-text-accent] hover:underline mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        공고로 돌아가기
      </Link>

      {/* Applicant info card */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-[--color-text-primary] mb-1">
              {application.candidate_name || '이름 없음'}
            </h1>
            {application.candidate_email && (
              <p className="text-sm text-[--color-text-secondary]">
                {application.candidate_email}
              </p>
            )}
          </div>
          <span
            className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${statusInfo.style}`}
          >
            {statusInfo.text}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* GitHub username */}
          {application.github_username && (
            <div className="flex items-center gap-2">
              <Github className="w-4 h-4 text-[--color-text-tertiary]" />
              <a
                href={`https://github.com/${application.github_username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-[--color-text-accent] hover:underline inline-flex items-center gap-1"
              >
                {application.github_username}
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}

          {/* LinkedIn URL */}
          {application.linkedin_url && (
            <div className="flex items-center gap-2">
              <Linkedin className="w-4 h-4 text-[--color-text-tertiary]" />
              <a
                href={application.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-[--color-text-accent] hover:underline inline-flex items-center gap-1"
              >
                LinkedIn 프로필
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}
        </div>

        {/* GitHub URLs */}
        {application.github_urls.length > 0 && (
          <div className="mt-4">
            <p className="text-xs text-[--color-text-tertiary] uppercase mb-2">
              GitHub 저장소
            </p>
            <div className="space-y-1">
              {application.github_urls.map((url) => (
                <a
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-sm text-[--color-text-accent] hover:underline inline-flex items-center gap-1"
                >
                  <Github className="w-3.5 h-3.5" />
                  {url}
                  <ExternalLink className="w-3 h-3" />
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Memo */}
        {application.memo && (
          <div className="mt-4">
            <p className="text-xs text-[--color-text-tertiary] uppercase mb-1">
              메모
            </p>
            <p className="text-sm text-[--color-text-secondary] whitespace-pre-line">
              {application.memo}
            </p>
          </div>
        )}
      </div>

      {/* File attachments */}
      {(application.resume_path ||
        application.cover_letter_path ||
        application.portfolio_path) && (
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6 mb-6">
          <h2 className="text-lg font-semibold text-[--color-text-primary] mb-4">
            첨부 파일
          </h2>
          <div className="space-y-3">
            {application.resume_path && (
              <div className="flex items-center gap-3">
                <FileText className="w-4 h-4 text-[--color-text-tertiary]" />
                <div>
                  <p className="text-xs text-[--color-text-tertiary] uppercase">
                    이력서
                  </p>
                  <a
                    href={application.resume_path}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-[--color-text-accent] hover:underline inline-flex items-center gap-1"
                  >
                    파일 보기
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            )}
            {application.cover_letter_path && (
              <div className="flex items-center gap-3">
                <FileText className="w-4 h-4 text-[--color-text-tertiary]" />
                <div>
                  <p className="text-xs text-[--color-text-tertiary] uppercase">
                    자기소개서
                  </p>
                  <a
                    href={application.cover_letter_path}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-[--color-text-accent] hover:underline inline-flex items-center gap-1"
                  >
                    파일 보기
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            )}
            {application.portfolio_path && (
              <div className="flex items-center gap-3">
                <FileText className="w-4 h-4 text-[--color-text-tertiary]" />
                <div>
                  <p className="text-xs text-[--color-text-tertiary] uppercase">
                    포트폴리오
                  </p>
                  <a
                    href={application.portfolio_path}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-[--color-text-accent] hover:underline inline-flex items-center gap-1"
                  >
                    파일 보기
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Analysis status and actions */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
        <h2 className="text-lg font-semibold text-[--color-text-primary] mb-4">
          분석
        </h2>

        {/* Pending or failed: show analyze button */}
        {(application.status === 'pending' ||
          application.status === 'failed') && (
          <div>
            <p className="text-sm text-[--color-text-secondary] mb-4">
              {application.status === 'pending'
                ? '분석이 아직 시작되지 않았습니다.'
                : '분석에 실패했습니다. 다시 시도할 수 있습니다.'}
            </p>
            <button
              onClick={handleAnalyze}
              disabled={analyzeApplication.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              {analyzeApplication.isPending ? '시작 중...' : '분석 시작'}
            </button>
            {analyzeApplication.isError && (
              <p className="text-sm text-[--color-text-danger] mt-3">
                {analyzeApplication.error instanceof Error
                  ? analyzeApplication.error.message
                  : '분석 시작에 실패했습니다.'}
              </p>
            )}
          </div>
        )}

        {/* Analyzing: show progress */}
        {application.status === 'analyzing' && (
          <div>
            <p className="text-sm text-[--color-text-secondary] mb-3">
              분석이 진행 중입니다...
            </p>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-2 bg-[--color-bg-neutral] rounded-full overflow-hidden">
                <div className="h-full bg-[--color-bg-accent] rounded-full animate-pulse w-2/3" />
              </div>
              <span className="text-xs text-[--color-text-tertiary]">
                분석 중
              </span>
            </div>
          </div>
        )}

        {/* Completed: show result link */}
        {application.status === 'completed' && (
          <div>
            <p className="text-sm text-[--color-text-secondary] mb-4">
              분석이 완료되었습니다.
            </p>

            {resultLoading ? (
              <div className="h-10 bg-[--color-bg-neutral] rounded w-32 animate-pulse" />
            ) : result ? (
              <Link
                to={`/jobs/${application.job_id}/candidates/default/analysis`}
                className="inline-flex items-center gap-2 px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
              >
                <FileText className="w-4 h-4" />
                결과 보기
              </Link>
            ) : (
              <p className="text-sm text-[--color-text-tertiary]">
                결과 데이터를 불러올 수 없습니다.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
