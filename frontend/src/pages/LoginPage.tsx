import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { setToken } from '../lib/api'

// Google Icon SVG
function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 533.5 544.3" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M533.5 278.4c0-17.4-1.6-34.1-4.6-50.2H272v95h146.9c-6.3 33.9-25 62.5-53.2 81.8v68.1h85.8c50.2-46.3 82-114.6 82-194.7z"
        fill="#4285F4"
      />
      <path
        d="M272 544.3c71.6 0 131.7-23.7 175.7-64.2l-85.8-68.1c-23.8 16-54.1 25.4-89.9 25.4-69.1 0-127.6-46.6-148.4-109.3h-89.6v68.9C77.7 480.5 168.5 544.3 272 544.3z"
        fill="#34A853"
      />
      <path
        d="M123.6 328.1c-10.8-32.1-10.8-66.9 0-99l-89.6-68.9c-39.1 77.6-39.1 168.3 0 245.9l89.6-68z"
        fill="#FBBC05"
      />
      <path
        d="M272 107.7c37.4-.6 73.5 13.2 101.1 38.7l75.4-75.4C403.4 24.5 341.4 0 272 0 168.5 0 77.7 63.8 34 159.2l89.6 68.9C144.4 154.3 202.9 107.7 272 107.7z"
        fill="#EA4335"
      />
    </svg>
  )
}

// GitHub Icon SVG
function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 0 0 5.47 7.59c.4.07.55-.17.55-.38v-1.48c-2.22.48-2.69-1.07-2.69-1.07-.36-.91-.88-1.15-.88-1.15-.72-.5.05-.49.05-.49.8.06 1.22.82 1.22.82.71 1.22 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.01.08-2.1 0 0 .67-.21 2.2.82a7.6 7.6 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.09.16 1.9.08 2.1.51.56.82 1.28.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.74.54 1.49v2.21c0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
    </svg>
  )
}

export function LoginPage() {
  const { t } = useTranslation()
  const [devLoading, setDevLoading] = useState(false)

  const handleDevLogin = async () => {
    setDevLoading(true)
    try {
      const res = await fetch(`/auth/dev-login`, { method: 'POST' })
      if (!res.ok) throw new Error('Dev login failed')
      const data = await res.json()
      setToken(data.token)
      window.location.href = import.meta.env.BASE_URL
    } catch {
      setDevLoading(false)
    }
  }

  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="rounded-2xl border border-[--color-border-default] bg-[--color-bg-surface] p-8 shadow-lg">
          {/* Header */}
          <div className="mb-8 text-center">
            <img src={`${import.meta.env.BASE_URL}logo-full.png`} alt="JittDa" className="h-20 mx-auto" />
            <h1 className="text-2xl font-bold text-[--color-text-primary]">{t('app_title')}</h1>
            <p className="mt-2 text-sm text-[--color-text-secondary]">{t('login_subtitle')}</p>
          </div>

          {/* OAuth Buttons */}
          <div className="space-y-3">
            <a
              href={`/auth/google/login`}
              className="group flex w-full items-center justify-center gap-3 rounded-lg border border-[--color-border-default] bg-white px-4 py-3 text-sm font-medium text-[--color-text-secondary] transition-all hover:border-ink-300 hover:bg-[--color-bg-surface-hover] hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-[--color-border-accent] focus:ring-offset-2"
            >
              <GoogleIcon className="h-5 w-5" />
              <span>{t('login_with_google')}</span>
            </a>

            <a
              href={`/auth/github/login`}
              className="group flex w-full items-center justify-center gap-3 rounded-lg bg-gray-900 px-4 py-3 text-sm font-medium text-white transition-all hover:bg-gray-800 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2"
            >
              <GitHubIcon className="h-5 w-5" />
              <span>{t('login_with_github')}</span>
            </a>
          </div>

          {/* Dev Login Button - only in development */}
          {import.meta.env.DEV && (
            <button
              onClick={handleDevLogin}
              disabled={devLoading}
              className="mt-3 flex w-full items-center justify-center gap-3 rounded-lg border border-dashed border-[--color-border-accent] bg-[--color-bg-accent-subtle] px-4 py-3 text-sm font-medium text-[--color-text-accent-strong] transition-all hover:bg-em-100 focus:outline-none focus:ring-2 focus:ring-[--color-border-accent] focus:ring-offset-2 disabled:opacity-50"
            >
              <span>🔧</span>
              <span>{devLoading ? t('loading') : t('dev_login')}</span>
            </button>
          )}

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[--color-border-subtle]"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-[--color-bg-surface] px-4 text-[--color-text-tertiary]">{t('login_secure_note')}</span>
            </div>
          </div>

          {/* Features */}
          <div className="space-y-3 text-sm text-[--color-text-secondary]">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-green-100">
                <svg className="h-3 w-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <span>{t('login_feature_1')}</span>
            </div>
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-green-100">
                <svg className="h-3 w-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <span>{t('login_feature_2')}</span>
            </div>
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-green-100">
                <svg className="h-3 w-3 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <span>{t('login_feature_3')}</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-xs text-[--color-text-tertiary]">
          {t('login_terms')}
        </p>
      </div>
    </div>
  )
}
