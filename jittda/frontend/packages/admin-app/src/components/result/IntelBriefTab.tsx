import { AuthenticityGauge, SkillHeatmap, CommitTimeline } from '../charts';
import type { SkillHeatmapItem } from '../charts';
import type { CommitTimelineEntry } from '../charts';
import type { AnalysisResult } from '../../types/result';
import { User, ShieldCheck, GitCommit, Briefcase } from 'lucide-react';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Extract skill data from deep_analysis.stack for the SkillHeatmap.
 * Falls back to an empty array if the data is unavailable.
 */
function extractSkills(result: AnalysisResult): SkillHeatmapItem[] {
  const stack = result.deep_analysis?.stack;
  if (!stack) return [];

  // If the backend provides a skills_detail array, use it
  const raw = (result as Record<string, unknown>).intel_brief as Record<string, unknown> | undefined;
  const skillsDetail = (raw?.skills_detail ?? []) as Array<{
    name: string;
    level: number;
    jd_match?: boolean;
  }>;

  if (skillsDetail.length > 0) {
    return skillsDetail.map((s) => ({
      name: s.name,
      level: s.level,
      jd_match: s.jd_match,
    }));
  }

  // Fallback: generate from stack analysis total count
  return [];
}

/**
 * Extract commit timeline data from deep_analysis.
 * Falls back to an empty array if unavailable.
 */
function extractCommitTimeline(result: AnalysisResult): CommitTimelineEntry[] {
  const raw = result as Record<string, unknown>;
  const deepAnalysis = raw.deep_analysis as Record<string, unknown> | undefined;
  const commitData = (deepAnalysis?.commit_timeline ?? []) as Array<{
    date: string;
    count: number;
    ai_suspected?: boolean;
  }>;

  return commitData.map((c) => ({
    date: c.date,
    count: c.count,
    ai_suspected: c.ai_suspected,
  }));
}

/**
 * Extract career timeline from intel_brief (LinkedIn data).
 */
interface CareerEntry {
  company: string;
  title: string;
  period: string;
  current?: boolean;
}

function extractCareerTimeline(result: AnalysisResult): CareerEntry[] {
  const raw = result as Record<string, unknown>;
  const intelBrief = raw.intel_brief as Record<string, unknown> | undefined;
  const careers = (intelBrief?.career_timeline ?? []) as CareerEntry[];
  return careers;
}

/**
 * Extract candidate profile summary from intel_brief.
 */
interface CandidateProfile {
  name?: string;
  github_username?: string;
  linkedin_url?: string;
  primary_languages?: string[];
  total_repos?: number;
  total_commits?: number;
  summary?: string;
}

