import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const TOKEN_KEY = 'jittda_token'

export function AuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  useEffect(() => {
    const token = searchParams.get('token')
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
      navigate('/', { replace: true })
    } else {
      navigate('/login', { replace: true })
    }
  }, [searchParams, navigate])

  return (
    <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
      <p className="text-[--color-text-secondary]">인증 처리 중...</p>
    </div>
  )
}
