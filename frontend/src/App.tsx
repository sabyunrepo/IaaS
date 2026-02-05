import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useAuth } from './hooks/useAuth'
import './i18n'

// 코드 스플리팅: 페이지별 lazy loading
const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })))
const JobListPage = lazy(() => import('./pages/JobListPage').then(m => ({ default: m.JobListPage })))
const CreateJobPage = lazy(() => import('./pages/CreateJobPage').then(m => ({ default: m.CreateJobPage })))
const JobStatusPage = lazy(() => import('./pages/JobStatusPage').then(m => ({ default: m.JobStatusPage })))
const ResultPage = lazy(() => import('./pages/ResultPage').then(m => ({ default: m.ResultPage })))
const AnalysisLogsPage = lazy(() => import('./pages/AnalysisLogsPage').then(m => ({ default: m.AnalysisLogsPage })))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })))
const AuthCallbackPage = lazy(() => import('./pages/AuthCallbackPage').then(m => ({ default: m.AuthCallbackPage })))

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
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500">Loading...</p>
      </div>
    )
  }

  return (
    <ErrorBoundary>
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route element={<Layout user={user} onLogout={logout} />}>
            <Route path="/login" element={isAuthenticated ? <Navigate to="/jobs" /> : <LoginPage />} />
            <Route path="/auth/callback" element={<AuthCallbackPage />} />
            <Route
              path="/jobs"
              element={isAuthenticated ? <JobListPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/jobs/new"
              element={isAuthenticated ? <CreateJobPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/jobs/:jobId"
              element={isAuthenticated ? <JobStatusPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/jobs/:jobId/result"
              element={isAuthenticated ? <ResultPage /> : <Navigate to="/login" />}
            />
            <Route
              path="/jobs/:jobId/logs"
              element={isAuthenticated ? <AnalysisLogsPage /> : <Navigate to="/login" />}
            />
            <Route path="/" element={<Navigate to={isAuthenticated ? '/jobs' : '/login'} />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
