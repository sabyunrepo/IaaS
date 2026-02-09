import { useState, useEffect, useCallback } from 'react'
import { setToken, getToken, clearToken } from '../lib/api'

interface User {
  id: string
  email: string
  display_name: string
  avatar_url?: string
  role?: string | null        // 'ceo' | 'candidate' | 'both' | null
  github_username?: string | null
  providers?: string[]        // ['google', 'github']
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUser = useCallback(async () => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    try {
      const res = await fetch(`/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Unauthorized')
      const data = await res.json()
      setUser({
        id: data.id,
        email: data.email,
        display_name: data.name || data.email?.split('@')[0] || 'User',
        avatar_url: data.image,
        role: data.role,
        github_username: data.github_username,
        providers: data.providers || [],
      })
    } catch {
      clearToken()
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    if (token) {
      setToken(token)
      window.history.replaceState({}, '', window.location.pathname)
    }
    fetchUser()
  }, [fetchUser])

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
    window.location.href = '/login'
  }, [])

  const updateRole = useCallback(async (role: string) => {
    const token = getToken()
    if (!token) return
    const res = await fetch('/auth/role', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ role }),
    })
    if (res.ok) {
      setUser(prev => prev ? { ...prev, role } : null)
    }
  }, [])

  const updateProfile = useCallback(async (data: {
    display_name?: string
    language_preference?: string
  }) => {
    const token = getToken()
    if (!token) return
    const res = await fetch('/auth/profile', {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (res.ok) {
      const updated = await res.json()
      if (data.display_name) {
        setUser(prev => prev ? { ...prev, display_name: updated.name } : null)
      }
    }
  }, [])

  return { user, loading, logout, isAuthenticated: !!user, updateRole, updateProfile }
}
