import { Routes, Route } from 'react-router-dom'
import { CareerPage } from './pages/CareerPage'
import { JobDetailPage } from './pages/JobDetailPage'
import { ApplyPage } from './pages/ApplyPage'
import { ConfirmPage } from './pages/ConfirmPage'

export function App() {
  return (
    <Routes>
      <Route path="/careers/:slug" element={<CareerPage />} />
      <Route path="/careers/:slug/:jobId" element={<JobDetailPage />} />
      <Route path="/careers/:slug/:jobId/apply" element={<ApplyPage />} />
      <Route path="/apply/confirm" element={<ConfirmPage />} />
    </Routes>
  )
}
