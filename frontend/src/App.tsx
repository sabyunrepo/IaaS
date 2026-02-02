import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { LoginPage } from './pages/LoginPage'
import { JobListPage } from './pages/JobListPage'
import { CreateJobPage } from './pages/CreateJobPage'
import { JobStatusPage } from './pages/JobStatusPage'
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
    <BrowserRouter>
      <Routes>
        <Route element={<Layout user={user} onLogout={logout} />}>
          <Route path="/login" element={<LoginPage />} />
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
          <Route path="/" element={<Navigate to={isAuthenticated ? '/jobs' : '/login'} />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
