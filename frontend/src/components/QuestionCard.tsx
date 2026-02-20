import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ActionButton, Badge } from '../../seed-design/ui'

// Backend returns this structure from finalization
export interface Question {
  // New backend structure (finalization output)
  revised_question?: string
  original_question?: string
  revision_type?: string
  revision_rationale?: string
  new_confidence_score?: number
  new_evidence_reference?: string
  original_index?: number

  // Legacy fields (for backwards compatibility)
  question_text?: string
  category?: string
  difficulty?: string
  alternative_phrasings?: string[]
  expected_answer?: Record<string, unknown>
  evaluation_scenarios?: Array<Record<string, unknown>>
  follow_up_questions?: Array<Record<string, unknown>>
  terminology?: Array<Record<string, string>>
  interviewer_note?: string | Record<string, unknown>
  time_allocation_minutes?: number
  code_reference?: Record<string, unknown>
}

interface QuestionCardProps {
  question: Question
  index: number
  onScoreChange?: (index: number, score: number) => void
}

function getConfidenceColor(confidence?: number): string {
  if (!confidence) return 'text-[--color-text-secondary]'
  if (confidence >= 0.9) return 'text-green-600'
  if (confidence >= 0.7) return 'text-blue-600'
  if (confidence >= 0.5) return 'text-yellow-600'
  return 'text-red-600'
}

function getConfidenceLabel(confidence?: number): string {
  if (!confidence) return ''
  if (confidence >= 0.9) return 'High'
  if (confidence >= 0.7) return 'Medium'
  if (confidence >= 0.5) return 'Low'
  return 'Very Low'
}

function getRevisionTypeBadge(type: string | undefined, t: (key: string) => string): { tone: 'brand' | 'informative' | 'critical' | 'positive' | 'neutral'; label: string } | null {
  if (!type) return null
  const badges: Record<string, { tone: 'brand' | 'informative' | 'critical' | 'positive' | 'neutral'; labelKey: string }> = {
    'duplicate_merge': { tone: 'brand', labelKey: 'badge_duplicate_merge' },
    'clarity_fix': { tone: 'informative', labelKey: 'badge_clarity_fix' },
    'hallucination_fix': { tone: 'critical', labelKey: 'badge_hallucination_fix' },
    'evidence_improvement': { tone: 'positive', labelKey: 'badge_evidence_improvement' },
    'scope_adjustment': { tone: 'brand', labelKey: 'badge_scope_adjustment' },
  }
  const badge = badges[type]
  if (!badge) return { tone: 'neutral', label: type }
  return { tone: badge.tone, label: t(badge.labelKey) }
}

