export interface ScoreInterpretationProps {
  label: string;
  score: number;
  interpretation: string;
  maxScore?: number;
}

function getBarColor(pct: number): string {
  if (pct >= 0.7) return 'bg-emerald-500';
  if (pct >= 0.4) return 'bg-yellow-500';
  return 'bg-red-500';
}

export function ScoreInterpretation({
  label,
  score,
  interpretation,
  maxScore = 100,
}: ScoreInterpretationProps) {
  const clampedScore = Math.max(0, Math.min(maxScore, score));
  const pct = maxScore > 0 ? clampedScore / maxScore : 0;
  const barColor = getBarColor(pct);

  return (
    <div className="space-y-1.5">
      {/* Label + Score */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-[--color-text-primary]">
          {label}
        </span>
        <span className="text-sm font-bold text-[--color-text-primary]">
          {clampedScore}
          <span className="text-xs font-normal text-[--color-text-tertiary]">
            /{maxScore}
          </span>
        </span>
      </div>

      {/* Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${barColor}`}
          style={{ width: `${pct * 100}%` }}
        />
      </div>

      {/* Interpretation */}
      <p className="text-xs text-[--color-text-secondary] leading-relaxed">
        {interpretation}
      </p>
    </div>
  );
}
