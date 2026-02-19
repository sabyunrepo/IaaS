import { Routes, Route } from 'react-router-dom'

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
      <Route path="/careers/:slug" element={<PlaceholderPage name="커리어 페이지" />} />
      <Route path="/careers/:slug/:jobId" element={<PlaceholderPage name="공고 상세" />} />
      <Route path="/careers/:slug/:jobId/apply" element={<PlaceholderPage name="지원 폼" />} />
      <Route path="/apply/confirm" element={<PlaceholderPage name="지원 확인" />} />
    </Routes>
  )
}
