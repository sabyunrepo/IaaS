import { Outlet } from 'react-router-dom'
import { Navbar } from './Navbar'

interface LayoutProps {
  user: { display_name: string; avatar_url?: string } | null
  onLogout: () => void
}

export function Layout({ user, onLogout }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar user={user} onLogout={onLogout} />
      <main className="max-w-5xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
