import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

interface NavbarProps {
  user: { display_name: string; avatar_url?: string } | null
  onLogout: () => void
}

export function Navbar({ user, onLogout }: NavbarProps) {
  const { t, i18n } = useTranslation()

  const toggleLang = () => {
    i18n.changeLanguage(i18n.language === 'ko' ? 'en' : 'ko')
  }

  return (
    <nav className="bg-gray-900 text-white px-6 py-3 flex items-center justify-between" aria-label={t('nav_label')}>
      <Link to="/" className="text-xl font-bold">{t('app_title')}</Link>
      <div className="flex items-center gap-4">
        <button
          onClick={toggleLang}
          className="text-sm px-2 py-1 border border-gray-600 rounded"
          aria-label={t('switch_language')}
        >
          {i18n.language === 'ko' ? 'EN' : 'KO'}
        </button>
        {user ? (
          <>
            <Link to="/jobs" className="hover:text-gray-300">{t('jobs')}</Link>
            <Link to="/jobs/new" className="hover:text-gray-300">{t('create_job')}</Link>
            <span className="text-sm text-gray-400" aria-label={t('logged_in_as')}>{user.display_name}</span>
            <button onClick={onLogout} className="text-sm text-red-400 hover:text-red-300">
              {t('logout')}
            </button>
          </>
        ) : (
          <Link to="/login" className="hover:text-gray-300">{t('login')}</Link>
        )}
      </div>
    </nav>
  )
}
