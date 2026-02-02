import { useState, useEffect, useCallback } from 'react'
import { setToken, getToken, apiFetch } from '../lib/api'

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
      const data = await apiFetch('/auth/me')
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
  }, [])

  return { user, loading, logout, isAuthenticated: !!user }
}
