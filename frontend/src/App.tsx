import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useAuth } from './hooks/useAuth'
import './i18n'

// 코드 스플리팅: 페이지별 lazy loading
const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })))
const HomePage = lazy(() => import('./pages/HomePage').then(m => ({ default: m.HomePage })))
const JobListPage = lazy(() => import('./pages/JobListPage').then(m => ({ default: m.JobListPage })))
const CreateJobPage = lazy(() => import('./pages/CreateJobPage').then(m => ({ default: m.CreateJobPage })))
const JobStatusPage = lazy(() => import('./pages/JobStatusPage').then(m => ({ default: m.JobStatusPage })))
const ResultPage = lazy(() => import('./pages/ResultPage').then(m => ({ default: m.ResultPage })))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })))
const AuthCallbackPage = lazy(() => import('./pages/AuthCallbackPage').then(m => ({ default: m.AuthCallbackPage })))
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })))

// 기존 /jobs/:jobId 경로 → /interview/:jobId 리다이렉트
function JobRedirect({ suffix }: { suffix?: string }) {
  const { jobId } = useParams<{ jobId: string }>()
  return <Navigate to={`/interview/${jobId}${suffix || ''}`} replace />
}

function PageLoader() {
  return (
    <div className="min-h-[50vh] flex items-center justify-center">
      <p className="text-gray-500">Loading...</p>
    </div>
  )
}

function App() {
  const { user, loading, logout, isAuthenticated } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[--color-bg-page]">
        <p className="text-[--color-text-tertiary]">Loading...</p>
      </div>
    )
  }

  return (
    <ErrorBoundary>
    <BrowserRouter basename="/demo">
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route element={<Layout user={user} onLogout={logout} />}>
            {/* Public */}
            <Route path="/login" element={isAuthenticated ? <Navigate to="/" /> : <LoginPage />} />
            <Route path="/auth/callback" element={<AuthCallbackPage />} />

            {/* Home */}
            <Route
              path="/"
              element={isAuthenticated ? <HomePage user={user} /> : <Navigate to="/login" />}
            />

            {/* Interview (기존 /jobs → /interview 리네임) */}
            <Route
              path="/interview"
              element={isAuthenticated ? <JobListPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/interview/new"
              element={isAuthenticated ? <CreateJobPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/interview/:jobId"
              element={isAuthenticated ? <JobStatusPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/interview/:jobId/result"
              element={isAuthenticated ? <ResultPage /> : <Navigate to="/login" />}
            />

            {/* 기존 /jobs 경로 호환 리다이렉트 */}
            <Route path="/jobs" element={<Navigate to="/interview" replace />} />
            <Route path="/jobs/new" element={<Navigate to="/interview/new" replace />} />
            <Route path="/jobs/:jobId" element={<JobRedirect />} />
            <Route path="/jobs/:jobId/result" element={<JobRedirect suffix="/result" />} />

            {/* Settings */}
            <Route
              path="/settings"
              element={isAuthenticated ? <SettingsPage /> : <Navigate to="/login" />}
            />

            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App

