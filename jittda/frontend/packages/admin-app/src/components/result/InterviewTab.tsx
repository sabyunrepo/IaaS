import { useState } from 'react';
import type { AnalysisResult, InterviewQuestion } from '../../types/result';
import { BookOpen, CheckCircle, AlertCircle } from 'lucide-react';

// ---------------------------------------------------------------------------
// Strategy display mapping
// ---------------------------------------------------------------------------

const STRATEGY_META: Record<
  string,
  { label: string; color: string; bgColor: string; description: string }
> = {
  negative_selection: {
    label: '네거티브 선별',
    color: 'text-red-600',
    bgColor: 'bg-red-50 border-red-200',
    description: '후보자의 약점이나 위험 신호를 탐지하기 위한 질문입니다.',
  },
  intentional_complexity: {
    label: '의도적 복잡성',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 border-purple-200',
    description: '코드의 복잡한 부분에 대한 의도와 이해도를 확인하는 질문입니다.',
  },
  code_evolution: {
    label: '코드 진화',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 border-blue-200',
    description: '코드 변화 과정과 성장 궤적을 파악하기 위한 질문입니다.',
  },
};

const DIFFICULTY_STYLES: Record<string, { label: string; style: string }> = {
  easy: { label: '기본', style: 'bg-green-100 text-green-700' },
  medium: { label: '보통', style: 'bg-yellow-100 text-yellow-700' },
  hard: { label: '심화', style: 'bg-red-100 text-red-700' },
};

// ---------------------------------------------------------------------------
// Answer guide parsing helpers
// ---------------------------------------------------------------------------

/**
 * Markers used to split expected_answer_guide into structured sections.
 * The guide may contain these markers:
 *   [GOOD_ANSWER] ... [RED_FLAG] ... [KEY_TERMS] ...
 * If markers are absent, the entire text is treated as a general guide.
 */
interface ParsedGuide {
  goodAnswer: string | null;
  redFlag: string | null;
  keyTerms: string | null;
  general: string | null;
}

