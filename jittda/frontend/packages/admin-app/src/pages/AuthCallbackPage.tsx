import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const TOKEN_KEY = 'jittda_token'
const API_BASE = import.meta.env.VITE_API_BASE || ''

export function AuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  useEffect(() => {
    const code = searchParams.get('code')
    if (!code) {
      navigate('/login', { replace: true })
      return
    }

    fetch(`${API_BASE}/api/auth/exchange?code=${encodeURIComponent(code)}`, {
      method: 'POST',
    })
      .then((res) => {
        if (!res.ok) throw new Error('Exchange failed')
        return res.json()
      })
      .then((data) => {
        if (data.token) {
          localStorage.setItem(TOKEN_KEY, data.token)
          navigate('/', { replace: true })
        } else {
          navigate('/login', { replace: true })
        }
      })
      .catch(() => {
        navigate('/login', { replace: true })
      })
  }, [searchParams, navigate])

  return (
    <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
      <p className="text-[--color-text-secondary]">인증 처리 중...</p>
    </div>
  )
}
