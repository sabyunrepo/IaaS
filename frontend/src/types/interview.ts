/**
 * Interview Script v2 TypeScript Interfaces
 *
 * Comprehensive type definitions for the 4-tab interview UI:
 * - Intel Brief: JD analysis, competency matching, GitHub/LinkedIn data
 * - Deep Analysis: Radar charts, engineering DNA, skill matching
 * - Live Interview: Questions with scenarios and follow-ups
 * - Decision: JD competency achievement and hiring recommendation
 */

// =============================================================================
// INTEL BRIEF TAB
// =============================================================================

/** JD requirement with match status */
export interface RequirementMatch {
  text: string
  desc: string
  matched: boolean
}

/** JD summary for Intel Brief */
export interface JDSummary {
  title: string
  subtitle: string
  requirements: RequirementMatch[]
  success_metrics: string[]
}

/** Competency match levels */
export type CompetencyMatchLevel = 'strong' | 'match' | 'partial' | 'unknown' | 'none'

/** JD competency vs candidate matching */
export interface CompetencyMatch {
  name: string
  match: CompetencyMatchLevel
  match_label: string
  desc: string
  why: string
  color: 'emerald' | 'amber' | 'red' | 'gray'
  icon: string
}

/** GitHub contribution summary */
export interface GitHubSummary {
  contributions: number
  repos: number
  main_languages: string
  tech_match: string
  tech_match_note?: string
  tenure_pattern: string
  tenure_note?: string
  activity_gap?: string
  chart_data: number[]
}

/** LinkedIn position entry */
export interface LinkedInPosition {
  initial: string
  title: string
  company: string
  detail: string
}

/** Intel Brief tab data */
export interface IntelBrief {
  jd_summary: JDSummary
  jd_full?: string
  competencies: CompetencyMatch[]
  github?: GitHubSummary
  linkedin?: LinkedInPosition[]
  linkedin_warning?: string
}

// =============================================================================
// DEEP ANALYSIS TAB
// =============================================================================

/** Engineering DNA item for progress bars */
export interface EngineeringDNAItem {
  label: string
  value: number
  display: string
  color: 'emerald' | 'blue' | 'amber' | 'red' | 'gray'
  note?: string
  tooltip?: string
}

/** Risk flag identified in analysis */
export interface RiskFlag {
  label: string
  detail: string
}

/** Skill matching types */
export type SkillMatchType = 'exact' | 'similar' | 'partial' | 'none'

/** Skill match row for table */
export interface SkillMatchRow {
  skill: string
  candidate: string
  type: SkillMatchType
  evidence: string
  confidence: number
}

/** Deep Analysis tab data */
export interface DeepAnalysis {
  radar_candidate: number[]
  radar_required: number[]
  engineering_dna: EngineeringDNAItem[]
  risk_flags: RiskFlag[]
  skill_table: SkillMatchRow[]
  overall_match?: number
}

// =============================================================================
// LIVE INTERVIEW TAB - QUESTIONS
// =============================================================================

/** Answer keyword with importance */
export interface AnswerKeyword {
  keyword: string
  importance: 'must' | 'good_to_have'
  explanation: string
}

/** Scenario level (v2 structure) */
export type ScenarioLevelType = 'Expert' | 'Mid' | 'Low'

export interface ScenarioLevel {
  level: ScenarioLevelType
  score: number
  text: string
  depth_expectations: string
}

/** Follow-up response (good/poor) */
export interface FollowUpResponse {
  text: string
  score: number
}

/** Follow-up question trigger */
export type FollowUpTrigger = 'Expert' | 'Mid' | 'Low' | 'any'

/** Follow-up question (v2 structure) */
export interface FollowUpQuestion {
  id: string
  trigger: FollowUpTrigger
  question_text: string
  why_matters: string
  listen_for: string
  good: FollowUpResponse
  poor: FollowUpResponse
}

/** Terminology entry */
export interface TerminologyEntry {
  term: string
  definition?: string
  plain_language_explanation?: string
  business_context?: string
}

/** Interviewer note with business interpretation */
export interface InterviewerNote {
  business_interpretation: string
  daily_analogy: string
  level_expectation: string
}

/** Interview Question (v2 structure) */
export interface InterviewQuestion {
  id: string
  title: string
  category: string
  difficulty: 'Easy' | 'Medium' | 'Hard'
  question_text: string
  why_matters: string
  listen_for: string

