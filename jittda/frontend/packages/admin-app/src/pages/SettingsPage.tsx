import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Building2, Save } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { BaseAPI } from '../lib/api'

interface CompanyForm {
  company_name: string
  company_slug: string
  company_description: string
}

class SettingsAPI extends BaseAPI {
  static updateCompany(data: CompanyForm) {
    return this.put<{ success: boolean }>('/api/settings/company', data)
  }
}

export function SettingsPage() {
  const { user } = useAuth()
  const [form, setForm] = useState<CompanyForm>({
    company_name: (user as Record<string, string>)?.company_name ?? '',
    company_slug: (user as Record<string, string>)?.company_slug ?? '',
    company_description: (user as Record<string, string>)?.company_description ?? '',
  })

  const mutation = useMutation({
    mutationFn: () => SettingsAPI.updateCompany(form),
  })

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

      {/* Company Profile */}
      <section className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Building2 size={18} className="text-[--color-text-secondary]" />
          <h2 className="text-lg font-semibold text-[--color-text-primary]">회사 프로필</h2>
        </div>
        <p className="text-xs text-[--color-text-tertiary] mb-4">
          커리어 페이지에 표시될 회사 정보입니다.
        </p>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-[--color-text-tertiary] uppercase block mb-1">
              회사명
            </label>
            <input
              type="text"
              value={form.company_name}
              onChange={(e) => setForm((f) => ({ ...f, company_name: e.target.value }))}
              className="w-full px-3 py-2 rounded-lg border border-[--color-border-default] bg-[--color-bg-primary] text-sm text-[--color-text-primary]"
              placeholder="Jittda Inc."
            />
          </div>
          <div>
            <label className="text-xs text-[--color-text-tertiary] uppercase block mb-1">
              URL Slug
            </label>
            <div className="flex items-center gap-1">
              <span className="text-xs text-[--color-text-tertiary]">/careers/</span>
              <input
                type="text"
                value={form.company_slug}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    company_slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''),
                  }))
                }
                className="flex-1 px-3 py-2 rounded-lg border border-[--color-border-default] bg-[--color-bg-primary] text-sm text-[--color-text-primary]"
                placeholder="jittda"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-[--color-text-tertiary] uppercase block mb-1">
              회사 소개
            </label>
            <textarea
              value={form.company_description}
              onChange={(e) => setForm((f) => ({ ...f, company_description: e.target.value }))}
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-[--color-border-default] bg-[--color-bg-primary] text-sm text-[--color-text-primary] resize-none"
              placeholder="회사 소개를 입력하세요..."
            />
          </div>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="flex items-center gap-1.5 px-4 py-2 bg-[--color-bg-accent] text-[--color-text-on-accent] rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            <Save size={14} />
            {mutation.isPending ? '저장 중...' : '저장'}
          </button>
          {mutation.isSuccess && (
            <p className="text-xs text-[--color-text-success]">저장되었습니다.</p>
          )}
          {mutation.isError && (
            <p className="text-xs text-[--color-text-danger]">
              저장 실패: {mutation.error.message}
            </p>
          )}
        </div>
      </section>

      {/* System Info */}
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
