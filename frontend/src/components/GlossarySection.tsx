import { memo, useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import type { InterviewScript } from '../types/interview'

interface GlossarySectionProps {
  glossary: InterviewScript['full_glossary']
}

export const GlossarySection = memo(function GlossarySection({ glossary }: GlossarySectionProps) {
  const { t } = useTranslation()
  const [expandedTerms, setExpandedTerms] = useState<Set<number>>(new Set())
  const [glossaryExpanded, setGlossaryExpanded] = useState(false)

  const toggleTerm = useCallback((idx: number) => {
    setExpandedTerms(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }, [])

  if (!glossary || glossary.length === 0) return null

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <button
        onClick={() => setGlossaryExpanded(!glossaryExpanded)}
        className="w-full p-6 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <svg className="h-5 w-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h2 className="text-lg font-semibold text-gray-900">{t('glossary')}</h2>
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
            {t('result_terms_count', { count: glossary.length })}
          </span>
        </div>
        <svg className={`w-5 h-5 text-gray-400 transition-transform ${glossaryExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {glossaryExpanded && (
        <div className="px-6 pb-6 animate-fadeIn">
          <div className="grid gap-2 sm:grid-cols-2">
            {glossary.map((term, i) => (
              <button
                key={i}
                onClick={() => toggleTerm(i)}
                className="w-full text-left rounded-lg border border-gray-100 bg-gray-50 p-3 hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <dt className="text-sm font-semibold text-gray-900">{term.term}</dt>
                  <svg className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${expandedTerms.has(i) ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
                {expandedTerms.has(i) && (
                  <dd className="mt-2 text-sm text-gray-600 animate-fadeIn">
                    {term.plain_language_explanation || term.definition}
                    {term.business_context && (
                      <p className="mt-1 text-xs text-indigo-600">{term.business_context}</p>
                    )}
                  </dd>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
})
