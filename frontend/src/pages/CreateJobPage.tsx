import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useJob } from '../hooks/useJob'

export function CreateJobPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { createJob } = useJob()

  const [jdText, setJdText] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('미들')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!jdText.trim()) return

    setSubmitting(true)
    setError(null)
    try {
      const job = await createJob({
        jd_text: jdText,
        experience_level: experienceLevel,
      })
      navigate(`/jobs/${job.job_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('create_job')}</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {t('jd_label')} *
          </label>
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder={t('jd_placeholder')}
            rows={10}
            className="w-full border border-gray-300 rounded-lg p-3 text-gray-900"
            required
            minLength={50}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {t('experience_level')}
          </label>
          <select
            value={experienceLevel}
            onChange={(e) => setExperienceLevel(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
          >
            <option value="신입">{t('level_entry')}</option>
            <option value="주니어">{t('level_junior')}</option>
            <option value="미들">{t('level_mid')}</option>
            <option value="시니어">{t('level_senior')}</option>
            <option value="CTO/VP">{t('level_executive')}</option>
          </select>
        </div>

        {error && (
          <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || jdText.length < 50}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {submitting ? t('loading') : t('submit')}
        </button>
      </form>
    </div>
  )
}
