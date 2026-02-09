import { Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Navbar } from './Navbar'

interface LayoutProps {
  user: { display_name: string; avatar_url?: string; role?: string | null } | null
  onLogout: () => void
}

export function Layout({ user, onLogout }: LayoutProps) {
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-gray-50">
      <a href="#main-content" className="skip-link">
        {t('skip_to_content')}
      </a>
      <Navbar user={user} onLogout={onLogout} />
      <main id="main-content" className="max-w-5xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
