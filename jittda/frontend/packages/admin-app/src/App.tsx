import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { AppLayout } from './components/layout/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { AuthCallbackPage } from './pages/AuthCallbackPage'
import { DashboardPage } from './pages/DashboardPage'
import { JobListPage } from './pages/JobListPage'
import { JobCreatePage } from './pages/JobCreatePage'
import { JobDetailPage } from './pages/JobDetailPage'
import { SettingsPage } from './pages/SettingsPage'
import { ResultPage } from './pages/ResultPage'

function PlaceholderPage({ name }: { name: string }) {
  return (
    <div className="p-8 flex items-center justify-center">
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-8 text-center">
        <h1 className="text-2xl font-semibold text-[--color-text-primary]">{name}</h1>
        <p className="text-[--color-text-secondary] mt-2">다음 Phase에서 구현됩니다.</p>
      </div>
    </div>
  )
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
        <p className="text-[--color-text-secondary]">로딩 중...</p>
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />

      {/* Protected routes with layout */}
      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/jobs" element={<JobListPage />} />
        <Route path="/jobs/new" element={<JobCreatePage />} />
        <Route path="/jobs/:jobId" element={<JobDetailPage />} />
        <Route path="/jobs/:jobId/candidates" element={<PlaceholderPage name="지원자 목록" />} />
        <Route
          path="/jobs/:jobId/candidates/:candidateId"
          element={<PlaceholderPage name="지원자 상세" />}
        />
        <Route
          path="/jobs/:jobId/candidates/:candidateId/analysis"
          element={<ResultPage />}
        />
        <Route
          path="/jobs/:jobId/candidates/:candidateId/interview"
          element={<PlaceholderPage name="면접 스크립트" />}
        />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/settings/company" element={<PlaceholderPage name="회사 설정" />} />
      </Route>
    </Routes>
  )
}
