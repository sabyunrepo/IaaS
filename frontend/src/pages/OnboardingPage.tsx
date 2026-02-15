import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

interface OnboardingPageProps {
  onSelectRole: (role: string) => Promise<void>
}

const ROLES = [
  {
    value: 'ceo',
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
    gradient: 'from-brand-500 to-navy-700',
    bg: 'bg-brand-50',
    border: 'border-brand-200 hover:border-brand-400',
    text: 'text-brand-600',
  },
  {
    value: 'candidate',
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
      </svg>
    ),
    gradient: 'from-emerald-500 to-teal-600',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200 hover:border-emerald-400',
    text: 'text-emerald-600',
  },
  {
    value: 'both',
    icon: (
      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
    ),
    gradient: 'from-brand-500 to-orange-600',
    bg: 'bg-brand-50',
    border: 'border-brand-200 hover:border-brand-400',
    text: 'text-brand-600',
  },
] as const

export function OnboardingPage({ onSelectRole }: OnboardingPageProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [selected, setSelected] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleConfirm = async () => {
    if (!selected) return
    setLoading(true)
    try {
      await onSelectRole(selected)
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] px-4">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('onboarding_title')}</h1>
      <p className="text-gray-500 mb-8 max-w-md text-center">{t('onboarding_desc')}</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-2xl mb-8">
        {ROLES.map((role) => (
          <button
            key={role.value}
            onClick={() => setSelected(role.value)}
            className={`relative rounded-2xl border-2 p-6 text-center transition-all ${
              selected === role.value
                ? `${role.border} ring-2 ring-offset-2 ring-${role.value === 'ceo' ? 'brand' : role.value === 'candidate' ? 'emerald' : 'brand'}-400 shadow-md`
                : `border-gray-200 hover:shadow-sm ${role.border}`
            }`}
          >
            <div className={`flex h-14 w-14 items-center justify-center rounded-xl ${role.bg} ${role.text} mx-auto mb-3`}>
              {role.icon}
            </div>
            <h3 className="font-semibold text-gray-900">{t(`onboarding_role_${role.value}`)}</h3>
            <p className="text-xs text-gray-500 mt-1">{t(`onboarding_role_${role.value}_desc`)}</p>
          </button>
        ))}
      </div>

      <button
        onClick={handleConfirm}
        disabled={!selected || loading}
        className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-navy-700 to-navy-600 px-8 py-3 text-sm font-semibold text-white shadow-md transition-all hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? t('loading') : t('onboarding_confirm')}
      </button>
    </div>
  )
}
