import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { getToken } from '../lib/api'
import { TextFieldRoot, TextFieldInput, CalloutRoot, CalloutContent, CalloutTitle, CalloutDescription, CheckboxRoot, CheckboxControl, CheckboxIndicator, CheckboxHiddenInput } from '../../seed-design/ui'

export interface GitHubRepo {
  name: string
  full_name: string
  html_url: string
  description: string | null
  language: string | null
  stargazers_count: number
  updated_at: string
  fork: boolean
  private: boolean
}

interface GitHubRepoSelectorProps {
  selectedRepos: string[]
  onSelectionChange: (repos: string[]) => void
  maxSelection?: number
  githubConnected: boolean
}

export function GitHubRepoSelector({
  selectedRepos,
  onSelectionChange,
  maxSelection = 10,
  githubConnected,
}: GitHubRepoSelectorProps) {
  const { t } = useTranslation()
  const [repos, setRepos] = useState<GitHubRepo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [langFilter, setLangFilter] = useState('')
  const [sortBy, setSortBy] = useState<'updated' | 'stars'>('updated')

  useEffect(() => {
    if (!githubConnected) return
    setLoading(true)
    setError(null)
    const token = getToken()
    fetch('/auth/github/repos', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to load repos')
        return res.json()
      })
      .then((data: GitHubRepo[]) => setRepos(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [githubConnected])

  if (!githubConnected) {
    return (
      <CalloutRoot tone="warning">
        <CalloutContent>
          <CalloutTitle>{t('github_not_connected')}</CalloutTitle>
          <CalloutDescription>{t('github_connect_hint')}</CalloutDescription>
        </CalloutContent>
      </CalloutRoot>
    )
  }

  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map(i => (
          <div key={i} className="animate-pulse rounded-lg border border-[--color-border-default] p-3">
            <div className="flex items-center gap-3">
              <div className="h-4 w-4 rounded bg-ink-200" />
              <div className="h-4 w-32 rounded bg-ink-200" />
              <div className="ml-auto h-3 w-16 rounded bg-[--color-bg-neutral]" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <CalloutRoot tone="critical">
        <CalloutContent>
          <CalloutDescription>{error}</CalloutDescription>
        </CalloutContent>
      </CalloutRoot>
    )
  }

  // Get unique languages for filter
  const languages = [...new Set(repos.map(r => r.language).filter(Boolean))] as string[]

  // Filter and sort
  const filtered = repos
    .filter(r => !r.fork)
    .filter(r => !search || r.name.toLowerCase().includes(search.toLowerCase()))
    .filter(r => !langFilter || r.language === langFilter)
    .sort((a, b) => {
      if (sortBy === 'stars') return b.stargazers_count - a.stargazers_count
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })

  const toggleRepo = (url: string) => {
    if (selectedRepos.includes(url)) {
      onSelectionChange(selectedRepos.filter(r => r !== url))
    } else if (selectedRepos.length < maxSelection) {
      onSelectionChange([...selectedRepos, url])
    }
  }

  const formatDate = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    if (days === 0) return t('today')
    if (days === 1) return t('yesterday')
    if (days < 30) return t('days_ago', { count: days })
    const months = Math.floor(days / 30)
    return t('months_ago', { count: months })
  }

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-2">
        <TextFieldRoot className="flex-1 min-w-[160px]">
          <TextFieldInput
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={t('repo_search_placeholder')}
          />
        </TextFieldRoot>
        <select
          value={langFilter}
          onChange={e => setLangFilter(e.target.value)}
          className="rounded-lg border border-gray-300 px-2 py-1.5 text-sm focus:border-[--color-border-accent] focus:outline-none focus:ring-1 focus:ring-[--color-border-accent]"
        >
          <option value="">{t('all_languages')}</option>
          {languages.map(lang => (
            <option key={lang} value={lang}>{lang}</option>
          ))}
        </select>
        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value as 'updated' | 'stars')}
          className="rounded-lg border border-gray-300 px-2 py-1.5 text-sm focus:border-[--color-border-accent] focus:outline-none focus:ring-1 focus:ring-[--color-border-accent]"
        >
          <option value="updated">{t('sort_updated')}</option>
          <option value="stars">{t('sort_stars')}</option>
        </select>
      </div>

      {/* Selection counter */}
      <div className="flex items-center justify-between text-sm">
        <span className={`font-medium ${selectedRepos.length >= maxSelection ? 'text-[--color-text-accent]' : 'text-[--color-text-secondary]'}`}>
          {t('repos_selected', { count: selectedRepos.length, max: maxSelection })}
        </span>
        {selectedRepos.length > 0 && (
          <button
            type="button"
            onClick={() => onSelectionChange([])}
            className="text-xs text-gray-500 hover:text-gray-700"
          >
            {t('clear_selection')}
          </button>
        )}
      </div>

      {/* Repo list */}
      <div className="max-h-80 space-y-1.5 overflow-y-auto rounded-lg border border-[--color-border-default] p-2">
        {filtered.length === 0 ? (
          <p className="py-6 text-center text-sm text-gray-400">{t('no_repos_found')}</p>
        ) : (
          filtered.map(repo => {
            const isSelected = selectedRepos.includes(repo.html_url)
            const isDisabled = !isSelected && selectedRepos.length >= maxSelection
            return (
              <CheckboxRoot
                key={repo.full_name}
                checked={isSelected}
                onCheckedChange={() => toggleRepo(repo.html_url)}
                disabled={isDisabled}
                className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${
                  isSelected
                    ? 'border-em-200 bg-em-50'
                    : isDisabled
                    ? 'cursor-not-allowed border-gray-100 bg-gray-50 opacity-50'
                    : 'border-[--color-border-default] hover:bg-[--color-bg-surface-hover]'
                }`}
              >
                <CheckboxHiddenInput />
                <CheckboxControl>
                  <CheckboxIndicator />
                </CheckboxControl>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-sm font-medium text-gray-900">{repo.name}</span>
                    {repo.private && (
                      <span className="rounded bg-ink-200 px-1.5 py-0.5 text-[10px] font-medium text-[--color-text-secondary]">
                        private
                      </span>
                    )}
                  </div>
                  {repo.description && (
                    <p className="mt-0.5 truncate text-xs text-gray-500">{repo.description}</p>
                  )}
                </div>
                <div className="flex flex-shrink-0 items-center gap-3 text-xs text-gray-400">
                  {repo.language && (
                    <span className="flex items-center gap-1">
                      <span className="h-2.5 w-2.5 rounded-full bg-em-600" />
                      {repo.language}
                    </span>
                  )}
                  {repo.stargazers_count > 0 && (
                    <span className="flex items-center gap-0.5">
                      <svg className="h-3.5 w-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      {repo.stargazers_count}
                    </span>
                  )}
                  <span className="hidden sm:inline">{formatDate(repo.updated_at)}</span>
                </div>
              </CheckboxRoot>
            )
          })
        )}
      </div>
    </div>
  )
}
