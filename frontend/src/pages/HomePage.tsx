import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

interface HomePageProps {
  user: {
    id: string
    display_name: string
    avatar_url?: string
    github_username?: string | null
  } | null
}

export function HomePage({ user }: HomePageProps) {
  const { t } = useTranslation()

  return (
    <div className="space-y-8">
      {/* 인사 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-[--color-text-primary]">
          {t('home_hello', { name: user?.display_name || 'User' })}
        </h1>
        <p className="text-[--color-text-tertiary] mt-1">{t('home_subtitle')}</p>
      </div>

      {/* 퀵 액션 카드 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* 면접 스크립트 생성 */}
        <Link
          to="/interview/new"
          className="group relative rounded-2xl border border-[--color-border-default] bg-[--color-bg-surface] p-6 shadow-sm transition-all hover:shadow-md hover:border-[--color-border-accent]"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-em-50 text-em-700 mb-4 transition-transform group-hover:scale-110">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="font-semibold text-[--color-text-primary]">{t('home_create_script')}</h3>
          <p className="text-sm text-[--color-text-tertiary] mt-1">{t('home_create_script_desc')}</p>
        </Link>

        {/* 내 면접 스크립트 */}
        <Link
          to="/interview"
          className="group relative rounded-2xl border border-[--color-border-default] bg-[--color-bg-surface] p-6 shadow-sm transition-all hover:shadow-md hover:border-ink-300"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[--color-bg-neutral] text-[--color-text-tertiary] mb-4 transition-transform group-hover:scale-110">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="font-semibold text-[--color-text-primary]">{t('home_my_scripts')}</h3>
          <p className="text-sm text-[--color-text-tertiary] mt-1">{t('home_my_scripts_desc')}</p>
        </Link>
      </div>
    </div>
  )
}
