import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../hooks/useAuth'
import { useCandidate } from '../hooks/useCandidate'

export function SettingsPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { user, updateProfile } = useAuth()
  const { fetchJDs, updateJD, deleteJD, fetchMyProfile } = useCandidate()

  const [activeTab, setActiveTab] = useState<'profile' | 'cto-info' | 'jd-management'>('profile')
  const [displayName, setDisplayName] = useState('')
  const [saving, setSaving] = useState(false)
  const [myProfile, setMyProfile] = useState<any>(null)
  const [myJDs, setMyJDs] = useState<any[]>([])
  const [loadingProfile, setLoadingProfile] = useState(false)
  const [loadingJDs, setLoadingJDs] = useState(false)
  const [editingJD, setEditingJD] = useState<string | null>(null)
  const [editJDText, setEditJDText] = useState('')

  const isCEO = user?.role === 'ceo' || user?.role === 'both'
  const isCandidate = user?.role === 'candidate' || user?.role === 'both'

  useEffect(() => {
    if (user?.display_name) {
      setDisplayName(user.display_name)
    }
  }, [user])

  useEffect(() => {
    if (activeTab === 'cto-info' && isCandidate && !myProfile) {
      loadMyProfile()
    }
  }, [activeTab, isCandidate])

  useEffect(() => {
    if (activeTab === 'jd-management' && isCEO && myJDs.length === 0) {
      loadMyJDs()
    }
  }, [activeTab, isCEO])

  const loadMyProfile = async () => {
    setLoadingProfile(true)
    try {
      const profile = await fetchMyProfile()
      setMyProfile(profile)
    } catch (e) {
      console.error('Failed to load profile:', e)
    } finally {
      setLoadingProfile(false)
    }
  }

  const loadMyJDs = async () => {
    setLoadingJDs(true)
    try {
      const jds = await fetchJDs()
      setMyJDs(jds)
    } catch (e) {
      console.error('Failed to load JDs:', e)
    } finally {
      setLoadingJDs(false)
    }
  }

  const handleSaveProfile = async () => {
    if (!displayName.trim()) return
    setSaving(true)
    try {
      await updateProfile({ display_name: displayName.trim() })
      alert(t('settings_profile_saved'))
    } catch (e) {
      alert(t('settings_save_error'))
    } finally {
      setSaving(false)
    }
  }

  const handleChangeLanguage = async (lang: string) => {
    i18n.changeLanguage(lang)
    try {
      await updateProfile({ language_preference: lang })
    } catch (e) {
      console.error('Failed to save language:', e)
    }
  }

  const handleEditJD = (jd: any) => {
    setEditingJD(jd.id)
    setEditJDText(jd.jd_text || '')
  }

  const handleSaveJD = async (jdId: string) => {
    try {
      await updateJD(jdId, { jd_text: editJDText })
      setMyJDs(prev => prev.map(j => j.id === jdId ? { ...j, jd_text: editJDText } : j))
      setEditingJD(null)
      alert(t('settings_jd_updated'))
    } catch (e) {
      alert(t('settings_save_error'))
    }
  }

  const handleDeleteJD = async (jdId: string) => {
    if (!confirm(t('settings_jd_delete_confirm'))) return
    try {
      await deleteJD(jdId)
      setMyJDs(prev => prev.filter(j => j.id !== jdId))
      alert(t('settings_jd_deleted'))
    } catch (e) {
      alert(t('settings_save_error'))
    }
  }

  const tabs = [
    { id: 'profile' as const, label: t('settings_tab_profile'), show: true },
    { id: 'cto-info' as const, label: t('settings_tab_cto_info'), show: isCandidate },
    { id: 'jd-management' as const, label: t('settings_tab_jd_management'), show: isCEO },
  ].filter(tab => tab.show)

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('settings_title')}</h1>
      <p className="text-sm text-gray-500 mb-8">{t('settings_desc')}</p>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-8" aria-label="Settings tabs">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 border-b-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-indigo-600 text-indigo-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="space-y-6">
          {/* Avatar & Name */}
          <div className="flex items-start gap-4 p-6 bg-white rounded-xl border border-gray-200">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt={user.display_name} className="h-16 w-16 rounded-full ring-2 ring-gray-100" />
            ) : (
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 text-xl font-medium text-white">
                {(user?.display_name || 'U').charAt(0).toUpperCase()}
              </div>
            )}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('settings_display_name')}</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                placeholder={t('settings_display_name_placeholder')}
              />
            </div>
          </div>

          {/* Email (readonly) */}
          <div className="p-6 bg-white rounded-xl border border-gray-200">
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('settings_email')}</label>
            <input
              type="email"
              value={user?.email || ''}
              disabled
              className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-500 cursor-not-allowed"
            />
            <p className="mt-1 text-xs text-gray-400">{t('settings_email_readonly')}</p>
          </div>

          {/* Connected Accounts */}
          <div className="p-6 bg-white rounded-xl border border-gray-200">
            <h3 className="text-sm font-medium text-gray-900 mb-3">{t('settings_connected_accounts')}</h3>
            <div className="space-y-2">
              {user?.providers?.includes('google') && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                  Google
                </div>
              )}
              {user?.providers?.includes('github') && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                  </svg>
                  GitHub {user.github_username && `(@${user.github_username})`}
                </div>
              )}
            </div>
          </div>

          {/* Language */}
          <div className="p-6 bg-white rounded-xl border border-gray-200">
            <h3 className="text-sm font-medium text-gray-900 mb-3">{t('settings_language')}</h3>
            <div className="flex gap-3">
              <button
                onClick={() => handleChangeLanguage('ko')}
                className={`flex-1 rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                  i18n.language === 'ko'
                    ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                    : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                한국어
              </button>
              <button
                onClick={() => handleChangeLanguage('en')}
                className={`flex-1 rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                  i18n.language === 'en'
                    ? 'border-indigo-600 bg-indigo-50 text-indigo-700'
                    : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                English
              </button>
            </div>
          </div>

          {/* Role */}
          <div className="p-6 bg-white rounded-xl border border-gray-200">
            <h3 className="text-sm font-medium text-gray-900 mb-1">{t('settings_role')}</h3>
            <p className="text-xs text-gray-500 mb-3">{t('settings_role_desc')}</p>
            <div className="inline-flex items-center gap-2 rounded-lg bg-gray-100 px-3 py-2 text-sm font-medium text-gray-700">
              {user?.role === 'ceo' && 'CEO / HR'}
              {user?.role === 'candidate' && 'CTO / Developer'}
              {user?.role === 'both' && 'CEO & Developer'}
              {!user?.role && t('settings_role_not_set')}
            </div>
            <button
              onClick={() => navigate('/onboarding')}
              className="ml-3 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
            >
              {t('settings_change_role')}
            </button>
          </div>

          {/* Save Button */}
          <button
            onClick={handleSaveProfile}
            disabled={saving || !displayName.trim()}
            className="w-full rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-3 text-sm font-medium text-white shadow-sm transition-all hover:from-indigo-700 hover:to-purple-700 hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? t('saving') : t('settings_save')}
          </button>
        </div>
      )}

      {/* CTO Info Tab */}
      {activeTab === 'cto-info' && (
        <div className="space-y-6">
          {loadingProfile ? (
            <div className="p-8 text-center text-gray-500">{t('loading')}</div>
          ) : myProfile ? (
            <>
              <div className="p-6 bg-white rounded-xl border border-gray-200">
                <h3 className="text-sm font-medium text-gray-900 mb-4">{t('settings_cto_summary')}</h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-xs text-gray-500">{t('candidate_name')}: </span>
                    <span className="text-sm font-medium text-gray-900">{myProfile.name}</span>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">{t('experience_level')}: </span>
                    <span className="text-sm font-medium text-gray-900">{myProfile.experience_level || '-'}</span>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">{t('settings_profile_completeness')}: </span>
                    <div className="mt-1 flex items-center gap-2">
                      <div className="h-2 w-full max-w-xs overflow-hidden rounded-full bg-gray-200">
                        <div className="h-full rounded-full bg-indigo-600" style={{ width: `${Math.round(myProfile.data_completeness * 100)}%` }} />
                      </div>
                      <span className="text-sm font-medium text-gray-700">{Math.round(myProfile.data_completeness * 100)}%</span>
                    </div>
                  </div>
                </div>
              </div>

              {myProfile.skills && myProfile.skills.length > 0 && (
                <div className="p-6 bg-white rounded-xl border border-gray-200">
                  <h3 className="text-sm font-medium text-gray-900 mb-3">{t('candidate_skills')}</h3>
                  <div className="flex flex-wrap gap-2">
                    {myProfile.skills.map((skill: string) => (
                      <span key={skill} className="inline-flex items-center rounded-md bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={() => navigate('/find-cto')}
                className="w-full rounded-lg border border-indigo-600 px-4 py-3 text-sm font-medium text-indigo-600 hover:bg-indigo-50 transition-colors"
              >
                {t('settings_edit_profile')}
              </button>
            </>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500 mb-4">{t('settings_no_profile')}</p>
              <button
                onClick={() => navigate('/find-cto')}
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:from-indigo-700 hover:to-purple-700"
              >
                {t('register_candidate')}
              </button>
            </div>
          )}
        </div>
      )}

      {/* JD Management Tab */}
      {activeTab === 'jd-management' && (
        <div className="space-y-6">
          {loadingJDs ? (
            <div className="p-8 text-center text-gray-500">{t('loading')}</div>
          ) : myJDs.length > 0 ? (
            <>
              <div className="space-y-3">
                {myJDs.map((jd) => (
                  <div key={jd.id} className="p-6 bg-white rounded-xl border border-gray-200">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">{jd.title}</h3>
                        <p className="text-xs text-gray-400 mt-1">
                          {t('created_at')}: {new Date(jd.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {editingJD !== jd.id ? (
                          <>
                            <button
                              onClick={() => handleEditJD(jd)}
                              className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
                            >
                              {t('settings_edit')}
                            </button>
                            <button
                              onClick={() => handleDeleteJD(jd.id)}
                              className="text-sm text-red-600 hover:text-red-700 font-medium"
                            >
                              {t('delete')}
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              onClick={() => handleSaveJD(jd.id)}
                              className="text-sm text-green-600 hover:text-green-700 font-medium"
                            >
                              {t('settings_save')}
                            </button>
                            <button
                              onClick={() => setEditingJD(null)}
                              className="text-sm text-gray-600 hover:text-gray-700"
                            >
                              {t('cancel')}
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                    {editingJD === jd.id ? (
                      <textarea
                        value={editJDText}
                        onChange={(e) => setEditJDText(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                        rows={6}
                      />
                    ) : (
                      <p className="text-sm text-gray-600 line-clamp-3">{jd.jd_text || t('settings_no_jd_text')}</p>
                    )}
                  </div>
                ))}
              </div>
              <button
                onClick={() => navigate('/find-ceo')}
                className="w-full rounded-lg border border-indigo-600 px-4 py-3 text-sm font-medium text-indigo-600 hover:bg-indigo-50 transition-colors"
              >
                + {t('ceo_create_jd')}
              </button>
            </>
          ) : (
            <div className="p-8 text-center">
              <p className="text-gray-500 mb-4">{t('ceo_no_jds_title')}</p>
              <button
                onClick={() => navigate('/find-ceo')}
                className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:from-indigo-700 hover:to-purple-700"
              >
                {t('ceo_create_jd')}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
