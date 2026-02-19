import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { setToken } from '../lib/api'
import { ProgressCircle } from '../../seed-design/ui'

export function AuthCallbackPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const token = searchParams.get('token')
    if (token) {
      setToken(token)
      navigate('/', { replace: true })
    } else {
      navigate('/login', { replace: true })
    }
  }, [navigate, searchParams])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <ProgressCircle size="large" tone="brand" className="mx-auto mb-4" />
        <p className="text-gray-600">{t('auth_callback_processing')}</p>
      </div>
    </div>
  )
}
