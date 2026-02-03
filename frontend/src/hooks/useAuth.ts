import { useState, useEffect, useCallback } from 'react'
import { setToken, getToken } from '../lib/api'

const BACKEND = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

interface User {
  id: string
  email: string
  display_name: string
  avatar_url?: string
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
      const res = await fetch(`${BACKEND}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('Unauthorized')
      const data = await res.json()
      setUser(data)
    } catch {
      setToken(null)
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
    setToken(null)
    setUser(null)
    window.location.href = '/login'
  }, [])

  return { user, loading, logout, isAuthenticated: !!user }
}
