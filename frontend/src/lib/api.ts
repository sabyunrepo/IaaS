const API_BASE = '/api/v1'

let accessToken: string | null = null

export function setToken(token: string | null) {
  accessToken = token
}

export function getToken(): string | null {
  return accessToken
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
    setToken(null)
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
