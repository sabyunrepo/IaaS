import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { AppLayout } from './components/layout/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { AuthCallbackPage } from './pages/AuthCallbackPage'
import { DashboardPage } from './pages/DashboardPage'
import { PostingListPage } from './pages/PostingListPage'
import { PostingCreatePage } from './pages/PostingCreatePage'
import { PostingDetailPage } from './pages/PostingDetailPage'
import { ApplicationDetailPage } from './pages/ApplicationDetailPage'
import { SettingsPage } from './pages/SettingsPage'
import { ResultPage } from './pages/ResultPage'

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

      {/* Legacy redirects */}
      <Route path="/jobs" element={<Navigate to="/postings" replace />} />
      <Route path="/jobs/new" element={<Navigate to="/postings/new" replace />} />

      {/* Protected routes with layout */}
      <Route
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/postings" element={<PostingListPage />} />
        <Route path="/postings/new" element={<PostingCreatePage />} />
        <Route path="/postings/:postingId" element={<PostingDetailPage />} />
        <Route
          path="/postings/:postingId/applications/:appId"
          element={<ApplicationDetailPage />}
        />
        <Route
          path="/postings/:postingId/applications/:appId/result"
          element={<ResultPage />}
        />
        {/* Legacy result route */}
        <Route
          path="/jobs/:jobId/candidates/:candidateId/analysis"
          element={<ResultPage />}
        />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}
