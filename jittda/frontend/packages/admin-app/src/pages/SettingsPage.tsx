import { useAuth } from '../contexts/AuthContext'

export function SettingsPage() {
  const { user } = useAuth()

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-[--color-text-primary] mb-6">설정</h1>

      {/* Profile */}
      <section className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold text-[--color-text-primary] mb-4">프로필</h2>
        <dl className="space-y-3">
          <div>
            <dt className="text-xs text-[--color-text-tertiary] uppercase">이름</dt>
            <dd className="text-sm text-[--color-text-primary]">{user?.name || '-'}</dd>
          </div>
          <div>
            <dt className="text-xs text-[--color-text-tertiary] uppercase">이메일</dt>
            <dd className="text-sm text-[--color-text-primary]">{user?.email || '-'}</dd>
          </div>
          <div>
            <dt className="text-xs text-[--color-text-tertiary] uppercase">인증 방법</dt>
            <dd className="text-sm text-[--color-text-primary] capitalize">
              {user?.oauth_provider || '-'}
            </dd>
          </div>
        </dl>
      </section>

      {/* API Info */}
      <section className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl p-6">
        <h2 className="text-lg font-semibold text-[--color-text-primary] mb-4">시스템 정보</h2>
        <dl className="space-y-3">
          <div>
            <dt className="text-xs text-[--color-text-tertiary] uppercase">버전</dt>
            <dd className="text-sm text-[--color-text-primary]">v5.0.0</dd>
          </div>
          <div>
            <dt className="text-xs text-[--color-text-tertiary] uppercase">엔진</dt>
            <dd className="text-sm text-[--color-text-primary]">LangGraph HMAS</dd>
          </div>
        </dl>
      </section>
    </div>
  )
}
