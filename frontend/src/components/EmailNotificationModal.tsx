import { useTranslation } from 'react-i18next'

interface Props {
  onAccept: () => void
  onDecline: () => void
}

export function EmailNotificationModal({ onAccept, onDecline }: Props) {
  const { t } = useTranslation()

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-sm mx-4">
        <div className="text-center">
          <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {t('email_notification_title')}
          </h3>
          <p className="text-sm text-gray-600 mb-6">
            {t('email_notification_desc')}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={onDecline}
            className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            {t('email_notification_no')}
          </button>
          <button
            onClick={onAccept}
            className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            {t('email_notification_yes')}
          </button>
        </div>
      </div>
    </div>
  )
}
