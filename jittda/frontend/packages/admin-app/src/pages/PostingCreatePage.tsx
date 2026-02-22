import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Plus, X } from 'lucide-react'
import { useCreatePosting } from '../hooks/usePostings'
import type { PostingCreateInput } from '../types/posting'

export function PostingCreatePage() {
  const navigate = useNavigate()
  const createPosting = useCreatePosting()

  const [title, setTitle] = useState('')
  const [department, setDepartment] = useState('')
  const [jdDescription, setJdDescription] = useState('')
  const [jdLanguages, setJdLanguages] = useState<string[]>([])
  const [jdTechStack, setJdTechStack] = useState<string[]>([])
  const [jdExperienceYears, setJdExperienceYears] = useState('')
  const [autoAnalyze, setAutoAnalyze] = useState(false)
  const [status, setStatus] = useState<'draft' | 'active'>('draft')

  const [languageInput, setLanguageInput] = useState('')
  const [techInput, setTechInput] = useState('')

  const handleLanguageKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter') return
    e.preventDefault()
    const value = languageInput.trim()
    if (value && !jdLanguages.includes(value)) {
      setJdLanguages([...jdLanguages, value])
    }
    setLanguageInput('')
  }

  const removeLanguage = (lang: string) => {
    setJdLanguages(jdLanguages.filter((l) => l !== lang))
  }

  const handleTechKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter') return
    e.preventDefault()
    const value = techInput.trim()
    if (value && !jdTechStack.includes(value)) {
      setJdTechStack([...jdTechStack, value])
    }
    setTechInput('')
  }

  const removeTech = (tech: string) => {
    setJdTechStack(jdTechStack.filter((t) => t !== tech))
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()

    if (!title.trim()) return

    const input: PostingCreateInput = {
      title: title.trim(),
      department: department.trim() || undefined,
      jd_description: jdDescription.trim() || undefined,
      jd_languages: jdLanguages.length > 0 ? jdLanguages : undefined,
      jd_tech_stack: jdTechStack.length > 0 ? jdTechStack : undefined,
      jd_experience_years: jdExperienceYears
        ? Number(jdExperienceYears)
        : undefined,
      auto_analyze: autoAnalyze,
      status,
    }

    createPosting.mutate(input, {
      onSuccess: () => navigate('/postings'),
    })
  }

  return (
    <div className="p-8 max-w-2xl">
      <Link
        to="/postings"
        className="inline-flex items-center gap-1.5 text-sm text-[--color-text-accent] hover:underline mb-4"
      >
        <ArrowLeft className="w-4 h-4" />
        공고 목록으로
      </Link>

      <h1 className="text-2xl font-bold text-[--color-text-primary] mb-6">
        새 채용 공고
      </h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
            공고 제목 <span className="text-[--color-text-danger]">*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="예: 시니어 백엔드 엔지니어"
            required
            className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
          />
        </div>

        {/* Department */}
        <div>
          <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
            부서
          </label>
          <input
            type="text"
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            placeholder="예: 플랫폼팀"
            className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
          />
        </div>

        {/* JD Description */}
        <div>
          <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
            채용 공고 설명
          </label>
          <textarea
            value={jdDescription}
            onChange={(e) => setJdDescription(e.target.value)}
            placeholder="채용 공고 내용을 입력하세요"
            rows={6}
            className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
          />
        </div>

        {/* Languages tag input */}
        <div>
          <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
            요구 언어
          </label>
          <div className="flex flex-wrap gap-1.5 mb-2">
            {jdLanguages.map((lang) => (
              <span
                key={lang}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-[--color-bg-neutral] text-[--color-text-secondary] rounded text-xs"
              >
                {lang}
                <button
                  type="button"
                  onClick={() => removeLanguage(lang)}
                  className="text-[--color-text-tertiary] hover:text-[--color-text-danger] transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
          <input
            type="text"
            value={languageInput}
            onChange={(e) => setLanguageInput(e.target.value)}
            onKeyDown={handleLanguageKeyDown}
            placeholder="언어를 입력하고 Enter (예: Python, TypeScript)"
            className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
          />
        </div>

        {/* Tech stack tag input */}
        <div>
          <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
            기술 스택
          </label>
          <div className="flex flex-wrap gap-1.5 mb-2">
            {jdTechStack.map((tech) => (
              <span
                key={tech}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-[--color-bg-neutral] text-[--color-text-secondary] rounded text-xs"
              >
                {tech}
                <button
                  type="button"
                  onClick={() => removeTech(tech)}
                  className="text-[--color-text-tertiary] hover:text-[--color-text-danger] transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
          <input
            type="text"
            value={techInput}
            onChange={(e) => setTechInput(e.target.value)}
            onKeyDown={handleTechKeyDown}
            placeholder="기술 스택을 입력하고 Enter (예: React, FastAPI)"
            className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
          />
        </div>

        {/* Experience years */}
        <div>
          <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
            요구 경력 (년)
          </label>
          <input
            type="number"
            min={0}
            max={30}
            value={jdExperienceYears}
            onChange={(e) => setJdExperienceYears(e.target.value)}
            placeholder="예: 3"
            className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
          />
        </div>

        {/* Auto analyze toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-[--color-text-primary]">
              자동 분석
            </p>
            <p className="text-xs text-[--color-text-tertiary]">
              지원서 접수 시 자동으로 분석을 시작합니다
            </p>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={autoAnalyze}
            onClick={() => setAutoAnalyze(!autoAnalyze)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              autoAnalyze
                ? 'bg-[--color-bg-accent]'
                : 'bg-[--color-bg-neutral]'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                autoAnalyze ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {/* Status select */}
        <div>
          <label className="block text-sm font-medium text-[--color-text-primary] mb-1">
            상태
          </label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as 'draft' | 'active')}
            className="w-full px-3 py-2 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:ring-2 focus:ring-[--color-focus-ring]"
          >
            <option value="draft">초안 (Draft)</option>
            <option value="active">활성 (Active)</option>
          </select>
        </div>

        {/* Error */}
        {createPosting.isError && (
          <p className="text-sm text-[--color-text-danger] bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {createPosting.error instanceof Error
              ? createPosting.error.message
              : '공고 생성에 실패했습니다.'}
          </p>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={createPosting.isPending || !title.trim()}
          className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          {createPosting.isPending ? '생성 중...' : '공고 등록'}
        </button>
      </form>
    </div>
  )
}
