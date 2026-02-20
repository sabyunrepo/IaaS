import { useState, useRef, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Divider, AvatarRoot, AvatarImage, AvatarFallback } from '../../seed-design/ui'

interface NavbarProps {
  user: {
    display_name: string
    avatar_url?: string
    role?: string | null
  } | null
  onLogout: () => void
}

export function Navbar({ user, onLogout }: NavbarProps) {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  // 드롭다운 외부 클릭 시 닫기
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  const role = user?.role

  const navItems = [
    { path: '/', label: t('nav_home'), show: true },
    { path: '/interview', label: t('nav_interview'), show: true },
  ].filter(item => item.show)

  return (
    <nav
      className="sticky top-0 z-50 border-b border-[--color-border-default]/50 bg-[--color-bg-surface]/80 backdrop-blur-lg"
      aria-label={t('nav_label')}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group shrink-0">
            <img
              src={`${import.meta.env.BASE_URL}logo-icon.png`}
              alt="JittDa"
              className="h-9 w-9 transition-transform group-hover:scale-105"
            />
            <span className="hidden sm:inline text-lg font-bold bg-gradient-to-r from-em-700 to-teal-500 bg-clip-text text-transparent">
              {t('app_title')}
            </span>
          </Link>

          {/* Navigation Links (데스크탑) */}
          {user && (
            <div className="hidden md:flex items-center gap-1">
              {navItems.map(item => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                    isActive(item.path)
                      ? 'bg-em-50 text-em-700'
                      : 'text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover] hover:text-[--color-text-accent]'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          )}

          {/* Right Side */}
          <div className="flex items-center gap-2">
            {user ? (
              <>
                {/* New Script CTA */}
                <Link
                  to="/interview/new"
                  className="hidden sm:flex items-center gap-1.5 rounded-lg bg-em-500 px-3 py-1.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-em-600 hover:shadow-[0_0_20px_-5px_hsl(160_60%_45%/0.2)]"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  {t('create_job')}
                </Link>

                {/* User Avatar + Dropdown */}
                <div className="relative ml-1" ref={menuRef}>
                  <button
                    onClick={() => setMenuOpen(prev => !prev)}
                    className="flex items-center gap-2 rounded-lg px-2 py-1.5 transition-colors hover:bg-[--color-bg-surface-hover]"
                    aria-expanded={menuOpen}
                    aria-haspopup="true"
                  >
                    <AvatarRoot size="36" className="ring-2 ring-em-200">
                      <AvatarImage src={user.avatar_url} alt={user.display_name || 'User'} />
                      <AvatarFallback className="bg-gradient-to-br from-em-500 to-teal-400 text-sm font-medium text-white">
                        {(user.display_name || 'U').charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </AvatarRoot>
                    <svg className={`h-4 w-4 text-[--color-text-tertiary] transition-transform ${menuOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {menuOpen && (
                    <div className="absolute right-0 mt-2 w-48 rounded-xl border border-[--color-border-default] bg-[--color-bg-surface]/90 backdrop-blur-md py-1 shadow-elevated z-50 animate-slideDown">
                      <div className="px-4 py-2 border-b border-[--color-border-subtle]">
                        <p className="text-sm font-medium text-[--color-text-primary] truncate">{user.display_name}</p>
                        <p className="text-xs text-[--color-text-tertiary] truncate">
                          {role === 'ceo' ? 'CEO / HR' : role === 'candidate' ? 'CTO / Developer' : role === 'both' ? 'CEO & Developer' : ''}
                        </p>
                      </div>

                      {/* 모바일 네비 (md 미만에서 표시) */}
                      <div className="md:hidden border-b border-[--color-border-subtle] py-1">
                        {navItems.map(item => (
                          <Link
                            key={item.path}
                            to={item.path}
                            onClick={() => setMenuOpen(false)}
                            className={`block px-4 py-2 text-sm ${
                              isActive(item.path) ? 'text-em-700 bg-em-50' : 'text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]'
                            }`}
                          >
                            {item.label}
                          </Link>
                        ))}
                        <Link
                          to="/interview/new"
                          onClick={() => setMenuOpen(false)}
                          className="block px-4 py-2 text-sm text-[--color-text-accent] font-medium hover:bg-[--color-bg-surface-hover]"
                        >
                          + {t('create_job')}
                        </Link>
                      </div>

                      <Link
                        to="/settings"
                        onClick={() => setMenuOpen(false)}
                        className="flex items-center gap-2 px-4 py-2 text-sm text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]"
                      >
                        <svg className="h-4 w-4 text-[--color-text-tertiary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {t('nav_settings')}
                      </Link>

                      <button
                        onClick={() => {
                          i18n.changeLanguage(i18n.language === 'ko' ? 'en' : 'ko')
                          setMenuOpen(false)
                        }}
                        className="flex items-center gap-2 w-full px-4 py-2 text-sm text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover] text-left"
                      >
                        <svg className="h-4 w-4 text-[--color-text-tertiary]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                        </svg>
                        {i18n.language === 'ko' ? 'English' : '한국어'}
                      </button>

                      <Divider className="my-1" />
                      <div>
                        <button
                          onClick={() => {
                            setMenuOpen(false)
                            onLogout()
                          }}
                          className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 text-left"
                        >
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                          </svg>
                          {t('logout')}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <Link
                to="/login"
                className="flex items-center gap-1.5 rounded-lg bg-em-500 px-4 py-2 text-sm font-medium text-white shadow-sm transition-all hover:bg-em-600 hover:shadow-md"
              >
                {t('login')}
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