function parseAnswerGuide(raw: string | undefined): ParsedGuide | null {
  if (!raw) return null;

  const markers = {
    goodAnswer: /\[GOOD_ANSWER\]/i,
    redFlag: /\[RED_FLAG\]/i,
    keyTerms: /\[KEY_TERMS\]/i,
  };

  const hasMarkers =
    markers.goodAnswer.test(raw) ||
    markers.redFlag.test(raw) ||
    markers.keyTerms.test(raw);

  if (!hasMarkers) {
    return { goodAnswer: null, redFlag: null, keyTerms: null, general: raw.trim() };
  }

  // Split by markers
  let remaining = raw;
  let goodAnswer: string | null = null;
  let redFlag: string | null = null;
  let keyTerms: string | null = null;
  let general: string | null = null;

  // Extract sections in order: find each marker and grab text until next marker
  const allMarkers = [
    { key: 'goodAnswer' as const, regex: /\[GOOD_ANSWER\]/i },
    { key: 'redFlag' as const, regex: /\[RED_FLAG\]/i },
    { key: 'keyTerms' as const, regex: /\[KEY_TERMS\]/i },
  ];

  // Find positions of all markers
  const positions: Array<{ key: string; index: number }> = [];
  for (const m of allMarkers) {
    const match = m.regex.exec(remaining);
    if (match) {
      positions.push({ key: m.key, index: match.index });
    }
  }
  positions.sort((a, b) => a.index - b.index);

  // Text before first marker is general
  if (positions.length > 0 && positions[0].index > 0) {
    general = remaining.slice(0, positions[0].index).trim() || null;
  }

  // Extract each section
  for (let i = 0; i < positions.length; i++) {
    const current = positions[i];
    const markerDef = allMarkers.find((m) => m.key === current.key);
    if (!markerDef) continue;

    const markerMatch = markerDef.regex.exec(remaining);
    if (!markerMatch) continue;

    const startIdx = markerMatch.index + markerMatch[0].length;
    const endIdx = i + 1 < positions.length ? positions[i + 1].index : remaining.length;
    const content = remaining.slice(startIdx, endIdx).trim();

    if (current.key === 'goodAnswer') goodAnswer = content || null;
    if (current.key === 'redFlag') redFlag = content || null;
    if (current.key === 'keyTerms') keyTerms = content || null;
  }

  return { goodAnswer, redFlag, keyTerms, general };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface InterviewTabProps {
  result: AnalysisResult;
}

export function InterviewTab({ result }: InterviewTabProps) {
  const { interview_script } = result;
  const { total_questions, by_strategy } = interview_script;

  // Determine available strategies (from data keys)
  const strategyKeys = Object.keys(by_strategy);

  // Active strategy filter (null = show all)
  const [activeStrategy, setActiveStrategy] = useState<string | null>(null);

  const displayQuestions: Array<{ strategy: string; questions: InterviewQuestion[] }> =
    activeStrategy
      ? [{ strategy: activeStrategy, questions: by_strategy[activeStrategy] ?? [] }]
      : strategyKeys.map((key) => ({ strategy: key, questions: by_strategy[key] }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h3 className="text-lg font-semibold text-[--color-text-primary]">
              면접 스크립트
            </h3>
            <p className="text-sm text-[--color-text-secondary] mt-1">
              총 {total_questions}개 질문 | {strategyKeys.length}개 전략
            </p>
          </div>
          {/* Strategy filter buttons */}
          <div className="flex gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => setActiveStrategy(null)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                activeStrategy === null
                  ? 'bg-gray-800 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              전체
            </button>
            {strategyKeys.map((key) => {
              const meta = STRATEGY_META[key] ?? {
                label: key,
                color: 'text-gray-600',
                bgColor: 'bg-gray-50 border-gray-200',
                description: '',
              };
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setActiveStrategy(key)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    activeStrategy === key
                      ? 'bg-gray-800 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {meta.label} ({(by_strategy[key] ?? []).length})
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Question groups */}
      {displayQuestions.map(({ strategy, questions }) => {
        const meta = STRATEGY_META[strategy] ?? {
          label: strategy,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50 border-gray-200',
          description: '',
        };

        return (
          <div key={strategy} className="space-y-4">
            {/* Strategy group header */}
            <div className={`rounded-xl border p-4 ${meta.bgColor}`}>
              <h4 className={`text-base font-semibold ${meta.color}`}>
                {meta.label}
              </h4>
              {meta.description && (
                <p className="text-sm text-[--color-text-secondary] mt-1">
                  {meta.description}
                </p>
              )}
            </div>

            {/* Question cards */}
            {questions.map((q, idx) => (
              <QuestionCard key={`${strategy}-${idx}`} question={q} index={idx + 1} />
            ))}
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// QuestionCard sub-component
// ---------------------------------------------------------------------------

function QuestionCard({
  question,
  index,
}: {
  question: InterviewQuestion;
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const diffStyle = DIFFICULTY_STYLES[question.difficulty] ?? {
    label: question.difficulty,
    style: 'bg-gray-100 text-gray-600',
  };

  // Parse expected_answer_guide if present
  const rawGuide = (question as Record<string, unknown>).expected_answer_guide as
    | string
    | undefined;
  const parsedGuide = parseAnswerGuide(rawGuide);

  return (
    <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-5">
      {/* Question header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono text-[--color-text-secondary]">
              Q{index}
            </span>
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-semibold ${diffStyle.style}`}
            >
              {diffStyle.label}
            </span>
            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
              {question.category}
            </span>
          </div>
          <p className="text-sm font-medium text-[--color-text-primary] leading-relaxed">
            {question.text}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="shrink-0 text-sm text-blue-500 hover:text-blue-700 transition-colors"
        >
          {expanded ? '접기' : '상세'}
        </button>
      </div>

      {/* Intent (always visible) */}
      <div className="mt-3 pt-3 border-t border-[--color-border-default]">
        <p className="text-xs text-[--color-text-secondary]">
          <span className="font-semibold">질문 의도:</span> {question.intent}
        </p>
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="mt-3 space-y-3">
          {/* Code reference */}
          {question.code_reference && (
            <div className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-[--color-text-secondary] mb-1">
                코드 참조
              </p>
              <code className="text-xs text-gray-700 font-mono break-all">
                {question.code_reference}
              </code>
            </div>
          )}

          {/* Expected Answer Guide (structured) */}
          {parsedGuide && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 mb-1">
                <BookOpen className="w-3.5 h-3.5 text-[--color-text-secondary]" />
                <p className="text-xs font-semibold text-[--color-text-secondary]">
                  예상 답변 가이드
                </p>
              </div>

              {/* General guide (when no markers found or preamble text) */}
              {parsedGuide.general && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-[--color-text-primary] leading-relaxed whitespace-pre-line">
                    {parsedGuide.general}
                  </p>
                </div>
              )}

              {/* Good Answer section */}
              {parsedGuide.goodAnswer && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                    <p className="text-xs font-semibold text-emerald-700">
                      좋은 답변 기준
                    </p>
                  </div>
                  <p className="text-xs text-emerald-900 leading-relaxed whitespace-pre-line">
                    {parsedGuide.goodAnswer}
                  </p>
                </div>
              )}

              {/* Red Flag section */}
              {parsedGuide.redFlag && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <AlertCircle className="w-3.5 h-3.5 text-red-600" />
                    <p className="text-xs font-semibold text-red-700">
                      경고 신호
                    </p>
                  </div>
                  <p className="text-xs text-red-900 leading-relaxed whitespace-pre-line">
                    {parsedGuide.redFlag}
                  </p>
                </div>
              )}

              {/* Key Terms section */}
              {parsedGuide.keyTerms && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <BookOpen className="w-3.5 h-3.5 text-blue-600" />
                    <p className="text-xs font-semibold text-blue-700">
                      핵심 용어
                    </p>
                  </div>
                  <p className="text-xs text-blue-900 leading-relaxed whitespace-pre-line">
                    {parsedGuide.keyTerms}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Checklist */}
          {question.checklist && question.checklist.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-[--color-text-secondary] mb-1">
                확인 체크리스트
              </p>
              <ul className="space-y-1">
                {question.checklist.map((item, i) => (
                  <li
                    key={i}
                    className="text-xs text-[--color-text-primary] flex items-start gap-2"
                  >
                    <span className="text-gray-400 mt-px shrink-0">&#9744;</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Follow-up questions */}
          {question.follow_up && question.follow_up.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-[--color-text-secondary] mb-1">
                추가 질문
              </p>
              <ul className="space-y-1">
                {question.follow_up.map((fu, i) => (
                  <li
                    key={i}
                    className="text-xs text-blue-600 flex items-start gap-2"
                  >
                    <span className="text-blue-400 mt-px shrink-0">&rarr;</span>
                    <span>{fu}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
