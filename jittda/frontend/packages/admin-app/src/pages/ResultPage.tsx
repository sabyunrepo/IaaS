import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAnalysisResult } from '../hooks/useAnalysisResult';
import { OverviewTab, CodeDeepDiveTab, InterviewTab } from '../components/result';

// ---------------------------------------------------------------------------
// Tab definitions
// ---------------------------------------------------------------------------

type TabId = 'overview' | 'code' | 'interview';

interface TabDef {
  id: TabId;
  label: string;
}

const TABS: TabDef[] = [
  { id: 'overview', label: '개요' },
  { id: 'code', label: '코드 심층 분석' },
  { id: 'interview', label: '면접 스크립트' },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ResultPage() {
  const { jobId, candidateId } = useParams<{
    jobId: string;
    candidateId: string;
  }>();
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const { data, isLoading, error, refetch } = useAnalysisResult(jobId ?? '');

  // -- Loading state --------------------------------------------------------

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-8 text-center">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-[--color-text-secondary]">분석 결과를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  // -- Error state ----------------------------------------------------------

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
        <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-8 text-center max-w-md">
          <p className="text-red-500 text-lg font-semibold mb-2">오류 발생</p>
          <p className="text-[--color-text-secondary] mb-4">
            {error ?? '분석 결과를 찾을 수 없습니다.'}
          </p>
          <button
            type="button"
            onClick={refetch}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  // -- Render ---------------------------------------------------------------

  return (
    <div className="min-h-screen bg-[--color-bg-primary]">
      {/* Header */}
      <header className="bg-[--color-bg-surface] border-b border-[--color-border-default] shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-[--color-text-primary]">
                분석 결과
              </h1>
              <p className="text-sm text-[--color-text-secondary] mt-1">
                Job: {jobId}
                {candidateId && <> | 지원자: {candidateId}</>}
                {' | '}등급: {data.intel_brief.grade} | 버전: {data.version}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  data.status === 'completed'
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-yellow-100 text-yellow-700'
                }`}
              >
                {data.status === 'completed' ? '완료' : data.status}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav className="bg-[--color-bg-surface] border-b border-[--color-border-default]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-0 -mb-px">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`px-5 py-3 text-sm font-medium transition-colors border-b-2 ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-[--color-text-secondary] hover:text-[--color-text-primary] hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Tab Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'overview' && <OverviewTab result={data} />}
        {activeTab === 'code' && <CodeDeepDiveTab result={data} />}
        {activeTab === 'interview' && <InterviewTab result={data} />}
      </main>
    </div>
  );
}
