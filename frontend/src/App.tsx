import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { ErrorBoundary } from './components/ErrorBoundary'
import { LoginPage } from './pages/LoginPage'
import { JobListPage } from './pages/JobListPage'
import { CreateJobPage } from './pages/CreateJobPage'
import { JobStatusPage } from './pages/JobStatusPage'
import { ResultPage } from './pages/ResultPage'
import { AnalysisLogsPage } from './pages/AnalysisLogsPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { AuthCallbackPage } from './pages/AuthCallbackPage'
import { useAuth } from './hooks/useAuth'
import './i18n'

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
    </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App
