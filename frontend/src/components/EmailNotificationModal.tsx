import { useTranslation } from 'react-i18next'
import {
  ActionButton,
  DialogRoot, DialogPositioner, DialogBackdrop,
  DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter,
} from '../../seed-design/ui'

interface Props {
  onAccept: () => void
  onDecline: () => void
}

export function EmailNotificationModal({ onAccept, onDecline }: Props) {
  const { t } = useTranslation()

  return (
    <DialogRoot open onOpenChange={(open) => { if (!open) onDecline() }}>
      <DialogBackdrop />
      <DialogPositioner>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <div className="w-12 h-12 bg-em-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-em-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <DialogTitle className="text-center">{t('email_notification_title')}</DialogTitle>
            <DialogDescription className="text-center">{t('email_notification_desc')}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <ActionButton variant="neutralOutline" size="medium" onClick={onDecline} className="flex-1">
              {t('email_notification_no')}
            </ActionButton>
            <ActionButton variant="brandSolid" size="medium" onClick={onAccept} className="flex-1">
              {t('email_notification_yes')}
            </ActionButton>
          </DialogFooter>
        </DialogContent>
      </DialogPositioner>
    </DialogRoot>
  )
}
