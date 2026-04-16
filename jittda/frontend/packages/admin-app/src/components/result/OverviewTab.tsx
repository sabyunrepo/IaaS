import { FourAxisRadar } from '../charts';
import type {
  AnalysisResult,
  Signal,
  Recommendation,
} from '../../types/result';
import { Sparkles } from 'lucide-react';

// ---------------------------------------------------------------------------
// Signal badge mapping
// ---------------------------------------------------------------------------

const SIGNAL_STYLES: Record<Signal, { bg: string; text: string; label: string }> = {
  green: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: '양호' },
  yellow: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: '주의' },
  red: { bg: 'bg-red-100', text: 'text-red-700', label: '위험' },
};

const AXIS_LABELS: Record<string, string> = {
  logic: '논리력',
  mastery: '전문성',
  stability: '안정성',
  authenticity: '진정성',
};

const RECOMMENDATION_MAP: Record<
  Recommendation,
  { bg: string; text: string; label: string }
> = {
  hire: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: '채용 추천' },
  conditional_hire: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-700',
    label: '조건부 채용',
  },
  no_hire: { bg: 'bg-red-100', text: 'text-red-700', label: '채용 비추천' },
};

const CONFIDENCE_MAP: Record<string, string> = {
  high: '높음',
  medium: '보통',
  low: '낮음',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface OverviewTabProps {
  result: AnalysisResult;
}

export function OverviewTab({ result }: OverviewTabProps) {
  const { intel_brief, decision_support } = result;
  const { grade, weighted_total, confidence, four_axes } = intel_brief;
  const rec = RECOMMENDATION_MAP[decision_support.recommendation];

  return (
    <div className="space-y-6">
      {/* One-line Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl shadow-card p-5">
        <div className="flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-blue-500 mt-0.5 shrink-0" />
          <div>
            <h3 className="text-sm font-semibold text-blue-700 mb-1">
              핵심 한 줄 요약
            </h3>
            <p className="text-sm text-blue-900 leading-relaxed">
              {decision_support.recommendation_reason}
            </p>
          </div>
        </div>
      </div>

      {/* Grade + Summary Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Overall Grade */}
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6 text-center">
          <p className="text-sm text-[--color-text-secondary] mb-1">종합 등급</p>
          <p className="text-5xl font-bold text-[--color-text-primary]">
            {grade}
          </p>
          <p className="text-sm text-[--color-text-secondary] mt-2">
            가중 점수: {weighted_total.toFixed(1)}
          </p>
          <p className="text-xs text-[--color-text-secondary] mt-1">
            신뢰도: {CONFIDENCE_MAP[confidence] ?? confidence}
          </p>
        </div>

        {/* Recommendation */}
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
          <p className="text-sm text-[--color-text-secondary] mb-2">채용 판단</p>
          <span
            className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${rec.bg} ${rec.text}`}
          >
            {rec.label}
          </span>
        </div>

        {/* AI Suspicion */}
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6 text-center">
          <p className="text-sm text-[--color-text-secondary] mb-1">
            AI 코드 의심률
          </p>
          <p className="text-4xl font-bold text-[--color-text-primary]">
            {intel_brief.ai_code_suspicion_pct.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Signal Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {(Object.keys(four_axes) as Array<keyof typeof four_axes>).map(
          (axis) => {
            const { score, signal } = four_axes[axis];
            const style = SIGNAL_STYLES[signal];
            return (
              <div
                key={axis}
                className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-4 text-center"
              >
                <p className="text-sm text-[--color-text-secondary] mb-1">
                  {AXIS_LABELS[axis]}
                </p>
                <p className="text-2xl font-bold text-[--color-text-primary]">
                  {score}
                </p>
                <span
                  className={`inline-block mt-2 px-2 py-0.5 rounded-full text-xs font-semibold ${style.bg} ${style.text}`}
                >
                  {style.label}
                </span>
              </div>
            );
          },
        )}
      </div>

      {/* Radar Chart */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
        <h3 className="text-lg font-semibold text-[--color-text-primary] mb-4">
          4축 레이더
        </h3>
        <div className="flex justify-center">
          <FourAxisRadar data={four_axes} size={320} />
        </div>
      </div>
    </div>
  );
}
