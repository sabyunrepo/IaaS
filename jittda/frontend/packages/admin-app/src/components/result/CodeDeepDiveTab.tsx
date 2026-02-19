import {
  ComplexityTreemap,
  AICodeHeatmap,
  AuthenticityGauge,
} from '../charts';
import type { TreemapNode } from '../charts';
import type { HeatmapCell } from '../charts';
import type { AnalysisResult } from '../../types/result';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildTreemapData(result: AnalysisResult): TreemapNode[] {
  const fileDetails = result.deep_analysis.logic.file_details;
  if (fileDetails && fileDetails.length > 0) {
    return fileDetails.map((f) => ({
      name: f.name,
      size: f.size,
      maintainability: f.maintainability,
    }));
  }
  // Fallback: generate a single node from aggregate stats
  return [
    {
      name: '전체 평균',
      size: Math.round(result.deep_analysis.logic.avg_cyclomatic_complexity),
      maintainability: Math.round(
        result.deep_analysis.logic.avg_maintainability_index,
      ),
    },
  ];
}

function buildHeatmapData(result: AnalysisResult): HeatmapCell[] {
  const detection = result.deep_analysis.forensic.ai_detection;
  if (detection.file_details && detection.file_details.length > 0) {
    return detection.file_details.map((f) => ({
      filename: f.filename,
      ai_suspicion: f.ai_suspicion,
    }));
  }
  return [];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface CodeDeepDiveTabProps {
  result: AnalysisResult;
}

export function CodeDeepDiveTab({ result }: CodeDeepDiveTabProps) {
  const { forensic, logic, stack } = result.deep_analysis;
  const treemapData = buildTreemapData(result);
  const heatmapData = buildHeatmapData(result);
  const authenticityAxis = result.intel_brief.four_axes.authenticity;

  return (
    <div className="space-y-6">
      {/* Statistics Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="분석 파일 수" value={forensic.total_files_analyzed} />
        <StatCard
          label="평균 순환 복잡도"
          value={logic.avg_cyclomatic_complexity.toFixed(1)}
        />
        <StatCard
          label="평균 유지보수성"
          value={logic.avg_maintainability_index.toFixed(1)}
        />
        <StatCard
          label="감지된 기술 스택"
          value={stack.total_skills_detected}
        />
      </div>

      {/* Authenticity Gauge */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
        <h3 className="text-lg font-semibold text-[--color-text-primary] mb-4">
          진정성 게이지
        </h3>
        <div className="flex justify-center">
          <AuthenticityGauge
            score={authenticityAxis.score}
            signal={authenticityAxis.signal}
            aiSuspicionPct={result.intel_brief.ai_code_suspicion_pct}
          />
        </div>
      </div>

      {/* Complexity Treemap */}
      {treemapData.length > 0 && (
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
          <h3 className="text-lg font-semibold text-[--color-text-primary] mb-4">
            복잡도 트리맵
          </h3>
          <p className="text-sm text-[--color-text-secondary] mb-3">
            파일별 복잡도(크기)와 유지보수성(색상)을 시각화합니다.
            녹색일수록 유지보수성이 높고, 빨간색일수록 낮습니다.
          </p>
          <ComplexityTreemap data={treemapData} width={700} height={350} />
        </div>
      )}

      {/* AI Code Heatmap */}
      {heatmapData.length > 0 && (
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
          <h3 className="text-lg font-semibold text-[--color-text-primary] mb-4">
            AI 코드 히트맵
          </h3>
          <p className="text-sm text-[--color-text-secondary] mb-3">
            파일별 AI 코드 의심률을 시각화합니다. 파란색은 인간 작성 코드,
            빨간색은 AI 생성 의심 코드입니다.
          </p>
          <AICodeHeatmap data={heatmapData} width={700} height={300} />
        </div>
      )}

      {/* Summaries */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {logic.logic_summary && (
          <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
            <h3 className="text-base font-semibold text-[--color-text-primary] mb-2">
              논리 분석 요약
            </h3>
            <p className="text-sm text-[--color-text-secondary] leading-relaxed">
              {logic.logic_summary}
            </p>
          </div>
        )}
        {stack.stack_summary && (
          <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
            <h3 className="text-base font-semibold text-[--color-text-primary] mb-2">
              기술 스택 요약
            </h3>
            <p className="text-sm text-[--color-text-secondary] leading-relaxed">
              {stack.stack_summary}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-4 text-center">
      <p className="text-sm text-[--color-text-secondary] mb-1">{label}</p>
      <p className="text-2xl font-bold text-[--color-text-primary]">{value}</p>
    </div>
  );
}
