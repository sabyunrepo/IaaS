/**
 * Analysis result types returned by the backend OutputAssembler.
 *
 * Corresponds to GET /api/jobs/{jobId}/result response body.
 */

export type Signal = 'green' | 'yellow' | 'red';

export interface AxisScore {
  score: number;
  signal: Signal;
}

export interface FourAxes {
  logic: AxisScore;
  mastery: AxisScore;
  stability: AxisScore;
  authenticity: AxisScore;
}

// ---------------------------------------------------------------------------
// Intel Brief (Overview tab)
// ---------------------------------------------------------------------------

export interface IntelBrief {
  grade: string;
  weighted_total: number;
  confidence: string;
  four_axes: FourAxes;
  ai_code_suspicion_pct: number;
}

// ---------------------------------------------------------------------------
// Deep Analysis (Code Deep Dive tab)
// ---------------------------------------------------------------------------

export interface AIDetection {
  total_files: number;
  suspected_ai_files: number;
  overall_suspicion_pct: number;
  file_details: Array<{
    filename: string;
    ai_suspicion: number;
  }>;
}

export interface StyleConsistency {
  score: number;
  details: string | null;
}

export interface Plagiarism {
  score: number;
  details: string | null;
}

export interface ForensicAnalysis {
  total_files_analyzed: number;
  ai_detection: AIDetection;
  style_consistency: StyleConsistency;
  plagiarism: Plagiarism;
}

export interface LogicAnalysis {
  files_analyzed: number;
  avg_cyclomatic_complexity: number;
  avg_maintainability_index: number;
  logic_summary: string | null;
  file_details?: Array<{
    name: string;
    size: number;
    maintainability: number;
  }>;
}

export interface StackAnalysis {
  total_skills_detected: number;
  avg_api_depth: number;
  architecture_score: { score: number; details: string | null } | null;
  stack_summary: string | null;
}

export interface DeepAnalysis {
  forensic: ForensicAnalysis;
  logic: LogicAnalysis;
  stack: StackAnalysis;
}

// ---------------------------------------------------------------------------
// Interview Script (Interview tab)
// ---------------------------------------------------------------------------

export interface InterviewQuestion {
  text: string;
  intent: string;
  strategy: string;
  category: string;
  difficulty: string;
  checklist?: string[];
  follow_up?: string[];
  code_reference?: string;
}

export interface InterviewScript {
  total_questions: number;
  questions: InterviewQuestion[];
  by_strategy: Record<string, InterviewQuestion[]>;
  by_category: Record<string, InterviewQuestion[]>;
}

// ---------------------------------------------------------------------------
// Decision Support
// ---------------------------------------------------------------------------

export type Recommendation = 'hire' | 'conditional_hire' | 'no_hire';

export interface DecisionSupport {
  recommendation: Recommendation;
  recommendation_reason: string;
  strengths: string[];
  concerns: string[];
  risk_factors: string[];
  confidence: string;
}

// ---------------------------------------------------------------------------
// Root analysis result
// ---------------------------------------------------------------------------

export interface AnalysisResult {
  job_id: string;
  version: string;
  intel_brief: IntelBrief;
  deep_analysis: DeepAnalysis;
  interview_script: InterviewScript;
  decision_support: DecisionSupport;
  status: string;
}