function extractProfile(result: AnalysisResult): CandidateProfile {
  const raw = result as Record<string, unknown>;
  const intelBrief = raw.intel_brief as Record<string, unknown> | undefined;
  const profile = (intelBrief?.candidate_profile ?? {}) as CandidateProfile;
  return profile;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface IntelBriefTabProps {
  result: AnalysisResult;
}

export function IntelBriefTab({ result }: IntelBriefTabProps) {
  const authenticityAxis = result.intel_brief.four_axes.authenticity;
  const skills = extractSkills(result);
  const commits = extractCommitTimeline(result);
  const careers = extractCareerTimeline(result);
  const profile = extractProfile(result);

  return (
    <div className="space-y-6">
      {/* Candidate Profile Summary */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <User className="w-5 h-5 text-blue-500" />
          <h3 className="text-lg font-semibold text-[--color-text-primary]">
            후보자 프로필
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            {profile.name && (
              <ProfileRow label="이름" value={profile.name} />
            )}
            {profile.github_username && (
              <ProfileRow label="GitHub" value={profile.github_username} />
            )}
            {profile.linkedin_url && (
              <ProfileRow label="LinkedIn" value={profile.linkedin_url} isLink />
            )}
          </div>
          <div className="space-y-2">
            {profile.primary_languages && profile.primary_languages.length > 0 && (
              <div>
                <span className="text-xs font-semibold text-[--color-text-secondary]">
                  주요 언어
                </span>
                <div className="flex gap-1.5 mt-1 flex-wrap">
                  {profile.primary_languages.map((lang) => (
                    <span
                      key={lang}
                      className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs font-medium"
                    >
                      {lang}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {profile.total_repos != null && (
              <ProfileRow
                label="리포지토리"
                value={`${profile.total_repos}개`}
              />
            )}
            {profile.total_commits != null && (
              <ProfileRow
                label="총 커밋"
                value={`${profile.total_commits.toLocaleString()}회`}
              />
            )}
          </div>
        </div>

        {profile.summary && (
          <p className="text-sm text-[--color-text-secondary] mt-4 leading-relaxed border-t border-[--color-border-default] pt-3">
            {profile.summary}
          </p>
        )}
      </div>

      {/* Authenticity Verification */}
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <ShieldCheck className="w-5 h-5 text-emerald-500" />
          <h3 className="text-lg font-semibold text-[--color-text-primary]">
            진정성 검증
          </h3>
        </div>
        <div className="flex justify-center">
          <AuthenticityGauge
            score={authenticityAxis.score}
            signal={authenticityAxis.signal}
            aiSuspicionPct={result.intel_brief.ai_code_suspicion_pct}
          />
        </div>
        <p className="text-sm text-[--color-text-secondary] text-center mt-2">
          코드 분석 기반 진정성 점수와 AI 작성 코드 의심률을 종합 평가합니다.
        </p>
      </div>

      {/* Skill Heatmap */}
      {skills.length > 0 && (
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
          <h3 className="text-lg font-semibold text-[--color-text-primary] mb-2">
            기술 역량 히트맵
          </h3>
          <p className="text-sm text-[--color-text-secondary] mb-4">
            감지된 기술 스택의 숙련도를 시각화합니다. JD 매칭 스킬은 녹색으로 강조됩니다.
          </p>
          <SkillHeatmap skills={skills} width={600} height={280} />
        </div>
      )}

      {/* Commit Timeline */}
      {commits.length > 0 && (
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
          <div className="flex items-center gap-2 mb-2">
            <GitCommit className="w-5 h-5 text-blue-500" />
            <h3 className="text-lg font-semibold text-[--color-text-primary]">
              커밋 타임라인
            </h3>
          </div>
          <p className="text-sm text-[--color-text-secondary] mb-4">
            기간별 커밋 빈도를 보여줍니다. 빨간색 점은 AI 생성 의심 커밋입니다.
          </p>
          <CommitTimeline commits={commits} width={700} height={200} />
        </div>
      )}

      {/* Career Timeline */}
      {careers.length > 0 && (
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-6">
          <div className="flex items-center gap-2 mb-4">
            <Briefcase className="w-5 h-5 text-purple-500" />
            <h3 className="text-lg font-semibold text-[--color-text-primary]">
              경력 타임라인
            </h3>
          </div>
          <p className="text-sm text-[--color-text-secondary] mb-4">
            LinkedIn 기반 경력 이력입니다.
          </p>
          <div className="relative pl-6 border-l-2 border-gray-200 space-y-4">
            {careers.map((entry, i) => (
              <div key={i} className="relative">
                {/* Timeline dot */}
                <div
                  className={`absolute -left-[25px] top-1 w-3 h-3 rounded-full border-2 ${
                    entry.current
                      ? 'bg-blue-500 border-blue-500'
                      : 'bg-white border-gray-400'
                  }`}
                />
                <div>
                  <p className="text-sm font-semibold text-[--color-text-primary]">
                    {entry.title}
                  </p>
                  <p className="text-sm text-[--color-text-secondary]">
                    {entry.company}
                  </p>
                  <p className="text-xs text-[--color-text-tertiary] mt-0.5">
                    {entry.period}
                    {entry.current && (
                      <span className="ml-2 px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded text-xs font-medium">
                        현재
                      </span>
                    )}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-component
// ---------------------------------------------------------------------------

function ProfileRow({
  label,
  value,
  isLink,
}: {
  label: string;
  value: string;
  isLink?: boolean;
}) {
  return (
    <div>
      <span className="text-xs font-semibold text-[--color-text-secondary]">
        {label}
      </span>
      {isLink ? (
        <a
          href={value}
          target="_blank"
          rel="noopener noreferrer"
          className="block text-sm text-blue-600 hover:underline truncate"
        >
          {value}
        </a>
      ) : (
        <p className="text-sm text-[--color-text-primary]">{value}</p>
      )}
    </div>
  );
}
