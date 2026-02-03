import { useTranslation } from 'react-i18next'

const BACKEND = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export function LoginPage() {
  const { t } = useTranslation()

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6">
      <h1 className="text-3xl font-bold text-gray-900">Vantict Sniper</h1>
      <p className="text-gray-600">AI Technical Interview Script Generator</p>
      <div className="flex flex-col gap-3 w-64">
        <a
          href={`${BACKEND}/auth/google/login`}
          className="block text-center bg-white border border-gray-300 rounded-lg px-4 py-3 hover:bg-gray-50 text-gray-800 font-medium"
        >
          {t('login_with_google')}
        </a>
        <a
          href={`${BACKEND}/auth/github/login`}
          className="block text-center bg-gray-900 text-white rounded-lg px-4 py-3 hover:bg-gray-800 font-medium"
        >
          {t('login_with_github')}
        </a>
      </div>
    </div>
  )
}
