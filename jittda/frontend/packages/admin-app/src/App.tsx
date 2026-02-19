import { Routes, Route } from 'react-router-dom'
import { ResultPage } from './pages/ResultPage'

function PlaceholderPage({ name }: { name: string }) {
  return (
    <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-8 text-center">
        <h1 className="text-2xl font-semibold text-[--color-text-primary]">{name}</h1>
        <p className="text-[--color-text-secondary] mt-2">Phase 1에서 구현됩니다.</p>
      </div>
    </div>
  )
}

export function App() {
  return (
    <Routes>
      {/* Auth */}
      <Route path="/login" element={<PlaceholderPage name="로그인" />} />

      {/* Dashboard */}
      <Route path="/" element={<PlaceholderPage name="대시보드" />} />

      {/* Job Management */}
      <Route path="/jobs" element={<PlaceholderPage name="채용 공고 목록" />} />
      <Route path="/jobs/new" element={<PlaceholderPage name="공고 생성" />} />
      <Route path="/jobs/:jobId" element={<PlaceholderPage name="공고 상세" />} />

      {/* Candidate Management */}
      <Route path="/jobs/:jobId/candidates" element={<PlaceholderPage name="지원자 목록" />} />
      <Route path="/jobs/:jobId/candidates/:candidateId" element={<PlaceholderPage name="지원자 상세" />} />

      {/* Analysis Results */}
      <Route path="/jobs/:jobId/candidates/:candidateId/analysis" element={<ResultPage />} />
      <Route path="/jobs/:jobId/candidates/:candidateId/interview" element={<PlaceholderPage name="면접 스크립트" />} />

      {/* Settings */}
      <Route path="/settings" element={<PlaceholderPage name="설정" />} />
      <Route path="/settings/company" element={<PlaceholderPage name="회사 설정" />} />
    </Routes>
  )
}
