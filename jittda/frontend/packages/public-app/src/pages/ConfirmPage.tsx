import { useLocation } from 'react-router-dom'

export function ConfirmPage() {
  const location = useLocation()
  const state = location.state as { name?: string; email?: string } | null

  return (
    <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-8 max-w-md text-center">
        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-xl font-bold text-[--color-text-primary]">지원 완료</h1>
        <p className="text-[--color-text-secondary] mt-2">
          {state?.name ? `${state.name}님, ` : ''}지원해주셔서 감사합니다.
        </p>
        {state?.email && (
          <p className="text-sm text-[--color-text-tertiary] mt-1">
            결과는 {state.email}로 안내드리겠습니다.
          </p>
        )}
      </div>
    </div>
  )
}
