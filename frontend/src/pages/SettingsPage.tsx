import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../hooks/useAuth'
import { ActionButton } from '../../seed-design/ui'

export function SettingsPage() {
  const { t, i18n } = useTranslation()
  const { user, updateProfile } = useAuth()

  const [displayName, setDisplayName] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (user?.display_name) {
      setDisplayName(user.display_name)
    }
  }, [user])

  const handleSaveProfile = async () => {
    if (!displayName.trim()) return
    setSaving(true)
    try {
      await updateProfile({ display_name: displayName.trim() })
      alert(t('settings_saved'))
    } catch (e) {
      alert(t('settings_save_error'))
    } finally {
      setSaving(false)
    }
  }

  const handleChangeLanguage = (lang: string) => {
    i18n.changeLanguage(lang)
    localStorage.setItem('language', lang)
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-[--color-text-primary] mb-2">{t('settings_title')}</h1>
      <p className="text-sm text-[--color-text-tertiary] mb-8">{t('settings_desc')}</p>

      <div className="space-y-6">
        {/* Profile Info */}
        <div className="p-6 bg-[--color-bg-surface] rounded-xl border border-[--color-border-default]">
          <h3 className="text-sm font-medium text-[--color-text-primary] mb-4">{t('settings_display_name')}</h3>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full rounded-lg border border-[--color-border-default] px-3 py-2 text-sm focus:border-[--color-border-accent] focus:outline-none focus:ring-2 focus:ring-em-500/20"
          />
        </div>

        {/* Email */}
        <div className="p-6 bg-[--color-bg-surface] rounded-xl border border-[--color-border-default]">
          <h3 className="text-sm font-medium text-[--color-text-primary] mb-2">{t('settings_email')}</h3>
          <div className="flex items-center gap-3">
            <span className="text-sm text-[--color-text-secondary]">{user?.email}</span>
            {user?.providers && user.providers.length > 0 && (
              <div className="inline-flex items-center gap-1.5 rounded-md bg-[--color-bg-neutral] px-2 py-0.5 text-xs font-medium text-[--color-text-secondary]">
                {user.providers.includes('google') && (
                  <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032 s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2 C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z" />
                  </svg>
                )}
                {user.providers.includes('github') && (
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                  </svg>
                )}
                {user.providers.join(', ')} {user.github_username && `(@${user.github_username})`}
              </div>
            )}
          </div>
        </div>

        {/* Language */}
        <div className="p-6 bg-[--color-bg-surface] rounded-xl border border-[--color-border-default]">
          <h3 className="text-sm font-medium text-[--color-text-primary] mb-3">{t('settings_language')}</h3>
          <div className="flex gap-3">
            <button
              onClick={() => handleChangeLanguage('ko')}
              className={`flex-1 rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                i18n.language === 'ko'
                  ? 'border-[--color-border-accent] bg-em-50 text-em-800'
                  : 'border-[--color-border-default] bg-[--color-bg-surface] text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]'
              }`}
            >
              한국어
            </button>
            <button
              onClick={() => handleChangeLanguage('en')}
              className={`flex-1 rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                i18n.language === 'en'
                  ? 'border-[--color-border-accent] bg-em-50 text-em-800'
                  : 'border-[--color-border-default] bg-[--color-bg-surface] text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]'
              }`}
            >
              English
            </button>
          </div>
        </div>

        {/* Save Button */}
        <ActionButton
          variant="brandSolid"
          size="medium"
          onClick={handleSaveProfile}
          loading={saving}
          disabled={saving || !displayName.trim()}
          className="w-full"
        >
          {t('settings_save')}
        </ActionButton>
      </div>
    </div>
  )
}