export function QuestionCard({ question, index, onScoreChange }: QuestionCardProps) {
  const { t } = useTranslation()
  const [expanded, setExpanded] = useState(false)
  const [score, setScore] = useState<number | null>(null)

  // Get question text from either new or legacy structure
  const questionText = question.revised_question || question.question_text || ''
  const confidence = question.new_confidence_score
  const confidenceColor = getConfidenceColor(confidence)
  const confidenceLabel = getConfidenceLabel(confidence)
  const revisionBadge = getRevisionTypeBadge(question.revision_type, t)

  // Legacy difficulty support
  const difficultyColor =
    question.difficulty === 'Hard' ? 'text-red-600' :
    question.difficulty === 'Medium' ? 'text-yellow-600' : 'text-green-600'

  const handleScore = (s: number) => {
    setScore(s)
    onScoreChange?.(index, s)
  }

  return (
    <div className="bg-[--color-bg-surface] rounded-xl shadow-sm border border-[--color-border-default] overflow-hidden hover:shadow-md transition-shadow">
      <button
        type="button"
        className="w-full p-5 cursor-pointer flex items-start justify-between hover:bg-[--color-bg-surface-hover] text-left gap-4"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        aria-controls={`question-${index}-details`}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-em-100 text-em-800 text-sm font-semibold">
              {index + 1}
            </span>

            {/* Revision type badge */}
            {revisionBadge && (
              <Badge tone={revisionBadge.tone} variant="weak">
                {revisionBadge.label}
              </Badge>
            )}

            {/* Confidence score */}
            {confidence !== undefined && (
              <span className={`text-xs font-medium ${confidenceColor}`}>
                {confidenceLabel} ({Math.round(confidence * 100)}%)
              </span>
            )}

            {/* Legacy difficulty */}
            {question.difficulty && (
              <span className={`text-xs font-medium ${difficultyColor}`}>
                {question.difficulty}
              </span>
            )}
          </div>

          <p className="text-[--color-text-primary] leading-relaxed">{questionText}</p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {question.time_allocation_minutes && (
            <span className="text-xs text-[--color-text-tertiary] whitespace-nowrap">
              {question.time_allocation_minutes}{t('minutes')}
            </span>
          )}
          <span className={`text-[--color-text-tertiary] transition-transform ${expanded ? 'rotate-180' : ''}`} aria-hidden="true">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </span>
        </div>
      </button>

      {expanded && (
        <div id={`question-${index}-details`} className="px-5 pb-5 space-y-4 border-t border-[--color-border-subtle]" role="region" aria-label={`Q${index + 1} ${t('details')}`}>

          {/* Original question (if revised) */}
          {question.original_question && question.original_question !== questionText && (
            <div className="mt-3 p-3 rounded-lg bg-[--color-bg-page] border border-[--color-border-default]">
              <h4 className="text-xs font-semibold text-[--color-text-tertiary] uppercase tracking-wide mb-1">{t('qcard_original_question')}</h4>
              <p className="text-sm text-[--color-text-secondary]">{question.original_question}</p>
            </div>
          )}

          {/* Revision rationale */}
          {question.revision_rationale && (
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
              <h4 className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-1">{t('qcard_revision_rationale')}</h4>
              <p className="text-sm text-blue-800">{question.revision_rationale}</p>
            </div>
          )}

          {/* Evidence reference */}
          {question.new_evidence_reference && (
            <div className="p-3 rounded-lg bg-green-50 border border-green-200">
              <h4 className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-1">{t('qcard_evidence_reference')}</h4>
              <p className="text-sm text-green-800">{question.new_evidence_reference}</p>
            </div>
          )}

          {/* Legacy: Expected answer */}
          {question.expected_answer && (
            <div>
              <h4 className="text-sm font-semibold text-[--color-text-secondary] mb-2">{t('expected_answer')}</h4>
              {Object.entries(question.expected_answer).map(([level, answer]) => (
                <div key={level} className={`text-sm p-3 rounded-lg mb-2 ${
                  level === 'expert' ? 'bg-green-50 text-green-800 border border-green-200' :
                  level === 'mid_level' ? 'bg-yellow-50 text-yellow-800 border border-yellow-200' :
                  'bg-red-50 text-red-800 border border-red-200'
                }`}>
                  <strong className="capitalize">{level.replace('_', ' ')}:</strong> {String(answer)}
                </div>
              ))}
            </div>
          )}

          {/* Legacy: Follow-up questions */}
          {question.follow_up_questions && question.follow_up_questions.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[--color-text-secondary] mb-2">{t('follow_up')}</h4>
              <div className="space-y-1">
                {question.follow_up_questions.map((fq, i) => (
                  <p key={i} className="text-sm text-[--color-text-secondary] pl-4 border-l-2 border-[--color-border-default]">
                    {typeof fq === 'string' ? fq : String((fq as Record<string, unknown>).question || JSON.stringify(fq))}
                  </p>
                ))}
              </div>
            </div>
          )}

          {/* Legacy: Terminology */}
          {question.terminology && question.terminology.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[--color-text-secondary] mb-2">{t('terminology')}</h4>
              <div className="grid gap-2">
                {question.terminology.map((term, i) => (
                  <div key={i} className="text-sm p-2 rounded bg-em-50 border border-em-200">
                    <strong className="text-em-800">{term.term}</strong>
                    <span className="text-em-700">: {term.plain_language_explanation || term.definition}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Legacy: Interviewer note */}
          {question.interviewer_note && (
            <div className="p-3 rounded-lg bg-em-50 border border-em-200">
              <h4 className="text-xs font-semibold text-em-800 uppercase tracking-wide mb-1">{t('interviewer_note')}</h4>
              <p className="text-sm text-em-800">
                {typeof question.interviewer_note === 'string'
                  ? question.interviewer_note
                  : JSON.stringify(question.interviewer_note)}
              </p>
            </div>
          )}

          {/* Scoring */}
          <div className="flex items-center gap-3 pt-3 border-t border-[--color-border-subtle] no-print">
            <span className="text-sm font-medium text-[--color-text-secondary]">{t('scoring')}:</span>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((s) => (
                <ActionButton
                  key={s}
                  variant={score === s ? "brandSolid" : "neutralOutline"}
                  size="xsmall"
                  onClick={() => handleScore(s)}
                  aria-label={`${t('scoring')} ${s}/5`}
                  aria-pressed={score === s}
                >
                  {s}
                </ActionButton>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
