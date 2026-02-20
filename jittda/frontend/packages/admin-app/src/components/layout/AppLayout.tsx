import { Link, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

const NAV_ITEMS = [
  { path: '/', label: '대시보드', icon: '📊' },
  { path: '/jobs', label: '채용 공고', icon: '📋' },
  { path: '/settings', label: '설정', icon: '⚙️' },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const location = useLocation()

  return (
    <div className="min-h-screen flex bg-[--color-bg-primary]">
      {/* Sidebar */}
      <aside className="w-60 bg-[--color-bg-surface] border-r border-[--color-border-default] flex flex-col">
        <div className="p-4 border-b border-[--color-border-default]">
          <h1 className="text-lg font-bold text-[--color-text-primary]">Jittda Admin</h1>
          <p className="text-xs text-[--color-text-tertiary]">v5.0</p>
        </div>

        <nav className="flex-1 p-2">
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-[--color-bg-accent] text-[--color-text-accent] font-medium'
                    : 'text-[--color-text-secondary] hover:bg-[--color-bg-neutral]'
                }`}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            )
          })}
        </nav>

        {user && (
          <div className="p-4 border-t border-[--color-border-default]">
            <p className="text-sm font-medium text-[--color-text-primary] truncate">
              {user.name}
            </p>
            <p className="text-xs text-[--color-text-tertiary] truncate">{user.email}</p>
            <button
              onClick={logout}
              className="mt-2 text-xs text-[--color-text-danger] hover:underline"
            >
              로그아웃
            </button>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
