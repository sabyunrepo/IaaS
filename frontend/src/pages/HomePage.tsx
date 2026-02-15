import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

interface HomePageProps {
  user: {
    id: string
    display_name: string
    avatar_url?: string
    role?: string | null
    github_username?: string | null
  } | null
}

export function HomePage({ user }: HomePageProps) {
  const { t } = useTranslation()
  const role = user?.role

  // 역할 미설정 → 온보딩 유도
  if (!role) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-navy-800 to-navy-700 shadow-lg mb-6">
          <svg className="h-10 w-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('home_welcome')}</h1>
        <p className="text-gray-500 mb-8 max-w-md">{t('home_welcome_desc')}</p>
        <Link
          to="/onboarding"
          className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-navy-800 to-navy-700 px-6 py-3 text-sm font-semibold text-white shadow-md transition-all hover:shadow-lg hover:from-navy-900 hover:to-navy-800"
        >
          {t('home_get_started')}
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* 인사 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          {t('home_hello', { name: user?.display_name || 'User' })}
        </h1>
        <p className="text-gray-500 mt-1">{t('home_subtitle')}</p>
      </div>

      {/* 퀵 액션 카드 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* 면접 스크립트 생성 — 모든 역할 공통 */}
        <Link
          to="/interview/new"
          className="group relative rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md hover:border-navy-300"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-navy-50 text-navy-700 mb-4 transition-transform group-hover:scale-110">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900">{t('home_create_script')}</h3>
          <p className="text-sm text-gray-500 mt-1">{t('home_create_script_desc')}</p>
        </Link>

        {/* CEO/HR: CTO 찾기 */}
        {(role === 'ceo' || role === 'both') && (
          <Link
            to="/find-cto"
            className="group relative rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md hover:border-brand-200"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600 mb-4 transition-transform group-hover:scale-110">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900">{t('home_find_cto')}</h3>
            <p className="text-sm text-gray-500 mt-1">{t('home_find_cto_desc')}</p>
          </Link>
        )}

        {/* 개발자: CEO 찾기 */}
        {(role === 'candidate' || role === 'both') && (
          <Link
            to="/find-ceo"
            className="group relative rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md hover:border-emerald-200"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 mb-4 transition-transform group-hover:scale-110">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900">{t('home_find_ceo')}</h3>
            <p className="text-sm text-gray-500 mt-1">{t('home_find_ceo_desc')}</p>
          </Link>
        )}

        {/* 내 면접 스크립트 */}
        <Link
          to="/interview"
          className="group relative rounded-2xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md hover:border-gray-300"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gray-100 text-gray-600 mb-4 transition-transform group-hover:scale-110">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="font-semibold text-gray-900">{t('home_my_scripts')}</h3>
          <p className="text-sm text-gray-500 mt-1">{t('home_my_scripts_desc')}</p>
        </Link>
      </div>
    </div>
  )
}
