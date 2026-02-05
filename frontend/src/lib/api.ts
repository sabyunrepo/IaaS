const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'
const TOKEN_KEY = 'vantict_access_token'

let accessToken: string | null = null

export function setToken(token: string | null) {
  accessToken = token
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

export function getToken(): string | null {
  if (!accessToken) {
    accessToken = localStorage.getItem(TOKEN_KEY)
  }
  return accessToken
}

export function clearToken() {
  accessToken = null
  localStorage.removeItem(TOKEN_KEY)
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (res.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }))
    throw new Error(err.detail?.message || err.message || 'API Error')
  }

  if (res.status === 204) return null

  return res.json()
}
