import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { apiFetch } from '../lib/api'
import { QuestionCard, type Question } from '../components/QuestionCard'

function downloadJSON(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

interface CandidateSummary {
  candidate_overview?: {
    name?: string
    current_position?: string
    primary_domain?: string
    experience_years?: string
    confidence_level?: string
  }
  key_strengths?: Array<{
    strength: string
    confidence: number
    evidence?: Record<string, string | null>
  }>
  risk_flags?: Array<{
    concern: string
    severity: string
    evidence?: string
    mitigation_question?: string
  }>
  technical_expertise?: {
    languages?: Array<{ skill: string; proficiency: string; confidence: number }>
    frameworks?: Array<{ skill: string; proficiency: string; confidence: number }>
    tools?: Array<{ tool: string; proficiency: string; confidence: number }>
  }
  notable_achievements?: Array<{
    achievement: string
    source: string
    details?: string
  }>
  data_quality_assessment?: {
    overall_confidence: number
    document_quality: number
    linkedin_quality: number
    github_quality: number
    recommendations?: string[]
  }
}

interface InterviewerGuide {
  interview_overview?: {
    total_duration_minutes: number
    question_count: number
    experience_level: string
    interview_style: string
  }
  interview_flow?: {
    opening?: { script: string; duration_minutes: number }
    main_body?: { recommended_order: string[]; transition_phrases: string[] }
    closing?: { script: string; duration_minutes: number }
  }
  category_breakdown?: Array<{
    category: string
    question_count: number
    time_allocation_minutes: number
    evaluation_priority: string
    focus_areas: string[]
  }>
  evaluation_matrix?: {
    scoring_scale: string
    passing_threshold: number
    strong_hire_threshold: number
    category_weights: Record<string, number>
  }
  red_flags_summary?: string[]
  green_flags_summary?: string[]
}

interface InterviewScript {
  metadata?: {
    language?: string
    total_questions?: number
    experience_level?: string
    has_linkedin_data?: boolean
  }
  questions: Question[]
  candidate_summary?: CandidateSummary
  interviewer_guide?: InterviewerGuide
  decision_guide?: Record<string, unknown>
  full_glossary?: Array<Record<string, string>>
  linkedin_profile?: {
    name?: string
    headline?: string
    current_company?: string
    profile_url?: string
    projects?: Array<{ title: string; description?: string }>
    honors_and_awards?: Array<{ title: string; issuer?: string; description?: string }>
  }
  generated_at?: string
}

export function ResultPage() {
  const { t } = useTranslation()
  const { jobId } = useParams<{ jobId: string }>()
  const [script, setScript] = useState<InterviewScript | null>(null)
  const [activeTab, setActiveTab] = useState<'questions' | 'summary' | 'guide'>('questions')
  const [scores, setScores] = useState<Record<number, number>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!jobId) return
    apiFetch(`/jobs/${jobId}/result`)
      .then(setScript)
      .catch((err) => {
        setError(String(err))
      })
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="relative">
          <div className="h-16 w-16 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600"></div>
          </div>
        </div>
        <p className="mt-4 text-sm font-medium text-gray-500">{t('loading')}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-red-200 bg-red-50 px-6 py-12">
        <svg className="h-12 w-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p className="mt-3 text-sm font-medium text-red-800">{t('result_error')}: {error}</p>
        <Link
          to="/jobs"
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
        >
          {t('go_home')}
        </Link>
      </div>
    )
  }

  if (!script) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-gray-50 px-6 py-12">
        <svg className="h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="mt-3 text-sm font-medium text-gray-800">{t('result_error')}</p>
      </div>
    )
  }

  const questions = script.questions || []
  const summary = script.candidate_summary
  const guide = script.interviewer_guide

  const handleScoreChange = (index: number, score: number) => {
    setScores((prev) => ({ ...prev, [index]: score }))
  }

  const totalScore = Object.values(scores).reduce((sum, s) => sum + s, 0)
  const maxScore = Object.keys(scores).length * 5
  const scorePercent = maxScore > 0 ? Math.round((totalScore / maxScore) * 100) : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg">
            <svg className="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('interview_script')}</h1>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span>#{jobId?.slice(0, 8)}</span>
              <span>·</span>
              <span>{questions.length}개 질문</span>
              {script.metadata?.experience_level && (
                <>
                  <span>·</span>
                  <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-medium">
                    {script.metadata.experience_level}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {maxScore > 0 && (
            <div className="flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2">
              <svg className="h-5 w-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span className="text-sm font-semibold text-indigo-700">
                {totalScore}/{maxScore} ({scorePercent}%)
              </span>
            </div>
          )}

          <div className="flex gap-2 no-print">
            <Link
              to={`/jobs/${jobId}/logs`}
              className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-300 bg-indigo-50 px-3 py-2 text-sm font-medium text-indigo-700 transition-colors hover:bg-indigo-100"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              분석 로그
            </Link>
            <button
              onClick={() => downloadJSON(script, `interview-${jobId?.slice(0, 8)}.json`)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {t('export_json')}
            </button>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              {t('print_pdf')}
            </button>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-xl no-print">
        <button
          onClick={() => setActiveTab('questions')}
          className={`flex-1 px-4 py-2.5 text-sm font-medium rounded-lg transition-all ${
            activeTab === 'questions'
              ? 'bg-white text-indigo-700 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          질문 목록 ({questions.length})
        </button>
        <button
          onClick={() => setActiveTab('summary')}
          className={`flex-1 px-4 py-2.5 text-sm font-medium rounded-lg transition-all ${
            activeTab === 'summary'
              ? 'bg-white text-indigo-700 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          후보자 분석
        </button>
        <button
          onClick={() => setActiveTab('guide')}
          className={`flex-1 px-4 py-2.5 text-sm font-medium rounded-lg transition-all ${
            activeTab === 'guide'
              ? 'bg-white text-indigo-700 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          면접관 가이드
        </button>
      </div>

      {/* Questions Tab */}
      {activeTab === 'questions' && (
        <div className="space-y-4">
          {questions.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-xl border border-gray-200 bg-gray-50 py-12">
              <svg className="h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="mt-3 text-sm text-gray-500">생성된 질문이 없습니다</p>
            </div>
          ) : (
            questions.map((q, i) => (
              <QuestionCard
                key={i}
                question={q}
                index={i}
                onScoreChange={handleScoreChange}
              />
            ))
          )}
        </div>
      )}

      {/* Candidate Summary Tab */}
      {activeTab === 'summary' && summary && (
        <div className="space-y-6">
          {/* Candidate Overview */}
          {summary.candidate_overview && (
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="h-5 w-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                후보자 개요
              </h2>
              <div className="grid gap-4 sm:grid-cols-2">
                {summary.candidate_overview.name && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">이름</dt>
                    <dd className="mt-1 text-lg font-semibold text-gray-900">{summary.candidate_overview.name}</dd>
                  </div>
                )}
                {summary.candidate_overview.current_position && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">현재 직책</dt>
                    <dd className="mt-1 text-gray-900">{summary.candidate_overview.current_position}</dd>
                  </div>
                )}
                {summary.candidate_overview.primary_domain && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">주요 도메인</dt>
                    <dd className="mt-1 text-gray-900">{summary.candidate_overview.primary_domain}</dd>
                  </div>
                )}
                {summary.candidate_overview.experience_years && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">경력</dt>
                    <dd className="mt-1 text-gray-900">{summary.candidate_overview.experience_years}</dd>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Key Strengths */}
          {summary.key_strengths && summary.key_strengths.length > 0 && (
            <div className="rounded-xl border border-green-200 bg-green-50 p-6">
              <h2 className="text-lg font-semibold text-green-900 mb-4 flex items-center gap-2">
                <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                주요 강점
              </h2>
              <div className="space-y-3">
                {summary.key_strengths.map((item, i) => (
                  <div key={i} className="bg-white rounded-lg p-4 border border-green-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-green-900">{item.strength}</span>
                      <span className="text-sm text-green-600">신뢰도: {Math.round(item.confidence * 100)}%</span>
                    </div>
                    {item.evidence && (
                      <div className="text-sm text-green-700 space-y-1">
                        {item.evidence.resume && <p>📄 이력서: {item.evidence.resume}</p>}
                        {item.evidence.linkedin && <p>💼 LinkedIn: {item.evidence.linkedin}</p>}
                        {item.evidence.github && <p>🔗 GitHub: {item.evidence.github}</p>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Risk Flags */}
          {summary.risk_flags && summary.risk_flags.length > 0 && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-6">
              <h2 className="text-lg font-semibold text-red-900 mb-4 flex items-center gap-2">
                <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                위험 요소
              </h2>
              <div className="space-y-3">
                {summary.risk_flags.map((item, i) => (
                  <div key={i} className="bg-white rounded-lg p-4 border border-red-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-red-900">{item.concern}</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        item.severity === 'high' ? 'bg-red-200 text-red-800' :
                        item.severity === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                        'bg-gray-200 text-gray-800'
                      }`}>
                        {item.severity}
                      </span>
                    </div>
                    {item.evidence && <p className="text-sm text-red-700 mb-2">{item.evidence}</p>}
                    {item.mitigation_question && (
                      <p className="text-sm text-red-800 bg-red-100 p-2 rounded">
                        💡 확인 질문: {item.mitigation_question}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Technical Expertise */}
          {summary.technical_expertise && (
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <svg className="h-5 w-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                기술 역량
              </h2>
              <div className="space-y-4">
                {summary.technical_expertise.languages && summary.technical_expertise.languages.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">프로그래밍 언어</h3>
                    <div className="flex flex-wrap gap-2">
                      {summary.technical_expertise.languages.map((lang, i) => (
                        <span key={i} className="px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-sm">
                          {lang.skill} ({lang.proficiency})
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {summary.technical_expertise.frameworks && summary.technical_expertise.frameworks.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">프레임워크</h3>
                    <div className="flex flex-wrap gap-2">
                      {summary.technical_expertise.frameworks.map((fw, i) => (
                        <span key={i} className="px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm">
                          {fw.skill} ({fw.proficiency})
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {summary.technical_expertise.tools && summary.technical_expertise.tools.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500 mb-2">도구</h3>
                    <div className="flex flex-wrap gap-2">
                      {summary.technical_expertise.tools.map((tool, i) => (
                        <span key={i} className="px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-sm">
                          {tool.tool} ({tool.proficiency})
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Data Quality Assessment */}
          {summary.data_quality_assessment && (
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">데이터 품질 평가</h2>
              <div className="grid gap-4 sm:grid-cols-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-indigo-600">
                    {Math.round(summary.data_quality_assessment.overall_confidence * 100)}%
                  </div>
                  <div className="text-sm text-gray-500">전체 신뢰도</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {Math.round(summary.data_quality_assessment.document_quality * 100)}%
                  </div>
                  <div className="text-sm text-gray-500">문서 품질</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {Math.round(summary.data_quality_assessment.linkedin_quality * 100)}%
                  </div>
                  <div className="text-sm text-gray-500">LinkedIn</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {Math.round(summary.data_quality_assessment.github_quality * 100)}%
                  </div>
                  <div className="text-sm text-gray-500">GitHub</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Interviewer Guide Tab */}
      {activeTab === 'guide' && guide && (
        <div className="space-y-6">
          {/* Interview Overview */}
          {guide.interview_overview && (
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">면접 개요</h2>
              <div className="grid gap-4 sm:grid-cols-4">
                <div className="text-center p-3 bg-indigo-50 rounded-lg">
                  <div className="text-2xl font-bold text-indigo-600">
                    {guide.interview_overview.total_duration_minutes}분
                  </div>
                  <div className="text-sm text-gray-500">총 소요시간</div>
                </div>
                <div className="text-center p-3 bg-indigo-50 rounded-lg">
                  <div className="text-2xl font-bold text-indigo-600">
                    {guide.interview_overview.question_count}개
                  </div>
                  <div className="text-sm text-gray-500">질문 수</div>
                </div>
                <div className="text-center p-3 bg-indigo-50 rounded-lg">
                  <div className="text-lg font-bold text-indigo-600">
                    {guide.interview_overview.experience_level}
                  </div>
                  <div className="text-sm text-gray-500">경력 수준</div>
                </div>
                <div className="text-center p-3 bg-indigo-50 rounded-lg">
                  <div className="text-lg font-bold text-indigo-600">
                    {guide.interview_overview.interview_style}
                  </div>
                  <div className="text-sm text-gray-500">면접 스타일</div>
                </div>
              </div>
            </div>
          )}

          {/* Interview Flow */}
          {guide.interview_flow && (
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">면접 진행 순서</h2>
              <div className="space-y-4">
                {guide.interview_flow.opening && (
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <h3 className="font-medium text-green-900 mb-2">
                      🎬 오프닝 ({guide.interview_flow.opening.duration_minutes}분)
                    </h3>
                    <p className="text-sm text-green-800">{guide.interview_flow.opening.script}</p>
                  </div>
                )}
                {guide.interview_flow.main_body && (
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <h3 className="font-medium text-blue-900 mb-2">📋 본 면접</h3>
                    <p className="text-sm text-blue-800 mb-2">
                      진행 순서: {guide.interview_flow.main_body.recommended_order?.join(' → ')}
                    </p>
                    {guide.interview_flow.main_body.transition_phrases && (
                      <div className="text-sm text-blue-700">
                        <p className="font-medium mb-1">전환 문구:</p>
                        <ul className="list-disc list-inside">
                          {guide.interview_flow.main_body.transition_phrases.map((phrase, i) => (
                            <li key={i}>{phrase}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
                {guide.interview_flow.closing && (
                  <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                    <h3 className="font-medium text-amber-900 mb-2">
                      🏁 클로징 ({guide.interview_flow.closing.duration_minutes}분)
                    </h3>
                    <p className="text-sm text-amber-800">{guide.interview_flow.closing.script}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Evaluation Matrix */}
          {guide.evaluation_matrix && (
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">평가 기준</h2>
              <div className="grid gap-4 sm:grid-cols-3 mb-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-lg font-bold text-gray-900">
                    {guide.evaluation_matrix.scoring_scale}
                  </div>
                  <div className="text-sm text-gray-500">점수 범위</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-lg font-bold text-green-600">
                    ≥ {guide.evaluation_matrix.passing_threshold}
                  </div>
                  <div className="text-sm text-gray-500">합격 기준</div>
                </div>
                <div className="text-center p-3 bg-indigo-50 rounded-lg">
                  <div className="text-lg font-bold text-indigo-600">
                    ≥ {guide.evaluation_matrix.strong_hire_threshold}
                  </div>
                  <div className="text-sm text-gray-500">Strong Hire</div>
                </div>
              </div>
              {guide.evaluation_matrix.category_weights && (
                <div>
                  <h3 className="text-sm font-medium text-gray-500 mb-2">카테고리별 가중치</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(guide.evaluation_matrix.category_weights).map(([cat, weight]) => (
                      <span key={cat} className="px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-sm">
                        {cat}: {Math.round(Number(weight) * 100)}%
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Red/Green Flags */}
          <div className="grid gap-6 sm:grid-cols-2">
            {guide.green_flags_summary && guide.green_flags_summary.length > 0 && (
              <div className="rounded-xl border border-green-200 bg-green-50 p-6">
                <h2 className="text-lg font-semibold text-green-900 mb-3">✅ Green Flags</h2>
                <ul className="space-y-2">
                  {guide.green_flags_summary.map((flag, i) => (
                    <li key={i} className="text-sm text-green-800 flex items-start gap-2">
                      <span className="text-green-500">•</span>
                      {flag}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {guide.red_flags_summary && guide.red_flags_summary.length > 0 && (
              <div className="rounded-xl border border-red-200 bg-red-50 p-6">
                <h2 className="text-lg font-semibold text-red-900 mb-3">🚩 Red Flags</h2>
                <ul className="space-y-2">
                  {guide.red_flags_summary.map((flag, i) => (
                    <li key={i} className="text-sm text-red-800 flex items-start gap-2">
                      <span className="text-red-500">•</span>
                      {flag}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Glossary (shown on all tabs) */}
      {script.full_glossary && script.full_glossary.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <svg className="h-5 w-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <h2 className="text-lg font-semibold text-gray-900">{t('glossary')}</h2>
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
              {script.full_glossary.length}개 용어
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {script.full_glossary.map((term, i) => (
              <div key={i} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                <dt className="text-sm font-semibold text-gray-900">{term.term}</dt>
                <dd className="mt-1 text-sm text-gray-600">
                  {term.plain_language_explanation || term.definition}
                </dd>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Back to list link */}
      <div className="flex justify-center pt-4 no-print">
        <Link
          to="/jobs"
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-gray-700"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          목록으로 돌아가기
        </Link>
      </div>
    </div>
  )
}
