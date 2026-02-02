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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!jdText.trim()) return

    setSubmitting(true)
    try {
      const job = await createJob({
        jd_text: jdText,
        experience_level: experienceLevel,
      })
      navigate(`/jobs/${job.id}`)
    } catch (err) {
      console.error('Failed to create job:', err)
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
            채용공고 (JD) *
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
            경험 레벨
          </label>
          <select
            value={experienceLevel}
            onChange={(e) => setExperienceLevel(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
          >
            <option value="신입">신입</option>
            <option value="주니어">주니어</option>
            <option value="미들">미들</option>
            <option value="시니어">시니어</option>
            <option value="CTO/VP">CTO/VP</option>
          </select>
        </div>

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
