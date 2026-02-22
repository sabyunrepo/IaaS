import { ScoreInterpretation } from '../ux/ScoreInterpretation';
import type { AnalysisResult, Recommendation, Signal } from '../../types/result';
import {
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  Shield,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Display mappings
// ---------------------------------------------------------------------------

const RECOMMENDATION_DISPLAY: Record<
  Recommendation,
  { bg: string; text: string; border: string; label: string; icon: typeof ThumbsUp }
> = {
  hire: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-300',
    label: '채용 추천',
    icon: ThumbsUp,
  },
  conditional_hire: {
    bg: 'bg-yellow-50',
    text: 'text-yellow-700',
    border: 'border-yellow-300',
    label: '조건부 채용',
    icon: AlertTriangle,
  },
  no_hire: {
    bg: 'bg-red-50',
    text: 'text-red-700',
    border: 'border-red-300',
    label: '채용 비추천',
    icon: ThumbsDown,
  },
};

const AXIS_META: Record<
  string,
  { label: string; icon: typeof Shield }
> = {
  logic: { label: '논리력', icon: Shield },
  mastery: { label: '전문성', icon: TrendingUp },
  stability: { label: '안정성', icon: Shield },
  authenticity: { label: '진정성', icon: Shield },
};

const SIGNAL_INTERPRETATION: Record<Signal, string> = {
  green: '우수한 수준입니다.',
  yellow: '보통 수준이며, 추가 확인이 필요합니다.',
  red: '부족한 수준으로, 주의가 필요합니다.',
};

const CONFIDENCE_MAP: Record<string, { label: string; style: string }> = {
  high: { label: '높음', style: 'bg-emerald-100 text-emerald-700' },
  medium: { label: '보통', style: 'bg-yellow-100 text-yellow-700' },
  low: { label: '낮음', style: 'bg-red-100 text-red-700' },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface DecisionTabProps {
  result: AnalysisResult;
}

export function DecisionTab({ result }: DecisionTabProps) {
  const { decision_support, intel_brief } = result;
  const {
    recommendation,
    recommendation_reason,
    strengths,
    concerns,
    risk_factors,
    confidence,
  } = decision_support;
  const { four_axes } = intel_brief;
  const rec = RECOMMENDATION_DISPLAY[recommendation];
  const RecIcon = rec.icon;
  const confidenceInfo = CONFIDENCE_MAP[confidence] ?? {
    label: confidence,
    style: 'bg-gray-100 text-gray-700',
  };

  return (
    <div className="space-y-6">
      {/* Recommendation Hero */}
      <div
        className={`${rec.bg} border ${rec.border} rounded-xl shadow-card p-8 text-center`}
      >
        <RecIcon className={`w-12 h-12 mx-auto mb-3 ${rec.text}`} />
        <h2 className={`text-3xl font-bold ${rec.text} mb-2`}>{rec.label}</h2>
        <p className="text-sm text-[--color-text-secondary] leading-relaxed max-w-xl mx-auto">
          {recommendation_reason}
        </p>
        <div className="mt-4">
          <span
            className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${confidenceInfo.style}`}
          >
            분석 신뢰도: {confidenceInfo.label}
          </span>
        </div>
      </div>

      {/* 4-Axis Detail with Interpretation */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
        <h3 className="text-lg font-semibold text-[--color-text-primary] mb-4">
          4축 상세 분석
        </h3>
        <div className="space-y-4">
          {(Object.keys(four_axes) as Array<keyof typeof four_axes>).map(
            (axis) => {
              const { score, signal } = four_axes[axis];
              const meta = AXIS_META[axis] ?? { label: axis, icon: Shield };
              const interpretation = SIGNAL_INTERPRETATION[signal];

              return (
                <ScoreInterpretation
                  key={axis}
                  label={meta.label}
                  score={score}
                  interpretation={interpretation}
                  maxScore={100}
                />
              );
            },
          )}
        </div>
      </div>

      {/* Strengths & Concerns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Strengths */}
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-emerald-500" />
            <h3 className="text-base font-semibold text-emerald-600">강점</h3>
          </div>
          {strengths.length > 0 ? (
            <ul className="space-y-2">
              {strengths.map((s, i) => (
                <li
                  key={i}
                  className="text-sm text-[--color-text-primary] flex items-start gap-2"
                >
                  <span className="text-emerald-500 mt-0.5 shrink-0 font-bold">
                    +
                  </span>
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[--color-text-tertiary]">
              분석된 강점이 없습니다.
            </p>
          )}
        </div>

        {/* Concerns */}
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingDown className="w-4 h-4 text-red-500" />
            <h3 className="text-base font-semibold text-red-600">우려 사항</h3>
          </div>
          {concerns.length > 0 ? (
            <ul className="space-y-2">
              {concerns.map((c, i) => (
                <li
                  key={i}
                  className="text-sm text-[--color-text-primary] flex items-start gap-2"
                >
                  <span className="text-red-500 mt-0.5 shrink-0 font-bold">
                    -
                  </span>
                  <span>{c}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[--color-text-tertiary]">
              우려 사항이 없습니다.
            </p>
          )}
        </div>
      </div>

      {/* Risk Factors */}
      {risk_factors.length > 0 && (
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-yellow-500" />
            <h3 className="text-base font-semibold text-yellow-600">
              리스크 요인
            </h3>
          </div>
          <ul className="space-y-2">
            {risk_factors.map((r, i) => (
              <li
                key={i}
                className="text-sm text-[--color-text-primary] flex items-start gap-2"
              >
                <span className="text-yellow-500 mt-0.5 shrink-0 font-bold">
                  !
                </span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Final Judgment Rationale */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
        <h3 className="text-lg font-semibold text-[--color-text-primary] mb-3">
          최종 판단 근거
        </h3>
        <p className="text-sm text-[--color-text-secondary] leading-relaxed">
          {recommendation_reason}
        </p>

        <div className="mt-4 pt-4 border-t border-[--color-border-default]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-[--color-text-secondary]">
                종합 등급:
              </span>
              <span className="text-lg font-bold text-[--color-text-primary]">
                {intel_brief.grade}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-[--color-text-secondary]">
                가중 점수:
              </span>
              <span className="text-lg font-bold text-[--color-text-primary]">
                {intel_brief.weighted_total.toFixed(1)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-[--color-text-secondary]">
                신뢰도:
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-semibold ${confidenceInfo.style}`}
              >
                {confidenceInfo.label}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