  // v2 structure
  answer_keywords: AnswerKeyword[]
  scenarios: ScenarioLevel[]
  follow_ups: FollowUpQuestion[]

  // Optional fields
  terminology?: TerminologyEntry[]
  interviewer_note?: InterviewerNote
  is_risk?: boolean
  time_allocation_minutes?: number
  code_reference?: {
    file?: string
    lines?: string
    snippet?: string
  }

  // Legacy v1 fields (for backward compatibility)
  evaluation_scenarios?: {
    expert?: Record<string, unknown>
    mid?: Record<string, unknown>
    low?: Record<string, unknown>
  }
  follow_up_questions?: Array<Record<string, unknown>>

  // Finalization output fields
  revised_question?: string
  original_question?: string
  revision_type?: string
  revision_rationale?: string
  new_confidence_score?: number
  new_evidence_reference?: string
  original_index?: number
}

// =============================================================================
// DECISION TAB
// =============================================================================

/** Resume-based tip */
export interface ResumeTip {
  section: string
  insight: string
  question_link?: string
}

/** Cover letter insight */
export interface CoverLetterInsight {
  highlight: string
  interpretation: string
  follow_up_opportunity?: string
}

/** Decision summary */
export interface DecisionSummary {
  experience: string
  jd_match: string
  level: string
  strengths: string[]
  concerns: string[]
}

/** Interviewer guide tips */
export interface InterviewerGuideTips {
  interview_flow: string
  time_allocation: Record<string, string>
  resume_based_tips: ResumeTip[]
  cover_letter_insights: CoverLetterInsight[]
  red_flags_to_watch: string[]
  positive_signals: string[]
}

/** JD competency weight */
export interface JDCompetencyWeight {
  competency: string
  weight: number
  related_questions: number[]
}

/** Decision Support tab data */
export interface DecisionSupport {
  summary: DecisionSummary
  interviewer_guide: InterviewerGuideTips
  jd_competency_map: JDCompetencyWeight[]
}

// =============================================================================
// CANDIDATE INFO
// =============================================================================

/** Candidate basic info */
export interface Candidate {
  name: string
  initials?: string
  role?: string
  company_context?: string
  experience?: string
  jd_match?: string
  level?: string
  current_title?: string
}

// =============================================================================
// MAIN INTERVIEW SCRIPT
// =============================================================================

/** Category weights for scoring */
export type CategoryWeights = Record<string, number>

/** Candidate summary (legacy structure) */
export interface CandidateSummary {
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

/** Interviewer guide (legacy structure) */
export interface InterviewerGuide {
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

/** LinkedIn profile (legacy structure) */
export interface LinkedInProfile {
  name?: string
  headline?: string
  current_company?: string
  profile_url?: string
  projects?: Array<{ title: string; description?: string }>
  honors_and_awards?: Array<{ title: string; issuer?: string; description?: string }>
}

/** Interview script metadata */
export interface InterviewScriptMetadata {
  language?: string
  total_questions?: number
  experience_level?: string
  has_linkedin_data?: boolean
}

/** Complete Interview Script (v2) */
export interface InterviewScript {
  // Core fields
  job_id?: string
  generated_at?: string
  output_language?: string

  // Questions
  questions: InterviewQuestion[]

  // v2 new fields
  candidate?: Candidate
  intel?: IntelBrief
  analysis?: DeepAnalysis
  decision?: DecisionSupport
  category_weights?: CategoryWeights

  // Legacy fields (v1 compatibility)
  metadata?: InterviewScriptMetadata
  candidate_summary?: CandidateSummary
  interviewer_guide?: InterviewerGuide
  decision_guide?: Record<string, unknown>
  full_glossary?: TerminologyEntry[]
  linkedin_profile?: LinkedInProfile
}

// =============================================================================
// SCORING STATE FOR LIVE INTERVIEW
// =============================================================================

/** Score state for a single question */
export interface QuestionScoreState {
  selectedLevel?: ScenarioLevelType
  followUpScores: Record<string, number>
  totalScore: number
  maxPossibleScore: number
}

/** All scores state */
export type ScoresState = Record<string, QuestionScoreState>

// =============================================================================
// TAB TYPES
// =============================================================================

/** Available tabs in the result page */
export type ResultTab = 'intel' | 'analysis' | 'interview' | 'decision'

/** Interview phase in Live Interview tab */
export type InterviewPhase = 'select' | 'interview'
